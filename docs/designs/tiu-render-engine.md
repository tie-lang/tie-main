# tiu 渲染引擎架构设计 —— 新一代 2D 引擎
*EN: tiu Render Engine Architecture — a next-gen 2D engine*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（文档；本期只落到设计，不进入实现）
**依据** / Basis: `ROAD.md` p.9.3（tiu 独立自研 UI 框架）· `docs/release.md` §3.4（tiu 组件仓定位）· 对 Skia 的根因分析（§1）
**关联** / Related: `docs/designs/keel-architecture.md`（可复用的注册/审计机制层）· `docs/plans/2026-09-11-p721-repo-split.md`（tiu 独立仓 tie-lang/tiu 规划）
**版本** / Version: v0.3（2026-09-12 实施闭环修订：后端排期落实施计划、范围职责归属、契约冻结引用）· v0.2（增补 OpenGL 兼容后端定位）· v0.1 初稿

> EXEC BRIEF: Defines the architecture for tiu's render engine — the bottom
> layer of the three-layer tiu framework (Engine / Drawing API / UI widgets).
> The engine follows a seven-layer next-gen 2D design that fixes Skia's root
> pain points: runtime shader compilation jank, CPU/GPU backend drift, full
> re-record on dirty frames, and per-layer offscreen memory duplication. Core
> decisions: (1) the draw-list is the only cross-layer interface, (2) all
> geometry/ordering/compositing is pushed to the GPU where available, (3) the
> shader set is precompiled — zero runtime compilation on the hot path, (4)
> memory lifetimes are decided by an explicit frame graph with aliasing, (5) a
> single raster core guarantees identical software/GPU output. This round is
> **design only — no implementation.**

---

## 1. 背景与动机 / Background & Motivation

tiu 的渲染引擎不建立在 Skia 之上，而是自研。取舍依据是下述对 Skia 的根因分析（RCA）——不是功能缺失，而是**结构性问题**。

| 痛点 / Pain point | 根因 / Root cause | 后果 / Consequence |
|---|---|---|
| 运行时 shader 编译 | GPU 后端到首帧遇到新 paint 组合才编译（SkSL → 后端 ISA）| 帧间卡顿（jank）；组合空间巨大，无法热身 | 
| CPU / GPU 双后端漂移 | SkRasterPipeline 与 GPU tessellator 是两套实现 | AA 覆盖率、滤镜细节对不上；双倍维护、行为不确定 |
| 伪保留模式 | Skia 本体即时模式；auto Layer tree 由宿主（Flutter/Android）外挂 | 任何 dirty 变化都整层 re-record / 全量重放 |
| 离屏内存按层翻倍 | saveLayer 每层分配独立位图/纹理，无资源复用 | 层多即内存与带宽成倍放大 |
| 几何三角化锁 CPU | path 串行细分（tessellation）在 CPU 侧 | 动态/变换路径成本高、机时不可预测 |
| 文本位图缓存 | strike cache 以位图缓存 glyph | 高 DPI/变焦时重复栅格化；内存占用不稳 |

**设计目标** / Goals：
* 确定性能：关键路径**零运行时编译**，帧时间可预测（不做"首帧尤其慢"的引擎）
* 内存可预测：以**显式预算 + 帧图别名**控制峰值；离屏数层不按层叠加
* 单一内核一致性：GPU 与软件回退共用同一渲染语义定义，视觉零漂移
* 可独立使用：Engine 只消费"绘制表"，不感知控件语义（tiu 三层可单取任意一层）

**非目标** / Non-goals（本期明示不做）：
* 不做 UI 层（组件树/布局/主题）——属于 tiu 上层，不在本文范围
* 不牺牲无 GPU 环境：软件回退是**第一优先实现**（见模块路线），不是事后补丁
* 不追求与 Skia API 兼容；绘制 API 形态见 `docs/designs/tiu-drawing-api.md`（已定稿）

---

## 2. 设计理念 / Design Pillars

这五个支点是全部下层决策的判定标准。

