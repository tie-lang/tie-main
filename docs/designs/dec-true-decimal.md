# 真小数 dec（设计 v0.1 / ROAD p.9.10.10）

*EN: True decimal `Dec` (design v0.1 / ROAD p.9.10.10)*

**日期** / Date: 2026-09-16 · **类型** / Type: 数值类型设计（tlib 库级数据类型 · 科学计算域数值底座）
**依据** / Basis: 用户两条硬性要求（2026-09-16 定）：**第一位，必须是真正的小数，不能有任何偏差；第二位，在零偏差前提下性能必须最佳——明显快于、明显省内存于其他编程语言的同类实现** · p.9.10 计算科学与多媒体域布局（2026-09-12）· p.8.2.4 运算符重载 · p.9.11.9 checked 运算 · p.9.13.7 tlib 独立仓
**关联** / Related: `tie-lang/tlib`（`/std/dec.tie`）· ROAD p.9.10 档 · tsci（p.9.10.1，消费方）· `docs/designs/tie-primitive-op-design.md`（op_ 契约）
**版本** / Version: v0.2（2026-09-16 big 分层修订：慢径 limbs 改挂独立 big 层）· v0.1（初稿定案）

> EXEC BRIEF: True decimal for tie's computational-science domains. Carrier
> decided: a pure-tie library type `Dec` in tlib (`/std/dec.tie`) — not a
> compiler primitive (p.8.2.4 operator overloading is the designated key for
> library numerics). Representation: sign × coefficient × 10^exponent, with a
> 96-bit inline fast path (24-byte struct, zero heap, ~28-digit width) and
> automatic limb-array escalation to arbitrary precision. Exactness contract
> (hard constraint 1): literals parse digit-exact (never through f64);
> add/sub/mul are always exact; div/sqrt/negative-pow are exact when
> terminating and trap otherwise — rounding exists only in explicit *_ctx
> calls, never silently. Performance plan (hard constraint 2): zero-allocation
> fast path, immutable sharing (neg/abs/shift10 free), base-10^18 limbs with
> i128 intermediates, const-fn folding, LLVM-native codegen; four-way benchmark
> gate vs Python decimal / Java BigDecimal / rust_decimal / C# decimal.
> Phased p.9.10.10.1–.5.

---

## 0. 定位与两条硬约束 / Positioning and the two hard constraints

* 真小数 = 「写什么就是什么」的十进制数：`0.1` 在内存里就是精确的十分之一，不是二进制近似；`1.230` 保留三位有效尾零。名称即承诺——与二进制浮点的「假小数」相对。
* **硬约束一（零偏差，最高优先）**：任何运算不允许静默产生不精确值——数学上能精确则必须精确；结果无限小数（如 1/3）则陷阱，绝不偷偷舍入；舍入只能显式声明。
* **硬约束二（性能，第二优先）**：零偏差为前提下，快于并省于其他语言的 decimal 实现：对动态/托管语言（Python decimal、Java BigDecimal）目标数量级领先；对定宽原语（C# decimal、rust_decimal）同级速度且能力面更广（28 位内联 → 任意位逃生，定宽方溢出即报错）。
* 生态位置：p.9.10 科学计算主轴（tsci→tstat→tsim）的数值底座；tsci 高精度路径的地基；金融/测量/统计输入回显同受益。

*EN: True decimal = "what you write is what you store": 0.1 is exactly one tenth (no binary approximation), 1.230 keeps significant trailing zeros. Hard constraint 1 (exactness, top priority): no operation may silently produce an inexact value — exact whenever mathematically exact; trap when non-terminating; rounding only via explicit context calls. Hard constraint 2 (performance, second): given exactness, beat other languages' decimals — order-of-magnitude lead over dynamic/VM implementations, parity-plus-capability against fixed-width primitives. It is the numeric substrate of the p.9.10 computational-science spine.*

## 1. 名称与落位（定案）/ Naming and carrier (decided)

