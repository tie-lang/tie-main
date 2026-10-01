# tie 能力域归类（2026-10-01 定案）

*EN: tie Capability Domain Classification (finalized 2026-10-01)*

> **定位**：`unsafe-credential-lock.md` 定义了「unsafe = 门禁上下文 + 域凭据」的双锁模型，
> 但**没有规定每个危险构造属于哪个域**——而「域匹配」（持 X 域证才能做 X 域操作）必须先有
> 这份归类才能实现。本文补齐这一层：把编译器里每一处 unsafe 门禁点位逐条归入能力域。
>
> EN: `unsafe-credential-lock.md` defines the double lock ("unsafe = gate context +
> domain credential") but never says which dangerous construct belongs to which
> domain — and domain matching (holding a mem credential to do mem work) cannot be
> implemented without that. This document supplies it: every unsafe gate site in the
> compiler is assigned to a domain.

## 1. 归类原则

*EN: 1. Classification Principle*

归类的依据**不是「哪些构造看起来危险」，而是「该构造一旦误用，会引发哪一种未定义行为」**。
域 = 危害面的分类学，一个域对应一种 UB 类别。

*EN: The basis for classification is not "which constructs look dangerous" but
"which class of undefined behaviour a construct causes when misused". A domain is a
hazard taxonomy — one domain, one class of UB.*

推论（本轮的三个判断都由此推出）：

- 同一 UB 类别的构造**必须**同域，哪怕它们的语法形态差别很大（`deref` 与 `memcpy`
  一个是解引用一个是块拷贝，但误用后果同为越界 ⇒ 同归 mem）；
- 不引发 UB 的构造**一律不入域**，哪怕它「看起来底层」（原子操作、系统调用、类型双关）；
- 一个域若**没有任何承载原语**，它就不该存在（见 §4 的 trm 处置）。

进一步把判据操作化（2026-10-01 追加）：**一个操作需要持证，当且仅当它要求书写者先满足
某个安全前提**。前提可以是「指针有效」，也可以是「内存已初始化」「未重复释放」
「长度不越界」。没有前提的操作即便产出的值可能无效，也不构成独立危害面——因为让那个
无效值真正出事的是**使用**它的操作，而那个操作自有门禁。

*EN: Operationalized: an operation requires a credential iff it imposes a
precondition on the caller — pointer validity, memory initialized, not already freed,
length in bounds. An operation with no such precondition cannot be an independent
hazard, because only a *use* of its (possibly invalid) result can go wrong, and that
use has its own gate.*

*EN: Corollaries: constructs sharing a UB class must share a domain regardless of
syntactic distance; constructs that cannot cause UB are never assigned a domain no
matter how low-level they look; and a domain with no carrier should not exist.*

## 2. 域与承载（定案）

*EN: 2. Domains and Their Carriers (Finalized)*

| 域 | 危害面（UB 类别） | 承载 |
| --- | --- | --- |
| `mem` | 悬垂 / 越界 / 未初始化 | `deref` `deref_write`（须有效指针）· `alloc` `free`（未初始化/未重复释放）· `memcpy` `memset`（长度不越界）、`cstr_to_string`、port 提升（借用） |
| `ext` | 外部效应不能静态验证 | `extern fn` 调用、`cb_ptr`、`load_library`、`get_proc`、`dyn_call`、`dyn_call_p` |
| `share` | 数据竞争（跨执行流共享可变数据） | **暂无**（见 §3.2） |
| `raw` | 绕过编译器对代码的假设 | `volatile_load` `volatile_store`、`asm!`、`unsafe goto #x` |
| `lock` | 绕过并发保护 | **不是原语而是作用域**：持 `guard<lock>` 时容器访问走免锁入口（见 §3.3） |

*EN: five domains — mem (dangling/OOB/uninit), ext (unverifiable external
effects), share (data race via cross-execution-stream sharing), raw (bypassing the
compiler's assumptions), lock (bypassing concurrency protection).*

两个域的门禁承载已全部落地（2026-10-01）：`mem` 为 `deref` `deref_write` `alloc`
`free` `memcpy` `memset` `cstr_to_string`，`ext` 为 `extern fn` 调用 `cb_ptr`
`load_library` `get_proc` `dyn_call` `dyn_call_p`。域内尚余一项待补：port 提升
（已门禁但**域标签未接**，见 §6）。

### 逐项判断记录（有争议的都在这里）

*EN: Item-by-item notes for the judgment calls*

- **`memcpy` / `memset` 归 `mem` 而非 `raw`**：它们操作的是 tie 可见的缓冲，误用后果
  是越界写（mem 的危害面），**不绕过任何编译器假设**（raw 的判据）。「无边界检查」
  不等于「裸机器面」。
- **`addr_of` / `addr_of_field` / `ptr_add` / `ptr_to_int` / `int_to_ptr` 已全部移出
  门禁（2026-10-01）**：它们**产出/计算指针值**，是纯值运算、不触碰内存，也没有任何
  安全前提——结果即便无效，也只在被解引用时才成为问题，而解引用另有门禁。
  边界因此可一句话概括：**产出指针值安全，用指针触碰内存须 unsafe**。
  与 Rust 的判法一致（`addr_of!` / `ptr as usize` / `without_provenance` /
  `wrapping_offset` 都是安全函数）。
- **原子操作不入任何域**：不产生 UB（内存序写错是正确性 bug，非内存不安全），与 Rust 同判。
- **系统调用族不入 `ext`**：见 §5。
- **`volatile_*` 归 `raw` 而非 `mem`**：它的语义是「这次访存不可被优化」，用于 MMIO——
  误用后果不是越界而是**编译器假设被打破** ⇒ raw。

*EN: memcpy/memset are mem (out-of-bounds write, not compiler-assumption
violation); the five pointer-value ops (addr_of, addr_of_field, ptr_add, ptr_to_int,
int_to_ptr) have left the gate — producing a pointer value is a pure value operation
with no precondition, so the boundary reads "producing a pointer is safe, using one to
touch memory is not"; atomics belong to no domain; syscalls belong to no domain (§5);
volatile is raw.*

## 3. 三个结构性决定

*EN: 3. Three Structural Decisions*

### 3.1 `trm` 域删除（五域定案）

*EN: 3.1 The trm domain is removed (five domains)*

`trm`（执行模型越界）在实现里**没有任何门禁承载**，且 trm 引擎已废弃。保留一个永空的域
会让「域匹配」的审计清单永远有一行无从填充，而域分类学的价值正在于**完备且不膨胀**。

将来若执行流原语需要门禁（例如裸调度接入），届时作为**新域**加回——成本与现在保留占位相同，
但不会有「这个域到底管什么」的长期歧义。属性白名单里的 `trm` 字符串与规范 §11.6 的表行
一并移除。

*EN: trm has no gate site and its engine is deprecated. An always-empty domain
leaves a permanently unfillable line in the audit manifest, while the taxonomy's
value is being complete without bloat. If execution-stream primitives ever need a
gate, it returns as a new domain at the same cost.*

### 3.2 `share` 域保留但暂无承载

*EN: 3.2 share stays, currently without a carrier*

候选承载 `spawn` / `ch_*` / `wg_*` **实测全部在安全路径**（通道传的是值，类型系统已保证
安全）。tie 的执行体模型是**消息传递**，不共享内存，因此「跨执行流共享可变数据」目前
**没有对应语法**。

给这些原语加门禁会让所有并发代码都要持凭据（破坏性），且把「消息传递」与「共享内存」
混为一类——而二者的危害面并不相同。故 share 保留为域，待「共享可变数据」在语言里落地时
再挂承载。

*EN: The candidate carriers spawn/ch_*/wg_* were measured to be on the safe path —
channels pass values, and the type system already makes that safe. tie's execution
model is message passing, not shared memory, so "cross-stream shared mutable data"
has no syntax yet. Gating these primitives would force credentials onto all concurrent
code and conflate message passing with shared memory. share stays reserved.*

### 3.3 `lock` 的承载是作用域，不是原语

*EN: 3.3 lock's carrier is a scope, not a primitive*

`lock` 域没有对应的内置函数——它的形态是**作用域持证**：进入持 `guard<lock>` 的作用域后，
范围内的容器访问走免锁入口。因此「域匹配」对 lock 的落地形态与其他四域不同：不需要在
内置清单里挂项，而是由凭据类型驱动 codegen（已在 r.1.6.7 落地）。

*EN: lock has no builtin; it is scope-based — inside a scope holding guard<lock>,
container accesses take the lock-free entry points. Domain matching therefore lands
differently for lock: no builtin-list entry, credential-typed codegen instead.*

## 4. 与门禁的关系（归类是域匹配的前置）

*EN: 4. Relation to Gates — Classification Precedes Domain Matching*

编译器共有 12 处 unsafe 门禁点位，归类后每处都有唯一域标签：

| 门禁点位 | 域 |
| --- | --- |
| `sinfer_ret_q2.tie` 内置清单（11 项 mem + 2 项 raw） | mem / raw |
| `sinfer_ie_ie2.tie` `asm!` | raw |
| `scheck_ie_ie2.tie` `unsafe goto` | raw |
| `scheck_q3.tie` port 提升 | mem |
| `sinfer_q3.tie` unsafe 函数/方法/命名空间函数调用（3 处） | 被调者声明的域 |
| `sinfer_ret_q2.tie` extern 函数调用 | ext |
| `scheck_ie_ie1.tie` / `sinfer_ie_ie3.tie` 凭据机制自身（`unsafe use`/`with`/`get`/`revoke`） | 无域（凭据机器） |
| 文件头/函数级属性授权 | 其标注的域 |

*EN: All 12 gate sites, each now carrying a unique domain label.*

**「域匹配」的判定规则**（实现时的落点，本轮不实现）：

1. 构造入 unsafe 上下文（锁一，现状不变）；
2. 当前作用域须持有**该构造所属域**的凭据（锁二）；
3. 域不符 → 诊断「持 `<A>` 域凭据不能做 `<B>` 域操作」。

*EN: Domain matching = gate context (unchanged) + a credential for the domain the
construct belongs to; a mismatch diagnoses.*

## 5. `ext` 的界定：C 互操作边界，不含系统调用族

*EN: 5. ext Means the C-Interop Boundary, Not the Syscall Family*

设计文档早期措辞把 `ext` 描述为「调用外部函数——包括系统调用与第三方库」。**实测与该
措辞相反**：`file_*` / `net_*` / `get_env` / `set_env` / `time_now` / `rand_range` /
`exec_output` / `http_get` / `eval` **全部在安全路径**（无需 unsafe 即可编译运行）。

**这是正确的，不改**。理由：规范 §11 自己规定「对系统调用与 C 库的封装应当集中在少数
模块内，其余代码使用封装后的安全接口」——内置 syscall 族**正是那个封装后的安全接口**
（有类型、有边界检查、失败语义明确）。既然语言已经替使用者封装好了，再要求凭据等于
否定封装的价值。

`ext` 的承载限定为**编译器无法验证的三类**：

- `extern fn` 调用：用户自己声明的 C 符号，签名与行为无从核对；
- `cb_ptr`：把 tie 函数交给 C，控制流离开语言管辖；
- **动态链接全链**：`load_library`（装载任意库）→ `get_proc`（取符号地址）→
  `dyn_call` / `dyn_call_p`（按地址调用）。其中 `dyn_call` 是这一族里最直接的
  危险面——它按整数地址调用任意函数，签名与返回值都由书写者断言。

> 归类补记：首次归类时这一族只列出了 `cb_ptr` 与 `load_library`，**漏了
> `get_proc` / `dyn_call` / `dyn_call_p`**——是逐个门禁点核对时（解释器的内置分派
> 里同时出现这五项）才发现的。教训：归类要**按机制成组**找，别按印象点名字。

*EN: The early wording said ext covers syscalls; measurement shows the opposite —
the whole syscall family is on the safe path, and that is correct and stays. The spec
itself prescribes wrapping syscalls behind safe interfaces, and the builtins ARE that
wrapper. ext is narrowed to the three things the compiler cannot verify: extern fn
calls, cb_ptr, and load_library.*

## 6. 归类缺口与处置

*EN: 6. Classification Gaps and Their Disposition*

| 构造 | 处置 | 状态 |
| --- | --- | --- |
| `cstr_to_string` | 归 `mem`，新增门禁 | **已落地**（2026-10-01） |
| `cb_ptr` | 归 `ext`，新增门禁 | **已落地** |
| `load_library` | 归 `ext`，新增门禁 | **已落地** |
| `get_proc` / `dyn_call` / `dyn_call_p` | 归 `ext`（归类时补入），新增门禁 | **已落地** |
| port 提升（struct → port） | 归 `mem`；门禁已在，**域标签未接** | 待办 |

本轮新增的六项门禁全部落在同一个内置清单（`sinfer_ret_q2.tie`），且编译器自身的
调用点已同批迁移——**用新编译器编译自身通过**，即迁移完备（对齐
`unsafe-credential-lock.md` §4 的验收口径）。

*EN: the six gates landed in one builtin list, and the compiler's own call sites
were migrated in the same batch - compiling the compiler with the new compiler
passes, which is the migration-completeness check. Only port promotion remains (gated
but without a domain label).*

## 7. 待实现

*EN: 7. Not Yet Implemented*

0. **迁移影响面**：见 `domain-matching-impact.md`——实测需迁移的调用点只分布在
   **5 个文件**（tlib/std 四个 + tiec 自身一个），且全部整文件同域，**可用文件级授权
   以「改 5 行」覆盖**。推进分三步：补前置（不破坏）→ 迁移 5 文件（靠自编译验证完备）
   → 打开强制（此时已无新失败）。
1. **域匹配判定**（§4 规则）——本归类是其前置，现已具备；
2. ~~六项新增门禁~~ **已完成**（2026-10-01）：`cstr_to_string` → mem；
   `cb_ptr` / `load_library` / `get_proc` / `dyn_call` / `dyn_call_p` → ext；
3. ~~`trm` 移除的连带清理~~ **已完成**：规范 §11.6 表行、凭据设计文档的域表、
   以及 `#[unsafe.*]` 属性白名单（改为 mem/ext/share/raw/lock 五域，不再接受
   `#[unsafe.trm]`）；
4. **端口提升的域标签**——门禁已在（`scheck_q3.tie`），但未走内置清单，需在
   实现域匹配时一并接线。

*EN: domain matching; the three new gates; the trm cleanup.*
