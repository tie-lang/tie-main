# SLH-DSA（SPHINCS+）前置分析：SHAKE128 系 128s + 域分离助手设计
*EN: SLH-DSA (SPHINCS+) Pre-Analysis: SHAKE128-Based 128s + Domain-Separation Helper Design*

> 状态：**前置分析 / 设计注记——非完整实现**。阶段二（SLH-DSA）为远期；本文梳理参数
> 集、ADRS/域分离助手与后续专项边界。**SLH-DSA 完整实现留待后续专项**（FORS + XMSS-MT
> + Hypertree + 签名/验签 + KAT，明显超出单任务容量，见文末工作量诚实评估）。
> EN: Status: **pre-analysis / design notes — not a complete implementation**. Phase Two (SLH-DSA) is long-term; this document sorts out the parameter sets, the ADRS/domain-separation helper, and the boundary of the follow-up task. **The complete SLH-DSA implementation is left for a later dedicated task** (FORS + XMSS-MT + Hypertree + sign/verify + KAT, clearly beyond the capacity of a single task; see the honest effort assessment at the end).
> 前置依赖：`std/shake.tie`（SHAKE128/256 XOF，本仓库阶段一已交付）。关联：
> EN: Prerequisite: `std/shake.tie` (SHAKE128/256 XOF; delivered in Phase One of this repository). Related:
> `docs/plans/pqc-roadmap.md`（纯 tie 决策：SLH-DSA-SHA2 首发、SHAKE 系可选）。
> EN: `docs/plans/pqc-roadmap.md` (pure-tie decision: SLH-DSA-SHA2 first; the SHAKE family is optional).

## 1. SLH-DSA 定位（Hash-based signature，HBS）
*EN: 1. Positioning of SLH-DSA (Hash-Based Signature, HBS)*

- 纯哈希签名：不依赖格/NTT/模 q 环，安全假设最保守（只靠哈希抗碰撞/抗原像）。
  EN: A pure hash-based signature: does not depend on lattices/NTT/mod-q rings, and its security assumption is the most conservative (relying only on hash collision/preimage resistance).
- 组成：**FORS（Few-Time Signature）+ XMSS-MT（多树哈希）** = 超树（Hypertree）+ 一次/
  少次签名。核心原语是**可微调哈希（TweakedHash）**：
  EN: Composition: **FORS (Few-Time Signature) + XMSS-MT (multi-tree hash)** = a Hypertree + one-time/few-time signatures. The core primitive is the **TweakedHash**:
  - `H`（树/叶子哈希，n 字节）、`F`（FORS 叶子，n 字节）、`Hmsg`（消息摘要，m 字节）、
    `PRF` / `PRF_m`（伪随机，密钥派生），均经 ADRS（地址）做**域分离**。
    EN: `H` (tree/leaf hash, n bytes), `F` (FORS leaf, n bytes), `Hmsg` (message digest, m bytes), `PRF`/`PRF_m` (pseudorandom, key derivation) — all go through an ADRS (address) for **domain separation**.
  - 域分离的目的：同一底层 Keccak 基础上，为不同用途/不同树节点生成不相关哈希，
    消除路径/索引碰撞攻击。
    EN: Purpose of domain separation: on the same underlying Keccak, generate unrelated hashes for different purposes/different tree nodes, eliminating path/index-collision attacks.
- tie 侧咬合：STD 哈希族（sha256/sha3）+ 新交付 `shake` 提供变长 XOF；tie 无原语 buffer
  与 memzero（用 `sensitive` 槽覆写约定），字节输入输出统一 hex（见 pqc-roadmap §3.5）。
  EN: tie-side fit: the STD hash family (sha256/sha3) + the newly delivered `shake` provide variable-length XOF; tie has no primitive buffer or memzero (relying on the `sensitive` slot-overwrite convention), and byte IO is uniformly in hex (see pqc-roadmap §3.5).

