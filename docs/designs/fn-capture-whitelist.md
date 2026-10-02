# tie fn 值捕获语义与捕获面白名单（设计定稿，p.9.11.22）

*EN: tie fn-value capture semantics and capture-surface whitelist (design final, p.9.11.22)*

**日期** / Date: 2026-09-27 · **状态** / Status: 定稿并部分落地
**关联** / Related: `docs/designs/round3-sugar-safe-std-design.md`（与其第三批「短闭包 `it`」同批）· `docs/designs/param-system-design.md`（`ref`/`immut` 约定）· `docs/designs/tiu-ui-widgets.md` §15.4/§15.6（控件动作参数位等待本档）

> EXEC BRIEF: Freezes the measured capture semantics of tie closures into a
> spec, defines the safe-zone capture surface as an explicit whitelist, lands
> the first enforceable rule (capturing a `ref` parameter is rejected in safe
> code), and records what remains open (mutable-capture annotation, event-loop
> thread interaction).

---

## 1. 实测冻结的捕获语义 / Measured capture semantics (frozen)

以下为 2026-09-27 在现役自举 tiec 上的实测结论，**作为规范冻结**（数字与判定均可复现）。

| 场景 | 实测行为 | 规范表述 |
|---|---|---|
| 捕获可写局部后，外层再改 | 闭包读到**旧值** | **按值快照**（捕获时刻的值） |
| 捕获后外层变量是否仍可用 | **可用**（`m` 改成 105 正常） | 捕获**不移交**外层绑定 |
| 闭包内写捕获的**标量** | 不回写外层 | 只读（无共享可变状态） |
| 捕获表（堆类型） | 可捕获 | 表可捕获 |
| 闭包内改捕获表的**内容**（`table_push`） | 外层 `len` **变化**（实测 inner=3 outer=3） | **表按引用捕获**（共享同一份底层数据，见规范 §5.10） |
| 捕获 `const` | 可捕获 | const 可捕获 |
| **捕获 `ref` 形参** | **闭包内写会回写到调用方** | **借用例外**（见 §3——这是唯一非值语义） |

关键结论：**捕获分两类** —— 标量、结构与枚举按**值**捕获（创建时刻的快照）；**表与映射按引用捕获**（闭包与外围共享同一份底层数据，任一方修改另一方可见）。引用捕获是"共享可变状态"进入程序的**唯一通道**，因此它也是并发安全规则的落点（规范 §10.5；第 11 章 `share` 域）。`ref` 形参是另一类例外：它按借用捕获，故在安全区被禁止（见 §3）。

> EN: Capture splits in two. Scalars, structs and enums are captured **by value**
> (a snapshot at creation time); **tables and maps are captured by reference** -
> the closure and its surroundings share one underlying buffer, so either side
> sees the other's writes. Reference capture is the only route by which shared
> mutable state enters a program, which is why the concurrency rules land here
> (spec 10.5; the `share` domain in chapter 11). `ref` parameters are the other
> exception: captured by borrow, hence rejected in safe code (see 3).

> **更正** / Correction (2026-10-02): 本表原记「表也是按值捕获（无别名）」**与实现不符**
> —— 2026-09-27 那次实测（外层 `len` 不变）未能复现；在现役自举 tiec 上重测为
> **外层 `len` 变化**（`var t=[1,2]`，闭包内 `table_push(t,99)` ⇒ `inner=3 outer=3`），
> 即共享句柄。规范正文 §5.10 / §10.5 自始写的就是「按引用捕获」，本档为对齐规范而更正。

---

### 1.1 捕获引用的生存期 / Lifetime of captured references

捕获一个引用类型，等价于**把该引用交给闭包保管**：闭包存续期间该引用必须有效。这条要求
由引用计数承担，且必须同时满足三个性质。

| 性质 | 要求 | 实现方式 |
|---|---|---|
| **性能强** | 捕获是 **O(1)** 的——只搬句柄，**绝不复制容器内容** | 捕获点只写 8 字节句柄（+ 一次引用计数递增） |
| **内存低** | 闭包不再被引用时，其捕获的引用必须**归还**，不得积压 | 闭包值消亡点（作用域结束、变量被覆盖）发出释放 |
| **内存安全** | 闭包存续期间捕获的引用**始终有效**；不得悬垂、不得重复释放 | 引用计数保证：捕获 **retain**、消亡 **release**，两侧配对 |