1. **声明式场景，非命令流** —— 上层产生的是带稳定 key 的绘制表（数据），不是运行期对象引用与调用链；引擎按表重放与缓存。
2. **与 GPU 协作** —— 几何细分、排序、合成在可行时全部下沉 GPU；CPU 只保留按需计算与编排。
3. **编译提前** —— 运行期不允许出现 shader 编译；着色集合离线预编译、持久化缓存。
4. **内存显式** —— 每个离屏资源生命周期由 Frame Graph 决定，同一帧可别名复用，峰值显式可算。
5. **单内核双端一致** —— 一份渲染语义规范，两套执行体（GPU pipeline / SIMD 软件内核），结果一致。

> EN: Five pillars — declarative scene (stable-keyed draw-list as data, not a
> call chain); GPU-first geometry/ordering/compositing; precompiled shaders
> with zero runtime compilation; explicit memory lifetimes via frame-graph
> aliasing; one raster core with identical software/GPU semantics.

---

## 3. 总体架构 / Architecture Overview

引擎分七层，自上而下（数据流方向）：

| 层 | 名称 | 职责 | 归属 tiu 层 |
|---|---|---|---|
| L1 | Scene 前端 · 保留场景图 | 场景快照、dirty-rect 差分、子树脏区传播 | UI 库 |
| L2 | 中间 IR 绘制表 | 稳定 key、骨架缓存、子图随机访问；immediate/retained 双模式 | API 库（割界） |
| L3 | Frame Graph 提交层 | pass 编排、barrier 自动、离屏内存别名 | 渲染引擎 |
| L4 | GPU 几何引擎 | compute tessellation；基础图元 GPU 细分子着色器 | 渲染引擎 |
| L5 | 预编译 Shader 库 | sparse 组合、SPIR-V 单源、持久化缓存 | 渲染引擎 |
| L6 | 统一光栅核心 | GPU 与软件同一语义执行体 | 渲染引擎 |
| L7 | 资源与缓存管理 | 纹理 atlas、显式预算、LRU 换出 | 渲染引擎 |

**数据流** / Data flow（唯一跨层接口）：

* UI 库：控件状态 → dirty rect → 增量绘制表段
* API 库：绘制意图 → 编码为绘制表（L2 IR，稳定 key）
* 渲染引擎（L3–L7）：绘制表 → Frame Graph pass 集 → 像素

> EN: Seven layers L1–L7. L1 lives in the UI layer, L2 spans the API layer
> boundary, L3–L7 form the engine proper. The draw-list is the only channel
> crossing layers — no object references, no code paths, data only.

---

## 4. 绘制表 IR（层 1–2） / Draw-list IR

绘制表是 tiu 的「跨层字节协议」——与编译器界 tieir 同等的地位：它是**数据**，可在 worker 线程构建、随机访问、缓存、序列化（zd 底座可选）。

**记录格式** / Record：

* `op`：图元种类（rect / rrect / 椭圆 / 弧线 / path / 文本 / 图像 / PushLayer / PopLayer / filter 生效）
* `key`：稳定差分键（见下）
* `geo`：几何引用（图元数据或 path 数据块）
* `paint`：paint 引用（颜色 / 渐变 / 图像 / 着色器 / 描边参数）
* `clip`：裁剪几何（可空，可嵌套）
* `meta`：图层归属 / 命名字段（调参用，不参与渲染语义）

**稳定 key 设计**（差分更新的核心）：

* key = `op · geo-hash · paint-hash · 变换分级`
* 变换分两级：**视图变换**（整帧共用，一组）与**逐项变换**（每个图元独立）——让同批图元共享 key 前缀，骨架缓存只需比较前缀段
* hash 计算采用轻量组合（如 TSHA 族指纹，复用 tie 既有密码学底座）

**差分与骨架缓存**：

* 场景树每个节点持有子树 key；子树未变 → 该子树绘制表段直接复用（骨架缓存），仅脏子树增量重编码
* dirty rect 沿树向上合并，Engine 只重放脏区的 pass

**双模式** / Dual mode：

* **Immediate**：API 直接生成绘制表并立即进引擎（画布即时用）
* **Retained**：API 缓存绘制表，UI 层差分复用（控件框架路径）
* 同一 IR，两种入口；引擎无感知差异

