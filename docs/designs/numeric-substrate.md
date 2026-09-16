# 数值底座扩展：big 大整数 · 进制转换器 · 素数寻找器（设计 v0.1 / ROAD p.9.10.11–.13）

*EN: Numeric substrate expansion: big integers, radix converter, prime finder (design v0.1 / ROAD p.9.10.11–.13)*

**日期** / Date: 2026-09-16 · **类型** / Type: 数值底座设计（tlib 库级模块 · 科学计算域数值地基）
**依据** / Basis: 用户定案（2026-09-16）：**抽 big 独立层（基 10^18 单内核 + Montgomery 预案）· 素数寻找器做全套 · 三立项 p.9.10.11/12/13 · 后续其他算法持续加入（算法族方向）· tie 已在用 48 进制（std/b48 事实标准）** · dec 真小数设计（`dec-true-decimal.md` v0.2）· std/base48.tie 现行实现
**关联** / Related: `tie-lang/tlib`（`/std/big.tie`、`/std/primes.tie`）· dec（p.9.10.10，改挂 big）· `docs/designs/dec-true-decimal.md` · std/base48.tie（b48 命名空间）· tsci（p.9.10.1，未来消费方）
**版本** / Version: v0.1（初稿定案）

> EXEC BRIEF: Expands the tie numeric substrate into three layers on one
> foundation. big (`/std/big.tie`): arbitrary-precision integers, base-10^18
> limbs (single core shared with dec, i128 intermediates), full arithmetic +
> gcd/pow + radix stringification; dec (p.9.10.10) re-rides on it. Radix
> converter (p.9.10.12): bidirectional parse/format over bases 2..48 — the
> default alphabet is the prefix of tie's canonical continuous digit table
> (base48 fully compatible with std/b48), custom alphabets configurable; the
> zero-deviation contract extends across bases: exact when terminating in the
> target base, otherwise trap or explicit ctx rounding. primes (`/std/
> primes.tie`): full suite — deterministic Miller-Rabin for u64, BPSW for big,
> next/prev/nth, segmented-sieve lazy streams (yield), factorize (Pollard-
> Brent), π(x) (Lehmer). Algorithm-family direction registered: the substrate
> keeps absorbing future algorithm modules, one module one ROAD item.

---

## 0. 定位与依据 / Positioning and basis

* 数值底座 = 科学计算域（p.9.10 tsci→tstat→tsim）的地基：dec 真小数（p.9.10.10）之下是**大整数**，之侧是**进制转换**与**数论算法**。三个能力共享一个大整数内核，一次抽层、处处受益。
* 用户四项定案（2026-09-16）：
  * **抽 big 层**：大整数独立成层，dec 改挂其上；基 10^18 单内核与 dec 同源，big 域模幂不达基准线再上 Montgomery（预案，探针裁决）；
  * **素数全套**：判定 + 搜索 + 筛流 + 因数分解 + 素数计数，一步到位；
  * **三立项**：p.9.10.11 big / p.9.10.12 进制转换器 / p.9.10.13 primes，一档一模块、各自独立验收；
  * **算法族方向**：数值底座是持续扩展面，后续其他算法一模块一立项持续加入（清单未讨论）。
* **事实标准并入：tie 已在用 48 进制**——`std/base48.tie`（命名空间 `b48`）以连续字符台服务 TSHA 摘要指纹编码。进制转换器以该字符台为一等公民（§3），两个 base48 语义（编码 vs 数值）并存不重叠、字符台同源可互认。

*EN: The numeric substrate = big integers beneath dec, radix conversion and number theory beside it — one shared big-integer core. User decisions (2026-09-16): extract the big layer (base-10^18 single core, Montgomery contingency), full prime suite, three ROAD items, algorithm-family direction, and adoption of tie's existing base48 (std/b48) as the de-facto standard digit table.*

## 1. 分层架构 / Layering

```
/std/primes.tie   /std/dec.tie          ← 算法与数域层（primes 消费 big；dec 值域层）
        \              |
         \        /std/big.tie        ← 大整数底座（p.9.10.11，唯一大数内核）
                  |
            tiec 基元 i64/i128       ← 快径（u64/i128 域不走 big）
```

