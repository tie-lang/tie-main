# trm-lite p.6.7 并行开发（双形态真并行 + 运行时全量并发安全）

* 日期 / Date：2026-09-03

* 状态 / Status：规划已对齐，待执行（Aligned with user, pending execution）

* 基线 / Baseline：trm-lite preview.2（2026-09-02，p.6.5 收尾）

* 依据 / Basis：`2026-09-01-trm-lite-completion-design.md`（p.6.5 收官）、`2026-08-26-trm-lite-design.md`（设计定稿）

* 实现约束 / Implementation constraint：本模块全部工作**用 tie 语言完成**（tiec 及运行时改造、探针、验收），不引入其他实现语言。
  EN: All work in this module is done **in tie** (tiec/runtime changes, probes, acceptance); no other implementation language.

***

## 1. 定位 / Positioning

p.6.6 完成库补全后，p.6.7 回到 trm-lite 本体：对齐 Go runtime 的并发模型，
让**简单形态变成真并行**（去掉「yield 手动驱动单线程排空」的伪并行），并**强化
复杂形态**（常驻线程池、per-P 细锁、协作抢占、channel/select、结构化并发）。
核心前置是 **tie 运行时全量并发安全**——任务体一旦触碰表/字符串/全局即竞态，
不解决它，任何「并行」都是玩具。

EN: After the p.6.6 library completion, p.6.7 returns to trm-lite itself: aligning with
the Go runtime concurrency model, making the **simple form truly parallel** (removing the
pseudo-parallelism of "yield manually drains a single-threaded FIFO"), and **strengthening
the complex form** (resident thread pool, per-P fine-grained locks, cooperative
preemption, channel/select, structured concurrency). The core prerequisite is **full
concurrency safety of the tie runtime** — task bodies racing on tables/strings/globals
make any "parallelism" a toy until this is solved.

***

## 2. 策略校准 / Strategy Calibration

对 tie 运行时深挖（compiler/backend/llvmgen_inst.tie str_cat 序列、
llvmgen_str.tie 运行时桥符号、llvmgen.tie SSO 池说明）得到三个事实，修正了原「对标
Go 并发 GC」的设想：

EN: Deep-dive into the tie runtime (str_cat lowering in
compiler/backend/llvmgen_inst.tie, runtime bridge symbols in llvmgen_str.tie, SSO pool
notes in llvmgen.tie) yields three facts that correct the original "align with Go's
concurrent GC" assumption:

* **tie 无追踪式 GC / tie has no tracing GC**：`str_cat` 每次 malloc 新串、旧串无回收
  （既有泄漏隐患）。因此「全量并发安全」的形态 = 分配器/SSO 池/表操作加锁 + 全局读写
  原子化 + 字符串与表生命周期确定性，而非 Go 式并发 GC 根扫描 + safe point。
  EN: str_cat mallocs a new string each time and old strings are never reclaimed (a
  pre-existing leak). "Full concurrency safety" thus means: locking the allocator/SSO
  pool/table operations, atomizing global reads/writes, and making string/table
  lifetimes deterministic — not Go-style concurrent GC root scanning + safe points.

* **CRT malloc 本身线程安全 / CRT malloc is thread-safe per se**：长串分配无需自建锁；
  竞争点集中在进程级 SSO 短串池、共享 table 的 push/写、全局变量读改写、println/输出。
  EN: No custom lock is needed for long-string allocation; contention concentrates on
  the process-level SSO short-string pool, shared-table push/writes, global read-modify-
  write, and println/output.

* **语言已有 `atomic<i64>` / the language already has `atomic<i64>`**
  （store/fetch_add/load/compare_exchange，tests/language/atomic_asm.tie）：
  原子基座现成，无需自造。
  EN: the atomic basis is ready-made (store/fetch_add/load/compare_exchange), no need to
  build from scratch.

用户决策 / User decisions：

