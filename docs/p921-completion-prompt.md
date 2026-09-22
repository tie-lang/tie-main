# p.9.21 收尾 —— 执行提示词 / p.9.21 Completion Execution Prompt

> 用途：新会话/子代理接手 p.9.21 剩余工作（p.9.21.3 收尾 + p.9.21.4/5/6 语言层）时，将本文件全文作为上下文注入。
> EN: Inject this file as context when a fresh session takes over the remaining p.9.21 work.
> 前置文档：`docs/designs/tiec-modularization-design.md`（定稿）、`docs/p921-execution-prompt.md`（首轮提示词）、`docs/designs/tiec-dual-axis-optimizer.md`。

---

## 一、常识 / Background

**项目**：tie 是自举编程语言（纯 tie 实现、禁 Rust、LLVM 后端）；tiec 是 tie 写的自举编译器。
**仓库**：编译器源码 `F:/Projects/tie-repo/tiec`（分支 p.7）；文档与 ROAD `F:/Projects/tie-repo/tie-main`（同分支）；内置库源仓 `F:/Projects/tie-repo/tlib`（发行副本 `~/.tiec-lib/tlib`）。
**v3 归档**：p.9.21 开工前的旧 tiec 已归档为 `tie-lang/tiec_v3`（归档点 dbbcc92；服务端完整副本，默认分支 p.7），只作历史参照，开发全在 tiec 主线。

**p.9.21 已完成（截至 2026-09-22）**

* **p.9.21.0 归档**：`tie-lang/tiec_v3` 已建（dbbcc92 / 自举 exe 2cec594a）。
* **p.9.21.1 依赖契约**：`tiec/scripts/deps-check.tsh.tie` 落地（21 库位矩阵 + 规模统计）；driver 全拆（2529 → 474 行 + 7 子模块，driver 库 0 超限）。
* **p.9.21.2 irgen_expr 拆解**：`builtin_expr` 2689 → 635 行（108 分支 → 8 个 `irgen_bi_*.tie`）；`irgen_expr.tie` 8790 → 744 行 + 16 域文件；两步制①完成，②（表驱动）待 L5。
* **p.9.21.3 批量拆分**：超 800 行文件 **33 → 3**（233 源文件）；后端 8 文件 + 前端/解释器/配置 12 文件分片；`tig_stmt` 1026 → 32、`gen_inst` 769 → 191、`builtin_call` 1122 → 165（三个大调度器分支提取）。
* 附带修复：`expand_generics` 的实例化上限由绝对 2000 改为相对 `2000 + n0 * 4`（单元已约 1900 函数，绝对上限会挡掉一切合法的小函数拆分）。

**剩余态势（本提示词的起点）**

* 超 800 行文件 3 个：`frontend/sstate.tie` 1919（179 个顶层全局表）、`frontend/sinfer_q2_q1.tie` 1522（单函数 `infer_expr` 1523 行）、`frontend/scheck_q2_q1.tie` 926（单函数 `check_stmt` 927 行）。
* 单函数超 300 行（D4）5 个：`infer_expr` 1523、`check_stmt` 927、`inline_expand` 414（middle/passes）、`tig_parse_float` 358、`tig_inflate_raw` 541。
* 依赖矩阵门禁仍报 **10 条越界边 / 7 库处环**（见 §四）。
* 层 II（p.9.21.4/5/6）未开工；库资格四项（pub API 面 README / 独立自检 / 独立发行 / 依赖单向）未收口。
* 孤儿模块 `compiler/middle/pass/*`（passmanager / pass_registry / passes / pass_test）无外部引用，待清理。

## 二、目标 / Goals

