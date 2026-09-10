# r.1.6.7 CSPRNG 调用链审计 — CSPRNG Call-Chain Audit

> 版本 / Version：r.1.6.7（Linux 平台移植子项 / Linux port item）
> 分支 / Branch：`r.167-csprng`（基座 = GitHub r.1 分支 HEAD `13a84b6`）
> 日期 / Date：2026-09-10
> 范围 / Scope：审计 + 基线探针（**不实现 shim**——实现归下一子项 r.1.6.8）
> 关联 / See also：`ROAD.md` r.1.6.7 / r.1.6.9；根因 `std/csprng.tie` + `ext/ecdsa.tie` 依赖 Windows CNG

---

## 1. 执行摘要 / Executive Summary

- `std/csprng.tie`（namespace `csrnd`）对外只有 **1 个公开函数** `csrnd.strong_bytes(n)`，
  且只声明 **1 个 extern** `BCryptGenRandom`。API 面极小，边界与哨兵语义明确（失败返回空表，不降级到伪随机）。
- tie 侧调用 **确认为** `hAlgorithm=NULL`、`dwFlags=0x2`（`BCRYPT_USE_SYSTEM_PREFERRED_RNG`），
  与 WIN32 文档要求的「`hAlgorithm=NULL` + `flags=0x2` 使用系统首选 RNG」**一致**。
- 3 个电话点集中在 TLS 握手（`tls1_3`/`tls1_2` 的 `rand_bytes`、`p256` 临时私钥），均为密钥材料，走 `csrnd` 是安全正解。
- **Linux 等价落点确认**：`trm-lite/core/mnn/linux_compat.c`（并入 `trm_lite_linux.a`）应新增同名
  `int BCryptGenRandom(void*, unsigned char*, unsigned int, unsigned int)` POSIX 实现。
  **建议用 `getrandom(2)` 直接 syscall**（非 `arc4random_buf`），理由见 §4。
- **Windows 基线探针实跑通过**（32/64 字节长度正确、字节域 `[0,255]`、非全零、`n<=0` 哨兵空表），Windows 路径自举不动点内回归不受影响。

---

## 2. csrnd API 面清单 / csrnd API Surface

文件：`std/csprng.tie`（`namespace csrnd`，头注声明 r.1.2.1 引入）。

| 项 / Item | 声明 / Declaration | 语义 / Semantics |
|---|---|---|
| 公开函数 | `pub func strong_bytes(n: i64) -> table<i64>` | 返回 **n 个加密安全随机字节** `[0,255]`；`n<=0` 或系统 RNG 失败 → 返回 **空表**（哨兵）；调用方按哨兵拒绝，**不降级到伪随机** |
| 唯一 extern | `unsafe extern fn BCryptGenRandom(hAlgorithm: i64, pbBuffer: ptr<u8>, cbBuffer: u32, dwFlags: u32) -> i32` | `bcrypt.dll` 原生；`hAlgorithm/指针` 走 `i64/ptr<u8>`、`ULONG` 走 `u32`、返回 `i32`（NTSTATUS） |
| 依赖 | 无 CNG 提供者打开原语 | tie 禁止跨模块重复声明 extern：`BCryptOpenAlgorithmProvider` 等已在 `ext/ecdsa.tie` 声明，故 csprng 不复用；`bcrypt.lib` 由 toolchain 默认链入 |

**语义要点**（读代码第 27–45 行）：
- 失败判定 `BCryptGenRandom(...) != 0` → 返回空表；仅当返回 `0`（`STATUS_SUCCESS`）才消费缓冲。
- 成功路径为「**按请求一次成块填充**」：`alloc(n)` 分配整块 → 单次 `BCryptGenRandom(0, p, n, 2)` 填满 →
  再循环把每字节压入结果表。（满足性能纪律：非逐字节/逐字符拼接，`O(n)`。）注：`strong_bytes` 返回 `table<i64>`，
  逐字节 `table_push` 是 ABC（表）层语义要求，非随机源瓶颈。

