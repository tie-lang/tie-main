# 规划：后量子密码（PQC）接入评估与路线图（ML-KEM / ML-DSA / SLH-DSA）

> 状态：**评估完成，立项分析**（2026-08-29，纯文档，未实现）
> 关联：`docs/plans/asymmetric-roadmap.md`（非对称族评估：ECDSA/Ed25519/X25519 先例）、
> `std/sha256.tie` / `std/sha3.tie` / `std/blake2.tie`（std 哈希族）、
> `ext/aes.tie` / `ext/chacha20.tie` / `ext/ascon_aead.tie`（ext 对称族）、
> `docs/plans/unsafe-model.md`（extern 能力边界）。
> 结论一句话：**密钥封装（ML-KEM-768）与格签名（ML-DSA-65）走 extern（首选 Windows CNG，
> 内建免新增依赖）；哈希签名（SLH-DSA-SHA2）具备纯 tie 最低风险通路，作长期审计凭证远期立项。**
> 当前编译基线不受本文档影响（纯文档，未触碰任何 `.tie` 与编译器源码）。

---

## 1. 目标与动机

### 1.1 tie 平台为何需要 PQC

| 动机 | 说明 | 紧迫度 |
| --- | --- | --- |
| 插件审计链长期签名凭证 | tie 生态的插件/包发布采用签名凭证，链上凭证需跨「量子日（Q-Day）」仍可验签；哈希签名（SLH-DSA）只依赖哈希抗碰撞/抗原像，安全假设最保守、最适合长期有效签名 | 中（凭证有效期决定，非即时） |
| 与 TLS / PGP 混合部署对接 | 生态系统（浏览器、K8s、OpenSSL）已大规模接入混合 PQC（如 X25519MLKEM768），tie 若做网络/证书将面临互操作义务 | 中 |
| 2030–2035 迁移表 | 商用实现逐步转向 PQC，CNSA 2.0 等规范要求对涉密系统主流化 PQC；平台需在迁移窗口内具备就绪路径 | 低（仍处窗口期） |

> 需求取舍（YAGNI 前置）：若 PQC 仅服务于平台**内部审计链**（未对外的长期签名），则不存在
> 「harvest-now-decrypt-later」的密文窃取风险，慢一点不致命——这使「陈退款（滞后）」成为
> 合法可选项（见 §5 劝退项）。

### 1.2 tie 平台现状（相关先决事实）

- **std 哈希族**：`sha256`（`std/sha256.tie`）、`sha3_256/512`（`std/sha3.tie`，含 Keccak
  轮函数 block）、`blake2` / `blake3`、`sha1`、`tsha1`（trit 混合）、`base48`。**尚无 SHAKE
  XOF 公开封装**（`sha3.tie` 的 keccak 可为其铺路）。
- **ext 对称族**：AES、ChaCha20、Ascon-AEAD。
- **ext 非对称**：ECDSA P-256 走 BCrypt extern（`ext/ecdsa.tie`，已实证）；Ed25519/X25519 受阻
  （BCrypt 曾无覆盖），拟走纯 tie bigint 或 libsodium（见 asymmetric-roadmap）。
- **无现成多项式 / 格 / 有限域数学库**（`std/linalg` 为浮点线性代数，非模 q 环运算）。
- **随机源**：`rdu/rnd.tie` 为 xorshift64 伪随机（**非密码学安全**）；PQC 密钥生成需密码学安全
  随机源，纯 tie 路径必须先接入系统 CSPRNG（Windows `BCryptGenRandom`）。
- **字节承载**：tie `string` 为 UTF-8、可含 NUL，但不能可靠承载 ≥0x80 的原始任意字节，IO 统一
  用**小写 hex 字符串**（与 asymmetric-roadmap / ext 一致）。

---

## 2. 三条路线对比

> extern 后端三选：**Windows CNG（内建，已含 ML-KEM/ML-DSA）**、**liboqs（需自带 dll）**、
> **OpenSSL 3.5+（需自带 dll）**。CNG 与 liboqs/OpenSSL 的取舍见 §3 核实与 §4 推荐。

