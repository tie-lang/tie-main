# tiec 模块化与库化设计 —— 解耦 · 组件化 · 阶段无关 · 消灭大文件

*EN: tiec modularization & library-ization design — decoupling, componentization, stage-agnostic APIs, eliminating oversized files*

**日期** / Date: 2026-09-22 · **类型** / Type: 设计（定稿；D1/D2 已拍板 2026-09-22，D3/D4 按推荐执行）
**依据** / Basis: 用户指令「tiec 彻底解耦、模块化、库化、与阶段无关、封装为 n 个方法、彻底消灭大文件」
**关联** / Related: ROAD p.9.20 双轴优化器（passes 组件已是本设计的首个受益者）· p.9.15 编译缓存（层 II 增量编译的地基）· p.9.0 自举纪律（每步不动点验证）

---

## 1. 现状勘察 / Current State

### 1.1 规模分布 / Size distribution

| 指标 | 数值 |
|---|---|
| .tie 源文件总数 | 124 个 / 98,777 行 |
| 超 800 行文件 | 36 个，合计 73,712 行（**75%**） |
| 超 1000 行文件 | 31 个 |
| 最大文件 | `backend/irgen_expr.tie` 10,844 行 |

Top 大文件：irgen_expr 10844 / proto/semantic 3802 / sinfer 3361 / irgen_stmt 3331 / proto/parser 2876 / scheck 2873 / irgen_str 2650 / diagcode_cat.gen 2583 / **driver 2529** / interp 2446 / pstmt_top 2443 / irgen_agg 2292 / pexpr 2135 / irgen_rt 2103。

### 1.2 关键病灶 / Key pathologies

1. **巨型函数**：`irgen_expr.tie` 全文 10,844 行**只有 4 个函数**——`builtin_expr` 一个函数 2,688 行（按内置名 if-else 串行分发，38+ 分支）。文件大是因为**函数大**，拆文件必须先拆函数。
2. **阶段耦合**：`backend/irgen_*` 直接读写 frontend 的全局（`node_types`/`s_tags`/`sstate`/`scope_*`）——AST→IR 生成层天然需要 AST，但当前是**裸全局共享**而非显式传递。
3. **driver 巨壳**：CLI 解析、config 加载、kpass 编译管线、缓存、诊断输出全部塞在 driver.tie 一个文件。
4. **可见性靠约定**：`pub` 是声明性的（文本内联后一切同作用域），跨组件误用无防护；全局冲突靠 `err_` 前缀等手工约定。

### 1.3 语言级约束（现状能力边界）/ Language-level constraints

tie 当前的模块机制是**文本内联**（`mexpand`：import 展开先于宏展开，主文件 + 全部导入文件顶层语句并集）：

| 机制 | 现状 | 对模块化的含义 |
|---|---|---|
| `import` | 文本内联，同编译单元 | 唯一的模块边界 = 同名 namespace 跨文件闭合并集 |
| `namespace` | 函数/类/嵌套 ns；**全局 var 必须在顶层** | 组件的函数隔离可用；组件状态不能进 ns |
| `pub` | 声明性，无强制 | 可见性无防护 |
| `const` | **跨文件不可见** | 跨文件共享常量需本地重定义（ir.tie 已注释此坑） |
| 函数 | 原子，不可跨文件部分拆 | 巨型函数只能「提子函数」拆解 |

**已验证可行的范式**：「同 namespace 跨文件」拆分（irgen 系列已用：S1-S4 拆出 irgen_builder/arith/lit/expr/stmt/agg/rt/str，主文件留全局 var 与 import 树）。

---

## 2. 目标与非目标 / Goals & Non-goals

**目标**：
1. **组件化**：编译器 = core 库 + 阶段组件 + 薄壳 driver；组件间仅经显式 API 通信。
2. **库化**：core 组件（ir/types/interner/diagcode/columnar）不感知任何调用者，独立可测可复用。
3. **阶段无关**：middle 的 pass 管线不感知 frontend/backend；组件 = 「输入 → 输出」纯能力单元，调用顺序由 driver 编排。
4. **API 面封装**：每组件一份显式方法清单（`pub` 函数全集即契约），新增能力必须扩 API 而非绕过。
5. **消灭大文件**：单文件 ≤ **800 行**（生成文件 `diagcode_cat.gen` 除外）；单函数 ≤ **300 行**。