* 执行层路线 / Execution-layer route：**双 runtime 并行开发**——简单形态自建独立
  常驻池，与复杂形态物理隔离；两者各带窃取与抢占。
  EN: **dual-runtime development in parallel** — the simple form builds its own resident
  pool, physically isolated from the complex form; both have their own stealing and
  preemption.

* 运行时安全 / Runtime safety：**全量并发安全**（按上述校准形态执行）。
  EN: **full concurrency safety** (pursuant to the calibrated shape above).

* 强化范围 / Enhancement scope：调度层强化、channel/select 增强、生命周期确定性
  （替代「GC 与 tie 运行时整合」）、结构化并发，全选。
  EN: scheduler hardening, channel/select enhancement, deterministic lifetime (replacing
  "GC-tie-runtime integration"), and structured concurrency — all selected.

***

## 3. 目标与范围 / Goals and Scope

1. 简单形态真并行：内置 `spawn` 投递即由常驻线程池并行执行；`yield` 重定义为
   同步点/协作让出（Go 无手动驱动概念）。
   EN: Simple form becomes truly parallel: builtin `spawn` dispatches to a resident
   thread pool; `yield` is redefined as a sync point/cooperative yield.

2. 复杂形态强化：常驻池（去每轮 drain 重建）、per-P 细锁（去全局单 CS）、协作抢占、
   WaitGroup 结构化并发、channel Go 语义（select/close 广播）。
   EN: Complex form hardened: resident pool, per-P fine-grained locks, cooperative
   preemption, WaitGroup structured concurrency, Go-style channel semantics.

3. 运行时全量并发安全：SSO 池/共享表/全局/输出加锁或原子化；字符串与表生命周期
   确定性（消泄漏）；多线程探针全 PASS。
   EN: Full runtime concurrency safety: lock or atomize SSO pool / shared tables /
   globals / output; deterministic string-table lifetimes (leak removed); all
   multi-threaded probes PASS.

**非目标 / Non-goals**：syscall 出借与 netpoller（M 解耦）、可增长栈/分段栈
（任务仍为 fn() 原子体，p.6.5.5「可迁移」语义不变）、跨平台完整矩阵、与 trm 引擎
（字节码 VM）功能合并。

***

