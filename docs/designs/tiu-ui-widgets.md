# tiu UI 库设计 —— 高性能 · 低内存 · 易用
*EN: tiu UI Library Design — high-performance, low-memory, easy-to-use*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（文档；本期只落到设计，不进入实现）
**依据** / Basis: `docs/designs/tiu-drawing-api.md`（绘制 API 库，本层唯一消费接口）· `docs/designs/tiu-render-engine.md`（引擎，本层不感知）· ROAD.md p.9.3.2（组件树与组合式布局框架）
**关联** / Related: `docs/designs/tiu-event-system.md`（事件轴，独立通道）· `docs/plans/2026-09-12-tiu-api-impl.md`（增量段协议 T2.3 冻结件，本层按此消费）
**版本** / Version: v0.3（2026-09-16 用法定案五议题收敛：Elem=enum 判别和 + payload 白名单二批 · 事件批次自动帧 · lazy_list 键行生成器 · 回调等待 fn 捕获定稿 · 不可变 props + 链式覆写，新增 §15）· v0.2（2026-09-12 依三支柱方针重构：高性能/低内存/易用贯穿全篇，内嵌实施任务清单闭环）· v0.1 概要

> EXEC BRIEF: Defines tiu's UI layer around three pillars — **performance**
> (differential update in O(changed), localized layout, zero-allocation hot
> path), **low memory** (compact SoA elements, structurally-shared props,
> unified cache budgets), **ease of use** (declarative pure-function widgets,
> complete defaults, diagnostic codes, typed props). Every mechanism below is a
> trade-off under these three; the arbitration order: performance and memory
> never compromise — ease of use is paid back through API shape (defaults,
> diagnostics) and must never introduce performance anti-patterns (per-frame
> allocation, whole-tree rebuild). The differencing primitive is a **two-tier
> key**: a UI structural key (O(1) version-number compare) plus the IR content
> key (hash, recomputed only on change). The only new contract frozen here is
> the UI structural key (§8); the incremental-segment protocol is consumed from
> the API plan T2.3 as-is. **Design only — no implementation.**

---

## 1. 定位与边界 / Position & Boundary

顶层。输入：应用状态 + 窗口/帧节奏；输出：**增量绘制表段**（经 API 库编码）与命中/焦点信息（经事件轴）。

* **本层负责**：组件树（保留树）、布局、样式/主题、动画、脏矩形差分、焦点视觉状态、滚动
* **本层不负责**：任何绘制/光栅/GPU（引擎）· 绘制意图编码（API 库）· 窗口与输入原生收取（p.9.3.1）· 排版计算（API 库模块四）· 事件路由本体（事件轴）

**依赖方向**（只依赖下游，绝不反向）：

* UI 库 → API 库（增量段编码）→ 渲染引擎
* UI 库 → 事件轴（命中结果消费，旁路），不进入绘制通道

---

## 2. 三支柱与裁决矩阵 / Three Pillars & Arbitration

| 支柱 | 含义 | 主要机制 | 冲突裁决 |
|---|---|---|---|
| 性能 | 帧循环成本 O(变化)，不随全树规模增长 | 两层 key 差分（§8）、布局局部化（§5）、零分配热路径（§3/§7）| 性能与内存**不妥协** |
| 低内存 | 常驻内存有界、可预测，缓存全部受预算约束 | 紧凑 Element（§3）、结构共享 props（§3）、统一缓存预算（§8/§9）| 内存与性能同级优先 |
| 易用 | 声明式、零生命周期焦虑、默认即用、报错可行动 | 纯函数组件 + 组合 API（§4）、默认主题（§6）、诊断标号（§12）| 易用靠 API 形态补足，**不得引入性能反模式** |

**裁决顺序**：性能 → 内存 → 易用。示例裁决：
* 交互期动画优先级低于帧时间 → 动画按活跃集预算降采样（§7），不以开发便利换帧稳定
* props 一律只读结构共享，不提供可变写入（避免隐含全树失效）；开发体验由组合 API 与默认值兜底