**为什么必须"捕获时 retain"**：容器在本作用域结束时会被释放。闭包可能逃逸出定义它的函数
（`func make() -> fn() -> i64 { var t = [...]; return func() -> i64 { return len(t) } }`），
此时若不在捕获点 +1，外层函数退出即释放 `t`，闭包持有悬垂句柄，调用即崩溃。
这与「`return <表>` 需 retain」是同一条规则，两个外传口（返回值、闭包捕获）对称处理。

**为什么必须"消亡时 release"**：只 retain 不 release 会让引用计数永不归零、容器永不回收。
**释放点必须在闭包值消亡处，而不是创建处**——env 的布局（捕获了哪些引用）只有创建闭包的
函数知道，而关掉闭包的是持有它的作用域。因此释放动作必须能**在不知道布局的地方发起**，
这要求 env 自带足以完成释放的信息（析构入口或引用计数），见 §6。

*EN: Capturing a reference means handing it to the closure to keep; a refcount
holds it. Three properties must hold together: capture is O(1) and never copies
the container (strong performance); the reference is returned when the closure
value dies (low memory); and it stays valid for the closure's whole life, with
no dangling or double release (memory safety). The retain must happen at the
capture site because the container is released at the defining scope's exit
while the closure may escape that function - the same rule as returning a
table. The release must happen where the closure value dies, not where it was
created: only the creating function knows the env layout, yet the scope holding
the closure is what ends. So the release must be initiable without knowing the
layout, which requires the env to carry enough information to complete it (a
destructor entry or a refcount); see 6.*

## 2. 捕获面白名单 / Capture-surface whitelist

### 2.1 可捕获 / Capturable

* 外层函数的**值形参**（`x: T`）与 **`immut` 形参**——值语义快照；
* 外层函数的**局部变量**（含表 / 字符串 / struct / fn 值）——值语义快照；
* **`const` 声明**——常量，无副作用；
* 全局变量（始终可见，不经捕获通道）。

### 2.2 不可捕获（安全区）/ Not capturable (safe zone)

* **`ref` 形参**——**已落地**（见 §3）。捕获它是借用而非副本，闭包逃逸即悬垂引用；
* **`unsafe` 上下文产生的裸指针 / 切片句柄**——沿用既有安全边界（指针类型本身不得出现在安全区）。

### 2.3 unsafe 区放宽 / Relaxed in unsafe

`unsafe func` 体内、或 `unsafe { }` 块内登记的闭包，捕获面放宽：`ref` 形参可捕获（开发者担责，与既有 unsafe 哲学一致）。

---

## 3. 已落地规则：禁止捕获 `ref` 形参 / Landed: no capturing ref parameters

**规则**：安全区（非 unsafe 上下文）中，闭包捕获 `ref` 形参 = 编译错误。

**依据（实测）**：捕获 `ref` 形参走的是**借用**——闭包内对捕获表的写会**回写到调用方**（实测：闭包内 `table_push` 后调用方 `len` 同步变化）。故闭包一旦**逃逸**出声明它的函数，借用所指向的栈帧已销毁 ⇒ **悬垂引用**。

**诊断**：`安全区禁止闭包捕获 ref 形参 'X'（捕获 ref 是借用而非副本，闭包逃逸会导致悬垂引用；需在 unsafe 块内或改用值/immut 形参）`

**实现要点（供维护者）**：捕获分析是**后置批量**的（所有函数检查完后 FIFO 处理 `g_clo_pending`），此时环境全局（`g_curfn` / `g_unsafe_depth`）**已不代表该闭包的外层**。故必须在**登记时**（外层上下文内）把归属记入平行表：

* `cl_owner_sig` —— 闭包索引 → 外层函数签名（供反查形参名与 `ref` 标志）；
* `cl_owner_unsafe` —— 闭包索引 → 登记时是否 unsafe 上下文；
* `sg_defnode` —— 签名 → 声明节点（形参名只存于声明节点，`sg_*` 表只有类型与修饰标志）。

---

## 4. 短闭包（与 p.9.11.34 同源）/ Short lambdas

### 4.1 设计原定形态 `t -> expr` —— **已实现**（2026-09-27）

**早先的判断（`t -> expr` 与管道歧义 ⇒ 不可实现）是错的**：歧义确实存在，但**不在"要求函数值"的位置**——而那些位置是可判定的。规则据此定义：

| 位置 | 判据 | 消歧时机 |
|---|---|---|
| **声明位** `var f: fn(A) -> R = t -> expr` | 标注是 fn 类型 **且** 初始化形如 `ident -> expr` | **解析期**（标注已在手） |
| **赋值位** `f = t -> expr` | 目标类型是 fn 类型 **且** 右值是 `ident -> expr` | **语义期**（目标类型此时才知） |

