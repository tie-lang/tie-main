# trm-lite p.6.7 阶段二/三/四 执行提示词（Prompt Pack）

* 日期 / Date：2026-09-03

* 定位：供后续执行会话/子代理直接粘贴使用；每个子项提示词 = 完整开工指令。

* 依据：`2026-09-03-trm-lite-p67-parallel-design.md`（规划 spec）+ 本包「通用纪律」。

* 约束：全部工作用 **tie 语言**完成；不引入其它实现语言；每子项完成后同步更新
  tie-main/CHANGELOG.md 与 trm-lite/CHANGELOG.md 对应条目。

***

## 0. 通用纪律（每个子项执行前必读）/ Common discipline

### 0.1 环境与构建链

* 编译器自举链：当前工作编译器 = `tie-main/compiler/tiec71.exe`（含 p.6.7.1\~6.7.6）。
  改完编译器源码后重建：`& tiec70.exe driver.tie -o tiec71.exe`（在 compiler/ 目录，
  源编译器选「上一个已知可用」——改坏了用 tiec70 重编）。

* trm\_lite.a 重建（双成员静态库）：

  ```powershell
  $ar = "F:\Projects\tie-repo\tie-main\dist\<dist>\bin\llvm\bin\llvm-ar.exe"
  # 在 trm-lite/ 目录
  & <tiec>.exe core\runtime\tl_runtime.tie -o _c.a
  & <tiec>.exe tl_chan_lib.tie -o _h.a
  New-Item -ItemType Directory -Force _t | Out-Null; Copy-Item _c.a,_h.a _t
  Push-Location _t; & $ar x _c.a; & $ar x _h.a; & $ar rcs ..\trm_lite.a tl_runtime.o tl_chan_lib.o; Pop-Location
  Remove-Item -Recurse -Force _t,_c.a,_h.a
  ```

* **.a 必须用「当前 tiec」重建**：编译器任何行为变化都会改变库产物，旧 .a 会导致
  LNK2005（如 worker 函数重复定义）。改 trm-lite 源码或编译器后先重建 .a。

* 探针目录：`tie-main/tests/_p67_probe/`；回归探针在 `tests/m6_actor/` 与
  `trm-lite/tests/`。

### 0.2 链接与符号纪律（血泪教训）

* **extern 单一声明源**：kernel32 同步/线程原语全部声明在 `tl_k32.tie`（纯声明、
  零函数零命名空间，文件尾 extern 以 `;` 收尾）。任何模块绝不自行声明同名 extern、
  绝不 import tl\_sync 来「拿声明」——tl\_sync 是命名空间封装宿主（产 `tl_sync$*`
  符号），import 它会泄漏符号进 .o 成员，与复杂形态内联方链接期多重定义。

* **函数符号不能走 kind3 全局直引**（global\_ref 查 g\_global\_names 登记；函数未登记
  → 落 `%N` use-of-undefined-value）。函数地址 = `op63(ptrtoint @fn to i64)`+
  `op25(inttoptr→ptr)` 值引用。

* **extern\_call(op36) 操作数段纪律**：所有值产生指令（inttoptr/const\_i/alloca…）
  必须在 `add_operand` 序列**之前**创建；IMM（kind2）参数直接传**字面量**（如 0），
  传值 id 会输出池 id 数字（如 288）。void call 不命名寄存器。

* **结构保持**：p.6.7.2\~6.7.6 已把 `tl_tbl` 锁原语自持化 + 双成员 .a，保持该结构。

### 0.3 并发与验收纪律

* 探针断言只依赖确定性结果（计数精确 / tid 去重 ≥2 / 无重复），不做墙钟严格时序断言
  （主机噪声，spec §6）；真并行主证据 = 多线程 tid 去重，墙钟为辅。

* 简单形态（内置 spawn/yield，无 import）任务体可并发触碰：全局表（每表锁）、SSO
  字符串（原子 bump）、全局计数（atomic<i64> 或独立槽位）、println（行级原子）。

* 每子项结束：p.6.7 全套探针回归 + m6\_actor 正向探针回归 + 自举 fixpoint
  （tiecN→tiecN+1→tiecN+2 字节一致：`(Get-FileHash tiecN+1).Hash -eq
  (Get-FileHash tiecN+2).Hash`）。

***

