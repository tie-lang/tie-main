# 规划：tie UI 框架（tieui + webui）+ 语言系统扩展（unsafe/内存/并发）
*EN: Plan: the tie UI Framework (tieui + webui) + Language-System Extensions (unsafe/Memory/Concurrency)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> 本文档整合一次完整设计讨论的决策：UI 框架架构、unsafe 语法、内存模型、
> 并发/并行模型、嵌入式子集。所有决策均为讨论产物，实现前可再调整。
> 2026-08-15 更新：webui 部分经专项技术调研修订（JSPI 方案替代状态机变换、
> M5 里程碑拆解），见 [webui-research.md](webui-research.md)。
> 关联：rdu（嵌入式基础层，docs/plans/embedded-rdu.md）、tiec 自举编译器。
>
> EN: Status: **Plan** (design discussion finalized on 2026-08-15, not implemented)
> EN: This document consolidates the decisions of one complete design discussion: the UI framework architecture, unsafe syntax, memory model, concurrency/parallelism model, and the embedded subset. All decisions are discussion output, adjustable before implementation.
> EN: 2026-08-15 update: the webui part has been revised through a dedicated technical study (the JSPI option replaces state-machine transformation; the M5 milestones are broken down), see [webui-research.md](webui-research.md).
> EN: Related: rdu (the embedded foundation layer, docs/plans/embedded-rdu.md) and the tiec self-hosting compiler.

## 1. 目标与定位
*EN: 1. Goals and Positioning*

### 1.1 产品目标
*EN: 1.1 Product Goals*

跨平台 UI 框架，同一套 tie 代码支持两种运行模式：

EN: A cross-platform UI framework; the same tie code supports two runtime modes:

| 模式 | 定位 | 运行环境 | 面向对象 |
| --- | --- | --- | --- |
| **tieui** | tie 原生 UI，直接系统底层 | 桌面（Win32/X11/Wayland）、嵌入式（MCU/帧缓冲） | 新应用 |
| **webui** | 现有 tie 应用的 Web 迁移通道 | 浏览器（wasm + HTML 壳） | 存量应用迁移 |

### 1.2 设计原则（讨论定稿）
*EN: 1.2 Design Principles (finalized in discussion)*

1. **全 tie 技术栈**：trm（运行时套件，原 trm）用 tie 写（不用 Rust、
   不用 C），延续自举精神；仅系统 API 互操作经 extern FFI（T0.7 已有先例：
   `std/process.tie` 调 libc system）。
   EN: **all-tie stack**: trm (the runtime suite, formerly trm) is written in tie (no Rust, no C), continuing the bootstrapping spirit; only system-API interop goes through extern FFI (T0.7 has a precedent: `std/process.tie` calls libc system).
2. **webui 是"壳 + 桥"**：不是给新应用做浏览器 UI，而是让现有 tie 程序
   （CLI/脚本/tieDB 应用）编译为 wasm，经标准 Web 壳（HTML 页面 + JS 桥）在
   浏览器运行，输入输出经桥接呈现。
   EN: **webui is a "shell + bridge"**: not building browser UIs for new apps, but letting existing tie programs (CLI/scripts/tieDB apps) compile to wasm and run in the browser through a standard Web shell (HTML page + JS bridge), with I/O presented through the bridge.
3. **性能热点下沉**：绘制、调度、切换等性能关键路径由 trm（tie 写但
   只做薄封装，直接透传系统调用）承载；tieui 框架层只做逻辑编排。
   EN: **performance hotspots sink down**: performance-critical paths (painting, scheduling, switching) are carried by trm (written in tie but only a thin wrapper that passes through system calls directly); the tieui framework layer only does logical orchestration.
4. **编译目标决定能力**：同一语言、同一套语义（协程/消息/所有权），
   桌面/服务器用完整模型，嵌入式用编译期裁剪子集（`tie:embedded` 角色）。
   EN: **the compile target decides capabilities**: the same language and the same semantics (coroutines/message passing/ownership) — desktop/server use the full model, embedded uses a compile-time-trimmed subset (the `tie:embedded` role).

### 1.3 风格哲学（2026-08-15 定稿）：过程式内核 + 函数式能力 + 接口抽象 + 组合式组织
*EN: 1.3 Style Philosophy (finalized 2026-08-15): procedural core + functional capability + interface abstraction + compositional organization*

tie 的开发范式不是单一范式，而是四者各司其职的组合：

EN: tie's development paradigm is not a single one, but a combination where each of the four plays its role:

| 范式 | tie 的定位 | 落地机制 |
| --- | --- | --- |
| **过程式** | 内核（语句/控制流/性能路径） | while/for/if、trm、tiec 编译器自身 |
| **函数式** | 抽象能力（组合与复用的武器） | 闭包 C2、高阶函数、enum ADT + switch 穷尽匹配 |
| **面向接口** | 扩展点（多态，实现可替换） | port（P1 显式 impl + D3 双形态） |
| **组合式** | 系统组织方式（粘合前三者） | 组件/行为/布局/模块四层组合（tucore-arch §9，已并入 trm.ui） |

**一句话**：面向过程写内核，函数式写抽象，接口写扩展，组合写系统。

EN: **In one sentence**: write the core procedurally, write abstractions functionally, write extensions via interfaces, and write the system compositionally.

**明确排除面向对象**（三个致命冲突）：
1. 封装状态与值语义冲突——移动语义/值拷贝下对象模型互斥（Rust 已证明）
2. 继承层级脆弱（脆弱基类问题）——组合优于继承
3. 封装状态不可序列化——tie 数据要进 tieir/数据库/网络（tieDB 定位）

EN: **Object orientation is explicitly excluded** (three fatal conflicts): (1) encapsulated state conflicts with value semantics — object models are mutually exclusive under move semantics/value copying (proven by Rust); (2) inheritance hierarchies are fragile (the fragile-base-class problem) — composition over inheritance; (3) encapsulated state is not serializable — tie data must go into tieir/databases/networks (the tieDB positioning).

