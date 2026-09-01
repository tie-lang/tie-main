# p.6.6 库补全总规划 + p.6.6.1 TLS 客户端设计

* 日期 / Date：2026-09-01

* 状态 / Status：设计待审（Design pending review）

***

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

***

## 2. p.6.6 子项总盘子 / Sub-item Plan

| 子项 / Item | 库 / Library | 内容 / Content                                                                             |
| --------- | ----------- | ---------------------------------------------------------------------------------------- |
| p.6.6.1   | ext/tls     | TLS 1.3 + 1.2 客户端（纯 tie）、X.509 解析与完整链校验、字节级网络 IO（p.6.4.5 承接）                             |
| p.6.6.2   | std/http 升级 | 完整 HTTP 客户端：https / POST / headers / cookies / 重定向；命名空间 httpc，旧 http.get 保留兼容            |
| p.6.6.3   | std/sse     | SSE 流式解码（`text/event-stream`：event / data / id / retry；LLM / WebSocket / Web 框架前置件）            |
| p.6.6.4   | ext/html    | HTML 分词 + DOM 树 + 选择器抽取 + 链接提取 + HTML→纯文本                                              |
| p.6.6.5   | ext/xml     | XML 分词 + 解析（与 html 共用标记语言分词底座；供 svg / 配置消费）                                          |
| p.6.6.6   | ext/spidey  | 爬虫治理：robots.txt 解析 + 限速 + URL 去重 + 编排（依赖 p.6.6.4 html）                                 |
| p.6.6.7   | std/ws      | WebSocket 客户端：握手 + 帧编解码 + 掩码（依赖 p.6.6.2 httpc）                                        |
| p.6.6.8   | std/smtp    | SMTP 发信：EHLO / AUTH / MAIL / RCPT / DATA，可配 STARTTLS（依赖 p.6.6.1 tls）                   |
| p.6.6.9   | std/dns     | DNS 解析：A / AAAA / TXT / MX 查询（依赖 std/net UDP）                                             |
| p.6.6.10  | std/yaml    | YAML 解析：块缩进 / 流式 / 标量类型（key-value / 列表 / 嵌套）                                        |
| p.6.6.11  | ext/config  | TOML 支持提升（并入 config：表 / 数组表 / 内联表，与 INI/KV 统一入口）                                      |
| p.6.6.12  | std/markdown | markdown 解析：块级元素 / 行内标记 → 结构表                                                      |
| p.6.6.13  | ext/png     | PNG 编解码：chunk 解析 + 滤波 + 位深/色彩类型（zlib 已有 → 复用 codec）                                  |
| p.6.6.14  | ext/qr      | QR 码生成：RS 纠错 + 矩阵布局 + 版本/掩码                                                      |
| p.6.6.15  | ext/svg     | SVG 解析：元素树 + 路径/形状结构（依赖 p.6.6.5 xml 底座）                                            |
| p.6.6.16  | std/tpl     | 模板引擎：`{{expr}}` 求值 + 渲染字符串/文件                                                     |
| p.6.6.17  | std/diff    | 文本 diff：LCS → 行级增删改（+ 统一格式输出）                                                       |
| p.6.6.18  | std/cron    | cron 调度：5 字段表达式 → 下次触发时间 / 到期判断（依赖 std/time）                                        |
| p.6.6.19  | std/jwt     | JWT：HS256 / RS256 签发与验证（依赖 std 哈希 + tls 的 RSA/ECDSA，供 p.6.6.21 会话）                      |
| p.6.6.20  | 数据库         | SQLite 驱动：C ABI 桥（参考 ext/ecdsa extern 范式）或纯 tie                                         |
| p.6.6.21  | Web 服务框架    | std/http\_server 升级：路由表 / keep-alive / 静态文件 / SSE 推送 / JWT 会话                           |
| p.6.6.22  | LLM 调用库     | OpenAI 兼容客户端：POST + JSON + SSE 流式（依赖 p.6.6.2 / p.6.6.3）                                 |
| p.6.6.23  | sys/win32   | 平台专用层首期：基础（注册表/系统信息/剪贴板/环境强化/用户目录/窗口消息）+ 高级（进程枚举/服务控制/网络接口/硬件信息）             |

* 依赖方向（单向）/ Dependency direction (one-way): tls → httpc → sse；html → xml → svg；
  httpc → ws；tls → smtp / jwt；httpc+sse → llm；db 相对独立。
* 平台层 / Platform layer: sys/win32 之后 linux/mac 同名层，命名空间 sys\_win32 / sys\_linux / sys\_mac。

