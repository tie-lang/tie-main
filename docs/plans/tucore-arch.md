# 规划：trm.ui 域架构（原 tieuicore/tucore，已并入 trm 运行时套件）
*EN: Plan: the trm.ui Domain Architecture (formerly tieuicore/tucore, merged into the trm Runtime Suite)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> **2026-08-15 更新：本文件为 trm.ui 域的详细设计**——tieuicore 已并入
> [trm-arch.md](trm-arch.md)（tie 运行时套件），原 tucore 即 trm 的 ui 域。
> 命名空间：**trm.ui**（原 tucore/tcore 弃用）。本文档架构决策全部保留。
>
> 本文档定义 trm.ui（tie UI 核心，原 tieuicore）的架构。
> 决策汇总：
> **A4**（抽象 API + Win32 起步渐进）+ **H2**（类型化句柄）+ **E3**（事件+信号
> 混合）+ **D2**（命令列表 Paint Commands）+ **F3**（系统字体+位图双轨）
> + **P2**（平台目录分离）+ **L1**（显式生命周期）。
> 设计借鉴：**JVM/.NET 设计思路**（P/Invoke 互操作、延迟绑定、元数据驱动、
> 程序集部署单元、接口抽象）。
> 关联：unsafe 模型（extern/repr(C)）、接口模型（port 抽象面）、包模型
> （P4b 接口依赖）、UI 框架（tieui 消费 tucore）、tieir 格式（导出表）。
>
> EN: Status: **Plan** (design discussion finalized on 2026-08-15, not implemented)
> EN: **2026-08-15 update: this file is the detailed design of the trm.ui domain** — tieuicore has been merged into [trm-arch.md](trm-arch.md) (the tie runtime suite), and the original tucore is trm's ui domain. Namespace: **trm.ui** (the original tucore/tcore are deprecated). This document's architecture decisions are all kept.
> EN: This document defines the architecture of trm.ui (the tie UI core, formerly tieuicore). Decision summary: **A4** (abstract API + Win32-first gradual) + **H2** (typed handles) + **E3** (event + signal mix) + **D2** (command-list Paint Commands) + **F3** (system glyphs + bitmap dual tracks) + **P2** (platform directory separation) + **L1** (explicit lifecycle).
> EN: Design borrowings: **JVM/.NET design ideas** (P/Invoke interop, lazy binding, metadata-driven, assembly deployment unit, interface abstraction). Related: the unsafe model (extern/repr(C)), the interface model (port abstraction surface), the package model (P4b interface dependency), the UI framework (tieui consumes tucore), and the tieir format (export table).

## 1. 定位
*EN: 1. Positioning*

tieuicore = tieui 的性能核心兼容层（tie 语言编写）：
- 系统 API 的标量化封装（窗口/绘制/事件/字体/输入）
- 直接系统底层（Win32/X11/Wayland/帧缓冲）
- 性能关键路径（绘制/事件/资源管理）全部在此层
- tieui 框架层（纯 tie）只做逻辑编排，调用 tucore 抽象 API

EN: tieuicore = tieui's performance-core compatibility layer (written in tie): a scalarized wrapper of system APIs (windows/painting/events/fonts/input); direct access to the system bottom level (Win32/X11/Wayland/framebuffer); all performance-critical paths (painting/events/resource management) live in this layer; the tieui framework layer (pure tie) only does logical orchestration, calling tucore's abstract API.

## 2. JVM/.NET 借鉴（设计思路映射）
*EN: 2. JVM/.NET Borrowings (Design-Idea Mapping)*

| JVM/.NET 机制 | tie 对应 | 借鉴点 |
| --- | --- | --- |
| **P/Invoke**（托管调非托管） | extern 声明 + 自动 marshaling | 互操作层模型：string↔char*、ptr 透传、repr(C) 结构体按引用 |
| **延迟绑定**（JVM 符号懒解析 / .NET 程序集加载） | extern 符号动态链接 | tucore 作为动态库（.dll/.so）运行时加载，**P4b 实现选择运行时分发** |
| **元数据驱动**（.NET metadata） | tieir 导出表 + port 声明 | 消费方按导出表生成调用代码（免头文件） |
| **程序集**（.NET assembly 版本化部署单元） | tieir 包 | 版本化、独立部署、依赖图（已定包模型） |
| **接口抽象**（JVM interface / .NET interface） | port（接口模型） | 抽象 API 面 = port 声明，多实现（win32/x11/fb） |
| **BCL 基础类库**（.NET 核心库） | std/tucore 分层 | tucore = 平台相关核心，std = 平台无关逻辑 |