> EN: The draw-list is tiu's cross-layer wire format, data-only, worker-thread
> friendly. Records carry a stable key = op · geo-hash · paint-hash · transform
> tier (frame-shared vs per-item). Unchanged subtrees reuse cached draw-list
> segments; dirty rects merge upward; only dirty passes are replayed.

---

## 5. Frame Graph（层 3） / Frame Graph

**节点**：渲染 pass（光栅 pass / 滤镜 pass / 合成 pass）。
**边**：资源依赖（读/写关系）。
**资源**：RenderTarget（离屏纹理 / FBO）、描述符与生命周期由引擎集中管理。

* **pass 编排**：按依赖图确定执行顺序并合并相邻 pass（减少渲染目标切换与屏障)
* **barrier / transition 自动**：跨 API 的布局转换（Vulkan layout transition、Metal/D3D12 等价物）由引擎推导插入，上层不感知
  * **GL 约束**：GL 后端无显式 layout transition / 同步原语，同步交给驱动（驱动保守同步 → p95 抖动风险）；故 GL 为「兼容后端」，不承担确定性能指标（见 §11/§12）
* **离屏别名**：同一帧内生命周期不重叠的 RenderTarget **复用同一块显存/内存**（区间图着色 / 贪心复用）
  * 收益：N 层离屏的峰值内存 ≈ 活跃期最大单层，而非 Σ 各层

**朴素对照** / Why it wins over saveLayer：Skia/宿主把每层当独立分配；Frame Graph 把「层」视为 pass 间共享的临时资源，显式、可算、可复用。

---

## 6. GPU 几何引擎（层 4） / GPU Geometry

图元分两级处理：

* **基础图元**（rect / rrect / arc / 线 / 常规渐变圆）：固定顶板 + 细分子着色器直接 GPU 生成，**不走 CPU 三角化**
* **复杂 path（任意轮廓）**：GPU compute pass 做三角形化（扫描线/覆盖计数写入顶点流），再进光栅 pass
* **文本**：矢量轮廓直接 GPU 化（SDF 或直接轮廓细分），不依赖位图 strike 缓存——缩放无损、内存稳定
* **GL 档位**（兼容后端）：
  * GL 4.3+ / GLES 3.1+：完整引擎（compute 细分、间接绘制）
  * GL 3.3 / GLES 3.0：基础图元 + **CPU 细分回退**（无 compute 分支）
  * GL 3.0 之下：直接走软件内核
  * **macOS 不提供 GL 后端**（macOS GL 止于 4.1、无 compute，且 Apple 已弃 GL；macOS 走 Metal）

**AA 语义**：边缘覆盖率在 GPU 上按「边缘场/覆盖场」计算，与软件内核共用同一覆盖定义（见层 6），保证两个执行体像素一致。

**软件回退**：无 GPU / 受限环境下同一图元由 SIMD 软件内核执行相同语义（第一优先实现，见模块路线）。

> EN: Simple primitives are GPU-subdivided natively; complex paths and text go
> through GPU compute tessellation — CPU does zero triangle generation. AA
> coverage shares one definition with the software core, so both paths produce
> identical pixels.

---

## 7. 预编译 Shader 库（层 5） / Precompiled Shader Bank

**组合空间裁剪**：着色组合 = `blend × mask × 颜色变换 × (实色/渐变/图像/着色器) × 滤镜集` 的**稀疏子集**。覆盖 P90 使用面（桌面 UI 实际组合数有限）。

* **离线预编译**：发布期把全集编译为各后端目标（按设备特性生成变体），写持久化缓存（hash key + 设备指纹）
* **运行期命中即用**：lookup 命中 → 直接绑定；未命中 → 走**降级组合**（拆成多个标准 pass），而不是即时编译
* **SPIR-V 单源**：tie 内嵌着色器 DSL → SPIR-V → 转 Vulkan / Metal(MSL) / D3D12(DXIL)；后端间行为零漂移
  * **GL（GLES）转译**：SPIR-V → GLSL 转译为 GL 兼容后端着色目标（GL 不原生消费 SPIR-V；驱动对 `ARB_gl_spirv` 支持差，故采用转译而非原生路径）；后端落地顺序（Vulkan → Metal → D3D12 → GL 转译）与各自独立验收见 `docs/plans/2026-09-12-tiu-render-impl.md` §1