**非目标**：不改编译语义与产物（不动点基线变更仅在明确标注的步骤发生）；一步到位（本设计分两期，见 §5）。

---

## 3. 两层方案 / Two-layer approach

### 层 I —— 组织重构（tiec 内部，不动语言）

维持文本内联机制，用「同 namespace 跨文件」范式 + 依赖方向纪律完成拆分。**全部收益立即可得，风险仅在于拆分过程的自举验证**。

#### I1 方法分类的库架构（2026-09-22 用户拍板：不用 frontend/backend 阶段桶）

**架构原则变更**：模块按**方法/能力域**分类，每库 = 一组方法（pub API）+ 自检 + 独立发行能力；**不设 frontend/backend 阶段桶**。库之间是「使用」关系（调用图），不是「流水线阶段」的先后关系——编译管线只是 driver 对方法库的一个编排序列，换一条编排（如解释器路径）不要求任何库移动位置。

```
tie.interner   字符串池            ← 零依赖（基础方法库）
tie.bytes      字节缓冲            ← 零依赖
tie.columnar   列式存储            ← 零依赖
tie.diag       诊断码 + 渲染       ← 零依赖
tie.types      类型系统            ← interner
tie.ir         tie-IR 列式 + ir_meta + opcode 表 ← interner/columnar/types
tie.lex        词法分析            ← interner/diag
tie.ast        AST 数据结构        ← interner
tie.parse      语法分析            ← lex/ast/interner/diag
tie.sema       语义分析            ← ast/types/diag/interner
tie.irgen      AST→IR 转换         ← ast/ir/sema 的注解（显式交接物）
tie.llvmgen    IR→LLVM 文本        ← ir（不感知 ast/sema）
tie.interp     解释器              ← ir
tie.passes     中端 pass 管道      ← ir（阶段无关示范组件）
tie.tieir      IR 序列化           ← ir
tie.config     构建配置            ← 零依赖
tiec（driver） 纯编排薄壳          ← 全部，唯一流程知识汇聚点
```

**关键显式化：sema → irgen 的交接物**。当前 `irgen_*` 裸读 sema 的全局（sstate/node_types/scope_*）——方法分类后这是**库间隐式耦合**，必须收敛为一个显式数据契约（`sema` 产出的「注解 AST」结构：节点类型表/符号表快照/作用域信息），irgen 只消费该契约。这是本次架构变更中**唯一有设计难度**的点，也是解耦收益最大的点。

**库的资格**（四条，缺一不可）：①显式 pub API 面（方法清单即契约）；②独立自检（`<lib>_test.tie`，无 driver 可跑）；③独立发行（L3/L4 模块系统就绪后即可 `pkg publish`）；④依赖单向（deps-check 门禁，禁止环）。

违规检查脚本化（`scripts/deps-check.tsh.tie`：解析 import vs 库依赖矩阵，CI 门禁）。

#### I1a 门禁实测记录（2026-09-22，p.9.21.3 收尾）

门禁初始报「10 条越界边 / 7 环节点 / 18 条待修记录」。逐条核实后分三类：

**① 分类缺陷（非真实越界，已修）**

* `_pN`/`_qN` 分片未继承主文件库归属，落到目录级泛化规则上——`middle/types_q1.tie` 被判成 ir（虚报 types → ir），`frontend/stype_p1.tie` 被判成 sema（虚报 types → sema）。已为主文件前缀补规则。
* `compiler/driver/*.tie`、`compiler/config_p*.tie` 未纳入矩阵（门禁按「未纳入矩阵」报错）。已归 driver / config。
* `frontend/stype.tie` 按文件名被判成 `tie.types`。实为**语义层**的 AST→类型 id 映射器，属 frontend `s*` 家族，已归 sema；`tie.types` 仅指 `middle/types.tie` 的类型 id 编码。
* `frontend/error_driver.tie` 按 `error` 前缀被判成 diag。实为自带 `main` 的错误 golden 语料编排入口，已归 driver。

**② 冗余 import（不改变耦合，已删）**