**面向过程不包打天下**（缺抽象/多态——由闭包/port/泛型补齐）；
**纯函数式不可行**（系统编程需要可变状态性能、unsafe 互操作、嵌入式无 GC 基础设施）。

EN: **Procedural programming alone doesn't cover everything** (missing abstraction/polymorphism — filled in by closures/ports/generics); **pure functional is infeasible** (systems programming needs mutable-state performance, unsafe interop, and embedded has no GC infrastructure).

> 这一哲学与 Rust 收敛（过程式内核 + FP 能力 + trait 接口 + 无继承），
> 也是 Go/现代 C++ 的共同方向。tie 的既有决策（struct 数据/逻辑分离 M2.1.8、
> 无继承、闭包、ADT）已自然汇聚于此——本文档是显式确认，非新增约束。
>
> EN: This philosophy converges with Rust (procedural core + FP capability + trait interfaces + no inheritance) and is also the common direction of Go/modern C++. tie's existing decisions (struct data/logic separation M2.1.8, no inheritance, closures, ADTs) have naturally coalesced here — this document is an explicit confirmation, not a new constraint.

### 1.4 序列化规范（2026-08-15）：通信用 zd，人读用 data
*EN: 1.4 Serialization Spec (2026-08-15): zd for communication, data for human reading*

**决策**：tie 生态的**机器间通信一律使用 zd**（二进制紧凑格式）；
`data`（文本格式）仅保留给人读场景（配置/数据交换文件）。

EN: **Decision**: **inter-machine communication in the tie ecosystem always uses zd** (a compact binary format); `data` (text format) is kept only for human-read scenarios (config/data-exchange files).

| 场景 | 格式 | 理由 |
| --- | --- | --- |
| 网络载荷（HTTP body/TCP 消息） | **zd** | 体积小、解析快 |
| 进程间通信（IPC） | **zd** | 同上 |
| 存储持久化（tieDB 等） | **zd** | 已实现（tieDB/persist/zd.tie） |
| 协程/channel 消息（进程内） | 内存对象直接 move | 无需序列化 |
| tieir 分发 | 二进制（自有格式） | 已定（tieir-format.md） |
| 配置文件（tie.config/tie.pkg） | **data** | 人维护，需可读 |
| 数据交换文件（导出/导入） | data（可读）或 zd（紧凑） | 按需求二选一 |

EN: This table shows the format per scenario: network payloads and IPC use zd (small, fast to parse); storage persistence uses zd (already implemented); in-process coroutine/channel messages move memory objects directly; tieir distribution uses its own binary; config files use data (maintained by humans, needs readability); data-exchange files choose data (readable) or zd (compact) as needed.

**现状基础**：zd 已实现（tieDB/persist/zd.tie，namespace zd，MessagePack+
Protobuf 参考，纯 tie）：fixint/varint/定宽/字符串/表/map/record 字段编码 +
save/load 8 字节魔数 "TIEDBZD"。已在 compiler/driver、std/db、prep 使用。

EN: **Current foundation**: zd is implemented (tieDB/persist/zd.tie, namespace zd, MessagePack+Protobuf-referenced, pure tie): fixint/varint/fixed-width/string/table/map/record field encoding + save/load with the 8-byte "TIEDBZD" magic number. Already used in compiler/driver, std/db, and prep.

**影响面**：
- std/http、std/net 的载荷默认 zd（文本头保留：HTTP 头仍是文本协议，body 用 zd）
- 未来协议设计（IPC/webui 桥/wasm 通信）默认 zd
- tieui/trm.ui 的事件序列化（跨进程/跨线程传递事件）用 zd

EN: **Impact surface**: std/http and std/net payloads default to zd (text headers stay: HTTP headers remain a text protocol, body uses zd); future protocol design (IPC/webui bridge/wasm communication) defaults to zd; tieui/trm.ui event serialization (events across processes/threads) uses zd.

## 2. 总体架构
*EN: 2. Overall Architecture*

```
┌─ tieui 框架层（tie 语言编写，平台无关）──────────────┐
│  组件树 / 盒模型布局 / 事件分发 / 状态管理             │
├─ trm.ui 域（tie 编写，原 trm，高性能薄封装）───┤
│  窗口封装 / 绘制封装 / 字体 / 事件轮询 / 协程调度     │
│  ↓ extern（扩展后：ptr/结构体支持）                   │
│  系统 API 直连：Win32 / X11 / Wayland / 帧缓冲        │
├─ webui 壳（HTML + JS + wasm）───────────────────────┤
│  Canvas 桥（对应 trm.ui 绘制面）                     │
│  Worker 桥（对应协程/线程面）                        │
└──────────────────────────────────────────────────────┘
```

> 2026-08-15 更新：trm 已并入 **trm（tie 运行时套件）**，原 trm
> 即 trm 的 ui 域（trm.ui）。详见 [trm-arch.md](trm-arch.md)。
>
> EN: 2026-08-15 update: trm has been merged into **trm (the tie runtime suite)**; the original trm is trm's ui domain (trm.ui). See [trm-arch.md](trm-arch.md) for details.

### 2.1 分层职责
*EN: 2.1 Layered Responsibilities*

- **tieui 框架层**：纯 tie，组件（Button/Text/Input/List/Scroll）、布局、事件、
  状态。与平台无关，只调用 trm.ui 的标量 extern 接口。
  - EN: **the tieui framework layer**: pure tie; components (Button/Text/Input/List/Scroll), layout, events, state. Platform-independent, calling only trm.ui's scalar extern interfaces.
- **trm.ui 域（原 trm）**：tie 写，但内部直接透传系统调用（窗口创建、
  GDI/Direct2D 绘制、字体加载、消息轮询）。是"系统 API 的标量化封装"，
  是性能关键路径。
  - EN: **the trm.ui domain (formerly trm)**: written in tie, but internally passes through system calls directly (window creation, GDI/Direct2D painting, font loading, message polling). It is the "scalarized wrapper of system APIs" and is the performance-critical path.