> EN: arbitration is performance → memory → ease of use. Ease of use is paid
> back through API shape (defaults, diagnostics, declarative composition) and
> must never cost per-frame allocation or whole-tree rebuilds.

---

## 3. 组件树模型 / Widget Tree（性能 + 内存核心）

### 3.1 骨架与快照分层

* **stable 骨架**（跨帧复用，不改写）：`type + slot + 布局矩形 + 父/长子/兄弟指针`；每帧除尺寸/位置外只读
* **帧快照**（当前帧数据，可替换）：仅两个引用 `props` 与 `版本号`；快照由**双缓冲 arena** 管理——帧间交换旧/新缓冲，回收旧快照零碎片、零逐元素释放
* 生命周期：骨架 = 结构身份（key 主体）；快照 = 值（props）载体；二者分离使"树比较"只在骨架层进行

### 3.2 紧凑存储（内存支柱）

* 骨架按 **SoA（结构数组）** 布局：类型数组、槽位数组、矩形数组、版本号数组；树遍历按 DFS 序连续内存，对缓存友好
* 单元素均摊内存目标：骨架 < 64 B/元素（SoA 下），快照 = 两个引用
* 无逐元素堆分配：arena 批量供给；props 采用**结构共享**（persistent），变更返回新引用，旧快照帧内安全

### 3.3 状态单源

* 应用状态（应用持有）→ 纯构建函数产 props → 树；UI 层无隐式可变共享
* 对比依赖：帧快照比较只看**版本号**（props 每次变更单调 +1），不是逐字段比较（性能刀刃）

---

## 4. 构建与复用 / Build & Reuse（易用核心）

### 4.1 声明式组合 API（tie 形态）

```text
// 示意：声明式、纯函数、无样板（语法以 tie 现行惯例为准，见 API 实施计划 §3）
let ui = view.column({
  view.text("标题", t.font.title(20)),
  view.button("确定", action),
  view.row({ view.icon(img), view.text("说明", t.text.caption) }),
})
```

* 组合优于继承；无手动 `add_child` / `set_attr`；每帧由应用构建新 props，框架管复用
* 类型安全：props 为具名记录，构建器与 token 均有静态检查

### 4.2 三类复用（同 slot 规则）

* 同 type + 同 slot → 复用骨架（仅换快照；脏才编码）
* 同 slot 异 type → 替换骨架（重建子树）
* 新 slot → 新建骨架
* **slot 化约束**：兄弟节点以槽位标识定位，**不靠闭包捕获**——避免"编辑器里改一行导致整树 key 失效"的经典痛点

### 4.3 反模式内建拦截（易用防呆）

| 反模式 | 内建对策 |
|---|---|
| 每帧 `new` props | 结构共享 + 双缓冲 arena，热路径零分配 |
| 全树重建 | 差分为 O(变化)；构建函数仅执行脏子树 |
| 闭包捕获导致全失效 | 强制 slot 化定位 |
| 忘写 key | 无需手写——slot 与版本号自动派生 |
| 主题硬编码 | 控件零硬编码，token 未提供时取默认主题 |

---

## 5. 布局引擎 / Layout（性能核心）

* **单趟约束传播**：父给子约束 [min,max] → 子返回尺寸 → 父定位；measure/layout 合并为一趟后置
* **三档约束**：宽松（自适应，默认）/ 紧凑（内容定尺寸）/ 固定（显式）；比例约束（百分比）基于父尺寸完成后再定
* **局部重排**：仅脏子树重跑；静态子树整块布局缓存（命中零重算）；沿脏矩形上卷合并
* **低内存**：约束与结果用 DFS 复用 buffer（栈式），无逐元素分配
* **幂等**：同约束 + 同 props → 同布局（gold 断言）；布局结果不回写 props（只写骨架矩形）
* **性能刀刃**：布局是纯函数且按"约束哈希 + props 版本号"做缓存——同内容重复帧直接命中