## 4. p.6.7 子项盘子 / Sub-item Plan

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.1 | 分配器与 SSO 池并发安全：`tie_sso_alloc` 进程级短串池加锁或 per-thread 池；长串走线程安全 CRT malloc；str_cat 并发正确 / Allocator and SSO pool safety: lock the process-level short-string pool or switch to per-thread pools; long strings use thread-safe CRT malloc; concurrent str_cat correct | N 线程并发 str_cat/字符串构建：逐字节正确、无越界 / N threads building strings concurrently: byte-exact, no overrun |
| p.6.7.2 | 共享表并发安全：tie_table_new/push/len 桥符号并发保护；realloc 扩表与并发写一致性 / Shared-table safety: protect tie_table_new/push/len bridges; realloc growth consistent with concurrent writes | 并发 push 计数精确、无老数据覆盖 / Concurrent push counts exact, no stale overwrite |
| p.6.7.3 | 全局读写原子化：跨线程共享计数用 atomic/独立槽位；Go 风格 race 指南（安全/不安全模式文档化）/ Atomize global RMW: atomic or per-slot for cross-thread counters; Go-style race guidance documented | fetch_add 并发求和探针 = N×M / fetch_add concurrent sum probe = N×M |
| p.6.7.4 | 输出与运行时余项：println/to_string 加锁；intern/静态池等余项审查并锁 / Output & remaining runtime bits: lock println/to_string; audit and lock intern/static pools | 并发 println 行不撕裂 / Concurrent println lines not torn |
| p.6.7.5 | 生命周期确定性：字符串/表分配改引用计数或 arena 回收（消除 str_cat 泄漏），多线程下确定性释放 / Deterministic lifetime: refcount or arena reclamation for strings/tables (removes str_cat leak), deterministic free across threads | 长跑并发探针内存有界 / Long-running concurrent probe memory bounded |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.6 | 简单形态常驻池（S-pool）：内置 spawn 投递到简单 runtime 自己的常驻线程池（与复杂形态物理隔离）；yield 重定义 = 同步点并兼容旧程序 / Simple-form resident pool: builtin spawn dispatches to its own resident pool (isolated from complex form); yield becomes a sync point, backward compatible | spawn_demo 类程序真实多线程，tid 去重 ≥ 2 / spawn_demo-style programs truly multithreaded, distinct tids ≥ 2 |
| p.6.7.7 | 简单形态窃取队列（S-deque）：per-worker 双端队列 + 窃取 + 溢出（复刻 sched_ws 算法、独立实现）；协作让出点 / Simple-form deque: per-worker deque + steal + overflow (reimplemented, isolated); cooperative yield points | 不平衡负载 stolen>0、结果全对 / Unbalanced load stolen>0, results exact |
| p.6.7.8 | 复杂形态常驻池（C-pool）：sched_ws 去每轮 drain 重建；池起于首次 drain、止于 shutdown；drain = 等本轮排空不回收池 / Complex-form resident pool: no per-drain rebuild; pool starts at first drain, ends at shutdown | 多轮 drain 复用同一组线程句柄 / Multiple drains reuse the same thread handles |
| p.6.7.9 | 复杂形态 per-P 细锁（C-deque）：每 worker 段独立锁 + 全局溢出队列细锁，去全局单 CS；窃取窗口缩小 / Complex-form per-P locks: per-worker segment locks + fine-grained overflow lock, remove the single global CS | ms4 < ms1 可复现（修复 78>47）/ ms4 < ms1 reproducible (fixing 78>47) |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.10 | 协作抢占统一：yield/gosched 显式点 + 时间片计数器检查插桩；两形态统一抢占机制 / Unified cooperative preemption: explicit yield/gosched points + timeslice counter checks | 长任务可让出，调度公平性探针 / Long tasks yield; fairness probe |
| p.6.7.11 | 结构化并发 WaitGroup：spawn 分组句柄 + 等全部完成（Go sync.WaitGroup）；内置与 ctx 双入口 / WaitGroup structured concurrency: grouped spawn + wait-all (Go sync.WaitGroup); both builtin and ctx entries | wg 并发求和多组精确 / Multi-group wg sums exact |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.12 | channel Go 语义：tl_chan 增加 close 广播唤醒、双向、select 多路收发 / Go-style channel: close broadcast wakeup, bidirectional, select multi-way | select/close 广播探针 PASS；parity_chan 对比仍逐字节一致 / select/close probes PASS; parity_chan still byte-identical |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.13 | 双形态并行验收矩阵：两形态各自真并行探针 + 行为一致对比 + m6_actor 零回归 / Dual-form parallel acceptance matrix: per-form truely-parallel probes + behavior parity + m6_actor zero regression | 全 PASS、exit 0 / All PASS, exit 0 |
| p.6.7.14 | 收尾：preview.3、README/CHANGELOG、已知限制清单、双语文档 / Wrap-up: preview.3, README/CHANGELOG, known-limits list, bilingual docs | 自举核验 + 零回归 / Bootstrap verify + zero regression |

***

## 5. 依赖主线 / Dependency Line

p.6.7.1-6.7.5（并发安全）→ p.6.7.6-6.7.9（真并行）→ p.6.7.10-6.7.11（抢占/WaitGroup）→
p.6.7.12（channel）→ p.6.7.13-6.7.14（验收发布）。p.6.7.6-6.7.9 内部 S-pool 与 C-pool 可并行
推进；C-deque（p.6.7.9）依赖 C-pool（p.6.7.8）。

