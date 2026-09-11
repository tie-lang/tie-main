# tiu UI 库设计 —— 三层顶层：控件 / 布局 / 主题 / 差分
*EN: tiu UI Library Design — the top layer: widgets / layout / theme / diff*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（文档；本期只落到设计，不进入实现）
**依据** / Basis: `docs/designs/tiu-drawing-api.md`（绘制 API 库，本层唯一消费接口）· `docs/designs/tiu-render-engine.md`（引擎，本层不感知）· ROAD.md p.9.3.2（组件树与组合式布局框架）
**关联** / Related: `docs/designs/tiu-event-system.md`（事件轴，独立通道）· p.9.3.1（运行时底座：窗口/绘制/事件/资源）
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Defines tiu's UI layer — widgets, layout, theme, animation and
> dirty-rect differencing. It is the top of the three-layer tiu (Engine /
> Drawing API / UI). The UI layer consumes ONLY the drawing API: it compiles
> widget state into incremental draw-list segments (subtree-keyed) and pushes
> them down; it never touches the engine or GPU. Core decisions: (1) a retained
> scene tree with immutable-ish per-frame state snapshots; (2) layout is a
> constraint-propagation pass separate from paint; (3) the subtree key from the
> IR layer is the single differencing primitive — unchanged subtrees skip encode
> and replay from skeleton cache; (4) theme is a typed token system resolved
> before layout; (5) animation is a declarative clock fed to the tree, not curl
> per-frame mutation. **Design only — no implementation.**

---

## 1. 定位与边界 / Position & Boundary

顶层。输入：应用状态 + 窗口/帧节奏；输出：**增量绘制表段**（经 API 库编码）与命中/焦点信息（经事件轴）。

* **本层负责**：组件树（保留树）、布局、样式/主题、动画、脏矩形差分、与事件轴对接（命中测试输入）
* **本层不负责**：任何绘制/光栅/GPU（引擎）· 绘制意图编码（API 库）· 窗口与输入原生收取（运行时底座 p.9.3.1）· 平台壳

**依赖方向**（只依赖下游，绝不反向）：

* UI 库 → API 库（增量段编码）→ 渲染引擎
* UI 库 → 事件轴（命中/焦点数据流，旁路，不走绘制），与 API/引擎无关

---

## 2. 设计原则 / Design Principles

1. **保留树 + 快照 → 差分** —— 组件树是保留（retained）的；每帧以「状态快照」驱动；未变子树直接复用（骨架缓存），变化区转换化为增量段。**差分原语只有一种：IR 子树 key**（API 库 §4 自动派生）。
2. **布局与绘制分离** —— 布局是纯约束传播（只算尺寸/位置，不产绘制数据）；绘制在布局结果之上按快照执行。两趟独立，可只跑其一。
3. **控件即数据** —— 单个控件是「参数记录（props）+ 构建函数」，不持可变全局；重建是廉价的（重建 assets 由 key 保护 → 不触发重绘）。
4. **主题先行（token 化）** —— 颜色/字号/间距/圆角全部走类型化 token，声明在构建前解析进绘制段；控件不硬编码视觉量。
5. **动画是声明式时钟** —— 动画以「起始值 + 目标值 + 曲线 + 时长」描述，由统一时钟驱动求值；动画不产生逐帧命令流，只更新快照字段（key 感知变化）。
6. **对引擎零感知** —— UI 层不 import 任何 GPU/帧图类型；一切渲染语义在 API/引擎层闭合。

> EN: retained tree + per-frame state snapshots; layout = pure constraint
> propagation decoupled from paint; widgets are props+build functions with cheap
> rebuilds (key-guarded, no repaint on reuse); tokenized theme resolved before
> layout; declarative animation clocks; zero awareness of the engine below.

---

## 3. 组件树模型 / Widget Tree

* `Element`：树节点（组合单元，对应 UI 语义，如 Button/Row/TextInput）
* 每个 Element 携带：
  * `props`（参数记录，不可变）——本帧外观/行为参数
  * `children`（子 Element 列表或懒构建描述）
  * `key`（子树差分键；由 API 库 IR 编解码器在构建期自动派生/继承）
  * `layout`（缓存的本帧尺寸/位置矩形）
* 状态快照：每帧由应用/框架构建新 props 传入（数据驱动），树结构增量复用（同类同 key → 复用节点，仅更新 props）

**构建与复用** · 三类节点：
* 同 key 同类型 → 复用节点（props 更新，脏时才编码）
* 同 key 不同类型 → 替换节点（重建子树）
* key 新出现 → 新节点（首编码）

---

## 4. 布局管线 / Layout Pipeline

* **约束传播**：父给子「约束（min/max 宽高）」，子返回「尺寸」；单趟 (`measure → layout`)；布局结果写回节点矩形
* **特性**：
  * 纯函数式：同样约束+props → 同样结果（可缓、可测）
  * 宽松 vs 固定两种约束模式；百分比/内容自适应/固定尺寸三类约定
  * 每帧可只对 dirty 子树重跑布局（脏矩形传播复用同一 diff 通道）
