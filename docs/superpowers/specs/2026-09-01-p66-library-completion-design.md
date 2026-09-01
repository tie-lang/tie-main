# p.6.6 库补全总规划 + p.6.6.1 TLS 客户端设计

* 日期 / Date：2026-09-01
* 状态 / Status：设计待审（Design pending review）

---

## 1. 定位 / Positioning

2026.1 正式版以修复缺陷与性能问题为主（p.6.1 正确性 / p.6.2 功能 / p.6.3 性能 /
p.6.4 原语 tie 化 / p.6.5 trm-lite 完善）。p.6.6 进入**库补全**阶段：补齐通用网络、
数据与接入侧能力，使 tie 可独立完成整条「抓取 → 解析 → 入库 → 对外服务」链路。

EN: The 2026.1 stable release focuses on defect fixes and performance (p.6.1 correctness /
p.6.2 features / p.6.3 performance / p.6.4 primitive tie-ification / p.6.5 trm-lite
completion). p.6.6 enters the **library completion** phase: filling general networking,
data, and access-side capabilities so tie can independently cover the whole
"fetch → parse → store → serve" pipeline.

**编号约定**：一个库一个子项号（p.6.6.N）。第三段自动递增。
EN: Naming convention: one library per sub-item number (p.6.6.N); the third segment auto-increments.

---

## 2. p.6.6 子项总盘子 / Sub-item Plan

| 子项 / Item | 库 / Library | 内容 / Content |
| --- | --- | --- |
| p.6.6.1 | ext/tls | TLS 1.3 + 1.2 客户端（纯 tie）、X.509 解析与完整链校验、字节级网络 IO（编译器新原语） |
| p.6.6.2 | std/http 升级 | 完整 HTTP 客户端：https / POST / headers / cookies / 重定向；命名空间 httpc，旧 http.get 保留兼容 |
| p.6.6.3 | ext/html | HTML 分词 + DOM 树 + 选择器抽取 + 链接提取 |
| p.6.6.4 | ext/spidey | 爬虫治理：robots.txt 解析 + 限速 + URL 去重 + 编排 |
| p.6.6.5 | 数据库 | SQLite 驱动（C ABI 桥或纯 tie） |
| p.6.6.6 | Web 服务框架 | std/http_server 升级：路由 / keep-alive / 静态文件 |
| p.6.6.7 | LLM 调用库 | OpenAI 兼容客户端（复用 httpc + SSE 流式） |

* 依赖方向（单向）/ Dependency direction (one-way): tls → httpc → html / spidey / llm。
  p.6.6.5（db）与 p.6.6.6（web）相对独立。
* 公共底座 / Shared foundation: ext/tls 与 std/http 升级版是 LLM / 爬虫 / Web 框架的公共底座，
  因此优先完成（p.6.6.1、p.6.6.2）。
  EN: ext/tls and the upgraded std/http are the shared foundation for the LLM / crawler / web
  framework; hence they come first (p.6.6.1, p.6.6.2).

---

## 3. p.6.6.1 设计 / Design (ext/tls)

### 3.1 目标 / Goals

* 纯 tie 实现 TLS 1.3 客户端（RFC 8446），并兼容 TLS 1.2（RFC 5246）以覆盖老服务器。
* 多加密套件一次到位：AES-128/256-GCM、ChaCha20-Poly1305；密钥协商 x25519 优先，
  secp256r1 可选。
* 完整证书链校验 + 主机名匹配（SAN/CN）+ 内置 CA 信任锚。
* 为 p.6.6.2 的 https 客户端与后续 LLM / Web 框架提供字节级安全信道底座。

EN: A pure-tie TLS 1.3 client (RFC 8446) with TLS 1.2 (RFC 5246) fallback. Multiple cipher
suites at once: AES-128/256-GCM, ChaCha20-Poly1305; key agreement x25519 first, secp256r1
optional. Full certificate chain validation + hostname matching (SAN/CN) + built-in CA trust
anchors. Provides the byte-level secure channel foundation for p.6.6.2 https and later LLM /
web framework.

### 3.2 文件划分 / File Layout

```
ext/tls/
  der.tie        ASN.1 DER TLV 解析器（通用，可被 db 复用）
  x509.tie       X.509 证书结构解析 + 指纹 + 有效期
  chain.tie      证书链构建与校验 + 主机名匹配 + 内置 CA 信任锚
  gcm.tie        AES-GCM 模式（在 ext/aes ECB/CBC 基础上补 GHASH + GCTR）
  aead.tie       ChaCha20-Poly1305 AEAD 组合（复用 ext/chacha20 + std/poly1305）
  tls1_3.tie     TLS 1.3 握手状态机 + 记录层（HKDF 子密钥派生 + AEAD seal/open）
  tls1_2.tie     TLS 1.2 握手状态机 + 记录层（PRF-SHA256 + ECDHE）
  tls.tie        统一入口：tls.connect() 协商 1.3/1.2，返回会话句柄
```

### 3.3 核心接口 / Core Interface

```tie
// 命名空间 tls / namespace tls
pub func connect(host: string, port: i64, ca: table<i64>) -> Session  // 完成握手，返回会话
pub func send(s: Session, plain: table<i64>) -> bool                 // 应用数据加密发送
pub func recv(s: Session, max: i64) -> table<i64>                    // 解密接收（阻塞）
pub func close(s: Session)                                           // 关闭会话
```

* 数据平面全走字节表 `table<i64>`（0..255）：tie 字符串只能承载可打印 ASCII，
  TLS 密文必须用字节表承载（与 bytes.lib 约定一致）。
  EN: The data plane uses byte tables `table<i64>` (0..255) throughout: tie strings can only
  carry printable ASCII, so TLS ciphertext must be carried as byte tables (consistent with
  bytes.lib conventions).

