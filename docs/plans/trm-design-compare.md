# 方案对比：trm（tie runtime suite）最终设计备选路径
*EN: Design Comparison: Alternative Paths for the trm (tie runtime suite) Final Design*

> 状态：**方案对比**（2026-08-22 讨论，定稿前依此决策）
> 本文档为 trm **最终设计**的候选方案对比。它不直接定义最终形态，
> 而是把每个关键架构维度铺开多个可选路径、逐项评估取舍，并给出推荐，
> 作为后续**最终设计定稿**（`docs/designs/trm-final-design.md`）的决策依据。
>
> 相关：`docs/plans/trm-arch.md`（规划稿，本文档的精化与重组）、
> `docs/designs/concurrency-model.md`（actor 原生语法，零运行时纯编译）、
> `docs/plans/dynamic-library.md`（M5 动态库，平台桥已可交付）、
> `docs/plans/tieir-format.md`（tieir 字节码契据）。
>
> EN: Status: **Design comparison** (discussion on 2026-08-22, decisions made here before finalization)
> EN: This document compares candidate options for trm's **final design**. It does not directly define the final form; rather, it lays out multiple optional paths for each key architectural dimension, evaluates the trade-offs item by item, and gives recommendations, serving as the basis for decisions in the upcoming **final-design finalization** (`docs/designs/trm-final-design.md`).
> EN: Related: `docs/plans/trm-arch.md` (the planning draft, refined and reorganized by this document), `docs/designs/concurrency-model.md` (actor native syntax, zero-runtime pure compilation), `docs/plans/dynamic-library.md` (M5 dynamic library, platform bridge already deliverable), `docs/plans/tieir-format.md` (the tieir bytecode contract).

## 0. 已对齐的战略决策（2026-08-22 讨论拍板）
*EN: 0. Aligned Strategic Decisions (decided in the 2026-08-22 discussion)*

以下决策**不再进入对比**，作为方案的既定约束：

EN: The following decisions **no longer enter the comparison**; they are fixed constraints of the options:

| 决策点 | 结论 |
| --- | --- |
| 整体架构 | **双层 + 非对称**：纯编译路线 A（保留现状）+ trm 运行时路线 B |
| 路线定位 | 路线 A = 零依赖纯编译（actor/纯逻辑）；路线 B = trm 运行时（新语法/新功能） |
| 引擎层 | **前端/后端分离**：前端 = interp（跨平台解释器）；后端**可替换** |
| GC | **引擎级统一 GC**（interp/JIT 共用堆，处理栈根扫描） |
| 库层形态 | **混合**：纯逻辑静态编入产物；平台实现走动态绑定 |
| 实现语言 | **全 tie 写**（库层 + 平台实现，unsafe extern + repr(C) 桥原生） |
| 平台覆盖 | Windows / Linux / macOS / Android（impl-win32 / impl-posix / impl-macos / impl-android） |
| 本期目标 | 仅产出**最终设计文档**（不实现） |
| 文档流程 | **两步制**：本文档（方案对比）→ 定稿文档 |

EN: This table lists the fixed strategic decisions: a two-layer + asymmetric overall architecture (Route A pure compile + Route B trm runtime); front/back-end separation in the engine layer with a replaceable back end; an engine-level unified GC; a hybrid library-layer form (static pure logic + dynamically bound platform implementation); all-tie implementation language; platform coverage of Windows/Linux/macOS/Android; this phase's goal limited to the final design document (not implementation); and a two-step document flow (this comparison → the finalized document).

---

## 1. 引擎层执行策略（前端 / 后端）
*EN: 1. Engine-Layer Execution Strategy (Front End / Back End)*

引擎层 = tieir 字节码执行。核心问题是：**用哪条执行路径、前后端如何解耦**。

EN: The engine layer = execution of tieir bytecode. The core question: **which execution path to use, and how to decouple the front end from the back end**.

### 方案 A：「纯 interp」前端单例
*EN: Option A: "Pure interp" Front-End Singleton*

```
tieir → interp 解释执行（唯一路径）
```