---

## 6. 主题与样式 / Theme & Styles（易用 + 内存）

* **token 单例**：一套主题对象全树共享；解析产物（最终颜色/宽度/圆角）为共享常量，零复制进绘制段
* **三层覆写**：主题 token（全局）→ 组件默认（控件级）→ 实例 inline（per-instance 覆写并入 props，仅脏实例影响 key）
* **默认主题内置**：无主题配置可直接运行（易用最低门槛）
* **换肤** = 替换主题单例 + 全局主题版本号 +1 → 全树结构 key 变 → **一次性**全量增量（不逐控件处理）
* **组合空间约束**：token 全部限定枚举，对齐引擎 §7 预编译 shader 组合空间（防组合爆炸）

---

## 7. 动画与时钟 / Animation（性能预算）

* **声明式动画**：`属性 token + 起始 + 目标 + 曲线 + 时长 + 延迟`；注册进帧时钟
* **活跃集预算**：动画数量设上限；超出时低优先级动画降采样（降帧求值）或完成——**帧时间不被动画撑破**
* 时钟单调 → 求值幂等（撤销/回放安全）；动画结束即出集释放（内存）
* **零命令流**：动画只写依赖属性的 props 版本号 → 差分通道自然承载（不产生逐帧绘制表追加）

---

## 8. 差分契约 / Diff Contract（性能核心：O(变化)）

### 8.1 两层 key（本设计唯一新增冻结契约）

* **UI 结构 key**（O(1) 比较）：`DFS 序 + type + slot + props 版本号`——比较 = 版本号差，**不是哈希**
* **IR 内容 key**（哈希）：`op · geo-hash · paint-hash · 变换分级`（API 库 §4）——**仅当**结构 key 变化时由 API 编解码器重算
* 效果：静态帧（快照相等）比较成本 O(深度)，编码为零；变化帧成本 O(变化子树)

### 8.2 脏集合位标记（性能 + 内存）

* 树以 DFS 序号数组存储 → 脏标记 = **位图**（O(1) 标注）；dirty rect 沿父链上卷合并（O(深度)）
* 位图为帧复用（arena 侧），不逐帧分配

### 8.3 流程

1. 构建快照（主题解析 → 布局 → props 版本号收敛）
2. 结构 key 比较 → 脏节点位图 + 脏矩形
3. 仅脏子树调 API 编解码器 → 增量段（**消费 API 实施计划 T2.3 冻结件**：子树 key 前缀 + dirty rect）
4. 骨架缓存：未变子树 IR 段直接重放（引擎只重放脏区 pass）

### 8.4 缓存预算（内存支柱）

* 骨架缓存段总量上限（LRU 换出）——未变子树缓存不得无界增长
* 修订：§8.1 结构 key 约定为本层冻结契约；修订走版本表回写（引擎/API 侧各自确认）

---

## 9. 文本 / 多语言 / 滚动（性能边角）

* **文本**：消费 API 库模块四排版输出（布局记录进 IR，UI 层不产字形）；文本排版缓存按 LRU 预算（同文本同 style 复用）
* **多语言**：文案 = 字符串资源表（文案 key）；控件结构不判断语言；RTL 以**布局镜像**（起始边翻转）在布局层闭合，不引入独立 bidi 引擎（复杂 bidi 细化归 API 排版模块，UI 只消费其结果）
* **滚动**（性能刀刃）：滚动容器 = clip 裁剪区 + 内容整体偏移——内容偏移是**变换级**变化（引擎视图变换分级支持），同内容滚动时静态子树骨架缓存**满命中**，不重编码内容段，只更新 clip 段

---

## 10. 焦点 / 键盘 / 命中 / 事件对接

