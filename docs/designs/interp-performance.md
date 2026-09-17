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

### 4.2 拆箱标量（p.9.17.2）

- 值模型拆箱：int/float/bool/trit/char 等小标量直接作为值/寄存器槽，不建节点 id，不做
  10 表 push；仅 table/map/string 等复合值仍盒装（保留 id）。
- 拆箱与 JIT 共用一套统一接口（双形态——解释器槽为拆箱值、JIT 寄存器即原生标量），
  无缝混用（对 p.9.17.4 的冷热切换是前提）。

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