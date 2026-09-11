# tiu 绘制 API 库设计
*EN: tiu Drawing API Library Design*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（文档；本期只落到设计，不进入实现）
**依据** / Basis: `docs/designs/tiu-render-engine.md`（渲染引擎七层架构与绘制表 IR）· ROAD.md p.9.3（tiu 独立自研 UI 框架）· `docs/release.md` §3.4
**关联** / Related: `docs/designs/tiu-render-engine.md` §4（绘制表 IR）· §10（tiu 三层边界）· p.9.3.2（组件树与布局框架，消费本库）
**版本** / Version: v0.2（2026-09-12 实施闭环修订：语法约定实写、跨层契约冻结于实施计划、效果栈范围闭合）· v0.1 初稿

> EXEC BRIEF: Defines tiu's drawing API library — the middle layer of tiu
> (Engine / Drawing API / UI widgets). Its sole job is to encode drawing intent
> into the draw-list IR: the API accepts primitive/paint/text semantics and
> produces stable-keyed IR data; it owns NO rasterization, NO state machine and
> NO control semantics. Core decisions: (1) declarative, value-semantics data
> records — descriptions, not function calls that execute; (2) the stable IR key
> is derived automatically, callers never write keys; (3) immediate and retained
> are one pipeline — immediate = record-then-submit; (4) records are immutable
> and worker-thread buildable; (5) resource handles are refcounted and separated
> from geometry. The draw-list remains the only cross-layer interface. **Design
> only — no implementation.**

---

## 1. 定位与边界 / Position & Boundary

中间层：输入「绘制意图」（来自 UI 层增量或开发者直接调用），输出「绘制表 IR」（唯一跨层接口，交付渲染引擎）。

* **本库负责**：图元/Path/Paint/文本/资源 的语义模型（数据记录）、意图 → IR 编码（含稳定 key 派生）、双模式入口（immediate / retained）、文本排版结果、资源句柄与缓存
* **本库不负责**（属其他层或文档）：任何光栅/合成/GPU 过渡（引擎）· 控件状态与脏矩形差分（UI 库）· 事件与输入（事件轴独立）· 窗口壳与平台抽象（p.9.3.1 运行时底座）

---

## 2. 设计原则 / Design Principles

1. **描述式，不执行式** —— 每次调用产生的是**数据描述**（图元记录、paint 记录），不是"立即画到某处"的副作用调用。描述可缓存、可复现、可序列化（zd 可选）、可跨线程传递。
2. **薄门面** —— API 只做「意图 → IR」编码与资源引用解析，不实现任何渲染逻辑；渲染语义全部在引擎（单内核，见引擎文档 §8）。
3. **key 自动化** —— 稳定差分 key（`op · geo-hash · paint-hash · 变换分级`）由 IR 编码器自动派生；调用方不写、也**不允许**手写 key（杜绝人为不一致）。
4. **双模式同构** —— immediate 与 retained 走同一条 IR 通道：`Immediate = Record(); Submit(record)` 的合成写法；retained 的「记录-重放」复用同一数据。
5. **不可变与线程友好** —— 图元/Paint 一经构建不可变（值语义 / 深度只读）；同一绘制表可在 worker 线程构建后移交流程，无需加锁。
6. **资源与几何分离** —— 图像/字体经资源句柄（引用计数）引用，不内嵌在几何数据中；句柄跨线程安全。

> EN: Declarative value-semantics records (no side-effect calls); thin facade
> (encode intent → IR only, all rendering lives in the engine); keys derived
> automatically; immediate = record+submit; immutable, worker-buildable; OS
> handles refcounted and decoupled from geometry.

---

## 3. 核心对象模型 / Object Model

### 3.1 会话与目标 / Surface

* `Canvas`：一次绘制会话（目标 = 窗口 Surface / 离屏 Surface / 图像 Surface）
* 会话属性：分辨率、DPI、色彩空间（对齐引擎固定工作空间 sRGB scene-linear）、视图变换（对齐 IR 变换分级中的「视图级」）
* 绘制单位：逻辑坐标（引擎最终按 DPI 缩放，与 UI 层一致）

### 3.2 图元 / Primitives（数据记录）

* rect / rrect（圆角矩形，含各角半径）· ellipse · arc / pie / chord · line · path · text（文本块）· image（贴图，经资源句柄）
* 每个图元记录字段：几何参数 + paint 引用 + 逐项变换 + clip 引用（可空）
* 语义：不带任何"渲染状态"——同一条记录在任何后端/任何时刻重放，结果一致

