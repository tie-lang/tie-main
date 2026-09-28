# 设计定稿：解释器性能优化（分级 JIT 即时编译 + 拆箱值模型 + 字符串原语优先）
*EN: Design Finalization: Interpreter Performance Optimization (Tiered-JIT + Unboxed Values + String-Primitives-First)*

> 状态：**设计定稿**（2026-09-17 讨论对齐）
> 关联里程碑：**p.9.17 解释器性能**（独立档，与 trm 字节码运行时路线 B **保持边界**：
> 解释器服务 REPL/脚本/DAP/崩溃诊断，trm 服务独立字节码运行时，本期不强行统一）。
> 主线四项：①**JIT 即时编译**（AST → LLVM IR → native，动态加载，复用 tiec 后端）
> ②**拆箱标量**（消灭 per-value 10 表 push/寻址）③**字符串/容器原语优先**（全局热点，
> 编译器/解释器/tsp 三方受益）④**分级执行策略**（冷路径回退解释器 + 热路径 JIT，阈值可配）。
> 设计基线：2026-09-17 现场核读 `tiec/compiler/interp/`（`interp.tie` tree 遍历 +
> `exec_stmt` if/else 分派、`value.tie` 盒装节点 id + 10 平行表、`interp_call.tie`
> 函数调用、`interp_code.tie` 为宏准引用非 VM）。

> EN: Status: **Design finalized** (2026-09-17 discussion alignment). Milestone **p.9.17 —
> interpreter performance** (independent; keeps boundary with the trm bytecode route-B runtime:
> interpreter serves REPL/script/DAP/crash-diagnostics, trm serves its own bytecode runtime;
> no forced merge this cycle). Four lines: ①**Tiered JIT** (AST → LLVM IR → native, dynamic
> load, reusing the tiec backend) ②**unboxed scalars** (remove per-value 10-table push/index)
> ③**string/container primitives first** (global hotspot benefiting compiler/interp/tsp)
> ④**tiered execution** (cold path falls back to the interpreter, hot path JIT; thresholds
> configurable). Baseline: read of `tiec/compiler/interp/` on 2026-09-17.

---

## 一、现状与性能画像

解释器为**纯树遍历 AST 解释器**，值全部盒装：

- **盒装值**（`value.tie`）：每值 = 节点 id，写进 10 张平行表
  （`v_types/v_ivals/v_aux/v_fvals/v_svals/v_koff/v_kcnt/v_kids/v_mkeys/v_mvals`）；
  `new_node()` 每建一个值做 **10 次 `table_push`**；局部算术/比较疯狂分配与表寻址。
- **树遍历分派**（`interp.tie`）：`exec_stmt`/`gen_expr` 按节点 tag if/else 链动态分派，
  一次执行重走整树，无扁平化、无编译缓存。
- **函数调用**（`interp_call`）：每 call 打包实参 + 按名字符串查函数表。
- **字符串/容器原语慢**：`str_char` 本机单次 ~360µs、逐码点遍历大文本 O(n²)（tsp 注释
  明示）、`+` 拼接分配——是编译器自身/解释器/tsp 三方共用热点。
- **值池只增不减**：会话内节点只增，长会话负面缓存局部性。

> 定位裁决：解释器是 REPL/脚本/DAP/诊断共享运行路径，性能差直接拖慢交互体验。**主求值
> 迁移到 JIT native，解释器退为冷/兜底路径**；字符串原语作为全局热点优先独立攻坚。

---

## 二、目标与定界

- **主路径 JIT**：热函数/脚本即时编译 native 并动态加载执行，性能逼近本机编译。
- **兜底解释器**：冷/小输入仍走优化后的解释器（拆箱 + 直分派），保证 REPL 单行低延迟
  （JIT 编译子进程开销对小输入反而慢，须分级）。
- **拆箱 + 原语**：值模型拆箱标量，字符串/容器原语优先优化。
- **不纳入**（接口预留）：
  * 与 trm 字节码运行时的内部统一（保持边界，另期评估）。
  * 线程内并发求值（解释器仍同步单线程；并行随 p.9.15 另行）。
  * 改变 tie 语义/诊断行为（只改执行路径与性能）。

---

## 三、方案总览

四级叠加，先基建后升级：

1. **字符串/容器原语优先**（全局热点）：优化 `str_char`/逐码点遍历/拼接分配等运行期
   原语——受益编译器、解释器、tsp。