### 3.4 套件与机制 / Cipher Suites and Mechanics

| 版本 / Version | 套件 / Suite |
| --- | --- |
| TLS 1.3 | TLS_AES_128_GCM_SHA256、TLS_AES_256_GCM_SHA384、TLS_CHACHA20_POLY1305_SHA256 |
| TLS 1.2 | TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 / AES_256_GCM / CHACHA20_POLY1305 |

* 密钥协商 / Key agreement: x25519（std/x25519 已有）；secp256r1 列为可选（依赖 ext/ecdsa 底座）。
* 证书验签 / Certificate verification: RSA PKCS#1 v1.5/PSS（std/bigint.powmod 已有）、
  ECDSA P-256（ext/ecdsa.verify 已有）。

### 3.5 编译前置 / Compiler Prerequisite

tie 无字节级网络接收原语（net_tcp_recv 返回 string，无法承载 >=0x80 原始字节）。因此
p.6.6.1 首先扩展编译器，注册两个新原语：

```tie
net_tcp_recv_bytes(handle: i64, max: i64) -> table<i64>  // 接收原始字节
net_tcp_send_bytes(handle: i64, data: table<i64>) -> i64 // 发送原始字节
```

* 注册位置 / Registration points: sbuiltin（语义内置表）、middle/data（原语名表）、
  irgen_expr（调用生成，两处）、llvmgen_str（LLVM declare）。
* interp 路径同步支持。
* 验证 / Gate: 单文件探针 TCP 回环字节收发往返全 PASS + 自举 tiec2==tiec3（不动点）。

---

## 4. 密码件盘点（缺什么补什么）/ Crypto Inventory (fill the gaps)

| 缺失件 / Gap | 补法 / Fill | 位置 / Where |
| --- | --- | --- |
| AES-GCM | ext/aes 加密轮 + GHASH + GCTR（GF(2^128)） | tls/gcm.tie |
| ChaCha20-Poly1305 AEAD | 组合现有 ext/chacha20 + std/poly1305 | tls/aead.tie |
| ASN.1 DER 解析 | 从零实现 DER TLV 解析器 | tls/der.tie |
| X.509 结构 | tbsCertificate / 签名 / 公钥提取 | tls/x509.tie |
| RSA 验签 | bigint.powmod（已有）+ PKCS#1 v1.5/PSS 解包 | tls/x509 内 |
| ECDSA P-256 验签 | 复用 ext/ecdsa.verify | 引用 |
| secp256r1 协商 | 可选；x25519 为主（std/x25519 已有） | tls1_2 内 |
| 信任锚 | 内置常见根 CA 公钥表（SPKI）+ 可配置追加 | chain.tie |

---

## 5. 任务流水线与验收 / Task Pipeline and Acceptance

```
p.6.6.1 TLS 客户端
  1.  compiler: net_tcp_recv_bytes / net_tcp_send_bytes 原语
      验收：TCP 回环字节收发探针 PASS + 自举 tiec2==tiec3
  2.  ext/tls/der.tie + gcm.tie + aead 组合
      验收：DER 探针（解析已知证书）、GCM 探针（RFC 权威向量）
  3.  ext/tls/tls1_3.tie 握手状态机 + 记录层
      验收：本地 openssl s_server 真实握手 + 应用数据回环
  4.  ext/tls/x509.tie + chain.tie 链校验 + 主机名匹配 + 内置 CA
      验收：真实 https 目标站链校验通过；篡改主机名/过期证书被拒
  5.  ext/tls/tls1_2.tie（PRF-SHA256 + ECDHE）
      验收：仅支持 1.2 的服务器握手成功
  6.  ext/tls/tls.tie 统一入口 + 文档 / CHANGELOG
```

* 测试策略 / Test strategy: 每步独立探针（对齐 tests/kdf_probe、tests/asym_probe 风格）；
  密码组件用 RFC 权威向量硬编码断言；握手与链校验用本机 openssl s_server（OpenSSL 3.6.1，
  已确认可用），不依赖外网。
* 文档 / Docs: 双语（中文 + 英文），无内部阶段编号，README/CHANGELOG 按仓库规范。

---

## 6. 后续子项简述 / Following Sub-items (brief)

* p.6.6.2 std/http 升级：在 std/net 字节 IO + ext/tls 之上提供 httpc 命名空间完整客户端；
  旧 http.get 保留兼容返回 Result。
* p.6.6.3 ext/html：HTML 分词器 + DOM 树（平行表）+ 选择器（tag/class/id/属性）+ 链接提取。
* p.6.6.4 ext/spidey：robots.txt 解析 + 限速 + URL 去重 + 编排（子命名空间 html/robots/crawl）。
* p.6.6.5 数据库：SQLite 驱动（C ABI 桥或纯 tie）。
* p.6.6.6 Web 服务框架：std/http_server 升级（路由 / keep-alive / 静态文件）。
* p.6.6.7 LLM 调用库：OpenAI 兼容客户端（POST + JSON + SSE 流式）。

---

## 7. 待决项 / Open Items

* secp256r1 密钥协商是否在 p.6.6.1 内一并实现（缺省：x25519 为主，P-256 可选延期）。
  EN: whether secp256r1 key agreement is implemented inside p.6.6.1 (default: x25519 primary,
  P-256 optional / deferred).
* 编译器原语改动归属：归入 p.6.6.1（本设计），与 p.6.4.5 net_* 原语 tie 化各自独立、
  互不阻塞。
  EN: the compiler primitive change belongs to p.6.6.1 (this design), independent of and
  unblocked by p.6.4.5 (net_* primitive tie-ification).