* **绘制后置**：布局结果 + props → 快照 → API 编码器产出该子树增量绘制段

---

## 5. 主题与样式 / Theme & Styles

* **Token 体系**：`颜色（色板+语义色）/ 间距 / 字号与行高 / 圆角 / 阴影（预设模糊+偏移）/ 动效曲线时长` —— 类型化并限定枚举（对齐引擎 §7 预编译 shader 组合空间，避免组合爆炸）
* **解析时机**：主题在布局前解析进 props（控件构建时按 token 取值）；绘制段中直接带最终值（引擎无需知道主题）
* **换肤**：主题对象整体替换 → 全树 key 变化 → 一次全局增量（低成本代表性变化）

---

## 6. 动画与时钟 / Animation

* 动画描述：`(目标属性 token, 起始值, 目标值, 曲线, 时长, 延迟)`；注册于动画时钟
* 时钟：单调帧驱动，逐类动画求值 → 写回快照字段（key 值变化 → 该段重编码）
* 隐式动画：控件上声明「transition 规则」由框架生成
* **零命令流**：动画不产生 DrawList 追加，只改快照 → 差分通道自然承载

---

## 7. 差分契约 / Diff Contract

* **原语**：子树 key（派生自 API 库 IR key 分级）——节点 key 段 + 变化位
* **流程**：
  1. 构建快照（主题解析 → 布局 → props 收敛）
  2. 比较上帧快照 key → 生成「脏根集合 + dirty rect」（沿树向上合并）
  3. 仅脏子树调 API 编解码器 → 增量绘制表段
  4. 骨架缓存：未变子树沿用（API 库 replay / 引擎只重放脏 pass）
* **验收探针**：变化区隔离——改一处控件，其余子树 key 与 IR 段字节不变（API 库 §8 同款探针，这里加"整树级"断言）

---

## 8. 与事件轴对接 / Event Hook

* 事件轴（`docs/designs/tiu-event-system.md`）交付：指针/键盘 等事件流（带坐标）
* UI 层消费：**命中测试**（按布局矩形与绘制顺序反查 Element）→ 焦点/悬停/点击路由
* 约束：事件不进绘制差分通道；命中测试只读布局结果

---

## 9. 验收基准 / Acceptance

| 指标 / Metric | 基准 / Baseline |
|---|---|
| 差分正确性 | 单节点变化 → 仅该子树重编码（整树 key 隔离探针）|
| 布局确定性 | 同约束+props → 同尺寸（gold 布局断言）|
| 重建成本 | 静态帧重建（快照相等）→ 零编码/零重绘（骨架命中）|
| 帧车道 | 动画与输入在帧节奏内完成；无逐帧命令流探针 |
| 主题换肤 | 全局换肤 → 一次增量段提交（不逐控件）|

工具：gold 布局/快照比较、变化区隔离探针（接入 API 库与引擎的探测线）。

---

## 10. 实现模块 / Module Roadmap

模块自底向上，每模块完成即自验证：

* **模块一：Element 树与快照** —— 节点模型、构建/复用三类规则、快照比较与脏集合；隔离探针
* **模块二：布局引擎** —— 约束传播、measure/layout 两趟；gold 布局断言
* **模块三：主题 token 与解析** —— token 表、解析进 props、换肤路径；组合空间校准（对齐引擎 shader 集）
* **模块四：差分→API 桥** —— 脏集合 → 增量段编码（消费 API 库模块二/三）；整树 key 隔离探针
* **模块五：动画时钟** —— 声明式动画、隐式 transition；帧车道探针
* **模块六：命中与焦点对接** —— 读布局结果命中 Element、路由到事件轴

依赖：API 库模块一/二/三先落地（对象模型/编码器/双模式）；本层不直接依赖引擎。

---

## 11. 风险与边界 / Risks & Non-scope

* **diff 协议与 API 库耦合** → 缓解：差分原语单一（子树 key），协议在 API 库模块二定稿（与 UI 层并行协商）
* **布局性能**（暴力约束重跑）→ 缓解：脏子树局部布局 + 纯函数缓存；模块二探针先行
* **动画与撤销/惊喜帧** → 缓解：动画求值幂等（同输入同输出），时钟单调
* **本期不做**：具体控件库（Button/TextInput/… 明细，随实现积累）、无障碍完整规范（事件轴提供钩子）、国际化/换行细则（API 库排版模块扩展）

---

## 12. 附录 / Appendix

* 术语 / Terms：快照（snapshot，每帧由 props 构建的状态）· 脏集合（dirty set，key 变化节点集）· 约束传播（父→子约束、子→父尺寸的单趟布局）
* 演进：与 API 库（§4 增量段）、事件轴（§8）互引用；模块一实现结论反向修订节点模型（记入版本表）