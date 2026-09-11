# p.7.1.6 库树收敛：std/ext/rdu ↔ lib_v1 定位

**日期** / Date: 2026-09-11 · **分支** / Branch: p.7 · **基准 HEAD**: b5704ac
**类型** / Type: 库树定位文档化（机制框架 + 文档，无实际库文件迁移）
**设计依据** / Spec: `docs/superpowers/specs/2026-08-29-plugin-kernel-design.md` §6.5（安全算法底座）
**关联** / Related: `docs/plans/2026-09-11-p7117-security-base-inventory.md`（p.7.1.7 审计）

> EXEC BRIEF: This document defines the standard/extension/reduced library tree
> (`std` / `ext` / `rdu`) places them against the immutable library-v1 archive
> (`lib_v1`), and cross-references the classification in spec §6.5 plus the
> p.7.1.7 audit's suggested migrations (logged only, no moves).

---

## 1. 结论摘要 / Executive Summary

| 指标 | 数量 |
|---|---|
| 库层 | 4 类（std / ext / rdu / lib_v1 存档） |
| CLI 子命令注册项（本任务新增，对齐 `tie <子命令>`） | 13 项（help/init/add/remove/install/update/build/run/publish/pack/verify/search/info） |
| 设计稿 §6.5 归属类别 | 7 类（哈希/MAC/对称/KDF/非对称/后量子/TSHA） |
| p.7.1.7 建议迁移项（**只记不改**） | 5 项 |

本任务落点：`compiler/keel/keel_cli.tie`（CLI 注册表）+ driver 接线 +
库树定位文档。库文件**零移动**——设计稿 §6.5 执行纪律与 p.7.1.7 一致：迁移建议只记入
文档，不实际移动（避免扰动已通过回归的库）。

---

## 2. 三库定位表 / Library-Layer Placement

| 库层 | 角色 / Role | 责任 / Responsibility | 典型内容 / Typical Contents |
|---|---|---|---|
| `std/` | 标准库 · Standard core | 语言核心自带、无外部依赖、随编译器发行；通用基础（字符串/集合/时间/进程）+ 密码学首选层（哈希/MAC 底座） | `string/bytes/json/csv/sort/set/map/regex`；哈希：`sha256/sha512/sha1/sha3/shake/blake2/blake3/xxh3/siphash`；MAC：`hmac/poly1305/ascon_mac`；KDF：`hkdf/pbkdf2`；TSHA：`tsha1/tsha1_w48` |
| `ext/` | 扩展库 · Extensions | 平台/领域扩展，依赖外部或重型，按需引入、不随核心；大项/重型/内存硬算法与工具 | `aes/scrypt/argon2`；`tls/http…` 大套件；`gfx/svg/png/qr/xml/html/codec/ml`；非对称/后量子评估层 |
| `rdu/` | 精简库 · Reduced density | 面向受限环境的精简复刻；同一算法给出小 footprint 变体（不复刻重型） | `rdu_bits/rdu_ascii/rdu_math/rdu_fixed/rdu_rnd/rdu_rdb/rdu_crc`；`rdu_poly1305/rdu_ascon_mac` |
| `lib_v1/` | 不可变归档 · Immutable archive | **library-v1 不可变归档**：语义冻结、不回填不迁移、只读存档 | 历史冻结发行版内容（归档定位；设计稿 §6.5 定位语） |

**定位原则** / Principles：
- `std` = 核心 + 安全底座首选；`ext` = 领域/重型/可选；`rdu` = 同一算法的受限精简变体。
- `lib_v1` 是**不可变归档**，不在其上改写；任何"应该放哪层"的讨论都相对
  `std/ext/rdu` 三库（§6.5 归属）。

---

## 3. 设计稿 §6.5 归属交叉引用 / §6.5 Cross-Reference

