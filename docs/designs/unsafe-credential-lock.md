# tie unsafe 凭据双锁设计（2026-09-17 定稿）

*EN: tie Unsafe Credential Double-Lock Design (finalized 2026-09-17)*

> **定位**（用户指令）：将凭证系统推广到全体 unsafe，给 unsafe 语法上最后一道安全锁。
> 模型一句话：**unsafe = 门禁上下文 + 域凭据，双锁缺一不可**——「能进 unsafe 块」不再
> 等于「能为所欲为」，每个 unsafe 构造还要持对应域的 move-only 凭据，持证路径全量
> 进入编译期审计清单（Keel 审计链）。
>
> EN: Per user directive: extend the credential system to all of unsafe — the final
> safety lock. One-line model: **unsafe = gate context + domain credential, both
> required** — "being inside an unsafe block" no longer means "can do anything";
> every unsafe construct additionally holds a move-only credential for its domain,
> and every credential path lands in the compile-time audit manifest (Keel audit chain).

## 1. 与现状的关系

*EN: 1. Relation to Current State*

- §7 凭据门禁已覆盖并发越界逃生（域 mem/ext/share：`#[unsafe.*]` 声明属性 +
  `unsafe.get` / `unsafe use g { }` / `unsafe.with` 持证 + 委派/对象绑定/层级回收/审计）；
  §14 其余 unsafe（ptr/alloc/extern/asm/volatile/goto）只有上下文锁、无凭据锁；
- EN: §7 credential gates already cover the concurrency escape hatches (domains mem/ext/share: `#[unsafe.*]` declaration attributes + `unsafe.get` / `unsafe use g { }` / `unsafe.with` holding + delegation/object binding/hierarchical reclamation/audit); the rest of §14 unsafe (ptr/alloc/extern/asm/volatile/goto) has only the context lock, no credential lock;

- 本设计 = 把 §7 机制**推广为全体 unsafe 的统一模型**，并将原四期「guard<mem>/<ext>
  全凭据面」计划提前落地为 unsafe 的最后一道锁；
- EN: this design **generalizes the §7 mechanism into the unified model for all unsafe**, pulling the original phase-4 "guard<mem>/<ext> full-credential surface" plan forward as unsafe's final lock;

- 基础设施全部现成：凭据 = move-only 值（`guard<cap>` 类型，§16 表）、审计链 =
  Keel 注册表/审计器（p.7.1.5）、`unsafe use`/`unsafe.with` 语法已定稿（§7.1）。
- EN: all infrastructure exists: credentials are move-only values (`guard<cap>`, §16), the audit chain is the Keel registry/auditor (p.7.1.5), and the `unsafe use`/`unsafe.with` syntax is finalized (§7.1).

## 2. 域映射（五域：mem / ext / share / raw / lock）

*EN: 2. Domain Mapping (Five Domains: mem / ext / share / raw / lock)*

| 域 | 凭据 | 覆盖构造 | 危害面 |
| --- | --- | --- | --- |
| `mem` | `guard<mem>` | `*p` 解引 / 指针算术 / `alloc(n)` / `addr_of` | 悬垂 / 越界 / 未初始化 |
| `ext` | `guard<ext>` | `extern fn` 调用（含 C 互操作全链） | 外部效应不可静态验证 |
| `share` | `guard<share>` | 跨 actor 共享内存（§7.1.1 A 组） | 数据竞争 |
| `raw` | `guard<raw>` | `asm!` / volatile_load/store（MMIO）/ `unsafe goto #x` | 裸机器面：任意寄存器内存 / 设备内存 / 裸跳转 |
| `lock` | `guard<lock>` | **表访问去锁**（`t[i]` 读/写、`table_push`、`for` 遍历绕过运行时表锁） | 数据竞争（绕过并发保护） |