| 维度 | 评 |
| --- | --- |
| 优点 | 跨端语义一致；启动快；嵌入式/无 LLVM 环境可用；实现最小 |
| 缺点 | 峰值性能约 10-50x 慢于原生；性能敏感程序（算法/图形）不可用 |
| 现实 | interp 已工程化（`compiler/interp/`），T4 会谈过「解释器启动 + JIT 热点」 |

EN: Pros: cross-end semantic consistency; fast startup; usable in embedded/no-LLVM environments; minimal implementation. Cons: peak performance roughly 10-50x slower than native; performance-sensitive programs (algorithms/graphics) unusable. Reality: interp is already engineered (`compiler/interp/`), and T4 discussed "interpreter bootstrap + JIT hotspots".

### 方案 B：「interp + ORC JIT」固定后端
*EN: Option B: "interp + ORC JIT" Fixed Back End*

```
tieir → interp（启动/冷路径）→ 热点 → LLVM ORC JIT（编译成原生）→ 峰值
```

| 维度 | 评 |
| --- | --- |
| 优点 | 峰值 ≈ 原生；HotSpot tiered 心智；复用 llvmgen（tie 写，已打通 tie-IR→LLVM） |
| 缺点 | 后端被 LLVM 锁死；跨平台需要 LLVM ORC 每端可用（Android ARM64 有风险）；LLVM 随包分发体积大 |
| 现实 | llvmgen 现输出 `.ll` 喂 clang；换 ORC 只需「喂 clang → LLVMParseIR+JIT」，一行不动逻辑 |

EN: Pros: peak ≈ native; HotSpot tiered mental model; reuses llvmgen (written in tie, already links tie-IR→LLVM). Cons: the back end is locked to LLVM; cross-platform requires LLVM ORC available on every end (Android ARM64 at risk); LLVM bundled distribution is large. Reality: llvmgen currently outputs `.ll` fed to clang; switching to ORC only needs "feed clang → LLVMParseIR+JIT", without moving a line of logic.

### 方案 C：「interp 前端 + 可替换后端」（推荐）
*EN: Option C: "interp Front End + Replaceable Back End" (recommended)*

```
tieir → interp（前端，跨端一致解释）
             └── 后端接口（Backend trait）：LLVM ORC JIT（默认） | wasm/AOT（扩展）
```

| 维度 | 评 |
| --- | --- |
| 优点 | **解耦成开放性**：interp 保证跨端；后端可换可裁；嵌入式可去后端只留 interp；Android 若无 ORC 可退纯 interp；未来加 wasm/AOT 后端不破前端 |
| 缺点 | 需定义后端接口契约（前端如何把字节码交给后端）；比「固定后端」多一层抽象 |
| 现实 | 前后端共用同一 tieir 与类型系统；前端只做「怎么轮转」，后端做「怎么编译」——职责干净且对称 |

EN: Pros: **decoupled into openness** — interp guarantees cross-end; the back end can be swapped/trimmed; embedded can drop the back end and keep only interp; Android can fall back to pure interp without ORC; future wasm/AOT back ends don't break the front end. Cons: a back-end interface contract must be defined (how the front end hands bytecode to the back end); one more layer of abstraction than a "fixed back end". Reality: the front and back ends share the same tieir and type system; the front end only does "how to interpret", the back end does "how to compile" — clean and symmetric responsibilities.

### 方案 D：「纯 JIT」
*EN: Option D: "Pure JIT"*

```
tieir → ORC JIT（唯一路径）
```

| 维度 | 评 |
| --- | --- |
| 优点 | 无解释器，性能原生 |
| 缺点 | 启动慢（首个函数须编译）；无 LLVM 环境不可用；嵌入式/沙箱场景退化 |

EN: Pros: no interpreter, native performance. Cons: slow startup (first functions must compile); unusable without LLVM; degraded in embedded/sandbox scenarios.

**推荐 C**：interp 前端保证跨端一致与可嵌入，后端接口让性能路径可替换可裁剪。它同时满足
「跨平台一致（路线 B 价值）」与「性能可追（JIT 后端）」且不锁死单一实现。方案 B 是 C 的
特例（后端固定 LLVM），C 向上兼容 B。

EN: **Recommendation C**: the interp front end guarantees cross-end consistency and embeddability, while the back-end interface makes the performance path replaceable and trimmable. It simultaneously satisfies "cross-platform consistency (Route B value)" and "performance can be pursued (JIT back end)" without locking in a single implementation. Option B is a special case of C (back end fixed to LLVM); C is upward compatible with B.

