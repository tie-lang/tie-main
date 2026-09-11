# tiu 事件轴设计 —— 输入事件 / 命中测试 / 焦点
*EN: tiu Event System Design — input events / hit-testing / focus*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（文档；本期只落到设计，不进入实现）
**依据** / Basis: `docs/designs/tiu-ui-widgets.md` §8（事件对接）· ROAD.md p.9.3.1（运行时底座：窗口/绘制/事件/资源）· `docs/designs/tiu-render-engine.md` §10（事件轴独立）
**关联** / Related: `docs/designs/tiu-drawing-api.md`（事件不进入绘制通道）· p.9.3.1（原生输入收取）
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Defines tiu's event axis — the input side of the framework,
> independent of the draw pipeline. The axis collects raw platform input
> (pointer / keyboard / scroll / touch / compositor), produces immutable event
> records with coordinates, runs hit-testing over UI-layer layout results, and
> routes events to focus / hover / gesture targets. Core decisions: (1) event
> records are immutable value data, timestamped and coordinates in one space
> (logical UI space); (2) hit-testing is a single read-only pass over cached
> layout rects — never runs during draw; (3) focus is a tree-level immutable
> state owned by the axis, shared into the UI layer's snapshot; (4) the axis
> runs on the event-loop thread, decoupled from frame rhythm (no per-frame
> event flush); (5) accessibility hooks are first-class, not an afterthought.
> **Design only — no implementation.**

---

## 1. 定位与边界 / Position & Boundary

事件轴是 tiu 的事实独立通道：**输入 → 事件记录 → 命中/路由 → 应用回调**；它不经过绘制表、不感知引擎、也不感知布局算法（只读取布局结果矩形）。

* **本轴负责**：原生输入收取（委托 p.9.3.1 运行时底座窗口部分）、事件记录化、命中测试、路由（hover/focus/gesture）、焦点状态、可访问性钩子
* **本轴不负责**：绘制/重绘触发（信号由 UI 层快照比较触发）· 布局/渲染（UI 层 / 引擎）· 输入法合成细节之外的一切

**与绘制/布局的关系**：事件消费**只读**布局结果；被其修改的状态进入 UI 层下一帧快照——事件与渲染通过「状态快照」解耦，无直接耦合。

---

## 2. 设计原则 / Design Principles

1. **事件即不可变数据** —— 每条事件是一条带时间戳、坐标系、目标上下文记录的不可变值；可记录、可回放、可测试（对浮点精度与多指场景友好）。
2. **坐标统一为逻辑空间** —— 原生（物理像素/窗口坐标）在收取时即换算为 UI 逻辑坐标（对齐全天候 DPI 语义）；命中测试与绘制天然同一坐标系。
3. **命中测试单趟只读** —— 命中 = 按绘制顺序（布局矩形 + 层序）的单趟查找，缓存布局结果；绝不在绘制中运行。
4. **焦点是轴内状态** —— 焦点树由事件轴持有（不可变快照），分享给 UI 层快照；键盘事件只路由到焦点链。
5. **与帧节奏解耦** —— 事件在事件循环线程处理、聚合、成批投递；不逐帧刷事件（无"每帧事件队列"），避免事件/渲染互锁。
6. **钩子优先（可访问性一等公民）** —— 事件记录保留语义字段（角色/标签/动作），供无障碍栈直接消费。

> EN: Events are immutable timestamped value records in logical UI space;
> hit-testing is one read-only pass over cached layout rects (never during
> draw); focus is axis-owned immutable state shared into UI snapshots; the axis
> runs on the event loop — decoupled from frame rhythm; accessibility hooks are
> first-class.

---

## 3. 事件模型 / Event Model

* 事件族 (Event kind)：
  * 指针：down / move / up / cancel（含笔压、悬停）；滚轮：scroll（含像素/行两级）
  * 键盘：keyDown / keyUp / textInput（转 IME 合成流）
  * 触控：touchDown / touchMove / touchUp（多点，事件组）
  * 合成：focusIn / focusOut · hoverChange · accessibilityRequest
* 每条记录：`kind + 时间戳 + 位置（逻辑空间） + 修饰键 + 目标候选（由命中阶段填充） + 上下文快照引用`
* 运动轨迹：原始点流 → 手势层聚合（tap / drag / longPress / pinch）→ 语义事件（如 click = tap 命中+时间窗）

