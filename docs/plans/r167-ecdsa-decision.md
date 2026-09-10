# 规划：ECDSA P-256 Linux 方案裁定（r.1.6.13）
*EN: Plan: ECDSA P-256 Linux Route Decision (r.1.6.13)*

> 状态：**决策已定——纯 tie（route A），弃 extern**（2026-09-10，纯文档+决策，未实现）
> EN: Status: **Decision made — pure tie (route A), drop extern** (2026-09-10, decision only, not implemented)
> 实现是 r.1.6.14（本文件不含实现代码）。
> EN: Implementation is r.1.6.14 (this file contains no implementation code).
> 关联：`ext/ecdsa.tie`（现 BCrypt/CNG 复数）、`ext/tls/p256.tie`（现纯 tie P-256 点数/ECDH）、
> EN: Related: `ext/ecdsa.tie` (current BCrypt/CNG impl), `ext/tls/p256.tie` (existing pure-tie P-256 point math/ECDH),
> `std/csprng.tie`（RNG 熵源，独立子项）、`std/bigint.tie`（大数底座）、`std/ed25519.tie`（纯 tie 签名先例）、
> EN: `std/csprng.tie` (RNG entropy, separate sub-item), `std/bigint.tie` (bigint base), `std/ed25519.tie` (pure-tie signing precedent),
> `docs/plans/pqc-roadmap.md`（已裁全量纯 tie 之铁律）。
> EN: `docs/plans/pqc-roadmap.md` (the full-pure-tie iron rule already decided).

---

## 1. 问题背景
*EN: 1. Problem Background*

Linux CI 回归（r.1.6.6）97 PASS / 0 FAIL；`std_httpc` / `std_net_text` / `std_net_bytes` / `std_sse_probe` 4 个网络探针在 Linux 标 FAIL——链接错误暴露**未定义 extern 符号**：BCryptGenRandom / BCryptOpenAlgorithmProvider / BCryptGenerateKeyPair / BCryptExportKey / BCryptImportKeyPair / BCryptFinalizeKeyPair / BCryptSignHash / BCryptVerifySignature / BCryptDestroyKey / BCryptCloseAlgorithmProvider。这些来自 `std/csprng` 与 `ext/ecdsa`（Windows CNG 密码学）。本裁定聚焦「ecdsa Linux 方案」；`std/csprng` 的 BCryptGenRandom 属**另一独立子项**，此处仅确认交集。

EN: Linux CI regression (r.1.6.6): 97 PASS/0 FAIL, but 4 network probes (`std_httpc`/`std_net_text`/`std_net_bytes`/`std_sse_probe`) FAIL on Linux — link errors surface **undefined extern symbols** listed above, from `std/csprng` and `ext/ecdsa` (Windows CNG crypto). This ruling focuses on the "ECDSA Linux route"; `std/csprng`'s BCryptGenRandom is a **separate sub-item**, confirmed here only for the intersection.

---

## 2. BCrypt API 面清单
*EN: 2. BCrypt API Surface Inventory*

### 2.1 ext/ecdsa.tie（命名空间 `ecdsa`）——9 个 extern
*EN: 2.1 ext/ecdsa.tie (namespace `ecdsa`) — 9 externs*

