# tiu 渲染引擎实施计划 —— 无遗留闭环
*EN: tiu Render Engine Implementation Plan — closed-loop, no leftovers*

**日期** / Date: 2026-09-12 · **类型** / Type: 实施计划（任务分解 + 契约冻结 + 后端落地顺序；交付可执行清单，不含挂起项）
**依据** / Basis: `docs/designs/tiu-render-engine.md` v0.3（§13 模块路线、§14 范围归属、§12 验收基准）· `docs/plans/2026-09-12-tiu-api-impl.md`（API 库实施计划：T2.1/T2.3/T5.2 冻结件，本计划同仓消费）
**关联** / Related: `docs/designs/tiu-drawing-api.md`（IR/wire 同源）· `docs/designs/tiu-ui-widgets.md`（增量协议消费方）· `docs/designs/tiu-event-system.md`（事件轴不进入本引擎范围）
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Turns the engine module roadmap (render-engine §13) into an
> executed task list with zero open tails. Cross-layer contracts are frozen in
> the companion API plan (§2 of that plan) and consumed here as-is — no new
> negotiation. Backend order is fixed: software core + Vulkan first, then
> Metal / D3D12 (single-source shader port), then GL transpilation (compat
> backend), each with its own acceptance gate. The shader DSL is a tie table/
> function form (no new language feature); the SPIR-V writer is an in-house
> minimal implementation covering the P90 instruction subset — no external
> shader toolchain. Each task ships one commit; every module self-verifies;
> the terminal gate (TP1–TP4) maps to §12 acceptance. **Design-to-execution
> bridge only — implementation starts after tiu repo creation (Z1).**

---

## 1. 任务清单 / Task List

执行顺序自上而下；**每任务一个提交**（英文 message）；每模块完成即自验证（探针全绿）。

### 零任务：开仓（与 API 计划共用，不推后）
* **Z1** `tie-lang/tiu` 独立仓创建（TPL 2.0 + README ## License + .gitignore；API 计划 Z1 同一动作，本计划沿用该仓；引擎与 API 同仓双目录：`engine/` 与 `api/`）
* **Z2** 工具链就绪：自举 tiec（现有生产 exe）验证可编译本项目形态；gold 图比较器、内存探针工具线落地（复用 tie 诊断工具线）

### 模块一：绘制表 IR + 软件统一内核（End-to-End 最小帧）
* **T1.1** record 字节布局解析装载（与 API T2.1 **同源冻结件**：引擎侧先按冻结定义实现 loader，直接消费手工构造/API 侧产出的 IR 字节）
* **T1.2** 软件图元光栅：rect / 纯色 / 文本（位图字形起步）→ 软件帧缓冲
* **T1.3** 渲染语义规范初版（插值 / 混合 / 覆盖率 / 颜色工作空间）落地为内核唯一执行路径
* **T1.4** 基础 gold 探针（软件输出与基准图比对 ≤1/255）
* **验收门**：T1.1–T1.4 全绿；与 API 模块一/二互验 IR 字节一致

### 模块二：Frame Graph + 离屏别名
* **T2.1** pass 图构建与依赖排序（光栅/滤镜/合成三类 pass）
* **T2.2** RenderTarget 生命周期 + 区间别名复用（同帧不重叠资源共享内存）
* **T2.3** 离屏内存探针（N 层 ≈ 最大单层）
* **验收门**：别名命中率探针 + 内存峰值断言

### 模块三：着色器 DSL + 预编译集
* **T3.1** 着色器 DSL（tie **表/函数形态，不引入新语法**）：sparse 组合模板（P90 集合实名枚举）
* **T3.2** SPIR-V 自研最小序列化器（P90 所需指令子集；**不绑定外部 shader 工具链**；缺指令的组合 → 登记降级拆分路径，不停工）
* **T3.3** 软件内核同位素生成（同一 DSL 模板 → SIMD 软件内核；复用模块一语义规范）
* **T3.4** 预编译集 + 持久化缓存（hash key + 设备指纹；落盘首启提速）
* **验收门**：P90 集合全编译通过；软件/GPU 语义同源断言

### 模块四：Vulkan 后端
* **T4.1** 平台最小抽象接线（窗口/上下文经 p.9.3.1 接口，引擎不绑定壳）
* **T4.2** 预编译 shader 绑定 + 基础光栅路径（模块三产物直接消费，运行期零编译断言）
* **T4.3** gold 一致性（Vulkan vs 软件内核 ≤1/255）
* **验收门**：零编译探针（无编译路径触发）+ gold 一致