* 类型名 `Dec`（struct，大写对齐用户 struct 惯例、避让小写标识符）；模块命名空间 `dec`；中文名「真小数」，英文 true decimal。
* 落位：tlib `std` 层 `/std/dec.tie`（`import "/std/dec.tie"`，p.9.13.7 库根别名）。平台无关核心数值 → std 层。
* **载体定案：纯 tie 库类型，不是编译器基元**。依据：p.8.2.4 运算符重载（`op_add..op_neg` 方法约定）正是为向量/矩阵/复数/日期这类库数值类型建的钥匙；p.9.9/9.10 布局纪律「不借道编译器开口子」；性能来自表示与 LLVM 原生代码，不来自「是不是基元」（rust_decimal 以库实现与 C# 基元同级即为证）。
* **分层修订（2026-09-16 定案）**：大整数内核抽为独立 big 层（p.9.10.11，`/std/big.tie`，基 10^18 单内核）——dec 慢径 limbs 改挂 big，快径（96-bit 内联）不变；进制转换器（p.9.10.12）与素数寻找器（p.9.10.13）同享该底座。分层设计见 `docs/designs/numeric-substrate.md`。
* 字面量后缀（`0.1d`）属语言增强，内核落地后立项语言档（§9 分期、§11 未讨论项）；架构今天就为它留位——后缀字面量的 desugar 目标即 `from_parts`（可 const 折叠）。

*EN: Type `Dec` (struct convention), namespace `dec`, Chinese 真小数. Lives in tlib std (`/std/dec.tie`). Carrier decided: pure-tie library type, NOT a compiler primitive — p.8.2.4 operator overloading is the designated key for library numerics, per the p.9.9/9.10 "no compiler backdoor" discipline; performance comes from representation plus LLVM codegen, not primitiveness. The literal suffix `0.1d` is a language-track item sequenced after the core; the architecture already reserves its desugar target (`from_parts`, const-foldable). Layering revision (2026-09-16): the big-integer core is extracted into an independent big layer (p.9.10.11); dec's slow path rides on it while the 96-bit fast path is unchanged; radix (p.9.10.12) and primes (p.9.10.13) share the same substrate — see numeric-substrate.md.*

## 2. 表示——性能地基（定案）/ Representation: the performance foundation (decided)

* 数学形态：`Dec = sign × coeff × 10^exp`（coeff 非负整数，exp 带符号）。「真」由表示保证：十进制系数 + 十进制指数，无任何二进制成分。
* **快径（绝大多数值）**：96-bit 十进制系数（保证 28 位有效数字，满量程 7.92e28）内联进 struct，零堆分配：

| 字段 | 类型 | 内容 |
|---|---|---|
| `coeff_lo` | i64 | 系数低 64 位 |
| `coeff_hi` | i64 | 系数高 32 位（低 32 位有效，高 32 保留） |
| `meta` | i64 | 位打包：堆标志(1 位) · 符号(1 位) · 指数(62 位带符号偏置，±2.3e18) |
| `limbs` | table<i64> | 慢径肢数组；快径恒引用**共享空表常量**（namespace const，p.9.12.4 机制）——快径值不产生任何堆分配 |

* struct 合计 **24 字节、8 字节对齐**，值语义传参。
* **慢径（逃生）**：结果超出 96 位 → 自动升位至 limbs（基 10^18、i64 肢、i128 中间积），任意精度无上限（内存为界）；运算后 ≤96 位且 |exp| 在界 → 自动降级回快径。类型不变，用户无感。
* **不可变值类型（定案）**：运算恒返回新值，从不原地改 limbs。收益：struct 赋值 = 句柄拷贝 O(1)；`neg`/`abs`/`shift10` 共享 limbs 零分配；不可变约定使 limb 表共享安全（无别名突变风险）；无写时复制开销。
* 单值内存对照：tie `Dec` 24B 内联/零堆 vs C# decimal 16B（定宽无逃生，溢出即炸）vs rust_decimal 16B（同 C#）vs Python decimal ≈100B+ 堆对象 vs Java BigDecimal ≈80B+（含 BigInteger）。

*EN: Value = sign × coeff × 10^exp — decimal coefficient and exponent, zero binary contamination. Fast path: 96-bit coefficient (guaranteed 28 significant digits) inline in a 24-byte struct whose limb-table handle references a shared empty-table const, so fast-path values allocate nothing. Slow path: automatic escalation to base-10^18 limb arrays (i128 intermediates, arbitrary precision) and automatic demotion back. Immutable value type: ops always return new values — O(1) assignment, allocation-free neg/abs/shift10, safe limb sharing, no COW cost.*