| # | extern 原型（tie 声明） | 使用函数 |
| :-: | --- | --- |
| 1 | `BCryptOpenAlgorithmProvider(ph: ptr<i64>, pszAlgId: ptr<u8>, pszImplementation: i64, dwFlags: u32) -> i32` | `open_p256()`（keygen/sign/verify 共用） |
| 2 | `BCryptGenerateKeyPair(hAlgorithm: i64, phKey: ptr<i64>, dwLength: u32, dwFlags: u32) -> i32` | `keygen()`（dwLength=256 位） |
| 3 | `BCryptFinalizeKeyPair(hKey: i64, dwFlags: u32) -> i32` | `keygen()` |
| 4 | `BCryptExportKey(hKey: i64, hExportKey: i64, pszBlobType: ptr<u8>, pbOutput: ptr<u8>, cbOutput: u32, pcbResult: ptr<u32>, dwFlags: u32) -> i32` | `keygen()`（导出 ECCPRIVATEBLOB，单次 256B 缓冲） |
| 5 | `BCryptImportKeyPair(hAlgorithm: i64, hImportKey: i64, pszBlobType: ptr<u8>, phKey: ptr<i64>, pbInput: ptr<u8>, cbInput: u32, dwFlags: u32) -> i32` | `sign()`/`verify()`（ECCPRIVATEBLOB → 回退 ECCPUBLICBLOB） |
| 6 | `BCryptSignHash(hKey: i64, pPaddingInfo: i64, pbInput: ptr<u8>, cbInput: u32, pbOutput: ptr<u8>, cbOutput: u32, pcbResult: ptr<u32>, dwFlags: u32) -> i32` | `sign()`（32 字节摘要 → 64B r‖s） |
| 7 | `BCryptVerifySignature(hKey: i64, pPaddingInfo: i64, pbHash: ptr<u8>, cbHash: u32, pbSignature: ptr<u8>, cbSignature: u32, dwFlags: u32) -> i32` | `verify()`（1 有效/0 无效） |
| 8 | `BCryptDestroyKey(hKey: i64) -> i32` | 清理（keygen/sign/verify） |
| 9 | `BCryptCloseAlgorithmProvider(hAlgorithm: i64, dwFlags: u32) -> i32` | 清理（keygen/sign/verify） |

- **算法串**：`BCRYPT_ECDSA_P256_ALGORITHM` = L"ECDSA_P256"；**blob 类型**："ECCPRIVATEBLOB"（keygen 产出 104B=8 头+X32+Y32+d32）、"ECCPUBLICBLOB"。
- **返回值**：NTSTATUS，0=STATUS_SUCCESS 成功；非常 0 即失败（sign/verify 返回哨兵 ""/0）。
- **平台**：Windows `-lbcrypt` 内建；linux 无 bcrypt.dll → 全部 9 个符号未定义。
- **对外契约**（须在 r.1.6.14 保持或被显式打上兼容性变更标记）：
  - `keygen()` → string（ECCPRIVATEBLOB hex，208 hex，内含 d+公钥 x,y）
  - `sign(key, hash)` → string（64B 原始 r‖s hex；`hash` 为调用方先 SHA-256 的 32 字节摘要）
  - `verify(key, hash, sig)` → i64（1/0）
  - IO 统一切 **hex 字符串**（tie string 不可承载 ≥0x80 原始字节）。

EN: 2.1. As above. `open_p256()` opens the CNG "ECDSA_P256" provider; keygen exports an ECCPRIVATEBLOB (104 B = 8 header + X32 + Y32 + d32 → 208 hex); sign uses a 32-byte pre-hashed digest over SHA-256; verify accepts ECCPRIVATEBLOB (falls back to ECCPUBLICBLOB). All 9 externs are undefined on Linux. Contract must be preserved or explicitly versioned. NTSTATUS 0 = success.

### 2.2 std/csprng.tie（命名空间 `csrnd`）——1 个 extern（交集确认）
*EN: 2.2 std/csprng.tie (namespace `csrnd`) — 1 extern (intersection note)*

| # | extern 原型 | 使用函数 |
| :-: | --- | --- |
| 10 | `BCryptGenRandom(hAlgorithm: i64, pbBuffer: ptr<u8>, cbBuffer: u32, dwFlags: u32) -> i32` | `csrnd.strong_bytes(n)`（NULL 句柄 + flag=0x2 系统首选 RNG） |

- `csrnd.strong_bytes(n)` 是纯 tie ECDSA/P-256 keygen 与 sign 的**熵源**（CSPRNG，r.1.2.1 起定）。
- **交集结论**：route A 消除 ecdsa 侧 9 个 BCrypt extern；但 **BCryptGenRandom 仍在**（keygen 私钥 d 与签名的随机 k 都要 CSPRNG 熵）。故 r.1.6.14 的 ecdsa 落地**硬性依赖** csprng 的 Linux 熵源子项（getrandom(2) 或 /dev/urandom，另行裁定与实现）。本文件不实现该子项。

