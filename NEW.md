# NEW — 发行版新鲜事

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

**内部代号**：Harbor 港湾（2026.1 正式版代号，首个正式版 = 工具链第一次靠岸停泊）
**本版**：Harbor-2026.1-preview.6
**对比基线**：Harbor-2026.1-preview.5

***

preview.6 是 2026.1 预发布段的**收官版**：编译器大程序崩溃根因收官、TLS 公网握手
修复与 ed25519 泄漏根治，并完成 **0-Rust 自举收官**的最后一环——LSP 重写（tsp）。
同时落地 trm-lite 双形态真并行与三色/分代 GC、23 个标准/扩展库补全、Skia 全栈图形
（ptr/repr(C)/窗口/事件/主循环）、tink v2 互联协议（zrpc + 加密位接线）与 tiec
诊断标号体系。

## 亮点速览

| ⚙️ **编译器**    | 大程序崩溃根因收官（表引用计数）+ TLS 公网握手修复 + E/W 诊断标号体系 + 生产不动点  |
| ------------- | -------------------------------------------------------------------- |
| 🛰️ **LSP 重写** | tsp 0-Rust 收官：16 能力矩阵（补全/跳转/引用/语义令牌/重命名/格式化…）+ VSCode 接线 |
| 🧵 **并发运行时** | trm-lite 双形态真并行（常驻池/窃取/细锁）+ 三色/分代 GC + WaitGroup + channel Go 语义 |
| 📚 **库补全**    | 23 库落地：tls/httpc/sse/html/xml/spidey/ws/smtp/dns/yaml/toml/markdown/png/qr/svg/tpl/diff/cron/jwt/sqlite/http_server/llm/sys-win32 |
| 🎨 **Skia 图形** | ptr 类型化指针 + repr(C) + extern unsafe + 窗口嵌入/事件/主循环 + 软件光栅基线 |
| 🔗 **数据互联**   | tink v2 帧协议（tsha1f 校验）+ 多语言库 + zrpc 可靠传输 + x25519 加密位接线 |

***

## 编译器：正确性收官

### 大程序崩溃根因定案（p.6.1.7）

"非平凡程序"（dpcodec/zstd/jcc-pack 全量等）产出即崩的家族根因收官：**表变量赋值
引用计数缺 1**（release 旧值后才 store）+ 循环体 alloca 全量提升 + 入口零初始化 +
非入口表局部登记 + 循环变量回边 + 表达式返回 retain——ed25519 阶梯泄漏消除，新生产
不动点 ACECEBA5（自举 tiec2==tiec3 逐字节一致）。

### TLS 公网握手修复（p.6.1.8）

https 公网握手 0xC0000005 根因修复（循环内表局部 alloca 未初始化槽 release 垃圾 +
字段 retain + SNI），配纯 tie secp256r1 ECDH（p256.tie），baidu TLS 1.2 握手闭环。

### 诊断标号体系（p.6.9.15）

tiec 全部错误/警告带 **C# 式标号**（五位纯序号 `error[E#####]` / `warning[W#####]`，
E00001 起全局连续，家族仅作归类）：归一化折叠 + 双查表的 `diagcode.tie`、tie 语言
自写生成器、542 条目录（td 清单 + zd 变体）；警告每条附「这样写的坏处」；配套双语
**tie-diag** 仓库按标号阐明成因与解决方案。

## 语言地基

* **ptr 类型化指针（p.6.8.1）**：`ptr` 类型 + addr_of/deref/指针算术 + unsafe 块/函数
  （文件级逃生舱）；安全代码触碰指针 = 编译错误；
* **repr(C) 结构体（p.6.8.2）**：显式 ABI 布局，字段偏移对照 C 编译输出全等；
* **extern 扩展（p.6.8.3）**：extern 强制 unsafe + ptr 参数/返回值 + 结构体按引用 +
  string↔char\*；
* **表内存自动回收（p.6.10.2-4）**：tl_tbl 引用计数 API（retain/release）+ irgen 表
  赋值插桩 + 作用域出口析构 + 嵌套表/循环内 var 遮蔽回收——2000 万次临时表循环峰值
  4.2MB（内存有界）。

## 并发运行时：trm-lite 双形态真并行（p.6.5 + p.6.7）

* **复杂形态完整化**：work-stealing 调度器（多 OS 线程池 + 双端队列 + 任务窃取 + 抢占）、
  并发三色 GC（写屏障 + 后台回收器）、分代 + mark-compact 整理、可迁移栈、精确根
  （任务闭包 env 即根）、channel 语言原语、actor × trm-lite mailbox 咬合；
