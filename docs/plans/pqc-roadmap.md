# 规划：后量子密码（PQC）接入评估与路线图（ML-KEM / ML-DSA / SLH-DSA）

> 状态：**决策已定——全量纯 tie**（2026-08-29，纯文档，未实现）
> 关联：`docs/plans/asymmetric-roadmap.md`（非对称族评估：ECDSA/Ed25519/X25519 先例）、
> `std/sha256.tie` / `std/sha3.tie` / `std/blake2.tie`（std 哈希族）、
> `ext/aes.tie` / `ext/chacha20.tie` / `ext/ascon_aead.tie`（ext 对称族）、
> `docs/plans/unsafe-model.md`（unsafe / extern 能力边界）。
> 结论一句话：**全量纯 tie 实现——SLH-DSA-SHA2（哈希基）优先 → ML-KEM-768 → ML-DSA-65；
> 弃 extern CNG / liboqs / OpenSSL。**理由：项目铁律「Cannot use Rust in implementation、
> 去 Rust 桥、tie 自写 tiec」——所有算法库必须纯 tie，不依赖 extern 系统库；CNG/liboqs/OpenSSL
> 仅保留为背景信息与验证向量来源（见 §3 §6）。
> **决策记录：同意用户纯 tie 决策，弃 extern。**
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
- **ext 非对称**：ECDSA P-256 已走 BCrypt extern 落地（`ext/ecdsa.tie`，已实证）——**过渡方案，
  远期纯 tie**；Ed25519/X25519 统一走纯 tie bigint（依赖 `std/bigint.tie`，见 asymmetric-roadmap）。
- **无现成多项式 / 格 / 有限域数学库**（`std/linalg` 为浮点线性代数，非模 q 环运算）。
- **随机源**：`rdu/rnd.tie` 为 xorshift64 伪随机（**非密码学安全**）；PQC 密钥生成需密码学安全
  随机源，纯 tie 只提供算法主体，熵仍须来自系统 CSPRNG（如 Windows `BCryptGenRandom`）——
  **熵源属基础设施，非算法库 extern，不违纯 tie 决策**（见 §3.5）。
- **字节承载**：tie `string` 为 UTF-8、可含 NUL，但不能可靠承载 ≥0x80 的原始任意字节，IO 统一
  用**小写 hex 字符串**（与 asymmetric-roadmap / ext 一致）。

---

## 2. 三条路线对比

> extern 后端三选（**仅作背景与验证向量来源，本项目不采用**）：**Windows CNG（内建，已含
> ML-KEM/ML-DSA）**、**liboqs（需自带 dll）**、**OpenSSL 3.5+（需自带 dll）**。
> 经用户决策：**全量纯 tie，弃 extern**。下表记录被否（A/B）与采纳（C）的路径。

| 维度 | A. extern C 库（CNG / liboqs / OpenSSL 3.5+） | B. 混合（extern + 纯 tie 分派） | **C. 纯 tie 全量（推荐）** |
| --- | --- | --- | --- |
| **算法覆盖** | CNG：ML-KEM ✓ ML-DSA ✓ **SLH-DSA ✗**；liboqs/OpenSSL 三者皆有 | KEM / 格签名 extern，SLH-DSA 纯 tie | **ML-KEM ✓ ML-DSA ✓ SLH-DSA ✓** 全栈自研（NTT、多项式 mod q、CBD 噪声、哈希树、超树） |
| **常数时间 / 侧信道** | 系统 / 库经 FIPS 或专业审计，安全 | extern 部分安全；纯 tie 部分仍暴露 | **高风险（可控）**：tie 无现成常数时间基建；以算法结构常数时间 + sensitive 数据槽覆写约定缓解（§3.5） |
| **正确性** | 系统级已验证，作往返即可 | 混合 | 自研格数学 + 编码易出边界 bug；靠 KAT + ACVP 向量逐字节收敛（每步挂钩） |
| **工作量大** | 小（CNG glue 约 300–600 行，同 ECDSA 先例） | 中 | **极大，分期消化**：SLH-DSA 约 1500+ 行首发；ML-KEM-768 约 1500–3000；**ML-DSA 最重** |
| **SHAKE XOF 前提** | 不需要（库内自带） | extern 不需；纯 tie 部分需 | **必需**：`sha3` → SHAKE128/256 XOF（ML-KEM / ML-DSA 均以 SHAKE 为核心） |
| **额外数学地基** | 不需要 | 仅纯 tie 部分 | **必需 `std/bigint.tie`（256/512 位大数、模逆/模幂）**——Ed25519 与格算法共通底座 |
| **外部二进制依赖** | CNG 内建零 dll；liboqs / OpenSSL 须自带打包 | 同 A + 纯 tie 无 | **无（满足铁律）** |
| **平台 / 可用性** | CNG 仅 Win 24H2+（且无 SLH-DSA）；liboqs/OpenSSL 跨平台 | 俱上 | 全平台 |
| **对项目铁律符合度** | **✗**（依赖 extern 系统库，违背用户决策） | **✗**（部分依赖 extern） | **✓**（纯 tie，去 Rust 桥 / tie 自写 tiec 之延伸） |
| **决策** | **弃**（仅背景） | **弃** | **采纳** |