* 依赖单向：primes → big；dec → big；radix 函数族落在 big 与 dec 各自命名空间（不立独立模块，p.9.10.12 为工作项立项）。
* **快径纪律**：u64/i128 能算的（绝大多数判定/搜索/进制场景）绝不绕道 big——big 只在超出 128 位时接管。与 dec 快径/慢径哲学同构。
* big 内核只此一份（基 10^18 limbs）：dec 慢径、素数器大数域、进制器大数域全部消费它，零重复实现。

*EN: One-way layering: primes→big, dec→big; radix lives as function families in big/dec namespaces. Fast-path discipline: the u64/i128 domain never detours through big. Exactly one big core (base-10^18 limbs) serves dec's slow path, big-domain primes, and radix — zero duplication.*

## 2. big 大整数（定案）/ big integers (decided)

* 类型 `Big`（struct），命名空间 `big`，落位 `/std/big.tie`。
* 表示：符号 × 系数，limbs 基 **10^18**（i64 肢，i128 中间积）——与 dec 慢径同源，进制串化/dec 尾零处理天然高效。
* 语义：不可变值类型（运算恒返回新值，同 dec 纪律）；除零陷阱（可捕获）；无人为上限（内存为界）。
* API 面：
```
构造    parse(s, base=10) · from_i64/from_u64/from_i128 · zero()
运算符  + - * / % == != < <= > >= 一元负号（op_ 契约，p.8.2.4；Big 在左收编整数）
显式    abs · pow(i64) · divmod · gcd · lcm
进制    to_str(base=10, alphabet=默认) · parse(s, base=10, alphabet=默认)
查询    is_zero · sign · even/odd · digits(base=10)
转换    to_i64/to_i128（越界陷阱）
```
* 性能杠杆：i128 中间积单指令乘（LLVM mulx）· 大数乘法 Karatsuba 阈值探针裁决 · 进制串化分治（§3）· const fn 常数折叠 · op_ 重载零抽象税（tiec 单态化）。