* 焦点树由事件轴持有（事件轴文档 §5）；UI 层只挂 hover/focus/tab **视觉状态**（= props 版本号驱动，天然进差分）
* 键盘导航 tab 序 = DFS 序（免费获得，与 SoA 布局一致）
* 命中测试消耗布局结果矩形（事件轴单趟只读）；事件不进差分通道
* 滚动命中：命中结果在滚动偏移上平移（O(1)），不重布局

---

## 11. 三支柱验收基准 / Acceptance

| 支柱 | 指标 / Metric | 基准 / Baseline |
|---|---|---|
| 性能 | 静态帧 | 重建（快照相等）→ 零编码零重绘，树比较 O(深度) |
| 性能 | 差分 | 单节点变化 → 仅该子树重编码（整树隔离探针）|
| 性能 | 布局 | 单节点变化只重排该子树；静态子树缓存命中零重算 |
| 性能 | 帧车道 | 动画/输入在帧节奏内，动画预算生效（无撑破帧时间）|
| 内存 | 元素 | 骨架均摊 < 64 B/元素（SoA 探针）|
| 内存 | 缓存 | 骨架、文本、布局缓存水位收敛于预算区间 |
| 内存 | 热路径 | 帧循环零分配（arena/位图复用探针）|
| 易用 | 门槛 | 默认主题可运行；无 key 手写；诊断标号 W/E 可行动 |
| 一致性 | gold | 与 API 库联调：绘制表 → 引擎 → 帧 gold 图 ≤1/255 |
| 一致性 | 换肤 | 全局换肤 = 一次增量段提交（不逐控件）|

工具：整树隔离探针、frame allocation 探针、gold 布局/快照比较器（接入 API 库与引擎探测线）。

---

## 12. 诊断标号 / Diagnostics

* 复用 tie 诊断标号体系（W/E）：
  * W 级：动画预算降采样提示 · 布局约束矛盾（宽松与固定冲突取宽松）· 深层嵌套（>64 层建议拆解）
  * E 级：非法 slot（同 slot 异 type 且无替换策略）· 循环依赖布局 · 未知 token
* 原则：编码期尽早报，重放期零新错误；提示含修正动作（易用）

---

## 13. 实施任务清单（内嵌闭环，不另出实施计划文档） / Task List

契约沿用 API 实施计划 §2（增量段 = T2.3 冻结件；IR/wire = T2.1）；**唯一新增冻结 = §8.1 UI 结构 key**。每任务单提交、模块完成即自验证：

* **模块一：骨架/快照/arena** —— SoA 骨架、双缓冲快照、帧位图；帧分配零探针
* **模块二：构建与三类复用** —— 声明式组合 API、slot 定位、替换/新建规则；复用率与首批控件（Button / Text / Row / Column / Scroll / ListView(lazy_list) / TextInput / Image）单提交交付；控件动作参数位冻结策略见 §15.4
* **模块三：布局引擎** —— 单趟约束传播、三档约束、局部重排 + 静态子树缓存；gold 布局断言
* **模块四：主题 token 与解析** —— token 单例、三层覆写、默认主题、换肤路径；组合空间对齐
* **模块五：差分桥** —— UI 结构 key → 脏位图 → 增量段（消费 API T2.3）；整树隔离探针
* **模块六：动画时钟** —— 声明式动画、活跃集预算、降采样；帧车道探针
* **模块七：滚动 / 焦点 / 文本消费** —— clip+偏移滚动（骨架命中探针）、焦点视觉状态、排版缓存 LRU；帧调度语义（事件批次自动帧 / request_frame / 空闲零帧，§15.2）
* **终点验收**：§11 全项探针 + 与 API 库联调 end-to-end gold

依赖：API 库模块一/二/三（对象模型 / 编码器 / 双模式）+ 事件轴定稿；本层不直接依赖引擎。

---

## 14. 范围归属（非挂起项） / Scope Ownership