* 公共底座 / Shared foundation: ext/tls 与 std/http 升级版是 LLM / 爬虫 / Web 框架的公共底座，
  因此优先完成（p.6.6.1、p.6.6.2）。
  EN: ext/tls and the upgraded std/http are the shared foundation for the LLM / crawler / web
  framework; hence they come first (p.6.6.1, p.6.6.2).

***

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

| 版本 / Version | 套件 / Suite                                                                            |
| ------------ | ------------------------------------------------------------------------------------- |
| TLS 1.3      | TLS\_AES\_128\_GCM\_SHA256、TLS\_AES\_256\_GCM\_SHA384、TLS\_CHACHA20\_POLY1305\_SHA256 |
| TLS 1.2      | TLS\_ECDHE\_RSA\_WITH\_AES\_128\_GCM\_SHA256 / AES\_256\_GCM / CHACHA20\_POLY1305     |

* 密钥协商 / Key agreement: x25519（std/x25519 已有）；secp256r1 列为可选（依赖 ext/ecdsa 底座）。

* 证书验签 / Certificate verification: RSA PKCS#1 v1.5/PSS（std/bigint.powmod 已有）、
  ECDSA P-256（ext/ecdsa.verify 已有）。

### 3.5 编译前置 / Compiler Prerequisite

tie 无字节级网络接收原语（net\_tcp\_recv 返回 string，无法承载 >=0x80 原始字节）。因此
p.6.6.1 首先扩展编译器，注册两个新原语：

```tie
net_tcp_recv_bytes(handle: i64, max: i64) -> table<i64>  // 接收原始字节
net_tcp_send_bytes(handle: i64, data: table<i64>) -> i64 // 发送原始字节
```

* 注册位置 / Registration points: sbuiltin（语义内置表）、middle/data（原语名表）、
  irgen\_expr（调用生成，两处）、llvmgen\_str（LLVM declare）。

* interp 路径同步支持。

* 验证 / Gate: 单文件探针 TCP 回环字节收发往返全 PASS + 自举 tiec2==tiec3（不动点）。

***

## 4. 密码件盘点（缺什么补什么）/ Crypto Inventory (fill the gaps)

| 缺失件 / Gap              | 补法 / Fill                             | 位置 / Where   |
| ---------------------- | ------------------------------------- | ------------ |
| AES-GCM                | ext/aes 加密轮 + GHASH + GCTR（GF(2^128)） | tls/gcm.tie  |
| ChaCha20-Poly1305 AEAD | 组合现有 ext/chacha20 + std/poly1305      | tls/aead.tie |
| ASN.1 DER 解析           | 从零实现 DER TLV 解析器                      | tls/der.tie  |
| X.509 结构               | tbsCertificate / 签名 / 公钥提取            | tls/x509.tie |
| RSA 验签                 | bigint.powmod（已有）+ PKCS#1 v1.5/PSS 解包 | tls/x509 内   |
| ECDSA P-256 验签         | 复用 ext/ecdsa.verify                   | 引用           |
| secp256r1 协商           | 可选；x25519 为主（std/x25519 已有）           | tls1\_2 内    |
| 信任锚                    | 内置常见根 CA 公钥表（SPKI）+ 可配置追加             | chain.tie    |

***

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

* 测试策略 / Test strategy: 每步独立探针（对齐 tests/kdf\_probe、tests/asym\_probe 风格）；
  密码组件用 RFC 权威向量硬编码断言；握手与链校验用本机 openssl s\_server（OpenSSL 3.6.1，
  已确认可用），不依赖外网。

* 文档 / Docs: 双语（中文 + 英文），无内部阶段编号，README/CHANGELOG 按仓库规范。

***

## 6. 后续子项简述 / Following Sub-items (brief)

* p.6.6.2 std/http 升级：在 std/net 字节 IO + ext/tls 之上提供 httpc 命名空间完整客户端；
  旧 http.get 保留兼容返回 Result。

* p.6.6.3 std/sse：`text/event-stream` 流式解码（event/data/id/retry 字段，行式增量读取）；
  LLM（p.6.6.22）与 WebSocket（p.6.6.7）与 Web 框架 SSE 推送（p.6.6.21）的前置件。

* p.6.6.4 ext/html：HTML 分词器 + DOM 树（平行表）+ 选择器（tag/class/id/属性）+ 链接提取
  + HTML→纯文本（可读性提取）。

* p.6.6.5 ext/xml：XML 分词器与解析（与 html 共用标记语言分词底座，block 结构树 +
  属性/命名空间），供 svg（p.6.6.15）与配置场景消费。

* p.6.6.6 ext/spidey：robots.txt 解析 + 限速 + URL 去重 + 编排（子命名空间 html/robots/crawl）。