- **webui 壳**：tie 编译为 wasm 后运行于浏览器；Canvas 2D 对应绘制面，
  Web Worker 对应并发面。迁移应用零改动（终端模拟路线）或页面化包装。
  - EN: **the webui shell**: tie compiles to wasm and runs in the browser; Canvas 2D maps to the painting surface, Web Worker maps to the concurrency surface. Migrating apps need zero changes (terminal-emulation route) or page-style packaging.

### 2.2 关键洞察：无软件光栅化
*EN: 2.2 Key Insight: No Software Rasterization*

tieui 不做自研光栅化器——绘制指令由**系统 API 执行**（桌面 GDI/Direct2D，
嵌入式帧缓冲直绘，浏览器 Canvas 2D）。三端消费同一份 Paint Commands 抽象，
绘制由平台完成。统一的是"指令流语义"，不是像素实现。

EN: tieui does not build its own rasterizer — drawing instructions are executed by **system APIs** (desktop GDI/Direct2D, embedded direct framebuffer drawing, browser Canvas 2D). The three ends consume the same Paint Commands abstraction, with painting done by the platform. What is unified is the "instruction-stream semantics", not the pixel implementation.

## 3. 语言扩展：unsafe 语法
*EN: 3. Language Extension: unsafe Syntax*

### 3.1 动机
*EN: 3.1 Motivation*

系统 API 需要指针、结构体、回调，而 tie 的 extern 目前只支持标量签名
（i64/f64/bool/string，见 `std/runtime.tie` 约束清单）。给 tie 加入 unsafe
语法，在**默认安全**的前提下显式打开底层能力。

EN: System APIs need pointers, structs, and callbacks, but tie's extern currently supports only scalar signatures (i64/f64/bool/string, see the `std/runtime.tie` constraint list). Adding unsafe syntax to tie explicitly opens low-level capabilities while staying **safe by default**.

### 3.2 设计草案（参照 Rust，更简单）
*EN: 3.2 Design Draft (referencing Rust, simpler)*

```tie
// unsafe 函数：可进行指针运算、结构体映射、系统调用
unsafe fn create_window(title: string, w: i64, h: i64) -> i64 {
    var cls: WndClassW = ...          // repr(C) 结构体直接映射系统内存布局
    var hwnd: i64 = user32_create_window_exW(...)   // 系统 API 直调
    return hwnd
}

// unsafe 块：局部逃逸，不需要整个函数 unsafe
unsafe {
    var p: ptr = addr_of(wnd)         // 取地址
    // ...
}
```

### 3.3 三块能力
*EN: 3.3 Three Capability Blocks*

1. **指针类型 `ptr`**：i64 的语义化包装，支持 `addr_of(x)` 取地址、
   `deref(p)` 解引用、指针算术。
   EN: **pointer type `ptr`**: a semantic wrapper of i64, supporting `addr_of(x)` address-taking, `deref(p)` dereferencing, and pointer arithmetic.
2. **repr(C) 结构体**：`struct WndClassW { ... }` 按 C ABI 内存布局
   （字段偏移精确对齐），可整体传给系统 API。
   EN: **repr(C) structs**: `struct WndClassW { ... }` laid out per the C ABI (field offsets precisely aligned), passable wholesale to system APIs.
3. **extern 调用归入 unsafe**：调用任何 extern fn 必须在 unsafe 上下文内
   （Rust 风格），安全代码不允许触底。
   EN: **extern calls fall under unsafe**: calling any extern fn must be within an unsafe context (Rust style); safe code is not allowed to touch the bottom.

### 3.4 安全边界
*EN: 3.4 Safety Boundary*

普通代码永远碰不到指针/地址/内存布局；只有显式 `unsafe` 区域可以。
编译器在 unsafe 边界强制检查。这是 tie 的卖点：**默认安全，显式解锁**。

EN: Ordinary code can never touch pointers/addresses/memory layouts; only explicit `unsafe` regions can. The compiler enforces checks at the unsafe boundary. This is tie's selling point: **safe by default, explicitly unlocked**.

### 3.5 绕开策略（优先）
*EN: 3.5 Workaround Strategy (preferred)*

窗口过程（WndProc）用**固定实现**：所有消息压入队列，tie 侧轮询
`poll_event()`。这样不需要回调函数指针扩展，只需要：
- extern 支持 **ptr 参数**（i64 地址透传）
- extern 支持**结构体按引用**（或编译器生成内存布局）
- 句柄一律 i64

EN: The window procedure (WndProc) uses a **fixed implementation**: all messages are pushed into a queue, polling `poll_event()` on the tie side. This avoids needing callback function-pointer extensions, requiring only: extern supports **ptr parameters** (i64 address pass-through); extern supports **structs by reference** (or the compiler generates the memory layout); handles are always i64.

## 4. 内存模型
*EN: 4. Memory Model*

### 4.1 现状（设计前提）
*EN: 4.1 Current State (design premise)*

| 层 | 现状 | 谁管理 |
| --- | --- | --- |
| 栈 | LLVM alloca，局部变量 | 编译器自动 |
| 字符串 | NUL 结尾 char*，`str_*` 原语操作 | Rust 侧隐藏堆（tie 代码不可见） |
| table | `table_*` 原语（table_push/at 等） | 同样是 Rust 侧隐藏堆 |
| rdu | 无堆无指针 | 纯栈/静态 |

核心事实：**tie 目前的"堆"是隐形式的——tie 代码看不到内存**。
加 unsafe + ptr 后，必须决定显式内存模型，否则 unsafe 没有地基。

EN: Core fact: **tie's current "heap" is implicit — tie code cannot see memory**. After adding unsafe + ptr, an explicit memory model must be decided, otherwise unsafe has no foundation.

### 4.2 决策：所有权子集（方案 3）+ 区域内存（方案 6）
*EN: 4.2 Decision: Ownership Subset (Option 3) + Region Memory (Option 6)*

**方案 3 的可行简化：只做移动语义，不做借用检查**

