# 规划：非对称签名 / 密钥交换族路线评估（Ed25519 / X25519 / ECDSA P-256）

> 状态：**评估已完成 + ECDSA P-256 实证（2026-08-29）**
> 关联：`std/blake2.tie`（bignum / 双半 [hi,lo] 先例）、`ext/aes.tie`（ext 风格）、
> `docs/plans/unsafe-model.md`（extern 能力边界）。
> 实证探针：`tests/asym_probe/ecdsa_p256_probe.tie`（本文件作者已跑通）。

---

## 1. 目标与约束

实现非对称签名 / 密钥交换族，覆盖三类算法：

| 算法 | 用途 | 曲线 | 备注 |
| --- | --- | --- | --- |
| Ed25519 | 签名（EdDSA） | Curve25519（Edwards） | RFC 8032 |
| X25519 | 密钥交换（DH） | Curve25519（Montgomery） | RFC 7748 |
| ECDSA P-256 | 签名（ANSI X9.62） | NIST P-256 | FIPS 186-4 |

**tie 平台约束**（决定输入输出形状）：
- tie `string` 为 UTF-8、可含 NUL，但不能可靠承载 ≥0x80 的**原始任意字节**（无字节串一等类型），
  故所有 IO 统一用**小写 hex 字符串**（与 `ext/aes.tie` / `std/encoding.hex_encode` 一致）；
- 运行期目标为 Windows，`compiler/backend/toolchain.tie` 的链入命令已含 `-lbcrypt`；
- extern 声明模型：`unsafe extern fn`（形参须标量/`ptr<T>`/`slice<T>`，不能 TK_STR 复杂类型），
  调用须在 `unsafe` 块内（E3 强制）；详见 `docs/plans/unsafe-model.md` §5。

---

## 2. 三条路线对比

| 维度 | A. 纯 tie bigint | B. extern BCrypt(CNG) | C. 混合（标量乘纯 tie + 杂项 extern） |
| --- | --- | --- | --- |
| **自研 256/512 位大数** | 必须（加减/模乘/模逆/模幂 + 蒙哥马利/Barrett 优化） | 不需要 | 仅标量乘（仍要大数） |
| **算法覆盖** | Ed25519 ✓ X25519 ✓ ECDSA P-256 ✓ | **ECDSA P-256 ✓**；**Ed25519 ✗、X25519 ✗**（见 §3） | Ed25519/X25519 ✓（纯 tie），ECDSA 走 extern |
| **常数时间 / 侧信道** | **高风险**：tie 无安全常数时间基建，secret 分支/索引泄漏风险高 | **安全**：系统 FIPS 140 已验证实现 | 标量乘仍暴露侧信道风险 |
| **正确性** | 自己写曲线+签名，易出边界 bug（I/O、编码、模约简） | 系统级已验证 | 半系统半自研 |
| **工作量大** | 极大（Ed25519+ECDSA 双曲线全栈，约 1500-2500 行 + 大量向量核对） | 中（只 ECDSA P-256 时约 300-500 行 extern glue；但覆盖不了 Curve25519 族） | 大 |
| **验证向量** | 必须逐向量核对（RFC 8032/7748/openssl），工作量与正确性强绑定 | 系统实现自带正确性，只需测往返 | Curve25519 部分仍要核对 |
| **外部依赖** | 无 | Windows 平台（bcrypt.dll 内建于 Windows Vista+；无新增 dll） | 无新增，平台性 |
| **可行性（已实证）** | 未证（量大） | **ECDSA P-256 已实证可编译/链接/运行**（见 §5） | 未证 |

---

## 3. BCrypt(CNG) 能力核实（Web 核实结论）

依据微软官方 CNG 算法标识与命名曲线文档（`docs.microsoft.com/.../cng-algorithm-identifiers`、
`.../cng-named-elliptic-curves`）：

| 目标 | BCrypt 支持？ | 核实详情 |
| --- | --- | --- |
| **Ed25519（EdDSA）** | **✗ 不支持** | CNG **算法标识表中不存在 `ED25519` / `EDDSA` / `ED448`**；BCrypt 的
  ECDSA 明确只覆盖「素数椭圆曲线」（P-256/P-384/P-521）。Windows CNG 不原生提供
  Ed25519 签名。 |
| **X25519（DH）** | **✗ 非一等支持** | `curve25519` 仅作为**命名曲线**（`BCRYPT_ECC_CURVE_25519`，255 位）
  出现在命名曲线列表，用于 ECDH 类密钥派生；无 `BCRYPT_X25519_ALGORITHM` 一等算法标识，
  RFC 7748 的 X25519 原语非可靠可调（曲线语义与 Ed25519 的 RFC 8032 强绑定也不互补）。 |