---

## 3. 外部事实核实（WebSearch 结论，来源见 §8）

> **标注**：本节为外部事实核实（背景信息）——**本项目不采用 extern 实现**，仅采纳其标准与
> 官方 self-test / ACVP 向量作为纯 tie 实现的核对基准。

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
> Windows CNG 已内建 ML-KEM / ML-DSA**。该事实使「extern CNG」在技术上从「无 PQC 可用」变为
> 「零新依赖即可满足 KEM + 格签名」——**但仅作背景信息：经用户纯 tie 决策，本项目不采用 extern，
> 不以此变更路线**。

---

## 3.5 前置依赖（纯 tie 数学地基）

> 纯 tie 全量路线必须先建立「大数 / XOF / 常数时间」三块地基，再进入任何算法。顺序增量自举，
> 每块完工即被后续算法复用——是「哈希基首发消化工具链」的物质前提。

| 地基 | 内容 | 复用算法 | 风险与缓解 |
| --- | --- | --- | --- |
| **`std/bigint.tie`（大数底座）** | 256/512 位无符号大数、模加/模乘、**模逆、模幂**（+ 蒙哥马利 / Barrett 优化）；以 `std/blake2.tie` 双半 `[hi,lo]` 为起点 | **Ed25519/X25519（标量 / 域运算）与格算法（ML-KEM / ML-DSA 的编码、模约简、树 hash 参数）共通底座** | 正确性风险：模约简/模逆边界 bug；以 RFC 8032 Ed25519 向量 + FIPS 203/204 KAT 收敛 |
| **SHAKE XOF（SHA-3 扩展）** | `std/sha3.tie` 的 Keccak block 封一层 SHAKE128/256 XOF（squeeze 任意长输出） | **SLH-DSA-SHAKE**、**ML-KEM**（XOF 派生 A / 种子）、**ML-DSA** 共同前提 | 少；Keccak block 已在 std 实证，仅需 XOF 封装与向量核对 |
| **常数时间与内存清除** | 常数时间结构（固定循环 / 无 secret 索引）；密钥 / 共享秘密清除 | 全部非对称算法 | tie **无 `memzero`**：`sensitive` 数据槽覆写约定——安全上下文里的临时 buffer 用毕逐字覆写为 0x00，不由通用 GC 保证；常数时间性由算法结构 + 向量兜底；**内存清除为该路线强制的先行前置** |

> 随机源（熵源基础设施，非算法 extern）：上述数学地基就绪后，密钥生成先接系统 CSPRNG 熵源
> （如 Windows `BCryptGenRandom`），`rdu/rnd`（xorshift64）不作为安全熵。

---

## 4. 推荐与分期

### 4.1 推荐：**C 纯 tie 全量**（弃 extern CNG / liboqs / OpenSSL）

| 目标算法 | 推荐实现 | 优先级 | 理由 |
| --- | --- | --- | --- |
| **SLH-DSA-SHA2**（哈希签名） | **纯 tie** | **① 首发** | 哈希基：无 NTT、无模 q 多项式环、无常数时间标量乘——纯哈希 + Merkle / 超树，与 std 哈希族（sha2 / sha3）咬合**可达性最高**；先消化「大数 / 常数时间 / KAT」全套基建与流程 |
| **ML-KEM-768**（密钥封装） | **纯 tie** | ② | 需 **NTT / 多项式环 mod q** 库（前置依赖 §3.5）；障碍居中 |
| **ML-DSA-65**（格签名） | **纯 tie** | ③ 最重 | 格族最重：多项式乘 / 格基 / 常数时间面最宽，放最后冲刺 |