EN: **The tractable simplification of Option 3: only move semantics, no borrow checking**

完整 Rust 所有权 = 移动 + 借用检查器（借用检查是 80% 的复杂度）。
tie 只做**移动**：

EN: Full Rust ownership = moves + a borrow checker (the borrow checker is 80% of the complexity). tie only does **moves**:

```tie
// 移动语义：堆类型（string/table/含堆字段的 struct）赋值即转移
var a: string = "hello"
var b: string = a        // a 被移动，此后使用 a = 编译错误
                         // 作用域结束自动释放（所有权树析构）

// 需要复制时显式 clone
var c: string = clone(a) // 或 copy(a)
```

编译器改动集中在 **semantic 层加"变量状态跟踪"**（live/moved 两态）：
- 使用已移动变量 → 编译错误（"use of moved value"）
- 参数传递 = 移动（所有权转移给被调函数）
- 返回值 = 移动（所有权转出）
- 栈类型（i64/f64/bool）不受影响，仍是拷贝

EN: The compiler changes concentrate on adding **"variable-state tracking" in the semantic layer** (two states: live/moved): using a moved variable → compile error ("use of moved value"); argument passing = move (ownership transferred to the callee); return value = move (ownership moves out); stack types (i64/f64/bool) are unaffected, still copied.

不需要生命周期标注、不需要借用规则——语言复杂度可控。

EN: No lifetime annotations, no borrow rules needed — language complexity stays manageable.

**方案 6：arena 是"区域所有者"**

EN: **Option 6: arena is the "region owner"**

```tie
// arena 块：块内分配的堆对象归 arena 所有，块结束整体释放
arena {
    var btn = ui_button("Click")    // 分配在 arena 内
    var row = ui_row(btn)           // 子对象也归 arena
}   // ← 整块释放，无需逐对象 free

// 逃逸规则：arena 内对象不允许以引用/指针逃出块
// 允许：按值拷贝/移动出去（脱离区域，成为独立对象）
```

编译器只检查 **arena 边界逃逸**（内部分配的引用不能出块）。

EN: The compiler only checks **arena-boundary escape** (references allocated inside cannot leave the block).

### 4.3 分层内存全景
*EN: 4.3 Layered Memory Panorama*

```
所有权树（自动析构，无泄漏无悬垂）
   └── arena 区域（批量释放，零碎片）
          └── 手动堆（unsafe alloc/free，系统互操作）
```

- UI 组件树 = 所有权树（父组件拥有子组件，窗口关闭整树析构）
  - EN: UI component tree = ownership tree (parent owns children; window close destructs the whole tree)
- 每帧渲染对象 = arena（帧结束整体释放）
  - EN: per-frame rendering objects = arena (released wholesale at frame end)
- 系统 API 互操作 = unsafe 手动堆
  - EN: system-API interop = unsafe manual heap

### 4.4 迁移策略（不考虑——直接默认移动语义）
*EN: 4.4 Migration Strategy (not considered — move semantics directly default)*

**决策（2026-08-15）**：目前 tie 无用户，**不做任何渐变路径/兼容层**——
移动语义直接成为默认语义，std/compiler 自举代码一次性迁移（编译器内部
重构，无外部依赖）。

EN: **Decision (2026-08-15)**: tie currently has no users, so **no gradual path / compatibility layer is made** — move semantics directly become the default semantics, with std/compiler bootstrap code migrated at once (an internal compiler refactor, no external dependency).

- 未来若需迁移：发布时附**迁移预处理脚本**（tie-prep --module 机制，
  先例 prep/rename_tcmsg_to_log.tie：`process(src)->string` 文本转换），
  发布说明附 `tie-prep --module migrate_owned_v1` 用法
  - EN: if migration is needed later: ship a **migration pre-processing script** at release (the tie-prep --module mechanism; precedent prep/rename_tcmsg_to_log.tie: `process(src)->string` text transformation), with the `tie-prep --module migrate_owned_v1` usage in the release notes
- 迁移脚本形态：读源码文本 → 输出迁移后文本（自动加 move/重构拷贝点）
  - EN: migration-script form: read source text → output migrated text (automatically add move/refactor copy points)

### 4.5 代价清单（诚实版）
*EN: 4.5 Cost List (honest version)*

- semantic 层：变量状态跟踪（live/moved）+ arena 逃逸检查——中等工程量
  - EN: the semantic layer: variable-state tracking (live/moved) + arena-escape checking — medium effort
- irgen：析构函数插入（作用域结束自动调 drop）——中等
  - EN: irgen: destructor insertion (auto drop at scope end) — medium
- 原语层：字符串/table 需要能"转移所有权"（现在 Rust 侧持有，要交控制权）——中等偏难
  - EN: the primitive layer: strings/tables need to be able to "transfer ownership" (currently held on the Rust side, control must be handed over) — medium-to-hard
- 编译器自举代码一次性迁移：std/compiler 全量改造（无渐进，一次到位）
  - EN: one-time migration of compiler bootstrap code: a full overhaul of std/compiler (no gradualism, done at once)

## 5. 并发/并行模型
*EN: 5. Concurrency/Parallelism Model*

### 5.1 决策汇总
*EN: 5.1 Decision Summary*

**安全层（语言级）**：协程/异步（方案 4）+ Actor（方案 5）+ Channel（方案 1）
**unsafe 层（trm）**：无锁并发（方案 7）

EN: **safe layer (language-level)**: coroutines/async (Option 4) + Actor (Option 5) + Channel (Option 1); **unsafe layer (trm)**: lock-free concurrency (Option 7).

这是 Go 的执行模型 + Erlang 的 actor 语法 + Rust 的安全哲学。

EN: This is Go's execution model + Erlang's actor syntax + Rust's safety philosophy.

### 5.2 统一模型
*EN: 5.2 Unified Model*

```
协程 = 一切并发的执行单元（轻量，万级）
  ├── actor = 协程 + 邮箱 + 状态隔离
  ├── channel = 协程间通信（无锁队列底层）
  ├── async IO = 协程挂起不阻塞线程
  └── M:N 调度 = 协程池映射到 OS 线程池（trm）
```

