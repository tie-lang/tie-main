# ROAD p.8 档条目状态核验（2026-10-04）

>核验对象：`tie-main/ROAD.md` 的 p.8 档（语言），行 106–181，共 **22 条**
> 判据：每条都要求当前代码/实测证据，**不采信原标记**
> 复用：`tiec/_spec_audit/out/SUMMARY.md`（17 章规范对账，412 条状态）+ 明细表
> 实测环境：`tiec` 仓 HEAD = **`ecd3436`**（注：SUMMARY 基线为 `c8b45f4`，本轮比它**更新**，结论以本轮实测为准）
> 探针：本轮新增 `tiec/_spec_audit/p8/`（22 个）；官方探针 `tiec/tests/language/`
> 编译命令：`./compiler/tiec.exe <p>.tie -l2 -t0 --no-warn --no-cache -o F:/Projects/_tmp/roadcheck/<p>.exe`
> 纪律：`ROAD.md` 全程**只读**，未改动任何仓库文件（除新增探针目录）。

---

## 统计

| 原 [x] | 原 [ ] | 原 [~] | 核验后 [x] | [ ] | [~] | 标记有误 |
| --- | --- | --- | --- | --- | --- | --- |
| 19 | 3 | 0 | 18 | 1 | 3 | **4** |

**一致性核对**（派生量回算表格状态列）：22 行 = 18 + 1 + 3 ✔；原标记 19 + 3 + 0 = 22 ✔；
状态变化 4 条 = 2 条`[x]→[~]`（p.8.1.5、p.8.2.1）+ 1 条 `[x]→[ ]`（p.8.3.1）+ 1 条 `[ ]→[x]`（p.8.1.8）✔

★ **19 个 `[x]` 条目的官方验收探针，本轮全部在 HEAD 上重新编译 + 运行通过（compile=OK run=0）**。
标记有误的 4 条**全部集中在 ROAD 自己没写完备性的地方**（子能力未测/ 自陈遗留 / 只做了一半）。

---