| **ECDSA P-256** | **✓ 支持** | `BCRYPT_ECDSA_P256_ALGORITHM`（L"ECDSA_P256"）一等算法，曲线隐含于算法类。
  本 probe 已实跑 sig/verify。另 ECDH 族 P-256 亦支持（未来可做密钥交换）。 |

**结论一句话**：纯 BCrypt（路线 B）**只能覆盖 ECDSA P-256（及 ECDH P-256/384/521 NIST 曲线）**，
**覆盖不了本族命名的 Ed25519 与 X25519**。这是决定推荐路线的关键事实。

---

## 4. extern 能力分析（tie → bcrypt 可行路径）

### 4.1 现状结论（已实证）
- `toolchain.tie` 两条链接路径（link_exe/link_shared）均含 `-lbcrypt`
  ——bcrypt 导入库已在链入命令；
- BCrypt 符号走「用户级 `unsafe extern fn`」声明路径：编译器由调用签名自动推导 `declare`
  （`llvmgen_str.user_extern_decl`），非 `is_libc_sym` 符号置 `g_used_interp=true` → 同时链
  `tie_interp.lib`（本机 `target/release/tie_interp.lib` 已有）。**无需改编译器**即可链接 bcrypt。
- 与 `tests/language/proc_createprocessw_pipe.tie`（CreateProcessW 传 UTF-16 宽串 + repr(C)
  结构体）同型——BCrypt 的 `LPCWSTR` 算法标识/曲线名、`BCRYPT_ALG_HANDLE` 句柄、`PBUFER`
  缓冲+长度均可用现成 tie 模式表达。

> 可选优化：把 BCrypt 常用符号加入 `backend/irgen.tie::is_libc_sym` + `backend/llvmgen_str.tie::extern_decl`
> 白名单，即可**免链 tie_interp.lib**（纯 codegen），与 kernel32 CreateThread 先例一致。当前
> 探针未改编译器，功能无碍，仅运行文件多带一个 Rust 桥。此项记为低成本后续。

### 4.2 extern 签名草案（结构化 buffer 地址 + 长度，句柄即 i64）
固定：`NTSTATUS` 成功 = 0，失败为负值；可空指针形参声明为 `i64` 传 0；UTF-16（`LPCWSTR`）
用 `alloc` 缓冲手拼 `{byte, 0x00}`（ASCII 够用，见 probe `widebuf`）。

```tie
unsafe extern fn BCryptOpenAlgorithmProvider(ph: ptr<i64>, pszAlgId: ptr<u8>, pszImplementation: i64, dwFlags: u32) -> i32
unsafe extern fn BCryptSetProperty(hObject: i64, pszProperty: ptr<u8>, pbInput: ptr<u8>, cbInput: u32, dwFlags: u32) -> i32
unsafe extern fn BCryptGenerateKeyPair(hAlgorithm: i64, phKey: ptr<i64>, dwLength: u32, dwFlags: u32) -> i32
unsafe extern fn BCryptFinalizeKeyPair(hKey: i64, dwFlags: u32) -> i32
unsafe extern fn BCryptExportKey(hKey: i64, hExportKey: i64, pszBlobType: ptr<u8>, pbOutput: ptr<u8>, cbOutput: u32, pcbResult: ptr<u32>, dwFlags: u32) -> i32
unsafe extern fn BCryptImportKeyPair(hAlgorithm: i64, hImportKey: i64, pszBlobType: ptr<u8>, phKey: ptr<i64>, pbInput: ptr<u8>, cbInput: u32, dwFlags: u32) -> i32
unsafe extern fn BCryptSignHash(hKey: i64, pPaddingInfo: i64, pbInput: ptr<u8>, cbInput: u32, pbOutput: ptr<u8>, cbOutput: u32, pcbResult: ptr<u32>, dwFlags: u32) -> i32
unsafe extern fn BCryptVerifySignature(hKey: i64, pPaddingInfo: i64, pbHash: ptr<u8>, cbHash: u32, pbSignature: ptr<u8>, cbSignature: u32, dwFlags: u32) -> i32
// Ed25519/X25519 无对应 extern（BCrypt 不支持）——见 §3
```