* `frontend/stype.tie` 经 `middle/data.tie` 只为「传递可达 types.tie」，未使用 data 的任何符号。改为直接 import types.tie 后，`middle/data.tie` 退出 import 树（其 API 已无调用方，列为孤儿待清理）。
* `backend/irgen.tie` 反向 import `llvmgen.tie` 仅为一处 `llvmgen.set_linux` 调用。已把装配上移到 driver 入口（`driver/pipeline.tie` 在 `irgen.set_target` 后注入同一判据），语义不变。
* `trm/trm_loader.tie → tieir_ser.tie`：加载器读 `.tieir` 模块 ABI 是该后端自身的输入契约，判定为**合法正向依赖**，矩阵显式放行（tieir 不并入 ir 库）。

**③ 待收口：前端求值环（parse ↔ sema ↔ interp，5 条边）**

| 边 | 实际形态 |
|---|---|
| sema → parse | `check_impl` 内做 import 展开（`expand_one_import`/`expand_imports` → lexer+parser）与宏展开（`mexpand.expand_sstate`） |
| interp → parse | 解释器执行源码/code 值：`parser.parse` / `parser.parse_src` |
| parse → interp | `mexpand` 借解释器做编译期求值（宏执行） |
| interp → sema | 解释器读写 AST：`sstate.load_ast` / `parse_dec` / `slot_off`（**仅 3 个符号**） |
| interp → types | 仅 `TK_TRIT` 一个关键字常量 |

**结论（本条为设计现状，非缺陷掩盖）**：这 5 条边在文本内联机制下不可用「搬 import」消除，且**不以 p.9.21 现状为可关闭目标**——它们的关闭条件在层 II：

1. `sema → parse`：需要把「import 展开 + 宏展开」从 `check_impl` 内搬到**独立编排模块**（依赖 parse + sema 状态），使 `sema.check_ast` 只消费已展开的 AST。属结构决策，与 L3（import 语义升级）同步最省工。
2. `parse → interp`：宏展开需要编译期求值器。设计要求的「公共编译期求值契约」在无一等函数引用时无法表达（见 §层 II L5）；L5 落地或 L3 命名空间绑定后按调用方注入（A5b `&func` 起步）最省工。
3. `interp → parse/sema`：解释器当前执行 **AST**（非 tieir），且 code 值是**源码文本协议**（`interp_code.tie` 生成源码 → 解析执行）。要达成设计写的「interp ← ir」，须把 code 值与解释目标改为 tieir——属 L4 模块 ABI 的同源工作。`interp → types` 同时随 `interp` 下放 `ext/interp` 一并消解（关键字常量由调用方注入）。

因此 p.9.21 G3 的判绿目标为：**①② 类清零（已完成，10 → 5 条边）**；③ 类作为**层 II 的输入约束**跟踪，不在层 I 阶段强行放宽矩阵——放宽会让门禁失去意义，强行关闭则须先完成 L3/L4/L5。

#### I1b 下放判定：哪些方法库进入 std/ext/rdu/sys（2026-09-22 补充）

**内置库现状性能审计**（实测，`~/.tiec-lib/tlib`，l2 档）：

| 证据 | 数据 |
|---|---|
| `coll.kmp_find` **正确性** | 20 万字符文本查找存在的串返回「未找到」（手写同算法找到）——库实现存在边界 bug |
| `coll.heap_push` 抽象成本 | 10 万次 push：库版 9ms vs 裸 `table_push` 3ms（3×，堆上滤合理但可优化） |
| 静态扫描 | 158 个文件含拼接表达式；`ext/nn.tie` 密度最高（118 处/722 行，且热循环内大量 `as_f64` 装箱）；`std/tsha1_w48.tie` 单文件 19,567 行（疑为展开生成物） |
| 抽查反模式 | 多数为整数自增/浮点累加（无害），但字符串拼接热路径与装箱转换在 httpc/json5/collection 等常用库普遍存在 |

**下放判定表**（16 个方法库 → std/ext/rdu/sys）：

