# 规划：tie 实施路线图（多会话并行执行）
*EN: Plan: tie Implementation Roadmap (Multi-Session Parallel Execution)*

> 状态：**规划**（2026-08-15 定稿，待执行）
> EN: Status: **Plan** (finalized 2026-08-15, pending execution)
> 本文档整合全部 19 份设计文档为可执行实施路线图。
> EN: This document consolidates all 19 design documents into an executable implementation roadmap.
> 执行模式：**多会话并行**（主控只规划与验收，不亲自写代码；
> EN: Execution mode: **multi-session parallel** (the controller only plans and accepts/delivers, never writing code itself;
> 每个工作单元 = 独立会话的可交付物）。
> EN: each work unit = the deliverable of an independent session).
> 决策确认：
> EN: Confirmed decisions:
> 1. S1.1 LLVM 升级先行独立推进
> EN: 1. S1.1 LLVM upgrade proceeds first, independently.
> 2. 多会话并行实现（主控验收）
> EN: 2. Multi-session parallel implementation (controller accepts).
> 3. **M3 移动语义提前到阶段 1**（避免后续特性建立在旧语义上）
> EN: 3. **M3 move semantics moved up to Stage 1** (to avoid later features being built on the old semantics).
> 4. tieconsole + 嵌入式纳入本年度目标
> EN: 4. tieconsole + embedded are included in this year's goals.
> 5. **时间约束：全部工作 1 星期内完成**（2026-08-15 决策）——
> EN: 5. **Time constraint: all work completed within 1 week** (2026-08-15 decision) —
>    高并行度执行，多会话同时推进，主控密集协调验收
> EN:    execute with high parallelism, multiple sessions advancing simultaneously, the controller coordinating acceptance intensively.
> 6. **时间观念修正（2026-08-15）**：AI 写代码比人工快 100 倍——
> EN: 6. **Time-perception correction (2026-08-15)**: AI writes code 100x faster than humans —
>    1 周是保守上限（缓冲），实际冲刺按"最快可达"调度，
> EN:    1 week is a conservative ceiling (buffer); the actual sprint is scheduled by "fastest achievable",
>    每波次不设固定 Day 门槛，依赖验收通过即启动下一波
> EN:    each wave has no fixed Day gate; the next wave starts as soon as its dependencies pass acceptance.
> 关联：ui-framework（里程碑 M0-M8）、全部专项模型文档（unsafe/int/error/
> EN: Related: ui-framework (milestones M0-M8), all the specialized model documents (unsafe/int/error/
> closure/port/package/role/string/macro/tieir/trm/tucore/tieconsole/tsp/
> EN: closure/port/package/role/string/macro/tieir/trm/tucore/tieconsole/tsp/
> build-config/hw-accel/llvm-upgrade）。
> EN: build-config/hw-accel/llvm-upgrade).
> 并发：语言级并发原语（原生 actor + trm 协程）的设计见
> EN: Concurrency: the design of the language-level concurrency primitives (native actor + trm coroutine) is in
> [docs/designs/concurrency-model.md](../designs/concurrency-model.md)。
> EN: [docs/designs/concurrency-model.md](../designs/concurrency-model.md).

## 0. 执行模式（多会话并行，1 周冲刺）
*EN: 0. Execution Mode (Multi-Session Parallel, 1-Week Sprint)*

```
主控（本会话）：规划 + 任务拆解 + 验收 + 密集协调
  │
  ├── 并行波 1：会话 A(S1.1) + B(S1.2-1.4) + C(S1.5) + F(webui 调研)
  ├── 并行波 2：会话 D(S2.1) + E(S2.2) + G(S2.3+S2.4) + H(S3.1)
  ├── 并行波 3：S3.2 + S3.3 + S3.4 + S4.1 + S4.2
  ├── 并行波 4：S4.3 + S4.4 + S4.5 + S4.6 + S4.7
  └── 每个单元完成后：验收（编译零错误 + 回归测试）→ 提交推送双远端
```

- **1 周时间盒（保守上限）**：AI 写代码比人工快 100 倍——全部 17 个单元
  按"最快可达"调度，1 周是缓冲而非目标
  EN: **1-week time box (conservative ceiling)**: AI writes code 100x faster than humans — all 17 units are scheduled by "fastest achievable"; 1 week is a buffer, not a target.
- **高并行度**：同一时间 4-6 个会话并行推进（远超常规串行）
  EN: **High parallelism**: 4-6 sessions advance in parallel at the same time (far beyond normal serial work).
- 会话间依赖通过"验收门槛"衔接；主控全天候协调
  EN: Inter-session dependencies are linked through "acceptance gates"; the controller coordinates around the clock.
- 风险控制：单元粒度已拆到最小（每单元独立可交付），
  依赖尽量消除（webui 调研提前、S1.1 独立）
  EN: Risk control: units are split to the minimum (each independently deliverable), and dependencies are minimized (webui research moved up; S1.1 is independent).