EN: This table maps JVM/.NET mechanisms to their tie counterparts and borrowing points: P/Invoke → extern declarations + automatic marshaling (the interop-layer model: string↔char*, ptr pass-through, repr(C) structs by reference); lazy binding → extern symbol dynamic linking (tucore loaded at runtime as a dynamic library .dll/.so, with P4b runtime implementation selection); metadata-driven → tieir export table + port declarations (consumers generate call code from the export table, no headers); assembly → tieir packages (versioned, independently deployed, dependency graph — package model decided); interface abstraction → port (interface model: the abstract API surface = port declarations, multiple implementations win32/x11/fb); the BCL → the std/tucore layering (tucore = platform-dependent core, std = platform-independent logic).

**关键借鉴：延迟绑定/动态加载**——tucore 编译为动态库，extern 符号运行时
解析（LoadLibrary/dlopen），使 backend 实现选择（P4b）在运行时分发，
三端共用同一抽象面。

EN: **Key borrowing: lazy binding/dynamic loading** — tucore compiles to a dynamic library, extern symbols are resolved at runtime (LoadLibrary/dlopen), enabling back-end implementation selection (P4b) to be distributed at runtime, with all three ends sharing the same abstract surface.

## 3. 目录结构（A4 抽象 API + P2 平台分离）
*EN: 3. Directory Structure (A4 Abstract API + P2 Platform Separation)*

```
tucore/（type tie<unsafe> 库，命名空间 tucore）
├── api.tie          抽象 API（port 声明，平台无关）── 框架层依赖面
├── win32/           Win32 实现（extern 封装）
│   ├── window_win32.tie
│   ├── draw_win32.tie
│   └── event_win32.tie
├── x11/             X11 实现（M6 渐进）
├── fb/              帧缓冲实现（嵌入式，M7）
└── shared/          跨平台共享（句柄表/命令列表/字体兜底）
```