一个 OS 线程跑多个协程 → actor 变轻量，线程变资源池。

EN: One OS thread runs many coroutines → actors become lightweight, threads become a resource pool.

### 5.3 协程：栈式（stackful）
*EN: 5.3 Coroutines: Stackful*

| | stackful（Go/Java 虚拟线程） | stackless（Rust async） |
| --- | --- | --- |
| 实现 | 每协程独立栈 + 上下文切换（~50 行汇编） | await 编译成状态机 |
| 编译器工作量 | **小**（trm 提供切换原语，unsafe 调用） | **大**（全链路变换） |
| 灵活度 | 任意函数可挂起，无需传染 | 挂起需 async 传染 |
| 与 tie 现状 | 契合（arena 可复用区域分配） | Rust 都痛苦，tie 自写更甚 |

**决策：stackful**。tiec 是自举编译器，状态机变换是编译器大手术；stackful
只需 trm 提供 `switch_context` 原语（汇编级，unsafe 内可写），编译器几乎不动。

EN: **Decision: stackful**. tiec is a self-hosting compiler, and state-machine transformation is a major compiler surgery; stackful only needs trm to provide the `switch_context` primitive (assembly-level, writable in unsafe), leaving the compiler almost untouched.

```tie
// 语言级语法（编译到 trm 切换原语）
async func fetch(url: string) -> string {
    var data = await http_get(url)    // 挂起协程，不阻塞线程
    return parse(data)
}

var task = spawn(fetch, url)          // 派生协程
var result = await task               // 等待协程完成
```

**决策细节**：
- 语法：**async/await**（显式挂起点，与 actor 的 on 消息处理兼容）
- 栈管理：**固定栈 + 栈大小参数**（`spawn(f, stack_size)`，默认 64KB，
  热协程显式调大）——第一版够用
- 调度器归属：**trm 提供**（M:N 线程池 + 工作窃取），tie 经 unsafe 原语调用

EN: **Decision details**: syntax: **async/await** (explicit suspension points, compatible with actor on-message handlers); stack management: **fixed stacks + a stack-size parameter** (`spawn(f, stack_size)`, default 64KB, hot coroutines explicitly increased) — enough for v1; scheduler ownership: **provided by trm** (M:N thread pool + work stealing), called by tie via unsafe primitives.

### 5.4 Actor
*EN: 5.4 Actors*

```tie
// actor = 状态隔离单元，私有状态 + 消息处理器（on 子句）
actor Counter {
    var n: i64 = 0                    // 私有状态，仅本 actor 可见
    on Inc() { n += 1 }               // 消息处理 = 模式匹配分发
    on Get() -> i64 { return n }      // 同步请求（reply channel）
}

Counter.send(Inc())                   // 投递：消息 move 进邮箱，异步
var v = Counter.ask(Get())            // 同步请求：send + reply 自动配对
```

**决策细节**：
- actor 与线程映射：**默认共享协程池 + 可 pin 专用线程**（`actor Pin` 声明）
- 邮箱模型：**单邮箱 + 模式匹配**（Erlang 式，on 子句按消息类型分发），
  select 多路复用后置，不做进第一版
- send/ask 双形态：send = 异步投递（默认）；ask = 同步请求-应答
  （编译器自动生成 reply channel）
- 生命周期：**结构化并发**（见 5.6）——`concurrent {}` 作用域内派生 actor，
  作用域退出自动排空停止

EN: **Decision details**: actor-to-thread mapping: **shared coroutine pool by default + optional pinned dedicated threads** (the `actor Pin` declaration); mailbox model: **single mailbox + pattern matching** (Erlang-style, on-clauses dispatch by message type), with select multiplexing deferred, not in v1; the send/ask dual forms: send = async delivery (default); ask = synchronous request-response (the compiler auto-generates a reply channel); lifecycle: **structured concurrency** (see 5.6) — actors spawned within a `concurrent {}` scope are drained and stopped automatically when the scope exits.

### 5.5 Channel
*EN: 5.5 Channels*

```tie
var (tx, rx) = channel<i64>()
tx.send(42)           // 值 move 进管道（所有权转移）
var v = rx.recv()     // 接收端获得所有权
```

- **send 即 move**：跨线程零拷贝、零锁、零数据竞争
  - EN: **send is a move**: cross-thread zero-copy, zero-lock, zero data races
- 底层实现：无锁队列（SPSC/MPMC，unsafe 层提供）
  - EN: underlying implementation: lock-free queues (SPSC/MPMC, provided at the unsafe layer)
- channel 生命周期 = 双方引用计数
  - EN: channel lifecycle = reference-counted on both sides

### 5.6 结构化并发（concurrent）
*EN: 5.6 Structured Concurrency (concurrent)*

```tie
concurrent {
    var a = spawn(...)    // 生命周期绑定此块
    var b = spawn(...)
}   // ← 自动 join 全部，无泄漏任务
```

- 消灭"游离任务/泄漏任务"，错误传播清晰
  - EN: eliminates "orphaned/leaked tasks", clean error propagation
- 与 arena 的"区域释放"哲学**完全同构**（都是作用域绑定生命周期）
  - EN: **fully isomorphic** to arena's "region release" philosophy (both bind lifecycle to scope)
- 需要编译器作用域跟踪（中量）
  - EN: needs compiler scope tracking (medium)

### 5.7 unsafe 层：无锁并发（方案 7）
*EN: 5.7 The unsafe Layer: Lock-Free Concurrency (Option 7)*

```tie
unsafe {
    var q: mpsc_queue<i64> = ...      // 无锁队列（channel 内部实现用）
    var counter: atomic<i64> = 0
    counter.fetch_add(1)              // 原子操作 + memory_order
}
```

- 原子操作、锁、共享计数全部归 unsafe——安全代码碰不到
  - EN: atomic operations, locks, and shared counters all belong to unsafe — safe code can't touch them