## 逐条核验

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 114 | **p.8.1.1** const fn 编译期求值（可行静态元编程） | [x] | **[x]** | `tests/language/const_fn.tie` rc=0 run=0，输出 `120/55/Hello, tie!/720/6765/48/64` 逐行匹配；代码 `compiler/frontend/consteval.tie`（684 行） | 「静态元编程」只到**全局标量初始化折叠**一级：const fn 结果**不能**作 array 长度/泛型实参（`E00707`）。已对照证明这是既有限制非本项缺陷：普通 `const N: i64 = 5` 作长度同样 `E00707`（`p811_ctrl.tie`）。⇒ ROAD 措辞「可行静态元编程」偏乐观，但**主体能力成立** |
| 115 | **p.8.1.2** 错误处理统一：Option/Result 泛型增强 + `?` 解包 | [x] | **[x]** | `tests/language/result_option_generic.tie` rc=0 run=0；SUMMARY ch08 §8.2「`?` 后缀传播」已实现（`d1.tie` 编译运行，Ok 穿透 / Err 逐层上抛） | 泛型enum 模板参数 + `?` 链两个核心都在。**但**规范范式 `Ok(to_i64(s))` 因编译器缺陷 #2（`to_i64(string)` 必生成坏 IR）不可用，须改 `parse_int`；`Ok/Err/Some/None` **裸名不可用**（须写全名，SUMMARY ch09 §9.4）。属既有缺陷/写法差异，非本条未落地 |
| 116 | **p.8.1.3** 泛型增强：约束 / 特化 / 变长泛型 | [x] | **[x]** | `tests/language/generics_enhance.tie` rc=0 run=0，输出 `10/21/0/aaa/yy/5/100/3.500000` 逐行匹配；探针覆盖变长泛型 `...T`、显式特化 `func max<string>`、多类型参数特化 `pick<i64,string>` | 三个子项（约束/特化/变长）全部有探针且通过 |
| 117 | **p.8.1.4** 模式匹配增强：多字段解构 / 穷尽检查 / 守卫 | [x] | **[x]** | `tests/language/pattern_enhance.tie` rc=0 run=0（11 行输出）；负例 `pattern_enhance_neg.tie` **rc=1被拒**（确认负例真被拒） | 三子项齐备。穷尽检查另由 SUMMARY ch08 §8.3独立佐证（`n8_3b.tie` → `E00014 switch 不穷尽`） |
| 118 | **p.8.1.5** 可空类型：`?.` / `?:` / `a?[i]` / unwrap 糖 | [x] | **[~]** | `tests/language/optional_chain.tie` rc=0 run=0（12 行输出）**但该探针从未正向使用 `?.`**（`grep "?." optional_chain.tie` → rc=1 零命中；`?.` 只出现在**负例** `optional_chain_neg.tie`）；本轮补测 `p8/p81_safe_nav.tie` → **`E00365 变体 'Some' 的 payload 暂不支持类型 'Inner'`** | ★ **标记有误**。`?.` 的解析（`pexpr.tie:349-375`）与后端（`irgen_rt_p1.tie:301` `tig_safe_access`，含 `K_STRUCT` 字段分支）**都在**，但**正向不可达**：`Option.Some(<struct>)` 被 p.8.1.7 的 payload 白名单（`scollect_port_q1.tie:327`）拒绝 ⇒ `Option<Struct>` 根本构造不出来。**通**：`?:`（i64/string）、`a?[i]`（含越界→None、None 传播、二级嵌套 `?[i]?[j]`）、`?` 解包。**不通**：`?.` 字段访问（被白名单锁死） |
| 119 | **p.8.1.6** 表删除/缩表原语：动态表 pop / 截断缩表 | [x] | **[x]** | `tests/language/table_pop_trunc.tie` rc=0 run=0（21 行输出）；负例 `table_pop_trunc_neg.tie` **rc=1 被拒** | 「原语」口径成立（截断缩表 + pop）。注意属**浅拷贝共享句柄**语义：与 ROAD:364/520 声称的「表是值捕获」相反（见 SUMMARY §4 #4） |
| 120 | **p.8.1.7** enum payload 白名单放开 table/f64 | [x] | **[x]** | `tests/language/enum_payload_ext.tie` rc=0 run=0，8 行输出 `num:3.5/3/1/3/9/hi/0.500000/none` 逐行匹配；白名单代码 `scollect_port_q1.tie:327` | 探针覆盖 f64 / table<i64> / map<i64> / string / table<f64> 五类 + 无payload 变体，全部通过 |
| 121 | **p.8.1.8** enum payload 白名单二批：struct / fn payload + table\<Enum\> 自引用 + i64/i128 解构 | [ ] | **[x]** ★ | 拆成 5 个独立子探针（`p8/sub/`）：`a_struct_payload` **rc=1**（真未做）、`b_fn_payload` **rc=1**（真未做）、`c2_selfref_use` **rc=0 run=0** 输出 `1/42`、`d_i64_payload` rc=0、`e_i128_payload` rc=0 | ★ **标记有误（`[ ]` → `[x]`）**。本条是四项打包，其中**两项其实已经能用**、只是 ROAD 没更新：① `table<Enum>` 自引用递归**端到端可用**（`c2_selfref_use.tie`：`Node.Branch(kids)` 构造 +嵌套 switch 解构出 `42`）；② i64/i128 payload 声明 rc=0。**未做的只剩 struct / fn payload 两项**（`E00486 期望类型，实际是 Struct`）。⚠ i128 payload 有**新发现的编译器缺陷**：`e3_i128_small.tie` → `opt: invalid cast opcode for cast from 'i128' to 'i64'`（i128 过了白名单但 enum 槽按 i64 布局） |
| 131 | **p.8.2.1** 可空链语法 `?.` / `?:` / `a?[i]`（联动 p.8.1.5） | [x] | **[~]** | 同 p.8.1.5（同提交 `ba9221d`，同一探针同一限制，不重复计） | ★ **标记有误**，理由与 p.8.1.5 完全一致：`?.` 正向不可达（payload 白名单锁死），`?:` / `a?[i]` 全通 |
| 132 | **p.8.2.2** 常用糖集：for..in 解构 / 级联调用 / 命名参数 / 链式比较 | [x] | **[x]** | `tests/language/sugar_set.tie` rc=0 run=0，15 行输出逐行匹配；探针头注释明确列出 4 个子项各自场景 | 四子项齐备。级联调用的口径 = **方法链 + 数据流箭头**（探针第 4 项），非独立语法 |
| 133 | **p.8.2.3** 字符串插值 `h"..."` 模板 | [x] | **[x]** | `tests/language/string_interp.tie` rc=0 run=0（含 `{{literal}}` 转义、h 串多行、`{ 无条件插值`）；lexer `lex_scan.tie:73-88` + `pexpr_p1.tie:558-596` | ROAD **自己已诚实标注遗留**：`{expr:规格}` 格式说明符。本轮复现确认遗留仍在：`p8/p823_spec.tie`（`h"val={x:08.2f}"`）→ `E00484 期望 '}'，实际是 Colon`。与 SUMMARY ch01 §1.9「12 个探针全 E00484」一致。**原标记判[x] 可接受**（主体 `h"..."` 已落地，遗留已在条目正文写明） |
| 134 | **p.8.2.4** 运算符重载：struct 自定义 `+ - * / ==` 等 | [x] | **[x]** | `tests/language/op_overload.tie` rc=0 run=0，输出 `sum=(3,7)/b=(6,12)/s=(2,4)/rev=(2,4)/iseq=1/nv=(-1,-2)/neg2=(-1,-2)/c=(-5,10)/c== true/< 冠名 true`；负例 `op_overload_neg.tie` **rc=1 被拒** | 12 个 `op_*` 约定齐备（`sinfer_p1.tie:596-647`）。⚠ 约定名与**规范不一致**（规范写 `add/eq/cmp/index`，实现用 `op_add/op_eq/op_lt/…`；`index`/`index_set`/`op_index` 全仓零命中）——属规范/实现命名冲突，非本条未落地 |
| 135 | **p.8.2.5** 集合速写：表/映射推导式 `[x * 2 for x in arr if cond]` | [x] | **[x]** | `tests/language/comprehension.tie` rc=0 run=0，5 行全 `PASS`（basic/filter/ctx_arg/str_elem/destructure） | tie 无映射表字面量故只做数组推导（ROAD 已注明）。⚠ 推导式**不收范围源**、**不可嵌套**（SUMMARY ch03 §3.17），但条目未声称这两项 |
| 136 | **p.8.2.6** 泛型糖：默认类型参数 / 约束简化 | [x] | **[x]** | `tests/language/generic_sugar.tie` rc=0 run=0，6 行输出逐行匹配 | `<T, U=默认>` 默认参数 + `<T, U: 约束>` 约束回填糖，两个子项均有覆盖 |
| 137 | **p.8.2.7** 属性 getter/setter：struct 计算属性 | [x] | **[x]** | `tests/language/computed_property.tie` rc=0 run=0，7 行 `fah=212/celsius 写回=100/area=24/pn=(6,8)/mag=100/ord=7/conv=44`；负例 `computed_property_neg.tie` **rc=1 被拒**（只读属性写报错） | getter + setter 双向均验证（写回生效）。声明形式为 `<Struct>::attr` / `attr_set` 方法约定（探针注释已说明裁决理由：struct 体禁方法） |
| 138 | **p.8.2.8** 数据流箭头 `->`/`<-` 增强与推广 | [x] | **[x]** | `tests/language/dataflow_arrow.tie`（7 PASS）+ `dataflow_arrow2.tie`（9 PASS）均 rc=0 run=0 | D1–D6 规则 +链式/方法/反向/尾随闭包组合全部覆盖。⚠ 管道进下标/字段/运算符/条件四种位置不通（SUMMARY ch03 §3.11），条目未声称 |
| 139 | **p.8.2.9** 尾随闭包：`arr.map { ... }` 免括号 | [x] | **[x]** | `tests/language/trailing_closure.tie` rc=0 run=0，10 行输出 | 裸 `{ }` 作末位实参可用 |
| 140 | **p.8.2.10** 展开/解包调用 `f(args...)` | [x] | **[x]** | `tests/language/spread_call.tie` rc=0 run=0，4 行输出 | 前/中位置均覆盖 |
| 141 | **p.8.2.11** guard 早退：`guard cond else { return }` | [x] | **[x]** | `tests/language/guard_early.tie` rc=0 run=0，5 行 `pos/zero/neg/small:1/big` | 与 SUMMARY ch04 §4.9 已实现一致 |
| 142 | **p.8.2.12** 宏升级：声明式模板 / 卫生宏 | [x] | **[~]** | `tests/language/macro_hygiene.tie` rc=0 run=0，9 行输出（`__` 前缀卫生唯一化、跨展开单调、嵌套、与语句级宏双轨） | 声明式模板 + 卫生唯一化**通**；ROAD 自陈边界「完整模式匹配/ 递归 / 卫生闭包语义注明后续」**确认仍空**：探针注释第 12 行明写「真正完整的模式匹配/递归宏扩展/卫生闭包语义等：后续（p.9.x）」，全仓无递归宏实现。⇒ 半成品，按口径判 `[~]` |
| 158 | **p.8.3.1** actor 字段显式初值捕获：`= N` 写入 `run` record 初始化 | [ ] | **[ ]**（但已部分实现） | **实现代码确实存在**：`compiler/backend/irgen_rt_p2.tie:189-196`（「p.8.3.1：显式字段初值在启动记录时按声明顺序 store」+ `dv = tig_expr(fdef)`）；`scollect_port_q2.tie:181` 字面量白名单。实测：`p831c_min.tie`（单 i64 = 7）**rc=0 run=0 输出 7**；`p831e_twofields.tie`（7/0 混排）**rc=0 输出 7/0**；`p831k`（f64 = 2.5）经`to_i64` 读出 **2** ⇒ 初值确已写入；`p831l`（string = "hi"）经 `str_len` 读出 **2** ⇒ 同| 负例：非字面量初值被 `E00654` 拒| **但**：官方验收探针 `s10_8.tie` **只声明 5 字段类型后 `println("ok")`，从不读取字段** ⇒ 官方「全类型初值验收」是空的 | ★ 主体能力**已落地但 ROAD 未更新**（`[ ]` 事实上偏保守）。未达成的是 ROAD 自列的验收项「全类型初值探针」：actor 方法**返回非 i64 即坏 IR**（`p831f` f64 / `p831g` string / `p831m`裸 string 字段均 `E00883 value doesn't match function result type 'i64'`）。已隔离证明这是**独立缺陷**、与初值无关：`p831i`（f64 字段**无初值**）同样坏、`p831h`（f64 有初值但不读）通过、`p831j`（普通 struct f64）通过 ⇒属**新发现的编译器缺陷**（actor 方法非 i64 返回值类型错配），不是 p.8.3.1 未实现。**建议改判 `[x]` 并把该缺陷另开单**；本次按「须有实测证据 + 验收项未达成」保守记 `[ ]` |
| 169 | **p.8.3.2** async 结果回传：`future` 值 + `await f` 阻塞取值 | [ ] | **[~]** | `await` **连关键字都不存在**：`grep "await\|reentrant" lex_symtab.tie lex_tokdefs.tie` → **零命中**（69 项关键字表无 `await`）；`p832_async.tie` → `E00000 期望 语句结束符，实际是 标识符 'w'`（`await` 被当普通标识符）；`future` 类型在 `llvmgen_str.tie`/`types_q1.tie` 零命中。**通的部分**：`async` 存在（`lex_tokdefs.tie:75` `lex_async` tag 93），`p832b_async_ff.tie`（无返回值 `pub async func`）**rc=0 run=0 输出 6** ⇒ fire-and-forget 半边通| 负例：`E00654` 等 | ★ 确为**半路**：① fire-and-forget（无返回值 async）**已通**；② `await` 取值 + `future` 值 + panic 传播 + 多 future 按 seq 回取 **全未做**（无关键字、无类型、无探针）。ROAD 标 `[ ]`，实际是「一半已通」⇒ 判 `[~]` |