- **A4**：抽象面先定（api.tie 的 port 声明），平台实现逐个加
  - EN: **A4**: the abstract surface is decided first (api.tie's port declarations); platform implementations are added one by one
- **P2**：平台目录分离，发布按平台打包
  - EN: **P2**: platform directory separation, packaged per platform at release
- 渐进：M1 Win32 → M6 X11 → M7 帧缓冲
  - EN: gradual: M1 Win32 → M6 X11 → M7 framebuffer

## 4. 抽象 API（api.tie，port 声明）
*EN: 4. Abstract API (api.tie, port Declarations)*

```tie
// 抽象面 = port 声明（平台无关签名）
port Window {
    pub func create(self, title: string, w: i64, h: i64) -> Window
    pub func show(self)
    pub func resize(self, w: i64, h: i64)
    pub func close(self)
}

port Painter {
    pub func begin(self) -> PaintCmd
    pub func rect(self, cmd: PaintCmd, x: i64, y: i64, w: i64, h: i64, color: u32)
    pub func text(self, cmd: PaintCmd, s: string, x: i64, y: i64, font: Font)
    pub func end(self, cmd: PaintCmd)
}

port EventSource {
    pub func drain(self) -> table<Event>       // E3 事件队列
    pub func signal_check(self) -> i64          // E3 信号标志
}
```

- 抽象面 = port（接口模型 P1 显式 impl）：win32/x11/fb 各实现
  - EN: the abstract surface = port (interface model P1 explicit impl): each of win32/x11/fb implements it
- tieui 框架层只依赖 api.tie 的 port（P4b 接口依赖，--backend 选实现）
  - EN: the tieui framework layer depends only on api.tie's ports (P4b interface dependency; --backend selects the implementation)

## 5. 句柄模型（H2：类型化句柄）
*EN: 5. Handle Model (H2: Typed Handles)*

```tie
// 句柄 = struct 包装 i64（系统句柄透传，零开销）
struct Window {
    var h: i64      // 系统句柄（HWND）
    // 私有字段，方法绑定（tie 的 struct 数据/逻辑分离）
}

// 使用：方法语法（obj.method() 转发）
var w = tucore.window_create("App", 800, 600)
w.show()
w.resize(1024, 768)

// 移动语义：句柄 move 不复制底层（安全）
var w2 = w          // move，w 失效
```

- 类型安全：Window 不能传成 Font（编译器检查）
  - EN: type safety: a Window cannot be passed as a Font (compiler-checked)
- 零开销：i64 透传，无额外分配
  - EN: zero overhead: i64 pass-through, no extra allocation
- 与移动语义咬合：句柄 move 语义（唯一所有者）
  - EN: interlocks with move semantics: handle move semantics (unique owner)

## 6. 事件模型（E3：事件 + 信号混合）
*EN: 6. Event Model (E3: Event + Signal Mix)*

### 6.1 事件队列（主通道）
*EN: 6.1 Event Queue (main channel)*

```tie
// 批量拉取（E2 语义并入）：一次取完队列
var batch = tucore.event_drain()      // table<Event>
for ev in batch {
    switch ev.kind {
        case MouseMove: ...
        case KeyDown: ...
        case WindowResize: ...
    }
}
```

- 队列：无锁 SPSC（ISR/系统线程 → 主循环，与并发模型咬合）
  - EN: queue: lock-free SPSC (ISR/system thread → main loop, interlocked with the concurrency model)
- 事件 = 值（struct/枚举），含位置/键码/时间戳
  - EN: events = values (struct/enum), including position/key code/timestamp

### 6.2 信号标志（轻量通知通道）
*EN: 6.2 Signal Flags (lightweight notification channel)*

```tie
// 信号：轻量标志位（系统消息映射），区别于事件队列
// 场景：重绘请求（WM_PAINT）、定时器到期、IO 就绪
var sig = tucore.signal_check()       // 位掩码：1=重绘 2=定时器 4=IO
if sig & 1 != 0 { render() }
if sig & 2 != 0 { on_timer() }
```

- 信号 vs 事件分工：
  - EN: division of labor between signals and events:
  - **事件**：有载荷的离散交互（鼠标/键盘/窗口消息）→ 队列
    - EN: **events**: discrete interactions with payloads (mouse/keyboard/window messages) → queue
  - **信号**：无载荷的状态通知（重绘/定时器/IO 就绪）→ 位标志
    - EN: **signals**: payload-free state notifications (repaint/timer/IO ready) → bit flags
- 效率：信号零分配（位运算），高频通知（每帧重绘）不走队列
  - EN: efficiency: signals have zero allocation (bit ops); high-frequency notifications (per-frame repaint) don't go through the queue
- 系统映射：WM_PAINT → 重绘信号；WM_TIMER → 定时器信号；
  鼠标/键盘 → 事件队列
  - EN: system mapping: WM_PAINT → repaint signal; WM_TIMER → timer signal; mouse/keyboard → event queue

### 6.3 主循环形态（三端同构）
*EN: 6.3 Main-Loop Form (isomorphic across three ends)*

```tie
tucore.init()
var w = tucore.window_create("App", 800, 600)
w.show()

while !tucore.signal_check(& Shutdown) {   // 退出信号
    var batch = tucore.event_drain()       // 事件
    for ev in batch { handle(ev) }
    if tucore.signal_check(& Redraw) {     // 重绘信号
        render()                           // 命令列表 → 系统绘制
    }
}
tucore.shutdown()                          // L1 显式生命周期
```

## 7. 绘制模型（D2：命令列表 Paint Commands）
*EN: 7. Painting Model (D2: Command List Paint Commands)*

```tie
// 记录 → 提交（与架构图 Paint List 一致）
var cmd = tucore.paint_begin()            // 开启命令列表
tucore.paint_rect(cmd, 10, 10, 100, 40, 0xFF3366)
tucore.paint_text(cmd, "Hi", 20, 20, font)
tucore.paint_end(cmd)                     // 提交：系统执行绘制

// 脏矩形重绘优化：只记录变化区域
tucore.paint_begin_dirty(cmd, x, y, w, h)
```

- 与系统 API 1:1 映射（GDI/Direct2D/Canvas/帧缓冲都是这个形态）
  - EN: 1:1 mapping with system APIs (GDI/Direct2D/Canvas/framebuffers all take this form)
- webui：命令列表 → Canvas 调用（1:1 翻译，工作量小）
  - EN: webui: command list → Canvas calls (1:1 translation, small workload)
- 嵌入式：命令列表 → 帧缓冲直绘
  - EN: embedded: command list → direct framebuffer drawing
- 重绘优化基础：脏矩形（信号驱动，见 §6.2）
  - EN: the basis of repaint optimization: dirty rectangles (signal-driven, see §6.2)

## 8. 字体（F3：系统字体 + 位图兜底）
*EN: 8. Fonts (F3: System Fonts + Bitmap Fallback)*

```tie
// 系统字体（桌面）：GDI/CoreText/DirectWrite
var font = tucore.font_load_system("Microsoft YaHei", 14)

// 位图字体（嵌入式兜底）：内置 ASCII + CJK 子集
var bfont = tucore.font_load_bitmap("rdu_font")

// 度量：文本宽高（布局引擎依赖）
var w = tucore.font_measure(font, "Hello")
```

- 桌面：系统字体（本地化好、零打包）
  - EN: desktop: system fonts (good localization, zero packaging)
- 嵌入式：位图字体（零依赖，rdu 风格）
  - EN: embedded: bitmap fonts (zero dependencies, rdu style)
- 统一抽象：font_measure/font_render 两实现
  - EN: unified abstraction: font_measure/font_render with two implementations

## 9. 组合式开发（一等设计原则，2026-08-15 补充）
*EN: 9. Composable Development (a first-class design principle, added 2026-08-15)*

### 9.1 原则
*EN: 9.1 Principle*

**"一切皆可组合"**——组件、行为、布局、模块四个层次全部支持组合式开发：

EN: **"Everything is composable"** — all four levels (components, behaviors, layouts, modules) support composable development:

| 层次 | 组合机制 | 依托 |
| --- | --- | --- |
| 组件组合 | 组件树嵌套（任意深度）+ children 插槽 | 组件树（所有权树） |
| 行为组合 | 闭包链装饰（logger/auth/guard 叠加） | 闭包模型 C2 |
| 布局组合 | 布局器即组件（row/column/grid/stack 可嵌套） | 组件树 |
| 模块组合 | 包依赖 + port 接口（实现可替换） | 包模型 P4b |

### 9.2 组件组合（UI 层）
*EN: 9.2 Component Composition (UI layer)*

```tie
// 组合：Container > Row > [Button, Input]
var row = tui.row(
    tui.button("OK", on_click),     // 子组件 = 闭包回调
    tui.input("name"),
)
var page = tui.container(row, padding = 16)
```

- **children 插槽**：容器组件接收子组件列表（组合点）
  - EN: **children slot**: a container component receives a list of child components (the composition point)
- 任意组件可作子组件（同构组合，无继承）
  - EN: any component can be a child (homogeneous composition, no inheritance)
- 组件树 = 所有权树（父拥有子，窗口关闭整树析构）
  - EN: the component tree = an ownership tree (parent owns child, window close destructs the whole tree)

### 9.3 行为组合（闭包层）
*EN: 9.3 Behavior Composition (closure layer)*

```tie
// 行为装饰链：组合而非继承
var guarded = auth_guard(logger(handler))   // 权限 → 日志 → 业务

// 组合子（高阶函数）：with_auth / with_logging 返回新闭包
func with_logging(f: fn(i64) -> i64) -> fn(i64) -> i64 {
    return func(x: i64) -> i64 {
        log("call " + to_string(x))
        return f(x)
    }
}
```

- 闭包模型（C2）天然支持组合：高阶函数返回闭包
  - EN: the closure model (C2) naturally supports composition: higher-order functions return closures
- tie 无继承 → **组合是唯一扩展方式**（设计上强制，符合"组合优于继承"）
  - EN: tie has no inheritance → **composition is the only extension method** (enforced by design, consistent with "composition over inheritance")

### 9.4 布局组合（布局层）
*EN: 9.4 Layout Composition (layout layer)*

```tie
tui.column([
    tui.row([a, b]),
    tui.expand(c),            // 弹性子组件（占剩余空间）
])
```

- 布局器也是组件 → 布局可嵌套（row 在 column 里）
  - EN: layouters are also components → layouts can nest (rows inside columns)
- 弹性/权重布局（expand/flex）是布局组合的基本算子
  - EN: elastic/weighted layout (expand/flex) is the basic operator of layout composition

### 9.5 tucore API 的组合性
*EN: 9.5 Composability of the tucore API*

- **命令列表可组合**：子命令列表嵌套 → 提交合并（组件的绘制递归进父列表）
  - EN: **command lists are composable**: nested sub-command lists → merged on submission (a component's painting recurses into the parent list)
- **事件管线可组合**：过滤器链（前置处理 → 事件 → 后置处理）
  - EN: **event pipelines are composable**: filter chains (pre-processing → event → post-processing)
- **句柄操作链**：方法链（w.show().resize(..) 或链式调用）
  - EN: **handle operation chains**: method chains (w.show().resize(..) or chained calls)

## 10. 生命周期（L1：显式 init/shutdown）
*EN: 10. Lifecycle (L1: Explicit init/shutdown)*

```tie
tucore.init()           // 初始化：加载平台后端（动态链接，延迟绑定）、注册句柄表
...                     // 应用运行
tucore.shutdown()       // 清理：释放资源、卸载后端
```

- 显式调用（main 首行/尾行），与嵌入式 main_loop 匹配
  - EN: explicit calls (first/last lines of main), matching the embedded main_loop
- init 时按 --backend 加载平台实现（延迟绑定，JVM/.NET 借鉴）
  - EN: at init, the platform implementation is loaded per --backend (lazy binding, JVM/.NET borrowing)

## 11. 编译器实现拆解（tiec 自举）
*EN: 11. Compiler Implementation Breakdown (tiec Self-Hosting)*

| 模块 | 改动 |
| --- | --- |
| unsafe 扩展 | extern ptr/repr(C) 结构体按引用（M0） |
| tucore api.tie | port 声明（抽象面） |
| tucore win32/ | extern 封装实现（窗口/绘制/事件/字体） |
| 动态库 | tucore 编译为 .dll/.so（延迟绑定，M5 动态库能力） |
| 句柄表 | 共享层：句柄 → 平台对象映射（i64 表） |

## 12. 决策记录（讨论产物）
*EN: 12. Decision Log (Discussion Output)*

| 决策点 | 结论 | 备选（未选） |
| --- | --- | --- |
| 分层 | A4：抽象 API + Win32 起步渐进 | A1 单层、A2 域模块、A3 三层全平台 |
| 句柄 | H2：类型化句柄（struct 包装 i64 + move） | H1 裸 i64、H3 引用对象 |
| 事件 | E3：事件队列 + 信号标志混合 | E1 单事件轮询、E2 纯批量 |
| 绘制 | D2：命令列表（Paint Commands） | D1 立即模式、D3 场景图 |
| 字体 | F3：系统字体 + 位图兜底双轨 | F1 纯系统、F2 纯位图 |
| 平台 | P2：目录分离（win32/x11/fb） | 条件编译、符号重定向 |
| 生命周期 | L1：显式 init/shutdown | RAII 自动 |
| 命名空间 | **tucore**（非 tcore） | tcore |
| 借鉴 | JVM/.NET：P/Invoke、延迟绑定、元数据驱动、程序集、接口抽象 | 无 |
| 组合式开发 | 一等设计原则：组件/行为/布局/模块四层全组合（组合优于继承） | 继承式 |

## 13. 未决问题
*EN: 13. Open Questions*

1. **动态库 vs 静态库**：tucore 延迟绑定需要动态库（.dll/.so）——M5 动态库
   编译能力（docs/plans/dynamic-library.md 规划中）是前置；嵌入式无动态库
   （静态链接，无延迟绑定——P4b 编译期选择）
   EN: **dynamic vs static library**: tucore's lazy binding needs a dynamic library (.dll/.so) — the M5 dynamic-library compilation capability (docs/plans/dynamic-library.md, in planning) is a prerequisite; embedded has no dynamic library (static linking, no lazy binding — P4b compile-time choice)
2. **句柄表的并发**：句柄 → 平台对象映射的访问（主线程专用？文档化）
   EN: **handle-table concurrency**: access to the handle → platform-object mapping (main-thread-only? document it)
3. **E3 信号的扩展**：信号位掩码 64 位够用吗（自定义信号留给应用？）
   EN: **extension of E3 signals**: is a 64-bit signal bitmask enough (reserve custom signals for applications?)
4. **绘制命令的序列化**：命令列表跨平台传输（wasm 场景命令列表编码——
   与 tieir 序列化技术同源）
   EN: **serialization of paint commands**: cross-platform transport of the command list (command-list encoding in the wasm scenario — same origin as tieir serialization)
5. **tucore 的测试策略**：无窗口环境（CI）——命令列表可离线回放验证
   （绘制命令纯数据，可 dump/比较）
   EN: **tucore's testing strategy**: windowless environments (CI) — command lists can be offline-replayed for validation (paint commands are pure data, dumpable/comparable)