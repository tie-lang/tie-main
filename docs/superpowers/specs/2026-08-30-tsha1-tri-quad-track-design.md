# tsha1b 第三轨海绵 + tsha1x 四轨重设计

- **日期**：2026-08-30
- **状态**：设计定稿（待 review 后分步实施）
- **范围**：tie 标准库 TSHA1 哈希族结构升级——(1) **tsha1b 增加第三轨「海绵结构」**（双轨 → 三轨）；(2) **tsha1x 独立重构**（脱离 f+b 排列组合，改为四轨并行 + 第四种算法）。二者 `docs/superpowers/specs/2026-08-29-plugin-kernel-design.md §6.6` 的续篇。
- **依据**：std/tsha1.tie（现行双轨实现）、tests/tsha_probe/gen_tsha1fr.py、gen_tsha1bx.py（现行参考生成器）、docs/papers/gen_tsha1_paper.py（论文生成脚本）。

## 1. 背景与目标

现行 tsha1b 是「三进制双轨并行 + 最后综合」：状态 `v[0..15]`，轨 A = v[0..7]、轨 B = v[8..15]，每字 = (M, N) 平衡三进制位平面，R_B=14 轮，尾端 `fin_synth`（S=4 收束）。tsha1x 是「f+b 排列组合再算」（digest_f/digest_b 各取四分按固定表拼接，NX=6 轮）。

本次升级目标：

| 模型 | 现行 | 目标 | 结构定位 |
| --- | --- | --- | --- |
| tsha1f | 双轨（R_F=12） | 不变 | 快速 |
| tsha1r | 双轨（R_R=8） | 不变 | 轻量 |
| tsha1b | 双轨（R_B=14） | **三轨**：双轨 + 海绵轨（R_B 不变） | 复杂 |
| tsha1x | f+b 排列组合 | **四轨**：双轨 + 海绵轨 + LFSR 轨，独立重构 | 加强 |

家族梯度：f（双轨）→ r（双轨轻量）→ b（三轨：+海绵）→ x（四轨：+海绵+LFSR）。四种处理哲学交汇：平衡三进制位平面、SHA-1/2 式链式压缩、SHA-3 式海绵态、LFSR 反馈移位。

**不变量（本设计不触碰）**：对外 API（`tsha.tsha1f/b/x/r(msg, n, base=48)`）、位长集合 `{2,3,4,6,8,12,16,24,32,48,64,88,96}`、进制 `{2,3,8,16,48}`、XOF 流扩展、`fit48`、`_hex` 变体、非法值拒绝语义。

## 2. tsha1b 第三轨：海绵结构（完整规格）

> 说明：本节为实施粒度规格，**每一项都是确定量**，实施（std/tsha1.tie 与 gen_tsha1bx.py）只允许按此执行，不得自行变更；如需调整须先回到本文档改版。

### 2.1 状态布局与初始化

- 压缩状态扩为 **24 字**：`v[0..23]`。
  - 轨 A：`v[0..7]`（4 个三进制字，每字 = (M,N) 一对半字）；
  - 轨 B：`v[8..15]`（4 个三进制字）；
  - **轨 C（海绵轨）**：`v[16..23]`（4 个三进制字）。
- 海绵轨 rate/capacity 分区（按三进制字划分，2 字一组）：
  - **rate**：`v[16..19]`（三进制字 S0 = (v16, v17)、S1 = (v18, v19)）——消息平面注入区；
  - **capacity**：`v[20..23]`（三进制字 S2 = (v20, v21)、S3 = (v22, v23)）——仅内部演化，不直接注入消息。