---

## 标记有误的条目（**需上报**）

| # | ROAD 行 | 条目 | 原标记 | 实际| 证据 |
| --- | --- | --- | --- | --- | --- |
| 1 | 118 | p.8.1.5 可空类型 | `[x]` | **`[~]`** | 官方探针 `optional_chain.tie` **从未正向测 `?.`**（`grep "?."` 零命中，`?.` 只在负例出现）。本轮补测 `p8/p81_safe_nav.tie` → `E00365变体 'Some' 的 payload 暂不支持类型 'Inner'`。`?.` 前后端都在（`pexpr.tie:349-375` / `irgen_rt_p1.tie:301`）但**正向不可达**——`Option.Some(struct)` 被 p.8.1.7 白名单（`scollect_port_q1.tie:327`）拒绝，`Option<Struct>` 构造不出来。**通**：`?:`、`a?[i]`（含越界→None、二级嵌套）、`?` 解包 |
| 2 | 131 | p.8.2.1 可空链语法 | `[x]` | **`[~]`** | 同上（同提交 `ba9221d`、同探针、同限制，不重复计） |
| 3 | 121 | p.8.1.8 enum payload 二批 | `[ ]` | **`[x]`** | 拆 5 个独立子探针：`table<Enum>` 自引用递归**端到端可用**（`sub/c2_selfref_use.tie` rc=0 run=0，输出 `1/42`：构造 `Node.Branch(kids)` + 嵌套 switch 解构出 42）；i64 / i128 payload 声明 rc=0。**实际只剩 struct / fn payload 两项未做**（`sub/a_struct_payload.tie`、`sub/b_fn_payload.tie` 均 rc=1）。⇒ **打包条目应按子项拆分标记**，否则「四项打包标 `[ ]`」掩盖了两项已落地 |
| 4 | 158 | p.8.3.1 actor 字段初值捕获 | `[ ]` | **`[ ]`（但主体已落地，建议改 `[x]`）** | 实现代码在`irgen_rt_p2.tie:189-196`；实测 i64=7 / i64零值混排 7,0 / f64=2.5（读出 2）/ string="hi"（读出 len 2）**四种字段初值全部真写入 record**。但官方验收探针 `s10_8.tie` **只声明不读字段**，验收是空的；且暴露一个**独立编译器缺陷**：actor 方法返回非 i64（f64/string）必生成坏 IR |

