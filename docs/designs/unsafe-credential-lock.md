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

## 7. 凭据 move-only 落地记录（r.1.6.7，2026-10-01）

*EN: 7. Credential Move-Only Landing Record*

**规范依据**：§11.6 早已写明「凭据是一类特殊的值：它可以转移，但不能复制——因此
同一时刻只有一处持有它，不存在权限被悄悄扩散的情形」。本轮把这个约束从规范文字
变成编译器强制。

**实现前的真实缺口**：移动语义检查（`frontend/smove.tie`）对每个移动位置只做
「标记 moved」而**不检查是否已 moved**。于是 `var g2 = g; var g3 = g` 编译通过
—— 同一份凭据出现两个持有者，正是规范要杜绝的「权限被悄悄扩散」。缺口**不限于
凭据**：堆类型（string/table/map）同样受影响（同一份所有权两个持有者 = 二次释放
/ 别名写），只是从未被开关打开过。

**修法（三处）**：

1. `guard<cap>` 纳入移动跟踪 —— `smove.is_owned` 增加凭据分支；含凭据字段的聚合
   经字段递归自然获得 move-only 性质（这正是它应有的语义）。
2. **移动动作收敛为唯一入口 `move_var(nid, node)`** —— 先查已 moved 再标记。
   此前 6 个移动位置（var 声明 / 赋值 / 实参 / return / 字段赋值 / 下标赋值）各自
   内联「只标记」，收敛后两处漏洞一起修好，且不再依赖调用顺序。
3. 报错标号**复用既有 E00372**（诊断目录的前缀规则按「消息以该键开头」命中，
   加后缀不影响标号，故标号稳定、无需重排全库码号）；凭据追加一句例外说明——
   通用建议「需要复制请用 clone」对凭据不成立。

**两层门控（关键设计）**：移动检查此前由 `TIE_MOVE_CHECK` 整体控制、默认**关闭**
（注释写明「std/compiler 全量迁移完成后默认开启」）。本轮把门控下沉到 `smove`
内部，分成两层：

| 层 | 对象 | 开关 | 理由 |
| --- | --- | --- | --- |
| 凭据 | `guard<cap>`（含凭据的聚合） | **始终检查** | 规范硬约束；既有代码**零违规**（tiec 自举可通过），可立即强制、无迁移成本 |
| 堆类型 | string / table / map / 含堆聚合 | `TIE_MOVE_CHECK` | 全库尚有约 85 处「按值传参后又复用实参」的写法待迁移 |

这一层划分让凭据约束**不必等待**堆类型迁移就能生效——正是「先让代码满足新规则，
再启用强制」的零停机范式。

**过程中发现并修掉的两个既有缺陷**：

- **全局变量被当作移动源**：`is_move_src` 只看类型/初值，判不出「被多处方共享」。
  `g_role` 这类全局首次使用即被标记 moved，后续每次读取都报「已移动」——审计最初
  的 118 条报告绝大多数是此类误报。修法是加独立全局闸 `is_global_var`（全局符号
  表判据），并把 `param_is_move` 的「无条件移交」分支也纳入同一豁免。**这与
  `esc_cand` 缺全局闸导致「全局表被误判为独占」是同一个坑**——判据若只看「类型 /
  初值新鲜度」，就区分不出共享这件事。修正后误报 118 → 85。
- **诊断渲染的全角冒号 off-by-3**：`diagcode.tail_of` 里 `dg_slice(msg, p + 1, ...)`
  跳全角冒号只跳了 1 字节，而 `：` 是 3 字节（EF BC 9A）——切片落在字符中间，
  丢掉首字节、留下非法残片，**渲染出的错误消息后半段乱码**。此前未暴露是因为既有
  消息极少含全角冒号。修为 `p + 3`。

**审计工具**：新增 `TIE_MOVE_AUDIT=1`（与 `--esc-audit` 同一定位）——移动违规
**只报告不中止**，逐条打印 `MVVIOL <行>:<列> <函数> '<变量>'`，用于评估迁移面。
实测 tiec 自身（import 全链）剩余 **85 处 / 13 个函数**，集中在
`driver::parse_args`(32)、`driver::pkg_dep_pairs`(13)、`driver::dep_manifest_ok`(12)、
`interp::fmt_err`(8) 等——构成堆类型迁移的待办清单。

**遗留问题（须单独处理）**：诊断目录 `diagcode_cat.gen.tie` 与源码**不同步**——
现有目录 648 条 exact，用 `scripts/gen-diagcodes.tie` 重建得 568 条。重建会**全量
重排**标号（按字节序连续分配），波及 `tie-diag` 等外部引用与文档。故本轮**不重建**，
新增诊断一律走前缀命中以保持标号稳定。