### 模块五：GPU 几何细分 + 文本 GPU 化
* **T5.1** 基础图元 GPU 细分（rect/rrect/arc 细分子着色器，不走 CPU 三角化）
* **T5.2** 复杂 path compute tessellation（扫描线/覆盖计数 → 顶点流）
* **T5.3** 文本 GPU 化（SDF/轮廓细分；无位图 strike）
* **T5.4** CPU 几何耗时探针（复杂 path 帧 CPU 细分 ≈ 0）
* **验收门**：T5.1–T5.4 全绿；软回退路径保底（无 GPU 自动回落软件内核）

### 模块六：资源管理收口
* **T6.1** 纹理 atlas（位图/字帖/图标合批）
* **T6.2** 显式预算（min(显存比例, 硬上限) 两档）+ LRU 换出
* **T6.3** 持久化缓存收口（shader 缓存衔接 T3.4、字体形状数据可选落盘）
* **验收门**：内存剖面探针（缓存水位收敛于配置区间）

### 模块七：差分契约兑现（对接 API/UI）
* **T7.1** 增量段消费（按 API 计划 **T2.3 冻结件**实现：子树 key 前缀 + dirty rect 段）
* **T7.2** 骨架缓存（未变子树绘制表段直接复用，只重放脏区 pass）
* **T7.3** 双端一致性终检 + §12 验收全项探针滚动通过
* **验收门**：T7.1–T7.3 + 整树 key 隔离探针

### 终点验收（全部模块完成后统一门禁）
* **TP1** 软件内核全链路 gold（§12 首帧零编译/帧时间/内存剖面探针）
* **TP2** Vulkan 后端 gold 一致性（vs 软件内核 ≤1/255；§12 双端一致）
* **TP3** 与 API 库联调：绘制表 → 引擎 → 帧缓冲 gold（对 API 计划 TP2 同基准，双向 gold IR 验）
* **TP4** Metal / D3D12 / GL 转译经模块三单源产物平移，各自独立 gold 门（按 §1 后端顺序逐期触发，不阻塞 TP1–TP3）

---

## 2. 契约与后端顺序（当场冻结，不中途谈判） / Frozen Contracts & Backend Order

| 契约 | 范围 | 冻结于 | 修订通道 |
|---|---|---|---|
| IR/wire | record 布局 + key 算法（引擎 §4 定义，API T2.1 同源）| T1.1（本计划）/ T2.1（API 计划）| 版本表回写，两仓双方同意 |
| 增量段协议 | 子树 key 前缀 + dirty rect（UI 层消费）| **消费 API T2.3 冻结件**（本计划不重新定义）| API 计划通道 |
| 资源句柄接口 | acquire/retain/release/handoff（引擎 §9 交互）| T5.2（API 计划）同源 | 版本表回写 |
| 后端顺序 | 软件+Vulkan → Metal → D3D12 → GL 转译 | 本文档 §1（TP4 触发）| 不谈判；顺序即路线 |

> EN: Engine consumes the API plan's frozen contracts as-is (IR wire via API
> T2.1, incremental protocol via API T2.3, resource handle interface via API
> T5.2). Backend order is fixed by this plan — software core + Vulkan first,
> then Metal/D3D12, then GL transpilation; each backend gate is independent.

---

## 3. 实现约定 / Implementation Conventions

* **语言**：全部以 tie 实现（每任务产 tie 代码）；自举 tiec 编译验证
* **着色器 DSL**：tie 表/函数形态，**不主张新语言特性**；歧义由 tie 既有语法裁决（同 API 计划 §3）
* **SPIR-V 生成**：自研最小序列化实现（P90 指令子集）；不引入 glslang/tint 等外部依赖——缺指令子集 → 该组合走降级拆分（引擎 §7 机制），**不产生等待外部组件**
* **探针工具线**：gold 图比较器、内存探针、零编译探针随 Z2 落地，全模块共用

---

## 4. 无遗留清单 / No-leftover Checklist

* 不设"后期优化 / 另行规划 / 待定稿"挂起项——后端顺序（§1）、契约（§2）、DSL 形态（§3）均当场定
* 契约不中途谈判——IR/wire、增量段、资源句柄走冻结通道；修订仅版本表回写
* 外部依赖不悬空——shader 工具链排除；DSL 不要求语言特性；窗口壳归 p.9.3.1（ROAD 已登记）
* 范围归属清晰——UI/API/事件均已有定稿文档，本计划不代管
* 每任务单提交、可回退；终点 TP1–TP4 有明确通过定义；无限循环风险 = 探针先绿再前进

---

## 5. 验收门禁汇总 / Gate Summary

* 每任务：该任务探针绿（gold / 断言），单提交
* 每模块：模块内任务全绿 = 模块完成
* 终点：TP1–TP4 全绿 = 本计划完成（**渲染引擎实施闭环**）；TP4 各后端按 §1 顺序独立触发，不依赖 TP1–TP3 完成之后的排程空窗