| 维度 | A. 纯 tie 实现 | B. extern C 库（CNG / liboqs / OpenSSL 3.5+） | C. 混合（按算法分派：extern + 纯 tie） |
| --- | --- | --- | --- |
| **算法覆盖** | ML-KEM / ML-DSA / SLH-DSA 全栈自研（NTT、多项式 mod q、CBD 噪声、哈希树） | ML-KEM ✓ ML-DSA ✓（CNG 内建）；SLH-DSA ✗（CNG 无）；liboqs 三者皆有 | KEM / 格签名走 extern（B），SLH-DSA 走纯 tie（A 子集） |
| **常数时间 / 侧信道** | **高风险**：tie 无安全常数时间基建，secret 分支 / 索引 / 乘法泄漏风险高；且**无内存清除原语**，密钥残留风险 | **安全**：系统 / 库经 FIPS 140 或专业审计 | extern 部分安全；纯 tie 部分仍暴露同上风险 |
| **正确性** | 自研格数学 + 编码易出边界 bug（中心二项分布、模约简、密钥派生），向量核对工作量巨大 | 系统级已验证，作往返即可 | 混合 |
| **工作量大** | **极大**（ML-KEM-768 约 1500–3000 行 + 全量 NIST ACVP 向量核对） | 小（CNG extern glue 约 300–600 行，同 ECDSA 先例） | 中 |
| **SHAKE XOF 前提** | 须先补 `sha3` → SHAKE128/256 XOF 公开封装（ML-KEM / ML-DSA 均以 SHAKE 为核心） | 不需要（库内自带） | extern 不需；纯 tie 的 SLH-DSA-SHA2 需 SHA2，SHAKE 仅作可选 |
| **外部二进制依赖** | 无 | CNG：无新增 dll（内建于 Windows，链接 `-lbcrypt`）；liboqs / OpenSSL：**须自带并打包 dll** | CNG 无新增；liboqs 有 |
| **平台 / 可用性** | 全平台 | CNG：仅 Windows 11 24H2+（含 ML-KEM / ML-DSA，SLH-DSA 无）；liboqs / OpenSSL：跨平台 | 俱上 |
| **可行性（现状）** | 未证（量大） | **ML-KEM extern 通路与 ECDSA 同型，底层机制已由 asymmetric-roadmap 实证** | CNG 通路沿用实证；纯 tie 仅 SLH-DSA 低风险 |

---

## 3. 外部事实核实（WebSearch 结论，来源见 §8）

### 3.1 标准状态

- NIST **FIPS 203（ML-KEM，原 Kyber）、FIPS 204（ML-DSA，原 Dilithium）、FIPS 205（SLH-DSA，
  原 SPHINCS+）** 于 **2024-08-13** 正式发布。
- **Falcon → FN-DSA** 为 **FIPS 206（制定中 / 草稿）**，因浮点签名常数时间化困难而延迟。
- **HQC** 于 **2025-03** 在格族之外被选中（码基 KEM），作为对格族潜在突破的多样化对冲。

### 3.2 OpenSSL 3.5+（PQC 支持状态）

| 核实项 | 结论 |
| --- | --- |
| 状态 | **OpenSSL 3.5（2025-04-08 起，LTS 至 2030-04）默认 provider 原生并入 ML-KEM、ML-DSA、SLH-DSA** |
| TLS 指纹 | 默认开混合 `X25519MLKEM768`；另有 `P-256+MLKEM768`、`P-384+MLKEM1024` 等混合组 |
| 成熟度 | 官方标注部分接口为 **experimental**；标准算法在默认 provider，无需 oqs-provider |

### 3.3 liboqs（现状）