EN: p.6.7.1-6.7.5 (safety) → p.6.7.6-6.7.9 (true parallelism) → p.6.7.10-6.7.11
(preemption/WaitGroup) → p.6.7.12 (channel) → p.6.7.13-6.7.14 (acceptance/release). Within
p.6.7.6-6.7.9, S-pool and C-pool can proceed in parallel; C-deque (p.6.7.9) depends on
C-pool (p.6.7.8).

***

## 6. 风险与对策 / Risks & Mitigations

* p.6.7.5 生命周期确定性波及 tiec 字符串/表 codegen，面大 → 放 p.6.7.1-6.7.5 组最后，先正确后性能。
  EN: p.6.7.5 touches tiec string/table codegen broadly → place last in the p.6.7.1-6.7.5 group, correctness first.

* 双 runtime 双份维护 → 借 tl_sync 单一声明源，队列/窃取算法在两处独立实现但同注释纪律。
  EN: Dual-runtime maintenance → reuse the tl_sync single declaration source; deque/steal
  reimplemented separately with the same commenting discipline.

* SSO 池加锁与性能冲突 → 优先 per-thread 池（零争用），加锁为后备。
  EN: SSO pool lock vs performance → prefer per-thread pools (zero contention), locking as fallback.

* 时序断言受宿主负载噪声 → 沿用 p.6.5.2 宽松门槛 + 多线程 tid 去重为主证，墙钟为辅。
  EN: Timing asserts suffer host noise → keep the p.6.5.2 loose threshold, treat distinct-thread-id counts as the primary evidence, wall-clock as secondary.

***

## 7. 相关文档 / Related Documents

* `tie-main/docs/superpowers/specs/2026-08-26-trm-lite-design.md`（设计定稿 / design final)

* `tie-main/docs/superpowers/specs/2026-09-01-trm-lite-completion-design.md`（p.6.5 收官 / p.6.5 wrap-up)

* `tie-main/docs/designs/trm-final-design.md`（trm 定稿，抢占语义参照 / trm final design, preemption reference)

* 落地仓库 / Landing repo：`trm-lite/`（独立仓库 / standalone repo，preview.2 → preview.3）

***

## 8. p.6.7.3 race 指南 / Race Guidance（安全 / 不安全模式）

> 目标：让多线程任务体写出无竞态代码。按强度从高到低给出**安全模式**，并列出
> **不安全模式**（编译期不拦截，运行时行为未定义——探针验收只保证安全模式正确）。
> EN: Goal — write race-free task bodies. Safe patterns below, strongest first; unsafe
> patterns are NOT rejected at compile time (behavior undefined at runtime) — probe
> acceptance only guarantees the safe patterns.

### 8.1 安全模式 / Safe patterns

| # | 模式 / Pattern | 说明 / Notes | 落地实例 / Instances |
|---|----------------|--------------|----------------------|
| S1 | **原子计数器 `atomic<i64>`**：`fetch_add/fetch_sub/load/store/compare_exchange`（须在 `unsafe` 块内调用）；全局或跨线程共享纯计数首选 | 纯计数无复合态，零锁零等待；内存序：store ∈ {monotonic/release/seq_cst}，load ∈ {monotonic/acquire/seq_cst}（LLVM 约束） | `atomic_sum_probe`：8 任务 × 1000 `fetch_add(1, AcqRel)` = 8000 精确；CAS 换值 |
| S2 | **独立槽位 / per-slot**：每任务只写自己的槽位（`g_slots[idx] = v`），结束时汇总 | 无跨线程写竞争，天然无锁；表下标写经 tl_tbl 每表锁，越界须先 push 播种 | `atomic_sum_probe` slots 分量 = 8000；`tbl_par_probe` g_tid 每任务一行 |
| S3 | **锁保护计数**：复合状态（计数 + 平行数组/游标一并变更）持同一把锁（CRITICAL_SECTION + CONDITION_VARIABLE） | 锁内一次做完全部相关变更，锁外统一读 | sched_ws `g_pending/g_active/g_done/g_stolen/g_migrated` 全在 `g_cs` 内；gc_tri 计数全在 `g_gc_cs` 内；`ch_open` 句柄序号 + 平行数组在 `g_alloc_cs` 内 |
| S4 | **运行时容器安全**：`table_push` 单步锁内（每表锁）；SSO 短串池原子 bump（编译器侧，程序无感）；长串分配走线程安全 CRT malloc | 容器自身不竞态；`len(t)/t[i]` 并发视图**最终一致**，需要精确值须在锁内读 | tbl_par_probe（共享表 800 元素）；sso_par_probe（8 线程构建字符串） |

