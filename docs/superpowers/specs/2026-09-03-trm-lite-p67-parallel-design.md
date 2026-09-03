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

* 阶段一：运行时并发安全地基 / Stage 1: runtime concurrency-safety foundation

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.1 | 分配器与 SSO 池并发安全：`tie_sso_alloc` 进程级短串池加锁或 per-thread 池；长串走线程安全 CRT malloc；str_cat 并发正确 / Allocator and SSO pool safety: lock the process-level short-string pool or switch to per-thread pools; long strings use thread-safe CRT malloc; concurrent str_cat correct | N 线程并发 str_cat/字符串构建：逐字节正确、无越界 / N threads building strings concurrently: byte-exact, no overrun |
| p.6.7.2 | 共享表并发安全：tie_table_new/push/len 桥符号并发保护；realloc 扩表与并发写一致性 / Shared-table safety: protect tie_table_new/push/len bridges; realloc growth consistent with concurrent writes | 并发 push 计数精确、无老数据覆盖 / Concurrent push counts exact, no stale overwrite |
| p.6.7.3 | 全局读写原子化：跨线程共享计数用 atomic/独立槽位；Go 风格 race 指南（安全/不安全模式文档化）/ Atomize global RMW: atomic or per-slot for cross-thread counters; Go-style race guidance documented | fetch_add 并发求和探针 = N×M / fetch_add concurrent sum probe = N×M |
| p.6.7.4 | 输出与运行时余项：println/to_string 加锁；intern/静态池等余项审查并锁 / Output & remaining runtime bits: lock println/to_string; audit and lock intern/static pools | 并发 println 行不撕裂 / Concurrent println lines not torn |
| p.6.7.5 | 生命周期确定性：字符串/表分配改引用计数或 arena 回收（消除 str_cat 泄漏），多线程下确定性释放 / Deterministic lifetime: refcount or arena reclamation for strings/tables (removes str_cat leak), deterministic free across threads | 长跑并发探针内存有界 / Long-running concurrent probe memory bounded |

* 阶段二：双形态真并行执行层 / Stage 2: truly parallel execution in both forms

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.6 | 简单形态常驻池（S-pool）：内置 spawn 投递到简单 runtime 自己的常驻线程池（与复杂形态物理隔离）；yield 重定义 = 同步点并兼容旧程序 / Simple-form resident pool: builtin spawn dispatches to its own resident pool (isolated from complex form); yield becomes a sync point, backward compatible | spawn_demo 类程序真实多线程，tid 去重 ≥ 2 / spawn_demo-style programs truly multithreaded, distinct tids ≥ 2 |
| p.6.7.7 | 简单形态窃取队列（S-deque）：per-worker 双端队列 + 窃取 + 溢出（复刻 sched_ws 算法、独立实现）；协作让出点 / Simple-form deque: per-worker deque + steal + overflow (reimplemented, isolated); cooperative yield points | 不平衡负载 stolen>0、结果全对 / Unbalanced load stolen>0, results exact |
| p.6.7.8 | 复杂形态常驻池（C-pool）：sched_ws 去每轮 drain 重建；池起于首次 drain、止于 shutdown；drain = 等本轮排空不回收池 / Complex-form resident pool: no per-drain rebuild; pool starts at first drain, ends at shutdown | 多轮 drain 复用同一组线程句柄 / Multiple drains reuse the same thread handles |
| p.6.7.9 | 复杂形态 per-P 细锁（C-deque）：每 worker 段独立锁 + 全局溢出队列细锁，去全局单 CS；窃取窗口缩小 / Complex-form per-P locks: per-worker segment locks + fine-grained overflow lock, remove the single global CS | ms4 < ms1 可复现（修复 78>47）/ ms4 < ms1 reproducible (fixing 78>47) |

* 阶段三：调度补齐（协作抢占 + 结构化并发）/ Stage 3: scheduling completion

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.10 | 协作抢占统一：yield/gosched 显式点 + 时间片计数器检查插桩；两形态统一抢占机制 / Unified cooperative preemption: explicit yield/gosched points + timeslice counter checks | 长任务可让出，调度公平性探针 / Long tasks yield; fairness probe |
| p.6.7.11 | 结构化并发 WaitGroup：spawn 分组句柄 + 等全部完成（Go sync.WaitGroup）；内置与 ctx 双入口 / WaitGroup structured concurrency: grouped spawn + wait-all (Go sync.WaitGroup); both builtin and ctx entries | wg 并发求和多组精确 / Multi-group wg sums exact |

* 阶段四：channel/select 增强 / Stage 4: channel/select enhancement

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.12 | channel Go 语义：tl_chan 增加 close 广播唤醒、双向、select 多路收发 / Go-style channel: close broadcast wakeup, bidirectional, select multi-way | select/close 广播探针 PASS；parity_chan 对比仍逐字节一致 / select/close probes PASS; parity_chan still byte-identical |

* 阶段五：验收与发布 / Stage 5: acceptance & release

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.7.13 | 双形态并行验收矩阵：两形态各自真并行探针 + 行为一致对比 + m6_actor 零回归 / Dual-form parallel acceptance matrix: per-form truely-parallel probes + behavior parity + m6_actor zero regression | 全 PASS、exit 0 / All PASS, exit 0 |
| p.6.7.14 | 收尾：preview.3、README/CHANGELOG、已知限制清单、双语文档 / Wrap-up: preview.3, README/CHANGELOG, known-limits list, bilingual docs | 自举核验 + 零回归 / Bootstrap verify + zero regression |

***

## 5. 依赖主线 / Dependency Line

阶段一（并发安全）→ 阶段二（真并行）→ 阶段三（抢占/WaitGroup）→ 阶段四（channel）→
阶段五（验收发布）。阶段二内部 S-pool 与 C-pool 可并行推进；C-deque 依赖 C-pool。

EN: Stage 1 (safety) → Stage 2 (true parallelism) → Stage 3 (preemption/WaitGroup) →
Stage 4 (channel) → Stage 5 (acceptance/release). Within Stage 2, S-pool and C-pool can
proceed in parallel; C-deque depends on C-pool.

***

## 6. 风险与对策 / Risks & Mitigations

* p.6.7.5 生命周期确定性波及 tiec 字符串/表 codegen，面大 → 放阶段一最后，先正确后性能。
  EN: p.6.7.5 touches tiec string/table codegen broadly → place last in Stage 1, correctness first.

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