## p.6.7.7–6.7.9：双形态真并行执行层 / Truly parallel execution in both forms

### p.6.7.7 简单形态窃取队列（S-deque）—— Simple-form stealing deque

**目标**：把简单形态 S-pool 的「单全局队列」升级为 per-worker 双端队列：owner 段尾
LIFO 自取、他人段头 FIFO 窃取、段满溢出全局（复刻 sched\_ws 算法，**独立实现**到
`trm-lite/core/mnn/sched.tie`，不依赖复杂形态）。

**前置**：p.6.7.6（S-pool 线程安全队列 / 锁体系已就位）。

**实现要点**：

1. 常量 `S_SEG_CAP: i64 = 256`；每 worker 段预分配 `P×S_SEG_CAP` 槽（g\_items），
   `g_h/g_t` 每 worker 头尾游标（g\_h\[me]..g\_t\[me] 左闭右开）。
2. `spawn_task`：`w = g_spi % P` 轮转选段；段未满 → 推段尾（g\_items\[w\*CAP+g\_t\[w]],
   g\_t\[w]++）；段满 → 溢出表 `g_ovf`（全局，同锁）。pending++；**广播唤醒**保留。
3. `pop_task`（worker 自取入口，出参 env/rc 不变）：锁内按序依次
   ①自己段尾 LIFO：`g_t[me]>g_h[me] → g_t[me]--，取 g_items[me*CAP+g_t[me]]`
   ②他人段头 FIFO 窃取：扫 `r=1..P`，`j=(me+r)%P`，`g_t[j]>g_h[j] → 取
   g_items[j*CAP+g_h[j]], g_h[j]++`，g\_stolen++
   ③全局溢出队头 `g_ovf[g_ovf_head++]`。
   全部在 g\_cs\_s 锁内完成（第一阶段保持单锁；per-segment 细锁是复杂形态
   p.6.7.9 的工作）。
4. 任务内再 spawn：执行任务时的 worker 调用 spawn\_task，轮转会投到某段（可能
   是自己段尾 → LIFO 本地优先消费）✓。
5. `yield_wait` 语义不变（等 pend==0）；`queued_count` 等旧观察量保留。

**验收**（新增 `tests/_p67_probe/s_deque_probe.tie`，无 import 纯内置）：

* 失衡负载：1 个「制造者」任务内 spawn 500 子任务（每子任务表 push 自编码），
  断言 `stolen>0`（新增观察量 `trm_lite_sched$stolen_count()` 或等价）**或**全部
  子任务执行线程 id 覆盖 ≥2；

* 共享表元素完整无重复（区间校验 + 两两去重），len 精确；

* yield 同步点后全部完成；`PASS / exit 0`；连跑 3 次全 PASS。

* 回归：s\_pool\_par\_probe / spawn\_demo / mix\_simple\_probe / p.6.7 全套 / m6\_actor；
  自举 fixpoint。

***

### p.6.7.8 复杂形态常驻池（C-pool）—— Complex-form resident pool

**目标**：`trm-lite/core/mnn/sched_ws.tie` 去掉「每轮 drain 重建线程池」：池起于
首次 drain、止于 shutdown；drain 只等本轮排空、不复建/不回收。

**前置**：p.6.7.6 的 S-pool 常驻语义可作参照（简单形态已常驻）。

**实现要点**：

1. 新标志 `g_pool_up`；`ensure_pool()` 在 `g_pool_up==0` 时起 `P worker + 1 GC`
   线程并把 `g_pool_up=1`；`drain()` 不再调 `join_pool()`，只 `等 pending==0`
   （延续现有 cv\_wait(pending==0) 循环）。
2. worker 主循环空闲分支：`pending==0 && active==0` 时**不再 return**，改为
   `cv_wait(g_cv, g_cs, 50)` 继续存活（类似简单形态 pool\_idle\_wait）；仅在
   `g_shutdown==1` 时退出。
3. 新增池收尾（沿用 ctx\_shutdown 路径）：置停止标记 + 广播唤醒 + join 全部线程
   （恢复 join\_pool 逻辑只走收尾）。
4. `g_ths` 只清于真正池销毁，不在 drain 末尾重建；`reset_round` 只清段/计数不动
   线程表。

**验收**（新增 `tests/_p67_probe/c_pool_resident_probe.tie`，import tl\_runtime\_ctx）：