| 核实项 | 结论 |
| --- | --- |
| 状态 | 活跃维护；**最新 0.16.0（2026-07）** |
| KEM / 签名覆盖 | **ML-KEM（512/768/1024）、ML-DSA（44/65/87）** 均已含；**SLH-DSA** 亦在列（Tier 3）；另有 HQC、SNOVA、MAYO、CROSS、MQOM、UOV 等 NIST 二轮候选 |
| 说明 | 0.16.0 移除旧版 SPHINCS+（Round-3 名），保留标准化 **SLH-DSA**；HQC 曾临时禁用后按 0.16.0 规范重启用；ML-DSA 默认实现切换为 `mldsa-native` |
| 形态 | C 库，需自带并打包（非平台内建）；提供 oqs-provider（OpenSSL 3 provider） |

### 3.4 Windows CNG / BCrypt（PQC 支持状态）

| 核实项 | 结论 |
| --- | --- |
| ML-KEM | **已加入 CNG**：`BCRYPT_MLKEM_ALGORITHM`（L"ML-KEM"），参数集 512/768/1024；官方提供 BCrypt 封装 / 解封装用法示例 |
| ML-DSA | **已加入 CNG**（Windows 11 24H2+ 首个后量子原语），`BCRYPT_MLDSA_ALGORITHM` |
| 复合 | `BCRYPT_COMPOSITE_MLKEM_ALGORITHM`（L"Composite-ML-KEM"，ML-KEM + 传统 KEM 复合）——标注 **prerelease / Windows Insider** |
| SLH-DSA | **CNG 未覆盖**（算法标识表无 SLH-DSA） |
| 可用性 | 微软 2025-05 官宣 PQC 入 Windows（Insider Canary 27852+）；ML-KEM / ML-DSA 随较新 Windows 内置；**内建于 `bcryptprimitives.dll`，无新增二进制依赖** |

> **关键更正**：asymmetric-roadmap 评估时（纯 ECDSA 阶段）BCrypt 无 PQC；**截至 2026-08，
> Windows CNG 已内建 ML-KEM / ML-DSA**。这使「extern CNG」路线从「无 PQC 可用」变为
> 「零新依赖即可满足 KEM + 格签名」——是本次评估最重要的事实更新。

---

## 4. 推荐与分期

### 4.1 推荐：B（extern）先行 + C（纯 tie）补充——按算法分派

| 目标算法 | 推荐后端 | 理由 |
| --- | --- | --- |
| **ML-KEM-768**（密钥封装） | **B. extern CNG** | 内建于 Windows、零新 dll、链接 `-lbcrypt` 与 ECDSA 同型（机制已实证）；常数时间 / 密钥处理由系统保证，规避 tie 无内存清除原语的风险 |
| **ML-DSA-65**（格签名） | **B. extern CNG**（或 liboqs 作跨平台备选） | 同 CNG 内建理由；CNG 不支持时（跨平台 / 旧 Win）退 liboqs |
| **SLH-DSA-SHA2**（哈希签名） | **C. 纯 tie（远期）** | CNG 无 SLH-DSA；哈希基算法与 tie std 哈希族完全咬合（见 §4.2），是**唯一低风险纯 tie 通路** |

> 为何不用 liboqs 作首选 B：tie 目标运行期是 Windows，CNG **内建无新增依赖**，liboqs 需自带
> 并打包 dll、升级需跟进上游 release；CNG 在「KEM + 格签名」覆盖面已够用。liboqs 保留为：
> （1）跨平台（非 Windows）；（2）需 SLH-DSA 也要 extern 快速到位；（3）需 HQC / SNOVA 等候选。

### 4.2 为何 SLH-DSA 是纯 tie 的「最低风险首选」

- SLH-DSA **不需要格数学**：无 NTT、无模 q 多项式环、无常数时间标量乘——本质是
  **哈希函数 + Merkle 树 + 超树（Hypertree）+ 少量 Tweak 参数算术**。
- tie 已具备 **SHA-256（`std/sha256.tie`）+ SHA-3（`std/sha3.tie`，含 Keccak block）**；
  SLH-DSA-SHA2-* 族基于 SHA-256/512，SLH-DSA-SHAKE-* 族基于 SHAKE128/256（从已有
  `sha3.keccak` 加一层 XOF 即可）。
