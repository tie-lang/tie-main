# NEW — 发行版新鲜事
*EN: NEW — Release highlights*

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

EN: Highlights of the **current release** of the tie language, for readers who want to know what's new at a glance. Full change log: [CHANGELOG.md](CHANGELOG.md). Project overview and usage: [README.md](README.md).

**内部代号**：Harbor 港湾（2026.1 正式版代号，首个正式版 = 工具链第一次靠岸停泊）
*EN: Codename: Harbor (the 2026.1 stable; the toolchain's first landing)*
**本版**：Harbor-2026.1（正式版）
*EN: This release: Harbor-2026.1 (stable)*
**对比基线**：Harbor-2026.1-preview.6
*EN: Baseline: Harbor-2026.1-preview.6*

***

tie语言迎来了**首个正式版**——2026.1！这意味着tie语言正式脱离早期开发阶段！

EN: tie has reached its **first stable release** — 2026.1! The language has formally left the early-development stage.

本次更新聚焦于**安全性**与**稳定性**，以及一些**性能优化**。我们还将tie语言工具链开发到了Linux上。

EN: This release focuses on **safety** and **stability**, plus a number of **performance optimizations**. We also brought the tie language toolchain to Linux.

作者使用tie语言制作了5个大型项目，证明了tie语言可以投入生产环境。

EN: The author has built five large projects in tie, demonstrating that the language is ready for production use.

## 亮点速览 / Highlights

| 亮点 / Highlight | 内容 / Content |
| --- | --- |
| 🐧 **Linux 平台** / Linux platform | 编译器内联 POSIX 分支（process/net/args/cwd/env）+ std/csprng getrandom + regex 运行期 POSIX 桥 + trm-lite pthread shim / Compiler-inline POSIX branches (process/net/args/cwd/env) + std/csprng getrandom + runtime-pattern POSIX regex bridge + trm-lite pthread shims |
| 🔐 **纯 tie 密码学** / Pure-tie crypto | ecdsa P-256 纯 tie 落地（复用 P-256 点数 + RFC 6979 确定性 k）+ TLS 认证链切换，弃 Windows CNG 依赖 / pure-tie ecdsa P-256 (reusing the P-256 point math + RFC 6979 deterministic k) + the TLS chain now switching to it, dropping the Windows CNG dependency |

***

## 几个重要的修复 / Key fixes

### 大程序崩溃根因定案 / Large-program crash root cause resolved

"非平凡程序"（dpcodec/zstd/jcc-pack 全量等）产出即崩的家族根因收官：**表变量赋值
引用计数缺 1**（release 旧值后才 store）+ 循环体 alloca 全量提升 + 入口零初始化 +
非入口表局部登记 + 循环变量回边 + 表达式返回 retain——ed25519 阶梯泄漏消除，新生产
不动点 ACECEBA5（自举 tiec2==tiec3 逐字节一致）。

EN: The long-standing crash family on "non-trivial" programs (dpcodec/zstd/jcc-pack at full scale) is closed: **table-variable assignment under-referenced by one** (release of the old value after store) + loop-body alloca hoisting + entry zero-init + non-entry table locals registration + loop-variable back edges + expression-return retain. The ed25519 ladder leak is gone; the new production fixpoint ACECEBA5 (bootstrap tiec2==tiec3 byte-identical).

### TLS 公网握手修复 / TLS handshake fix

https 公网握手 0xC0000005 根因修复（循环内表局部 alloca 未初始化槽 release 垃圾 +
字段 retain + SNI），配纯 tie secp256r1 ECDH（p256.tie），baidu TLS 1.2 握手闭环。

EN: The 0xC0000005 in public https handshakes is root-caused and fixed (release of garbage in uninitialized slots of loop-local table allocas + field retain + SNI), paired with the pure-tie secp256r1 ECDH (p256.tie) — a baidu TLS 1.2 handshake now completes end to end.