## 3. 零偏差契约（硬约束一，定案）/ The exactness contract (hard constraint 1, decided)

* **字面量**：`0.1d` 词法直解析数字串 → (coeff, exp)，**永不过 f64**（多数语言 decimal 实现既慢又有偏差的隐形根源）；无后缀小数字面量仍 f64，零破坏。
* **加减乘（含非负整数幂 pow）**：恒精确。结果超快径 → 自动升位，永不舍入；内存为界，无人为上限。
* **除法 / 开方 / 负整数幂**：结果为有限小数 → 精确返回（1/4=0.25、√0.25=0.5、2^-3=0.125）；无限小数（1/3、√2）→ **陷阱**（可捕获 panic，对齐 p.9.11.9 checked 哲学），诊断明示改用 `div_ctx/sqrt_ctx/pow_ctx` 显式声明精度与舍入。**静默舍入值在这个类型里不存在。**
* **取模 op_mod / 整除 quo / 余 rem**：恒精确（余数天然有限）。
* **无 -0、无 NaN、无 Inf（定案）**：负零/非数/无穷是近似域伪影，与「真」相悖——零只有规范零（coeff=0, exp=0, sign=+）；除零/指数越界（±2.3e18 外）走陷阱。近似域需求归 f64。
* **from_f64 诚实桥（定案）**：`from_f64(0.1)` = 该 f64 的**精确**十进制展开（0.1000000000000000055511151231257827021181583404541015625）——桥接浮点世界时说真话；要「人类意图的 0.1」用 `parse("0.1")`。`to_f64`/`to_i64` 显式有损并范围检查（越界陷阱）。

*EN: Literals parse digit-exact, never through f64. add/sub/mul/non-negative pow are always exact (auto-escalate, never round). div/sqrt/negative pow: exact when the result terminates, otherwise trap (catchable panic) directing to explicit *_ctx calls — silently rounded values do not exist in this type. mod/quo/rem always exact. No -0/NaN/Inf (approximation-domain artifacts; canonical zero only; overflow and zero-division trap). from_f64 is the honest bridge: the exact decimal expansion of the binary value; parse("0.1") is how you get the human-intended 0.1.*

## 4. 舍入与 context（显式制，定案）/ Rounding and context (explicit-only, decided)

* 舍入**只**发生在显式 ctx 调用：`div_ctx(a,b,prec,rounding)` · `sqrt_ctx` · `pow_ctx` · `mul_ctx`/`add_ctx`（对齐 context 宽度的省内存模式）· `round(a,prec,rounding)` · `quantize(a,exp)`（定点对齐）。
* 舍入模式六种：`half_even`（默认）· `half_up` · `half_down` · `floor` · `ceil` · `trunc`。
* **无全局可变 context（与 Python decimal 的关键分野）**：context 显式传参，进程状态不改变算术结果——跨平台逐位确定（科学计算可复现性硬需求）、并发无锁。便利性由默认参数承担（prec 默认 = 快径保证宽 28）。
* 溢出/陷阱策略不可静默关闭（对齐 tie checked 族哲学）；陷阱可捕获。

*EN: Rounding happens only in explicit *_ctx calls with six modes (half_even default). No global mutable context — unlike Python decimal — so results are bit-deterministic across platforms and lock-free under concurrency; convenience via default arguments (prec defaults to the 28-digit guaranteed fast width). Traps are catchable, never silently suppressible.*

## 5. 语义细则（定案）/ Semantics details (decided)

* **尾零保留**：`parse("1.230")` 回显 `1.230`——有效数字（测量精度语义）是数据的一部分；数值比较按值（1.230 == 1.23 为真）。
* **规范零**：任何形式的 0 统一为 (coeff=0, exp=0, sign=+)；is_zero 判定与相等语义一致。
* **比较全家**：op_eq/ne/lt/le/gt/ge 数值序，跨快径/慢径一致。
* **科学记数**：`to_sci()`（d.ddddE±x）；`shift10(a,k)` 精确移位——纯指数算术，O(1) 零分配（科学计算高频操作进 O(1)）。