### 3.3 Path 记录

* 命令序列（数据数组）：moveTo / lineTo / quadTo / cubicTo / arcTo / close 等；支持 fill 与 stroke 两种边界语义
* 数值不动点/精度约定：几何以 32 位浮点表达（引擎端以统一内核规格处理）；文本排版坐标同理

### 3.4 Paint（效果栈，不可变）

* 填充：实色 / 线性渐变 / 径向渐变 / 扫描渐变 / 图像平铺 /（后续扩展更高级着色器）
* 描边：线宽、端帽（butt/round/square）、连接（miter/round/bevel）、虚线（pattern + phase）
* 颜色变换：透明度、颜色矩阵滤镜
* 图像滤镜：模糊（radius）、阴影（offset+blur+color）、(P90 集合内有限扩展)
* 混合模式：标准有限集（src-over 默认、dst-over、multiply、screen、xor…），对齐引擎 §7 预编译组合空间
* 不可变：任何"修改"返回**新 Paint**（结构共享），旧引用恒有效 → key 稳定、缓存安全

### 3.5 变换与裁剪

* 变换：视图级（会话级，整帧共用）与逐项级（每图元独立）——与 IR key 分级一一对应（引擎 §4）
* Clip：几何裁剪，可嵌套（遮蔽范围为栈）；编译为引擎裁剪语义

### 3.6 图层 / Layer

* `saveLayer(区域, paint)` / `restoreLayer()`：显式标记图层边界 → 引擎 Frame Graph 离屏层（**离屏内存别名复用由引擎 §5 负责，API 层无感知**）
* 图层错误使用提示：嵌套过深/空区域等由诊断标号体系给 W 级提示（不阻断）

### 3.7 文本 / Text

* `Text` 记录：内容 + 字体句柄 + 字号 + 行高 + 对齐 + 换行规则；**排版结果**（字形布局、度量）随记录传入，字形形状的 GPU 化由引擎负责（引擎 §6 文本 GPU 化）
* 排版引擎独立为模块（见 §9 模块四），可单独替换

### 3.8 资源句柄 / Resource Handles

* `Image`、`Font` 等：引用计数句柄，经引擎资源管理（atlas / 预算 / LRU，引擎 §9）落地
* 句柄生命周期：库内管理；跨线程安全；失效访问 → 诊断错误（见 §8）

---

## 4. 双模式与 IR 接口 / Dual Mode & IR Interface

* `canvas.record(...)` → 构建 `DrawList`（IR 段，数据）：若干图元记录 + 元信息（key 前缀、视图变换、目标 Surface 参数）
* `canvas.submit(drawlist)` → 立即下发引擎（immediate 路径；内部为 record→submit 一步）
* `canvas.replay(drawlist)` → 已缓存绘制表再放（retained 重放；配合 UI 层骨架缓存，引擎 §4 只重放脏区 pass）
* IR 序列化：zd 底座可选（跨进程/缓存编排）
* 增量：UI 层以「dirty rect + 增量图元段」调用编码器，产出**增量绘制表段**（key 前缀表明归属子树，引擎只差分重放）

```text
// 语法样例按 tie 现行语法（p.7 已定）写作；本库不主张任何新语言特性，
// 歧义一律由 tie 既有语法规则裁决（详见 docs/plans/2026-09-12-tiu-api-impl.md §3）
let dl = canvas.record()
dl.rect(10, 10, 200, 40, paint.rounded(8).fill(theme.primary))
dl.text("hello", at(60, 40), font.body(16), align.center)
dl.save_layer(...); dl.path(stroke_path); dl.restore_layer()
canvas.submit(dl)          // immediate
canvas.replay(dl)          // 复用重放
```

---

## 5. 工作线程与生命周期 / Threading & Lifecycle

* 图元/Paint/DrawList 不可变 → 可在任意 worker 线程构建；完成后移交引擎线程
* `submit` 为所有权转移（move），杜绝重复提交
* 资源句柄引用计数：构建期与重放期计数自动维护；引擎换出（LRU）对 API 层透明
* 会话（Canvas）绑定单线程（对应窗口事件循环）；**离屏 Surface 的绘制可在 worker**（对齐引擎后台提交能力）

---

## 6. 与上下层契约 / Cross-layer Contract