* **软件内核同位素**：同一 DSL 模板同时生成 SIMD 软件内核（层 6 的软件执行体），一份语义两处落地

**预期结果**：首帧无编译；帧时间不随「第一次遇到某 paint」波动。

---

## 8. 统一光栅核心（层 6） / Unified Raster Core

* **单一渲染语义规范**：插值、混合、覆盖率、颜色管理（固定工作空间：sRGB scene-linear → display transform）、伽马处理——全部在一份规范里定义
* **两执行体**：
  * GPU：由层 5 预编译 shader 组合驱动
  * 软件：预编译 SIMD 内核（SSE/AVX/NEON），合并阶段、不产生中间位图（借鉴 SkRasterPipeline 的合并思路，但语义由统一规范约束）
* **一致性校验**：CI 中 gold 图对比（软件 vs GPU 输出差异阈值），防止漂移回归

---

## 9. 资源与缓存管理（层 7） / Resources & Caching

* **纹理 atlas**：位图 / 字帖 / 图标合批进图集，减少 draw call 与纹理切换
* **显式预算**：
  * GPU 资源预算 = `min(显存比例, 硬上限)`，配置两档（低内存 / 高性能）
  * 离屏池由 Frame Graph 生命周期决定（§5 别名）
* **LRU 换出**：path 细分数据、文本矢量结果按预算换出
* **可持久化**：层 5 shader 预编译缓存、字体形状数据可选落盘（首启提速）

---

## 10. tiu 三层边界 / Boundaries

| 层 | 内容 | 不负责 |
|---|---|---|
| UI 库 | 控件、布局、主题、动画、脏矩形差分 | 不下发几何细节到引擎、不触碰 GPU |
| API 库 | 绘制命令、图元与 paint、文本排版、immediate/retained 入口 | 不持有控件状态、不管理 GPU 过渡 |
| 渲染引擎 | L3–L7：帧图、几何、shader、内核、资源 | 无控件/DPR 语义；输入只有绘制表 |

**边界铁律**：层间只走数据（绘制表 / 脏矩形 / 事件轴独立），不穿越代码引用。三层各自可单独测试、单独嵌入、单独替换后端（软件 / Vulkan / Metal 互换不改上层）。

---

## 11. 跨平台后端策略 / Backends

* **主路径**：Vulkan（Windows / Linux / Android）· Metal（macOS / iOS）· D3D12（Windows 备选相同语义）
* **GL 兼容后端**（覆盖 Vulkan/Metal 之外的长尾：GL 4.3+/GLES 3.1+ 完整引擎；GL 3.3/GLES 3.0 基础图元 + CPU 细分回退；更旧走软件内核）：
  * 定位：**兼容件**——老 Android（无 Vulkan）、老 iGPU、虚拟机/远程桌面等仅 OpenGL 可用的环境
  * **macOS 不提供 GL 后端**（GL 4.1 无 compute + Apple 弃 GL；macOS 走 Metal）
  * 线程模型受限：GL 单上下文单线程、「make current」切换昂贵 → GL 后端不承担后台提交/多线程记录优化
* **软回退**：SIMD 统一内核（同上）；无 GPU（VM / 服务器 / 老设备）自动回落
* **落地顺序**（见 `docs/plans/2026-09-12-tiu-render-impl.md` §1）：软件内核 + Vulkan 先行，验证全链路；其后按序 Metal / D3D12（单源 shader 平移）、GL 转译（兼容后端），各自独立验收
* **窗口 / 输入**：最小平台抽象层由 p.9.3.1 运行时底座窗口部分负责，引擎不绑定任何具体平台壳

---

## 12. 验收基准 / Acceptance