2. **拆箱标量值模型**：int/float/bool/小标量直接值，不做 10 表 push/寻址；容器/字符串
   仍盒装。
3. **优化树遍历直驱**（JIT 冷/兜底路径）：`exec_stmt` 直分派 switch + 解码-执行直驱，
   作为未进入 JIT 输入的高效基线。
4. **分级 JIT 即时编译**（主路径）：AST → LLVM IR（复用 irgen/llvmgen）→ native
   （clang 子进程）→ 动态加载；函数/脚本级 JIT 缓存；分级策略决定何时 JIT（热/阈值可配）。

---

## 四、详细设计

### 4.1 字符串/容器原语优先（p.9.17.1）

- 攻坚运行期 string 原语：`str_char` 高开销（本机 ~360µs）与逐码点 O(n²)、`+`/拼接分配。
  改为字节级缓存/增量长度/RoW 共享等；容器操作（表/映射复制/遍历）同步优化。
- 收益面：编译器自身（parser/semantic 逐字节遍历）、解释器、tsp（p.9.16 同受益），
  属全局性能基建，独立可验收。

#### 4.1.1 勘察增补（2026-09-25，p.9.17.1 执行记录）

*EN: Survey addendum for p.9.17.1 (2026-09-25 execution record).*

**str_char 缓存（实测基线，铁律 3 事实验证）**：`str_char` 编译路径为
O(n²) 步进（100K 码点 char-wise 遍历 >120s 被 120s 命令上限截断；10K ≈ <1s；
interp 路径 10K ≈ 1s，~100µs/char——设计文档旧数字 ~360µs 与 interp 路径量级
吻合）。单槽 (ptr,len) 键缓存方案 **2026-09-24 已验证可行**（@tie_sc_* 手写
LLVM helper：phi 自环重建循环 + legacy 兜底；50K 遍历 9.2s→0.27s），遗留两缺陷
（phi 退出值差一 / 交替串单槽失效）后回滚——全部设计/坑/出路存 tiec
`docs/p9216-findings.md` §10/§11，重上时勿改架构。基准脚本就绪：
`_tiec_verify/bench_50k.tie` / `bench_mb.tie` / `bench_tsh3.tie`。

*EN: str_char compile path is O(n²) (100K codepoints >120s); the single-slot
(ptr,len)-keyed cache design was proven (50K: 9.2s→0.27s) but rolled back with
two bugs pending (phi exit off-by-one / alternating-string single-slot miss).
Full record in tiec findings §10/§11 — keep the architecture when re-landing.*

**str_sub_bytes 勘察结论（同范式适用性）**：字符串切片 `t[lo..hi]` 走
`s21_str_sub_bytes`（irgen_str_p1.tie）——字节区间 + clamp + 单次 memcpy
（SSO 分配，O(len) 一次拷贝），**无 O(n²) 问题，缓存范式不适用**。码点索引
访问只有 `str_char` 一条路；若未来出现码点区间子串需求，应复用 str_char 缓存
的码点→字节偏移表（同一 (ptr,len) 键），不另立缓存。

*EN: string slicing is byte-range with one memcpy (O(len)) — the cache scheme
does not apply; a future codepoint-range substring should reuse str_char's
offset table under the same key rather than a new cache.*

**容器按值传参 COW/移动语义（裁定：v1 维持拷贝语义，不实施）**：字符串不可变，
子串 = 拷贝（memcpy 入 SSO/malloc 块，头 {len,data}）；表切片 = 新表（拷贝非
视图）。改 COW/视图需动字符串内存布局（父指针 + 偏移或视图标记），波及 FFI
边界（全部桥按 {len,data} ptr 约定）、SSO 池布局与 free 路径
（tie_str_free_if_heap），风险/收益比差——除非剖析显示子串密集负载，否则维持
拷贝语义（文档化边界）。

*EN: v1 keeps copy semantics for by-value containers/strings; COW views would
change the string layout and ripple through FFI/SSO/free paths — poor
risk/benefit unless substring-heavy workloads show up.*

### 4.2 拆箱标量（p.9.17.2）

- 值模型拆箱：int/float/bool/trit/char 等小标量直接作为值/寄存器槽，不建节点 id，不做
  10 表 push；仅 table/map/string 等复合值仍盒装（保留 id）。
- 拆箱与 JIT 共用一套统一接口（双形态——解释器槽为拆箱值、JIT 寄存器即原生标量），
  无缝混用（对 p.9.17.4 的冷热切换是前提）。

