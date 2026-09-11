# p.7.1.7 安全算法底座：分类清单与缺口报告

**日期** / Date: 2026-09-11 · **分支** / Branch: p.7 · **基准 HEAD**: 0adeb65
**类型** / Type: 审计交付（核对 + 分类 + 缺口清单），零代码补缺
**设计依据** / Spec: `docs/superpowers/specs/2026-08-29-plugin-kernel-design.md` §6.5

> 执行纪律（按设计稿 §6.5）：哈希/校验 → std；MAC → std + rdu 复刻；
> 对称加密 → AES 归 ext / ChaCha20 归 std / Ascon 归 rdu；KDF（HKDF/PBKDF2）→ std，
> scrypt/Argon2id → ext；非对称 → ext；后量子 → ext（评估后列）；TSHA 族 → std（p.7.1.8 专属，只核对不下结论）。
> 迁移项一律只记入"建议迁移"，不实际移动（避免动已通过回归的库）。

---

## 1. 结论摘要 / Executive Summary

| 指标 | 数量 |
|---|---|
| 设计稿所列算法类别 | 7 类（哈希/MAC/对称/KDF/非对称/后量子/TSHA） |
| 已存在（含兼容标注） | 25 项 |
| 缺失（大项或依赖未就绪，列入缺口不实现） | 7 项 |
| 归属层偏差（建议迁移，不移动） | 6 项 |
| 本次补缺实现 | 0 项 |

本次为纯审计交付：**零代码改动零补缺模块零探针**。抽查 5 个已存在算法文件入口函数均确认存在。
大工程（RSA 独立模块、AES GCM/CTR/XTS、后量子全系）按设计稿归 ext 且实现量远超"单文件中等规模"，
一律写入缺口报告，不纳入本次实现。

---

## 2. 分类清单 / Inventory

### 哈希/校验 / Hash & checksum —— 归属 std（设计稿）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| SHA-2 族（SHA-224/256/384/512） | `std/sha256.tie` `std/sha512.tie` | `sha256.sha256` `sha512.sha512(_bytes)` | 已有 ✓ | — |
| SHA-3（Keccak） | `std/sha3.tie` | `sha3.*` | 已有 ✓ | — |
| SHAKE128/256 | `std/shake.tie` | `shake.shake128/256` | 已有 ✓ | — |
| BLAKE2s/b | `std/blake2.tie` | `blake.blake2s/blake2b` | 已有 ✓ | — |
| BLAKE3 | `std/blake3.tie` | `blake3.*` | 已有 ✓ | — |
| XXH3 | `std/xxh3.tie` | `xxh3.xxh3_64/xxh3_hex` | 已有 ✓ | 非密码学快速校验 |
| SipHash | `std/siphash.tie` | `siph.sip24` | 已有 ✓ | — |
| MD5（仅兼容标注） | `std/md5.tie` | `md5.*` | 已有（标注兼容）✓ | 禁止用于安全场景 |
| SHA-1（仅兼容标注） | `std/sha1.tie` | `sha1.*` | 已有（标注兼容）✓ | 禁止用于安全场景 |

### MAC —— 归属 std + rdu 复刻（设计稿）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| HMAC | `std/hmac.tie` | `hmac.hmac_sha256` | 已有 ✓（std） | **rdu 复刻缺失**：`rdu/rdu_hmac.tie` 不存在。rdu 层现无 SHA-256 哈希底座（rdu 仅 crc/bits/ascii/fixed/rnd/math/rdb），HMAC 非自给须先拉入 SHA-256 → 超出本次"单文件中等规模"，列缺口不实现 |
| Poly1305 | `std/poly1305.tie` + `rdu/rdu_poly1305.tie` | `poly.poly1305` `rdu_poly.poly1305` | 已有 ✓（std+rdu） | — |
| Ascon-MAC-128 | `std/ascon_mac.tie` + `rdu/rdu_ascon_mac.tie` | `ascon_mac.*` `rdu_ascon.ascon_mac128` | 已有 ✓（std+rdu） | — |