- 与 Rust 哲学一致：**安全代码做消息传递，unsafe 做共享内存**
  - EN: consistent with the Rust philosophy: **safe code does message passing, unsafe does shared memory**

### 5.8 UI 线程模型（tieui 场景）
*EN: 5.8 UI Thread Model (the tieui scenario)*

```
主线程（UI 线程）：事件轮询 + 渲染 + 组件树所有权
   └── spawn 工作协程：计算/IO/解码（move 数据进，channel 结果回）
        └── 结果通过 channel 回传，主线程 move 进组件树
```

UI 单线程模型（Flutter/浏览器同款）——组件树只被主线程触碰，工作协程纯计算，
无锁 UI。trm 的事件轮询天然适配：`poll_event()` 主线程专用。

EN: The single-threaded UI model (same as Flutter/browser) — the component tree is only touched by the main thread; worker coroutines are pure computation; a lock-free UI. trm's event polling naturally fits: `poll_event()` is main-thread-only.

### 5.9 wasm（webui）兼容策略
*EN: 5.9 wasm (webui) Compatibility Strategy*

**2026-08-15 调研修订**（完整依据见 [webui-research.md](webui-research.md) §3）：

EN: **2026-08-15 research revision** (full basis in [webui-research.md](webui-research.md) §3):

- **阻塞式 IO 用 JSPI（首选）**：JavaScript Promise Integration 已 phase 4
  标准化，Chrome 137+/Firefox 139+ 支持（Safari 未确认）。阻塞式 extern IO
  的 JS import 用 `WebAssembly.Suspending` 包装，wasm 内保持同步风格调用，
  **tie 代码与编译器零改动**。壳层探测 `WebAssembly.Suspending`，缺失时
  （Safari）IO 降级为回调模式（tie 侧 poll 结果）。
  - EN: **blocking IO uses JSPI (preferred)**: JavaScript Promise Integration is standardized at phase 4, supported by Chrome 137+/Firefox 139+ (Safari unconfirmed). The JS imports for blocking extern IO are wrapped with `WebAssembly.Suspending`, keeping synchronous-style calls inside wasm, with **zero changes to tie code and the compiler**. The shell detects `WebAssembly.Suspending`; when missing (Safari), IO degrades to callback mode (tie polls the result).
- **多协程（M:N）wasm 化后置**：stack switching 提案截至 2026-05 仍在设计
  阶段、浏览器未落地 → webui 第一版单线程顺序执行（CLI 迁移应用天然顺序），
  后续可选状态机变换或等 stack switching 落地。
  - EN: **multi-coroutine (M:N) wasm-ification deferred**: as of 2026-05 the stack-switching proposal is still in the design phase and not shipped in browsers → webui v1 executes single-threaded and sequentially (CLI-migrated apps are naturally sequential), with later options of state-machine transformation or waiting for stack switching to land.
- `spawn` 编译为 **Web Worker**（消息传递天然映射 postMessage，
  channel → Worker 消息；Worker 内独立 wasm 实例，无共享内存）
  - EN: `spawn` compiles to a **Web Worker** (message passing naturally maps to postMessage; channels → Worker messages; an independent wasm instance inside the Worker, no shared memory)
- 共享内存原语在 wasm 上不可用（SAB 需 COOP/COEP 跨源隔离，浏览器仍非默认）
  → unsafe 共享路径在 webui 模式报编译错误
  - EN: shared-memory primitives are unavailable on wasm (SAB requires COOP/COEP cross-origin isolation, still not the browser default) → the unsafe shared path reports a compile error in webui mode
- 语义一致：主线程 UI + worker 计算，与 tieui 桌面模型同构
  - EN: consistent semantics: main-thread UI + worker computation, isomorphic to the tieui desktop model

## 6. 嵌入式子集（tie:embedded）
*EN: 6. Embedded Subset (tie:embedded)*

### 6.1 约束（rdu 既定哲学）
*EN: 6.1 Constraints (the rdu established philosophy)*

无 OS/无线程、无堆（仅 i64/f64/bool）、无递归、不链接运行时、
无全局可变状态。完整模型不能跑，需要编译期裁剪。

EN: No OS/threads, no heap (only i64/f64/bool), no recursion, no runtime linking, no mutable global state. The full model cannot run; compile-time trimming is needed.

### 6.2 核心洞察：协程是嵌入式友好的
*EN: 6.2 Key Insight: Coroutines Are Embedded-Friendly*

栈式协程只需要"切换栈 + 保存寄存器"，不需要 OS——纯用户态操作。
**"每个协程一个 OS 线程"才不友好，协程本身是嵌入式的朋友**。

EN: Stackful coroutines only need "switch stacks + save registers", no OS needed — pure user-mode operations. **"One OS thread per coroutine" is what's unfriendly; coroutines themselves are embedded's friend**.

### 6.3 嵌入式子集设计
*EN: 6.3 Embedded-Subset Design*

```tie
// 1. 协程降级：协作式调度（无 M:N，无线程池）
async func read_sensor() -> i64 {
    await delay_ms(10)        // 挂起，让出 CPU 给其他协程
    return adc_read()
}

main_loop() {                 // 协作式调度循环（代替 M:N 调度器）
    while true {
        run_ready_coroutines()
        poll_events()         // 中断置位的事件标志
    }
}

// 2. 无锁 SPSC → 嵌入式最合适的原语（ISR 安全）
interrupt fn on_button_press() {
    event_queue.push(ButtonEvent)   // 无锁 SPSC，ISR 安全（关中断即可）
}

// 3. actor 降级：状态机 + 事件分发
actor ButtonFSM {             // 单 actor = 状态机，事件驱动
    state: Idle | Pressed | Held
    on Press()   { → Pressed }
    on Release() { → Idle }
}
```

### 6.4 编译期裁剪（tie:embedded 文件角色）
*EN: 6.4 Compile-Time Trimming (the tie:embedded file role)*

