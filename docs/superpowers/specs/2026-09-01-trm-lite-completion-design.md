# trm-lite 完善计划（p.6.5）——复杂形态完整实现

- **日期**：2026-09-01
- **状态**：规划（p.6.5 模块任务书，待执行）
- **范围**：在 trm-lite preview.1（简单形态 spawn/yield/collect 内置 + actor 简单执行体承载）基础上，补齐简单形态缺口（channel 原语），并**完整实现复杂形态**（work-stealing 调度、并发三色 GC 含分代/整理、可迁移栈、静态链接外壳 `import trm-lite`）。
- **依据**：`tie-main/docs/superpowers/specs/2026-08-26-trm-lite-design.md`（设计定稿）、`docs/designs/concurrency-model.md`（actor、C 组接入门 `#[unsafe.trm]`）。
- **对比基线**：trm-lite preview.1（2026-08-27）。

## 1. 现状盘点

**已完成（preview.0/1，简单形态）**：

- `spawn`/`yield`/`collect` 成为 tiec 完整内置原语（三处注册：is_builtin_name / builtin_call / ensure_builtins 主表 73→76）。
- 静态链接：`g_used_trmlite` → `link_exe` 追加 `trm_lite.a`（`TIE_TRM_LITE_LIB` 环境变量 → 相对默认路径）；`tig_trmlite_call` 直发 extern_call 不置 tie_interp。
- 闭包任务队列（core/mnn/sched）：`spawn_task/queued_count/queued_entry/queued_env/queued_retcode/queued_dequeue`；扁平 mark-sweep `collect()->i64`（core/gc）；表全局惰性初始化 `tl_sched_ensure/tl_gc_ensure`。
- actor 默认由简单执行体承载（替换 1:1 线程默认）：irgen_rt 每条消息 = `trm_lite_sched$spawn_task` 任务；yield 排空 + actor 等待循环 + 同步 RPC；actor 与 import trm-lite 混用 → 编译期报错。
- 闭包字面量 spawn 端到端通过（含捕获、void 返回、嵌套 spawn）。
- 汇总库 `core/runtime/tl_runtime.tie`（import sched+gc → trm_lite.a）。

**缺口（p.6.5 目标）**：

- 简单形态：channel 语言原语未实现（仅 actor 的 record mailbox，无通用 channel）。
- 复杂形态：work-stealing 调度、并发三色 GC、可迁移栈、静态链接外壳 `import trm-lite` 均未实现。

## 2. 目标与范围

p.6.5 目标 = **让 trm-lite 达到「Go 式静态内置 runtime」的完整形态**：

1. **简单形态补全**：channel/mailbox 语言原语（`ch_send`/`ch_recv`/`ch_close`），actor mailbox 与之衔接。
2. **复杂形态完整实现**（用户定调，超越设计 §8 的最小可靠子集）：
   - work-stealing 调度（多 OS 线程池 + 双端队列 + 任务窃取 + 抢占（时间片/协作） + M:N 承托）。
   - 并发三色 GC 完整（标记栈/写屏障 + 后台回收器 + 分代（新生代/老年代）+ 整理（mark-compact））。
   - 可迁移栈完整（栈段管理（分段栈/拷贝栈）+ 精确根扫描来源 + 与调度/GC 咬合）。
   - 静态链接外壳：`import trm-lite` 触发 tiec 将复杂 runtime 静态链接进单一二进制。
   - 抢占能力与 trm 路线 B 对齐。
3. **验收闭环**：多执行体分配/回收 + 消息传收 demo；简单 vs 复杂行为一致；m6_actor 零回归。

**非目标**：反射、热更、动态加载、跨平台完整矩阵、与 trm 引擎（字节码 VM）功能合并。

## 3. 架构与机制要点

- **双形态**：简单 = tiec 内置 codegen（零 import）；复杂 = `import trm-lite` 静态链接。同程序不可混用（编译期报错，已有）。
- **依赖方向（硬约束）**：应用 → 库 → runtime 接口 → 执行层；执行层不依赖库层；语言级原语不依赖 trm-lite 库；trm-lite 库不依赖 trm 引擎。
- **执行层落位**：
  - sched：`tl_task`（env/entry/retcode）+ 多线程池 + 窃取双端队列 + 抢占计时；`yield` 仍是协作让步。
  - gc：并发三色（标记栈/写屏障/后台回收器）+ 分代 + mark-compact 整理；精确根扫描依赖栈图，无栈图降级保守根（文档明示）。
  - stack：可迁移栈段，GC 根来源 + 调度切换载体。
  - runtime 汇总：`import trm-lite` 时 tiec 把 sched+gc+stack 编译为 `trm_lite.a` 静态链接。
- **channel**：语言原语 → tiec codegen（互斥 + 条件变量 + 队列），复杂形态承载于 trm-lite mailbox；`ch_send`/`ch_recv`/`ch_close` 语义对标 Go。