### 对称加密 / Symmetric —— 归属 ext(AES)/std(ChaCha20)/rdu(Ascon)（设计稿）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| AES-128/256 ECB/CBC | `ext/aes.tie` | `aes.encrypt_ecb/decrypt_ecb/encrypt_cbc/decrypt_cbc` | 已有 ✓ | 归属 ext ✓ |
| AES-GCM | `ext/tls/gcm.tie`（TLS 子模块内） | — | 已有（内嵌 TLS）✓ | 仅存在于 TLS 子模块，无独立 `ext/aes` GCM 接口 → 属大项缺口（下游可能误以为已有完整 AES 套件） |
| AES-CTR / XTS | 缺失 | — | **缺失** | 大项，归 ext，按纪律列入缺口不实现 |
| ChaCha20 | `ext/chacha20.tie` | `chacha.chacha20_encrypt` | 已有但是**归属层偏差** | 设计稿归 **std**，实际在 ext → 建议迁移 std（不移动） |
| Ascon-128a/AEAD | `ext/ascon_aead.tie` | — | 已有但是**归属层偏差** | 设计稿归 **rdu**，实际在 ext → 建议迁移 rdu（不移动） |

### KDF/口令 / KDF & password —— 归属 HKDF/PBKDF2:std；scrypt/Argon2id:ext（设计稿）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| HKDF | `std/hkdf.tie` | `hkdf.extract/expand/derive` | 已有 ✓ | 归属 std ✓ |
| PBKDF2 | `std/pbkdf2.tie` | `pbkdf2.pbkdf2_hmac_sha256` | 已有 ✓ | 归属 std ✓ |
| scrypt | `ext/scrypt.tie` | `scrypt.*` | 已有 ✓ | 归属 ext ✓（内存硬） |
| Argon2id | `ext/argon2.tie` | `argon2.*` | 已有 ✓ | 归属 ext ✓（内存硬） |

### 非对称 / Asymmetric —— 归属 ext（设计稿）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| Ed25519 | `std/ed25519.tie` | `ed25519.keygen/sign/verify` | 已有但是**归属层偏差** | 设计稿归 **ext**，实际在 std → 建议迁移 ext（不移动） |
| X25519 | `std/x25519.tie` | `x25519.keygen/dh` | 已有但是**归属层偏差** | 设计稿归 **ext**，实际在 std → 建议迁移 ext（不移动） |
| ECDSA/P-256 | `std/ecdsa_p256.tie` + `ext/ecdsa.tie` | `ecdsa.keygen/sign/verify`（ext，BCrypt/CNG extern） | 已有但是**归属层偏差** | 设计稿归 **ext**；std 另有纯 tie 版 → 建议归并到 ext，std 副本按"仅兼容标注"或移除（不移动） |
| RSA | 无独立模块；RSA verify/RSAPublicKey 解析内嵌 `ext/tls/x509.tie`（`is_rsa/rsa_n_bytes/rsa_e_bytes`） | — | **缺失（独立模块）** | 需独立 `ext/rsa.tie`（加解密/签名完整套件），大项，按纪律列入缺口不实现 |

### 后量子 / Post-quantum —— 归属 ext（评估后列，设计稿）
| 算法 | 实际位置 | 状态 | 缺口说明 |
|---|---|---|---|
| ML-KEM（FIPS 203） | 缺失 | **缺失** | 大项，ext 评估后列（另有 `docs/plans/pqc-roadmap.md`） |
| ML-DSA（FIPS 204） | 缺失 | **缺失** | 大项，ext 评估后列 |
| SLH-DSA（FIPS 205） | 缺失 | **缺失** | 预案在 `docs/plans/slhdsa-shake128s-prelude.md`，未落代码；大项，ext |
| Falcon / HQC | 缺失 | **缺失** | 待标准，不实现 |

### TSHA 族 / TSHA family —— 归属 std（核心，p.7.1.8 专属）
| 算法 | 实际位置 | 入口函数 | 状态 | 缺口说明 |
|---|---|---|---|---|
| TSHA1（f/b/x/r 四档） | `std/tsha1.tie` | `tsha.tsha1f/tsha1b/tsha1x/tsha1r` | 已有 ✓ | p.7.1.8 专属，**本任务只核对不下结论，不触碰** |
| TSHA1-48（48 进制底座） | `std/tsha1_w48.tie` | — | 已有 ✓ | 同上 |