---

## 4. 命中测试 / Hit-testing

* 输入：布局矩形（UI 层 §4 布局结果）+ 绘制层序
* 过程：倒序查找（顶层最优先）→ 命中判定（矩形内含 + 命中区域裁剪，供控件细分如圆角/点击区）→ 产出「目标 Element + 折叠的命中路径」
* 缓存：布局矩形版本号关联——布局未变则命中使用缓存，不重算
* 频率约束：只在事件到达时运行；无事件无命中开销

---

## 5. 路由与焦点 / Routing & Focus

* **路由次序**：捕获（root → leaf）→ 目标 → 冒泡（leaf → root，可阻止）
* **焦点**：
  * 焦点树状态（当前焦点元素链）为事件轴持有的不可变快照
  * 键盘事件沿焦点链递送；`tab`/方向键导航由轴提供内建策略（可被应用策略替换）
  * 焦点变化生成为 `focusIn/focusOut` 语义事件 → 进入 UI 层快照 → 触发重绘依赖（如焦点描边）
* **悬停**：由 move 事件驱动，命中变化才发 `hoverChange`（低噪声）

---

## 6. 线程与节奏 / Threading & Cadence

* 事件循环线程收取原生输入 → 记录化 → 成批投递（一批事件可能对应多帧时间，但不会跨帧撕裂状态）
* 状态立即可见：事件处理后更新焦点/悬停状态；**渲染侧在下一帧快照看到**（无信号抢占）
* 快照提交：UI 层以快照比较触发重绘（差分通道），事件轴不主动唤醒帧

---

## 7. 可访问性 / Accessibility

* 钩子：事件记录携带语义字段（角色、标签、值、动作集）
* 输出：`accessibilityRequest`（读屏/旁白查询）→ 树遍历返回语义快照
* 原则：控件默认可从其 props 获得语义字段（UI 层 §3 覆盖），缺失则事件轴提供缺省推断

---

## 8. 验收基准 / Acceptance

| 指标 / Metric | 基准 / Baseline |
|---|---|
| 不可变性 | 事件记录可回放重放（记录/回放一致性探针）|
| 命中性能 | 单趟命中 O(树深)；布局未变 → 缓存命中零重算 |
| 路由正确性 | 捕获→目标→冒泡 次序断言 + 阻止传播生效 |
| 焦点一致性 | 焦点快照与应用侧一致（状态隔离探针）|
| 节奏解耦 | 批量投递下状态无撕裂（快照原子性探针）|
| 无障碍 | 语义字段完整率探针（关键控件 100%）|

工具：事件记录/回放器、命中缓存探针、快照原子性探针。

---

## 9. 实现模块 / Module Roadmap

* **模块一：事件记录与收取** —— 原生输入 → 不可变记录（坐标换算）；记录/回放器
* **模块二：命中测试** —— 布局矩形 + 层序单趟命中、分区判定、缓存版本控制
* **模块三：路由与手势** —— 捕获/冒泡、gesture 聚合（tap/drag/pinch）、阻止传播
* **模块四：焦点系统** —— 焦点树、内建导航、焦点语义事件
* **模块五：无障碍钩子** —— 语义字段收集与 `accessibilityRequest` 响应

依赖：UI 层模块六（命中对接）与模块四（焦点）联调；原生收取依赖 p.9.3.1 窗口部分（先行约定接口）。

---

## 10. 风险与边界 / Risks & Non-scope

* **事件/渲染时序竞争** → 缓解：状态经快照单向流动，轴不唤醒帧；快照原子性探针兜底
* **多指/手势复杂性** → 缓解：原始点流与手势层分离，聚合可替换策略
* **布局矩形失效** → 缓解：矩形版本号关联缓存（布局一改，命中缓存失效）
* **本期不做**：IME/输入法编辑器实现（只转合成流）、无障碍平台适配器物理接入、平台级手势冲突策略细节

---

## 11. 附录 / Appendix

* 术语 / Terms：命中路径（hit path，目标及其祖先链）· 焦点链（focus chain）· 逻辑空间（logical UI space，DPI 归一坐标系）· 手势聚合（gesture recognition，原始点流 → 语义事件）
* 演进：与 UI 库（§8）互引用；模块一实现结论反向修订事件记录定义（记入版本表）