| 库 | 判定 | 去向 | 注记 |
|---|---|---|---|
| tie.interner | **下放 std** | `std/interner` | 纯通用数据结构，零编译器耦合 |
| tie.bytes | 已在 std | （确认统一） | tiec 内 lib/bytes 为副本，删除改引用 |
| tie.columnar | **下放 std** | `std/columnar` | 通用列式结构 |
| tie.diag（渲染部分） | **下放 std** | `std/diagfmt` | 通用诊断渲染框架；**码表注册表留 tiec**（编译器私有） |
| tie.ast | **下放 std** | `std/ast` | tie 语法的官方 AST = 语言规范资产（linter/formatter/IDE 皆需） |
| tie.lex / tie.parse / tie.sema | **下放 std** | `std/lex` `std/parse` `std/sema` | 官方解析器/语义器 = 语言规范实现，tiec 改为消费 std（自举自洽：用 std 解析 tie） |
| tie.ir / tie.tieir | **下放 std** | `std/ir` `std/tieir` | **tie-IR 是语言公共资产**（trm 引擎/dbg/pkg 工具皆消费，非 tiec 私有） |
| tie.interp | **下放 ext** | `ext/interp` | 解释器为可选组件（tshell/REPL 复用） |
| tie.types | 留 tiec | — | 编译器类型 ID 编码，等语言静态类型注解（L 系列远期）成熟再评估 |
| tie.irgen | 留 tiec | — | AST→IR 是 tiec 本职 |
| tie.llvmgen | 留 tiec | — | 后端专属 |
| tie.passes | 留 tiec | — | 优化 pass 属编译策略；管道**框架**若通用再评估 |
| tie.config | **下放 ext** | `ext/config` | config.data.tie 格式解析，pkg/构建工具复用 |

**下放 × 性能联动（硬规则）**：下放 = 高质量实现随行，禁止把烂实现一放了之——
1. 下放库必须带基准（`<lib>_bench.tie`）与性能预算，不达标的先修再放；
2. 热路径原语（如 kmp/regex/编码）可评估「编译器内建/内联」路线（irgen_regex 的编译期解析+运行时 VM 即先例）——性能关键处语言内建，通用实现进 std；
3. tiec 内部经过 p.9.14/9.19 优化的实现（字符串池 O(1)、sb_scan）反哺内置库重写。

**正确性优先**：`coll.kmp_find` 边界 bug 为审计发现的第一例，下放前内置库需一轮正确性回归（现有 tests/language/std_* 为起点补全）。

#### I2 大文件拆解（按病灶定策略）

| 病灶 | 策略 |
|---|---|
| **巨型分发函数**（builtin_expr 2688 行） | 两步：①每分支提为独立函数 `bi_<name>(id)`（机械，语义等价）；②`builtin_expr` 变纯调度器（名字 → 处理函数 id 表 + 单点分发），按内置域拆文件：`expr_builtin_mem/agg/arith/str/rt/...` |
| **巨壳 driver**（2529 行） | 拆 `driver/`：`cli_args`（parse_args/usage）/`cfg_load`（config 合并）/`pipeline`（kpass 序列）/`cache_drv`（缓存键/产物）/`diag_out`（渲染输出）——driver.tie 留 main 与编排 ≤300 行 |
| **语言层巨文件**（sinfer 3361/scheck 2873 等） | 同 namespace 跨文件按职责拆（sinfer_expr/sinfer_ret…已有先例），每拆步 regress 全绿 |
| **生成文件**（diagcode_cat.gen 2583） | 生成物不拆，豁免上限 |

#### I3 API 面封装（n 个方法）

每组件一份 `README.tie`（或注释头）列出 **pub 方法全集** = 组件契约；非 pub 函数约定 ns 内私有。样例（已成型组件）：

- `ir` 库（17 方法）：`new_module / new_func / new_block / new_inst / add_operand / get_value / ins_op / ins_ty / ins_val / ins_opnd / ins_opnd_kind / ins_ops_cnt / set_opnd / rewrite_to_const / compact_dead / op_count / op_name`
- `passes` 库（2 方法 + 常量）：`pipeline_ver / run`（+ `set_tail_enable` 属 llvmgen）
- `llvmgen`（3 方法）：`emit / set_tail_enable / dump`（规划）

组件 API 变更 = 契约变更，须同步组件 README 与 ROAD。

### 层 II —— 语言模块系统（tie 增强，tiec dogfood）

#### 层 II 深化（2026-09-22 补充）：语言层面优化五项

**核心洞察**：限定名调用已存在且工作（`passes.run`/`ir.ins_opnd`）——模块化的调用机制是现成的，缺的是四件事：**强制边界、常量可见性、编译单元、表驱动能力**。语言优化是四个增量特性 + 一个可选补齐，不是推倒重来。