EN: 2.2. `csrnd.strong_bytes` is the CSPRNG entropy source for pure-tie keygen/sign. **Intersection**: route A removes the 9 ecdsa-side BCrypt externs, but **BCryptGenRandom remains** (both private key d and per-signature k need CSPRNG entropy). So r.1.6.14's ECDSA landing has a **hard dependency** on the separate csprng Linux entropy sub-item (getrandom(2) or /dev/urandom), decided/implemented elsewhere. Not part of this file.

---

## 3. 存量资产评估
*EN: 3. Existing-Asset Assessment*

| 资产 | 位置 | 状态 | 复用价值 |
| --- | --- | --- | --- |
| **纯 tie P-256 点数/ECDH** | `ext/tls/p256.tie`（命名空间 `p256`） | **可复用（核心）** | 已实现 p/a=-3/b/G/n 域常量、仿射 Weierstrass `point_double/point_add`、LSB-first double-and-add `scalar_mul`、`keygen/pubkey/dh`、`to_be32/from_be32`。经 `tests/tls_probe/p256_ecdh_probe.tie` 用 openssl 3.6.1 确定性密钥对逐字节验证。**缺**：ECDSA 层（mod-n 运算、k 生成、r/s 计算、verify 的 u1·G+u2·Q 点加）。 |
| **纯 tie 大数库** | `std/bigint.tie`（命名空间 `bigint`） | 可用 | 变长 32-bit limb 小端表；加减/乘（schoolbook，u128 内层）/除（Knuth D）/模逆（扩展欧几里得）/模幂（平方乘）。PSD 自举前提之一。 |
| **纯 tie Ed25519 签名先例** | `std/ed25519.tie` | 可用（模板） | 完整的纯 tie keygen/sign/verify（RFC 8032），sign/verify 的标量乘 + 模 l 运算正是 P-256 ECDSA 的**直接模板**。 |
| 熵源 CSPRNG | `std/csprng.tie` | 仅 Win（子项解决） | route A 依赖其 Linux 熵源子项。 |
| 哈希族 | `std/sha256.tie`（`sha`）、`std/sha512.tie` | 可用 | `sha.sha256` 可用于 optional RFC 6979 确定性 k 或全消息散列；现有接口契约取预散列摘要，非强制。 |
| P-256 ECDSA 现役 | `ext/ecdsa.tie` | 仅 Win（本裁定被 route A 替换） | 保留 API 契约作为 r.1.6.14 兼容性目标。 |
| 旧库 lib_v1/ | （不存在） | — | `F:\Projects\tie-repo\wt-167c\lib_v1` 不存在；无 P-256/p256 旧实现残留。 |

**柳暗花明结论**：纯 tie P-256 的群运算/标量乘**已存在且已验证**（`ext/tls/p256.tie`），并非«defunct»仅剩 ECDSA 一层 + mod-n 算术，增量工作量远小于全新实现。

EN: The asset sweep shows a **key win**: pure-tie P-256 point math / scalar multiplication **already exists and is openssl-verified** in `ext/tls/p256.tie` (domain constants, affine point_double/add, double-and-add scalar_mul, keygen/pubkey/dh). Together with the pure-tie bigint base (`std/bigint.tie`) and the Ed25519 sign/verify template (`std/ed25519.tie`), the missing piece is only the **ECDSA layer** (mod-n arithmetic, k generation, r/s, verify point combo) — a small incremental delta, not a from-scratch build. `lib_v1/` does not exist (no leftover P-256).

---

## 4. 三路线比对
*EN: 4. Three-Route Comparison*