其余一切情形维持**管道语义不变**（`v = v -> g` 仍按管道求值——回归探针守着）。

两类位置都产出**完整闭包节点**，其中：
* 声明位在解析期直接用标注里的形参/返回类型构造（零语义/IR 改动）；
* 赋值位在语义期构造，为此新增两项**通用能力**：
  * `sstate.new_node_sem` —— 语义期**新建**节点（此前只能就地改写；2 子节点的箭头节点要变成 4 子节点的闭包，必须能新建）；
  * `N_SEM_TYPE` / `S_N_SEM_TYPE` —— **语义期类型引用**节点（`val` = 类型 id）。语义期手上只有类型 id，而复杂类型（fn/表/聚合）**无法逆向构造**为等价 AST 节点；`sgen.parse_generic_type_node` 对该节点直接返回 id，任何类型都能表达。

这两项是**面向后续**的能力：凡"语义期才知要不要展开、且展开需要增子节点"的消糖都要用。

### 4.2 fn 类型上下文省略形参类型（`func` 字面量形态）

闭包字面量在**有 fn 类型上下文**时可省略形参类型——

```
var f: fn(i64) -> i64 = func(t) -> i64 { return t + 1 }
```

**类型来源**：`var` 声明的 fn 类型标注（`FnType` children = `[返回类型, 形参类型...]`，故第 i 个形参 = `children[1+i]`）。**无上下文**时报「闭包形参必须标注类型」，**不静默推断**。

### 4.3 未支持 / Not supported

* **`var f: fn(A) -> R`（无初始化）+ 后续单独赋值**：属解析层对"有标注无初始化变量"的限制（tie 要求变量声明带初始化）。安全放开需要配套的**「读未初始化变量」检查**，该检查目前不存在——故**保持现状而非不安全地开放**。声明位形态一行即可表达同一意图。
* **实参位上下文**（`apply(func(t) -> …, 5)`）的形参类型推定：需把期望类型传过 `infer_expr` 边界，属独立改造。
* **`it` 隐式单参**与单表达式隐式返回（p.9.11.28）的咬合：随后。

---

## 5. 仍待定 / Still open

* **可变捕获标注**：捕获引用类型**即**共享可变状态（见 §1.1），故"可变捕获"本身已经存在，只是**不需要标注**——它由类型（表/映射 vs 标量）直接决定，不依赖位置或修饰符；给一条本可由类型推出的规则再添语法，只会增加书写面而无新信息。仍待定的是**跨执行流**那一步：把携带容器的闭包交给别的执行流时，规范要求「并发写入由书写者负责排除」（§10.5），而编译期能否把这条责任变成**显式门禁**（`share` 域凭据）尚待定案——它涉及「消息传递原语是否要持证」的分类学取舍，见 `domain-classification.md` §3.2。
* **与事件循环线程的交互**：tiu 侧的控件动作参数位（`tiu-ui-widgets.md` §15.4/§15.6）等待本档。本档已给出可用结论：**值语义捕获 + 值形参**在跨线程时天然安全（无共享可变状态）。`ref` 形参不可入动作参数位（本档 §3 已使其编译期不可捕获）；若 tiu 确需跨线程共享状态，走既有 `trm-lite` 的信道 / actor 通道，不经闭包捕获。
* **`immut` 形参捕获**：本档随 unsafe 一并放宽（未单列规则）。只读借用的外部可观察风险低于可写借用（无回写），但其跨线程可观察性仍取决于被借用对象的线程安全——细则随 tiu 定。

---

## 6. 落地状态与缺口 / Landing status and gaps

**已落地**（2026-10-02）：

* 捕获引用类型时发出 **retain** —— 满足 §1.1 的"内存安全"一半（不悬垂）。此前缺失，
  表现为捕获表的闭包被调用即段错误（实测退出码 139）。
* **env 尺寸按真实布局计算**（`agg_ty_size`）—— 修复聚合字段（struct/tuple/数组）捕获时的
  堆越界写（此前按"每字段 8 字节"分配，而字段访问按聚合布局，二者不自洽）。
