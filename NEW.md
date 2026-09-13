# NEW — 发行版新鲜事
*EN: NEW — Release highlights*

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

EN: Highlights of the **current release** of the tie language, for readers who want to know what's new at a glance. Full change log: [CHANGELOG.md](CHANGELOG.md). Project overview and usage: [README.md](README.md).

**内部代号**：Shipyard 造船厂（2026.2 版本代号，编译器进入 Keel 龙骨架构时代）
*EN: Codename: Shipyard (the 2026.2 version; the compiler enters the Keel architecture era)*
**本版**：Shipyard-2026.2-preview.2（预发布 2）
*EN: This release: Shipyard-2026.2-preview.2 (preview 2)*
**对比基线**：Shipyard-2026.2-preview.1
*EN: Baseline: Shipyard-2026.2-preview.1*

***

2026.2 预发布 2 聚焦**语言层全量**与**库/工具链大幅落地**：

EN: Shipyard 2026.2 preview 2 delivers the full **language layer** plus a large **library & toolchain** batch:

* 语言两轮 40 项：第一轮 p.8（const fn / 泛型/模式/可空增强 / 运算符重载 / 推导式 / 尾随闭包 / 宏升级等 19 项）+ 第二轮 p.9.11（match 表达式 / if-let / try / defer / 记录字面量 / 切片 / 生成器 / 迭代器 / interface 轻量化等 21 项）
* 内置库 20 项：zlib/gzip·WebP·GIF·JSON5·WAV·regex 增强·datetime·xlsx·zip·fs·process·bytes·color·rng·QR 解码·BMP·单调时钟等
* 编译体验：`--mem-limit`/`--jobs` 资源可调 + 编译缓存（`~/.tiec-cache`，`--no-cache`）
* 工具链：crashdiag 崩溃诊断 / DAP 调试器 / profiler 剖析器 / tpkg 包管理器正式落地 / 脚手架 `tpkg new`
* tshell 命令行壳：REPL+脚本+管道、会话/补全/历史、zd 双形态协议、九模块可嵌入
* 生态：组件仓命名迁移（tdiag/tpkg/twi/tdb）、0-Rust 自举（gate 脚本 .ps1→.tsh.tie 批量迁移）

EN: 40 language features across two rounds (p.8 round 1: 19 items — const fn, generics/pattern/nullable upgrades, operator overloading, comprehensions, trailing closures, macro upgrade; p.9.11 round 2: 21 items — match-as-expression, if-let, try, defer, record literals, slicing, generators, iterator protocol, lightweight interface); 20 builtin libraries (zlib/gzip, WebP, GIF, JSON5, WAV, regex-pro, datetime, xlsx, zip, fs, process, bytes, color, rng, QR decode, BMP, monotonic clock…); compile experience (memory/jobs knobs + compile cache); toolchain (crashdiag, DAP debugger, profiler, formal package manager tpkg, `tpkg new` scaffold); the **tshell** command shell (REPL+scripts+pipelines, session/completion/history, dual-mode framing, nine embeddable modules); ecosystem (component naming migration tdiag/tpkg/twi/tdb; 0-Rust self-host with gates ported .ps1→.tsh.tie).

## 亮点速览 / Highlights

| 亮点 / Highlight | 内容 / Content |
| --- | --- |
| 🏗️ **语言两轮铺满** / Two full language rounds | 特性+语法糖 40 项全落地——const fn、可空链、运算符重载、推导式、尾随闭包、声明式宏（p.8）与 match 表达式、defer、记录/切片/with、生成器、interface 轻量化（p.9.11）/ 40 items across feature & sugar rounds — const fn, optional chaining, operator overloading, comprehensions, trailing closures, declarative macros (p.8); match-as-expression, defer, record/slice/with, generators, lightweight interface (p.9.11) |
| 📚 **内置库 20 项** / 20 builtin libraries | 纯 tie 多媒体与数据格式：zlib/gzip、WebP(VP8L)、GIF、JSON5、WAV、regex 增强、datetime、xlsx、zip、BMP、QR 解码、rng、color、单调时钟、fs/process/bytes 增强等 / pure-tie media & data formats: zlib/gzip, WebP(VP8L), GIF, JSON5, WAV, regex-pro, datetime, xlsx, zip, BMP, QR decode, rng, color, monotonic clock, fs/process/bytes enhancements… |
| ⚙️ **编译体验** / Compile experience | `--mem-limit`/`--jobs` 资源可调 + 编译缓存 `~/.tiec-cache` / configurable resources (mem-limit/jobs) + compile cache (~/.tiec-cache) |
| 🛠️ **工具链四连** / Toolchain quartet | crashdiag 崩溃诊断 / DAP 调试器 / profiler / tpkg 包管理器 + 脚手架 / crashdiag, DAP debugger, profiler, formal tpkg package manager + scaffold |
| 🐚 **tshell 命令行壳** / tshell shell | 三身份壳（REPL/脚本/管道）+ 九模块可嵌入 + `--stdio` 帧协议 / three-role shell (REPL/scripts/pipelines) + nine embeddable modules + `--stdio` framing |
| ♻️ **0-Rust 自举深化** / Deeper 0-Rust bootstrap | gate 脚本大规模 .ps1→.tsh.tie 迁移，门禁不再依赖 Rust 产物 / large-scale gates ported .ps1→.tsh.tie, gates independent of Rust artifacts |