- 主控不做实现，只做：任务拆解、依赖协调、验收、提交推送
  EN: The controller does not implement; it only does: task breakdown, dependency coordination, acceptance, and commit-push.

## 阶段 1：地基加固 + 移动语义
*EN: Stage 1: Foundation Hardening + Move Semantics*

> 目标：语言核心互操作能力 + 内存模型底座。**并行波 1**。
> EN: Goal: language-core interop capability + the memory-model foundation. **Parallel Wave 1**.

### S1.1 LLVM 升级（独立，先行）✅ 已完成（2026-08-15）
*EN: S1.1 LLVM Upgrade (independent, first) ✅ Done (2026-08-15)*

- **内容**：LLVM 18.1.8 → 22.1.8（见 [llvm-upgrade.md](llvm-upgrade.md)）
  EN: **Content**: LLVM 18.1.8 → 22.1.8 (see [llvm-upgrade.md](llvm-upgrade.md)).
- **交付**：vendored LLVM 22.1.8 替换 + 回归全绿
  EN: **Deliverable**: vendored LLVM 22.1.8 replacement + all-green regression.
- **验收**：compiler/tests + _driver_test 行为等价通过；IR 语法无错；MSVC ABI 回归
  EN: **Acceptance**: compiler/tests + _driver_test behavioral equivalence pass; no IR syntax errors; MSVC ABI regression.
- **并行**：与其他会话完全独立
  EN: **Parallelism**: fully independent of other sessions.
- **实现记录**：D:\LLVM 切换 22.1.8（18 备份 D:\LLVM18）；toolchain.tie 适配 clang 22
  默认 lld-link（非 vendored 显式 -fuse-ld=link）；回归全绿（详见 llvm-upgrade.md §5.2a）
  EN: **Implementation record**: D:\LLVM switched to 22.1.8 (18 backed up to D:\LLVM18); toolchain.tie adapted to clang 22's default lld-link (non-vendored explicitly uses -fuse-ld=link); regression all green (see llvm-upgrade.md §5.2a).

### S1.2 M0：unsafe 语法（语言地基）
*EN: S1.2 M0: unsafe Syntax (Language Foundation)*

- **内容**：unsafe（U3）+ ptr<T>/slice<T>（T2/T4/O3）+ repr(C)（R1）+
  extern 强制 unsafe（E3）+ atomic<T>（A1）+ asm!（I1）+ alloc/free（M1）
  （见 [unsafe-model.md](unsafe-model.md)）
  EN: **Content**: unsafe (U3) + ptr<T>/slice<T> (T2/T4/O3) + repr(C) (R1) + extern-forced unsafe (E3) + atomic<T> (A1) + asm! (I1) + alloc/free (M1) (see [unsafe-model.md](unsafe-model.md)).
- **交付**：编译器支持 unsafe 全能力；示例：unsafe fn 调 Win32 API
  EN: **Deliverable**: the compiler supports the full unsafe capability; example: an unsafe fn calls the Win32 API.
- **验收**：编译零错误；unsafe 边界检查生效；repr(C) 布局精确
  EN: **Acceptance**: zero compile errors; unsafe-boundary checks in effect; repr(C) layout exact.
- **状态**：✅ 完成（2026-08-15，S1.2 落地，tiec 自举 0-Rust；
  详见 unsafe-model.md 实现记录）
  EN: **Status**: ✅ done (2026-08-15; S1.2 landed; tiec bootstraps with 0-Rust; see unsafe-model.md implementation record).

### S1.3 窄整数（互操作前置）
*EN: S1.3 Narrow Integers (Interop Prerequisite)*

- **内容**：i8/i16/i32/u8/u16/u32/u64/f32（L2+L3 字面量/C2+C3 转换/
  O3 溢出/A1 算术/B2 移位）（见 [int-model.md](int-model.md)）
  EN: **Content**: i8/i16/i32/u8/u16/u32/u64/f32 (L2+L3 literals / C2+C3 conversions / O3 overflow / A1 arithmetic / B2 shifts) (see [int-model.md](int-model.md)).
- **交付**：窄整数完整语义 + checked_* + as_* 转换族
  EN: **Deliverable**: complete narrow-integer semantics + the checked_* + as_* conversion families.
- **验收**：repr(C) 结构体字段宽度精确匹配 C ABI
  EN: **Acceptance**: repr(C) struct field widths exactly match the C ABI.
- **状态**：✅ 完成（2026-08-15，S1.3 落地，tiec 自举 0-Rust；
  详见 int-model.md 实现记录）
  EN: **Status**: ✅ done (2026-08-15; S1.3 landed; tiec bootstraps with 0-Rust; see int-model.md implementation record).

### S1.4 角色系统扩展
*EN: S1.4 Role-System Extension*

- **内容**：R2 多角色 + R3 参数化 + 文件名声明（F1/R3）
  + db:vector 向量数据库角色（见 [role-model.md](role-model.md)）
  EN: **Content**: R2 multi-role + R3 parameterization + filename declaration (F1/R3) + the db:vector vector-database role (see [role-model.md](role-model.md)).