* **简单形态真并行（p.6.7.6/6.7.7）**：S-pool 常驻线程池 + S-deque 窃取队列；
* **复杂形态常驻池 + per-P 细锁（p.6.7.8/6.7.9）**：去每轮 drain 重建、每 worker 段
  独立锁，窃取窗口缩小（ms4 < ms1 可复现）；
* **结构化并发**：协作抢占统一（yield/gosched + 时间片插桩）、WaitGroup（spawn 分组 +
  等全部完成）、channel Go 语义（close 广播唤醒 + select 多路收发）；
* **双形态验收矩阵（p.6.7.13）**：两形态各自真并行探针 + 行为一致对比 + m6_actor 零回归。

## 库补全：23 库（p.6.6，一库一子项）

* **网络**：ext/tls（TLS 1.3+1.2 纯 tie + X.509 全链校验）、std/httpc（完整 HTTP：
  https/POST/headers/cookies/重定向）、std/sse（流式事件解码）、std/ws（WebSocket）、
  std/smtp（STARTTLS 发信）、std/dns（A/AAAA/TXT/MX）；
* **Web 服务**：std/http_server 升级（路由表/keep-alive/静态文件/SSE 推送/JWT 会话）、
  std/jwt（HS256/RS256）、std/llm（OpenAI 兼容客户端 + SSE 流式）；
* **结构化数据**：ext/html（分词/DOM/选择器/链接）、ext/xml（含命名空间）、std/yaml、
  ext/config（TOML 提升）、std/markdown、std/tpl 模板引擎；
* **图形/编码**：ext/png（编解码）、ext/qr（RS 纠错 + 8 掩码）、ext/svg；
* **工具**：std/diff（LCS 行级 diff）、std/cron（5 字段调度）、std/sqlite（C ABI 桥）、
  ext/spidey 爬虫治理（robots/限速/去重/编排）；
* **平台**：sys/win32（注册表/系统信息/剪贴板/进程枚举/服务控制/网络接口/硬件信息）。

## Skia 全栈图形（p.6.8）

* 源码裁剪（SkSurface/SkCanvas/SkPaint/SkPath/SkTextBlob/SkFont/SkImage/SkCodec +
  Raster 软件光栅），构建脚本 tie 写，产物静态库；
* extern "C" thunk + trm.ui.gfx 句柄层（repr(C) 句柄 + 方法转发 + arena 生命周期）；
* D2 命令列表翻译器（rect/text/path/image + font_measure 文本度量桥）；
* Win32 窗口嵌入层（CreateWindow + 消息泵 + 后备缓冲 blit）+ 事件系统 E3（鼠标/键盘
  事件队列 + 信号标志）+ 主循环（脏矩形重绘 + 帧节流/vsync）；
* 全栈演示（窗口 + 命令列表 + 事件响应 + row/column 组合式布局雏形）+ 验收矩阵 +
  软件光栅性能基线（vs GDI）。

## LSP 重写：tsp 0-Rust 收官（p.6.9）

* std/stdio 字节原语 → JSON-RPC over stdio 协议层 → 复用编译器前端（lex/parse/
  semantic）的分析/符号索引/增量诊断；
* **16 能力矩阵**：补全/悬停/跳转定义/跨文件引用/签名帮助/文档符号/语义令牌/折叠/
  跨文件重命名/文档高亮/快速修复/格式化 + 生命周期/错误隔离/import 变更级联；
* **性能**：全字节扫描改造后 97KB 文档 didOpen 93s → 1.7s（死循环修复 + 消除 O(n²)
  str_char 拖累）；
* **VSCode 接线**：vscode-languageclient 自动注册全部特性（能力声明 16 项）。

## 数据互联：tink v2（p.6.11）

* **帧 v2 协议**（std/tink_v2.tie）：magic + version + flags + TLV 扩展头 + payload +
  tsha1f 校验（默认 8 符号 48 进制，强档 f/n=48 截 32 字节）+ 分块流 + v1 兼容读；
* **多语言库 v2 化**：c/rust/python/aardio 首批（各保留 v1 读路径），跨语言 KAT 一致；
* **zrpc 信封 + 可靠传输**：CALL/REPLY/ACK/PING/PONG + ACK 序号确认 + 丢帧重传重组；
* **加密位接线**：x25519 握手 + HKDF 对称密钥 + ascon_mac128（XOR-OTR+MAC）AEAD——
  P2P 传输层准备。

***

## 挑战与回退记录

字符串拼接就地追加优化（preview.5 记录 300× 实测）因别名安全自举不稳回退，详见
docs/language.md 性能节记录；p.6.1.7 RCA 期间的五变体边界化修复全数证伪，最终以
引用计数根因定案（见上）。