**路线 A — 纯 tie P-256（推荐）。** 在 tie 内实现 ECDSA 层，复用 `ext/tls/p256.tie` 点数 + `std/bigint` mod-n；keygen/sign/verify 全部为内部函数，仅最终序列化走 hex 字节表。私钥 d 与随机 k 的熵来自 `std/csprng`（Linux 子项）。
**Route A — pure tie P-256 (recommended).** Implement the ECDSA layer in tie, reusing `ext/tls/p256.tie` point math + `std/bigint` mod-n; only final serialization touches hex byte tables. Entropy (d, k) from `std/csprng` (Linux sub-item).

**路线 B — openssl libcrypto 桥。** Linux 链 `-lcrypto`，extern EVP_PKEY/EC_KEY 面（Windows 仍 BCrypt 或改 libcrypto）。CI 需 apt `libssl-dev`。
**Route B — openssl libcrypto bridge.** Link `-lcrypto` on Linux, extern an EVP_PKEY/EC_KEY surface; CI needs apt `libssl-dev`.

**路线 C — 链接层 shim。** 在 `trm_lite_linux.a` 的 compat 成员用 C 实现 BCrypt* 家族（同 _gcvt/GetTickCount 先例），内部走 openssl 或自实现；tie 源码不动。
**Route C — link-layer shim.** Implement the BCrypt* family in C inside `trm_lite_linux.a`'s compat member (per the _gcvt/GetTickCount precedent); tie source untouched.

| 维度 | A 纯 tie P-256 | B openssl 桥 | C 链接层 shim |
| --- | --- | --- | --- |
| **工作量** | 小~中：复用 `p256.tie` 点数，仅 ECDSA 层约 120–220 行 + 向量探针 | 中：EVP_PKEY/EC_KEY extern 胶水 ~150–300 行 + CI 依赖 | 中~大：C 实现或引 openssl 的 BCrypt 再封装；跨 C ABI 边界 |
| **外部依赖** | 无（0-Rust，纯 tie + 系统 CSPRNG 熵源） | **-lcrypto / apt libssl-dev**（新二进制/升级依赖） | apt libssl-dev（若走 openssl）或自写 C 密码学 |
| **性能** | 一次性签名/验签，仿射 double-and-add ~384 次域求逆/标量乘，实测握手 <100ms 级；验签 ~2 标量乘 | 库内高度优化，最快 | 取决于内部实现 |
| **0-Rust 符合度** | **✓ 全符合**（延续 pqc-roadmap「全量纯 tie 弃 extern」裁决；Ed25519 已纯 tie 先例） | **✗**（依赖外部系统库，直接违反已决铁律） | **✗**（把密码学放 C，违背 tie 化方向与「缺组件则补」原则） |
| **风险** | 中（自研 mod-n / k 计算边界 bug；**缓解**：RFC 6979 已知答案向量逐字节收敛） | 中（CI 新增依赖、跨平台行为差异、Windows/Linux 双后端分叉） | 中~高（C 侧安全隐患面、双栈维护、外部行为黑盒） |
| **平台** | 全平台（唯一） | Win/Linux 需双后端维护 | Win 仍 BCrypt、Linux shim——双真相源 |
| **决策** | **采纳** | **弃**（违背铁律；pqc-roadmap 已拒 openssl） | **弃**（违背 tie 化方向） |

> EN: Route A is both principled and cheap because the P-256 point math already exists pure-tie. B and C pull in external/foreign crypto (openssl or C) that contradicts the project's documented iron rule and the already-adopted pure-tie decision in `docs/plans/pqc-roadmap.md` (which explicitly rejected CNG/liboqs/OpenSSL as backends, keeping them only as vector sources). Ed25519/X25519 already set the pure-tie precedent in `std/`.

---

## 5. 最终裁定
*EN: 5. Final Ruling*

**选定路线 A：纯 tie P-256 ECDSA（组合中的唯一采纳项；不需 B/C）。**