| 指标 / Metric | 基准 / Baseline |
|---|---|
| 首帧编译 | 运行期零 shader 编译（探针断言无编译路径触发）|
| 帧时间 | p95 波动 ≤ 均值 1.5×（非首帧）|
| draw call | 普通 UI 帧 ≤ 数十级（atlas + 批量后）|
| 离屏内存 | N 层离屏峰值 ≈ 最大单层（Frame Graph 别名生效探针）|
| CPU 几何 | 复杂 path 帧 CPU 细分耗时 ≈ 0（GPU 化后）|
| 双端一致性 | 软件 vs GPU gold 图差 ≤ 1/255（逐像元允许容差）|
| GL 降档（兼容件）| GL 后端只要求 **gold 一致性达标**；性能指标（p95、draw call）按档放宽，不适用确定性能基准 |
| 内存剖面 | 预算生效：缓存水位收敛于配置区间 |

工具：内置 benchmark、gold 图比较器、内存探针（复用 tie 诊断标号体系输出 W/E 级别提示）。

---

## 13. 实现模块路线 / Module Roadmap

模块按依赖自底向上；**每个模块完成后即自验证**（不是事后统一验收）。

* **模块一：绘制表 IR + 软件统一内核** —— 最小 End-to-End：rect/文本纯色帧，走通绘制表 → 软件光栅 → 帧缓冲；确立 key 与 record 格式
* **模块二：Frame Graph + 离屏别名** —— 滤镜/图层 pass、资源生命周期、别名复用；离屏内存探针
* **模块三：着色器 DSL + 预编译集** —— DSL → SPIR-V 管道；P90 组合集离线编译；软件内核同位素生成
* **模块四：Vulkan 后端** —— 统一内核语义由预编译 shader 落地；gold 一致性比较与模块一/二
* **模块五：GPU 几何细分 + 文本 GPU 化** —— compute tessellation、基础图元细分子着色器、SDF/轮廓文本
* **模块六：资源管理收口** —— atlas、预算、LRU、持久化缓存
* **模块七：差分/骨架缓存正式契约** —— 场景树 dirty-rect 与绘制表段的增量协议定稿（对接 API/UI 层）

依赖：tie 语言（自举后的生产工具链）；复用 tie 安全底座（TSHA 指纹、密钥体系）于 key/缓存校验；zd 底座可选用于绘制表序列化。跨层契约在实施计划中**当场冻结**（IR/wire 与 API 库实施计划 T2.1 同源、增量段协议消费 API 库 T2.3 冻结件、资源句柄接口与 API 库 T5.2 同源）；后端着色目标按实施计划 §1 顺序落地。

---

## 14. 风险与边界 / Risks & Non-scope

* **GPU 特性依赖收窄兼容面** → 缓解：软件内核第一优先（模块一即存在），GPU 特性缺失时自动回落
* **全自研 shader DSL 工作量大** → 缓解：先覆盖 P90 组合集，稀疏命中外组合走降级拆分（不即时编译）
* **文本 GPU 化的渲染质量风险** → 缓解：gold 阈值 + 极复杂字形可回退软件位图模式（仅提示性，不引入 strike 常驻）
* **GL 驱动差异** → 缓解：GL（尤其 Windows Intel/AMD）驱动行为差异大，gold 一致性验证按 GL 档放宽阈值；GL 定位兼容件，不作字节级一致承诺（见 §12）
* **不在本引擎范围（职责归属，非挂起项）**：
  * UI 组件树/布局/主题/差分 → `docs/designs/tiu-ui-widgets.md` 已定稿（本引擎不感知控件语义）
  * 绘制 API 语法与对象模型 → `docs/designs/tiu-drawing-api.md` 已定稿（增量段协议已冻结于其实施计划 T2.3，本引擎按冻结件消费，不"对接时再定"）
  * 窗口与输入封装 → p.9.3.1 运行时底座（ROAD 已登记）· 事件通道 → `docs/designs/tiu-event-system.md` 已定稿（不进入绘制通道）

---

## 15. 附录 / Appendix

* 术语 / Terms：IR（中间表示）· Frame Graph（帧图）· RenderTarget（渲染目标）· 别名（aliasing，资源共享复用）· SDF（有向距离场，文本 GPU 化一种方案）· gold 图（基准图一致性对比）
* 演进：本设计随实现修正；模块一的实现结论会反向修订 IR 定义（记录在文档版本表）