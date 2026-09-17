# 设计定稿：tiec 多线程并行构建
*EN: Design Finalization: tiec Parallel Build (Multithreading)*

> 状态：**设计定稿**（2026-09-17 讨论对齐）
> 关联里程碑：**p.9.15**（与[p.9.15 缓存重构](compiler-cache-redesign.md)**合档**，
> 双线一档：内容寻址缓存 + 多线程并行构建；`--jobs` 自 p.9.1.3 预留的
> “增量/缓存/并行一并落地”在此兑现）。本档为**并行构建**权威设计。
> 设计基线：2026-09-17 现场核读 `tie-repo/tiec/compiler/driver.tie`
> （`g_jobs` 仅写配置 `advanced.threads`、无并行逻辑；`keel_dispatch`/`keel_run_pipeline`
> 5 段串行管线）与 `backend/toolchain.tie`（opt/clang/llvm-ar 经 `run()` 子进程执行）。
> 并发底座：**双模式**——默认**原生线程桥**（CreateThread/pthread，零运行时、确定性）；
> 参数开关`**超级并行模式**`（高性能吞吐，trm-lite Go 式 M:N 超订，默认关，
> 引擎不锁实现、可配置）。

> EN: Status: **Design finalized** (2026-09-17 discussion alignment). Milestone **p.9.15** —
> parallel build, **same tier as the [p.9.15 cache redesign](compiler-cache-redesign.md)**
> (two tracks, one tier): content-addressed cache + multithreading; the `--jobs` concurrency
> reserved by p.9.1.3 is delivered here. Concurrency substrate: **dual-mode** — default
> **native-thread bridge** (CreateThread/pthread; zero-runtime, deterministic); an opt-in
> **super-parallel mode** (high-throughput, trm-lite Go-style M:N over-subscription, default
> off; config-driven, not implementation-locked).

---

## 一、现状

- **编译器单线程串行**：`--jobs <N>`（driver.tie:60,184-188）仅把 N 写进配置
  `advanced.threads`（driver.tie:1422-1423），**无任何并行逻辑**。原注释即声明并行
  “随 p.9.1.3 增量/缓存一并落地”，一直延期。
- **管线 5 段强阶段依赖**：`kpass_front`（词法→语法→语义+import）→ `kpass_irgen`
  （AST→tie-IR）→ `kpass_tieir`/`kpass_trmemit` → `kpass_emit`（→.ll）→ `kpass_link`
  （clang opt/编译/链接）。单编译单元纵向链，**单文件内几乎不可并行**。
- **后端已子进程化**：opt/clang/llvm-ar 由 `backend/toolchain.tie` `run()` 经
  `exec_code`/`exec_output` 外部执行——已具备天然并发执行面。
- 输入形态为**单入口**（`g_input`），import 在语义阶段 `semantic.expand_imports` 递归
  读取 → 一个入口可展开成多模块依赖图。

---

## 二、目标与定界

- **目标**：工程级 batch（多入口/工程清单）下按**文件级粗粒度**并行，前端+中端在 worker
  池上分布，后端 clang 子进程并发，最终统一收口。收益最大化且与 p.9.15 缓存的内容寻址
  粒度天然协同。
- **双模式**：默认原生线程池（零运行时、确定性门禁）；参数开关超级并行（trm-lite M:N，
  高吞吐，默认关）。
- **不纳入**（接口预留）：
  * 单文件内函数/符号级细粒度切分（纵向依赖强、收益低）。整文件粒度为本期交付。
  * 常驻后台守护/长期存活 worker 进程（沿用“编译入口即开即合”）。
  * 改变产物语义（并行只改调度/顺序，产物逐字节不变）。

---

## 三、方案总览

以「工程级 batch + 文件级任务并行 + 双后端调度」为轴，串起六项设计：

1. **工程级 batch 输入**：多入口或工程清单 → 依赖图 → 并行任务集。
2. **默认模式：原生线程 worker 池**：固定 `--jobs` 线程抓文件任务，前端+irgen 并行，
   确定性汇合。
3. **后端 clang 并发**：lntermediate opt/编译/链接子进程池并发，最后统一链接。
4. **并发缓存写**：与内容寻址缓存协同（临时文件+rename 原子），多线程/多进程无竞态。
5. **超级并行模式**：参数开启高性能 M:N，超订到多核。
6. **确定性门禁 + 性能报告**（兼顾）：串行/并行/超并行产物逐字节恒等为硬门禁，加速比
   为参考报告。

---

## 四、详细设计

### 4.1 工程级 batch 输入

- 形态：`tiec batch.td`（工程清单）或 `tiec a.tie b.tie`（多入口）；清单声明依赖图、
  共享参数、入口集合与目标（exe/lib/shared per 入口）。
- 依赖解析：复用语义 `expand_imports` 的闭包结果，为每个入口生成（入口+依赖）任务集；
  与 p.9.15 缓存的内容寻址指纹（同构依赖指纹）共用，锁定“哪些文件未变可复用”。

### 4.2 默认模式：原生线程 worker 池