- **交付**：`type tie<db:vector, owned>` 解析 + `xxx.db-vector.tie` 文件名一致检查
  EN: **Deliverable**: `type tie<db:vector, owned>` parsing + `xxx.db-vector.tie` filename-consistency checking.
- **验收**：不一致 = 编译错误；角色语法子集约束生效
  EN: **Acceptance**: inconsistency = a compile error; the role-syntax subset constraints take effect.
- **状态**：✅ 完成（2026-08-15，S1.4 落地，prep+driver 双端；
  详见 role-model.md 实现记录）
  EN: **Status**: ✅ done (2026-08-15; S1.4 landed on both prep and driver; see role-model.md implementation record).

### S1.5 M3：移动语义 + arena（提前到阶段 1）
*EN: S1.5 M3: Move Semantics + arena (Moved to Stage 1)*

- **内容**：live/moved 状态跟踪 + 所有权析构 + arena 块 + 逃逸检查
  + **std/compiler 一次性迁移**（无渐进，见 [ui-framework.md](ui-framework.md) §4.4）
  EN: **Content**: live/moved state tracking + ownership destructors + arena blocks + escape checking + **one-shot migration of std/compiler** (no gradual rollout; see [ui-framework.md](ui-framework.md) §4.4).
- **交付**：默认移动语义 + arena 区域 + std/compiler 全量迁移
  EN: **Deliverable**: default move semantics + arena regions + full std/compiler migration.
- **验收**：move 示例正确；arena 释放正确；编译器自身迁移后自举成功
  EN: **Acceptance**: move examples correct; arena release correct; the compiler itself bootstraps successfully after migration.
- **并行**：与 S1.2-1.4 可部分并行（不同语言面），但影响 std/compiler
  需与后续单元衔接
  EN: **Parallelism**: partially parallel with S1.2-1.4 (different language surfaces), but the std/compiler impact must align with later units.

## 阶段 2：语义升级
*EN: Stage 2: Semantic Upgrade*

> 目标：字符串/闭包/错误/接口——语言表达力完整。**并行波 2**。
> EN: Goal: strings/closures/errors/interfaces — complete language expressiveness. **Parallel Wave 2**.

### S2.1 字符串模型
*EN: S2.1 String Model*

- **内容**：{ptr,len} 二进制安全 + 迭代器（chars/char_indices）+
  StringBuilder + SSO + 边界自动 NUL（见 [string-model.md](string-model.md)）
  EN: **Content**: {ptr,len} binary-safe + iterators (chars/char_indices) + StringBuilder + SSO + automatic boundary NUL (see [string-model.md](string-model.md)).
- **依赖**：S1.5（移动语义）
  EN: **Dependency**: S1.5 (move semantics).
- **验收**：字符串含 \0 + len O(1) + 迭代器 + FFI 零拷贝
  EN: **Acceptance**: strings contain \0 + len O(1) + iterators + zero-copy FFI.

### S2.2 闭包
*EN: S2.2 Closures*

- **内容**：func 字面量（A3）+ move 捕获（B1）+ 函数指针（C2）+
  递归/闭包内 await（见 [closure-model.md](closure-model.md)）
  EN: **Content**: func literals (A3) + move capture (B1) + function pointers (C2) + recursion/await inside closures (see [closure-model.md](closure-model.md)).
- **依赖**：S1.5（移动语义/所有权）
  EN: **Dependency**: S1.5 (move semantics/ownership).
- **验收**：闭包示例 + 递归闭包 + 与协程咬合（spawn 闭包）
  EN: **Acceptance**: closure examples + recursive closures + interlocking with coroutines (spawning closures).

### S2.3 错误处理
*EN: S2.3 Error Handling*

- **内容**：Result/Option（E2）+ ? 传播（P1）+ 可配置 panic（F3）
  + 内外分明（R2）（见 [error-model.md](error-model.md)）
  EN: **Content**: Result/Option (E2) + ? propagation (P1) + configurable panic (F3) + clear internal/external division (R2) (see [error-model.md](error-model.md)).
- **依赖**：S1.5 + S2.2（闭包）
  EN: **Dependency**: S1.5 + S2.2 (closures).
- **验收**：? 链式传播 + panic 三端行为 + Result 跨 channel
  EN: **Acceptance**: ? chained propagation + panic behavior on three backends + Result across channels.

### S2.4 接口 port
*EN: S2.4 Interface port*

- **内容**：显式 impl（P1）+ 双形态分发（D3）+ 隐式 vtable（I1+I2）
  + 借用归 unsafe（见 [port-model.md](port-model.md)）
  EN: **Content**: explicit impl (P1) + dual-form dispatch (D3) + implicit vtable (I1+I2) + borrow-under-unsafe (see [port-model.md](port-model.md)).
- **依赖**：S2.2（函数指针做 vtable）
  EN: **Dependency**: S2.2 (function pointers for the vtable).
- **验收**：静态/动态分发 + 手写 vtable（unsafe）+ 异构容器
  EN: **Acceptance**: static/dynamic dispatch + hand-written vtable (unsafe) + heterogeneous containers.