#### 4.2.1 详细设计增补（2026-09-27 勘察；2026-09-28 已实施——第二步热路径切换落地）

*EN: Detailed design addendum for p.9.17.2 (2026-09-27 survey; implemented 2026-09-28).*

**状态：已实施（第二步）**。本节为 p.9.17.2 的实施方案（值表示选型 + 分期迁移 + 验收），
经用户审阅确认后进入实现；第二步（call_builtin 分派链 + interp 全树 Value 化）已于
2026-09-28 落地（tiec 788f2df，门禁与性能分账见 tiec docs/p9216-findings.md §19），
第三步收口（value.tie 退役删除、标量池槽位清理、内存收口）待做。

*EN: Status: implemented (step 2). This section is the implementation plan for p.9.17.2;
step 2 (call_builtin dispatch + full interp-tree Value switch) landed 2026-09-28
(tiec 788f2df; gates and perf ledger in tiec docs/p9216-findings.md §19). Step 3
(value.tie removal, scalar-pool slot cleanup, memory accounting) remains.*

**一、实测基线（探针实测，交替多轮取最小）**

| 项 | 实测值 | 来源 |
| --- | --- | --- |
| 盒装：`new_int` + `int_val` 一轮 | **621 ns/次** | 探针 50 万次、交替 5 轮取最小 |
| 拆箱：`Value.Int(i)` + 解构读取一轮 | **332 ns/次** | 同上 |
| 拆箱相对盒装加速 | **1.87×** | 同上 |
| enum 传递 vs `i64` 传递（同构循环） | 164.7 ms vs 171.7 ms（2000 万次） | 无可测惩罚 |
| 解释器每值成本（含 `new_node`） | 每算术运算 +1.3 µs | `p9216-findings.md` §16.1 |

读法：**值模型本身的可优化空间约 1.9×**；解释器整体收益取决于值操作在每条指令中的
占比，须在实现前后用同一套 micro-benchmark（M2/M20/C_arith/F_call）如实对比记录。

*EN: The value model itself has ~1.9x headroom; the end-to-end gain depends on how
much of each instruction is value handling, to be measured before/after with the
same micro-benchmark set.*

**二、值表示选型（三案对比）**

* 案 A **enum 标签联合（采用）**：tie 原生 ADT，LLVM 层为静态结构体
  `{ i64 tag, i64×K 槽 }`，**零堆分配、零运行时开销**。探针实测：构造 + 解构一轮
  332 ns（vs 盒装 621 ns）；enum 循环与 `i64` 循环耗时在噪声内相等（传递无惩罚，
  LLVM 把静态结构体拆解到寄存器）。语言原生 ⇒ 无手工位运算，可读、可调试、可被
  编译器的优化档位正常优化。
* 案 B **NaN-boxing（不采用）**：单 `i64` 位编码，传递最省（8 字节）、与 JIT 寄存器
  最贴合。否决理由：enum 方案实测已无传递惩罚，省下的字节换不来可测收益；而代价是
  手工位运算 + `f64` NaN 空间处理（NaN 载荷/`-0.0` 语义须逐项论证）+ 调试可读性下降，
  且 tie 无原生 union/位域，需大量 `bitcast` 手搓——风险与收益不成比例。
* 案 C **保留盒装 + 减表/池化（不采用）**：爆炸半径最小，但仍是「id + 表寻址」，
  未触及根因，收益上限远低于案 A。

*EN: Case A (enum tagged union) is adopted — native ADT, zero allocation, measured
1.87x over boxing and no measurable passing penalty. Case B (NaN-boxing) is
rejected: the passing saving is not measurable against enum, while hand-rolled bit
encoding of f64 raises risk for no gain. Case C (keep boxing, trim tables) does not
address the root cause.*

**三、值表示**

```
enum Value {
    Nil                        // 未初始化 / 空
    Int(i64)
    Float(f64)                 // 原生 f64 载荷
    Bool(bool)
    Trit(i64)
    Char(i64)
    Range(i64, i64)
    Str(i64)                   // 字符串槽 id（复合值，仍盒装）
    Table(i64)                 // 表节点 id
    Map(i64)
    Code(i64)                  // 宏/准引用文本槽 id
}
```

* **标量内联、复合值留 id** 是本设计的核心折中：`int/float/bool/trit/char/range`
  直接内联（消灭每值 7 次 `table_push` 与后续表寻址）；`string/table/map/code` 保持
  「id 指向既有池」——变长或需 SSO/堆的值无法内联，且 §4.1.1 已裁定维持拷贝语义。
  由此容器路径几乎不动，爆炸半径被限制在标量侧。