- **worker 池**：`--jobs N` 起 N 个原生线程（wrapper 走 CreateThread/pthread；
  进程内仅在编译入口创建、结束汇合销毁）。每个 worker 任务队列取一个「入口文件（及其
  import 闭包）」跑 `kpass_front` + `kpass_irgen`,完成把中间物交回。
- **同步原语**：自持最小集（队列锁 / 条件变量 / 汇合 barrier / 原子计数），封装为
  跨平台薄层（Win32 ↔ pthread，镜像 irgen_rt 的 `tl_linux_shim` 做法）。
- **确定性**：任务分发顺序确定；汇合后按**规范顺序**（入口清单顺序）落盘/拼接，保证
  **同输入同 `--jobs` 不同值产物逐字节一致**。后端子进程并发亦在汇合后统一链接。

### 4.3 后端 clang 并发

- `kpass_link` 段的 opt/`compile_object`/`archive` 已是子进程（`toolchain.run`）；
  批处理下按文件提交到同一 worker 池或子进程池并发执行，仅**最终链接串行**收口。
- 中间 `.o`/`.opt.ll` 按规范命名，避免并发写冲突；完成后统一链接。

### 4.4 并发缓存写（与 p.9.15 内容寻址协同）

- 多线程/多进程并发写缓存遵守 p.9.15 原子写约定（临时文件 + rename），内容寻址
  天然去重与幂等；读缓存命中做产物指纹核对。此处在并行档补齐多线程并发写验证。

### 4.5 超级并行模式（参数开关）

- 新增参数（默认关）：`--parallel-mode=<native|super>`（或等价配置项）；`super` 模式
  用 trm-lite Go 式 M:N 调度（`spawn_task`/channel 背压/可迁移栈）超订到多核，面向
  大批量高吞吐；此时 tiec 链接 trm-lite.a，**离默认零运行时**——故默认仍 `native`。
- 引擎**不锁实现**：具体超订策略/调度参数均可配置；`native` 与 `super` 产物一致性
  仍以确定性门禁校验（super 下调度非确定，但汇合结果按规范顺序，产物保持不变）。

### 4.6 CLI 与配置

| 项 | 取值 | 说明 |
|----|------|------|
| `--jobs <N>` | 现状（N≥2 生效） | 原已解析，落地为 worker 池规模（默认=核心数） |
| `--parallel-mode` | 新增 `native`(默认)/`super` | 并发底座选择 |
| `advanced.threads` | 现状 | 配置文件写出的 jobs 基线 |
| `batch.td` | 新增 | 工程清单输入形态 |
| 并发写（cache） | 复用 p.9.15 | 原子写 + 内容寻址 |

---

## 五、排号与分期

**档位：p.9.15（与缓存重构合档）。并行为第 .6–.9 子项（在缓存 .1–.5 之后）**

- p.9.15.6 **工程级 batch + 原生线程 worker 池（默认底座）**：多入口/工程清单、`--jobs`
  落为 worker 池、前端+irgen 文件级并行、汇合确定性、后端 clang 子进程并发 + 统一链接。
- p.9.15.7 **并发缓存写验证**：多线程/进程并发写 p.9.15 内容寻址缓存（原子 rename/指纹
  核对），无竞态、无半截缓存。
- p.9.15.8 **超级并行模式**：`--parallel-mode=super` 接入 trm-lite M:N 超订，高吞吐；
  默认关保持零运行时基线。
- p.9.15.9 **并行验收与性能报告**：确定性门禁（串行/并行/超并行产物恒等 + 自举不动点
  二次 SHA）+ 性能参考报告（多核利用率/编译耗时）+ s21/diagcodes/m5 回归不劣化 +
  grep `.ps1`=0。

> 分期顺序原则：先默认底座确定性（.6）后并发写（.7）再超级模式（.8）再总验收（.9）；
> 依赖缓存档 .1–.5 的原子写/内容寻址已就位。各期可并线、无前置依赖。

---

## 六、验收度量（兼顾）

- **确定性门禁（硬）**：同一 batch，`--jobs` 取不同值 / `--parallel-mode` 取 native|super，
  产物逐字节恒等；自举不动点二次 SHA 一致。
- **性能参考（软）**：多核利用率、编译耗时相对串行下降比；不设硬加速比门槛，仅报告。
- **正确性**：并行结果的 exit 码/产物与串行等价；并发缓存写后无竞态、无残缺对象。
- **回归**：s21 / diagcodes / m5 全量不劣化；`verify-cache` 新旧全绿。

---

## 七、兼容性与迁移

- `--jobs` 旧语义（仅写配置）升级为真实并行：N<2 即串行、行为与旧一致，无破坏。
- 新参数均默认值保守（`parallel-mode=native`、Jobs 默认核心数），不改变无参数编译行为。
- 单入口路径保持完全向后兼容（不传 batch/工程清单即旧单文件行为）。

---

*本设计为 tiec 多线程并行构建的权威执行依据（tie-main 侧），与
[p.9.15 缓存重构](compiler-cache-redesign.md)同档双线；代码实现落在 tie-repo/tiec。*