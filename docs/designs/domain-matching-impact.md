# 域匹配影响面评估（2026-10-01）

*EN: Domain Matching — Impact Assessment (2026-10-01)*

> **目的**：`domain-classification.md` 把五域与承载定案了，「域匹配」判定（持 `<A>` 域凭据
> 才能做 `<A>` 域操作）是其下一步。那一步是**破坏性**的——现有 `unsafe { alloc(8) }`
> 这类写法要改成持证形式。本文只做一件事：**数清楚要改多少**，据此判断可行性与推进方式。
>
> EN: the domain taxonomy is settled; domain matching is the next step and it is
> breaking. This document only counts the migration surface, so the decision can rest
> on numbers rather than on a guess about how much pointer code tie has.

## 1. 方法（以及一个必须先排除的统计陷阱）

*EN: 1. Method, and a Counting Trap That Must Be Removed First*

**陷阱**：直接 grep 内置名会把**两类完全不同的代码**混在一起——

- **调用方**：用户/库代码调用受门禁的内置，例如 `sqlite.tie` 里的 `dyn_call(g_step, ...)`；
  这一类**需要迁移**；
- **实现方**：编译器自己实现这些内置的代码，例如 `backend/irgen_bi_mem.tie` 里构造
  `memcpy` 指令、`frontend/sbuiltin_q1.tie` 里 `fn_name == "memcpy"` 的字符串匹配。
  这一类**不需要迁移**，它们不是「调用受门禁的 API」，而是在**定义**那个 API。

按朴素 grep，tiec 自身会报出 45 处；其中绝大多数属于实现方。区分办法：看该文件是否
在 `sbuiltin*` / `irgen_bi_*` / `builtin_expr*` 这类**内置实现文件**里，以及该命中是否
出现在 `nm == "..."` / `fn_name == "..."` 这类**字符串匹配**位置。

*EN: A naive grep merges callers with implementers; only callers need migrating. On
tiec the naive count is 45, mostly implementers.*

## 1b. 数据修正（2026-10-01 实施时发现）

**本文档初版的迁移面统计有误，此处更正**：初版报「5 个文件」，是因为扫描时只覆盖了
`tlib/std`，**漏了 `tlib/ext` 与 `tlib/sys`**。实施时按「整仓扫」重测，真实迁移面是
**11 个文件**（下表已更新）。漏项性质与 §1 的陷阱同源——**扫描范围本身选窄了**，
而当时并未察觉。

教训：报「有 N 处」之前先问「我的扫描范围是否覆盖了全部可能位置」。目录级遗漏比
grep 模式遗漏更隐蔽，因为它不会产出任何可疑输出（少扫的目录静默贡献 0）。

*EN: the first version of this document undercounted because the scan covered only
tlib/std. tlib/ext and tlib/sys were missed entirely - 11 files, not 5. A directory
left out of a scan contributes a silent zero, which is why it is easy to miss.*

## 2. 实测数据

*EN: 2. Measurements*

### 2.1 真实的迁移面

| 位置 | 处数 | 文件 | 域构成 | 状态 |
| --- | --- | --- | --- | --- |
| **tlib/std** | 39 行 / 48 次 | **4**（`sqlite` `process` `rng_adv` `csprng`） | ext + mem | 已迁移 |
| **tlib/ext**（初版漏扫） | — | **5**（`ecdsa` `gfx/event` `gfx/gfx` `gfx/port` `gfx/window`） | 全 mem | 已迁移 |
| **tlib/sys**（初版漏扫） | — | **1**（`win32`） | mem | 已迁移 |
| **tiec 自身** | 5 处 | **1**（`interp/call_builtin_seg2.tie`） | ext + mem | 已迁移 |
| tdb | **0** | 0 | — | — |
| tshell | **0** | 0 | — | — |
| **合计** | — | **11 个文件** | — | **全部已迁移** |

*EN: 39 lines / 48 calls across 4 files in tlib/std, plus one file inside tiec; tdb
and tshell are clean. Five files in total.*

### 2.2 tlib/std 明细

按内置名（一次调用计一次）：

| 内置 | 次数 | 域 |
| --- | --- | --- |
| `dyn_call` | 13 | ext |
| `deref_write` | 8 | mem |
| `deref` | 7 | mem |
| `cstr_to_string` | 5 | mem |
| `load_library` | 4 | ext |
| `dyn_call_p` | 4 | ext |
| `alloc` | 4 | mem |
| `get_proc` | 3 | ext |