* 连续 3 轮 `ctx_spawn × N → ctx_drain`；断言线程句柄表长度恒定（不随轮数增长）
  （新增观察量或经 `ctx_*` 转发），且每轮执行线程 tid 覆盖 ≥2；

* 每轮结果精确（共享表 len 恰好累积、无重复无丢失）；

* `ctx_shutdown()` 后进程正常退出 exit 0；

* 回归：ctx\_ws\_demo / ctx\_gc\_demo / s\_pool\_par\_probe / p.6.7 全套 / m6\_actor；
  自举 fixpoint。

***

### p.6.7.9 复杂形态 per-P 细锁（C-deque）—— Complex-form per-P fine locks

**目标**：去掉 sched\_ws 的**全局单 CS**（g\_cs 既做队列又做计数与唤醒）：每 worker
段独立锁 + 全局溢出队列细锁 + 计数专用锁；窃取窗口缩小（只锁目标段）。

**前置**：p.6.7.8（常驻池）。基线性能数据：`ms4 > ms1`（78>47 即为退化拐点，
spec §4 记录）。

**实现要点**：

1. 每 worker 段锁 `g_seg_lks[i]`（CS）；段头尾读写（自取 / 窃取 / 溢出转移）持
   「目标段（或自段）」锁；锁序固定（自段→他段）防死锁。
2. 全局溢出队 `g_ovf` 独立锁 `g_ovf_lk`（push 溢出与取溢出分离细锁）。
3. 计数 `g_pending/g_active` + 空判断 + cv 唤醒收敛到一把**短临界**计数锁
   `g_cnt_lk`（不做任务数据操作，临界区极小）。
4. spawn（轮转选段 + 写段）+ 任务内再 spawn 路径同步更新；drain 等待逻辑不变
   （等 pending==0）。
5. 保留观察量（stolen/migrated/completed），线程数语义与 p.6.7.8 一致。

**验收**（新增 `tests/_p67_probe/c_deque_perf_probe.tie`）：

* 负载探针：P=4，两组对比——M=1 单线程串行 vs M=4 并行，同负载下**并行墙钟
  < 串行墙钟可复现**（宽松门槛：连续 3 次测量中 ≥2 次成立；spec §6：墙钟为辅，
  tid 覆盖 ≥2 为主证）；

* 失衡负载 stolen>0、结果精确；连续 3 轮 drain 复用同一组线程；

* 回归：ctx\_ws\_demo / ctx\_gc\_demo / s\_pool\_par / p.6.7 全套 / m6\_actor；自举
  fixpoint。

***

## 阶段三：调度补齐（协作抢占 + 结构化并发）/ Scheduling completion

### p.6.7.10 协作抢占统一 / Unified cooperative preemption

**目标**：两形态统一协作抢占：显式让出点（`yield()`=同步点已就位、新增 `gosched()`
\=纯让出不等待）+ **时间片计数器检查插桩**（调度级抢占点：任务再 spawn / pop 循环
边界）。

**前置**：p.6.7.6/6.7.7（简单形态）、p.6.7.8/6.7.9（复杂形态）。任务体为 `fn()`
原子执行体（p.6.5.5 语义不变），不可硬中断——抢占体现为**调度点让出**。

**实现要点**：

1. `gosched()` 内置（tiec irgen\_expr 注册）+ 双形态运行时入口：简单 =
   `trm_lite_sched$gosched()`（让出 = 时间片归零 + 转 idle 后重查队列，不等待
   pending）；复杂 = `trm_lite_ws$gosched()` 同语义。
2. 时间片：每 worker 本地计数 `g_slice[i]`；fetch 任务时 slice--，归零 → 让出
   （任务**已原子跑完**，让出 = 转队尾 / 等待窗口，避免单任务长期独占 pop 循环）；
   插桩点 = worker 循环「pop→执行→pop」边界（不深入任务体）。
3. `yield()` 语义不变（同步点）；`gosched()` 为不等待让出。旧程序只用 yield，
   零行为回归。
4. 公平性观察量：每 worker 执行任务计数（或子任务被其它 worker 承接数）。