| 项 | 语义 | tiec 落点 | 改动量 |
|---|---|---|---|
| **L1 可见性梯度** | 开放度参数化（见下方选项菜单） | sstate（符号可见级标记）→ sinfer（校验）→ diagcode | 小 |
| **L2 常量可见性统一** | 常量与函数同规则（见选项菜单） | sstate + consteval | 小 |
| **L3 import 语义升级** | 双轨：内联（兼容）+ 命名空间绑定（opt-in）；导入语法三选项 | mexpand + parser + sstate | 中 |
| **L4 模块即编译单元** | ABI 基于 tieir（后端无关）；缓存深度两档可选 | tieir_ser + driver/cache | 大 |
| **L5 函数引用（可选）** | 三档：一等函数值 / 编译期引用常量 / 宏生成 | mexpand 或 sinfer | 中 |

**L1 可见性梯度（选项菜单，用户自选）**：

| 档 | 语义 | 适用场景 |
|---|---|---|
| A1a 全开放（默认档=现状） | 一切符号跨 ns 可见，`priv` 仅文档性 | 脚本/原型/单人项目 |
| A1b ns 级私有 | ns 内非 pub 跨 ns 不可见（原 L1 设计） | 组件化项目（tiec 自身） |
| A1c 包级 | 同目录/同包可见，跨包需 pub | 多人协作的中型库 |
| A1d 全私有 + 显式导出 | 默认不可见，`pub` 逐个导出 | 严格 API 契约的发行库 |

档位声明：编译器 flag（`--visibility=a1b`）或文件级声明（`tie:visibility=ns`）皆可；**默认 A1a，老代码零影响**。梯度实现共用一套符号可见级标记（sstate 存 0-3 级），检查逻辑统一。

**L2 常量可见性（选项菜单）**：

| 档 | 语义 |
|---|---|
| A2a 现状+pub 例外 | 默认跨文件不可见，`pub const` 显式可见（原设计） |
| A2b 与函数同规则 | 常量即不可变绑定，可见性完全跟随 L1 梯度（推荐——无特例，规则统一） |
| A2c ns 常量 | ns 内 const 经限定名访问（与 L3 联动最干净） |

**L3 import 升级（选项菜单）**：

| 档 | 语义 |
|---|---|
| 启用方式 | 文件头 `module <name>` 显式 opt-in（推荐）vs 目录约定 vs 编译器 flag |
| 导入语法 | `import ns.path`（限定名，推荐最小集）／`from ns import item`（符号导入）／`import ns as alias`（别名）——可分批提供 |
| 未导入符号 | A3-strict：不可见／A3-lint：可见但警告（迁移缓冲） |

**L4 缓存深度（选项菜单）**：A4a 模块 ABI = tieir 分发单元（后端无关，提速最大）；A4b 源码级哈希缓存（简单）；两档共存（开发 A4b / 发行 A4a）。

**L5 函数引用（选项菜单）**：A5a 一等函数值（最通用，改动最大）；A5b 编译期引用常量 `&func`（仅表初始化/直接调用，够用且成本可控——推荐起步）；A5c 宏生成（mexpand 承载，不改语言核心）。

#### 层 II 通用性总原则（2026-09-22 用户约束：不影响通用性、加强通用性、给可选菜单）

1. **opt-in 原则**：所有新语义对既有代码零影响——默认行为不变，新能力显式选择启用；
2. **脚本友好**：无 namespace 的顶层脚本/小工具场景零迁移成本（可见性等特性不触及顶层符号）；
3. **正交原则**：L1-L5 相互独立，可单独采用、单独回退；
4. **后端无关**：模块 ABI 一律基于 tieir 序列化，不绑 LLVM/任何特定后端；
5. **可选项菜单**：每个特性提供至少两档语义（宽松/严格），由编译器 flag 或文件级声明选择，默认档 = 最接近现状的一档；
6. **梯度可见性**：可见性不是开/关二元，而是开放度参数（全开放 / 包级 / ns 级 / 全私有），用户按项目性质自选。

**L1 迁移策略（关键）**：先诊断后强制——违例先发警告（复用 tiec W##### 体系，dogfood），全仓清零后翻转为 E#####。诊断阶段同时完成 tiec 全仓的「API 面普查」：每个 namespace 真正对外暴露多少方法一目了然，与层 I 拆分同步进行（一次迁移两份收益）。

#### II2 现状核实（2026-09-23，p.9.21.5 诊断步；探针 `tests/_p9215_probe/`）

设计 §1.3「const 跨文件不可见」的记述**已过时**（p.9.12.4 ns 常量落地后的现状）：

