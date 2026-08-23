# guard<cap> 凭据委派（delegate）设计——第 1 批：同域派生

- **日期**：2026-08-23
- **状态**：设计定稿（待评审）
- **范围**：仅实现 `g.delegate(cap')` 委派/衰减操作，**同域派生**；不做 branch/revoke/audit（后续批次）。
- **依据**：concurrency-model §7.1.1 / unsafe-model §13.2 CommonOps（`var g2 = g.delegate(mem)`）。

## 1. 背景与现状

一期已落 `guard<cap>` 最小闭环：`unsafe.get(cap)` / `unsafe use g {}` / `unsafe with(cap) {}` /
`#[unsafe.share]`。其中 cap ∈ {`share`, `mem`, `ext`} 三域。当前 `guard` 是**纯编译期类型标记**
（cap 字段仅用于类型/门禁，无运行时守卫对象、无层级/活性状态）。

本批补 `delegate`：把「越界权」在**同能力域**内派生成语义上独立的新凭据，体现「最小权限移交」。

## 2. 语义（同域派生，move 式）

```tie
var g  = unsafe.get(share)          // 源凭据（move-only）
var g2 = g.delegate(share)          // 派生：消费 g，返回新 guard<share>；此后 g 作废
func helper(buf, g: guard<share>)   // 把 g2 move 交给帮手，最小权限移交
```

规则：

1. **move 式派生**：`g.delegate(cap')` 消费源凭据 `g`，返回一张**新的** `guard<cap'>`。
   调用后 `g` 视为已 move（move-only 语义，smove 标记，后续使用报错）。
2. **同域校验**：`cap' == cap_of_g`，否则编译期报错（本期不做跨域强弱序）。
3. **返回值**：`guard<cap'>`（== `guard<cap_of_g>`）。
4. 派生出的凭据与源在**同一能力域**，能力不扩大；仅体现凭据权的独立移交。
5. 期 batch 内 `guard` 仍为类型标记，**不引入运行时守卫对象、分支/撤销/审计状态**。

## 3. 语法

`g.delegate(cap)`——cap 为能力名（`share` / `mem` / `ext` 标识符）。在表达式位置作为对
`guard` 类型值的**方法式调用**解析（复用 `g.method(...)` 调用解析路径，方法名 `delegate`
为 guard 内建，能力参数为标识符）。

## 4. 编译期检查（规则 + 错误用例）

- 接收者 `g` 类型必须是 `guard<cap>`；否则（对普通值调 `delegate`）→ 报错。
- `cap'` 必须是合法能力名（share/mem/ext）；否则 → 报错「能力域必须是 share/mem/ext」。
- **同域**：`cap' != cap` → 报错「delegate 只能同域派生（guard<cap> 不能委派为 guard<cap'>）」。
- **move 检查**：`var g2 = g.delegate(cap)` 后 `g` 被 move，后续再用 `g` → 已 move 报错
  （复用 smove 现有 move 标记机制）。
- 仅 unsafe 上下文可调用（受限处，与 `unsafe.get` 一致；delegate 源 guard 本身就只在 unsafe 中取得）。

**正例** `tests/m6_actor/guard_delegate_pos.tie`：
`unsafe.get(share)` → `delegate(share)` → 把派生凭据 move 传给 `pub unsafe fn helper(…, g: guard<share>)`，
块内 `unsafe use g {}` 有效，helper 内完成读写断言。

**负例**：
- `g.delegate(mem)`（跨域）→ 报错；
- `unsafe.get(share).delegate(share)` 后再用源 → 已 move 报错；
- 对非 guard 值调 `.delegate(...)` → 报错；
- 安全上下文内 `delegate` → 报错。

## 5. 实现落点（第 1 批同域，纯编译期）

| 层 | 改动 |
| --- | --- |
| 解析 | 识别 guard 值上的 `.delegate(cap)` 方法式调用（cap=标识符），产出专用 AST 节点或走方法调用特殊分支 |
| 类型(sinfer) | 校验接收者为 guard、能力名合法、同域；node_types 记 `guard<cap'>` |
| 语义(scheck) | 同上域/能力名校验；仅在 unsafe 上下文判可正则通过（接收者本身即 guard 类型即已受限） |
| 移动(smove) | 把 `g` 标记为 move（delegate 消费源） |
| IR(irgen) | guard 本期无运行时表示 → 派生表达式不需运行时指令（返回哑值，类型即传递的语义） |
| 文档 | unsafe-model §13.2/13.3 标注「delegate 第1批：同域派生已实现」 |

> 注：因 `guard` 本期为类型标记、无运行时对象，`delegate` 派生是**编译期纯变换**（类型 + move 标记）
> 而非分配新运行时凭据——真正的运行时守卫对象、branch/revoke/audit 仍在后续批次引入。

## 6. 验收

- `guard_delegate_pos.tie` 编译通过且运行行为正确（派生凭据可 move 交帮手、帮手持证越界）；
- 上述负例全部编译期拒绝，错误信息含「同域派生」或「已 move」等关键提示；
- 既有 `actor_a5_guard.tie`（get/use/with）零回归；
- m6_actor 全量正负例回归通过。

## 7. 后续（不在本批）

- `branch()` / `unsafe.revoke(g)` 层级派生与级联撤销——需引入运行时守卫对象（父链/活性位）；
- `unsafe.audit(g)` 调用链审计；
- 跨域衰减强弱序定义（若需要）；
- atomic 弱序凭据门禁。