### 8.2 不安全模式 / Unsafe patterns

| # | 模式 / Pattern | 后果 / Consequence | 修复 / Fix |
|---|----------------|--------------------|------------|
| U1 | **裸读-改-写**：`g_cnt = g_cnt + 1`（全局共享计数） | 丢失更新（两个线程同时读到旧值） | 改 `atomic<i64>` fetch_add，或持锁后更新 |
| U2 | **复合分配无锁**：句柄序号 `++` 与平行数组追加分开做 | 丢句柄 / 平行数组错位（handle 1 的 cs/cv/head/tail 不在同一行） | 复合临界区一把锁（`g_alloc_cs`） |
| U3 | **无锁遍历共享容器 + 并发写**：一任务读 `g_t[i]` 同时他任务 push 扩容 | 读到旧缓冲/越界（realloc 换址） | `tbl_at/tbl_set` 锁内读写下标；遍历前先取快照 len 或持同一把锁 |
| U4 | **跨线程共享的「已读」游标裸自增**（`head = head + 1`） | 竞争消费丢消息/重复消费 | 游标与数据同锁（chan 的 per-channel CS） |
| U5 | **依赖全局变量初值**：`var g_x: i64 = 4` 跨线程共享 | tie 标量全局初值被静默丢弃（=0）——并发下初始状态错 | `ensure()` 幂等显式初始化（sched_ws `g_workers` 模式） |
| U6 | **relaxed 序用于 store/load** | LLVM 拒绝 `store atomic ... relaxed`（物理不存在该序） | store 用 release/seq_cst，load 用 acquire/seq_cst |

### 8.3 通则 / General rules

* 纯计数 → `atomic<i64>`（S1，唯一正确且无锁）；计数+状态连招 → 一把锁内完成（S3）；
  各写各的 → 独立槽位（S2）；什么都别共享 → 每任务自闭环。
* 锁的粒度决定扩展性：per-表/per-通道锁 >> 全局单锁（p.6.7.9 C-deque 将进一步去全局单 CS）。
* 探针验收纪律：并发断言只依赖 S1~S4 提供的确定性结果，不做墙钟时序断言（主机噪声，
  p.6.7 spec §6 风险对策）；线程级并行性证据 = 多线程 tid 去重 ≥ 2。

EN:
* Pure counter → `atomic<i64>` (S1, the only correct lock-free option); counter plus
  compound state → finish all related mutations inside ONE lock (S3); each task writes
  its own slot → per-slot (S2); share nothing → self-contained tasks.
* Lock granularity = scalability: per-table/per-channel locks ≫ single global lock
  (p.6.7.9 C-deque will further remove the global single CS).
* Probe discipline: concurrent assertions only rely on deterministic S1–S4 results, no
  wall-clock timing assertions (host noise, §6 risk column); thread-parallelism evidence
  = distinct OS thread ids ≥ 2.

### 8.4 输出与静态池审计（p.6.7.4）/ Output & static-pool audit