* 槽数 K = 2（`Range` 两个载荷）⇒ 每个值 24 字节；实测传递无惩罚。
* `Float` 载荷直接写 `f64`（由编译器处理槽承载与转换），无需手工 `bitcast`。
* 值的 `==` 比较：enum 比较不支持（语言一期限制），故比较一律经解构后按载荷比较——
  与现有 `type_of` + 分支的语义一一对应，行为不变。

*EN: Scalars are inlined, composite values keep their slot id — the central
trade-off. It confines the change to the scalar side while container paths stay as
they are (copy semantics per §4.1.1). K = 2, so a value is 24 bytes.*

**四、分期迁移（禁止大爆炸式改动）**

* **第一步 · 基建（可独立验收）**：引入 `Value` enum + 装箱/拆箱层；标量走 enum、
  复合值继续用既有池，**双形态共存**；对外 API（`new_int`/`int_val`/`type_of`…）
  签名暂不变，内部表示切换。此步不改任何调用点，独立跑门禁。

  > **执行状态（2026-09-27）——阻塞已解除，基建门禁通过**：`vval.tie`（690 行，
  > enum 值模型 + 复合值槽）已写好并可单独编译为库，`table<Value>` 存取经探针
  > 验证可用；曾**受阻于「enum case 载荷绑定在被导入的文件里一律失效」**
  > （`error[E00488]`），根因为 import AST 合并时 `append_ast_mem` /
  > `sstate.append_ast` 把 N_CASE_BIND 的裸名池 id 子节点当节点 id `+base`
  > 平移（详见 `tiec/docs/p9216-findings.md` §18.2）。**已修复**（tiec
  > `b567548`，不动点 `2fc7e125` → `6d7664af` 升格；回归 158/8/2 FAIL 集合
  > 同基线；`tests/interp` 11 套件逐字节一致）：`vval.tie` 作为被导入库编译
  > 通过，parity 门禁 **PARITY OK（74 用例逐字节一致）**。第一步「基建 +
  > 双形态共存」的验收标准（本设计 §验收）已满足；下一步为第二步热路径切换。
  > 探针修正版归档 `_tiec_verify/p917_wip/p917_parity_fixed.tie`
  > （跨模块全局按裸名访问，见 findings §18.4）。
  > 同期修掉一个**前置**编译器缺陷（`table<Enum>/table<Struct>` 元素赋值发射非法
  > `add`，tiec 4be6977）：不修它连 `table<Value>` 的元素写都编译不过。

  > 注：本节原文写「对外 API 签名暂不变，内部表示切换」——实测**类型上不可行**：
  > 一个表达式的值类型只能是一种，`i64`（盒装 id）与 `Value`（拆箱）无法在同一
  > 接口下共存。故第一步的实体应是「新增 `Value` 版实现 + parity 门禁」（扩张），
  > 第二步才是原子切换调用点（收缩）；签名不变只在第一步内成立。

* **第二步 · 热路径切换**：`gen_expr`/`exec_stmt`/环境槽/`ivalue` 公共 API 改传
  `Value`；错误文本仍只在冷分支还原。
* **第三步 · 清理与内存收口**：标量不再入池后，淘汰仅服务标量的平行表槽位
  （`v_ivals`/`v_fvals` 的标量用途等），会话内存随之下降；补值池/常量池复用勘察结论。

每步一次提交、独立跑全套门禁；任一步门禁失败即回退该步（不叠加）。

*EN: Three steps (infrastructure with dual-form coexistence / hot-path switch /
cleanup), each committed and gated on its own; no big-bang rewrite.*

**五、低内存与内存治理（兼任 p.9.18.1）**

* 标量不再入池 ⇒ 池只装复合值，**会话内存只增不减**问题的主要来源（标量）被消除；
  池增长曲线应与「脚本中复合值数量」而非「求值步数」相关。
* 值池/常量池复用：小整数是否预置缓存，待勘察真实脚本的整数分布后再定（不预设结论）。
* 面 A 附加交付（嵌入裁剪形态 + 内存峰值/稳态报告）随 p.9.18.5 一并给出。

**六、与 JIT 的接口统一（衔接 p.9.17.4）**