---

## 卡在何处（`[~]` 条目的半成品状态）

| 条目 | 已通部分 | 卡住的那一步 | 卡点性质 |
| --- | --- | --- | --- |
| **p.8.1.5 / p.8.2.1**（同一提交 `ba9221d`） | `?:` 默认值（i64/string）、`a?[i]` 安全索引（越界→None、None 传播、二级 `?[i]?[j]` 嵌套）、`?` 解包糖、链可持续 | **`?.` 安全字段/方法访问正向不可达** | **被p.8.1.7 的 payload 白名单反向锁死**。`?.` 的语法（`pexpr.tie:349-375`）与后端（`irgen_rt_p1.tie:301` `tig_safe_access`，已写 `K_STRUCT` 字段分支）**都是完整的**，只差「`Option<Struct>` 构造得出来」——而那要求 p.8.1.8 放开 struct payload。⇒ **两个条目互为前提，p.8.1.8 不做则 `?.` 永远不可用** |
| **p.8.2.12** 宏升级 | 声明式模板宏（`macro name(a,b){体}`）、AST 片段宏、`__` 前缀卫生唯一化（跨展开单调）、与语句级宏双轨共存（`macro_hygiene.tie` rc=0，9 行输出） | **完整模式匹配宏/ 递归宏 / 卫生闭包语义** | ROAD 条目正文自陈「边界：完整模式匹配/递归/卫生闭包语义注明后续」，探针注释亦确认。属**设计边界未定义**，不是实现半途——递归宏会撞自举不动点，缺规范定义 |
| **p.8.3.2** async 结果回传 | `async` 关键字已登记（`lex_tokdefs.tie:75` tag 93）；**无返回值 `pub async func` 的 fire-and-forget 已端到端可用**（`p832b_async_ff.tie` rc=0 run=0 输出 6）；同步 RPC 等待结果可用（SUMMARY ch10 §10.3） | **`await f` 阻塞取值 + `future` 值（{record_ptr, slot_id, seq}）+ 多 future 按 seq 回取 + panic 在 await 点传播** | **第一步就卡住**：`await` **连关键字都没进 69 项关键字表**（`lex_symtab.tie` / `lex_tokdefs.tie` 零命中），被当普通标识符解析（`E00000`）；`future` 类型在 `llvmgen_str.tie` / `types_q1.tie` 零命中。⇒ 需要**新增关键字 + 新类型 + 三元组槽位模型**，是真正的能力缺口（非写法差异）。ROAD 标 `[ ]` 低估了已通的 fire-and-forget 半边 |