```tie
// tie:embedded          ← 文件角色（与 tie:library/tie:script 并列）
// 编译器行为：
//   - 禁用：spawn(OS线程)、M:N调度器、动态堆分配、锁原语
//   - 启用：协作式协程、SPSC channel、静态 arena、状态机 actor
//   - 错误：使用禁用特性 = 编译错误（编译期保证，不是运行时）
```

### 6.5 内存模型降级
*EN: 6.5 Memory-Model Degradation*

- 动态 arena 堆分配 → **静态内存池**（编译期固定大小）
  - EN: dynamic arena heap allocation → **static memory pool** (fixed size at compile time)
- 协程栈 → 静态数组（`coro_stack[4][2048]`，编译期声明数量）
  - EN: coroutine stacks → static arrays (`coro_stack[4][2048]`, number declared at compile time)
- 移动语义照常（编译期分析，不需要 OS）
  - EN: move semantics as usual (compile-time analysis, no OS needed)
- unsafe 的 alloc/free → 从静态池分配，无动态堆
  - EN: unsafe alloc/free → allocated from the static pool, no dynamic heap
- 原子操作 → 单核无竞争，编译为普通读写（或关中断）
  - EN: atomic operations → single-core no contention, compiled to ordinary reads/writes (or interrupt-disabling)

### 6.6 与 tieui 嵌入式的咬合
*EN: 6.6 Interlocking with tieui's Embedded Mode*

```
tieui 嵌入式 = 帧缓冲直绘 + 嵌入式并发子集
  主循环：协作式协程 + 事件循环
  ├── 渲染协程：绘制帧缓冲 → LCD
  ├── 输入协程：轮询按键/触摸（或 ISR 事件队列）
  └── 逻辑协程：状态更新（actor 状态机）
```

单线程协作式天然适配"渲染 + 输入 + 逻辑"的 UI 主循环——不需要锁。

EN: Single-threaded cooperative scheduling naturally fits the "render + input + logic" UI main loop — no locks needed.

## 7. 三端能力对比
*EN: 7. Three-End Capability Comparison*

| 特性 | 桌面/服务器 | 嵌入式 | webui (wasm) |
| --- | --- | --- | --- |
| 协程 | 栈式，M:N 调度，工作窃取 | 栈式，协作式主循环 | 单线程顺序 + JSPI IO（多协程后置） |
| channel | MPMC/SPSC 无锁 | SPSC 无锁（ISR 安全） | → Worker 消息 |
| actor | 多 actor 并发 | 单 actor 状态机 | 协程池内调度 |
| 原子/锁 | 真实原子 + memory_order | 关中断/普通读写 | 禁用（编译错误） |
| arena | 动态分配 | 静态内存池 | 动态分配 |
| spawn(线程) | ✅ | ❌ 编译错误 | → Web Worker |
| unsafe 无锁 | ✅ | ✅（更简单） | ❌ 共享路径禁用 |

**同一个语言、同一套语义（协程/消息/所有权），编译目标决定能力**——
这是 tie 的 `tie:xxx` 角色体系的价值延伸。

EN: **The same language and the same semantics (coroutines/message passing/ownership), with the compile target deciding capabilities** — this is the value extension of tie's `tie:xxx` role system.

## 8. 里程碑
*EN: 8. Milestones*

| 阶段 | 内容 | 依赖 |
| --- | --- | --- |
| M0 | 编译器扩展：unsafe + ptr + repr(C) 结构体 + extern 扩展 | tiec 现有链路 |
| M1 | trm：窗口创建 + 绘制 + 事件轮询（tie 写，Win32 起步） | M0 |
| M2 | tieui 框架：组件树、布局、事件分发 | M1 |
| M3 | 内存模型：move 关键字 + arena（P1/P2） | M0 |
| M4 | 并发：协程（stackful）+ actor + channel + concurrent | M3 |
| M5.1 | webui 工具链：tiec `--target=wasm32`（link_exe wasm 分支 + wasm-ld + 显式导出清单 + wasm 版运行时重编译） | M0 |
| M5.2 | libc 桩层（tie 写）：printf/puts→stdout 队列、malloc→arena 分配器、文件→内存桩、数学→LLVM 内建 | M5.1 |
| M5.3 | webui 壳 v1：HTML + JS 桥 + `@xterm/xterm` 6 终端模拟 + 事件队列 + JSPI 包装 | M5.2 |
| M5.4 | 页面化：Canvas 2D 桥 + trm.ui 绘制面 wasm 化（tieui 应用迁移） | M5.3 + M2 |
| M5.5 | tieDB web 化：Worker + OPFS + zd 持久化 | M5.4 |
| M6 | 跨平台：X11/Wayland 后端 | M1 |
| M7 | 嵌入式：tie:embedded 子集 + 静态池 + 协作式调度 | M3 + M4 |
| M8 | owned 模式落地：std/compiler 一次性迁移（无渐进） | M3 |

> 注：M3/M4 与 M1/M2 可并行推进（不同语言面）；M5.x 依赖 wasm 后端先行，
> M5.1-M5.3 串行推进（工具链 → 桩层 → 壳），M5.4/M5.5 可并行。
>
> EN: Note: M3/M4 can proceed in parallel with M1/M2 (different language surfaces); M5.x depends on the wasm backend going first; M5.1-M5.3 advance serially (toolchain → stub layer → shell); M5.4/M5.5 can be parallel.

## 9. 待定决策与前置调查
*EN: 9. Pending Decisions and Advance Investigation*

1. ~~**闭包/函数值**~~ **已定案**（2026-08-15）：A3 func 字面量 + B1 move 捕获 +
   C2 函数指针 + C4 协程统一，允许递归与闭包内 await。
   完整设计见 [closure-model.md](closure-model.md)。spawn(闭包) 直接用闭包式。
   EN: **Decided** (2026-08-15): A3 func literals + B1 move capture + C2 function pointers + C4 coroutine unification, allowing recursion and await inside closures. Full design in [closure-model.md](closure-model.md). `spawn(closure)` directly uses the closure form.