## 4. 任务书（切片，依赖升序）

- **p.6.5.1 复杂形态静态链接外壳**：`import trm-lite` → tiec 静态链接复杂 runtime（import 即选择；与内置 spawn 混用报错已有）；最小可编译闭环。
- **p.6.5.2 work-stealing 调度器**：多 OS 线程池 + 每线程双端队列 + 任务窃取 + 抢占（时间片/协作）；M:N 承托 spawn/actor 任务；sched 从单队列升级。
- **p.6.5.3 并发三色 GC**：标记栈/写屏障 + 后台回收器推进；精确根扫描（依赖 p.6.5.5 栈图，缺失降级保守根）。
- **p.6.5.4 分代 + 整理**：新生代/老年代分代回收 + mark-compact 整理（老年代），对象头/年龄记录。
- **p.6.5.5 可迁移栈**：分段栈/拷贝栈切换 + 与调度抢占/GC 根扫描咬合；普通栈（简单形态）不受影响。
- **p.6.5.6 精确栈图**：语言栈图（IR/元数据）供精确根扫描；落地归属与顺序（设计 §9 待决项拍板）。
- **p.6.5.7 channel 语言原语**：`ch_send/ch_recv/ch_close`（tiec codegen + trm-lite mailbox 队列；互斥+条件变量）；actor mailbox 衔接。
- **p.6.5.8 actor × 复杂形态咬合**：actor 消息经 trm-lite mailbox 承载；`#[unsafe.trm]` C 组接入门落地。
- **p.6.5.9 多执行体分配/回收 + 消息传收 demo**：两形态验收载体（断言 exit 0 + 内存平衡）。
- **p.6.5.10 回归与对比验收**：m6_actor 零回归、路线 A/B 不受影响、简单 vs 复杂行为一致（输出/退出码）。
- **p.6.5.11 收尾**：trm-lite preview.2、README/CHANGELOG、已知限制清单、zero 依赖核验。

## 5. 依赖与前置

- 精确根扫描依赖**语言栈图**（p.6.5.6）；未就绪时 GC 降级保守根（行为正确、精度损失，文档明示）。
- **p.6.5.6 拍板（2026-09-02，设计 §9 待决项 3 定案）——「任务 env 即根」**：
  tie 闭包 env 为编译期静态捕获（副本），无运行时枚举能力；因此复杂形态的
  「精确根」落地为——**任务闭包 env 引用对象的根集合**，由任务内 `add_root`
  显式登记 + 写屏障（set_ref 黑→白 置灰、循环中晚到根置灰）维护；运行时其余
  sweep 仅在「pending==0 && active==0」无任务窗口执行，任务运行期（active>0）
  的对象天然受保护。精度损失：任务运行期未显式登根/未建立引用边的局部临时
  对象依赖「无任务窗口」而非逐帧栈图，语义正确（不停驻漏保），仅接受程度保守
  （该精度损失已由探针 root_protect_demo 证明：active>0 期间对象不回收、任务
  结束后收敛至 0 无泄漏）。
- 抢占对齐 trm 路线 B：以 trm-final-design 的抢占语义为参照，不 gate 于 trm 引擎能力。
- actor C 组接入门 `#[unsafe.trm]`：concurrency-model §7.1 定义的语法门，p.6.5.8 落地。

## 6. 验收标准

- 每片：对应 probe/单测 + 行为等价（vs 简单形态/Rust 桥既有语义）+ 编译零错误。
- p.6.5.9 demo：多执行体并发分配/回收 + 消息传收，exit 0，内存平衡（无泄漏/无双重释放）。
- p.6.5.10：m6_actor 全量零回归；路线 A/B 产物不受影响；简单 vs 复杂同一程序输出/退出码一致。
- 收尾：自举（tiec 编译自身）零错误；`import trm-lite` 产物零外部依赖。

## 7. 风险与对策

- 纯 tie 实现 work-stealing/并发 GC/可迁移栈复杂度高 → 分片推进、每片独立验收；先正确后性能。
- 精确栈图缺失 → 保守根降级 + 文档明示精度损失（设计 §6 既定）。
- 平台差异（Windows 线程/同步原语）→ 沿用 kernel32/CRT 既有 extern 手法（参照 m6_actor 既有实现）。
- 与内置路径混淆 → 编译期报错（已有）；import 路径独立验证。

## 8. 相关文档

- `tie-main/docs/superpowers/specs/2026-08-26-trm-lite-design.md`（设计定稿）
- `tie-main/docs/designs/concurrency-model.md`（actor、C 组接入门）
- `tie-main/docs/designs/trm-final-design.md`（trm 定稿，抢占语义参照）
- 落地仓库：`trm-lite/`（独立仓库，preview.1 基线）