| 项 / Item | 形态 / Shape | 并发结论 / Concurrency verdict |
|-----------|--------------|-------------------------------|
| `println/print` | 每次 = **单次 vararg printf**（格式化串+参数一次调用） | CRT 每调用内部加锁 → 行级原子不撕裂（探针 400 行逐字节精确） |
| `to_string(i64/u64/i128/u128/f64/窄型)` | 全内联，数字循环/`_gcvt` 写 **每次调用新分配** 的缓冲（SSO 原子 bump / CRT malloc） | 无共享静态缓冲，线程安全 |
| SSO 短串池 / 回退计数 | 进程级池 `@s21_sso_off` + `@s21_sso_malloc_cnt` | atomicrmw（p.6.7.1）零锁零争用 |
| 表 / 通道 / 调度 / GC 内部表 | 全局平行数组 | 各表每表锁；句柄分配全局锁；计数锁内（p.6.7.2/3） |
| 编译器 intern/常量池 | irgen 期（单线程主机） | 非运行时共享，无并发面 |
| `len(t)/t[i]` 无锁读 | final-consistent | 精确值须锁内读（S3）；只读校验可放行（探针 assertEquals 用） |

EN: println/print = one vararg printf per call (CRT locks per call → lines never tear;
400-line probe byte-exact). to_string(i64/u64/i128/u128/f64/narrow) is fully inlined and
writes into a freshly-allocated per-call buffer (SSO atomic bump / CRT malloc) — no
shared static buffer. SSO pool + fallback counter are atomicrmw (p.6.7.1). Table/chan/
sched/GC internal arrays are per-table-locked / alloc-locked / counted under locks
(p.6.7.2/3). Compiler interner/const pools are irgen-time only (single-threaded host).
Unlocked len(t)/t[i] is final-consistent; read exact values under the lock (S3).

### 8.5 p.6.7.5 生命周期确定性（链上临时释放）/ Deterministic lifetime (chain temps)

* 实现 / Implementation：str_cat（op56）在拼接结果就绪后，对**直连链上中间体**（前一
  str_cat 结果值除本次拼接外零引用）调用 `@tie_str_free_if_heap(数据指针, 数据长度)`
  ——数据长 > 31（池外 malloc）→ `free(块基址=数据指针-8)`；短串池内只读不释放。
  判定严格：任何 store 进槽 / 传参 / 返回 / 其它拼接引用 → 不释放（防 UAF）。
  确定性释放无 GC、与线程身份无关。
* 探针 / Prove：`chain_leak_probe`（8 任务 × 2M 轮 6 段长串链）sum 精确 PASS；
  生成 IR 内联释放点分布正确；二阶自举 tiec70→tiec71→tiec72 字节不动点一致；
  全 p.6.7 探针套件回归 PASS。RSS 取证：同一长跑负载峰值工作集下降约 1.5×
  （CRT 复用 freed 块，既释放堆不动点低于基线）。
* 已知限制 / Known limits：仅覆盖**直连链临时**；经临时槽路由的链节、以及被变量/
  函数返回/调用持有的**末值**仍由程序生命周期管理（逐表达式一值留存）——完整
  所有权模型（作用域末引用释放）留待后续，见 §9 待决项。

EN: str_cat (op56) frees directly-nested chain temps (a previous str_cat result whose only
reference is the current concat) via @tie_str_free_if_heap(data-ptr, data-len) — heap
strings > 31 bytes are free()'d (block base = data-ptr - 8); SSO-pooled short strings are
read-only and skipped. The check is strict: any store/argument/return/other-concat
reference means no free (prevents UAF). Deterministic, GC-free, thread-identity
independent. Probe chain_leak_probe (8 tasks × 2M rounds × 6-segment long-string chains)
sum exact PASS; inlined free points placed correctly in generated IR; self-host 2-stage
byte fixpoint tiec70→tiec71→tiec72 identical; full p.6.7 probe suite PASS. RSS evidence:
≈1.5× lower peak working set at identical load (CRT recycles freed blocks above the
freed-heap fixpoint). Known limits: only directly-nested chain temps are reclaimed;
slot-routed chain links and the final value held by a variable/return/call remain
program-lifetime (one value retained per top-level expression) — full ownership model
(scope-end last-use release) deferred, see §9 open items.