后端接口要点：

EN: Key points of the back-end interface:

```
Backend 接口（引擎层内部）：
  compile(module: tieir_module) -> Executable      // 把字节码模块变成可执行体
  execute(exe, entry: FuncId, args) -> Value        // 调用入口
  invoke(exe, fn: FuncId, args) -> Value            // 动态调用函数（sanbox/热更用）
```

- interp 也实现同一接口（`InterpBackend`）——前后端对引擎调度器透明，可热切换。
  - EN: interp also implements the same interface (`InterpBackend`) — front and back ends are transparent to the engine scheduler and can hot-swap.
- **GC 与后端**：所有后端共享同一托管堆与根扫描（见 §2），JIT 只负责编译，不再管堆。
  - EN: **GC and the back end**: all back ends share the same managed heap and root scanning (see §2); JIT is only responsible for compilation, no longer managing the heap.

---

## 2. GC 落点与执行面关系
*EN: 2. GC Placement and Its Relationship to the Execution Surface*

GC 是运行时最大能力之一。核心问题是：**GC 建在哪层、是否与双执行面统一**。

EN: GC is one of the runtime's biggest capabilities. The core question: **which layer the GC is built at, and whether it is unified with the two execution surfaces**.

### 方案 a：interp 内建 GC（仅服务 interp）
*EN: Option a: GC Built Into interp (serving only interp)*

```
interp 内部托管堆；JIT 后端对象自管（不归 GC 管）
```

| 维度 | 评 |
| --- | --- |
| 优点 | interp 先落地，步伐小 |
| 缺点 | **两套对象模型**：interp 有 GC、JIT 另搞一套 → 跨执行面互操作两个堆（复制/转换），成本长期大于建设期；违背「单运行时单一对象身份」 |

EN: Pros: interp lands first, small steps. Cons: **two object models** — interp has GC and JIT builds another → interoperating two heaps across execution surfaces (copy/convert), a cost that over time exceeds the construction phase; violates "single runtime, single object identity".

### 方案 b：引擎级统一 GC，前后端共用堆（推荐）
*EN: Option b: Engine-Level Unified GC, Shared Heap Across Front and Back Ends (recommended)*

```
引擎层托管堆（对象头 + 遍历 + 回收器）+ 栈根扫描
        ↑            ↑
      interp         ORC JIT 后端
   （解释执行可溯源栈根）  （编译代码参与根扫描/写屏障）
```

| 维度 | 评 |
| --- | --- |
| 优点 | 单一对象身份；interp 与 JIT 可互操作同一批对象（hot SO 提升/cold 降回无搬迁成本）；与 M:N 协程可迁移栈天然配套；诊断/堆 dump 一处实现 |
| 缺点 | 工程量最大：需 JIT 协作（编译代码里的对象引用要登记、潜在的写屏障）；需要**精确 vs 保守根扫描**决策 |
| 现实 | 你的拍板即为本方案；与「引擎级 GC」承诺一致 |

EN: Pros: single object identity; interp and JIT can interoperate on the same set of objects (hot SO promotion / cold demotion with no relocation cost); naturally pairs with M:N coroutines' migratable stacks; diagnostics/heap dump implemented in one place. Cons: the largest engineering effort — requires JIT cooperation (object references in compiled code must be registered, with potential write barriers); requires a **precise vs conservative root-scanning** decision. Reality: your call is this option; consistent with the "engine-level GC" commitment.

关键子决策（displacing 到定稿继续细化，不在此定）：

EN: Key sub-decisions (deferred to the finalization for further detail, not decided here):

- **精确根扫描 vs 保守根扫描**：精确需编译器/JIT 产栈图（写出每处 GC 安全点的存活根），
  保守扫描用"栈上看似指针的值"，器量小但假根多、可迁移性差。**路线 B 采用可迁移栈 + M:N**，
  强烈倾向**精确根扫描**（编译期产栈图，interp 与 JIT 通用）。
  - EN: **precise vs conservative root scanning**: precise requires the compiler/JIT to produce stack maps (writing the live roots at each GC safepoint); conservative scanning uses "values on the stack that look like pointers", small in implementation but with many false roots and poor migratability. **Route B uses migratable stacks + M:N**, strongly favoring **precise root scanning** (stack maps produced at compile time, common to interp and JIT).