- 初始化（`compress_b` 内，紧随轨 A/B 初始化之后）：
  - `v[16] = h[0] & 0xFFFFFFFF; v[17] = rr32(h[4], 7)`（S0 由链值左半派生）；
  - `v[18] = h[1] & 0xFFFFFFFF; v[19] = rr32(h[5], 13)`（S1）；
  - `v[20] = iv[0] & 0xFFFFFFFF; v[21] = rr32(iv[4], 7)`（S2 由 IV 派生）；
  - `v[22] = iv[1] & 0xFFFFFFFF; v[23] = rr32(iv[5], 13)`（S3）；
  - 末块标记：`if last { v[19] = (v[19] ^ 0xFFFFFFFF) & 0xFFFFFFFF }`（rate 高位翻转，等效海绵 padding 边界）。

### 2.2 常量

- 新增**海绵轨轮常量表 `tsha_bscon`**（16 个 32 位字），与 `tsha_biv`/`tsha_brcon` 并列的库级惰性表（`var tsha_bscon: table<i64>;` + `ensure_bscon()`）。
- 派生：独立种子 `SEED_S = "TSHA1-2026-b-sponge-v1"`，扩展方式与现有常量完全一致：`SHA-256(SEED_S || u64be(k))` 计数器流（k=0,1,2,…），取前 16 字。**不吃** `SEED_B`/`tsha_brcon`（保证 b 的 IV/RCON 向量不变，只增不改）。
- 惰性构建函数 `ensure_bscon()`：`len(tsha_bscon) > 0` 则直接返回；否则按头部常量扩展注释逐字 push（与 ensure_brcon 同风格）。

### 2.3 每轮海绵处理（并入现有 R=14 轮循环体）

在现有一轮的最后（轨间耦合之后、轮常量注入之后），追加以下海绵轨处理（共 5 步，全部在 `r` 循环内）：

1. **吸收（absorb）**：消息平面按新移位量注入 rate——
   `var sA = (r * 3 + (skey >> 12) & 7) & 31; var sB = (r * 7 + ((skey >> 15) & 7)) & 31;`
   `var (a0m, a0n) = tadd2(v[16], v[17], rrp(M0, sA), rrp(N0, sA)); v[16] = a0m & 0xFFFFFFFF; v[17] = a0n & 0xFFFFFFFF;`
   `var (a1m, a1n) = tadd2(v[18], v[19], rrp(M1, sB), rrp(N1, sB)); v[18] = a1m & 0xFFFFFFFF; v[19] = a1n & 0xFFFFFFFF;`

2. **海绵置换（8 字环式）**：对 v[16..23] 做 1 次环式三进制置换（复用 tadd2/tmul2/quant3/rrp）——
   ```
   (p0m, p0n) = tadd2(v[16], v[17], rrp(v[18], sA+1), rrp(v[19], sA+1))
   (p1m, p1n) = tadd2(v[18], v[19], rrp(v[20], sA+5), rrp(v[21], sA+5))
   (p2m, p2n) = tadd2(v[20], v[21], rrp(v[22], sB+2), rrp(v[23], sB+2))
   (p3m, p3n) = tadd2(v[22], v[23], rrp(v[16], sB+6), rrp(v[17], sB+6))
   (q1m, q1n) = tmul2(p0m, p0n, p2m, p2n)
   (q2m, q2n) = tmul2(p1m, p1n, p3m, p3n)
   mj = quant3(p0m, p0n, p1m, p1n, p2m, p2n)
   v[16] = p0m & 0xFFFFFFFF; v[17] = p0n & 0xFFFFFFFF
   v[18] = (p1m ^ q1m) & 0xFFFFFFFF; v[19] = (p1n ^ q1n) & 0xFFFFFFFF
   v[20] = (p2m ^ q2m) & 0xFFFFFFFF; v[21] = (p2n ^ q2n) & 0xFFFFFFFF
   v[22] = (p3m ^ mj) & 0xFFFFFFFF; v[23] = (p3n ^ rrp(mj, sA+7)) & 0xFFFFFFFF
   ```