理由（按权重）：
1. **铁律/项目方向**：`pqc-roadmap.md`（2026-08-29 已决）白纸黑字："全量纯 tie，弃 extern CNG/liboqs/OpenSSL"，并已逐条拒绝 extern 后端；`std/ed25519`/`x25519` 纯 tie 已成先例。B（openssl）与 C（shim）与该裁决正面冲突。
2. **柳暗花明**：P-256 群运算/标量乘已纯 tie 且 openssl 验证（`ext/tls/p256.tie`），缺的仅 ECDSA 一层——增量小，无需从零建大数或曲线。
3. **单一真相源**：A 使 Win/Linux 共用同一纯 tie 实现，消灭 BCrypt extern 面与双后端分支；B/C 都制造双实现/double-source-of-truth。
4. **资源边界（pragmatic）**：无量纲绝对最小——不是"从零写 P-256"，而是"给现成 ECDH 点数加 sign/verify"。

裁定英文一句话：*Choose **route A (pure tie)** for ECDSA P-256 on Linux. Reuse the existing pure-tie P-256 point math (`ext/tls/p256.tie`) + bigint base, add the mod-n ECDSA sign/verify layer, and rely on the `std/csprng` Linux entropy sub-item for d/k randomness. Routes B (openssl bridge) and C (C shim) are rejected as contradicting the project's full-pure-tie iron rule and prior decision. No combination needed.*

**边界声明**：本裁定仅针对 ecdsa 签线。`std/csprng` 的 BCryptGenRandom 仍需在独立的 csprng Linux 子项中处理（getrandom(2)//dev/urandom）；route A 的 keygen/sign 熵源依赖该子项先行或同期落地。