* 双形态落点：解释器槽持 `Value`（标量内联 + 复合 id），JIT 寄存器持原生标量。
* 边界转换：JIT 出口把原生标量包成 `Value.Int`/`Value.Float`，入口反向；复合值一律
  传 id——该边界是冷热路径热切换的前提（§4.2 原文）。
* 本设计不引入任何 trm 依赖（保持 §4.2 与 trm 字节码路线的边界）。

**七、验收**

* **性能**：micro-benchmark 前/后全套（M2/M20/C_arith/F_call + 每值成本），
  对照本节的 1.87× 上限如实记录实际达成。
* **正确性（硬门禁）**：REPL/DAP/脚本行为**逐字节恒等**——别名/段视图语料 +
  解释器行为套件 + tshell 冒烟，新旧逐字节比对；错误消息文本逐字节不变。
* **回归**：`regress-s21` 集合与全量日志同基线；三阶自举不动点重录 + 升格。
* **内存**：峰值/稳态对比报告（面 A 附加交付）。

**八、边界（不做）**

* 不改 tie 语义与诊断文本；不引入 trm 依赖；容器不做 COW/移动语义（§4.1.1 裁定）；
  不改 REPL/DAP 对外签名。

**九、风险与对策**

* 第二步是结构性改动（值表示切换，`ivalue` API 调用点约三百处）——用第一步的
  「双形态共存」把它切成可回退的小步；类型系统在编译期兜住大多数漏改（`i64` 与
  `Value` 不可混用）。
* 若实现中发现 enum 载荷在真实负载下出现传递惩罚（探针为理想场景），退路是：把
  `Value` 改为 `{tag, i64 payload}` 的手工编码（案 B 的受限形式），接口层不变。

**十、本次勘察附记（操作台事实，供执行者省时间）**

* `language.md` §3.8 的「当前限制（一期）」段**已过时**：其称 `f32/f64`、`string`、
  `struct`、`table/map` payload 不支持，而 p.8.1.7 已放开 `f64`/`table`/`map`；
  本次探针实测 `f64`/`string` payload 构造与解构均正常。该段须随本档勘误
  （当前白名单仍不含 `struct`/嵌套 `enum`，见 `scollect_port_q1.tie` 的白名单注释）。
* 探针单元标记：`type tie<logic>` 产出可执行文件，`type tie<class>` 产出静态库
  （`!<arch>`）——写独立探针须用 `logic`，否则拿到的是库而非可执行文件。
* `value.tie` 隐式依赖 interner（`text_less` 用 `interner.lookup`）却未自行 import，
  单独 import 它的探针须同时 import `compiler/lib/interner.tie`。

*EN: Addendum facts: the "phase-one limits" paragraph in language.md §3.8 is stale
(f64/string payloads work as of p.8.1.7 — verified by probe); `type tie<logic>`
yields an executable while `tie<class>` yields a static library; `value.tie` needs
an explicit interner import in standalone probes.*

**探针（可复现，均以 `--no-warn --no-cache` 编译）**：

| 探针 | 用途 | 运行位置 |
| --- | --- | --- |
| `_tiec_verify/p917_probe_enumcap.tie` | enum 载荷类型能力（`f64`/`string` 构造与解构） | `_tiec_verify` 下 |
| `_tiec_verify/p917_probe_i64loop.tie` / `p917_probe_enumloop.tie` | `i64` 与 enum 传递成本对照（2000 万次） | `_tiec_verify` 下 |
| `tiec/_p917_box.tie` / `tiec/_p917_unbox.tie` | 盒装（`new_int`+`int_val`）与拆箱（enum 构造+解构）核心对照（50 万次） | tiec 工程根下（含 import，须在根内编译） |

计时须**交替多轮取最小**（本轮实测教训：串行单轮对照会给出反向结论，见
`tiec/docs/p9216-findings.md` §17.5）。

*EN: Probes are listed above with their run location; time them with interleaved
rounds and take the minimum (single serial passes gave an inverted conclusion —
see findings §17.5).*

### 4.3 优化树遍历直驱（p.9.17.3，JIT 冷路径基线）

- `exec_stmt`/`gen_expr` 改为**直分派表**（switch/间接跳转），消除长 if/else 链逐次比较；
  解码-执行直驱，减少重复字段/表寻址。
- 与 4.2 拆箱配合：标量运算不再 alloc；容器路径保留。
- 服务未达 JIT 阈值的小输入/REPL 单行，保证低延迟。

### 4.4 分级 JIT 即时编译（p.9.17.4，主路径）