| 方向 | 数据 | 说明 |
|---|---|---|
| UI 库 → 本库 | dirty rect + 增量图元（子树 key 前缀）| UI 只下"变了什么" |
| 本库 → 引擎 | 绘制表 IR（增量段 + 重放引用）| 唯一跨层通道，纯数据 |
| 本库 ↔ 资源 | 句柄与缓存引用 | 与几何隔离，独立生命周期 |

边界铁律同引擎文档 §10：层间只走数据（绘制表 / 脏矩形 / 事件轴独立），不穿越代码引用。

---

## 7. 错误模型 / Errors

* 遵循 tie 语言惯例（可检查结果，非异常流）
* 诊断类别：非法图元参数（越界/空数据）、资源句柄失效、非法图层配对（restore 无 save）、内部编码错误
* 输出：错误码 + 诊断标号（复用 tie 诊断标号体系 W/E 风格）；渲染层错误（真实 GPU 失败）转引擎侧诊断
* 原则：**编码期错误尽早暴露**（record 时校验），重放期不产生新语义错误

---

## 8. 验收基准 / Acceptance

| 指标 / Metric | 基准 / Baseline |
|---|---|
| gold IR | 给定绘制序列 → IR 字节与基准一致（gold 断言）|
| 双模式等价 | immediate 直接渲染 == retained 记录后重放（同 gold 图）|
| key 稳定性 | 未变子树的 key/IR 段不因其它子树变化而变（变化区隔离探针）|
| 线程安全 | worker 构建并发下 IR 结果与串行一致（无数据竞争探针）|
| 编码开销 | 普通图元记录编码 ≤ 内存拷贝量级（无锁、无分配于热路径）|

工具：gold IR 比较器、变化区隔离探针、并发构建探针（与引擎共用诊断工具线）。

---

## 9. 实现模块 / Module Roadmap

模块自底向上，每模块完成后即自验证：

* **模块一：对象模型** —— 图元/Path/Paint/Layer 数据记录 + 不可变构建（结构共享）；Paint 单测（创建/不变性/结构共享）
* **模块二：IR 编码器** —— 意图 → 绘制表记录；稳定 key 派生；gold IR 比较器落地（关键 key 稳定性探针）
* **模块三：双模式入口与会话** —— Canvas 会话、record/submit/replay、immediate 合成路径；双模式等价探针
* **模块四：文本排版** —— 字体句柄、度量、换行对齐，排版结果进 IR；gold 排版断言
* **模块五：资源句柄与缓存** —— Image/Font 句柄、引用计数、失效诊断；跨线程探针

依赖：tie 语言（自举生产工具链）。跨层契约在实施计划中**当场冻结**（`docs/plans/2026-09-12-tiu-api-impl.md` §2：IR/wire、增量段协议、资源句柄接口），各模块按 `§9` 顺序实现、每模块独立自验证；全部完成后与引擎「模块一」做 gold IR / 金图联调（计划 §1 终点验收 TP2）。

---

## 10. 风险与边界 / Risks & Non-scope

* **API 与 tie 语法演进** → 约定：样例按 tie 现行语法写作；本库不主张任何新语言特性，歧义由 tie 既有语法规则裁决（不产生新决策，见实施计划 §3）
* **与 UI 层差分协议** → 契约先于实现：增量段与 key 前缀协议在实施计划 §2 冻结（模块二 T2.3 产出即定稿，UI 库模块四按此对接，不"并行协商"）
* **资源生命周期跨层** → 句柄集中在资源模块；与引擎资源接口的契约在实施计划 §2 定稿（T5.2，冻结后修订只走版本表回写）
* **不在本库范围（职责归属，非挂起项）**：
  * 事件/输入与无障碍 → `docs/designs/tiu-event-system.md` 已定稿（本库不经过事件通道）
  * 平台窗口壳 → p.9.3.1 运行时底座（ROAD 已登记）
  * 纹理/字体后端存储与 LRU → 引擎 §9（本库只持有句柄）
  * 效果栈扩展 → 默认范围即 P90 集合（实色/渐变×3/图像平铺/透明度/颜色矩阵/模糊/阴影/标准混合集），不在集合内的组合由引擎 §7 降级拆分机制承载——**不设立"另行规划"的扩展集**

---

## 11. 附录 / Appendix

* 术语 / Terms：DrawList（绘制表段）· gold IR（基准 IR 断言）· 结构共享（persistent data structure，修改返回新记录、旧引用有效）
* 演进：本设计与引擎文档 §4/§10 互为引用；模块一实现结论反向修订对象模型（记入版本表）