## 阶段 3：工具链完备
*EN: Stage 3: Complete Toolchain*

> 目标：构建/库包/宏/LSP——开发者体验完整。**并行波 2-3**。
> EN: Goal: build / library-package / macro / LSP — complete developer experience. **Parallel Waves 2-3**.

### S3.1 构建配置
*EN: S3.1 Build Configuration*

- **内容**：config.data.tie（L2 分层）+ 分节（tiec/prep/pkg）+ profile（P3）
  （见 [build-config.md](build-config.md)）
  EN: **Content**: config.data.tie (L2 layering) + sections (tiec/prep/pkg) + profile (P3) (see [build-config.md](build-config.md)).
- **依赖**：阶段 1（角色系统）
  EN: **Dependency**: Stage 1 (role system).
- **验收**：`--backend=wasm` 实现选择 + profile dev/release
  EN: **Acceptance**: `--backend=wasm` implementation selection + dev/release profiles.

### S3.2 库/包模型
*EN: S3.2 Library/Package Model*

- **内容**：多文件包（L1c）+ tieir 序列化（S3）+ MVS（P2c）+ 签名（P5c）
  + 接口依赖（P4b）（见 [package-model.md](package-model.md) + [tieir-format.md](tieir-format.md)）
  EN: **Content**: multi-file packages (L1c) + tieir serialization (S3) + MVS (P2c) + signing (P5c) + interface dependencies (P4b) (see [package-model.md](package-model.md) + [tieir-format.md](tieir-format.md)).
- **依赖**：S2.4（port）+ S3.1（构建配置）
  EN: **Dependency**: S2.4 (port) + S3.1 (build configuration).
- **验收**：发布 tieir 包 + 消费方链接 + 签名校验
  EN: **Acceptance**: publish a tieir package + consumer linking + signature verification.

### S3.3 宏/元编程
*EN: S3.3 Macros / Metaprogramming*

- **内容**：code 三形态（C1+C2+C3）+ 函数式宏（M3）+ 过程宏（M4 后置）
  + 卫生（H2+H3）（见 [macro-model.md](macro-model.md)）
  EN: **Content**: three forms of code (C1+C2+C3) + functional macros (M3) + procedural macros (M4 deferred) + hygiene (H2+H3) (see [macro-model.md](macro-model.md)).
- **依赖**：S2.2（闭包）
  EN: **Dependency**: S2.2 (closures).
- **验收**：宏展开 + gensym 隔离 + code 类型三形态
  EN: **Acceptance**: macro expansion + gensym isolation + the three code-type forms.

### S3.4 LSP 重写（tsp）
*EN: S3.4 LSP Rewrite (tsp)*

- **内容**：tsp 全量 16 项能力 + 增量分析 + 语义高亮 + tieconsole 复用
  （见 [tsp-lsp.md](tsp-lsp.md)）
  EN: **Content**: tsp's full 16 capabilities + incremental analysis + semantic highlighting + reuse by tieconsole (see [tsp-lsp.md](tsp-lsp.md)).
- **依赖**：S2.1（符号表稳定）
  EN: **Dependency**: S2.1 (stable symbol table).
- **验收**：VSCode 补全/引用/重命名 + 增量编辑流畅
  EN: **Acceptance**: VSCode completion/references/rename + smooth incremental editing.

## 阶段 4：运行时与 UI + Web（1 周冲刺目标）
*EN: Stage 4: Runtime & UI + Web (1-Week Sprint Goal)*

> 目标：trm/tieui/tieconsole/嵌入式/webui/硬件加速——产品形态落地。
> **并行波 3-4**。webui 提前 + 定义更新（网页 + tie 索引）；
> 硬件加速提前（2026-08-15 决策）。
> EN: Goal: trm/tieui/tieconsole/embedded/webui/hardware acceleration — the product form lands.
> **Parallel Waves 3-4**. webui moved up + definition updated (web pages + tie index);
> hardware acceleration moved up (2026-08-15 decision).

### S4.1 trm
*EN: S4.1 trm*

- **内容**：动态库（延迟绑定）+ system 域（terminal/process/fs/env/
  session/clock/net/data）+ 直接编译保留（opt-in）（见 [trm-arch.md](trm-arch.md)）
  EN: **Content**: dynamic library (lazy binding) + the system domain (terminal/process/fs/env/session/clock/net/data) + direct compilation retained (opt-in) (see [trm-arch.md](trm-arch.md)).
- **依赖**：S1.2（unsafe）+ S3.2（动态库/包）
  EN: **Dependency**: S1.2 (unsafe) + S3.2 (dynamic library/packages).
- **验收**：动态加载 + 域粒度裁剪 + 直接编译零依赖保持
  EN: **Acceptance**: dynamic loading + domain-granularity trimming + keeping direct-compilation zero dependencies.

### S4.2 trm.ui（原 tucore）
*EN: S4.2 trm.ui (formerly tucore)*