**验收**（新增 `tests/_p67_probe/preempt_fair_probe.tie`，双形态各一）：主线程连环
spawn 大量轻任务 + 少量长任务，长任务体内显式 `gosched()`；断言：所有任务全部完成
（计数精确）+ 执行分布 >1 个 tid（长任务未独占单线程）+ 时间片让出路径不丢任务
（len 精确）。回归全套 + fixpoint。

***

### p.6.7.11 结构化并发 WaitGroup / WaitGroup structured concurrency

**目标**：`sync.WaitGroup` 语义：`wg_add(n)` / `wg_done()` / `wg_wait()`；
内置 + 复杂形态 ctx 双入口。

**前置**：p.6.7.10（gosched/抢占点）。运行时已有 pending 计数机制可复用底座。

**实现要点**：

1. 运行时（trm-lite）新增 `trm_lite_wg`（并入 sched/sched\_ws 或独立模块均可）：
   `wg_new() -> i64`（句柄：CS/CV 惰性 init + 计数槽）、`wg_add(h,n)`、
   `wg_done(h)`（计数--，归零广播）、`wg_wait(h)`（锁内等计数 0）、`wg_close(h)`。
   计数读写全持组锁（U3/U4 纪律：游标与数据同锁）。
2. 语言入口：内置 `wg_new/wg_add/wg_done/wg_wait`（tiec 注册 + extern 桥，冲突
   检测对齐 spawn/channel 模式）+ 复杂形态 `tl_runtime_ctx.ctx_wg_*` 转发。
3. 简单形态探针：主线程 `wg_add(8)` → spawn 8 任务各 `wg_done` → `wg_wait` 后
   断言汇总精确；复杂形态同逻辑走 ctx 入口。

**验收**（新增 `tests/_p67_probe/wg_par_probe.tie`，双形态各一组）：多组 × 多任务
并发 `wg_done`，`wg_wait` 返回后每组分和精确（如 4 组 × 8 任务 × 自编码求和）、
重复执行 3 次一致；回归全套 + fixpoint。

***

## 阶段四：channel/select 增强 / channel/select enhancement

### p.6.7.12 channel Go 语义 / Go-style channel

**目标**：`tl_chan` 增强：**close 广播唤醒**（当前只唤醒一个）、双向语义明确、
**select 多路收发**（任一可用分支执行）。

**前置**：p.6.5.7 channel 原语（mailbox + 每通道锁）已就位；p.6.7.3 全局分配锁。

**实现要点**：

1. `ch_close`：进入临界区置 closed → **广播唤醒**（循环 WakeConditionVariable
   或按等待者计数），后续 send 全部失败、recv 排空后 -1——保持 Go 语义（close 后
   recv 直到空再返回零值/-1；send 失败）。
2. `select`：语言级新增内置 `ch_select`（平行数组承载：通道表 + 动作码表
   \[1=recv / -1=send] + 值槽表，返回命中的分支下标）；运行时锁内轮询各通道非阻塞
   可用分支，全不可用 → cv\_wait 限时重试（与现有 ch\_send/ch\_recv 非阻塞降级一致）。
3. 广播唤醒在 chan 成员内实现（tl\_chan）；tl\_k32 视需补充
   `WakeAllConditionVariable` 声明并让 tl\_sync 封装一次。
4. 保持既有通道句柄 ABI 与每通道锁；`parity_chan` 语义不回归。

**验收**：

* 新增 `tests/_p67_probe/chan_select_probe.tie`：3 通道竞争 + close 广播：多 reader
  全部看到关闭（close 后所有阻塞 recv 依次返回 -1，无丢 reader）；select 多路各
  分支均可达（计数精确）；

* 既有 `parity_chan_demo`（简单 vs 复杂行为对照）输出逐字节一致；

* 回归：chan\_open\_par\_probe / mix\_simple\_probe / m6\_actor / p.6.7 全套；fixpoint。

***

## 完成标准（p.6.7.7–6.7.12 通用）

1. 全部新增探针 `PASS / exit 0`，连跑 3 次稳定；
2. p.6.7 全套 + m6\_actor 正向探针零回归（panic\_raise 预期非零）；
3. 自举 fixpoint：tiecN→tiecN+1→tiecN+2 字节一致；
4. CHANGELOG（tie-main + trm-lite）逐子项记录；spec 风险/已知限制更新；
5. 每一子项均恪守 §0 纪律（全 tie / 链接纪律 / 探针纪律）。