---

## 3. BCryptGenRandom 契约确认 / BCryptGenRandom Contract

WIN32 API 原型（`bcrypt.h`）：

```c
NTSTATUS BCryptGenRandom(
    BCRYPT_ALG_HANDLE hAlgorithm,   // NULL → 用系统首选 RNG（须配 0x2 flag）
    PUCHAR            pbBuffer,     // 输出缓冲
    ULONG             cbBuffer,     // 长度（字节，≤ 0xFFFFFFFF）
    ULONG             dwFlags       // BCRYPT_USE_SYSTEM_PREFERRED_RNG = 0x2
);
```

- 返回 `0` = `STATUS_SUCCESS`；非 0 为 NTSTATUS 错误码。
- Flag 常量：`BCRYPT_USE_SYSTEM_PREFERRED_RNG` **= 0x2**（Win10 1607+，FIPS 认可的 CSPRNG）。
- **`hAlgorithm=NULL` + `dwFlags=0x2` → 使用 Windows 内置系统首选 CSPRNG，无需先打开算法提供者**。
- **tie 侧确认一致**：源码第 35 行实际调用 `BCryptGenRandom(0, p, as_u32(n), 2u32)` —— `h=0(NULL)`、`flags=2` ✔。
  （头注记录：`NULL 句柄 + flags=0` 会返回 `0xC0000008 STATUS_INVALID_HANDLE`，故必须配 `0x2`。）

---

## 4. Linux 等价方案建议 / Linux POSIX Equivalent

### 4.1 落点 / Landing point

`trm-lite/core/mnn/linux_compat.c`（发版方已并入 `trm_lite_linux.a` 成员；现含 `_gcvt`/`GetTickCount` shim，
无头文件写法、`clang --target=x86_64-unknown-linux-gnu -c` 交叉编译，无需 Linux sysroot 头文件）。
新增同名符号：

```c
/* 建议签名（对齐 WIN32）——实现留待 r.1.6.8，勿在本项落代码 */
int BCryptGenRandom(void *h, unsigned char *buf, unsigned int cb, unsigned int flags)
```

- `flags==BCRYPT_USE_SYSTEM_PREFERRED_RNG(0x2)` 时 **忽略 `h`**；`flags` 非 2 返回失败码（非 0）。
- 返回 `0` 表示成功，非 0 表示失败（对齐 NTSTATUS「0=成功」语义，tie 侧的 `!=0` 判定即可复用）。

### 4.2 getrandom vs arc4random_buf 取舍 / Trade-off

| 维度 | `getrandom(2)`（直接 syscall） | `arc4random_buf()`（glibc 封装） |
|---|---|---|
| 内核/glibc 门槛 | 内核 ≥ 3.17（2014）即可；**无需 glibc 新版本** | glibc ≥ **2.36**（2022-08 才标准），较旧发行版（CentOS 7/8、RHEL、Ubuntu < 22.10）**不含** |
| 可用性/兼容性 | 现代 Linux 发行版内核普遍 ≫ 3.17，兼容面最广 | `__GLIBC__ < 2.36` 因 `link_error` 导致编译/链失败，兼容性差 |
| 内存效率 | 单次 syscall 直接写入调用方缓冲（**一次成块填充**，零中间缓冲） | 内部自旋/缓冲，对大缓冲仍需中转 = 额外拷贝 |
| 安全属性 | 内核 CSPRNG，熵源由内核管理，等效 Windows 系统 RNG | 底层同为内核 CSPRNG，语义等价 |
| 无头文件成本 | compat 层本就手排结构/内联 asm；x86_64 `SYS_getrandom=318` 直接内联 syscall | 需声明 `arc4random_buf` 符号，跨 glibc 版本行为不一 |