*EN: Trailing zeros preserved (significant-figure semantics); numeric comparison uniform across paths; canonical zero; scientific formatting and O(1) allocation-free decimal shifting.*

## 6. API 面 / API surface

```
构造    parse(s) · from_int(i64) · from_f64(f64) · from_parts(neg, coeff:i128, exp:i64) · zero()
查询    is_zero() · is_neg() · digits() · exp() · to_coeff_i128()（超 38 位陷阱）
运算符  + - * / % == != < <= > >= 一元负号（op_ 契约，p.8.2.4）
显式    abs · pow(i64) · sqrt · quo · rem · shift10(a,k)
舍入族  div_ctx · sqrt_ctx · pow_ctx · mul_ctx · add_ctx · round · quantize
格式化  to_string（尾零保留）· to_sci · to_fixed(n)
转换    to_i64（越界陷阱）· to_f64（最近舍入，有损明示）
```

* 混合运算边界（如实写明，由 p.8.2.4 裁决表决定）：`dec + 整数` 成立（Dec 在左，op_add 将整数精确收编为 dec）；`整数 + dec` 不成立（左为基元走原路径）——惯用法 `d + 1` 或 `Dec.from_int(1) + d`；字面量后缀落地后 `1d + d` 自然成立。这是库类型载体的已知代价，如实进用户文档。

*EN: API surface as listed. Mixed-arithmetic boundary (honest, per the p.8.2.4 dispatch table): `dec + int` works (Dec on the left absorbs the integer exactly); `int + dec` does not dispatch — idioms are `d + 1` or `Dec.from_int(1) + d`; the literal suffix resolves this ergonomically once landed.*

## 7. 性能工程与达标路径（硬约束二）/ Performance engineering (hard constraint 2)

* 已定案的杠杆：
  * 快径零堆 + 24B 内联（§2）——对托管实现（对象头 + 堆 + GC 压力）是数量级差；
  * 共享空表常量——快径构造与运算不触碰分配器；
  * neg/abs/shift10 零分配共享（不可变红利）；
  * 基 10^18 + i128 中间积——肢数最少、乘法单指令化（LLVM mulx）；
  * 升位/降级自动且对称——结果一进快径立即回内联，无长期驻留慢径；
  * const fn 编译期折叠（p.8.1.1）——科学常数表零运行期成本（分期验证）；
  * tiec→LLVM O3 原生码——对解释器/VM 实现的根本优势。
* 基准协议（p.9.10.10.4，验收门）：同题四方对比 Python decimal（C libmpdec）/ Java BigDecimal / rust_decimal / C# decimal——乘法链 10^7 次 · 除法链 · parse/format 往返 · 升位路径 · 单值内存与分配次数。**验收目标：对 Python/Java ≥10×；对 rust_decimal/C# 同级（差距 ≤2×）且能力面更广（28 位内联 + 任意精度逃生 + 零偏差除法契约，定宽方均无）；单值内存 ≤ rust_decimal 2× 且快径零堆。**未达线 → 探针 RCA → 调优迭代（16B 单 i128 位打包、小值路径、肢基数终裁 10^18/10^19 均为预案），不达线不放行。

*EN: Decided levers: zero-heap inline fast path, shared empty-table const, allocation-free neg/abs/shift10, base-10^18 limbs with i128 intermediates, symmetric auto escalate/demote, const-fn folding, LLVM-native codegen. Benchmark gate (phase 4): four-way comparison vs Python decimal / Java BigDecimal / rust_decimal / C# decimal; targets ≥10× over Python/Java, within 2× of rust_decimal/C# with strictly broader capability, ≤2× rust_decimal memory with zero fast-path heap. Miss → RCA → iterate; no pass, no ship.*

## 8. 与科学计算域的衔接 / Fit into p.9.10

* tsci（p.9.10.1）依赖 Dec 做高精度路径（ODE 步长统计、优化收敛判据、特殊函数任意精度求值）；超越函数（exp/ln/三角）**归 tsci**——在 Dec 之上实现 argument reduction + 级数，Dec 保持「数」的纯度不膨胀。
* tstat/tsim 的蒙特卡洛/大规模统计仍以 f64 为主（速度域）；Dec 服务精确输入、金融/经济序列、高精度求值——两域分工在 tsci 设计推演时明示（未推演）。