- 密钥 Blob：`BCRYPT_ECCPUBLIC_BLOB`（L"ECCPUBLICBLOB"）= `ULONG magic + ULONG cbKey(=32) + X[32] + Y[32]`，
  `BCRYPT_ECCPRIVATE_BLOB`（L"ECCPRIVATEBLOB"）= 上述 + `d[32]`；
- `BCryptExportKey` / `BCryptSignHash` 用两段式（先 NULL 缓冲取 `pcbResult` 尺寸，再分配实调）。

---

## 5. 实证探针（tests/asym_probe/ecdsa_p256_probe.tie）

已在当前 tiec（`compiler/tiec.exe`）编译+运行通过，输出 `PASS`：

```
Open ECDSA_P256 → GenerateKeyPair(256) → FinalizeKeyPair
→ SignHash(固定32B摘要) → 签名 64B（r||s）
→ VerifySignature → ACCEPT（rc=0）
→ 翻转签名首字节 → VerifySignature → REJECT（rc≠0）
```

**结果**：
- `编译` 零错误（仅 1 条 clang target triple 覆盖 warning）；
- `链接` 成功（-lbcrypt 解析到 bcrypt.dll 导出）；
- `往返` + `微变敏感` 均通过；
- NTSTATUS 负值正确透传（调试期 0xC00000BB 即 STATUS_NOT_SUPPORTED 可读）。

**结论**：**路线 B 的 extern 机制可行性已实证**（对 BCrypt 覆盖的算法，即 ECDSA P-256）。

---

## 6. 推荐路线

### 推荐：**混合（C 形态）——按算法分派后端**

| 算法族 | 推荐后端 | 理由 |
| --- | --- | --- |
| ECDSA P-256（及 ECDH P-256/384/521） | **B. extern BCrypt** | 已实证链路走通、系统 FIPS 140 安全、零自研大数风险 |
| Ed25519 / X25519 | **A. 纯 tie bigint 后续件**（或若允许，加 libsodium extern） | BCrypt 不支持；纯 tie 作教学/可验证实现，但须严格按 RFC 8032/7748 向量核对 + 自证常数时间 |

> 理由：tie 语言当前**无安全常数时间 bigint 基建**，纯自研 Ed25519/X25519/ECDSA 全栈易出
> 侧信道与正确性 bug——故 ECDSA 优先复用系统 BCrypt（B）；而 Curve25519 族（Ed25519/X25519）
> 是任务命名目标但 BCrypt 缺失，只能走纯 tie（A）或引入 libsodium（需加 `-lsodium` + 打包 dll，
> 引入外部二进制依赖）。**若目标是尽快落地「可用的签名/密钥交换」，最务实是：ECDSA P-256 走
> BCrypt（本评估已交付探针），Ed25519/X25519 立项纯 tie 二期。**

### 三路线结论表

| 路线 | 覆盖 Ed25519 | 覆盖 X25519 | 覆盖 ECDSA | 常数时间 | 工作量 | 平台依赖 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A 纯 tie | ✓ | ✓ | ✓ | 高风险 | 极大 | 无 | 教学/可验证，二期 |
| B 纯 BCrypt | ✗ | ✗ | ✓ | 安全 | 中 | Windows | **ECDSA 采用** |
| **C 混合（推荐）** | **（A 二期）** | **（A 二期）** | **B ✓** | 安全/自研并存 | 大 | Windows | **落地路径** |

---

## 7. 实施记录 / 受阻点

- 本评估**已实现并实证 ECDSA P-256（BCrypt extern）**：探针通过。性质上属「路线 B 可行性验证」，
  而非完整 `ext/ecdsa.tie` 库（后者为增量包装：hex IO + 密钥 import/export + SHA-256 摘要链）。
- **Ed25519 / X25519：受限于 BCrypt 能力缺口**（§3），若按路线 B 纯 BCrypt 走即**不可行**；
  需 A（纯 tie）或引入 libsodium。`ext/ed25519.tie`、`ext/x25519.tie` 暂不产出（避免半吊子假实现）。
- 探针依赖 `tie_interp.lib`（g_used_interp）——构建环境已具备；若要纯 codegen 免 Rust 桥，
  走 §4.1 白名单优化。

---

## 8. 外部参考

- 微软 CNG 算法标识：`learn.microsoft.com/windows/win32/seccng/cng-algorithm-identifiers`
- 微软 CNG 命名椭圆曲线：`learn.microsoft.com/windows/win32/seccng/cng-named-elliptic-curves`
- RFC 8032 Edwards（Ed25519 签名）／ RFC 7748 Curve25519（X25519 密钥交换）