1. **G1 p.9.21.3 收尾（D1：单文件 ≤800 行，`diagcode_cat.gen` 豁免）**：3 个超限文件全部达标。
   * `sstate.tie`：属数据主导文件——把表初始化搬进函数、或把 179 个全局表按域拆到多个文件（全局 var 允许分布在多个文件顶层，各文件各自顶层声明即可）。
   * `sinfer` 的 `infer_expr`、`scheck` 的 `check_stmt`：**语句级提取**（非分支分派，需按语义段落命名提子函数），或先按「域子段」拆文件再逐个提函数。
2. **G2 D4：单函数 ≤300 行**：上面 5 个函数全部达标（`inline_expand` / `tig_parse_float` / `tig_inflate_raw` 同样是语句级提取）。
3. **G3 deps-check 全绿**：清 10 条越界边 + 7 库跨库环（见 §四），门禁退出码 0。
4. **G4 p.9.21.4 II1 强制可见性**：按 L1 梯度落地（A1a 现状默认 / A1b ns 级 / A1c 包级 / A1d 全私有+显式导出），**先诊断警告后强制错误**，tiec 自身 dogfood 迁移到 A1b。
5. **G5 p.9.21.5 II2 pub const**：常量可见性与函数同规则（推荐 A2b），消灭跨文件常量本地重定义漂移（opcode 表事故根因之一）。
6. **G6 p.9.21.6 II3 模块级增量编译**：模块 = 缓存单元（联动 p.9.15 编译缓存），提供增量正确性验证 + 提速数据；模块 ABI 基于 tieir（后端无关）。
7. **G7 库资格四项收口**：每个方法库一份 pub API 面清单（`README.tie` 或注释头）、一个可脱离 driver 跑的 `<lib>_test.tie`、依赖单向（G3）、下放判定按设计 §I1b 执行（interner/columnar/diag 渲染/ast/lex/parse/sema/ir/tieir → std；interp/config → ext；types/irgen/llvmgen/passes 留 tiec）。
8. **G8 清理与收敛**：孤儿 `middle/pass/*` 删除或并入 `middle/passes.tie`；`driver/util.tie` 的 flat 平铺在 L1 落地后收敛为 `namespace driver`；拆分工具从临时目录入库（建议 `tiec/tools/split/` 或 `tiec/scripts/`）。
9. **G9 p.9.20.6 性能参考报告**：与 G1 合并验收（l×t 各档性能 + trm/WASM 前瞻验证）。

**总验收**：全仓 ≤800 行/文件、≤300 行/函数、deps-check 退出码 0、自举不动点达成、regress 不劣化、层 II 四项 dogfood、库资格四项齐备。

## 三、纪律 / Discipline

**工作流**

* 小任务逐个交付：完成一个 = 一次提交（commit message 英文）+ regress 全绿；全部完成再总回归。
* 遇 bug 必做 RCA 并直接修复，不绕过、不掩盖；RCA 结论写进提交与注释。
* 不交付已知缺陷：探针过但 driver 级失败的改动必须门控（t3 先例：00dd649 门控 → dbbcc92 解封）。
* 文档双语、列表用 `*`、禁 "P1"/"F1" 这类无意义标签；回归细节不进对外文档。
* **严禁后台运行命令**；单命令约 120 秒上限（超时被 SIGTERM）。清缓存用 `mv ~/.tiec-cache <backup>`，**禁止 rm -rf**。
* 推送：禁止向 `git.franj2.top` 推送；tie-main 远端名是 `github`。**本机代理会让 `git push` 假报 "Everything up-to-date"——用显式 SHA 推送**（`git push https://$(gh auth token)@github.com/tie-lang/<repo>.git <sha>:refs/heads/p.7`），推完必须 `ls-remote` 核对 tip。

**自举门禁（每个改动后）**