- **移动式 vs 非移动式 GC**：移动式（压缩/分代搬运）配精确根扫描效率高；非移动式（mark-sweep）
  简单但碎片。倾向**分代 + 移动式**，量力后置优化。
  - EN: **moving vs non-moving GC**: moving (compacting/generational relocation) is efficient with precise root scanning; non-moving (mark-sweep) is simple but fragmented. Preference: **generational + moving**, with optimization deferred within capacity.
- **与路线 A 的关系**：路线 A 无 GC（确定性释放保持现状）；GC 是**路线 B 独有能力**。
  同一份源码在路线 A/B 的表现不同——这是双路线的自然结果，文档里讲清楚。
  - EN: **relationship to Route A**: Route A has no GC (deterministic release keeps the status quo); GC is a **Route-B-only capability**. The same source behaves differently on Route A/B — a natural result of the dual routes, to be explained clearly in the document.

**推荐 b，但要在定稿里明确「精确根扫描」这个决策**——它决定 JIT 代码生成难度与 M:N 可迁移栈能否成立。

EN: **Recommendation b, but the "precise root scanning" decision must be made explicit in the finalization** — it determines the difficulty of JIT code generation and whether M:N migratable stacks can hold.

---

## 3. 库层形态：静态 / 动态 / 混合
*EN: 3. Library-Layer Form: Static / Dynamic / Hybrid*

库层 = 业务能力面（terminal/process/fs/... + 工具集成）。核心问题是：以什么形态交付给应用。

EN: The library layer = the business-capability surface (terminal/process/fs/... + tool integration). The core question: in what form it is delivered to applications.

### 方案 ①「全静态」
*EN: Option 1 "All Static"*

```
库层 tie 源码 import 即编入产物，零动态库
```

| 维度 | 评 |
| --- | --- |
| 优点 | 零依赖、零分发、符号内联快；与路线 A 现状一致 |
| 缺点 | 平台实现（win32/posix）也编进去 → 每平台需各自交叉编译产物；平台实现更新 → 应用须重编 |

EN: Pros: zero dependencies, zero distribution, fast symbol inlining; consistent with Route A's status quo. Cons: platform implementations (win32/posix) are also compiled in → each platform needs its own cross-compiled output; platform-implementation updates → the app must recompile.

### 方案 ②「全动态」
*EN: Option 2 "All Dynamic"*

```
库层 → trm.dll / trm.so，运行期 LoadLibrary/dlopen 延迟绑定
```

| 维度 | 评 |
| --- | --- |
| 优点 | 平台实现一次编译，应用按版本指向；延迟绑定支持运行时分发（P6） |
| 缺点 | **M5 边界规则限制**：导出函数参数/返回仅标量 + string（table/map/struct 不可跨库）；引入分发/版本/ABI 负担 |
| 现实 | M5 已交付但边界严——库层若传复杂结构跨库会被拒 |

EN: Pros: platform implementation compiled once, apps point by version; lazy binding supports runtime distribution (P6). Cons: **M5 boundary-rule restrictions** — exported function parameters/returns are only scalars + string (table/map/struct cannot cross the library boundary); introduces distribution/version/ABI burdens. Reality: M5 is delivered but with strict boundaries — passing complex structs across the library boundary would be rejected.

### 方案 ③「混合：逻辑静态 + 平台动态」（推荐）
*EN: Option 3 "Hybrid: Static Logic + Dynamic Platform" (recommended)*

```
库层 = 两半
├── 纯逻辑（terminal/fs/env/net 语义层）→ 静态编译进产物（tie 源码 import）
└── 平台实现（impl-win32/posix/macos/android）→ 动态绑定（trm_platform.dll/.so）
```

