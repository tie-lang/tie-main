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

#### I1 依赖方向契约（硬规则）

```
lib/     （interner/columnar/bytes）—— 不 import 任何编译器内部
core/    （ir/types/diagcode/ir_meta）—— 只 import lib/
frontend/（proto 解析 + 语义）           —— import lib/ + core/
backend/ （irgen + llvmgen）             —— import lib/ + core/ + frontend（AST 输入）
middle/  （passes/tieir_ser）            —— import lib/ + core/（不 import frontend/backend）
interp/  （解释器后端）                  —— import lib/ + core/ + frontend
driver/  （薄壳）                        —— import 全部，唯一 know-how 汇聚点
```

违规检查脚本化（`scripts/deps-check.tsh.tie`：解析 import 语句 vs 方向矩阵，CI 门禁）。

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

1. `middle/` 的任何文件不出现 `frontend|backend` 字样的 import；
2. 每组件可在无 driver 的情况下编译并通过独立自检（ir_test 模式推广：每组件一个 `*_test.tie`）；
3. pass 管线可被外部重排（kpass 序列只是 driver 的编排数据，组件无顺序知识）；
4. 依赖方向矩阵检查脚本全绿。

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