* 具体控件库 → 本章模块二随首批控件交付（明细属实施产物，非"另行规划"）
* 无障碍钩子 → `docs/designs/tiu-event-system.md` 已定稿（本层只挂视觉状态）
* 排版引擎 → API 库模块四（已计划）
* 窗口/输入收取 → p.9.3.1 运行时底座（ROAD 已登记）
* 复杂 bidi 细化 → API 排版模块扩展（UI 层消费其布局镜像结果）

---

## 15. 用法定案（2026-09-16 五议题收敛）/ Usage rulings (five topics, 2026-09-16)

> 用法侧五个悬置议题经讨论收敛为本节定案；每条含定案、依据与否决记录。
> 语言档依赖（p.8.1.8 / p.9.11.22）随本节登记进 ROAD。
> EN: The five usage-side open topics converge here; each ruling carries its
> basis and rejected alternatives. Language-track dependencies (p.8.1.8 /
> p.9.11.22) are registered into the ROAD alongside.

### 15.1 Elem 表示（议题 1 定案）

* `Elem` = **enum 判别和**（Rust 风格 ADT 已落地：带载荷构造 / switch tag 判别 / 泛型全通）。变体示意：`Text(TextProps) · Button(ButtonProps) · Row(table<Elem>, LayoutProps) · Column(…) · Scroll(…) · TextInput(…) · Image(…)`——payload 结构随模块二冻结。
* **依赖语言档 p.8.1.8**：payload 白名单二批放开 **struct / fn**（一批 f64/table<T>/map<V>/string 已落，p.8.1.7），附 `table<Elem>` 自引用递归探针（enum 作表元素已证、enum 作 struct 字段已证，自引用待证）与 i64/i128 解构确认。
* 过渡期：`table<any>` + 运行时 kind 校验；控件构造签名不变，白名单落地换表示不动应用代码。
* 否决记录：统一 struct Elem（kind + 全 props 内嵌——每个 Elem 背全部控件字段，内存/缓存劣）；裸 `table<any>` 定案（静态安全全失、每帧装箱）。