* 配方（三阶不动点）：`tiec.exe compiler/driver.tie -l2 -t0 --no-warn --no-cache -o n1.exe` → `n1` 自编 → n2 → n2 自编 → n3；`SHA(n2)==SHA(n3)` 即不动点，然后 `cp n3.exe compiler/tiec.exe` 升格。
* 现成脚本：`F:/Projects/tie-repo/_tiec_verify/fp.sh`（`sh fp.sh <输出目录>`，约 100 秒跑完三阶）。
* **自举次序铁律**：改编译器语义/上限/诊断的改动，必须**先落该改动 → 自举升格 → 再改依赖它的源码**；否则旧编译器会把新源码判错（E00520 上限修正就卡过这一步）。
* 涉及 llvmgen/irgen 语义的变更 = 有意的不动点变更，重录基线并在 ROAD 标注。

**回归门禁**

* regress-s21 基线 **157 PASS / 8 FAIL / 2 SKIP**（8 项既有失败）。判定回归必须**用旧编译器跑同一套对照**（`git show HEAD:compiler/tiec.exe > old.exe` 后同命令跑），并比对 FAIL/SKIP **集合**（不只数量）。
* 命令：`tsh_main.exe -f 'scripts\regress-s21.tsh.tie' 'compiler\tiec.exe'`（tsh_main.exe 在 `F:/Projects/tie-repo/tshell/src/tsh_main.exe`），约 110 秒。

**技术铁律**

* 禁 Rust；一切能力优先纯 tie；性能永远优先；开发期编译加 `--no-warn`，**全部完成后专门跑一次警告检查**（不带 `--no-warn` 全量编译），认真消除每条警告而不是压掉。
* 语言改动六原则：opt-in、脚本友好、正交、后端无关、选项菜单、梯度可见性；**先诊断后强制**；默认档 = 最接近现状。
* 每次代码 patch 后 **grep 核验标记存在**（Python replace / Edit 的 old_string 不匹配会静默跳过）；删大块调试代码后核验相邻 `var`/函数仍在。
* `git add <目录>/` 会把本地调试产物一起入库——只 add 明确文件，误入后用 `git rm --cached` 收回。

**tsh 脚本（`.tsh.tie`）写作铁律**（实测，违反必卡）

1. 解释器约 5 万语句/秒——**禁止**在解释器里逐字符扫全仓；重活交原生 `findstr`/`find`，解释器只处理小输出（`split_lines` 本身很快，130KB/31ms）。
2. 表作形参是**值拷贝**，函数内改表无效 → 共享状态用全局表直接写。
3. 顶层 `var x = f()` 的初始化会被**提升**到最前 → 顺序敏感逻辑收进单一入口函数。
4. 函数内 `while` 中「标志位 + 嵌套 if/else」**不终止**（interp 缺陷，复现件 `tiec/tests/_p921_interp_flag_probe/flag_nested_if.tie`）→ 只用扁平单层 if。
5. `exit()` 不终止后续语句；`find <文件>` 经 `exec_output` 恒空（可行形态 `cmd /c type "f" | find /c /v ""`）；保留字坑：`text`、`num` 不能作变量名。

**拆分工程铁律**（前两轮踩坑总结，工具已固化）

1. else-if 链与多行条件块必须**整块**搬（含起始 `if` 与闭合 `}`）；切短会把后续函数吞进体内。
2. 链块与相邻语句共享局部变量时按**区域**搬（向上吞并紧邻 `var`/注释、向下到下一个同级块起点），或就地保留。
3. 花括号计数必须**字符串/注释感知**（tie 里 `{` 常出现在注释与字符串）。
4. 拆出文件只含函数与注释：**不含 import、不含顶层全局 var**（globals 与 import 树留主文件，由主文件 import 分片）。
5. `main` 必须留顶层（放进 ns 链接期缺入口 LNK1561）。
6. **命名空间归属决定函数身份**：`namespace X {` **之前**定义的函数是顶层函数，被其他 ns 裸调（semantic 的 `sm_warn_*` ← `namespace scheck`）；分片必须按各函数自身上下文包裹，否则报「未定义函数」。
7. **分片文件绝不覆盖**：新分片用 `_qN` 后缀；改完必须做函数集完整性校验（原函数集 ⊆ 主文件剩余 ∪ 全部分片）。
8. void 调度分支体必须多行（tie 语句以换行分隔）；提取函数的形参**整组透传**，类型直接取自原签名。