3. **轮常量注入（海绵轨独立常量）**：
   `v[16] = (v[16] ^ tsha_bscon[r & 15]) & 0xFFFFFFFF`
   `v[19] = (v[19] ^ rrp(tsha_bscon[(r + 3) & 15], r * 3)) & 0xFFFFFFFF`

4. **与轨 A/B 双向耦合**（海绵 rate 出 → 轨 A/B；轨 A/B 状态回填海绵 capacity）：
   ```
   (c0m, c0n) = tadd2(v[0], v[1], rrp(v[16], r*5), rrp(v[17], r*5))   // 海绵 S0 → 轨 A
   v[0] = c0m & 0xFFFFFFFF; v[1] = c0n & 0xFFFFFFFF
   (c1m, c1n) = tadd2(v[8], v[9], rrp(v[18], r*7), rrp(v[19], r*7))   // 海绵 S1 → 轨 B
   v[8] = c1m & 0xFFFFFFFF; v[9] = c1n & 0xFFFFFFFF
   (c2m, c2n) = tadd2(v[20], v[21], rrp(v[4], r*11), rrp(v[5], r*11)) // 轨 A → 海绵 capacity
   v[20] = c2m & 0xFFFFFFFF; v[21] = c2n & 0xFFFFFFFF
   (c3m, c3n) = tadd2(v[22], v[23], rrp(v[12], r*13), rrp(v[13], r*13)) // 轨 B → 海绵 capacity
   v[22] = c3m & 0xFFFFFFFF; v[23] = c3n & 0xFFFFFFFF
   ```

5. **轮常量注入（轨 A/B 既有注入不变）**：保留现有 `v[0] ^= tsha_brcon[r&15]`、`v[9] ^= rrp(...)` 两行，位置在步骤 4 之后。

> 顺序约定：吸收 → 海绵置换 → 海绵常量注入 → 双轨耦合 → 既有常量注入。此顺序固定。

### 2.4 折回与链值更新（compress_b 末尾）

现行折回仅折叠双轨。三轨版改为折叠**双轨 + 海绵 rate**（capacity 不直接折回 h，仅参与内部演化与终筛）：

```
while i < 8 {
    h[i] = (h[i] ^ v[2*i] ^ rrp(v[2*i+1], i*3)
            ^ rrp(v[16 + (i & 3) * 2], i*7) ^ rrp(v[17 + (i & 3) * 2], i*7)) & 0xFFFFFFFF
    i = i + 1
}
// rate 4 字全部参与：i 0..7 循环两遍覆盖 v16..v19（i&3 取千位）。
```

### 2.5 digest_b 末端与 fin_synth

- **fin_synth 不改**：仍只接收 8 字链值 h（S=4 收束轮逻辑与现行完全一致）。
- digest_b 增补一行（`fin_synth(h)` 之前）：把海绵 capacity 末块折叠进 h——
  ```
  // 末块海绵 capacity 折回链值（终筛前）
  h[0] = (h[0] ^ v[20]) & 0xFFFFFFFF; h[1] = (h[1] ^ rr32(v[21],7)) & 0xFFFFFFFF
  h[2] = (h[2] ^ v[22]) & 0xFFFFFFFF; h[3] = (h[3] ^ rr32(v[23],7)) & 0xFFFFFFFF
  ```
  实现方式：在 digest_b 中维护一个 `sp_last` 4 字小表（`table<i64>`，末块压缩后从调用点带回），或让 compress_b 在 `last` 时把 v[20..23] 写回 h 追加折叠字段——**选择：digest_b 维护 `sp: table<i64>`（4 字），末块 `compress_b(h, msg, n, pos, t_lo, t_hi, true, sp)` 由 compress_b 把 v[20..23] 填入 sp，digest_b 在 fin_synth 前按上式折回 h。**

> 注意：compress_b 签名为兼顾历史调用方，新增可选尾参 `sp: table` 默认值由调用方传入——tie 跨模块默认参数补齐不可靠（历史教训），故 **digest_b 内显式创建 sp 表并无条件传入**（不依赖默认参数）。