* p.6.6.7 std/ws：WebSocket 客户端——HTTP Upgrade 握手（依赖 p.6.6.2）+ 帧编解码
  （FIN/opcode/mask/长度）+ 掩码与 payload 校验；供实时推送/聊天。

* p.6.6.8 std/smtp：SMTP 发信——EHLO / AUTH（LOGIN/PLAIN）/ MAIL / RCPT / DATA / QUIT，
  可配 STARTTLS 升级（依赖 p.6.6.1 tls）；附 MIME 文本/附件基础。

* p.6.6.9 std/dns：DNS 解析——UDP 查询 A / AAAA / TXT / MX / NS（依赖 std/net UDP），
  报文编解码 + 服务器可配。

* p.6.6.10 std/yaml：YAML 解析——块缩进/流式/标量类型（key-value / 列表 / 嵌套映射），
  输出平行表（对齐 std/json 节点风格）。

* p.6.6.11 ext/config：TOML 支持提升——[table] / [[array-of-table]] / 内联表 / 基础
  数据类型，与既有 INI/KV 统一入口出来。

* p.6.6.12 std/markdown：markdown 解析——块级元素（标题/列表/引用/代码/表格）与行内
  标记（粗体/斜体/链接/行内代码）→ 结构表。

* p.6.6.13 ext/png：PNG 编解码——chunk 遍历（IHDR/IDAT/IEND/PLTE）+ 滤波（5 型）+
  位深/色彩类型适配（zlib 已有则复用 codec）。

* p.6.6.14 ext/qr：QR 码生成——RS 纠错码 + 版本/掩码 + 模块矩阵输出（可转 ASCII/PNG）。

* p.6.6.15 ext/svg：SVG 解析——元素树 + 路径/形状/变换结构（依赖 p.6.6.5 xml 底座）。

* p.6.6.16 std/tpl：模板引擎——`{{expr}}` 求值 + 控制结构（if/for），渲染字符串/文件；
  供页面/代码生成/文档复用。

* p.6.6.17 std/diff：文本 diff——LCS → 行级增删改 + 统一格式输出（供 config 对比/文档）。

* p.6.6.18 std/cron：cron 调度——5 字段表达式（分/时/日/月/周）→ 下次触发时间 /
  到期判断（依赖 std/time）。

* p.6.6.19 std/jwt：JWT——HS256 / RS256 签发与验证（base64url + 签名，依赖 std 哈希 +
  p.6.6.1 tls 的 RSA/ECDSA），供 p.6.6.21 会话。

* p.6.6.20 数据库：SQLite 驱动——C ABI 桥（参考 ext/ecdsa 的 extern 范式）：
  open / exec / query / 行迭代 / 预处理。

* p.6.6.21 Web 服务框架：std/http\_server 升级——路由表 / keep-alive / 静态文件 /
  SSE 推送（p.6.6.3）/ JWT 会话（p.6.6.19）。

* p.6.6.22 LLM 调用库：OpenAI 兼容客户端——POST + JSON 请求体 + SSE 流式响应解析
  （依赖 p.6.6.2 httpc + p.6.6.3 sse），对话/补全/流式回调。

* p.6.6.23 sys/win32：平台专用层首期（命名空间 sys\_win32）——基础六件：注册表读写
  （RegQuery/Set/Enum）、系统信息（版本/内存/CPU）、剪贴板文本（Get/SetClipboardData）、
  环境变量强化、用户目录/桌面路径（SHGetKnownFolderPath）、窗口消息基础（FindWindow/
  PostMessage）；高级四项：进程枚举（Toolhelp）、服务控制（OpenSCManager/Enum）、
  网络接口（GetAdaptersInfo）、硬件信息（WMI 子集或 GetSystemInfo 扩展）。linux/mac
  后续 sys\_linux / sys\_mac 同名层。定位独立于 std/ext（平台绑定），延续 rdu 的
  「层级独立、自包含」纪律。

***

## 7. 待决项 / Open Items

* secp256r1 密钥协商是否在 p.6.6.1 内一并实现（缺省：x25519 为主，P-256 可选延期）。
  EN: whether secp256r1 key agreement is implemented inside p.6.6.1 (default: x25519 primary,
  P-256 optional / deferred).

* 编译器原语改动归属：归入 p.6.6.1（本设计），与 p.6.4.5 net\_\* 原语 tie 化各自独立、
  互不阻塞。
  EN: the compiler primitive change belongs to p.6.6.1 (this design), independent of and
  unblocked by p.6.4.5 (net\_\* primitive tie-ification).

