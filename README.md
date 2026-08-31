# tie

<p align="center">
  <img src="assets/tie-logo-full.svg" alt="tie 语言 Logo / tie language logo" width="600">
</p>

> ⚠️ **早期开发阶段**：语言设计与实现仍在快速演进，语法、语义与工具链随时可能变更，暂不建议用于生产。
> EN: **Early development stage**: the language is still evolving rapidly; syntax, semantics, and toolchain may change at any time. Not recommended for production yet.

tie 是一门**通用编程语言**：用一门语言写逻辑、写界面、写数据库、当数据交换格式。

EN: tie is a **general-purpose programming language**: one language for logic, UI, databases, and data-exchange formats.

我们的目标：全领域通用，Python 的体验，Rust 的性能与安全。

EN: Our goal: universal across domains — Python's experience, Rust's performance and safety.

## 文档目录
*EN: Documentation*

| 文档 / Doc | 内容 / Content |
| --- | --- |
| [README.md](README.md) | 本文件：工程入口（快速开始、CLI、结构、路线图）/ This file: entry point (quick start, CLI, structure, roadmap) |
| [docs/language.md](docs/language.md) | 语法规范：文件结构、类型系统、语句/控制流、函数、数据结构、语法速查表 / Language spec: file structure, type system, statements/control flow, functions, data structures, quick reference |
| [docs/cli.md](docs/cli.md) | CLI 用法：主入口选项、包管理器子命令、多文件并行编译、库编译、REPL 自举 / CLI usage: main entry options, package-manager commands, parallel multi-file builds, library builds, REPL bootstrap |
| [docs/language-comparison.md](docs/language-comparison.md) | 语言对比报告：tie vs 42 种语言的特性/标准库全景对比 / Comparison report: tie vs 42 languages (features / stdlib panorama) |
| [docs/tiec.md](docs/tiec.md) | tiec 自举编译器文档：架构、自举链、CLI、运行时依赖 / tiec self-hosted compiler: architecture, bootstrap chain, CLI, runtime deps |
| [docs/tie-script.md](docs/tie-script.md) | tie:script 模块协议：注册/调用机制、模块约定、协议文本格式 / tie:script module protocol: registration/call mechanism, module conventions, wire format |
| [docs/ai-guide.md](docs/ai-guide.md) | AI 教学指南：语言用法 + 负例 + 编译器架构 / AI teaching guide: usage + negative examples + compiler architecture |
| [docs/prompt-pack.md](docs/prompt-pack.md) | 可粘贴 Prompt 包：自包含简介，直接发给任何 AI / Copy-paste prompt pack: self-contained intro for any AI |
| [NEW.md](NEW.md) | 发行版新鲜事：本发行版的新功能与特色速览 / Release highlights: what's new in this release |
| [docs/plans/](docs/plans/) | 后续开发模块设计规划（trm/tiu/UI/LSP/PQC/硬件加速等；已实现规划归档至 [tie-archive](https://github.com/tie-lang/tie-archive)）/ Upcoming development-module plans (trm/tiu/UI/LSP/PQC/hw-accel…; implemented plans archived in tie-archive) |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录（按发布档）/ Changelog (grouped by release slot) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南：p.x.x.x 编号规范、CHANGELOG 规范、发布流程 / Contributing guide: p.x.x.x numbering, CHANGELOG rules, release flow |

## 快速开始
*EN: Quick start*

```bash
# 编译并运行示例（tiec 自举编译器）/ compile and run an example (tiec self-hosted compiler)
compiler\tiec.exe examples\hello.tie
examples\hello.exe

# 无参数 → 进入 REPL / no args → REPL
compiler\tiec.exe repl\repl.tie
```

`examples/hello.tie` 输出 / Output of `examples/hello.tie`:

```
Hello, tie!
四段式: 预处理 [前端 中间优化 后端]
50
336
100
x 大于 y
0
1
2
3
4
5
6
7
8
9
```

## 工程结构
*EN: Repository structure*

```text
tie/
|
├── compiler/              编译器 / compiler：
│                         - frontend/：词法/语法/语义分析器（lexer/parser/semantic）
│                         - middle/：tie-IR 列式表 + 类型系统
│                         - backend/：irgen + llvmgen + toolchain
│                         - interp/：解释器（REPL 路径）
│                         - config/tdzd：构建配置 / --compress-data（td→zd）
│                         - driver.tie → tiec.exe：CLI 壳
│                         - repl.tie → repl.exe：REPL
|
├── prep                  预处理器核心模块（tie 语言自写：头部提取/角色判定/正文重建，编译期内嵌）
├── std/                  标准库（library-v2 三层之一）：
│                         - 文本/编码：string、utf、ascii、bytes、encoding、base48、regex、json、csv
│                         - 数据结构/算法：sort、collection、set、deque、bigint、graph、linalg、
│                           exmath、math、radix、optsearch
│                         - IO/系统：fs、path、args、process、intern、version、format、time、random、db
│                         - 网络/服务：net、http、http_server
│                         - 数据互联：tink（帧协议）/ zd v2 序列化
│                         - 哈希/密码：sha1/256/512/3、blake2/3、shake、md5、hmac、pbkdf2、hkdf、
│                           poly1305、ascon_mac、siphash、xxh3、ed25519、x25519、tsha1 家族
├── ext/                  扩展库（codec：brotli/lz4/jpeg/zstd；vecsearch；aes/chacha20/ascon_aead/
│                         scrypt/argon2/ecdsa；ml；log；pretty；tui；test；bench；config；registry；cache）
├── rdu/                  嵌入式基础层（无栈纪律：ascii/bits/crc/fixed/math/rdb/rnd/mac）
├── repl/repl.tie         REPL 外壳
├── tieDB/                tieDB（内存数据库（含 zd 持久化副本））
├── pkg/                  包管理器（tie 语言自写）
├── scripts/              构建与回归脚本（含 tie 自写打包器 package.tie）
├── tests/                探针与回归测试（probe_*/language/errors）
├── skills/tie-dev/       tie-dev AI 开发技能（随发行包分发）
├── docs/                 文档（中英双语）
└── examples/             示例程序
```

## CLI 用法
*EN: CLI usage*

主入口 `tie`（四段式调度器）与包管理器子命令的完整用法见 [docs/cli.md](docs/cli.md)：
主入口选项表、`tie init/add/install/publish` 等包管理命令、多文件并行编译、
库编译（静态库 `.a`/`.lib`）、`--compress-data`（td→zd）、子工具与 REPL 自举构建。

EN: The main entry `tie` (four-stage dispatcher) and package-manager subcommands are documented in [docs/cli.md](docs/cli.md): main-entry options, `tie init/add/install/publish` package commands, parallel multi-file builds, library builds (`.a`/`.lib`), `--compress-data` (td→zd), sub-tools, and REPL bootstrap.

## License

本仓库按 tie-lang 组织自创的宽松许可证 **TIE-LANG Open Source License v1.1** 授权发布（全文见 [LICENSE](LICENSE)）：你可自由使用、修改并分发本软件源码，包括用于商业产品，仅需保留版权声明并附本许可证；而用该语言开发的自有软件完全归你所有，不附带任何署名义务。

EN: This repository is released under the **TIE-LANG Open Source License v1.1** (full text in [LICENSE](LICENSE)): you may freely use, modify, and redistribute the source code, including in commercial products, provided you retain the copyright notice and a copy of the license; programs you write in the language are entirely your own, with no attribution obligation.