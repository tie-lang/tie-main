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
| 闭包内改捕获表的**内容**（`table_push`） | 外层 `len` **不变** | **表也是按值捕获**（无别名） |
| 捕获 `const` | 可捕获 | const 可捕获 |
| **捕获 `ref` 形参** | **闭包内写会回写到调用方** | **借用例外**（见 §3——这是唯一非值语义） |

关键结论：**除 `ref` 形参外，捕获一律是值语义**（快照/副本），故不存在"共享可变状态"这一类经典闭包缺陷。

> EN: Apart from `ref` parameters, capture is uniformly by value, so there is
> no shared-mutable-state class of closure bug. `ref` parameters are the one
> borrow exception.

---

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

## 4. 临时单参函数（与 p.9.11.34 同源）/ Temporary single-arg fn

设计原定形态 `f = t -> expr` **不可实现**：表达式位的 `t -> expr` 已是数据流管道（`t` 已知时读作管道、未声明时想读作形参），而"`t` 是否已声明"解析期不可知 ⇒ 无判据。花括号形态 `{ t -> expr }` 与闭包体的**延迟回填**机制冲突（体是语句块，`t -> expr` 不是合法语句）。

**落地形态**：闭包字面量在**有 fn 类型上下文**时省略形参类型——

```
var f: fn(i64) -> i64 = func(t) -> i64 { return t + 1 }
```

**类型来源**：`var` 声明的 fn 类型标注（`FnType` children = `[返回类型, 形参类型...]`，故第 i 个形参 = `children[1+i]`）。**无上下文**时报「闭包形参必须标注类型」，**不静默推断**。

**待后续**：实参位上下文（`apply(func(t) -> …, 5)`）的形参类型推定需把期望类型传过 `infer_expr` 边界，属独立改造；短闭包 `it`（隐式单参）与单表达式隐式返回（p.9.11.28）的咬合同样随后。

---

## 5. 仍待定 / Still open

* **可变捕获标注**：本档冻结的语义是「捕获一律值语义」，故**当前不存在可变捕获**——没有可标注之物。若将来引入"共享可变捕获"（多闭包共享一份可变状态），需先定标注语法与线程安全规则；在此之前不引入标注，以免为不存在的能力增加语法面。
* **与事件循环线程的交互**：tiu 侧的控件动作参数位（`tiu-ui-widgets.md` §15.4/§15.6）等待本档。本档已给出可用结论：**值语义捕获 + 值形参**在跨线程时天然安全（无共享可变状态）。`ref` 形参不可入动作参数位（本档 §3 已使其编译期不可捕获）；若 tiu 确需跨线程共享状态，走既有 `trm-lite` 的信道 / actor 通道，不经闭包捕获。
* **`immut` 形参捕获**：本档随 unsafe 一并放宽（未单列规则）。只读借用的外部可观察风险低于可写借用（无回写），但其跨线程可观察性仍取决于被借用对象的线程安全——细则随 tiu 定。

---

## 6. 验收 / Acceptance

* 捕获语义七项实测（§1 表）——已由 `g56_capture` 探针覆盖；
* 白名单负例：安全区捕获 `ref` 形参被拒；unafe 内同一代码通过；`immut` 与普通捕获不受影响——已覆盖；
* 回归：`regress-s21` 与基线逐项一致；**自举不动点成立**（同时证明规则不误伤既有代码——tiec 自身闭包无一违反）；
* 临时单参函数：声明位推定可用、无上下文报诊断、显式标注行为不变——已覆盖。
