# 规划：非对称签名 / 密钥交换族路线评估（Ed25519 / X25519 / ECDSA P-256）

> 状态：**评估已完成 + ECDSA P-256 实证（2026-08-29）；路线决策更新——非对称族统一纯 tie**
> 关联：`std/bigint.tie`（规划的地基库，Ed25519 与格算法共通底座）、`std/blake2.tie`
> （bignum / 双半 [hi,lo] 先例）、`ext/aes.tie`（ext 风格）、
> `docs/plans/unsafe-model.md`（extern 能力边界）、`docs/plans/pqc-roadmap.md`（PQC 纯 tie 先例）。
> 实证探针：`tests/asym_probe/ecdsa_p256_probe.tie`（本文件作者已跑通）。
> **决策记录：同意用户纯 tie 决策——Ed25519/X25519 统一纯 tie bigint（依赖 `std/bigint.tie`）；
> ECDSA P-256 已 extern 落地，标注为过渡方案，远期纯 tie。**

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

| 维度 | A. extern BCrypt(CNG) | B. 混合（bigint / libsodium） | **C. 纯 tie bigint（推荐）** |
| --- | --- | --- | --- |
| **自研 256/512 位大数** | 不需要 | 需（Ed25519 标量乘仍要大数）；走 libsodium 则不需要 | **必须**：`std/bigint.tie`（加减 / 模乘 / 模逆 / 模幂 + 蒙哥马利 / Barrett 优化） |
| **算法覆盖** | **仅 ECDSA P-256（+ NIST 曲线 ECDH）**；**Ed25519 ✗、X25519 ✗**（见 §3） | Ed25519/X25519 纯 tie；ECDSA extern | **Ed25519 ✓ X25519 ✓ ECDSA P-256 ✓**（统一）：Ed25519/X25519 纯 tie；ECDSA 远期纯 tie 并入 |
| **常数时间 / 侧信道** | **安全**（系统 FIPS 140 已验证，但仅覆盖 ECDSA） | 标量乘仍暴露侧信道风险 | **高风险（可控）**：算法结构常数时间 + `sensitive` 槽覆写约定（见 pqc-roadmap §3.5） |
| **正确性** | 系统级已验证，作往返即可 | 半系统半自研 | 自研曲线 + 签名易出边界 bug（I/O、编码、模约简）；靠 RFC 8032/7748 向量 + openssl 交叉逐字节核对 |
| **工作量大** | 中（ECDSA glue 约 300–500 行，但覆盖不了 Curve25519 族） | 大 | 大（Ed25519/X25519 全栈自研约 1000–1500 行，依赖地基库先行） |
| **验证向量** | 系统实现自带正确性，只需测往返 | Curve25519 部分仍要核对 | 必须逐向量核对（RFC 8032 / 7748 / openssl），正确性与工作量强绑定 |
| **外部依赖** | Windows（bcrypt.dll 内建） | libsodium 需 `-lsodium` + 打包 dll | **无（满足铁律）** |
| **决策** | **过渡**（ECDSA 已落地）；远期纯 tie | **弃**（不再 libsodium 二选一） | **采纳** |

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

**结论**：**路线 A 的 extern 机制可行性已实证**（对 BCrypt 覆盖的算法，即 ECDSA P-256）；
ECDSA 的 extern 只列为过渡方案，远期随 `std/bigint.tie` 转纯 tie。

---

## 6. 推荐路线

### 推荐：**统一纯 tie bigint（C）——双曲线 + ECDSA 全量纯 tie，extern 仅过渡**

| 算法族 | 推荐实现 | 理由 |
| --- | --- | --- |
| **Ed25519 / X25519** | **纯 tie bigint（`std/bigint.tie`）** | BCrypt 不支持（§3）；按用户纯 tie 决策**不再 libsodium 二选一**——统一依赖 `std/bigint.tie`，Curve25519 族原生落地 |
| **ECDSA P-256** | **现状 extern（BCrypt）为过渡；远期纯 tie** | 已 extern 落地（探针实证）——**列为过渡方案**；待 `std/bigint.tie` 成熟后整体转纯 tie |

> 理由：项目铁律（Cannot use Rust in implementation、去 Rust 桥、tie 自写 tiec）与用户决策要求
> **弃 extern 系统库**。虽然 tie 当前无现成常数时间 bigint 基建、纯自研全栈易出侧信道 / 正确性
> bug——但决策要求算法库纯 tie。故：**Ed25519 / X25519 统一纯 tie bigint**（依赖地基库 `std/
> bigint.tie`）；**ECDSA P-256 的 BCrypt extern 仅作为「已落地的过渡方案」**（记录其验证作用），
> 远期随 `std/bigint.tie` 成熟整体转纯 tie。**libsodium 不再作为备选。**

### 三路线结论表

| 路线 | 覆盖 Ed25519 | 覆盖 X25519 | 覆盖 ECDSA | 常数时间 | 工作量 | 平台依赖 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. extern BCrypt | ✗ | ✗ | ✓（已落地） | 安全（过渡） | 中 | Windows | ECDSA 过渡采用；无法覆盖本族命名目标 |
| B. 混合（bigint / libsodium） | ✓ | ✓ | ✓ | 自研部分高风险 | 大 | libsodium 需打包 | 弃（不再 libsodium 二选一） |
| **C. 纯 tie bigint（推荐）** | **✓** | **✓** | **✓（远期并入）** | 高风险（可控） | 大 | 无 | **落地路径**（符合纯 tie 铁律） |

---

## 7. 实施记录 / 受阻点

- 本评估**已实现并实证 ECDSA P-256（BCrypt extern）**：探针通过。性质上属「路线 A 可行性验证」。
  **ECDSA 的 extern 列为过渡方案**——待 `std/bigint.tie` 成熟后整体转纯 tie；完整库形态为增量
  包装（hex IO + 密钥 import/export + SHA-256 摘要链），纯 tie 化列入后续。
- **Ed25519 / X25519：统一走纯 tie bigint（`std/bigint.tie`）**，不再 libsodium 二选一——符合
  用户纯 tie 决策。依赖地基库先行（见 pqc-roadmap §3.5 / §5 步骤 3）；`ext/ed25519.tie`、
  `ext/x25519.tie` 待地基库就绪后产出，避免半吊子假实现。
- 探针依赖 `tie_interp.lib`（g_used_interp）——构建环境已具备；若要纯 codegen 免 Rust 桥，
  走 §4.1 白名单优化。

---

## 8. 外部参考

- 微软 CNG 算法标识：`learn.microsoft.com/windows/win32/seccng/cng-algorithm-identifiers`
- 微软 CNG 命名椭圆曲线：`learn.microsoft.com/windows/win32/seccng/cng-named-elliptic-curves`
- RFC 8032 Edwards（Ed25519 签名）／ RFC 7748 Curve25519（X25519 密钥交换）