| 类别 | 算法 | 设计稿 §6.5 归属 | 现实际位置 | 一致性 |
|---|---|---|---|---|
| 哈希/校验 | SHA-2/SHA-3/BLAKE2/3/XXH3/SipHash/MD5/SHA-1（兼容标注） | std | `std/*` | ✓ |
| MAC | HMAC / Poly1305 / Ascon-MAC | std + rdu 复刻 | `std` + `rdu`（HMAC 的 rdu 复刻缺失 → 缺口 G1） | 部分 ✓ |
| 对称加密 | AES | ext | `ext/aes` | ✓ |
| 对称加密 | ChaCha20 | **std** | `ext/chacha20` | **归属层偏差** |
| 对称加密 | Ascon-128a/AEAD | **rdu** | `ext/ascon_aead` | **归属层偏差** |
| KDF/口令 | HKDF / PBKDF2 | std | `std` | ✓ |
| KDF/口令 | scrypt / Argon2id | ext | `ext` | ✓ |
| 非对称 | Ed25519 / X25519 / ECDSA-P256 / RSA | ext | `std/ed25519` `std/x25519` `std/ecdsa_p256`, `ext/ecdsa`, RSA 缺独立模块 | **归属层偏差** / 缺口 |
| 后量子 | ML-KEM / ML-DSA / SLH-DSA | ext（评估后列） | 缺失（计划预案在 pqc-roadmap） | 缺口 |
| TSHA 族 | tsha1 f/b/x/r + w48 | std（核心） | `std/tsha1` `std/tsha1_w48` | ✓（p.7.1.8 专属） |

---

## 4. p.7.1.7 审计建议迁移（只记不改）/ Suggested Migrations (logged only)

以下来自 `docs/plans/2026-09-11-p7117-security-base-inventory.md` §4。**本任务 /
任何任务均不实际移动**；仅在库树收敛时作为归属共识固化为目标态。

1. `ext/chacha20.tie` → **std**（设计稿对称类 ChaCha20 归 std）。
2. `ext/ascon_aead.tie` → **rdu**（设计稿 Ascon 归 rdu；受限环境精简 AEAD）。
3. `std/ed25519.tie` → **ext**（非对称归 ext；独立大工程候选）。
4. `std/x25519.tie` → **ext**（非对称归 ext）。
5. `std/ecdsa_p256.tie` → 归并 **ext**（非对称归 ext；`ext/ecdsa` 为 extern 高效版）。

缺口（不入库树收敛，见 p.7.1.7 Gap Register）：`rdu/rdu_hmac.tie`（G1）、AES-CTR/XTS（G2）、
AES-GCM 独立接口（G3）、RSA 独立模块（G4）、ML-KEM/ML-DSA/SLH-DSA（G5–G7）。

---

## 5. 落地窗口 / Landing

本任务 CLI 注册化落点：`compiler/keel/keel_cli.tie` + `compiler/keel/keel_boot.tie` +
`compiler/driver.tie`（tie `<子命令>` 层注册化分派；tiec 自身参数语义逐字节不变）。
库树文档交付 `docs/plans/2026-09-11-p7116-libtree-convergence.md`。真实库文件迁移留待
后续 p.7.1.x（审计结论确认后单列迁移任务执行）。

---

## EN — p.7.1.6 Library-Tree Convergence: `std`/`ext`/`rdu` ↔ `lib_v1` Placement

Date 2026-09-11 · Branch p.7 · Base HEAD b5704ac · Mechanism framework + doc, **zero library moves**.

**Placement table** — `std/` standard core (self-contained, ships with compiler; hash/MAC base +
general util), `ext/` extensions (platform/domain, heavy or optional), `rdu/` reduced-density
lightweight replicas of the same algorithms for constrained targets, `lib_v1/` immutable
library-v1 archive (frozen, read-only, never rewritten). Placement discussion is relative to
`std/ext/rdu` per design spec §6.5.

**Cross-reference** — hash/checksum → std ✓; MAC → std + rdu replica (HMAC rdu replica missing,
G1); AES → ext ✓; ChaCha20 → **std** (currently `ext/chacha20`, placement drift); Ascon-AEAD →
**rdu** (currently `ext/ascon_aead`, drift); HKDF/PBKDF2 → std ✓; scrypt/Argon2id → ext ✓;
Ed25519/X25519/P-256 → **ext** (currently std, drift); post-quantum → ext (gap); TSHA family →
std/core ✓ (owned by p.7.1.8).

**p.7.1.7 suggested migrations (logged only, no moves)**: ChaCha20→std, Ascon-AEAD→rdu,
Ed25519→ext, X25519→ext, ECDSA-P256→merge ext. Gaps deferred per p.7.1.7 Gap Register.

CLI layer (this task): `compiler/keel/keel_cli.tie` + `keel_boot` + `driver.tie` — registers
the 13 `tie <subcommand>` keys and dispatches by table; tiec's own `-o/-O/--emit-ir/...` args
remain untouched (byte-identical).