*EN: Type `Big` in `/std/big.tie`: sign × coefficient, base-10^18 i64 limbs with i128 intermediates (shared with dec's slow path). Immutable value semantics, catchable division-by-zero trap, no artificial cap. Full op_ overload set; explicit abs/pow/divmod/gcd/lcm; radix-aware parse/to_str; performance levers: i128 single-instruction multiply, probe-gated Karatsuba threshold, divide-and-conquer radix conversion, const-fn folding.*

## 3. 进制转换器（定案）/ Radix converter (decided)

* **字符台定案（tie 连续台一条规则）**：默认字母表 = tie 连续字符台的前 b 个字符，覆盖基 2..48：

```
0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL
 └─ 0-9 (10) ─┘└──── a-z (26) ────┘└── A-L (12) ──┘
```

  * **基 48 = std/b48 全台**：`big.parse(s, 48)` / `big.to_str(n, 48)` 与现行 base48 字符串逐字符互认（同一字母表、索引即值）；
  * 自定义字母表作为可选参数（默认起点不锁死，对齐可配置原则）；基 >48 走自定义字母表；
  * 解析大小写敏感（台内 a 与 A 值不同），非法字符陷阱。
* **双向、两域**：
  * 整数域（big）：`big.parse(s, b)` / `big.to_str(n, b)`——整数在任意基恒可尽，**恒精确**；负数 `-` 前缀；最短表示（无前导零补齐，0 = "0"）。
  * 小数域（dec）：`dec.parse_base(s, b)` / `dec.to_str_base(d, b, ...)`——**跨基零偏差契约**：在目标基判定可尽性，可尽则精确、不可尽陷阱，显式 `*_ctx(prec, rounding)` 才允许舍入。例：`dec.parse_base("0.1", 2)` = 0.5 ✓；`dec.to_str_base(0.5, 2)` = "0.1" ✓；`dec.to_str_base(0.1, 2)` → 陷阱（1/10 二进制无限）。
* **与 std/b48 的边界（写清避免「两个 base48」混淆）**：b48 是**字节串编码**（hex ↔ base48，定长块切分、长度保留、指纹域）；进制转换器是**数值进制**（大整数值 ↔ 基 b 字符串，最短表示、可带小数）。两者字符台同源、语义不同、并存互补——指纹走 b48，数值走 big/dec。
* 性能：大数进制串化分治（按 base^k 分半递归，O(M(n)logn)，对齐 GMP 做法）；快径（≤i128）直接算；基 10^18 limbs 对十进制系输出近零开销。

*EN: Digit table decided: default alphabet = first b characters of tie's canonical continuous table (0-9a-zA-L), covering bases 2..48 — base48 is byte-compatible with std/b48; custom alphabets configurable for bases beyond. Two domains, bidirectional: integer domain (big) always exact in any base; fractional domain (dec) extends the zero-deviation contract across bases — exact when terminating in the target base, else trap, rounding only via explicit ctx. Boundary vs std/b48 stated: b48 = byte-string block encoding (fingerprints), radix = numeric base conversion; same table, different semantics, complementary. Divide-and-conquer stringification for big values.*

## 4. primes 素数寻找器（全套，定案）/ Prime finder (full suite, decided)

* 命名空间 `primes`，落位 `/std/primes.tie`。
* API 面：
```
判定    is_prime(n)               u64/i128 域：确定性 Miller-Rabin（7 基，无假阳性，微秒级）
                                  big 域：BPSW（base-2 MR + 强 Lucas，无已知反例）
搜索    next_prime(n) · prev_prime(n)        wheel-30 跳跃（候选密度 8/30，约 3.75× 提速）
        nth_prime(k)              上界估计（k·(ln k + ln ln k)）+ 分段筛定位
生成    stream(limit)             分段筛 + yield 惰性素数流（p.9.11.15/16 现货）——
                                  常量内存流式产出，for p in primes.stream(1e12) 不爆内存
        primes_between(a, b)      区间表（同分段筛内核）
计数    count_primes(x)  π(x)     Lehmer（Meissel 层下 O(x^(2/3))），大 x 性能亮点
分解    factorize(n)              小素数试除 + Pollard-Brent rho → (素数, 指数) 对表
                                  n=1 空表；n=0/负数陷阱（定义域 n ≥ 1）
```
* 语义：全函数纯函数、确定性（同输入同输出，跨平台一致——对齐 dec 无全局态纪律）；big 域判定走 big（§1 层依赖），u64/i128 域不碰 big。
* 性能纪律（继承 dec 两条硬约束精神）：判定微秒级 + 确定性无假阳性（验收硬门）；筛流常量内存；π(x) 大 x 对对照实现明确加速比；不达线 → 探针 RCA → 调优（Montgomery 模幂/更紧 wheel 均为预案）。
* 对照基准（p.9.10.13 基准门）：Python（sympy isprime/nextprime、gmpy2）、Java BigInteger.isProbablePrime——关键路径（大判定/筛流/π(x)）目标 ≥10×，判定正确性零妥协。

*EN: Namespace primes in /std/primes.tie: deterministic 7-base Miller-Rabin for u64/i128 (no false positives, microsecond class), BPSW for big; next/prev via wheel-30; nth_prime via upper-bound estimate + segmented sieve; lazy prime streams via segmented sieve + yield (constant memory); primes_between; π(x) via Lehmer O(x^(2/3)); factorize via trial division + Pollard-Brent. Pure deterministic functions, no global state. Acceptance gates: correctness (zero false positives), constant-memory streaming, ≥10× over Python references on key paths; Montgomery modexp is a prepared contingency.*

## 5. 算法族方向（2026-09-16 用户定）/ Algorithm-family direction

* 数值底座 = **持续扩展面**：big 之上后续算法模块按同一模式加入——一模块一立项、一文档、同两条硬约束纪律（零偏差 + 基准门）、同快径/慢径哲学。
* 形态先例：本档三模块（big/radix/primes）即前三个；后续候选（排序/数论扩展/特殊函数……）**清单未讨论**，随需求逐个推演立项。
* 纪律：算法模块不反向修改 big 接口（需求缺口走 big 自身演进子项），依赖保持单向（§1）。

*EN: The substrate keeps absorbing future algorithm modules — one module, one ROAD item, one doc, same hard constraints, same fast/slow-path philosophy, one-way dependency (no back-door changes to the big interface).*

## 6. 落地分期 / Phasing

* **p.9.10.11.1 big 内核**：表示/构造/比较/加减乘/十进制串化 + 探针 + 自举回归不劣化
* **p.9.10.11.2 big 补全与 dec 改挂**：除模/gcd/lcm/pow · 任意基串化（tie 连续台）· op_ 全套 · **dec 慢径 limbs 改挂 big（dec 全探针回归绿）**
* **p.9.10.12.1 进制器整数域**：big 域 parse/to_str 基 2..48 + 自定义字母表 + 负号/非法字符文法 + 探针（含 b48 字符台逐字符互认验证）
* **p.9.10.12.2 进制器小数域**：dec 域 parse_base/to_str_base + 跨基可尽判定 + ctx 舍入族 + 文档
* **p.9.10.13.1 判定与搜索**：u64 确定性 MR · big BPSW · next/prev（wheel-30）· nth_prime
* **p.9.10.13.2 生成、计数与分解**：分段筛惰性流 · primes_between · factorize（Pollard-Brent）· π(x)（Lehmer）
* **p.9.10.13.3 基准与文档**：对照基准（§4 验收门）· 双语用户文档 · 示例集
* 每子项完成即追加双语记忆（记忆纪律）。

*EN: Seven sub-items across three tiers: big core → big completion + dec re-ride → radix integer domain → radix fractional domain → primality/search → sieve/count/factorize → benchmarks and docs. Bilingual memory per completed sub-item.*

## 7. 边界 / Boundary（不做什么）

* 不做模运算公开接口之外的高阶数论（原根/椭圆曲线…——算法族后续按需立项）
* 不做密码域随机素数生成（归 tlib 密码域模块，与 ed25519/x25519 同域）
* 不做 IEEE 定宽十进制交换格式（dec 文档 §10 已定）
* 不立独立 radix 模块（进制函数族落 big/dec 命名空间，p.9.10.12 为工作项编号）
* 素数变体（孪生/梅森/安全素数）不进本轮（未讨论项）

*EN: Non-goals for this round: advanced number theory beyond public mod arithmetic, crypto-domain random prime generation (belongs to the crypto modules), IEEE fixed-width interchange, a standalone radix module, special prime variants.*

## 8. 未讨论项（不落为结论）/ Not yet concluded

* 算法族后续清单（§5 方向已定，具体模块未推演）
* Montgomery 模幂的启用触发线（基准探针后裁决）；Karatsuba 阈值同
* BPSW 之外的加强轮策略（显式多基 MR 可选参数形态）
* radix 负基/基前缀（0x/0b 自动识别）文法细节——实现期定
* π(x) 超大 x（>1e15）是否引入 Lucy_Hedgehog 式算法——基准后定
* big 作 map 键的哈希规范化（与 dec map 键同题，依赖 tie map struct 键形态）

*EN: Open items: future algorithm-family list, Montgomery/Karatsuba trigger lines (probe-gated), extra MR rounds form, radix prefix/negative-base grammar, ultra-large π(x) algorithm, big-as-map-key hashing (same topic as dec).*

---

## 附录 / Appendix

* **base48 事实档案**（2026-09-16 现场核查）：`std/base48.tie`（命名空间 `b48`，纯 tie，零依赖）——连续字符台 48 字符 `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL`（索引即值，'0'=0）；用途 = hex 字节串 ↔ base48 定长块编码（m = ceil(8n/log2 48)，长度保留，encode/decode 精确互逆，服务 TSHA 摘要指纹/授权码/审计链 ID）；实现 = 字节数组长除/乘法（进位 < 2^63 不溢出）；错误约定 = 非法输入返回空串。本设计的字符台与互认契约（§3）即以它为准。
* 术语 / Terms：快径（fast path，u64/i128 直算域）· 可尽（terminating，目标基下有限表示）· wheel-30（模 30 剩余类筛跳跃）· BPSW（Baillie–PSW 素性测试）· 分段筛（segmented sieve，常量内存筛法）· Lehmer（Meissel–Lehmer 素数计数）
* 演进：本档为数值底座扩展定案；dec 分层修订见 `dec-true-decimal.md` v0.2；基准报告落 `docs/bench/`；算法族后续模块各自立项推演