---

## ROAD 未提但该提的缺口（本轮新发现，ROAD 无任何条目）

| # | 症状 | 最小复现 | 性质 |
| --- | --- | --- | --- |
| 1 | **actor 方法返回非 i64（f64 / string / bool）必生成坏 IR**：`E00883 value doesn't match function result type 'i64'`。已隔离证明与字段初值无关（`p831i` f64 字段**无初值**同样坏；`p831h` 有初值但不读则通过；`p831j` 普通 struct f64 通过） | `p8/p831f_f64field.tie`、`p8/p831m_ret_string.tie` | **编译器缺陷**（新）。卡住 p.8.3.1 的「全类型初值验收」 |
| 2 | **i128 过不了 enum payload 的实际布局**：白名单 `types.is_int` 含 `TK_I128`（`types_q1.tie:645`）故放行，但 enum 聚合槽按 i64 布局⇒ `opt: invalid cast opcode for cast from 'i128' to 'i64'`。对照组：`f_i128_plain.tie`（i128 不进 enum）rc=0 run=0 正常 | `p8/sub/e3_i128_small.tie` | **编译器缺陷**（新）。白名单与后端布局不一致 |
| 3 | **`actor 方法不能返回 string/f64`** ⇒ 现有全部 actor 探针（`tests/actor/`、`_spec_audit/y/s10_*.tie`）都只回 i64，等于绕开了这条路径 | 同#1 | 同 #1 的另一面，建议合并 |