EN: **Ruling — route A (pure tie).** Because (1) the full-pure-tie iron rule is already documented and decided in `pqc-roadmap.md`, and B/C directly contradict it; (2) P-256 point math already exists pure-tie and openssl-verified, so the delta is a small ECDSA layer rather than a from-scratch build; (3) A yields a single Win/Linux source of truth and removes the BCrypt extern surface; (4) pragmatically cheapest. Boundary: BCryptGenRandom in `std/csprng` is a separate sub-item (getrandom(2)/*/dev/urandom*) — route A's keygen/sign entropy depends on it.

---

## 6. r.1.6.14 落地要点草案
*EN: 6. Implementation Points Draft for r.1.6.14*

> 草案，非实现；具体文件名/命名空间在实现时定稿。
> EN: Draft only, not implementation; concrete file/namespace names finalized during implementation.

**文件/改造面（File / touch surface）**
- 新增纯 tie ECDSA 模块（候选：`std/ecdsa_p256.tie`，命名空间 `ecdsa`），`import` `ext/tls/p256.tie`（点数）、`std/bigint.tie`（mod-n）、`std/csprng.tie`（熵）。不触碰 `compiler/backend/*.tie`、不触碰 `compiler/tiec.exe`。
- （可选，若需去重）把 `ext/tls/p256.tie` 的域常量/点运算上提为共享纯 tie 模块；否则直接 import 复用。最小打扰优先：**直接 import 既有 p256，不做搬运**。
- 保留 ext/ecdsa.tie 的对外三相（`keygen()/sign()/verify()`）**API 形状**；序列化格式变更需声明为兼容性变更（见 §7）。
- 新增向量探针（候选 `tests/tls_probe/ecdsa_p256_vec_probe.tie`）挂已知答案向量。

**ECDSA 数学要点（Math essentials）**
- 群/域算术：完全复用 `p256` 的 `point_double/point_add/scalar_mul/mul_mod/inv`，换模数到**子群阶 n**（`g_n` 已定义）。P-256 用一组模 p 域数 + 一组模 n 标量数；点乘用域 p，r/s 用模 n。
- `sign`：随机 k（`csrnd.strong_bytes(32)`，重试至 1≤k<n）→ `R = k·G`，`r = Rx mod n`（Rx≠0），`s = k⁻¹·(z + r·d) mod n`（s≠0，否则重来）。可加 **RFC 6979 确定性 k**（HMAC-SHA256 DRBG；需 std 提供 HMAC/`sha.sha256`）作为**推荐增强**，既防 k 复用又利于确定性向量的逐字节断言；v1 最小集可先 CSPRNG k + 固定 k 的已知答案路径。
- `verify`：解码 d 的 Q=d·G（或直接导入公钥/私钥→取公钥）；`u1=z·s⁻¹ mod n`，`u2=r·s⁻¹ mod n`，`P = u1·G + u2·Q`；`P≠∞ 且 Px mod n == r` → 有效。公钥点须过 on-curve 校验（沿用 p256.dh 模式）。

**性能纪律（Performance discipline）**
- **大数方案无 O(n²) 位串拼接**：全部 mod-n/模 p 运算走 `bigint` limb 数组（`divrem` Knuth D、`mul` schoolbook 8×8=64 次 u128 乘、`invmod` 扩展欧几里得）——**无字符串参与**。hex 只在 API 边界做（固定 64/128 hex），预分配目标缓冲，不做循环内字符串拼接。
- **标量乘复杂度预算**：仿射 double-and-add 每点运算 1 次域求逆 → `scalar_mul` ≈ 256 doub + ~128 add ≈ **384 次域求逆**（dominant cost）。sign=1 标量乘；verify=2 标量乘 + 1 点加（u1·G + u2·Q）≈ 3 标量乘。p256 握手实测 <100ms 级（keygen+pubkey+dh=3 标量乘）→ verify 同级、sign 更低，一次性签名可接受，不投优化。
- **优化预留（可选，非 v1）**：若需压时，点运算换 Jacobian 投影坐标——每标量乘从 ~384 次求逆降到 1 次（r.1.6.14 无需）。
- **复用缓冲**：点/标量临时大数需显式 clone 或复用预分配槽（照搬 `bigint.divrem` 的 p.6.1.7-RCA-2 entry 级预声明槽模式），避免 ECDSA 每步表分配抖动/泄漏。反馈 `sensitive` 槽覆写约定（pqc-roadmap §3.5）：sign 的 k 与私钥临时缓冲用毕覆写 0x00。

**验证向量来源（Verification vectors）**
- **主源**：RFC 6979 §A.2.5（P-256/SHA-256，「sample」「test」两组已知 d、k、r、s）——实现 RFC 6979 确定性 k 时**逐字节断言**。
- 次源：固定已知 d 的确定性 sign 输出对 openssl `pkeyutl` 交叉生成（与 `p256_ecdh_probe.tie` 同法）；公钥导出沿用 `p256_ecdh_probe.tie` 已硬编码的 openssl 验证对。
- 微变敏感：篡改签名/摘要 1 字节 → REJECT（沿用 `ecdsa_lib_probe.tie` 语义）。
- 回归定位：探针入 `tests/*_probe/`，不进通用回归（pqc-roadmap §5 三挂钩：向量字节一致→自举可运行→不破坏基线）。

**关键成功判据（Key success criteria）**：Linux CI 该项转 PASS；`ext/ecdsa` 的 9 个 BCrypt extern 在 Linux build 不再被引用（或仅 Windows 条件编译）;sign→verify 往返 + 篡改拒绝 + RFC 6979 已知答案逐字节 PASS。

EN: 6. Draft plan for r.1.6.14: add a pure-tie ECDSA module importing the existing P-256 point math + bigint + csprng; reuse rather than relocate code; keep the `keygen/sign/verify` API shape (serialization change flagged as a compatibility break). Math: reuse p256 point ops, work mod n for r/s; sign via CSPRNG k (recommend RFC 6979 deterministic k as an enhancement); verify via u1·G+u2·Q with on-curve checks. Performance: all mod-p/n math goes through bigint limb arrays with **no O(n²) string concatenation** (hex only at fixed 64/128-char API boundaries with preallocated buffers); scalar-mul budget ≈384 field inversions (sign=1, verify≈3 scalar muls); reuse the preallocation/`sensitive`-slot patterns from bigint.divrem & pqc-roadmap §3.5. Vectors: RFC 6979 §A.2.5 known-answer + openssl-cross-generated + tamper-reject. Success: Linux CI turns PASS and the 9 ecdsa BCrypt externs vanish from the Linux link.

---

## 7. 遗留问题
*EN: 7. Open Issues*

1. **序列化兼容性破坏**：`ext/ecdsa.keygen()` 现返回 Windows CNG **ECCPRIVATEBLOB** hex（104B=8 头+X+Y+d，208 hex）；纯 tie 自然产出的私钥为 **raw 32B d hex（64 hex）**。纯 tie 版若改序列化格式，是相对现役 `ecdsa_lib_probe`（断言 len==208 与 blob 导入）的**契约破坏**。r.1.6.14 需决策：a) API 换成 raw d hex（推荐，与 `p256.keygen` 对齐）并同步改探针/调用方；b) 提供 ECCPRIVATEBLOB→raw 的兼容封装。验签既可收 d 也可收公钥点（64B 非压缩）。
   EN: Serialization compatibility break. CNG keygen returns an ECCPRIVATEBLOB hex (104 B, 208 hex) with a 8-byte CNG header; pure-tie naturally yields raw 32-B d hex (64 hex). Need to decide in r.1.6.14: (a) switch API to raw d hex (recommended, aligns with `p256.keygen`) and update the probe/callers, or (b) provide a blob→raw compatibility wrapper. Verify should accept either d or a public point.
2. **csprng Linux 熵源（硬性前置依赖）**：BCryptGenRandom 需独立子项用 getrandom(2)//dev/urandom 替换；route A 的 keygen/sign 熵依赖它。两子项需排期耦合。
   EN: The `std/csprng` Linux entropy sub-item (getrandom(2)//dev/urandom) is a hard prerequisite for route A's keygen/sign randomness; the two sub-items must be scheduled together.
3. **常数时间 / 侧信道**：纯 tie 点运算与 bigint 分支（affine inv、double-and-add 按位分支）**非常数时间**——与 `p256.tie`/`ed25519.tie` 同定位：面向功能正确 + 一次性临时密钥，不做侧信道隔离；生产签名需在调用层复核或后续补 Jacobian + 常数时间基建（pqc-roadmap §3.5）。
   EN: Constant-time/side-channel: pure-tie affine point ops and bigint branches (field inversion, per-bit double-and-add) are **not constant-time** — same positioning as `p256.tie`/`ed25519.tie` (functional correctness, one-time ephemeral keys). Production signing needs a call-layer review or later Jacobian + constant-time infrastructure (pqc-roadmap §3.5).
4. **RFC 6979 确定性 k 的 HMAC 依赖**：推荐增强需 std 提供 HMAC（基于 `sha.sha256`）。若 std 暂无 HMAC 封装，属于"缺组件则补"的纯 tie 增量，非 blocker。
   EN: RFC 6979 deterministic k needs an HMAC (over `sha.sha256`). If std lacks an HMAC wrapper yet, it is a pure-tie add-on under the "fill missing components" convention, not a blocker.

---

## 8. 决策记录表
*EN: 8. Decision Record*

| 决策点 | 结论 |
| --- | --- |
| ecdsa Linux 路线 | **A 纯 tie P-256（复用 `ext/tls/p256.tie` 点数 + `std/bigint` mod-n + `std/csprng` 熵）** |
| openssl 桥 / C shim | **弃**（违背全量纯 tie 铁律与 pqc-roadmap 已决；Ed25519 纯 tie 已成先例） |
| 组合 | 不需要（A 已最小化；csprng 熵源属独立子项且仍在路线内） |
| 实现 | r.1.6.14（本文件为 r.1.6.13 裁定，不含实现） |

EN: Decision record — route A pure tie (reuse existing P-256 point math + bigint + csprng), reject B/C, no combination needed; implementation deferred to r.1.6.14.