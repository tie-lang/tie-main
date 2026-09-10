# NEW — 发行版新鲜事

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

**内部代号**：Harbor 港湾（2026.1 正式版代号，首个正式版 = 工具链第一次靠岸停泊）
**本版**：Harbor-2026.1（正式版）
**对比基线**：Harbor-2026.1-preview.6

***

tie语言迎来了**首个正式版**——2026.1！这意味着tie语言正式脱离早期开发阶段！

本次更新聚焦于**安全性**与**稳定性**，以及一些**性能优化**。我们还将tie语言工具链开发到了Linux上。

作者使用tie语言制作了5个大型项目，证明了tie语言可以投入生产环境。

## 亮点速览

| 🐧 **Linux 平台**  | 编译器内联 POSIX 分支（process/net/args/cwd/env）+ std/csprng getrandom + regex 运行期 POSIX 桥 + trm-lite pthread shim |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| 🔐 **纯 tie 密码学** | ecdsa P-256 纯 tie 落地（复用 P-256 点数 + RFC 6979 确定性 k）+ TLS 认证链切换，弃 Windows CNG 依赖                             |

***

## 几个重要的修复

### 大程序崩溃根因定案

"非平凡程序"（dpcodec/zstd/jcc-pack 全量等）产出即崩的家族根因收官：**表变量赋值
引用计数缺 1**（release 旧值后才 store）+ 循环体 alloca 全量提升 + 入口零初始化 +
非入口表局部登记 + 循环变量回边 + 表达式返回 retain——ed25519 阶梯泄漏消除，新生产
不动点 ACECEBA5（自举 tiec2==tiec3 逐字节一致）。

### TLS 公网握手修复

https 公网握手 0xC0000005 根因修复（循环内表局部 alloca 未初始化槽 release 垃圾 +
字段 retain + SNI），配纯 tie secp256r1 ECDH（p256.tie），baidu TLS 1.2 握手闭环。