### 2.6 验证向量与参考生成器

- **gen_tsha1bx.py 必须同步**：`compress_b`/`digest_b` 按上述 2.1–2.5 重写（Python 与 tie 逐式一致），重新输出 12 组 b 向量（empty/abc/a1000/b55/b56/b63/b64/b65/b127/b128/b129/b256），同时重算 x 向量（见 §3）。
- `tsha1b_probe.tie` / `tsha1x_probe.tie` 内嵌向量以生成器输出为准整体替换。
- 验收：`tsha1b_probe.exe` 12+12 断言全 PASS；`tsha1_len_probe`（位长/进制/非法/前缀）全 PASS；`tsha1f/tsha1r` 探针不受影响仍全 PASS。

## 3. tsha1x 四轨独立重构（含第四种算法）

### 3.1 候选：第四种算法权衡

第四轨要求与既有三轨同构但**算法哲学完全不同**（不重叠：位平面代数 ≠ 链式压缩 ≠ 海绵态）：

| 候选 | 机制 | 优点 | 缺点 | 评价 |
| --- | --- | --- | --- | --- |
| A. LFSR 反馈移位 | 状态字作反馈移位寄存器（反馈多项式 + 输入异或），位运算纯 | 极简、成本低、与位平面/海绵/链式均异质；天然周期扩散 | 纯 LFSR 线性，须配非线性化（吸收量化门） | **推荐**（结合 quant3 门控去线性化） |
| B. 混沌映射类 | 帐篷/Logistic 整数化（定点 fold） | 动力系统异质扩散、强非线性 | 定点缩放破坏可复现性；论证复杂 | 备选 |
| C. Feistel 网络 | 左右半无钥轮，环式轮函数 | 密码学成熟、易论证 | 与 ARX/位平面生态位相近，异质性弱 | 不选 |
| D. 位平面矩阵置乱 | Latin 方/置换矩阵重排 (M,N) 平面 | 与位平面天然契合 | 表驱动需常量表；扩散维度与位平面重叠 | 不选 |

**选定：A（LFSR 反馈移位轨），并用 quant3 门控做非线性化**——吸收消息字时经「LFSR 反馈 ⊕ 量化门 × 移位」复合，避免纯线性。

### 3.2 tsha1x 结构总览（四轨并行 + 最后综合）

- **轨 A**：三进制位平面轨（tadd2/tmul2/quant3/rrp，R_X 轮并行扩散）——复用 tsha1f 压缩器同构；
- **轨 B**：三进制位平面轨变体（不同相位/常量）——复用 tsha1b 同构；
- **轨 C**：海绵轨（rate/capacity，§2 海绵语义同款）——复用 tsha1b 三轨版同构；
- **轨 D（新增）**：LFSR 反馈移位轨（第四种算法），状态 4 字；
- **末段**：四轨状态投影折叠 → `fin_synth_x`（终筛）→ 64 hex。
- 工作状态：`v[0..31]`（轨 A=0..7、轨 B=8..15、轨 C=16..23、轨 D=24..27，保留 28..31 为综合暂存）。

### 3.3 轨 D（LFSR）规格

- 状态：`d[0..3]`（4 个 32 位字）。
- 初始化：`d[k] = parse_hex32(摘要状态派生)`——取压缩链 h 与 IV 的线性混合（与轨 A/B 初始化派生风格一致，见实施时以常量派生注释为准，**固定且可复现**）。
- 每轮（R_X 循环内）：
  1. **反馈**：`fb = (d[3] >> 16) ^ d[1]`（抽取高位混合）；
  2. **吸收**：`d[0] = (d[0] ^ rrp(M0, sX)) & 0xFFFFFFFF; d[1] = (d[1] ^ rrp(N0, sX)) & 0xFFFFFFFF`（消息平面注入）；
  3. **移位**：`d[k+1] ← d[k]`（左移，末位由 fb 补入），`d[3] = (fb ^ quint3(...))`——`quint3` 取轨 A/B 某字对的 quant3 输出做非线性门控（去线性化）；
  4. **与轨 A/B 耦合**：`v[24] ↔ v[2]`、`v[25] ↔ v[6]`、`v[26] ↔ v[10]`、`v[27] ↔ v[14]`（四向平衡加/tmul 混合）；
  5. **常量注入**：`tsha_xrcon`（新种子 `SEED_XD = "TSHA1-2026-x-lfsr-v1"` 扩展 16 字）。