- 因此纯 tie SLH-DSA 的**实现风险 / 工作量远低于任何格算法**（格路线核心难点是常数时间 + 侧信道；
  哈希签名的主要风险仅是 Merkle / 超树的状态与索引正确性，可用 KAT / ACVP 向量收敛）。
- 定位：**平台审计链的长期签名凭证**（安全假设最保守、有效期长），与 CNG 短平快的 KEM / 格签名
  形成互补。

### 4.3 分期建议

| 阶段 | 内容 | 前提 / 验收 |
| --- | --- | --- |
| 一（现行） | 本文档立项评估 | 无需实现 |
| 二 | **ML-KEM-768 extern（CNG）** 探针 + `ext/mlkem.tie` 封装（hex IO + key import / export + encap / decap 往返） | 复用 ECDSA extern 模式；要求目标机 Win 24H2+；往返 + 微变敏感 + KAT 向量一致 |
| 三 | **ML-DSA-65 extern**（CNG / liboqs）封装 | 同上；向量核对 + 验签 |
| 四 | **SLH-DSA-SHA2 纯 tie** 立项：`sha3` → SHAKE XOF 公开化 → Merkle / 超树 → 签名 / 验签 | KAT + ACVP 向量核对；`rdu/rnd` 换 CSPRNG（`BCryptGenRandom`） |
| 五（远期） | 接入插件审计链凭证签发 / 验签 | 自举（自签凭证用 tie 验签）+ 全量回归 |

---

## 5. 落地步骤（每步验收挂钩自举 + 回归）

> 通用验收准则：每步产出独立探针，**与既有回归基线解耦**——新功能不得破坏现有编译 / 运行
> 基线；新增代码的测试归入对应探针目录，不并入通用回归。

| 步骤 | 交付 | 验收挂钩 |
| --- | --- | --- |
| 1 评估期 | 本文档 | 通过评审即可（无代码） |
| 2 基础数学库（仅纯 tie A） | `std/ntt` / `modq` 多项式环，或 `sha3`∷shake XOF | 单测 + KAT 向量；若选 B 跳过 |
| 3 extern 封装（若选 B） | `ext/mlkem` / `ext/mldsa` glue（声明 + 段缓冲 IO） | 编译零错误 + `-lbcrypt` 链入，同 ECDSA 探针 |
| 4 单算法原型 | 单一算法探针（encap/decap 或 sign/verify） | 自举：产出可运行 exe；回归：既有用例通过 |
| 5 向量核对 | NIST ACVP + 每算法 KAT（确定性向量） | 输出字节与标准向量逐字节一致 |
| 6 探针化 | 探针回归进 tests 对应目录 | 与主回归基线隔离运行 |
| 7 接入审计链凭证（远期） | 签发 / 验签接入插件链路 | 自举闭环（tie 验自己的签）+ 全量回归 |

---

## 6. 风险

| 风险 | 等级 | 说明与缓解 |
| --- | --- | --- |
| 实现复杂度 | A 高 / B 低 / C 中低 | 格路线（ML-KEM / ML-DSA 纯 tie）复杂度与 bug 面最大；推荐 extern 承担；纯 tie 只保留 SLH-DSA |
| 常数时间 / 侧信道 | 纯 tie 高 | tie 无安全常数时间基建；纯 tie 格算法不建议用于生产密钥；extern 由系统保证 |
| 内存安全（**tie 无内存清除原语**） | 中 | 密钥 / 共享秘密残留：
  - extern 路径：密钥驻留在系统对象（CNG handle），tie 侧仅接触 hex，泄漏面小；
  - 纯 tie 路径：须先引入**零化清除**约定（临时 buffer 用完覆写）——**本文档明确将其列为纯 tie 强制的先行前置** |