按文件：

| 文件 | 行数 | 性质 |
| --- | --- | --- |
| `sqlite.tie` | 19 | **SQLite FFI 绑定**——整文件都在跟 C 打交道（`dyn_call` 一族 + `cstr_to_string`） |
| `process.tie` | 15 | 构造 `argv` 缓冲（`alloc` + `deref_write` 写指针数组） |
| `rng_adv.tie` | 3 | 字节缓冲拷贝（`memcpy`） |
| `csprng.tie` | 2 | 同上 |

### 2.3 部署链路

`F:/Projects/tlib/std` 是**源头**；`~/.tiec-lib/tlib/` 是**部署副本**（独立目录，非链接，
且已落后于源头——副本 31 处 vs 源头 39 处）。⇒ 迁移需**改源头 + 重新部署**。

*EN: tlib/std is the source; ~/.tiec-lib/tlib is a deployed copy that has drifted
behind. Migration means editing the source and redeploying.*

## 3. 三个结论

*EN: 3. Three Conclusions*

### 3.1 tie 几乎不用裸指针——迁移面比预想小一个数量级

`deref` / `alloc` 在 **tiec 自身**的实现代码之外基本不出现；整个编译器只有一个文件
（`interp/call_builtin_seg2.tie`）真正调用受门禁的内置。原因不难理解：tie 的数据面用
**表**与**字符串**承载（二者是安全容器，`t[i]` 与 `str_byte` 都在安全区），需要
`memcpy` 级批量操作时走 `byte_concat` / `str_sub_bytes` 这类安全原语。这与既有的
性能结论一致（字符串密度 1× 且是 memcpy 级批量）。

**推论**：设计文档说的「破坏性变更，无兼容期」在**成本上**是可行的——迁移面是 5 个
文件而非上百处。

*EN: tie's data plane is tables and strings, not raw pointers; only one file inside
the compiler calls gated builtins. A 5-file migration makes "breaking, no grace
period" affordable.*

### 3.2 危险构造的分布是集中的，且与「按模块授权」的判断标准完全吻合

`sqlite.tie` 一个文件占了 ext 域的绝大部分（19 处）。这个文件**通篇都在跟 C 打交道**，
正是设计文档 §3 描述的按模块授权适用场合——「它的适用范围是『整块代码都属同一域』的
场合」。

**推论**：迁移形态应当以**文件级授权**为主（改文件头一行），而非逐个调用点标注。

*EN: One file holds most of the ext surface, and it is exactly the "whole block is
one domain" case that module-level authorization was designed for. File-level
authorization should be the primary migration form.*

### 3.3 「无兼容期」可行，但需要先补齐三块前置

迁移本身简单，但它依赖三件**目前尚不存在**的能力（见 §4）。

*EN: The migration is easy, but three prerequisites are missing.*

## 4. 前置缺口（按依赖顺序）

*EN: 4. Prerequisites, in Dependency Order*

| # | 缺口 | 现状 | 影响 |
| --- | --- | --- | --- |
| 1 | **文件级授权只服务 `lock` 域** | `role_reg.tie` 的 `is_valid_mod_param` 接受 `share/mem/ext/trm/lock` 五个值，但**只有 `lock` 被消费**（`role_has_lock` 是 lock 专用） | 迁移主形态不可用。需把 `role_has_lock` 推广为「本文件持哪些域」→ 供 irgen 注入 |
| 2 | **函数级 `#[unsafe.<域>]` 只服务 `lock` 域** | 属性解析后只对 `unsafe.lock` 保留域信息（`sstate.lock_fn_put`），其余域名被丢弃 | 细粒度迁移不可用 |
| 3 | **port 提升的域标签未接** | 门禁已在 `scheck_q3.tie`，但不走内置清单 | 域匹配无法覆盖它（会漏判） |

*EN: file-level authorization and the function attribute both serve lock only; port
promotion is gated but unlabelled.*

## 5. 迁移形态的成本对比

*EN: 5. Migration Forms Compared*