| 形态 | 现状 |
|---|---|
| 顶层 `const` 跨文件引用（同编译单元） | ✓ 可见（text-inline 合并顶层作用域） |
| ns 内 `const` 经 `ns::NAME` 跨文件引用 | ✓ 可见（以 ns::NAME 全名登记全局符号通道） |
| ns 内 `const` 经 `ns.NAME` 点号引用 | ✗ 不适用（点号形式仅函数调用） |
| `pub const` | ✗ **无法解析**——`lex_pub` 分支只分派 func/macro/import，落到 parse_fn_def 报「期望 'func'」 |

**因此 II2 的实际缺口**比原描述窄：不是「常量不可见」，而是 ①`pub const` 语法缺失（库无法把
常量纳入 pub API 面，消费者只能本地重定义 → 漂移根因）；②常量引用尚无可见性护栏（ns 常量
对跨 ns 引用全开放，等价 A1a 态）。

**落地路径（A2b：常量可见性跟随 L1 梯度）**：
1. 解析层：`lex_pub` 分支增加 `pub const` → `parse_var_decl(1)` + val bit1 = ispub
   （顶层与 ns 体两处；顶层文件 `pstmt_top.tie`、ns 体 `pstmt_top_p2.tie`）；
2. 语义层：常量登记读取 val bit1 → 写入符号 pub 位（sg_pub bit0，与函数同通道）；
3. 护栏：常量引用接入 L1 梯度（复用 check_visibility 的档位逻辑）——**先诊断后强制**：
   先以警告模式普查全仓跨 ns 非 pub 常量引用，清零后翻转为错误；
4. 同步修订 §1.3 与 ir.tie「常量跨文件不可见」的过时注释。

#### II1 现状核实（2026-09-23，p.9.21.4 诊断步）

**A1b（ns 级私有）已经作为错误强制生效**，本设计早前「pub 是声明性的（无强制）」的记述已过时：