> 弃 extern 的理由：**项目铁律——Cannot use Rust in implementation、去 Rust 桥、tie 自写 tiec**；
> 用户明确要求**全部算法库纯 tie 实现，不依赖 extern 系统库**。CNG / liboqs / OpenSSL 仅保留作
> 背景与验证向量来源（其官方 self-test / ACVP 向量用于核对纯 tie 输出），不再作为实现后端。
> 同理弃「混合」：只要引 extern 即违背决策，纯 tie 部分也会被 extern 拖累。

### 4.2 为何 SLH-DSA 是纯 tie 的「最低风险首选」

- SLH-DSA **不需要格数学**：无 NTT、无模 q 多项式环、无常数时间标量乘——本质是
  **哈希函数 + Merkle 树 + 超树（Hypertree）+ 少量 Tweak 参数算术**。
- tie 已具备 **SHA-256（`std/sha256.tie`）+ SHA-3（`std/sha3.tie`，含 Keccak block）**；
  SLH-DSA-SHA2-* 族基于 SHA-256/512，SLH-DSA-SHAKE-* 族基于 SHAKE128/256（从已有
  `sha3.keccak` 加一层 XOF 即可）。
- 因此纯 tie SLH-DSA 的**实现风险 / 工作量远低于任何格算法**（格路线核心难点是常数时间 + 侧信道；
  哈希签名的主要风险仅是 Merkle / 超树的状态与索引正确性，可用 KAT / ACVP 向量收敛）。
- 定位：**平台审计链的长期签名凭证**（安全假设最保守、有效期长），并作为纯 tie 格路线的
  **首发入口**——先用低风险哈希基消化「大数 / 常数时间 / 向量核对」全套基建，再攻格算法。

### 4.3 分期建议

| 阶段 | 内容 | 前提 / 验收 |
| --- | --- | --- |
| 一（现行） | 本文档决策定稿（纯 tie） | 无需实现 |
| 二 | **数学地基**：`std/bigint.tie`（256/512 位大数、模逆/模幂）+ `sha3`→SHAKE128/256 XOF + `sensitive` 槽覆写约定 | 单测 + RFC 8032 Ed25519 向量 + KAT |
| 三 | **SLH-DSA-SHA2 纯 tie（哈希基首发）**：Merkle / 超树 / 签名 / 验签 | NIST SLH-DSA KAT + ACVP 逐字节；接系统熵源 |
| 四 | **Ed25519 / X25519 纯 tie**（依赖 bigint） | RFC 8032 / RFC 7748 向量逐字节 |
| 五 | **ML-KEM-768 纯 tie**：多项式环 mod q、NTT、CBD、K-PKE、encap / decap、密钥派生 | FIPS 203 KAT + ACVP |
| 六 | **ML-DSA-65 纯 tie（格签名，最重）** | FIPS 204 KAT + ACVP |
| 七（远期） | 接入插件审计链凭证签发 / 验签 | 自举（自签凭证用 tie 验签）+ 全量回归 |

---

## 5. 落地步骤（地基 → SLH-DSA → Ed25519/X25519 → ML-KEM → ML-DSA）

> 通用验收准则（每步三挂钩）：**① KAT / ACVP 向量逐字节一致；② 自举**——产出可运行 exe、
> tie 自己编译运行；**③ 回归**——与既有回归基线解耦，不破坏现有编译 / 运行基线；新增测试归入
> 对应探针目录，不并入通用回归。