2. **channel select 多路复用**：第一版只做阻塞 recv，select 后置。
   EN: **channel select multiplexing**: v1 only does blocking recv; select is deferred.
3. **actor pin 语法**：`actor Pin` 声明专用线程的形态待细化。
   EN: **actor pin syntax**: the form of the `actor Pin` declaration for dedicated threads is to be refined.
4. ~~**wasm 后端的 async 状态机变换**~~ **取消**（2026-08-15 调研定案）：
   JSPI 替代（webui-research.md §3.1），tiec 后端零改动；待定项改为
   "JSPI 不可用浏览器（Safari）的 IO 降级模式设计"。
   EN: **Canceled** (decided by the 2026-08-15 study): replaced by JSPI (webui-research.md §3.1), zero changes to the tiec backend; the pending item changes to "design of the IO-degradation mode for browsers without JSPI (Safari)".
5. **协程栈默认大小与增长策略**：固定 64KB 起步，动态增长留待第二版。
   EN: **default coroutine-stack size and growth strategy**: fixed 64KB to start; dynamic growth reserved for v2.
6. **arena 逃逸检查的编译策略**：semantic 层静态检查 vs 运行时检查的取舍。
   EN: **compilation strategy for arena-escape checking**: the trade-off between static checking in the semantic layer vs runtime checking.
7. **接口模型（port）** **已定案**（2026-08-15）：P1 显式 impl + D3 双形态分发
   （静态泛型约束 / 动态 port 对象）+ 实现 **I1+I2 混合**（编译器隐式 vtable 为默认，
   用户手写方法表为 escape hatch 归 unsafe）。完整设计见 [port-model.md](port-model.md)。
   EN: **Decided** (2026-08-15): P1 explicit impl + D3 two-form dispatch (static generic constraints / dynamic port objects) + implementation **I1+I2 hybrid** (compiler implicit vtable as the default; user-written method tables as the escape hatch, belonging to unsafe). Full design in [port-model.md](port-model.md).
8. **库/包模型** **已定案**（2026-08-15）：L1c 多文件包 + 预编译为 tieir 分发
   + L3a/L3b 命名空间混合 + L4b port 即接口 + P1b 双版本 + P2c 最小版本选择
   + P3c 双通道 + P4b 接口依赖 + P5a/P5c 手动发布+签名。
   完整设计见 [package-model.md](package-model.md)。
   EN: **Decided** (2026-08-15): L1c multi-file packages + precompiled tieir distribution + L3a/L3b namespace mixing + L4b port-as-interface + P1b dual versions + P2c minimal version selection + P3c dual channel + P4b interface dependency + P5a/P5c manual publishing + signing. Full design in [package-model.md](package-model.md).
9. **unsafe 模型** **已定案**（2026-08-15）：**U3** 语法（块/函数 + 文件级逃生舱）
   + **指针模型**（T2 类型化指针 + T4 切片 + O3 全量操作集 + S1 全归 unsafe
   + U1 ref 通用化）+ **R1** 显式 repr(C) + **E3** extern 强制 unsafe
   + **A1** 语言级 atomic<T> + **I1** asm! 内联汇编 + **M1** alloc/free。
   完整设计见 [unsafe-model.md](unsafe-model.md)。
   EN: **Decided** (2026-08-15): **U3** syntax (blocks/functions + a file-level escape hatch) + **pointer model** (T2 typed pointers + T4 slices + O3 full operation set + S1 all-unsafe + U1 ref commonization) + **R1** explicit repr(C) + **E3** extern forced-unsafe + **A1** language-level atomic<T> + **I1** asm! inline assembly + **M1** alloc/free. Full design in [unsafe-model.md](unsafe-model.md).
10. **窄整数模型** **已定案**（2026-08-15）：L2+L3 字面量推断/后缀 + C2+C3
    拓宽隐式/常量缩窄 + O3 回绕默认 + checked_* + A1 窄宽度算术 + B2 明确移位
    （无 UB）。repr(C)/extern 互操作的数据基础。
    完整设计见 [int-model.md](int-model.md)。
    EN: **Decided** (2026-08-15): L2+L3 literal inference/suffixes + C2+C3 implicit widening/constant narrowing + O3 wrap-around default + checked_* + A1 narrow-width arithmetic + B2 explicit shifts (no UB). The data foundation for repr(C)/extern interop. Full design in [int-model.md](int-model.md).
11. **错误处理模型** **已定案**（2026-08-15）：E2 Result/Option 枚举 + P1 `?` 传播
    + F3 可配置 panic（桌面退出/嵌入式 halt/wasm trap）+ R2 内外分明
    + C1 协程 Result 跨 channel + L1 std 预置。异常（E3）明确排除。
    完整设计见 [error-model.md](error-model.md)。
    EN: **Decided** (2026-08-15): E2 Result/Option enums + P1 `?` propagation + F3 configurable panic (desktop exit/embedded halt/wasm trap) + R2 clear internal/external distinction + C1 coroutine Result across channels + L1 std preset. Exceptions (E3) explicitly excluded. Full design in [error-model.md](error-model.md).

## 10. 关联与影响
*EN: 10. Related and Impact*

- **tiec 自举编译器**：M0/M3/M4 全部落在 compiler/（tie 自写），
  是自举链的又一次能力升级。
  - EN: **the tiec self-hosting compiler**: M0/M3/M4 all land in compiler/ (written in tie), another capability upgrade of the bootstrapping chain.
- **rdu**：嵌入式子集与 rdu 哲学对齐（无堆/无 OS），静态池与 rdu 分层衔接。
  - EN: **rdu**: the embedded subset aligns with rdu's philosophy (no heap/no OS), and the static pool links into rdu's layering.
- **std**：一次性迁移到 owned 模式（无渐进）；新增 concurrency 模块面。
  - EN: **std**: one-time migration to owned mode (no gradualism); a new concurrency module surface added.
- **tieDB**：可作为 webui 迁移应用的数据层示例。
  - EN: **tieDB**: can serve as a data-layer example for webui-migrated apps.