| 维度 | 评 |
| --- | --- |
| 优点 | **各自最优**：逻辑静态=零依赖内联、符号快；平台动态=一次编译多平台、可热更、按版本分发。**M5 边界规则不再是障碍**——平台桥只需要导出标量 + 句柄（intptr）+ string，复杂数据以 **repr(C) 结构 + intptr 句柄**在桥内外传递（Win32 惯例） |
| 缺点 | 两层形态带来的分割成本：需定义**平台桥 ABI**（平台实现对外暴露的最小 C ABI 面） |
| 现实 | 你的拍板即本方案；平台桥走 M5 动态库能力，边界面收窄到「repr(C) 结构体 + 指针句柄 + 字符串」——这正是 unsafe-model + repr(C) 的设计主战场 |

EN: Pros: **each optimal** — static logic = zero-dependency inlining and fast symbols; dynamic platform = one compile across platforms, hot-updatable, versioned distribution. **The M5 boundary rule is no longer an obstacle** — the platform bridge only needs to export scalars + handles (intptr) + string, and complex data crosses the bridge as **repr(C) structs + intptr handles** (the Win32 convention). Cons: the split cost of the two forms — a **platform-bridge ABI** must be defined (the minimal C-ABI surface the platform implementation exposes). Reality: your call is this option; the platform bridge uses M5 dynamic-library capability, narrowing the boundary surface to "repr(C) structs + pointer handles + strings" — exactly the design battleground of unsafe-model + repr(C).

关键子决策（定稿继续细化）：

EN: Key sub-decisions (further refined at finalization):

- **平台桥 ABI 面**缺一不可：`trm_platform.dll` 导出一组固定符号（`pl_window_create`
  `pl_paint_*` ...），参数全为 `i64/ptr`（repr(C) 句柄/标量），无 table/struct 直接跨库。
  - EN: **the platform-bridge ABI surface is indispensable**: `trm_platform.dll` exports a fixed set of symbols (`pl_window_create` `pl_paint_*` ...), with all parameters as `i64/ptr` (repr(C) handles/scalars), no table/struct crossing the library boundary directly.