---

## 3. 缺口汇总 / Gap Register

| # | 缺口 | 设计归属 | 规模 | 处置 |
|---|---|---|---|---|
| G1 | `rdu/rdu_hmac.tie`（HMAC rdu 复刻） | rdu | 中（依赖 rdu 无 SHA-256，先拉底座） | 本次不实现，列入缺口 |
| G2 | AES-CTR / AES-XTS | ext | 大 | 本次不实现，列入缺口 |
| G3 | AES-GCM 独立接口（现仅内嵌 TLS） | ext | 大 | 本次不实现，列入缺口 |
| G4 | RSA 独立模块（加解密/签名/填充） | ext | 大 | 本次不实现，列入缺口 |
| G5 | ML-KEM（FIPS 203） | ext | 大 | 本次不实现，列入缺口 |
| G6 | ML-DSA（FIPS 204） | ext | 大 | 本次不实现，列入缺口 |
| G7 | SLH-DSA（FIPS 205） | ext | 大 | 本次不实现，列入缺口 |

## 4. 建议迁移（只记不改） / Suggested migration (logged only)
1. `ext/chacha20.tie` → std（设计稿对称类 ChaCha20 归 std）。
2. `ext/ascon_aead.tie` → rdu（设计稿 Ascon 归 rdu）。
3. `std/ed25519.tie` → ext（非对称归 ext）。
4. `std/x25519.tie` → ext（非对称归 ext）。
5. `std/ecdsa_p256.tie` → 归并 ext（非对称归 ext；ext/ecdsa 为 extern 高效版）。

---

## 5. 验证记录 / Verification

零补缺 → 按任务纪律抽查已成 5 个文件入口函数存在性（读文件确认）：
- `std/hmac.tie`：`hmac.hmac_sha256(key,msg)->string` 存在（L5/L40）。
- `std/poly1305.tie`：`poly.poly1305(key,msg)->string`（L5）。
- `ext/aes.tie`：`aes.encrypt_ecb/decrypt_ecb/encrypt_cbc/decrypt_cbc`（L6-9）。
- `ext/chacha20.tie`：`chacha.chacha20_encrypt(key,nonce,counter,msg)->string`（L6）。
- `std/tsha1.tie`：`tsha.tsha1f/tsha1b/tsha1x/tsha1r(msg,n,base)->string`（L11-14）。
另经全文 grep 复核：sha256/sha512/blake2/blake3/sha3/shake/xxh3/siphash/md5/sha1/pbkdf2/hkdf/ascon_mac/x25519/ecc
/hkdf/csprng 等入口均存在。

---

## EN — p.7.1.7 Security-Algorithm Base: Inventory & Gap Register

Date 2026-09-11 · Branch p.7 · Base HEAD 0adeb65 · Audit-only delivery (verify + classify + gaps), zero code.

**Classification source** — `docs/superpowers/specs/2026-08-29-plugin-kernel-design.md` §6.5:
hash/checksum → std; MAC → std + rdu replica; symmetric → AES ext / ChaCha20 std / Ascon rdu;
KDF (HKDF/PBKDF2) → std, scrypt/Argon2id → ext; asymmetric → ext; post-quantum → ext (assess first);
TSHA family → std (owned by p.7.1.8, verified but not concluded here).

**Result**: 25 items present, 7 missing (large: RSA standalone, AES-GCM/CTR/XTS API, ML-KEM/ML-DSA/SLH-DSA;
small but non-self-contained: rdu_hmac — no SHA-256 base in rdu), 6 placement mismatches logged as
suggested migration only (no moves to avoid disturbing regression-passed libs): ChaCha20→std, Ascon
AEAD→rdu, Ed25519/X25519/P-256→ext. **Zero implementations added (no probe).** Verified entry points
exist for std/hmac, std/poly1305, ext/aes, ext/chacha20, std/tsha1.

Delivery doc: `docs/plans/2026-09-11-p7117-security-base-inventory.md`.