*EN: Elem = payload enum (ADT already landed). Depends on p.8.1.8 whitelist batch 2 (struct/fn payload + recursive table<Elem> probe); table<any> as interim with unchanged constructor signatures. Rejected: unified struct Elem (carries all widgets' props), any-only representation (no static safety, per-frame boxing).*

### 15.2 帧调度（议题 2 定案）

* 事件批次处理完 → UI 层**自动排一帧**（差分 O(变化)、静态帧零编码，多排不亏）；`ui.request_frame()` 显式出口（后台线程/定时器，经事件循环投递）。
* 动画时钟活跃期自驱节奏；**空闲零帧**——不做连续 60fps 空转（功耗纪律，对齐 §7 活跃集预算哲学）。
* 状态归应用（§3.3 不动摇）：框架不关心状态住在哪，只认「帧函数 + 变更后重算」；不做 tiu 侧 Signal/Store。

*EN: auto-frame per event batch + explicit request_frame escape; the animation clock drives its own cadence; zero idle frames (no 60fps spinning); app-owned state per §3.3 — no framework-side signals/stores.*

### 15.3 变长列表（议题 3 定案，B+A 结合）

* `ui.lazy_list(count, rows)`：count = 总行数（i64，数据驱动）；rows = **键行生成器**，`yield RowSlot(key: string, elem: Elem)`——生成器写法之顺（B，yield 惰性 p.9.11.15 现货）+ 显式 count 与稳定键之魂（A，对账与随机定位）。
* `RowSlot` 为普通 struct 表元素（**不涉 payload 白名单**；enum 作 struct 字段已证）；键与行同源单产，无平行生成器同步负担。
* 对账按 key：新行建骨架 / 消失行回收 / 未变行只换快照——位置漂移不触发重建（「无需手写 key」承诺范围 = 静态树；动态列表恰为例外，本控件即例外出口）。
* 惰性拉取窗口 = 视口 ± overscan（可配）；滚动 = 换窗 + 内容偏移（§9 变换级，静态子树骨架缓存满命中）。
* 语义约束：count 与产出数不一致 → E；key 重复 → E；`scroll_to(i)` 顺序拉 O(N)（文档明示；将来可加 height_hint 参数位优化常跳场景）。
* 否决记录：纯位置生成器（键弱、跳转 O(N) 全占）；虚拟化后置（列表最常见控件，欠债必还）。

*EN: ui.lazy_list(count, rows) — generator yields RowSlot(key, elem) pairs: generator ergonomics (B) with explicit count and stable keys (A). Reconciliation by key; lazy window = viewport±overscan; count/keys mismatches are E diagnostics; scroll_to is O(N) sequential by contract. Rejected: positional-only generators, deferred virtualization.*

### 15.4 回调冻结策略（议题 4 定案）

* **控件动作参数位冻结，等待 tie fn 捕获语义定稿**（新语言档 **p.9.11.22**：fn 值捕获规则——安全区捕获面 / 可变捕获标注 / 与事件循环线程的交互）。
* 定稿前控件 API 不含 action 形参：Button 首批交付时动作位留待补，或以可后填 props 槽位冻结结构。
* Msg 消息值方案（`enum Msg` + 单点 update）搁置不立项——fn 捕获定稿后如仍需零捕获形态（录制回放/测试）可再评。

*EN: action parameters stay unfrozen until tie's fn-capture semantics land (new p.9.11.22: safe capture surface / mutable-capture annotation / event-loop-thread interaction). Msg-value alternative shelved, re-evaluable for record/replay needs.*

### 15.5 特殊属性/自定义属性（议题 5 定案）

* 三类分清：**框架语义字段**（focusable / tab 序 / a11y 角色·标签·值·动作 / test_id / hit 内边距——事件轴 §7 一等公民）/ **布局约束**（expand / margin / 对齐——§5 三档约束的表达载体）/ **真自定义**（应用私有/平台穿透）。
* **不可变 props + 链式覆写**：对齐 drawing-api §3.4 Paint「任何修改返回新引用（结构共享）」既有裁决——控件 props 内嵌 `Common`（上述语义字段与布局约束全集，默认值齐），修饰符 `with_*` 返回新值：`ui.text("标题", t.font.title(20)).a11y("计数器标题").expand(1)`。
* 修饰链进差分：只动 props 版本号，零命令流（对齐 §7 零命令流纪律）。
* 自定义属性**不开 map 后门**：自定义控件 = 组合内置控件 + 自有 props struct（§4.1 组合优于继承）；平台穿透需求走版本表立项。
* Common 内嵌依赖白名单二批（同 15.1）。

*EN: three prop classes (framework semantic fields / layout constraints / truly custom). Immutable props + with_* modifier chain mirroring the Paint structural-sharing ruling; Common struct embedded with full defaults; modifier chains ride the diff via props versioning; no map backdoor for custom props — composition instead. Depends on whitelist batch 2 (as 15.1).*

### 15.6 语言档依赖汇总

* **p.8.1.8** enum payload 白名单二批：struct / fn payload + 递归 `table<Elem>` 探针 + i64/i128 解构确认——15.1/15.5 受益；与 p.8.1.7 一批同动机（ECS 组件标记/事件类型同族）。
* **p.9.11.22** fn 值捕获语义白名单：安全区捕获面 / 可变捕获标注 / 事件循环线程交互——15.4 等它。

*EN: two language-track items registered: p.8.1.8 (payload whitelist batch 2) serving 15.1/15.5, and p.9.11.22 (fn capture semantics) serving 15.4.*

---

## 16. 附录 / Appendix

* 术语 / Terms：骨架（stable skeleton，跨帧复用的结构身份）· 快照（per-frame props 载体）· 双缓冲 arena · SoA（结构数组）· 结构 key（UI 层 O(1) 版本号差分键）· 槽位（slot，兄弟定位）
* 演进：与 API 库（§4/§8）、事件轴（§5）互引用；模块一实现结论反向修订骨架定义（记入版本表）