## 四、依赖矩阵越界边清单（G3 工作清单）

设计方向：`interner/bytes/columnar/diag` 零依赖 → `types←interner`、`ir←interner/columnar/types`、`lex←interner/diag`、`ast←interner`、`parse←lex/ast/interner/diag`、`sema←ast/types/diag/interner`、`irgen←ast/ir/sema`、`llvmgen←ir`、`interp←ir`、`passes←ir`、`tieir←ir`、`trm←ir`；`driver` 可编排全部；`core`（dispatch 等公共基建）全库可依赖。当前 10 条越界边（2026-09-22 实测）：

| 越界边 | 具体位置 | 收口方向建议 |
|---|---|---|
| diag → sema | `error_driver.tie → semantic.tie` | 诊断驱动不应反向依赖语义层：把错误消息拼装下移为 diag 侧参数化 API |
| types → ir | `frontend/stype.tie → middle/data.tie` | 类型系统只依赖 interner；`data.tie` 的 tag/运算符表若为语言规范资产，应下放 std 或经 diag/types 显式导入 |
| types → sema | `frontend/stype.tie → frontend/sstate.tie` | 同上：类型构造不应读语义状态，改为形参传入 |
| parse → interp | `frontend/mexpand.tie → interp/interp.tie` | import 展开借用解释器求值：抽公共「编译期求值」契约（或下放 std），禁 parse 依赖 interp |
| sema → parse | `semantic.tie → parser.tie / mexpand.tie` | 语义检查读 AST 应由「parse 产出的 AST 契约」承接，而不是反向 import 解析器 |
| irgen → llvmgen | `irgen.tie → llvmgen.tie` | 反向依赖（后端插件注册）；改为 driver 侧装配注册表 |
| interp → types / parse / sema | `interp.tie → types.tie / parser.tie / sstate.tie` | 解释器只应依赖 ir + 显式契约（源码/AST 由调用方传入） |
| trm → tieir | `trm_loader.tie → tieir_ser.tie` | 加载体读 tieir 序列化属正向后端依赖，评估把 tieir 归入 ir 库或允许 trm←tieir |

判绿标准：门禁退出码 0（无越界边、无跨库环、无悬空 import、无未纳入矩阵文件）。

## 五、避坑清单 / Pitfalls

* `fn(i64) -> i64` 函数类型参数已存在（collection 的 map_i64）——L5 是普及 + 性能确认，不是新增。**两层制②（表驱动调度）阻塞在此**：没有一等函数引用时「名字→处理函数表」无法表达，索引+switch 只是等价形态、不改架构。
* ns 私有**已部分生效**（E00332：`pub func` 才能在 ns 外调用）——L1 落地前先做全仓普查，别重复实现已有检查；同时注意这与设计「pub 无强制」的记述有出入，动工前先核实语义层现状并更新设计文档。
* std 库函数在 namespace 内（如 `coll.kmp_find`），调用须限定名。
* 全局 var 必须文件顶层——`sstate.tie` 的 179 个表可以拆到多文件（各自顶层声明），但不能进 namespace。
* `compiler/middle/pass/*` 与 `middle/passes.tie` 是**两套同名 passes**（前者 9 月 12 日旧件、无外部引用）——清理前先确认无 `import` 引用，避免误删现行件。
* `driver/util.tie` 目前是 flat 平铺：`consteval.tie`、`putil` 等 12+ 处前端/后端文件**裸调** `slice/trim/split_lines/find_char/has_prefix/strip_type_header` 等 driver 顶层函数（历史隐藏耦合）；L1 落地时必须一并收口，否则会把耦合固化。
* `frontend/putil.tie` 树里的 `split_current_gt` 是**非 pub 的顶层函数**（不在 `namespace putil` 内），被 `expect_type_gt`（活代码：`pexpr_type.tie`、`pstmt_top` 多处调用）引用；一次分片覆盖事故曾把它的定义删掉而直接报 E00489——改动该目录前先 `grep -rn "func split_current_gt" compiler/` 确认定义仍在，并按 §三 第 7 条做完整性校验。
* 缓存键不含编译器二进制版本（跨版本可能命中过期产物，随 p.9.15.2 补）——改编译语义后统一用 `--no-cache` 或先 `mv ~/.tiec-cache`。
* 性能审计方法（内置库下放前）：Python 正则扫 `= x + y` 密度 + 循环上下文 + 实测微基准（库版 vs 手写同算法）；静态 grep 判不准类型（整数自增无害）。
* 拆分脚本工具目前在 `F:/Projects/tie-repo/_tiec_verify/`（**未入库**），换机即丢：先入库再继续（见 G8）。