## 2. 参数集选择：**SLH-DSA-SHAKE-128s**（本阶段前置分析锁定）
*EN: 2. Parameter-Set Selection: **SLH-DSA-SHAKE-128s** (locked in by this phase's pre-analysis)*

| 参数 | 值 | 说明 |
| --- | --- | --- |
| shake | SHAKE128 基（n=16=128bit 安全，S 档小签名） | 签名 7856 字节（任务核对）|
| n | 16（哈希输出字节） | H/F/PRF 输出 |
| w | 16（Winternitz 基） | WOTS+ 链长 |
| len / len1 / len2 | 35 / 32 / 3 | WOTS+ 签名元素数（含校验和）|
| h | 63 | 超树总高 |
| d | 7 | 分层数（子层高 hp=9）|
| k | 14 | FORS 树数目 |
| t=2^a, a | 16, 4 | FORS 每树叶子数与指数 |
| m | 30 | Hmsg 消息摘要长度（128s）|
| 熵 | 密钥生成需系统 CSPRNG（BCryptGenRandom），`rdu/rnd`(xorshift64) 不可用 | |

EN: Parameter table for SLH-DSA-SHAKE-128s: shake = SHAKE128 base (n=16, 128-bit security, S-tier small signatures, signature 7856 bytes); n=16, w=16, len/len1/len2=35/32/3, h=63, d=7, k=14, t=2^a with a=4 (t=16), m=30; entropy must come from the system CSPRNG (`BCryptGenRandom`), never `rdu/rnd` (xorshift64).

> 选 SHAKE 系而非 SHA2 系的理由：SHA2 系不改动伴随哈希，但重复调用 128 位截断需精细；
> SHAKE 基直接复用本仓库刚交付的 `shake128/256` XOF（变长、可任意挤压），twitter 哈希：
> `T(pk_seed, ADRS, M) = SHAKE256(pk_seed || ADRS || M)` 系均为 XOF 一阶应用，最顺滑。
> EN: Why the SHAKE family rather than SHA2: the SHA2 family leaves the accompanying hash untouched, but careful 128-bit truncation on repeated calls is needed; the SHAKE base directly reuses the just-delivered `shake128/256` XOF (variable-length, arbitrarily squeezable), and the "twitter" hashes such as `T(pk_seed, ADRS, M) = SHAKE256(pk_seed || ADRS || M)` are all one-step XOF applications, which is the smoothest.

## 3. ADRS / 域分离助手设计（阶段二先行的原子件）
*EN: 3. ADRS / Domain-Separation Helper Design (the Atomic Piece to Do First in Phase Two)*

ADRS（Address，域分离地址）为 **32 字节**，字节布局（FIPS 205 §4.2，大端）：
EN: The ADRS (Address, the domain-separation address) is **32 bytes**, laid out as follows (FIPS 205 §4.2, big-endian):

```
偏移  长度  字段                    说明
0     4     layer                超树层号（WOTS+FORS 在叶子层，type 已有，layer 主要给 TREE 用）
4     8     tree                 该层树号（子树在超树中的位置）
12    4     type                  用途类型：
                                    WOTS_HASH=0, WOTS_PK=1
                                    TREE=2, FORS_HASH=4, FORS_PK=5, FORS_ROOTS=6
16    16    类型相关（前 12 字节有效 + 4 字节填充）
```

类型相关 16 字节（每字段 4 字节大端，不足补零——**域分离敏感点：不同 type 用同一
32B 槽位，若字节布局歧义会导致碰撞**）：
EN: The type-dependent 16 bytes (each field 4 bytes big-endian, zero-padded when short — **a domain-separation sensitive point: different types share the same 32B slot, and ambiguous byte layouts would cause collisions**):

- `WOTS_HASH(0)`：keypair(4) + chain(4) + hash(4) + pad(4)
  EN: `WOTS_HASH(0)`: keypair(4) + chain(4) + hash(4) + pad(4).
- `WOTS_PK(1)`   ：keypair(4) + pad(12)
  EN: `WOTS_PK(1)`: keypair(4) + pad(12).
- `TREE(2)`      ：keypair(4) + tree_height(4) + tree_index(4) + pad(4)
  EN: `TREE(2)`: keypair(4) + tree_height(4) + tree_index(4) + pad(4).
- `FORS_HASH(5)`：keypair(4) + h_t(4) + hash(4) + pad(4)（h_t=FORS 叶子序号）
  EN: `FORS_HASH(5)`: keypair(4) + h_t(4) + hash(4) + pad(4) (h_t = FORS leaf index).
- `FORS_PK(5)`   ：keypair(4) + tree_height(4) + tree_index(4) + pad(4)
  EN: `FORS_PK(5)`: keypair(4) + tree_height(4) + tree_index(4) + pad(4).
- `FORS_ROOTS(6)`：pad(16)
  EN: `FORS_ROOTS(6)`: pad(16).

TweakedHash（全部经 `std/shake.shake256` 变长）：
EN: TweakedHash (all via the variable-length `std/shake.shake256`):
- `F(pk_seed, ADRS, M)`    = SHAKE256(pk_seed || ADRS_fors_hash || M),   取 n 字节
  EN: `F(pk_seed, ADRS, M)` = SHAKE256(pk_seed || ADRS_fors_hash || M), taking n bytes.
- `H(pk_seed, ADRS, M)`    = SHAKE256(pk_seed || ADRS_tree     || M),   取 n 字节
  EN: `H(pk_seed, ADRS, M)` = SHAKE256(pk_seed || ADRS_tree     || M), taking n bytes.
- `PRF(seeds, ADRS)`       = SHAKE256(seeds || ADRS_wots_pk),           取 n 字节
  EN: `PRF(seeds, ADRS)` = SHAKE256(seeds || ADRS_wots_pk), taking n bytes.
- `Hmsg(R, pk, ADRS_HMSG, M)` = SHAKE256(R || pk || ADRS_hmsg || M),    取 m 字节
  EN: `Hmsg(R, pk, ADRS_HMSG, M)` = SHAKE256(R || pk || ADRS_hmsg || M), taking m bytes.

**自洽探针（阶段二 b 项，无权威 KAT 时的兜底）**：对同一 (pk_seed, ADRS, M) 输出确定
唯一、且仅翻转 ADRS 任一个 type/索引字段即整体变化——验证域分离敏感与确定性。本仓库
阶段一并未带 SLH-DSA KAT（FIPS 205 官方向量需单独落地），故完整实现须以 NIST ACVP /
openssl `slh_dsa_*` 自检向量逐字节收敛（见 pqc-roadmap §6）。
EN: **Self-consistency probe (Phase Two item b; the fallback when there is no authoritative KAT)**: for the same (pk_seed, ADRS, M), the output is deterministic and unique, and flipping any single type/index field of the ADRS changes the whole output — verifying domain-separation sensitivity and determinism. This repository's Phase One did not ship an SLH-DSA KAT (the FIPS 205 official vectors must be landed separately), so a complete implementation must converge byte-for-byte against NIST ACVP / openssl `slh_dsa_*` self-test vectors (see pqc-roadmap §6).

## 4. 分阶段落地建议（阶段二内部再拆分，每步挂钩）
*EN: 4. Staged Implementation Recommendation (split further within Phase Two; every step hooked)*

| 子步 | 交付 | 验收 |
| --- | --- | --- |
| 2.1 | `std/slhdsa`：ADRS 构造 + 字节拼接 + `F/H/PRF/Hmsg` 域分离哈希 | 自洽探针：确定性 + 域分离敏感 |
| 2.2 | WOTS+ 密钥/签名/验签（链函数 `chal` + 基 w 对数展开） | WOTS+ KAT |
| 2.3 | FORS（每树 t 叶）+ XMSS（一个 h/d 子树） | 树哈希 KAT |
| 2.4 | XMSS-MT 超树 + 密钥生成(接系统熵) + 签名 + 验签 | FIPS 205 SLH-DSA-SHAKE-128s 全 KAT |

EN: Sub-step 2.1 delivers ADRS construction + byte concatenation + the F/H/PRF/Hmsg domain-separation hashes under `std/slhdsa` (verified by self-consistency probes); 2.2 delivers WOTS+ key/sign/verify; 2.3 delivers FORS + XMSS; 2.4 assembles XMSS-MT hypertree + key generation (with system entropy) + sign + verify against the full FIPS 205 SLH-DSA-SHAKE-128s KAT.

## 5. 工作量为实评估（为何本期停在前置）
*EN: 5. Honest Effort Assessment (Why This Phase Stops at the Pre-Analysis)*

FIPS 205 全量 = FORS 少次签名 + WOTS+（含校验和编码）+ XMSS-MT 分层树哈希 + Tweak
上下文（四类 ADRS）+ 签名/验签 + 密钥派生接入系统 CSPRNG，且需逐字节对齐官方 KAT/ACVP。
EN: Full FIPS 205 = FORS few-time signature + WOTS+ (including checksum encoding) + XMSS-MT layered-tree hashing + tweak contexts (four ADRS kinds) + sign/verify + key derivation connected to the system CSPRNG, and it must align byte-for-byte with the official KAT/ACVP.
代码量估计 1500+ 行纯 tie（pqc-roadmap §2 亦估 SLH-DSA 约 1500+ 行），显著超过单任务
容量。故**本期交付：阶段一 SHAKE XOF 完全落地 + 本文前置分析与域分离助手设计；SLH-DSA
完整实现明确留待后续专项**，按 §4 子步顺序推进。
EN: The code volume is estimated at 1500+ lines of pure tie (pqc-roadmap §2 also estimates SLH-DSA at roughly 1500+ lines), clearly beyond a single task's capacity. So **this phase delivers: Phase One's SHAKE XOF fully landed + this pre-analysis and the domain-separation helper design; the complete SLH-DSA implementation is explicitly deferred to a later dedicated task**, to proceed in the §4 sub-step order.