- **编译器管线复用**：解释单元（函数/脚本）首次达热即提交 JIT——跑 irgen+llvmgen 产出
  LLVM IR，经 clang 子进程编译为临时 native 目标，动态加载（Windows `LoadLibrary`
  / 平台对等），经 `call_indirect` 调用（irgen 已支持函数值间接调用与 dllexport 导出）。
- **JIT 编译缓存**：函数级产物缓存，键=AST 指纹（复用/挂钩 p.9.15 内容寻址 tsha1r 与
  编译缓存层），二次命中零重编；与 p.9.16 的 AST 生命周期衔接（JIT 后无需保留整树）。
- **分级策略**：冷/热判定（调用计数/使用频次阈值）驱动——热则 JIT、冷则 4.3 走解释器；
  阈值与开关**可配置**（引擎不锁）。小输入不 JIT（避免 clang 子进程等待压倒执行时间）。
- **确定性**：JIT 与解释器对同一输入产物/结果**逐字节恒等**为硬门禁（可关，默认开）。

### 4.5 配置与架构协同

| 项 | 取值 | 说明 |
|----|------|------|
| `interp.jit` | 新增默认 `on` | JIT 开关 |
| `interp.jit_threshold` | 新增 | 热路径触发阈值（调用/频次） |
| `interp.unbox` | 新增默认 `on` | 拆箱标量开关 |
| string 原语 | tiec 运行期 | 全局原语优化（受益三方） |
| JIT 缓存 | 复用 p.9.15 | 内容寻址指纹 + 编译缓存 |
| AST 生命周期 | 衔接 p.9.16 | JIT 后释放前端静态表 |

---

## 五、排号与分期

**档位：p.9.17 解释器性能（JIT + 拆箱 + 字符串原语优先）**

- p.9.17.1 **运行期字符串/容器原语优化**：`str_char`/逐码点遍历/拼接分配 + 容器复制遍历
  优化；全局受益（编译器/解释器/tsp）。
- p.9.17.2 **解释器拆箱标量**：int/float/bool/trit/char 拆箱，消灭 per-value 10 表 push；
  与 JIT 统一接口。
- p.9.17.3 **优化树遍历直驱**：`exec_stmt`/`gen_expr` 直分派 switch + 解码直驱，作 JIT
  冷路径基线。
- p.9.17.4 **分级 JIT 即时编译**：AST → LLVM IR → native 动态加载 + 函数级 JIT 缓存 +
  冷热阈值；复用/挂钩 p.9.15 编译缓存与 p.9.16 AST 生命周期。
- p.9.17.5 **验收与回归**：性能基准报告（树遍历 vs 解释器优化 vs JIT）+ 正确性探针
  （REPL/DAP/脚本逐个等价 + JIT/解释器逐字节恒等门禁）+ 回归不劣化 + 脚本一律 `.tsh.tie`。

> 分期顺序原则：先全局基建（.1 原语）→ 值模型（.2 拆箱）→ 冷路径基线（.3 直驱）→ 主路径
> （.4 JIT）→ 总验收（.5）。依赖 p.9.15 编译缓存与 p.9.16 AST 生命周期已就位；与前两档
> 无前置冲突、可并线。

---

## 六、验收度量

- **主路径**：热循环/密集脚本 JIT 后耗时相对优化树遍历大幅下降（基准对比报告）。
- **交互**：REPL 小输入仍低延迟（JIT 阈值避免小输入走 clang 子进程）。
- **正确性**：JIT 与解释器对同输入结果逐字节恒等（硬门禁）；REPL/DAP/脚本功能等价。
- **全局**：字符串原语优化后编译器构建、tsp 分析（p.9.16）同受益。
- **回归**：tiec 全套 s21/diagcodes/m5 不劣化；探针/冒烟全绿；脚本 `.tsh.tie`。

---

## 七、兼容性与迁移

- JIT/拆箱为新增路径，默认值保守（jit on、unbox on、阈值合理），无参行为不劣化现有解释器
  功能（结果等价）。若 JIT 门禁失败自动回退解释器路径。
- 既 eval/eval_script/eval_call 对外签名不变；内部按分级策略选路径。
- 与 trm 字节码运行时保持边界（本期不统一），不引入 trm 依赖。

---

*本设计为解释器性能优化的权威执行依据（tie-main 侧），配套 tiec 编译器后端 JIT 衔接与
运行期字符串原语；随 p.9.17 解释器性能档执行。*