## 六、建议执行顺序 / Suggested order

1. 工具与文档入库（拆分脚本、复现探针已入库）→ 提交。
2. G3 依赖矩阵逐边收口（一次一边，每边一提交 + regress 对照）；同步更新设计文档中与现状不符的记述。
3. G1 + G2 逐文件收尾（`sstate` → `infer_expr` → `check_stmt` → `inline_expand` → `tig_parse_float` → `tig_inflate_raw`），每文件一提交。
4. G7 库资格四项（pub API 清单 + `<lib>_test.tie`），从 core/字段清晰的库开始。
5. G4 → G5 → G6 层 II 语言项（先诊断后强制；每项先在 tests 试点再 tiec dogfood；语言行为变化处重录不动点）。
6. G8 清理（孤儿模块、flat util 收敛）、G9 性能报告。
7. 总验收：门禁全绿 + 全仓行数上限 + 不动点 + regress + 警告检查。

## 七、验收清单 / Acceptance checklist

* [ ] 全仓 .tie 文件 ≤800 行（`diagcode_cat.gen` 豁免）
* [ ] 单函数 ≤300 行
* [ ] `deps-check.tsh.tie` 退出码 0（无越界边/环/悬空 import/未纳入文件）
* [ ] 三阶自举不动点达成，`compiler/tiec.exe` 升格为新不动点
* [ ] regress-s21 与旧编译器同套对照：FAIL/SKIP 集合逐项一致且不劣化
* [ ] 全量编译零警告（专门一轮警告检查）
* [ ] 层 II 四项（L1/L2/L4 落地，L5 独立评估）在 tiec dogfood 完成
* [ ] 每库 pub API 清单 + 独立自检可跑
* [ ] 下放判定执行完毕（std/ext 到位，tlib 源仓同步）
* [ ] ROAD 与设计文档同步到「已完成」状态（含重录的不动点基线）

---

*EN summary: Completion prompt for p.9.21. Already landed: v3 archive, the deps-check gate, full driver split, builtin_expr + irgen_expr decomposition, and the repo-wide file split (33 → 3 oversized files; three big dispatchers cut into per-branch functions). Remaining: finish the last three oversized files (sstate is a data-table file; infer_expr and check_stmt need statement-level extraction), bring every function under 300 lines, clear the ten cross-library edges reported by the gate, then land Layer II (L1 visibility ladder, L2 pub const, L4 module-level incremental compilation; L5 function references stay independent), close out the four library qualifications, clean the orphan middle/pass module and the flat driver util coupling, and ship the p.9.20.6 performance report. Discipline: per-task commits with fixed-point bootstrap (bootstrap the compiler change first, then the source that depends on it), regress 157/8/2 cross-checked against the old compiler, tsh scripting and splitting rules recorded in sections three and five, explicit-SHA pushes because the local proxy can fake "Everything up-to-date".*