**验证**：三阶不动点 `d0161de8cef442ee8eb80ab8ecbffa51454e7b653ffc5d4b9b9b7021f4c81173`
并升格；正例 `tests/language/cred_move_probe.tie`（三条合法转移路径：局部转移 /
跨函数 move out / 转移后消费）输出 `cred-move PASS (transfer 7 chain 9)`；负例
`cred_dup_move_neg.tie` 被拒并报告 E00372。

*EN: Credentials are now move-only in the compiler, matching §11.6. Three
changes: guard<Cap> joins the move-tracking predicate; every move site funnels
through a single `move_var` entry that checks before marking (previously each of
six sites only marked, so a repeated transfer silently produced two holders);
and the diagnostic reuses the stable E00372 code via prefix matching. Gating is
two-layered — credentials are always checked (existing code is violation-free),
heap types stay behind `TIE_MOVE_CHECK` (85 migration sites remain, audited via
the new `TIE_MOVE_AUDIT=1`). Two pre-existing defects were found and fixed on
the way: globals were wrongly treated as move sources (118 → 85 false reports),
and `tail_of` skipped only 1 byte of the 3-byte full-width colon, corrupting
UTF-8 in rendered messages.*

## 8. 凭据挂空告警落地记录（W00030，2026-10-02）

*EN: 8. Idle-Credential Warning Landing Record*

**依据**：本文档 §3「凭据规则」——「作用域内未使用对应域构造的凭据 → 编译告警
（凭据挂空）」。§11 审计的最后一项未实现由此关闭。

**判据**：`该作用域新持的域位集 − 该作用域实际用到的域位集`。非空即逐域报 W00030。

| 域 | 「用到」如何判定 |
| --- | --- |
| `mem` / `ext` / `raw` | 双锁通过时置位（`g_used_caps`）——承载清单 `types.builtin_domain` 是单一事实源；port 提升（mem）单独挂一个点 |
| `lock` | 子树扫描：下标读/写、表增删、`for` 遍历（lock 的承载是运算符而非门禁清单项） |
| `share` | **跳过**：该域在实现里暂无承载，任何作用域都不可能「用到」它，报挂空只会是噪声 |

**粒度分两级（关键设计）**：

* **函数级**只判**函数属性位**（`#[unsafe.域]`）。文件级授权是规范明文认可的**粗粒度**
  授权（「适用范围是整块代码都属同一域的场合」），逐函数比对会退化成「授权文件里每个
  不碰该域的函数都告警」——实测 tlib 12 个模块 68 条全属此类，故逐函数判定必须排除。
* **文件级**按**文件**粒度判，且**只判主输入文件**。库文件的文件级授权服务于它自身的
  实现，「引用方有没有用到该域」不是它的判据；把库算进来会对着 `std/process.tie` 这类
  「声明 `unsafe:mem`、但本次编译只用到其中非 mem 函数」的模块报挂空（tiec 自举实测
  2 条全属此类）。直接编译库文件时它自己就是主输入文件，照常受判。

**作用域配对**：`g_used_caps` 与 `g_held_caps` **成对进出**每一个持证作用域；函数是
全新的凭据作用域（凭据不跨函数继承），进入时清零。缺配对会跨作用域累积——前一处用过
的域会掩盖本处的挂空。

**零成本**：整个判定由警告 pass 开关门控，默认（只报错）零额外开销。

**踩坑**：警告目录的查表是「核心消息（ASCII 段归一化为 `%` 后）**精确匹配**」——
文件级措辞与块级不同就必须**单独登记一条 core**，否则告警发出去了却渲染不出来
（静默降级成 W00000 兜底）。

**验证**：三阶不动点 `b8bf636153416122c2dadc447133395eebe5b18567d5e58c456e7a36819167b9`；
探针 `tests/language/cred_idle_probe.tie`（块级 `with(mem)`/`with(lock)`/`unsafe use g`
+ 函数级 `#[unsafe.ext]`，4 条挂空命中、同形态正例全静默）与
`tests/language/cred_idle_file_probe.tie`（文件级，1 条 @1:1）；tiec 自举与 tlib 全量
（177 文件）**零误报**；s21 回归 PASS=197 FAIL=10（FAIL 集合与基线逐字一致，PASS 增量
来自本特性新增探针）。

*EN: The idle-credential warning (W00030) closes the last unimplemented item of
the §11 audit. The predicate is "domains newly held by this scope minus domains
actually used in it". Usage is recorded where the double-lock check passes
(carrier list is the single source of truth) plus a sub-tree scan for the lock
domain; share is skipped because it has no carrier yet. Granularity is
two-levelled: per-function checking only looks at function attributes, since
file-level authorization is explicitly coarse-grained by the spec (checked
per-file, and only for the main input file). Zero cost unless the warning pass
is enabled.*