* **env 首字段放析构入口**（`{drop, cap...}`）+ **闭包值消亡点调用它** —— §1.1 的
  "内存低"在**闭包字面量形态**下已满足。
  * 释放点两处：函数出口（挂进 `tig_tbl_exit_release`，唯一出口析构入口，一处覆盖
    函数尾与 return）、循环回边（复用表变量同款零值哨兵）。
  * 不逃逸判定**复用既有 esc 分析**——其 kill 条件已覆盖全部逃逸形态；且 `f()` 的 callee
    存在节点 name 字段而非子节点，故"调用"不被误判为逃逸。逃逸者一律不释放
    （残余泄漏，绝不产生悬垂）。
  * `drop_<闭包>` 内部自带 null 守卫 ⇒ 释放点可**无条件调用**，调用点零分支、
    不在函数出口处分裂控制流块。
  * 实测：循环 20 万次创建「捕获 200 元素表的闭包字面量」⇒ 峰值从 **326.6MB 降至 8.2MB**；
    探针 `tiec/tests/language/closure_env_release.tie`。

**未落地（已知缺口）**：**「跨函数返回的闭包」的释放**。

* 形态：`var f = mk()`，其中 `mk() -> fn() -> i64` 内部创建并返回闭包（工厂模式）。
  编译器在赋值点**不知道**该闭包是哪个字面量 ⇒ 不知道调用哪个 `drop_<id>`。
* 实测：该形态循环 20 万次 ⇒ 峰值仍 **299.6MB**（残余泄漏）。
* 这正是 **env 首字段（析构入口）的用武之地**：释放点无需知道布局，读 `env[0]` 间接调用
  即可。待补的是**读路径的 null 守卫**（`env` 可能为 null，即无捕获闭包），候选做法：
  （a）生成一个全局辅助函数 `tie_clo_drop_if(env)`（内部 `if (env) ((void(*)(void*))env[0])(env);`），
  释放点无条件调用它——但需解决多编译单元静态链接时的符号唯一性；
  （b）约定所有闭包的 env 恒非 null（无捕获时指向一个静态 env，其析构入口为 no-op），
  释放点即可零守卫直接读 `env[0]`——代价是无捕获闭包不再以 null 表示 env，
  需核查依赖该约定的既有路径。
* 根因是**信息不对称**：env 的布局（捕获了哪些引用、各在哪个字段）**只有创建闭包的函数
  知道**，而闭包值消亡在**持有它的作用域**里；后者拿到的 fn 值只是 `{env, entry}`，
  无从知道如何释放 env 内的引用。
* 因此释放必须由 env **自带**完成信息。候选落地方案（择一，待定）：
  * **env 首字段放析构入口**：env = `{ drop, cap0, ... }`，`drop(env)` 释放各捕获引用并
    free(env)；持有方在闭包值消亡点调用。**风险**：闭包值可被复制（赋值/传参/存容器），
    两个持有方各调一次 drop ⇒ 重复释放。故需配合"仅在**不逃逸**的局部闭包值上发射 drop"
    的保守判定（逃逸者不释放，残余泄漏但安全）。
  * **env 引用计数**：env = `{ rc, cap0, ... }`，复制点 retain、消亡点 release。
    能覆盖逃逸闭包，但需在**全部复制点**插桩，漏一处即错。
* 未落地前，§1.1 的"内存低"应视为**待实现的要求**，而非既有保证。

*EN: Landed: retain on reference capture (the "no dangling" half of memory safety;
its absence previously made closures capturing a table crash on call), and
env sizing by real aggregate layout (fixing an out-of-bounds store for aggregate
captures). Not landed: releasing captured references - the "low memory" property
does not hold yet. Measured: 200k iterations capturing a 200-element table peak
at 326.6 MB, matching the predicted 320 MB of leaked tables, so neither the env
nor the captured tables are reclaimed. The root cause is an information
asymmetry: only the creating function knows the env layout, yet the closure dies
in the holding scope, which sees just {env, entry}. Release therefore has to be
initiable from the env itself. Two candidate designs are listed above (a drop
entry as env's first field, guarded by a conservative non-escaping test; or a
refcount on env with instrumentation at every copy site). Until one lands, "low
memory" in 1.1 is a requirement to implement, not an existing guarantee.*

## 7. 验收 / Acceptance

* 捕获语义七项实测（§1 表）——已由 `g56_capture` 探针覆盖；
* 白名单负例：安全区捕获 `ref` 形参被拒；unafe 内同一代码通过；`immut` 与普通捕获不受影响——已覆盖；
* 回归：`regress-s21` 与基线逐项一致；**自举不动点成立**（同时证明规则不误伤既有代码——tiec 自身闭包无一违反）；
* 临时单参函数：声明位推定可用、无上下文报诊断、显式标注行为不变——已覆盖。
