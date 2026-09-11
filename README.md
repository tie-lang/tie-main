# tie

<p align="center">
  <img src="assets/tie-logo-full.svg" alt="tie 语言 Logo / tie language logo" width="600">
</p>

**效率 · 性能 · 安全 · 通用** / *Efficiency · Performance · Safety · Universality*

## 文档目录
*EN: Documentation*

| 文档 / Doc | 内容 / Content |
| --- | --- |
| [README.md](README.md) | 本文件：工程入口（快速开始、CLI、结构、路线图）/ This file: entry point (quick start, CLI, structure, roadmap) |
| [docs/language.md](docs/language.md) | 语法规范：文件结构、类型系统、语句/控制流、函数、数据结构、语法速查表 / Language spec: file structure, type system, statements/control flow, functions, data structures, quick reference |
| [docs/cli.md](docs/cli.md) | CLI 用法：主入口选项、包管理器子命令、多文件并行编译、库编译、REPL 自举 / CLI usage: main entry options, package-manager commands, parallel multi-file builds, library builds, REPL bootstrap |
| [docs/tiec.md](docs/tiec.md) | tiec 自举编译器文档：架构、自举链、CLI、运行时依赖 / tiec self-hosted compiler: architecture, bootstrap chain, CLI, runtime deps |
| [docs/tie-script.md](docs/tie-script.md) | tie:script 模块协议：注册/调用机制、模块约定、协议文本格式 / tie:script module protocol: registration/call mechanism, module conventions, wire format |
| [docs/ai-guide.md](docs/ai-guide.md) | AI 教学指南：语言用法 + 负例 + 编译器架构 / AI teaching guide: usage + negative examples + compiler architecture |
| [docs/prompt-pack.md](docs/prompt-pack.md) | 可粘贴 Prompt 包：自包含简介，直接发给任何 AI / Copy-paste prompt pack: self-contained intro for any AI |
| [NEW.md](NEW.md) | 发行版新鲜事：本发行版的新功能与特色速览 / Release highlights: what's new in this release |
| [docs/plans/](docs/plans/) | 后续开发模块设计规划（PQC 后量子 / 硬件加速 / SLH-DSA；已随 2026.1 发布归档的历史文档移至 [tie-lang/old_docs](https://github.com/tie-lang/old_docs) `2026.1/` 目录）/ Upcoming development-module plans (PQC / hardware acceleration / SLH-DSA; docs archived with 2026.1 now live in [tie-lang/old_docs](https://github.com/tie-lang/old_docs) under `2026.1/`) |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录（按发布档）/ Changelog (grouped by release slot) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南：p.x.x.x 编号规范、CHANGELOG 规范、发布流程 / Contributing guide: p.x.x.x numbering, CHANGELOG rules, release flow |

## 快速开始
*EN: Quick start*

**路径 A：下载发行包（整套工具链）**
*Path A: download the release archive (full toolchain)*

从 [GitHub Releases](https://github.com/tie-lang/tie-main/releases) 下载 `tie-2026.2-win-x64.zip`
并解压（含自举 tiec、REPL、包管理器与捆绑 LLVM 精简工具链；发行目录布局见
[docs/release.md](docs/release.md) §4.3）：

```bash
# 解压后，用发行包内的编译器编译并运行示例（示例源码位于 src/ 下）
bin\tiec.exe src\examples\hello.tie
src\examples\hello.exe
```

EN: Download `tie-2026.2-win-x64.zip` from GitHub Releases, unzip, then compile
and run an example with the bundled self-hosted compiler (sources live under
`src/` in the release).

**路径 B：从源码构建整套工具链（0-Rust 自举）**
*Path B: build the whole toolchain from source (0-Rust self-hosted)*

```bash
# 编译并运行示例 / compile and run an example (tiec self-hosted compiler)
compiler\tiec.exe examples\hello.tie
examples\hello.exe

# 自举验证 + 回归门禁 / bootstrap verification + regression gate
scripts\regress-s21.ps1 compiler\tiec.exe

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

## 发行模型
*EN: Release model*

tie 以 **tie-main 聚合/发行仓** + **组件独立仓** 双轨发行（2026.2 起，详见
[docs/release.md](docs/release.md)）：

- **整套工具链聚合发行包**：`dist/tie-{版本}-win-x64.zip`（bin/ + docs/ + src/ + 包根文档）
  与源码包 `tie-{版本}-src.zip`；版本集约束在 `scripts/tie-versions.data.tie`，
  聚合校验 `scripts/agg-check.tie`。
- **组件独立发行**：各组件仓独立版本与 Release，附件命名
  `tie-<component>-<version>-<platform>-<arch>.zip`，产物出仓不进 git。

EN: tie ships on a dual track — the **tie-main aggregation/release repo** plus
**per-component repos** (from 2026.2; see [docs/release.md](docs/release.md)):
the full-toolchain aggregate archive `dist/tie-{version}-win-x64.zip` (+ the
`tie-{version}-src.zip` source archive; version-set in
`scripts/tie-versions.data.tie`, verified by `scripts/agg-check.tie`) and
per-component archives named
`tie-<component>-<version>-<platform>-<arch>.zip`, released from each component
repo (artifacts stay out of git).

## 工程结构
*EN: Repository structure*

tie-main 是**聚合/发行仓**：保留 `dist/` 发行产物、当前版本文档与仓库级文件；
源码目录处于**迁移中**（按 [docs/plans/2026-09-11-p721-repo-split.md](docs/plans/2026-09-11-p721-repo-split.md) 迁移清单
逐项迁往组件仓）。

```text
tie-main/              聚合/发行仓（aggregation/release repo）
├── dist/              发行产物（zip 出仓不进 git；发行包内源码收拢于 src/）
├── docs/              当前版本文档（language/ai-guide/release/cli/tiec/designs/plans…）
├── README.md  NEW.md  CHANGELOG.md  LICENSE  CONTRIBUTING.md  ROAD.md  AGENTS.md
├── assets/ .github/   宣传资源 / CI
├── scripts/           构建与测试脚本（自举打包 package.tie、聚合校验 agg-check.tie 等）
└── 源码（迁移中，见组件索引）：
    compiler/  std/  ext/  rdu/  repl/  pkg/  prep/  tieDB/
    examples/  skills/  editor/  sys/  tools/  tests/
```

## 组件索引
*EN: Component index*

| 组件 / Component | 职责 / Role | 独立仓 / Repo | 状态 / Status |
|---|---|---|---|
| 编译器 tiec | 自举编译器 + Keel 架构 + 标准/扩展/精简库 + REPL | `tie-lang/tiec` | 本仓内（迁移中）|
| 数据互联 tink | zd v2 帧协议 + 管道编排器（语言无关） | `tie-lang/tink` | 本仓内（std/tink 起步）|
| LSP 服务 tsp | language server（`tie --lsp`） | `tie-lang/tsp` | 本仓内（compiler/lsp）|
| 运行时 trm | 可选 JVM 式 VM（不捆绑编译器） | `tie-lang/trm` | 规划中（p.7.3）|
| UI 框架 tiu | 独立自研 UI（不依赖 trm） | `tie-lang/tiu` | 规划中（p.9.3）|
| 数据库 tiedb | 列式持久化 + 向量检索（zd 底座） | `tie-lang/tiedb` | 本仓内（tieDB/）|
| 安装器 tiwi | tie 自研安装程序制作器 | `tie-lang/tiwi` | 规划中（p.9.7）|
| 包管理器 pkg | 依赖解析 + tie.lock + registry 交互 | `tie-lang/tie-pkg` | 本仓内（pkg/）|
| 编辑器扩展 | VSCode 语法高亮 + LSP 诊断 | `tie-lang/vscode-tie` | 本仓内（editor/）|
| 开发技能 | tie-dev AI 开发技能 | `tie-lang/tie-dev` | 本仓内（skills/）|
| 历史归档 | 过时文档与历史版本 | `tie-lang/old_docs` | 已独立 |

EN: tie-main is the aggregation/release repository (dist artifacts + current
docs + repo-level files); the source directories above are mid-migration to the
per-component repos listed in the index (per the p.7.2.1 split plan).

## CLI 用法
*EN: CLI usage*

主入口 `tie`（四段式调度器）与包管理器子命令的完整用法见 [docs/cli.md](docs/cli.md)：
主入口选项表、`tie init/add/install/publish` 等包管理命令、多文件并行编译、
库编译（静态库 `.a`/`.lib`）、`--compress-data`（td→zd）、子工具与 REPL 自举构建。

EN: The main entry `tie` (four-stage dispatcher) and package-manager subcommands are documented in [docs/cli.md](docs/cli.md): main-entry options, `tie init/add/install/publish` package commands, parallel multi-file builds, library builds (`.a`/`.lib`), `--compress-data` (td→zd), sub-tools, and REPL bootstrap.

## License

本仓库按 **Tie Public License v2.0（TPL 2.0）** 授权发布（全文见 [LICENSE](LICENSE)）：你可自由使用、修改并分发本软件源码，包括用于商业产品，仅需保留版权声明并附本许可证；而用该语言开发的自有软件完全归你所有，不附带任何署名义务。

EN: This repository is released under the **Tie Public License v2.0 (TPL 2.0)** (full text in [LICENSE](LICENSE)): you may freely use, modify, and redistribute the source code, including in commercial products, provided you retain the copyright notice and a copy of the license; programs you write in the language are entirely your own, with no attribution obligation.