- **句柄即 intptr**：窗口/设备/上下文之类以 `i64` 句柄跨桥（复用 unsafe model `guard<ext>` 凭据思想）。
  - EN: **handle = intptr**: windows/devices/contexts cross the bridge as `i64` handles (reusing the unsafe model's `guard<ext>` credential idea).
- **调度**：平台桥是否允许回调进业务层（事件驱动）→ 定稿明确事件契约（复用 tucore E3/D2 命令列表心智）。
  - EN: **scheduling**: whether the platform bridge allows callbacks into the business layer (event-driven) → the finalization clarifies the event contract (reusing the tucore E3/D2 command-list mental model).

**推荐 ③**，与战略吻合且绕开 M5 边界限制。

EN: **Recommendation 3**, consistent with the strategy and bypassing the M5 boundary restriction.

---

## 4. 实现语言：全 tie vs 引入 native
*EN: 4. Implementation Language: All tie vs Introducing Native*

库层与平台实现用什么语言写。核心问题是：**是否守住 0-Rust 自举灵魂**。

EN: What language the library layer and platform implementation are written in. The core question: **whether to hold the 0-Rust bootstrapping soul**.

### 方案 α「全 tie 写」推荐
*EN: Option α "All written in tie" (recommended)*

```
库层 + 平台实现全部 tie 源码，unsafe extern + repr(C) 桥 Win32/POSIX/AppKit/NDK
```

| 维度 | 评 |
| --- | --- |
| 优点 | 保 0-Rust 自举；生态价值（std/ext 已有大量 tie 纯逻辑，如 std/fs/net/process）；跨平台一致（同一 tie 源码跑四端）；平台实现与路线 A 产品用同一语言，心智统一 |
| 缺点 | 平台实现需 unsafe extern 大量原生调用——开发成本集中在此；repr(C) 结构布局要与 C 精确对齐 |
| 现实 | unsafe/ptr/repr(C)/extern 已全部就绪（S1.2）；runtime.a 已退役，纯逻辑已全部 tie/内联 libc；方向已铺平 |

EN: Pros: preserves 0-Rust bootstrapping; ecosystem value (std/ext already has a lot of tie pure logic, e.g. std/fs/net/process); cross-platform consistency (the same tie source runs on all four ends); the platform implementation shares the same language as Route-A products, a unified mental model. Cons: the platform implementation needs unsafe extern with many native calls — development cost concentrates here; repr(C) struct layouts must align precisely with C. Reality: unsafe/ptr/repr(C)/extern are all ready (S1.2); runtime.a has retired; all pure logic is tie/inlined libc; the path is paved.

### 方案 β「platform 层少量 C」
*EN: Option β "A Little C in the platform Layer"*

```
纯逻辑 tie，平台桥 C extern（impl-*.c）
```

| 维度 | 评 |
| --- | --- |
| 优点 | 平台桥 C 写更直接（C 接近 Win32 API），免 tie 写 extern 桥接 |
| 缺点 | 偏离 0-Rust 轴线；C 工具链分发负担；四端各有一份 C 维护 |

EN: Pros: writing the platform bridge in C is more direct (C is close to the Win32 API), avoiding tie-written extern bridging. Cons: deviates from the 0-Rust axis; C toolchain distribution burden; each of the four ends has a C codebase to maintain.

### 方案 γ「引擎 native + 库层 tie」
*EN: Option γ "Native Engine + tie Library Layer"*

```
引擎层（interp/GC/JIT）用 C/Rust 写；库层 tie 写
```

| 维度 | 评 |
| --- | --- |
| 优点 | 引擎性能最好、最接近系统 |
| 缺点 | **致命冲突**：0-Rust 自举灵魂被打破；引擎是编译器外的第二个巨型 native 工程；与 tiec 自举的哲学完全背离 |

EN: Pros: the engine has the best performance and is closest to the system. Cons: **fatal conflict** — the 0-Rust bootstrapping soul is broken; the engine becomes a second giant native project outside the compiler; completely diverges from tiec's bootstrapping philosophy.

**推荐 α**（全 tie 写）。你已拍板「tie-win/tie-linux 用 tie 写」。引擎层（interp/GC/JIT）
也倾向 tie 写（复用 `compiler/interp/` 已是 tie），保持自举——这是本项目的立身根本。

EN: **Recommendation α** (all written in tie). You've decided "tie-win/tie-linux written in tie". The engine layer (interp/GC/JIT) also leans toward tie (reusing `compiler/interp/`, which is already tie), keeping bootstrapping — the very foundation of this project.

> 注：引擎层是否必然全 tie？interp 已 tie 化；GC/栈图生成属于 tiec 侧 + irgen（tie 写）
> 能产；ORC 接入是「tie 写 llvmgen 输出 → C API 调用」——引擎核心逻辑仍可全 tie，仅
> 在最底层调 LLVM C 接口。定稿需给出「interp/GC tie 写、LLVM 仅作后端 C 依赖」的明确分层。
>
> EN: Note: must the engine layer necessarily be all tie? interp is already tie-ified; GC/stack-map generation is on the tiec side + irgen (written in tie) and can be produced; ORC integration is "tie-written llvmgen output → C-API calls" — the engine-core logic can still be all tie, only calling the LLVM C interface at the very bottom. The finalization must give a clear layering of "interp/GC written in tie, LLVM only as a back-end C dependency".

---

## 5. 能力落地顺序（分期）
*EN: 5. Capability Rollout Order (Phased)*

路线 B 的运行时能力面很大。核心问题是：**哪些先做、按什么依赖序**。

EN: Route B's runtime capability surface is large. The core question: **which to do first, and in what dependency order**.

| 候选批次 | 内容 | 依赖 | 价值 |
| --- | --- | --- | --- |
| **P0** | tieir 加载 + 校验 + interp 执行（跨端） | tieir_ser 已就绪 | 打通「编译器发 tieir → trm 执行」最小闭环 |
| **P1** | 库层起步（terminal/process/fs/env/session）+ 平台桥 | P0 + M5 动态库 | 让路线 B 产出第一个真实应用 |
| **P2** | 引擎级 GC + M:N 协程 + 可迁移栈 | P0 | 运行时杀手锏；GC 是 M:N 前提 |
| **P3** | ORC JIT 后端（热点性能） | P0 + 栈图（P2） | 峰值性能 |
| **P4** | 反射/内省 + 动态加载/热更 + 沙箱/校验强化 + 诊断 | P2（对象模型） | 生态长尾 |

EN: This table lists the candidate batches — P0 (tieir load + validation + interp execution): opens the minimal closed loop of "compiler emits tieir → trm executes"; P1 (library layer start + platform bridge): lets Route B produce the first real app; P2 (engine-level GC + M:N coroutines + migratable stacks): the runtime's killer feature, GC being a prerequisite for M:N; P3 (ORC JIT back end): peak performance; P4 (reflection/introspection + dynamic loading/hot-reload + sandbox/validation strengthening + diagnostics): ecosystem long tail.

- **依赖链**：P0→P1 线性（先字节码执行再库层）；P2 之后 GC 成为对象模型底座，
  P3（JIT 精确根扫描）依赖 P2 的栈图；P4 依赖 P2 的统一对象身份。
  - EN: **dependency chain**: P0→P1 is linear (bytecode execution first, then the library layer); after P2, GC becomes the object-model foundation, P3 (JIT precise root scanning) depends on P2's stack maps; P4 depends on P2's unified object identity.
- **不成 P0-P4 严格串行**：P1 库层可与 P2 并行（库层多用标量 + 句柄，不强依赖 GC）；
  若 P3 JIT 成本过高可后置，interp 已是可用形态。
  - EN: **not strictly serial P0-P4**: the P1 library layer can run parallel with P2 (the library layer mostly uses scalars + handles, not strongly dependent on GC); if P3 JIT cost is too high it can be deferred, and interp is already a usable form.
- **路线 B 第一个可演示里程碑**：P0+P1 交集 —— `import "trm:terminal"` → tiec 发 tieir →
  trm interp 执行，调 terminal 打印，平台桥 win32 动态加载。
  - EN: **Route B's first demonstrable milestone**: the P0+P1 intersection — `import "trm:terminal"` → tiec emits tieir → executed by trm interp, calling terminal to print, with the win32 platform bridge dynamically loaded.

---

## 6. 版本化 / 分发 / 跨平台一致
*EN: 6. Versioning / Distribution / Cross-Platform Consistency*

### 6.1 形态
*EN: 6.1 Form*

```
trm.dll / trm.so / trm.dylib / libtrm.so（Android）——动态库延迟绑定（平台桥主形态）
+ 库层纯逻辑静态（随应用）
+ trm-embedded 子集（静态链接，无动态库，纯 interp）
```

### 6.2 版本策略（沿用 trm-arch §8）
*EN: 6.2 Version Strategy (following trm-arch §8)*

| 项 | 值 |
| --- | --- |
| 版本号 | `major.minor.patch`；major 变 = ABI 破坏 |
| ABI 绑定 | 应用声明 `trm@^x`，机器只有别的 major → 拒绝加载 |
| LLVM | 随 trm 分发（vendored 经验）；无 LLVM 环境退纯 interp |
| min_tiec | 编译期校验编译器能力（unsafe/repr(C)/协程） |

### 6.3 跨平台一致
*EN: 6.3 Cross-Platform Consistency*

- 语义契约 + 四端行为测试矩阵（继承 trm-arch §6）；
  - EN: semantic contracts + four-end behavior test matrix (inherited from trm-arch §6);
- **引擎核心跨端一致**（interp/GC/对象模型平台无关）；平台差异只在平台桥（extern 实现）。
  ——这比「JIT 跨端」可控得多（interp 天然可移植）。
  - EN: **the engine core is cross-end consistent** (interp/GC/object model is platform-independent); platform differences live only in the platform bridge (extern implementation) — far more controllable than "JIT across ends" (interp is naturally portable).

---

## 7. 推荐路径汇总
*EN: 7. Recommended-Path Summary*

| 维度 | 推荐 | 一句话理由 |
| --- | --- | --- |
| 引擎层 | **interp 前端 + 可替换后端**（C） | 跨端一致 + 性能可追 + 后端可裁/可换 |
| GC | **引擎级统一 GC 共用堆**（b）+ **精确根扫描** | 单一对象身份；配 M:N 可迁移栈 |
| 库层 | **逻辑静态 + 平台动态**（③） | 各自最优；绕开 M5 边界限制 |
| 平台桥 | track.repr(C) **句柄 + 标量 + string** 面 | 与 unsafe-model 一致，四端同构 |
| 实现语言 | **全 tie 写**（α） | 保 0-Rust 自举；std/compiler 已 tie 化 |
| 能力序 | P0 字节码 → P1 库层 → P2 GC/M:N → P3 JIT → P4 生态 | 依赖链最短、价值优先 |
| 形态/版本/一致性 | 动态库 + 版本 ABI + 契约矩阵 | 沿用 trm-arch 已定决策 |

EN: This table summarizes the recommendations per dimension: an interp front end + replaceable back end (C) for the engine layer (cross-end consistency + performance pursuit + trimmable/swappable back end); an engine-level unified GC with a shared heap (b) + precise root scanning (single object identity, paired with M:N migratable stacks); static logic + dynamic platform (3) for the library layer (each optimal, bypassing the M5 boundary restriction); a repr(C) handle + scalar + string platform-bridge surface (consistent with unsafe-model, isomorphic across the four ends); all-tie implementation (α) (preserves 0-Rust bootstrapping; std/compiler already tie-ified); the capability order P0 bytecode → P1 library → P2 GC/M:N → P3 JIT → P4 ecosystem (shortest dependency chain, value first); and dynamic library + version ABI + contract matrix for form/version/consistency (following trm-arch's decided decisions).

> **核心洞察**：本方案相比 trm-arch 的最大变化不是「堆了更多层」，而是**把引擎层的
> JIT 从「唯一定位」降为「可替换后端之一」**，把 **GC 提到引擎级共用**（而非 interp
> 私藏），并借 **interp 前端 + 语义契约**把跨平台一致从「依赖每端 JIT」改为「依赖平台
> 无关引擎核心 + 平台桥」——跨平台可控性显著提升，同时完整保留运行时独有能力。
>
> EN: **Core insight**: compared to trm-arch, the biggest change of this option is not "piling on more layers", but **demoting the engine layer's JIT from "sole positioning" to "one of several replaceable back ends"**, **raising GC to engine-level sharing** (rather than interp keeping it private), and, via **the interp front end + semantic contracts**, changing cross-platform consistency from "depending on per-end JIT" to "depending on a platform-independent engine core + platform bridge" — significantly improving cross-platform controllability while fully preserving the runtime's unique capabilities.

---

## 8. 定稿文档前仍须细化的决策点
*EN: 8. Decision Points Still Needing Specification Before the Finalization Document*

1. **精确根扫描的实现策略**：interp 与 JIT 共用一套栈图，还是各自产栈图（定稿给出方案）。
   EN: **precise root-scanning implementation strategy**: whether interp and JIT share one set of stack maps or each produces its own (the finalization gives a plan).
2. **分代/移动式与否**：第一版 GC 策略（mark-sweep 起步 vs 直接分代 + 移动）。
   EN: **generational/moving or not**: the v1 GC strategy (mark-sweep start vs direct generational + moving).
3. **平台桥 ABI 面**：固定导出符号清单、句柄传递约定、事件回调进业务层的契约。
   EN: **platform-bridge ABI surface**: the fixed exported-symbol list, handle-passing conventions, and the contract for event callbacks entering the business layer.
4. **与 actor 的衔接**：actor 路线 A 纯编译；路线 B 是否给 actor 表达「M:N 提升」可选升级，
   且语法零改动（concurrency-model §10 已留此口）。
   EN: **integration with actors**: actors on Route A compile purely; whether Route B gives actors an optional "M:N promotion" upgrade expression, with zero syntax changes (concurrency-model §10 already left this opening).
5. **JIT 后端一致性**：后端是「热点替换」还是「全模块编译」；与 interp 语义边界的测试矩阵。
   EN: **JIT back-end consistency**: whether the back end is "hotspot replacement" or "whole-module compilation"; the test matrix for the semantic boundary with interp.
6. **LLVM 分发**：四端 ORC 可用性（Android ARM64 需实验），不可用端退化纯 interp。
   EN: **LLVM distribution**: ORC availability on the four ends (Android ARM64 needs experiments); unavailable ends degrade to pure interp.

---

## 9. 待确认（本文档为草稿，待用户审阅）
*EN: 9. Pending Confirmation (this document is a draft, awaiting user review)*

确认后据此产出 **`docs/designs/trm-final-design.md`** 定稿。

EN: Upon confirmation, **`docs/designs/trm-final-design.md`** finalization is produced accordingly.