| 步骤 | 交付 | 验收挂钩 |
| --- | --- | --- |
| 1 数学地基 | `std/bigint.tie`（256/512 位大数、模逆/模幂）+ `sha3`→SHAKE128/256 XOF + `sensitive` 槽覆写 / 常数时间约定 | 单测 + KAT；RFC 8032 Ed25519 向量作早期交叉验证 |
| 2 哈希签名首发 | `std/slhdsa`（SLH-DSA-SHA2 → 可选 SLH-DSA-SHAKE）：Merkle / 超树 / 签名 / 验签 | NIST SLH-DSA KAT + ACVP 逐字节一致 |
| 3 曲线族 | `std/ed25519`、`std/x25519`（依赖 bigint） | RFC 8032 / RFC 7748 向量逐字节一致 |
| 4 格 KEM | `std/mlkem`（ML-KEM-768：多项式环 mod q、NTT、CBD、K-PKE、encap/decap、密钥派生） | FIPS 203 KAT + ACVP |
| 5 格签名 | `std/mldsa`（ML-DSA-65，最重） | FIPS 204 KAT + ACVP |
| 6 接入审计链凭证（远期） | 签发 / 验签接入插件链路 | 自举闭环（tie 验自己的签）+ 全量回归 |

---

## 6. 风险

| 风险 | 等级 | 说明与缓解 |
| --- | --- | --- |
| 实现复杂度 / bug 面 | 纯 tie 高 | 格路线（ML-KEM→ML-DSA）复杂度与 bug 面最大；**缓解：分别期**——SLH-DSA 哈希基首发消化工具链与 KAT 流程，格路线靠逐字节向量收敛 |
| 常数时间 / 侧信道 | 纯 tie 高（可控） | tie 无现成常数时间基建；**缓解**：算法结构常数时间（固定循环 / 无 secret 索引）+ `sensitive` 槽覆写 + 明确不上线侧信道测量 |
| 内存安全（**tie 无内存清除原语**） | 中 | 密钥 / 共享秘密残留：纯 tie 路径须先引入 **`sensitive` 数据槽覆写约定**（临时 buffer 用毕逐字覆写 0x00，不由 GC 保证）——**列为强制的先行前置（§3.5）** |
| 互操作向量源 | 中 | KEM / 签名需对齐 ASCII 化字节序（tie 用 hex）；向量源：NIST ACVP / 各算法 KAT / OpenSSL / liboqs 自检向量（**仅作核对基准，不引用其实现**） |
| 平台可用性 | 低 | 纯 tie 全平台，无 CNG / Win 版本耦合（extern 特有的旧 Win / 跨平台问题在本路线不存在） |
| 密码学安全随机源 | 中 | `rdu/rnd` 为 xorshift64 非安全；密钥生成接系统 CSPRNG 熵源（如 `BCryptGenRandom`）——**熵源属基础设施，非算法 extern** |
| 工期 / 范围膨胀 | 高 | 全栈三算法自研边宽；**缓解：严格分期**（地基→哈希基→Ed25519→ML-KEM→ML-DSA），每步三挂钩收敛后才启动下一步 |
| 劝退项（YAGNI） | — | 已按用户纯 tie 决策立项，不再整体滞后；但若审计链无对外长期凭证刚需，仍可选择性延后格路线保留哈希基凭证 |

---

## 7. 决策记录表

| 决策点 | 结论 | 备选 |
| --- | --- | --- |
| PQC 牵头算法 | **SLH-DSA-SHA2 哈希基作纯 tie 首发**（哈希基、与 std 哈希族咬合、风险远低于格） | ML-KEM 作首发（弃，需 NTT 前置更重） |
| 实现路径 | **纯 tie 全量（弃 extern CNG / liboqs / OpenSSL）** | extern / 混合——仅背景，不采用 |
| 纯 tie 范围 | **ML-KEM-768 + ML-DSA-65 + SLH-DSA-SHA2 全栈** | 收敛到 SLH-DSA（弃，不符合全量纯 tie 决策） |
| 前置依赖 | **`std/bigint.tie` + SHAKE XOF + `sensitive` 槽覆写 / 常数时间约定 + 系统熵源**（§3.5） | 无地基直接上格路线（弃，风险不可控） |
| extern 后端（CNG / liboqs / OpenSSL） | **弃**（仅作背景与验证向量来源） | — |
| 是否现在就投实现 | **是——同意用户纯 tie 决策，弃 extern**；按 地基→SLH-DSA→Ed25519/X25519→ML-KEM→ML-DSA 分期 | 仅立项评估（弃，已被决策取代） |
| 随机源 / 内存清除 | 密钥生成接系统 CSPRNG 熵源 + `sensitive` 槽覆写约定（先行前置） | — |

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