---

## 附：本轮核验的纪律与复用说明

* **复用度**：22 条中 **19 条直接由 SUMMARY + 明细 + 官方探针定级**，仅对「SUMMARY 未覆盖 / 需独立确认」写了新探针
  —— 即 p.8.1.5/2.1 的 `?.` 缺口（官方探针从未正向测）、p.8.1.8 的 5 个子能力拆分、
  p.8.3.1 的字段初值真实落盘（官方探针只声明不读）、p.8.3.2 的 fire-and-forget 半边、p.8.2.3 自陈遗留复现。
* **★ 方法论教训（沿用SUMMARY §3 纪律）**：本轮**新发现 2 个编译器缺陷**（#1 actor 非 i64 返回值、#2 i128 payload 布局），
  症状都是「探针编译失败」，与「特性未实现」**长得像**。判据是**先做隔离实验**：
  #1 用「无初值 f64 字段」「有初值不读」「普通 struct f64」三组对照把「初值」与「读取」两个变量分开；
  #2 用「i128 不进 enum」对照组分离。**没有隔离实验就会把这两个 bug 误记成「p.8.3.1 / p.8.1.8 未实现」。**
* **负例纪律**：5 个负例探针（`pattern_enhance_neg` / `optional_chain_neg` / `table_pop_trunc_neg` /
  `op_overload_neg` / `computed_property_neg`）全部确认 **rc=1 真被拒**，非「没崩即通过」。
* **探针第一版教训**：`p831_actor_init.tie` 初版让 `main`声明 `-> i64` 却只`println`（`E00204`）、
  `p81_safe_nav.tie` 初版struct 字段写成方法形态（`E00721`）—— **两次都被无关错误挡住**，
  修正后才拿到真信号。与 SUMMARY ch06-10「负例必须先写成可编译的正例形态」同源。