| 互操作向量源 | 中 | KEM / 签名需对齐 ASCII 化字节序（tie 用 hex）；向量源：NIST ACVP / 各算法 KAT / OpenSSL / liboqs 自检向量 |
| 平台可用性（CNG） | 低-中 | ML-KEM / ML-DSA 随 Win 24H2+，部分功能标 prerelease / Insider；旧 Win / 跨平台须退 liboqs 或纯 tie |
| 密码学安全随机源 | 中（纯 tie） | `rdu/rnd` 为 xorshift64 非安全；纯 tie 签名须接 `BCryptGenRandom`（extern）作熵源 |
| 劝退项（YAGNI） | — | 若 PQC 仅用于平台内部审计链、无对外长期密文 / 凭证刚需，**可整体滞后**（Ed25519 都未定，PQC 应在非对称族稳定后推进）；本文档仅背书「评估」，现阶段不投重 |

---

## 7. 决策记录表

| 决策点 | 结论 | 备选 |
| --- | --- | --- |
| PQC 牵头算法 | SLH-DSA 作纯 tie 优先（哈希基、与 std 哈希族咬合、风险远低于格） | ML-KEM 作 extern 优先 |
| 密钥封装 / 格签名实现路径 | **extern（首选 CNG，内建零依赖）** | liboqs（跨平台 / 需 SLH-DSA extern）；OpenSSL 3.5+ |
| extern 后端首选 | **CNG / `-lbcrypt`** | 不做纯 tie 的格路线（量大、常数时间风险） |
| 纯 tie 范围 | 收敛到 **SLH-DSA-SHA2（远期）** | ML-KEM / ML-DSA 纯 tie 仅作教学若促成 |
| 是否现在就投实现 | **否**（先立项评估，待非对称族 Ed25519 稳定后重估） | 若审计链有长期凭证刚需，可提前立项 SLH-DSA |
| 随机源 / 内存清除 | 纯 tie 需先接 CSPRNG 外源 + 引入零化清除约定 | extern 路径暂不需要 |

---

## 8. 外部参考（核实来源）

- NIST FIPS 203 / 204 / 205（2024-08-13 发布）：`csrc.nist.gov/pubs/fips/203/final`（ML-KEM）、
  `.../fips/204/final`（ML-DSA）、`.../fips/205/final`（SLH-DSA）；FIPS 206（FN-DSA）草稿；HQC 2025-03 选定。
- OpenSSL 3.5（PQC）：
  - OpenSSL 3.5 Final Release 博客（2025-04-08）：`mirror.openssl-corporation.org/blog/2025-04-08-openssl-35-final-release.html`
  - OpenSSL NEWS.md（ML-KEM / ML-DSA / SLH-DSA default provider）：`github.com/openssl/openssl/blob/master/NEWS.md`
  - 3.5+ TLS 默认 `X25519MLKEM768` 与混合组：`cloud.tencent.com/developer/article/2568549`
  - 部分接口标注 experimental 的说明：`evertrust.io/guide/pqc-algorithms/`
- liboqs：
  - Releases（0.16.0，2026-07；移除 SPHINCS+、保 SLH-DSA）：`github.com/open-quantum-safe/liboqs/releases`
  - 算法支持 / Tier 状态：`openquantumsafe.org/liboqs/api/doxygen/index.html`
  - ML-DSA 默认 `mldsa-native`、HQC 重启用、候选算法：`lwn.net/Articles/1086192/`（SUSE 安全通告）
- Windows CNG（BCrypt）：
  - CNG 算法标识（`BCRYPT_MLKEM_ALGORITHM`、`BCRYPT_MLDSA_ALGORITHM`、`BCRYPT_COMPOSITE_MLKEM_ALGORITHM`，
    标注 prerelease）：`learn.microsoft.com/windows/win32/seccng/cng-algorithm-identifiers`
  - 用 BCrypt 进行 ML-KEM 封装 / 解封装官方示例：`learn.microsoft.com/zh-hk/windows/win32/seccng/cng-mlkem-examples`
  - 微软官宣 PQC 入 Windows（Insider Canary 27852+，2025-05）：Microsoft Security Blog（techcommunity）
  - Windows 11 24H2 内建 ML-KEM / ML-DSA 为 CNG 一等算法：`paragmali.com/blog/cng-architecture-bcrypt-ncrypt-ksps.md`