* 落点：`sstate.check_visibility`（M2.1.7，对齐 Rust check_visibility），接在 sinfer 全部 6 处
  函数调用解析点上。规则：显式 `pub` 放行；**顶层函数**（全名无 `::`）恒放行；同命名空间或
  **子命名空间**放行；否则报错——「函数 'x::y' 是命名空间 'x' 的私有函数（默认私有，
  \`pub func\` 显式导出），不可在命名空间之外调用」。诊断码 = **E00332**（G7 diag 自检以
  目录查表实证；E00331 为「无签名」）。
* tiec 自身 dogfood 已经是 A1b 态（编译通过 = 零违例）。

**全仓 API 面普查**（`tiec/tools/visibility_survey.tie`，纯 tie 实现；按函数回溯所属命名空间统计）：
59 个命名空间、**2415 个 ns 内函数（pub 1261 / 私有 1154，48% 私有）**、141 个顶层函数（按规则豁免）。

**普查暴露的真问题**（比「缺强制」更重要）：`pub` 目前承担两种语义，被 p.9.21.3 的机械拆分进一步混淆——

1. **跨文件同 ns 链接**（机械需要：拆出文件的函数要与主文件互调）；
2. **对外 API 契约**（设计本意）。

极端样例：`driver` 58/0、`sbuiltin` 94/0、`sstate` 77/1、`irgen` 139/511——这些 `pub` 绝大多数
只是「同 ns 跨文件可见」，不是对外承诺。**因此 II1 的剩余工作不是补强制（已存在），而是把两种
语义分开**：

* 「同 ns 跨文件」应成为默认可见（L3 命名空间绑定落地后自然成立，见下）；
* 「对外 API」收敛到各库 README/注释头的**方法全集清单**（G7 已在逐库补齐）；
* 梯度档位（A1a 脚本默认 / A1c 包级 / A1d 全私有+显式导出）作为编译器 flag 落地时，
  **A1b 必须保持为现有默认**——设计原文「默认 A1a，老代码零影响」与现实相悖（现实已是 A1b），
  照搬会把现有护栏拆掉，需改为「默认 A1b；A1a 仅作为脚本/无 ns 项目的显式降档选项」。

**自举与鸡生蛋**：语言特性在 tiec 实现 → tiec 重新自举后特性可用 → tiec 源码迁移 → 不动点重录。顺序不可倒置；语言行为变化处重录基线。

**实现落点顺序**：L1 → L2 → L3 → L4（L5 独立评估，不阻塞）；L1/L2 与层 I 的 p.9.21.1-3 可并行。

层 I 的天花板由语言决定。以下按 tiec 的真实痛点驱动 tie 语言增强，**增强后由 tiec 自身 dogfood**：

| 项 | 语义 | 解决的痛点 |
|---|---|---|
| II1 强制可见性 | namespace 内非 `pub` 跨 ns 不可见（tiec 语义检查 + 违例诊断） | pub 从约定变护栏 |
| II2 `pub const` | 跨文件常量可见（进入模块契约） | 消灭「常量本地重定义」漂移（opcode 表事故的根因之一） |
| II3 模块级独立编译 + 增量 | 模块 = 编译缓存单元（联动 p.9.15）；模块 ABI 经序列化校验 | 编译时间线性化，模块边界机器可查 |
| II4 模块注册表 | 显式 `import` 图构建 + 环检测 + 版本字段 | 库化的最终形态：tiec 自身库化为 n 个可独立发行的 tie 模块 |

层 II 每项独立立项，**先在 tests 试点、再 tiec dogfood**。

---

## 4. 「与阶段无关」的验收定义 / Stage-agnostic acceptance

1. 每库不 import 依赖矩阵之外的其他库（如 `tie.llvmgen` 不出现 ast/sema 字样的引用）；
2. 每库可在无 driver 的情况下编译并通过独立自检（ir_test 模式推广：每库一个 `tie.<lib>_test.tie`）；
3. 编译管线可被外部重排（kpass 序列只是 driver 的编排数据，方法库无顺序知识）；
4. 库依赖矩阵检查脚本全绿（无环、单向）。

---

## 5. 分期 / Staging（提案 p.9.21）

| 期 | 内容 | 验收 |
|---|---|---|
| p.9.21.1 | 依赖方向契约 + `deps-check` 脚本 + driver 拆分试点（cli_args/cfg_load 先行） | regress 全绿；deps-check 全绿 |
| p.9.21.2 | irgen_expr 拆解（builtin_expr 两步拆 + 按域分文件） | 单文件 ≤800、单函数 ≤300；t2/t3 自举不动点重录 |
| p.9.21.3 | driver 全拆 + 其余 >1000 行文件批量拆（每文件一个子任务，独立提交） | 全仓 ≤800（gen 豁免） |
| p.9.21.4 | II1 强制可见性（tie 语言 + tiec 试点） | 违例诊断 + tiec dogfood 迁移 |
| p.9.21.5 | II2 pub const | 同上 |
| p.9.21.6 | II3 模块级增量编译 | 增量正确性 + 提速数据 |
| p.9.20.6 | （既有）各档性能参考报告 | 与 p.9.21.3 合并验收 |

**每期提交纪律**：一个小任务一次提交；涉及 llvmgen/irgen 的期不动点重录并标注。

---

## 6. 风险 / Risks

1. **自举不动点震荡**：拆分不改语义，但文本内联的编译单元边界变化会改产物（缓存键含源码）——每步重录不动点基线（已有配方：瘦入口 ~3min）。
2. **同作用域重名**：拆文件时新文件与主文件顶层重名 → E00449；靠 namespace 归位 + deps-check 兜底。
3. **巨型函数拆分的性能**：提子函数后 LLVM 优化器可再内联，实测回归（p.9.20 的性能报告体系复用）。
4. **层 II 触及语言核心**（可见性检查在语义层 sinfer）——自举双体（tiec 与 tie 语言）同步变更，需分两步落（先诊断后强制）。

---

## 7. 决策点（待拍板）/ Decision points

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 单文件上限 | **800 行（已拍板 2026-09-22）** |
| D2 | 层 II 语言增强入 ROAD | **是（已拍板 2026-09-22）**，p.9.21.4-6 执行 |
| D3 | builtin_expr 拆法 | 两步制（按推荐执行：先提子函数，后表驱动调度） |
| D4 | 单函数上限 | 300 行（按推荐执行） |
|---|---|---|
| D1 | 单文件上限 | **800 行**（gen 生成文件豁免） |
| D2 | 层 II 语言增强是否入 ROAD | **是**，p.9.21.4-6 预留，tiec 痛点驱动 |
| D3 | builtin_expr 拆法 | **两步制**：先提子函数（机械安全），后表驱动调度 |
| D4 | 单函数上限 | **300 行**（超限需拆子函数或查表化） |