- **内容**：窗口/绘制/事件信号/字体（A4/H2/E3/D2/F3）+ 组合式开发
  （见 [tucore-arch.md](tucore-arch.md)）
  EN: **Content**: window/drawing/event-signal/fonts (A4/H2/E3/D2/F3) + composable development (see [tucore-arch.md](tucore-arch.md)).
- **依赖**：S4.1
  EN: **Dependency**: S4.1.
- **验收**：Win32 窗口显示 + 命令列表绘制 + 事件/信号混合
  EN: **Acceptance**: Win32 window display + command-list drawing + event/signal mixing.

### S4.3 tieui 框架
*EN: S4.3 tieui Framework*

- **内容**：组件树/布局/事件分发 + 组合式开发（children 插槽/行为装饰）
  （见 [ui-framework.md](ui-framework.md) + tucore-arch §9）
  EN: **Content**: component tree / layout / event dispatch + composable development (children slots / behavior decoration) (see [ui-framework.md](ui-framework.md) + tucore-arch §9).
- **依赖**：S4.2
  EN: **Dependency**: S4.2.
- **验收**：组合组件示例 + 三端复用抽象面
  EN: **Acceptance**: composite-component example + a three-backend reusable abstraction surface.

### S4.4 tieconsole（本年度目标）
*EN: S4.4 tieconsole (This Year's Goal)*

- **内容**：对象化 shell：`->` 管道 + cmdlet 预定义 + 格式系统（F1+F2+F3）
  + 交互（I1+I2+I3）+ 会话（A1+A2）（见 [tieconsole.md](tieconsole.md)）
  EN: **Content**: an object-oriented shell: `->` pipeline + cmdlet predefined + format system (F1+F2+F3) + interaction (I1+I2+I3) + session (A1+A2) (see [tieconsole.md](tieconsole.md)).
- **依赖**：S4.1（terminal/process 域）+ S3.4（LSP 补全复用）
  EN: **Dependency**: S4.1 (terminal/process domain) + S3.4 (reuse of LSP completion).
- **验收**：PowerShell 对标交互 + 对象管道 + 跨平台一致
  EN: **Acceptance**: PowerShell-parity interaction + object pipeline + cross-platform consistency.

### S4.5 嵌入式（本年度目标）
*EN: S4.5 Embedded (This Year's Goal)*

- **内容**：tie:embedded 子集 + trm-embedded + 协作式协程 + 静态池
  （见 [ui-framework.md](ui-framework.md) §6 + [embedded-rdu.md](embedded-rdu.md)）
  EN: **Content**: the tie:embedded subset + trm-embedded + cooperative coroutines + static pools (see [ui-framework.md](ui-framework.md) §6 + [embedded-rdu.md](embedded-rdu.md)).
- **依赖**：阶段 2（移动语义/闭包）+ S4.2（帧缓冲）
  EN: **Dependency**: Stage 2 (move semantics/closures) + S4.2 (frame buffer).
- **验收**：MCU 帧缓冲输出 + 编译期裁剪（禁用 spawn = 编译错误）
  EN: **Acceptance**: MCU frame-buffer output + compile-time trimming (disabling spawn = a compile error).

### S4.6 webui（提前，定义更新：网页 + tie 索引）
*EN: S4.6 webui (Moved Up; Definition Updated: Web Pages + tie Index)*

- **内容**：**webui = 网页 + tie 索引**——tie 程序编译 wasm 跑浏览器 +
  tieDB/vecsearch 检索能力作为 Web 服务（索引在服务端，网页端查询）
  （见 [ui-framework.md](ui-framework.md) §2 + [tiedb 规划](tiedb.md)）
  EN: **Content**: **webui = web pages + tie index** — tie programs compile to wasm to run in the browser + tieDB/vecsearch retrieval as a web service (index server-side, query web-side) (see [ui-framework.md](ui-framework.md) §2 + [tiedb plan](tiedb.md)).
- **依赖**：阶段 2 + LLVM 22（wasm 支持成熟）+ tieDB（索引基础）
  EN: **Dependency**: Stage 2 + LLVM 22 (mature wasm support) + tieDB (index foundation).
- **验收**：tie 程序浏览器运行 + 网页端检索 tie 索引（向量/文本搜索）
  EN: **Acceptance**: tie programs run in the browser + web-side retrieval of the tie index (vector/text search).

### S4.7 硬件加速（提前）
*EN: S4.7 Hardware Acceleration (Moved Up)*

- **内容**：SIMD（P1 立即）→ GPU 检索（P2）→ Intel NPU（P3）
  ——**GPU/NPU 直接服务 webui 的 tie 索引检索**（embedding + 检索全链路）
  （见 [hw-accel.md](hw-accel.md)）
  EN: **Content**: SIMD (P1 immediate) → GPU retrieval (P2) → Intel NPU (P3) — **GPU/NPU directly serve webui's tie-index retrieval** (embedding + retrieval, the full chain) (see [hw-accel.md](hw-accel.md)).
- **依赖**：S4.6（webui 索引场景）+ tieDB（vecsearch）
  EN: **Dependency**: S4.6 (webui index scenario) + tieDB (vecsearch).
- **验收**：vecsearch GPU 10-50x + OpenVINO embedding + 网页端低延迟检索
  EN: **Acceptance**: vecsearch GPU 10-50x + OpenVINO embedding + low-latency web-side retrieval.

## 阶段 5：远景（明年）
*EN: Stage 5: Far Vision (Next Year)*

> 目标：更广泛平台与生态。**原 webui/硬件加速已提前至阶段 4**。
> EN: Goal: a broader platform and ecosystem. **The original webui/hardware-acceleration work has been moved to Stage 4**.

### S5.1 生态扩展
*EN: S5.1 Ecosystem Expansion*

- **内容**：更多平台（macOS/Wayland 后端完善）、tieir 生态、更多组件库
  EN: **Content**: more platforms (macOS/Wayland backend refinement), the tieir ecosystem, more component libraries.
- **依赖**：阶段 4 完成
  EN: **Dependency**: Stage 4 complete.
- **验收**：三端全平台 + 生态包增长
  EN: **Acceptance**: three-backend full platform + ecosystem-package growth.

## 依赖图总览
*EN: Dependency-Graph Overview*

```
S1.1 LLVM升级（独立）──────────────┐
                                   ├─→ 阶段2（S2.1→S2.2→S2.3→S2.4）
S1.2-S1.4 语言地基 ────────────────┤         │
                                   │         ├─→ 阶段3（S3.1→S3.2 / S3.3→S3.4）
S1.5 移动语义（提前）──────────────┘         │
                                             ├─→ 阶段4（S4.1→S4.2→S4.3→S4.4→S4.5）
                                             │      └─→ S4.6 webui → S4.7 硬件加速
                                             │
                                             └─→ 阶段5（S5.1 生态扩展，明年）
```

> 说明：S4.6 webui 依赖 tieDB（索引基础）与阶段 2；S4.7 硬件加速直接服务
> S4.6 的索引检索——三者联动，webui 落地后硬件加速立即跟进（GPU/NPU 加速
> tie 索引检索）。
> EN: Note: S4.6 webui depends on tieDB (index foundation) and Stage 2; S4.7 hardware acceleration directly serves S4.6's index retrieval — the three move in tandem, so once webui lands, hardware acceleration follows immediately (GPU/NPU accelerating tie index retrieval).

## 会话分配建议（1 周冲刺）
*EN: Recommended Session Assignment (1-Week Sprint)*

| 会话 | 工作单元 | 波次 |
| --- | --- | --- |
| 会话 A | S1.1 LLVM 升级 | 波 1 |
| 会话 B | S1.2-S1.4 语言地基 | 波 1 |
| 会话 C | S1.5 移动语义 | 波 1 |
| 会话 F | S4.6 webui 前置调研（wasm 可行性） | 波 1（提前） |
| 会话 D | S2.1 字符串 | 波 2 |
| 会话 E | S2.2 闭包 | 波 2 |
| 会话 G | S2.3 错误处理 + S2.4 接口 | 波 2 |
| 会话 H | S3.1 构建配置 + S3.2 库包 | 波 2-3 |
| 会话 I | S3.3 宏 + S3.4 tsp | 波 3 |
| 会话 J | S4.1 trm + S4.2 trm.ui | 波 3 |
| 会话 K | S4.3 tieui + S4.4 tieconsole | 波 4 |
| 会话 L | S4.5 嵌入式 + S4.7 硬件加速 | 波 4 |
| 主控 | 全程：验收 + 依赖协调 + 双远端提交 | 全程 |

EN: The session table maps each session (A–L plus controller) to its work units and wave, with the controller doing acceptance, dependency coordination, and dual-remote commits throughout.

> 备注：波次为建议调度，实际以依赖验收为准（前一单元验收通过才启动
> 依赖它的单元）；无依赖的单元可随时提前。
> EN: Note: waves are a suggested schedule; the actual scheduling is governed by dependency acceptance (a dependent unit starts only after its prerequisite unit passes acceptance); units with no dependencies can be moved up anytime.

# P1 数据流箭头 -> / <-（2026-08-30，提交 02b181b）——已实现
*EN: P1 Dataflow Arrows -> / <- (2026-08-30, commit 02b181b) — Implemented*

用户定义的 P1（在 P2 表增强之后接续）：`->` / `<-` 表示数据流向，用于传参与赋值。
EN: User-defined P1 (continuing after the P2 table enhancement): `->` / `<-` express dataflow direction, used for argument passing and assignment.

- **传参**（数据作末参）：`a -> f(x)` = `f(x, a)`；`a -> f()` = `f(a)`；
  链式 `a -> f() -> g()` = `g(f(a))`；方法调用 `a -> obj.m(x)` = `obj.m(x, a)`；
  函数值 `a -> f` = `f(a)`
  EN: **Argument passing** (data as the trailing argument): `a -> f(x)` = `f(x, a)`; `a -> f()` = `f(a)`; chained `a -> f() -> g()` = `g(f(a))`; method call `a -> obj.m(x)` = `obj.m(x, a)`; function value `a -> f` = `f(a)`.
- **赋值**（双向）：`x <- a` 与 `a -> x` 均为 `x = a`；下标 `arr[i] <- a`、
  字段 `obj.f <- a`
  EN: **Assignment** (bidirectional): both `x <- a` and `a -> x` equal `x = a`; subscript `arr[i] <- a`, field `obj.f <- a`.
- **实现**：lex_larrow=95 + 符号表 `<-`；parse_arrow 层（低于三目，左结合）——
  目标=调用 → 附加末参脱糖；= 下标/字段 → N_INDEX_ASSIGN/N_FIELD_ASSIGN；
  = 裸 Var → 箭头节点（语义按 fn/变量分派：传参走 tig_call_fn_value，
  赋值走 N_ASSIGN 同款 store）
  EN: **Implementation**: lex_larrow=95 + `<-` in the symbol table; the parse_arrow layer (below the ternary, left-associative) — target = call → desugar an appended trailing argument; = subscript/field → N_INDEX_ASSIGN/N_FIELD_ASSIGN; = bare Var → an arrow node (semantics dispatch by fn vs variable: passing goes through tig_call_fn_value, assignment uses the same store as N_ASSIGN).
- **验收**：tests/language/dataflow_arrow.tie（7 项 PASS）+ 探针 p1_arrow.tie；
  tests/language 全量正例 70/70 无回归
  EN: **Acceptance**: tests/language/dataflow_arrow.tie (7 PASS) + probe p1_arrow.tie; tests/language full positive cases 70/70 with no regression.

# P2d 表/集合标准库（2026-08-30，提交 8f32a05..20e0235）——已实现
*EN: P2d Table/Coll Standard Library (2026-08-30, commits 8f32a05..20e0235) — Implemented*

在 P1 数据流箭头 + P2b/P2c any 异构表基础上，为表（table）补充集合标准库与嵌套能力：
EN: On top of the P1 dataflow arrow + P2b/P2c any heterogeneous tables, add collection standard-library and nesting capabilities for tables:

- **coll 高阶函数**（std/collection.tie，表作末参配合 P1 管道）：
  map_i64/map_string、filter_i64/filter_string、reduce_i64/reduce_string、
  foreach_i64（fn 值参数，S2.2 命名函数/闭包均可传）
  EN: **coll higher-order functions** (std/collection.tie; the table is the trailing argument, working with the P1 pipeline): map_i64/map_string, filter_i64/filter_string, reduce_i64/reduce_string, foreach_i64 (fn-valued parameters; both S2.2 named functions and closures can be passed).
- **coll 表操作**：reverse_i64/reverse_string、to_string_i64/to_string_string（`[1, 2, 3]`）、
  join（分隔符连接）、sum_i64/product_i64/max_i64/min_i64（空表约定）
  EN: **coll table operations**: reverse_i64/reverse_string, to_string_i64/to_string_string (`[1, 2, 3]`), join (delimiter-joined), sum_i64/product_i64/max_i64/min_i64 (empty-table convention).
- **嵌套 table\<any\>**（编译器）：tig_box_any 表/映射分支——tag=精确表/映射类型 id，
  payload=ptrtoint(表 ptr)（引用类型 8 字节直接容纳，无堆拷贝）；
  tig_unbox_any inttoptr 还原表值 + 运行时 tag 检查（不匹配 → 运行时错误退出）；
  新增 as_table_i64/string/bool/f64/char/any 六个拆箱内置（sbuiltin/sinfer_ret/irgen 三处登记）
  EN: **Nested table\<any\>** (compiler): the tig_box_any table/map branch — tag = exact table/map type id, payload = ptrtoint(table ptr) (a reference type is held directly in 8 bytes, no heap copy); tig_unbox_any inttoptr restores the table value + a runtime tag check (mismatch → runtime error exit); add six unboxing builtins as_table_i64/string/bool/f64/char/any (registered in sbuiltin/sinfer_ret/irgen).
- **验收**：tests/language/table_coll_p2d.tie（7 项 PASS）+ 探针 p2d_hof/p2d_ops/
  p2d_nested/p2d_nested_mismatch；tests/language 全量正例编译+运行 52/52 无回归；
  自举（tiec 编译自身 driver.tie）零错误
  EN: **Acceptance**: tests/language/table_coll_p2d.tie (7 PASS) + probes p2d_hof/p2d_ops/p2d_nested/p2d_nested_mismatch; tests/language full positive compile+run 52/52 with no regression; bootstrap (tiec compiling its own driver.tie) zero errors.

# P2d 深化：集合库（2026-08-31，提交 de2364d..5740a53）——已实现
*EN: P2d Deepening: Collection Library (2026-08-31, commits de2364d..5740a53) — Implemented*

在 P2d 基础集合库之上深化：统计 + 谓词查找 + map 高阶（编译器内置）：
EN: Deepen the P2d base collection library: statistics + predicate search + map higher-order functions (compiler built-in):

- **统计**（coll，std/collection.tie）：mean/median/variance/stddev（i64 与 f64 变体）；
  中位数复用 sort 冒泡（新增 sort.sort_f64）；总体方差 1/n；空表 → 0.0
  EN: **Statistics** (coll, std/collection.tie): mean/median/variance/stddev (i64 and f64 variants); the median reuses the sort bubble (adding sort.sort_f64); population variance 1/n; empty table → 0.0.
- **谓词/查找**（coll）：count_if/any/all（fn 谓词 HOF，表作末参配合 P1 管道，any 短路、
  all 空表 true）+ find_index/contains（线性扫描，无序可用；find_index 未找到 -1）
  EN: **Predicate/search** (coll): count_if/any/all (fn-predicate HOFs, table as trailing argument working with the P1 pipeline; any short-circuits, all on an empty table is true) + find_index/contains (linear scan, usable unordered; find_index returns -1 when not found).
- **map 高阶**（编译器内置）：map_keys(m)→table<string>；map_values(m)→table<V>
  （V 从 map<string,V> 解码，map<any> 值槽堆指针解引用还原）；map_contains(m, key)→bool
  （不 raise；数组二分 / 哈希线性扫描）。三处登记：sbuiltin 返回类型 + sinfer_ret 实参
  校验 + irgen 分发
  EN: **map higher-order** (compiler built-in): map_keys(m)→table<string>; map_values(m)→table<V> (V decoded from map<string,V>; the map<any> value slot is restored by dereferencing the heap pointer); map_contains(m, key)→bool (does not raise; array binary search / hash linear scan). Registered in three places: sbuiltin return types + sinfer_ret argument validation + irgen dispatch.
- **验收**：tests/language/table_coll_deep.tie（7 项 PASS：stats/stats_empty/pred/pred_pipe/
  map_hof/map_str/map_any）+ 探针 p2d_stats/p2d_pred/p2d_map/p2d_map_any；
  tests/language 全量正例 50/50 无回归；自举零错误
  EN: **Acceptance**: tests/language/table_coll_deep.tie (7 PASS: stats/stats_empty/pred/pred_pipe/map_hof/map_str/map_any) + probes p2d_stats/p2d_pred/p2d_map/p2d_map_any; tests/language full positive cases 50/50 with no regression; bootstrap zero errors.

# P2e：集合库补全（2026-08-31，提交 74a4da0/80a1b96）——已实现
*EN: P2e: Collection-Library Completion (2026-08-31, commits 74a4da0/80a1b96) — Implemented*

P2d 规划中的 table/set 标准库补全 set 部分，并深化表运算：
EN: Complete the set part of the table/set standard library in the P2d plan, and deepen table operations:

- **set 集合**（coll，纯 std）：载体 = 有序唯一 table（复用 std/sort 二分 contains/index_of
  与有序插入 insert_sorted_*）；set_new/add（去重）/contains（二分）/remove/size/to_table +
  set_union/intersect/diff（双指针归并 O(n+m)）；i64 与 string 变体；修改类用 ref 表参数 +
  局部表重绑定（T0.3）
  EN: **set collection** (coll, pure std): carrier = an ordered, unique table (reusing std/sort binary contains/index_of and the ordered-insert insert_sorted_*); set_new/add (dedup)/contains (binary)/remove/size/to_table + set_union/intersect/diff (two-pointer merge O(n+m)); i64 and string variants; mutating kinds use ref table params + local-table rebinding (T0.3).
- **表运算**（coll）：concat 拼接、slice 半开区间切片（越界截断/空表防护）、copy 深拷贝、
  dedup 去重（保持首次出现顺序）；i64 与 string 变体
  EN: **table operations** (coll): concat concatenation, slice half-open interval slicing (out-of-range truncation / empty-table guard), copy deep copy, dedup deduplication (preserving first-occurrence order); i64 and string variants.
- **验收**：tests/language/table_coll_set_p2e.tie（3 项 PASS：set_i64/set_ops/table_ops）+
  探针 p2e_set/p2e_ops；tests/language 全量正例 52/52 无回归；自举零错误
  EN: **Acceptance**: tests/language/table_coll_set_p2e.tie (3 PASS: set_i64/set_ops/table_ops) + probes p2e_set/p2e_ops; tests/language full positive cases 52/52 with no regression; bootstrap zero errors.

## 验收总则（每单元）
*EN: General Acceptance Rules (per Unit)*

1. 编译零错误（用户核心关注）
   EN: Zero compile errors (the user's core concern).
2. 单元回归测试通过（tests/ + _driver_test 行为等价）
   EN: Unit regression tests pass (tests/ + _driver_test behavioral equivalence).
3. 遵循设计文档决策（无偏离）
   EN: Follow the design-document decisions (no deviation).
4. 提交推送双远端（franj2 + GitHub）
   EN: Commit and push to both remotes (franj2 + GitHub).
5. 更新 README/CHANGELOG（用户文档维护要求）
   EN: Update README/CHANGELOG (the user's documentation-maintenance requirement).