**结论（结合「软件选择优先内存效率与兼容性」）**：**选 `getrandom(2)` 直接 syscall**。
- 兼容性最佳：不依赖 glibc ≥ 2.36，覆盖更老发行版，契合 r.1.6 Linux 发行版范围。
- 内存效率最佳：一次成块直接填满请求缓冲，无中间缓冲/拷贝。
- 安全等价：内核 CSPRNG，与 BCrypt 系统 RNG 同级别。
- `arc4random_buf` 仅作 **可选备选** / 后续 glibc 新版本时的简化路径，本项不采用为首选。

### 4.3 实现形态示意（供 r.1.6.8，不落地） / Implementation sketch

compat 层无头文件，采用**内联 syscall**（x86_64：`rax=318`，`rdi=buf, rsi=cb, rdx=0`，返回 `rax`，`<0` 为 `-errno`）：

```c
int BCryptGenRandom(void *h, unsigned char *buf, unsigned int cb, unsigned int flags) {
    long rc;
    if (flags != 0x2) return 0xC000000D;                /* STATUS_INVALID_PARAMETER 类比 */
    __asm__ volatile("syscall"
        : "=a"(rc)
        : "a"(318), "D"(buf), "S"(cb), "d"(0)
        : "rcx", "r11", "memory");
    return rc < 0 ? (int)-rc : 0;                        /* <0 = -errno → 非 0 = tie 侧「失败」 */
}
```

- tie 侧零改动：`csrnd.strong_bytes` 已按「非 0 即失败」写死，Linux 侧返回 `0`=成功即复用全部语义。
- 随机填充满足性能纪律：**按请求一次成块填充**，无逐字节拼接；兼容层只做转码不复制。

---

## 5. Windows 基线探针结果 / Windows Baseline Probe

临时探针：`tests/_r167_probe/csprng_baseline_probe.tie`（**已实跑通过，验证后删除，不入库**；编译用
`worktree\compiler\tiec.exe`，不触碰 `compiler/backend/*.tie` 与 `compiler/tiec.exe`）。

| 断言 / Assertion | 结果 / Result |
|---|---|
| `csrnd.strong_bytes(32)`：`len==32`、每字节 ∈ `[0,255]`、**非全零**（首字节采样 128） | **PASS** |
| `csrnd.strong_bytes(64)`：`len==64`（长度精确，成块填充语义） | **PASS** |
| `csrnd.strong_bytes(0)` / `strong_bytes(-5)`：哨兵 → `len==0`（空表） | **PASS** |

结论：**Windows 路径正常**，`csrnd` 调用链在自举不动点/回归（97 PASS）内不受影响；4 个网络探针的 Linux FAIL
纯系 CSPRNG 的 Windows-CNG 依赖，与 csrnd 自身逻辑无关，等待 r.1.6.8 的 compat shim 落地。

---

## 6. 风险与遗留 / Risks & Follow-ups

- **范围纪律**：本项**未实现** `BCryptGenRandom` 的同名 POSIX shim——落点与签名已在本报告锁定（`linux_compat.c`），
  实现归 r.1.6.8。
- **`ext/ecdsa.tie` 的 BCrypt 密钥族**同为本批 4 个网络探针 Linux FAIL 的第二根因（`BCryptOpenAlgorithmProvider`/
  `BCryptGenerateKeyPair`/`BCryptSignHash`/`BCryptVerifySignature` 等），**不在本项 CSPRNG 审计范围**，
  需单独子项评估（P-256 在 Linux 无 CNG 等价 → 建议纯 tie 曲线实现或 libsodium 接入，见 `docs/plans/asymmetric-roadmap.md`）。
- **随机性冒烟**仅验证「非全零+范围」，不构成质量级随机性证明；正式 CSPRNG 验收与扰动/统计冒烟归 r.1.6.9。
- **getrandom 需小样本/中途 EINTR**：内核 `getrandom(2)` 是非阻塞请求时可能因熵池不足返回少量字节；本实现建议
  `flags=0`（阻塞直至足额）一次填满即可，避免分片循环——留待 r.1.6.8 实现时按此约束落定。
- worktree 仅新增 `docs/plans/r167-csprng-audit.md`，无编译器/标准库/CI 改动，工作树与 base `13a84b6` 干净对齐。