*EN: tsci builds arbitrary-precision transcendentals on top of Dec (Dec stays a pure number); tstat/tsim Monte-Carlo stays f64 while Dec serves exact inputs, financial/economic series, and high-precision evaluation paths.*

## 9. 落地分期 / Phasing（p.9.10.10.1–.5）

* **p.9.10.10.1 内核与快径**：表示落地 · 共享空表探针 · i128 语义探针（除法/溢出行为验证，异常则按预案换 2×i64 手工除法）· 24B 布局断言 + parse/from_int/from_parts/to_string/比较/取负/abs + 加减乘（含升位）——探针全绿、tlib 探针绿、tiec 回归不劣化（随 p.9.10.11 big 先行：慢径 limbs 由 big 层提供，dec 为其消费者）
* **p.9.10.10.2 除与根**：可尽性判定 · 精确除 · quo/rem/op_mod · 陷阱诊断 · sqrt/pow/shift10 + ctx 族与六舍入模式
* **p.9.10.10.3 转换与格式化**：from_f64 精确展开 · to_f64/to_i64 · to_sci/to_fixed · quantize/round · 慢径自动降级
* **p.9.10.10.4 性能攻坚**：基准协议四方对比（§7 验收门）· 探针调优迭代 · const fn 折叠验证
* **p.9.10.10.5 文档与字面量立项**：双语用户文档 · 示例集 · 字面量后缀 `d` 语言档立项材料
* 每子项完成即追加双语记忆（记忆纪律）。

*EN: Five phases: core and fast path → division/root plus ctx family → conversions/formatting plus auto demotion → benchmark campaign (acceptance gate) → docs and literal-suffix proposal. Bilingual memory appended per completed sub-item.*

## 10. 边界 / Boundary（不做什么）

* 不做 NaN/Inf/-0（§3 定案）；不做全局可变 context（§4 定案）
* 不做有理数/区间算术/符号计算（tsci 需求另行评审，不改 Dec 表示）
* 不做超越函数（归 tsci，§8）
* 内核零编译器依赖（不改 tiec）；字面量后缀走语言档独立立项
* 不做 IEEE 754-2008 decimal64/128 交换格式互操作（如需另评）

*EN: Explicit non-goals: NaN/Inf/-0, global mutable context, rationals/intervals/symbolic math, transcendentals (tsci's job), zero compiler changes in the core, IEEE 754-2008 interchange formats (re-evaluate if needed).*

## 11. 未讨论项（不落为结论）/ Not yet concluded

* dec 作 map 键的语义——依赖 tie map 对 struct 键的支持形态（当前键限标量/any），未推演
* 16B 单 i128 位打包（flag/sign/exp/coeff 全压缩一元）——探针后裁决（§7 预案）
* 字面量后缀 `d` 的语法细节（`1.23d` / 科学计数组合文法 / 与无后缀 f64 的混用规则）——立项时推演
* 肢基数 10^18 vs 10^19 终裁——基准后定
* tsci 超越函数精度协议（reduction 目标位数/误差界）——tsci 设计推演

*EN: Open items (not conclusions): Dec as map key, 16B single-i128 packed layout (probe-gated), literal-suffix grammar details, limb base final call (post-benchmark), tsci transcendental precision protocol.*

---

## 附录 / Appendix

* 术语 / Terms：快径（fast path，内联零分配表示）· 升位/降级（escalate/demote，快径↔慢径自动转换）· 可尽（terminating，除/根/负幂结果为有限小数）· 有效数字（significant digits，尾零承载）
* 先例对照 / Precedents：Python decimal（任意精度 + 全局可变 context，慢，约 100B+/值）· Java BigDecimal（任意精度不可变，GC 压力）· C# decimal / rust_decimal（96-bit 定宽内联 16B，溢出即错，无逃生）· IEEE 754-2008 decimal128（定宽 34 位，含 NaN/Inf）· 本设计 = **内联快径 + 任意精度逃生 + 零偏差除法契约** 的组合，无先例同款
* 演进：本档为 dec 内核定案；字面量后缀立项后补语言档条目；基准报告落 `docs/bench/`