*EN: five domains — mem (dangling/OOB/uninitialized), ext (external code the language cannot check), share (cross-stream sharing, races), raw (bare machine: asm / MMIO / raw jumps), lock (bypassing the runtime table lock, races).*

- **每个构造属于哪个域，逐条归类见 `domain-classification.md`（2026-10-01 定案）**——
  本文只定义域与持证形态，「哪处门禁归哪个域」是那份文档的职责，也是「域匹配」的前置。
- `trm` 域**已删除**（2026-10-01）：它在实现里没有任何门禁承载，且 trm 引擎已废弃；
  保留一个永空的域会让审计清单永远有一行无从填充。将来执行流原语需要门禁时作为新域加回。
- `raw` 为本次新增域：`unsafe goto #x` 降级到 LLVM `br` 即裸跳转，与 asm/MMIO 同属
  「绕过语言执行模型直接操作机器」——归并同一域，域分类学保持完备且不膨胀；
- EN: `raw` is the one new domain: `unsafe goto #x` lowers to an LLVM `br` — a bare jump, same class as asm/MMIO ("bypass the language's execution model, operate the machine directly") — merged into one domain, keeping the taxonomy complete without bloat;

- `lock` 为**本期新增域**（r.1.6.7，2026-09-30 落地）：能力面 = 绕过运行时表锁，
  危害面 = 数据竞争。与 `share` 域**语义分开**——`share` 管「把内存共享出去」
  （跨 actor 共享内存逃生口），`lock` 管「主动去掉并发保护」；二者危害面同属数据竞争，
  但**意图不同**，分开记账让审计清单能区分「共享」与「去锁」两种行为。
  该域**已实现**（见 §6）。
（atomic/slice 下标/ptr 声明/repr(C) 声明）**不需要**任何
  凭据——双锁只锁真正的危险构造。
- EN: the p.9.11.35 reclassified safe surfaces (atomics/slice indexing/ptr values/repr(C) declarations) need **no** credential — the double lock only guards genuinely dangerous constructs.

## 3. 双锁语义（定稿）

*EN: 3. Double-Lock Semantics (Finalized)*

- **锁一（上下文）**：构造必须位于 `unsafe fn` / `unsafe { }` 内（现状不变）；
- EN: **Lock one (context)**: the construct must sit inside `unsafe fn` / `unsafe { }` (unchanged);

- **锁二（凭据）**：当前作用域必须已持有该构造对应域的凭据。两种持证形态沿用 §7.1：
  - 函数级：`#[unsafe.mem] func f(...)`（隐式持证，整函数作用域，签名可见——调用方
    审计面）；
  - 块级：`unsafe use g = unsafe.get(mem) { ... }` / `unsafe.with(mem) { ... }`（细粒度，
    凭据 move 进块、块尾回收）；
- EN: **Lock two (credential)**: the enclosing scope must hold a credential for the construct's domain. Two holding forms per §7.1: function-level `#[unsafe.mem] func f(...)` (implicit hold, whole-function scope, visible in the signature for caller-side audit) and block-level `unsafe use g = unsafe.get(mem) { ... }` / `unsafe.with(mem) { ... }` (fine-grained; the credential moves into the block and is reclaimed at block end);

- **凭据规则**：`guard<cap>` move-only——拷贝凭据 = 编译诊断；委派/对象绑定/层级回收
  沿用 §7.1 既有语义；作用域内未使用对应域构造的凭据 → 编译告警（凭据挂空）；
- EN: **Credential rules**: `guard<cap>` is move-only — copying a credential is a compile diagnostic; delegation/object binding/hierarchical reclamation follow §7.1 as-is; a held credential whose domain is never used in scope → compiler warning (idle credential);

- **文件级快捷**：文件头 `type tie<logic> + unsafe` 角色扩展（S1.4）升级为
  `type tie<logic> + unsafe[mem,ext]`——整仓平台桥/FFI 模块按域授权，免逐函数标注；
  审计清单仍逐构造落盘；