| 形态 | 改什么 | 5 个文件的成本 | 适用 |
| --- | --- | --- | --- |
| **文件级** `type tie<class, unsafe:ext>` | 文件头 1 行 | **5 行** | `sqlite.tie`（整文件同域）等 |
| **函数级** `#[unsafe.mem]` | 每函数 1 行 | 取决于函数数 | 文件内**混合域**时 |
| **块级** `unsafe.with(mem) { }` | 每处 1 行 | 逐调用点 | 少量、局部 |

`process.tie` 需留意：它同时含 `alloc`（mem）与指针写入（mem）——**同域**，故文件级
同样适用。`rng_adv` / `csprng` 只有 `memcpy`（mem）——同样整文件同域。

⇒ **11 个文件全部整文件同域，全部用文件级授权覆盖**。成本 = 11 行文件头。

*EN: all eleven files are single-domain, so file-level authorization covers every
one of them — eleven header lines.*

## 6. 实际推进过程（2026-10-01 实施完毕）

三步全部完成，实际路径与初版建议一致，但**实施中发现了三个初版未预见的问题**：

1. **前置补齐**（声明性、不拦人）——落地时发现两处设计-实现缺口：
   * 文件级授权**只服务 lock 域**：`role_has_lock` 是 lock 专用，其余域名在属性解析时
     被丢弃 ⇒ 推广为**域位集**（`s_file_caps` / `s_fn_caps`）；
   * **import 模块拿不到自己的授权，且会继承主模块的**（越权）：import 解析期间
     `s_file_caps` 仍是主文件的值。修法是按**文件基址**（`g_file_base`）逐模块切换，
     并把 parser 侧的登记改为「记局部 id → 装载后按基址提交」（parser 的节点 id 是
     模块内局部的，直接登记会错位）。
2. **迁移 11 个文件**——全部文件级授权，改文件头一行。
3. **打开强制**——门禁从「仅判 unsafe 上下文」改为「锁一 + 锁二」，并按
   `types.builtin_domain` 查表定位每个内建所属域。port 提升（不走内建清单）
   也补了域标签。

**验证**：三阶不动点 `a329e94660b86a45`（域匹配开启后自举链自我一致）；
s21 回归 PASS=192 / FAIL=10，与**旧编译器基线**（188/10）的 FAIL 集合逐字一致，
PASS 增量 4 = 域匹配正例 1 + 负例 3。

## 6b. 初版建议的三步（保留原文，供对照）

*EN: 6. Suggested Path — Three Independently Verifiable Steps*

1. **补齐 §4 的三块前置**（不改门禁本身、不破坏任何现有代码）：
   推广文件级/函数级授权到五域 + 接线 port 域标签。此时授权是**声明性的**，
   尚未真正拦人 ⇒ 回归基线应完全不动。
2. **迁移 5 个文件**（改文件头 + tiec 自身剩余调用点），**同时**让授权生效于
   自举链：验证口径 = **用新编译器编译 tiec 自身通过**（即
   `unsafe-credential-lock.md` §4 的迁移完备性检查）。
3. **打开域匹配判定**（`unsafe {}` 内不再无视域）：此时代码已经全部持证，
   打开门禁**不产生新的失败**——这是把破坏性变更做到「零停机」的常规办法：
   先让代码满足新规则，再启用规则的强制。

*EN: (1) add the missing plumbing without enforcing; (2) migrate the five files and
let the compiler prove migration completeness by compiling itself; (3) switch
enforcement on — at which point nothing new breaks, because the code already holds
the credentials.*

## 7. 风险与未决

*EN: 7. Risks and Open Questions*

- **授权粒度与审计面**：文件级授权是粗粒度的，一旦某文件被授权 `ext`，其**所有**函数
  都能调 FFI。设计文档对此的立场是「审计时这类文件仍然可见——头部本身就是标记」。
  本文按该立场推进，但这意味着**审计清单要靠文件头而非逐调用点**来定位。
- **`share` 域仍无承载**：域匹配对它无处落地（无承载 ⇒ 无可判之处），不阻塞本方案。
- **迁移顺序的先后**：先迁移 std 库还是先迁移编译器自身？建议**编译器自身优先**
  （它的迁移完备性可被「自编译通过」直接验证），std 库随后（靠回归覆盖）。
- **`~/.tiec-lib` 部署同步**：迁移后需重新部署，否则编译器仍读旧副本。

*EN: risks are coarse granularity, the empty share domain (not blocking), migration
order (compiler first, since self-compilation proves it), and redeployment.*