- R_X：**16 轮**（四模型最高）。

### 3.4 常量与实现文件清单

- 新增库级常量表：`tsha_xdcon`（轨 D 轮常量）、可能复用 `tsha_bscon`（轨 C）；轨 A/B 复用 `tsha_fiv/tsha_frcon`、`tsha_biv/tsha_brcon` 或独立 x 常量（实施时二选一，须在 gen_tsha1x.py 与 std/tsha1.tie 保持一致——**选择：独立 x 常量族 `tsha_xiv/tsha_xrcon`（SEED_X = "TSHA1-2026-x-256-v1"），轨 C 复用标有 SEED_S 的 `tsha_bscon`**）。
- `digest_x` 完全重写（脱离 f+b 排列组合），`tsha1x/tsha1x_hex` 包装不变。
- 新参考生成器：`tests/tsha_probe/gen_tsha1x.py`（x 独立四轨实现，与 tie 逐字节一致），`gen_tsha1bx.py` 保留仅输出 b。
- `tsha1x_probe.tie` 向量以新生成器输出为准。

### 3.5 验证向量（x）

- 12 组向量（empty/abc/a1000/b55/b56/b63/b64/b65/b127/b128/b129/b256），由 gen_tsha1x.py 生成并与 tie 编译结果交叉核对，逐字节一致。
- 位长/进制/前缀一致性探针（tsha1_len_probe 的 x 条目）同步更值并全 PASS。

## 4. 分步实施与验收

| 步骤 | 内容 | 提交 | 验收 |
| --- | --- | --- | --- |
| S1 | std/tsha1.tie：compress_b/digest_b 三轨化（§2）；ensure_bscon；gen_tsha1bx.py 同步 | 1 个 commit | tsha1b 探针 12+12 PASS、len 探针全 PASS、f/r 探针不回归 |
| S2 | std/tsha1.tie：digest_x 四轨重写（§3）；ensure_bscon/ensure_xdcon；gen_tsha1x.py 新建；tsha1x_probe.tie 更新 | 1 个 commit | tsha1x 探针 12+12 PASS、x 在 len 探针条目更新后全 PASS |
| S3 | 重跑 scripts/bench/tsha1-bench → 刷新 tsha1-bench-out.txt | 1 个 commit | 输出含四模型新吞吐 |
| S4 | 论文：gen_tsha1_paper.py（3.4/3.5/表1/表2/表3/附录 A.3–A.4/摘要性能表述）+ gen_tsha1_arch.py 重绘；重新生成 tsha1-paper.docx、tsha1-arch.png | 1 个 commit | docx 打开无误、KAT 与基准数字与实现一致 |

**实施权限**：子代理执行时以本文档为唯一规格源；任何偏离须先回本文档改版，不得自行发明常量/轮数/公式。

## 5. 已知取舍与风险

- 海绵轨保持 R_B=14 不变，预期 b 吞吐略降（每轮新增 ~5 步位运算），以论文 §5.3 新基准呈现；若降幅 >30% 需回到本文档评估。
- LFSR 轨的非线性化依赖 quant3 门的强度；其独立安全性未独立审计，论文 §4 须标注（沿用"未经第三方审计"声明）。
- 三轨/四轨使 b、x 的 KAT 全变，涉及探针/论文/基准三处联动，实施须一次对齐，禁止部分提交导致中间态不一致。