- EN: **File-level shortcut**: the file-header role extension (S1.4) upgrades to `type tie<logic> + unsafe[mem,ext]` — repo-wide platform-bridge/FFI modules get per-domain authorization without per-function annotation; the audit manifest still records every construct;

- **审计清单（最后一道锁的产出）**：tiec 编译期输出 unsafe-audit 清单——每个 unsafe
  构造一行（位置 / 域 / 凭据获取路径 / 签名链），接 Keel 审计链（p.7.1.5）入指纹树；
  「谁在哪持什么证干了什么」全程可审计、零运行时。
- EN: **Audit manifest (the final lock's output)**: tiec emits an unsafe-audit manifest at compile time — one line per unsafe construct (location / domain / credential acquisition path / signature chain), fed into the Keel audit chain's fingerprint tree (p.7.1.5); "who held what credential where, doing what" is fully auditable at zero runtime cost.

## 4. 迁移与兼容

*EN: 4. Migration and Compatibility*

- **破坏性变更，无兼容期**（对齐 p.9.0 命名迁移纪律：趁未发行彻底切）：存量 unsafe
  位机械补 `#[unsafe.<域>]` 或 `unsafe.with`；自举链（tiec 自举）自身的 unsafe 位同批
  迁移，作为迁移完备性的实证验收；
- EN: **Breaking change, no grace period** (aligned with the p.9.0 naming-migration discipline: switch thoroughly pre-release): existing unsafe sites mechanically add `#[unsafe.<domain>]` or `unsafe.with`; the bootstrap chain's own unsafe sites migrate in the same batch, serving as the empirical acceptance of migration completeness;

- `unsafe { }` 裸上下文写法保留但降级为「只进门、无钥匙」——编译报
  「unsafe 需 <域> 凭据」，提示两种持证形态；诊断即迁移指南；
- EN: bare `unsafe { }` stays legal as syntax but downgrades to "door without a key" — the compiler reports「unsafe 需 <域> 凭据」(unsafe requires a <domain> credential) with a hint for both holding forms; the diagnostics double as the migration guide;

- concurrency-model §7 与 trm-final-design §1.2 的 7 类能力清单在落地时按五域映射
  修订（share 语义不变，mem/ext 从计划转正，raw 并入，trm 删除）。
- EN: concurrency-model §7 and the trm-final-design §1.2 seven-capability catalog get revised to the five-domain mapping at landing (share semantics unchanged; mem/ext move from plan to reality; raw merged in; trm removed).

## 5. 验收

*EN: 5. Acceptance*

- 负例探针：五域各构造无凭据 → 「unsafe 需 <域> 凭据」诊断；凭据拷贝 → move 诊断；
  错域凭据（持 `mem` 调 `extern`）→ 域不匹配诊断；
- EN: Negative probes: each domain's construct without a credential → the「unsafe 需 <域> 凭据」diagnostic; credential copy → move diagnostic; wrong-domain credential (holding `mem` while calling `extern`) → domain-mismatch diagnostic;

- 正例探针：函数级/块级/文件级三种持证 × 五域矩阵；凭据 move 委派 + 层级回收；
  挂空凭据告警；
- EN: Positive probes: function/block/file holding forms × five-domain matrix; credential move-delegation + hierarchical reclamation; idle-credential warning;

- 审计清单：unsafe 位与清单逐行对账（漏记 = 失败）；清单入 Keel 指纹树验证；
- EN: Audit manifest: line-by-line reconciliation between unsafe sites and the manifest (any miss = failure); manifest verified into the Keel fingerprint tree;

- 自举链迁移完备（tiec 自举零裸 unsafe）+ 自举不动点 + 回归基线不劣化。
- EN: Bootstrap-chain migration completeness (zero bare unsafe in self-hosting) + bootstrap fixpoint + no regression-baseline degradation.

## 6. lock 域落地记录（r.1.6.7，2026-09-30）

*EN: 6. lock Domain Landing Record*

**已实现的语法形态**（四种持证形态全部可用）：

| 形态 | 语法 | 生效范围 |
| --- | --- | --- |
| 块级临时凭据 | `unsafe { unsafe with(lock) { ... } }` | 块内表访问去锁 |
| 块级绑证 | `unsafe { var g: guard<lock> = unsafe.get(lock); unsafe use g { ... } }` | 块内表访问去锁 |
| 函数级 | `#[unsafe.lock] func f(...)` | 整函数体（隐式持证） |
| 文件级 | `type tie<logic, unsafe:lock>` | **本文件**所有函数 |

*EN: four holding forms implemented: block-scoped temporary credential
(`unsafe with(lock)`), block-scoped bound credential (`unsafe use g` with
`g: guard<lock>`), function-level (`#[unsafe.lock]`), and file-level
(`type tie<logic, unsafe:lock>`).*

**与本文档原设计的差异（实现形态以本表为准）**：

- 文件级授权在实现中走**角色修饰参数**：`type tie<logic, unsafe:lock>`（逗号 +
  冒号参数），而非本文档 §3 早期草案的 `type tie<logic> + unsafe[mem,ext]` 写法
  ——后者与逗号分词冲突（`unsafe[mem,ext]` 会被拆成两段）。S1.4 的多角色体系
  （`基础[:参数][, 修饰...]`）已就位，故直接沿用。
- 四种形态**统一经 `guard<lock>` 域**判别（`types.is_lock_guard`），块级绑证形态
  读凭据变量的静态类型决定是否去锁 —— 即「持什么域的证，干什么域的事」。

**范围精确性（关键安全属性）**：文件级授权**只作用于主输入文件**，**不波及
`import` 的模块**。实现要点：`parser.parse_ast` 只对主输入文件调用一次，文件级授权
在 parser 内展开为「本文件每个函数隐式持 lock 域」，import 模块走语义层另一条解析
路径、读不到该标志。探针 `tests/language/lock_file_auth.tie` 断言：主文件函数走
免锁入口 `tbl_push_nl`，而同编译单元内 import 的模块函数**仍走加锁** `tbl_push`。

**凭据不跨函数继承**：闭包体 / port 方法体是独立函数，其内 lock 作用域清零 ——
否则闭包若被 `spawn` / 存全局，另一执行流会对同一张表做免锁访问，形成真实竞态。
探针 `tests/language/lock_credential.tie` 的 `no_closure_inherit` 断言此项。

**与编译期自动独占分析的关系**：`compiler/backend/irgen_esc.tie` 有两条并列的去锁
来源，统一经单一判定入口 `esc_take` 裁决：
1. **自动**：编译器静态证明该表独占（局部 + 新鲜初值 + 句柄未离开本次调用）⇒ 免锁；
2. **显式**：处于持 `lock` 凭据的作用域 ⇒ 免锁（开发者声明，责任归开发者）。

审计开关 `--esc-audit` 对两条来源**分别打印**（`独占免锁` / `凭据去锁`），
`_tiec_verify/esc_safety.sh` 双向断言 22 条不变量（13 条自动路径 + 9 条凭据路径）。

**验证**：三阶不动点 `5c11868db64ef056` 并升格；s21 回归 PASS=161 FAIL=8 SKIP=2
（FAIL 集合与基线逐字一致，PASS 增量来自本特性新增探针）。

*EN: The four forms are implemented and verified: block/function/file-level
holding; file-level scope is provably confined to the main input file (imported
modules keep locking, asserted via IR inspection); credentials do not cross
function boundaries (closure bodies reset the lock scope, preventing a spawned
closure from racing). Two de-locking sources (compile-time exclusivity proof and
explicit credential) share one decision point, are printed separately under
`--esc-audit`, and 22 invariants are asserted by `_tiec_verify/esc_safety.sh`.*
