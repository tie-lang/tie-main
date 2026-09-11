# 正式发行版设计规划
*EN: Official Release Design Plan*

> 本文档定义 tie 语言**正式发行版（Release）**的版本规则、内部代号、
> 工具链合集组成、工程改造点与发布流程。
> 实施依据：README 路线图 Harbor M0（2026.1 正式发行版基础）、Shipyard 2026.2（完整形态）。

EN: This document defines the **official release** rules for the tie language: versioning, internal codenames, the toolchain-collection composition, engineering modifications, and the release process. Implementation basis: the Harbor M0 milestone (2026.1 official-release foundation) in the README roadmap, and Shipyard 2026.2 (full toolchain form).

## 1. 版本命名规则
*EN: Version Naming Rules*

正式发行版版本号格式：`年份.修订号`，例如 `2026.1`。

EN: The official-release version format is `year.revision`, e.g. `2026.1`.

- **年份**：发行年份（4 位数字），如 `2026`。
- **修订号**：该年内的发行序数，从 1 递增（`2026.1` → `2026.2` → …）。
- 版本号与 git tag 一致：`2026.1`（裸版本号，不带 `v` 前缀）。

EN: **Year**: the release year (4 digits), e.g. `2026`.
EN: **Revision**: the release ordinal within that year, incrementing from 1 (`2026.1` → `2026.2` → …).
EN: The version matches the git tag exactly: `2026.1` (a bare version without a `v` prefix).

### 1.1 两段式开发：预发布 → 正式版
*EN: Two-stage development: preview → stable*

每个正式发行版内采用「预发布 → 正式版」两段式开发：

EN: Each official release develops in two stages:

- **预发布段（preview.N）**：全部新功能在开发模块完成，开发号 **P.x.y.z**
  （CHANGELOG 中写作 `p.x.y.z`）；CHANGELOG 版本段标题
  `## Harbor-2026.1-preview.N（YYYY-MM-DD）`。
  EN: **preview stage (preview.N)**: all new features land in development modules,
  numbered **P.x.y.z** (`p.x.y.z` in the CHANGELOG); CHANGELOG heading
  `## Harbor-2026.1-preview.N（YYYY-MM-DD）`.
- **正式版段（2026.1）**：preview.N 发布后启动，**基于 preview.N** 开发——**不引入任何
  新功能**，只做优化与稳定性；开发号 **R.x.y.z**。正式版与预发布是**双轨**（两个独立
  轨道）：预发布轨 **P.x.y.z** 做新功能，正式版轨 **R.x.y.z** 只做优化与稳定性，两轨
  共用 x.y.z 格式但**各自独立编号、不互相延续**；CHANGELOG 版本段标题
  `## 2026.1（正式版，开发中）`。
  EN: **stable stage (2026.1)**: starts after preview.N ships, **based on preview.N**,
  introducing **no new features** — only optimization and stability; dev numbers
  **R.x.y.z**. The stable and preview are **dual-track** (two independent tracks): the
  preview track (**P.x.y.z**) does new features, the stable track (**R.x.y.z**) only does
  optimization/stability; both share the x.y.z format but **number independently and
  neither continues the other**; CHANGELOG heading `## 2026.1（stable, in development）`.
- 正式版发布即发行版（版本号 `年份.修订号`，git tag 裸版本号 `2026.1`）。
  EN: the stable release is the official release (version `year.revision`, bare git tag `2026.1`).

## 2. 内部代号（架构代号）
*EN: Internal Codenames (architecture codenames)*

每个正式发行版配一个内部代号，代表该版本的架构特征或主题。

EN: Each official release is assigned an internal codename that represents the architectural feature or theme of that version.

| 版本 | 内部代号 | 含义 |
| --- | --- | --- |
| 2026.1 | **Harbor 港湾** | 首个正式版 = 工具链第一次靠岸停泊，形成可交付的稳定形态 |
| 2026.2 | **Shipyard 造船厂** | 编译器彻底重构 = 进入 **Keel 龙骨架构**时代：核心只余机制层（注册表/审计器/加载器/执行骨架，零行为），一切行为皆为注册项；插件/包经 tieir 分发与审计链入港。工具链完整形态：**trm**（运行时）、**UI 框架**、**tiedb**（数据库/向量检索）与 **tiwi**（安装器）随船厂一体下水 |

EN: The table above lists each release version, its internal codename, and its meaning: 2026.1 is codenamed **Harbor 港湾**, where the first official release = the toolchain's first docking and berthing, forming a deliverable, stable shape.
EN: 2026.2 is codenamed **Shipyard 造船厂**, marking the complete compiler restructure into the **Keel 龙骨架构** era: the core retains only the mechanism layer (registry/auditor/loader/execution skeleton, zero behavior), and all behavior is a registration item; plugins/packages dock via tieir distribution and the audit chain. The toolchain reaches its full form — **trm** (runtime), **UI framework**, **tiedb** (database/vector search) and **tiwi** (installer builder) are launched together from the shipyard.

代号仅用于宣传/文档/产物命名（如安装包名），不进入版本号。

EN: The codename is used only for promotion, docs, and artifact naming (e.g. installer names); it does not enter the version number.

## 3. 工具链合集组成
*EN: Toolchain Collection Composition*

正式发行版是一套**工具链的合集**：把自举编译器、REPL 外壳、包管理器、
捆绑 LLVM 精简工具链、标准/扩展库与文档打包为一个可安装、可分发的整体。
2026.1 起整链 **0-Rust 自举**（Rust 参考编译器已归档 tiec_rust）。

EN: An official release is a **collection of a toolchain**: it packages the self-hosted compiler, the REPL shell, the package manager, a bundled minimal LLVM toolchain, the standard/extension libraries, and the documentation into a single installable, distributable whole. From 2026.1 the whole chain is **0-Rust self-hosted** (the Rust reference compiler is archived as tiec_rust).

### 3.1 二进制组件（bin/）
*EN: Binary components (bin/)*

| 组件 | 源 | 职责 |
| --- | --- | --- |
| `tiec.exe` | compiler/driver.tie | 自举编译器（tie 语言自写，前端→tie-IR→LLVM 后端工具链驱动） |
| `repl.exe` | repl/repl.tie | REPL 外壳（tie 自写解释器求值，自举产物） |
| `pkg.exe` | pkg/ | 包管理器（依赖解析 + tie.lock，自举产物） |
| `bin/llvm/` | D:\LLVM 捆绑精简 | clang / opt / llvm-ar / lld-link + 头文件，`TIE_LLVM_HOME` 开箱即用，用户无需另装 LLVM |

EN: The table above lists each binary component and its source/role: `tiec.exe` (from compiler/driver.tie) is the self-hosted compiler written in tie (frontend → tie-IR → LLVM-backend toolchain driver); `repl.exe` (repl/repl.tie) is the REPL shell backed by the tie-written interpreter; `pkg.exe` (pkg/) is the package manager (dependency resolution + tie.lock); `bin/llvm/` is the bundled minimal LLVM toolchain (clang/opt/llvm-ar/lld-link + headers) so users need no separate LLVM install.

### 3.2 库与源码包
*EN: Libraries and source packages*

- 包根：`README.md`、`NEW.md`、`CHANGELOG.md`、`LICENSE`（发行文档 + 许可证置于包根）
- `docs/`：文档全目录（language/ai-guide/prompt-pack/release 等）
- `examples/`：示例 `.tie` 源码（hello / wide / table / tuple / oop / m4_ops 等）
- `std/` `ext/` `rdu/`：标准库、扩展库与嵌入式基础层（全部 tie 语言自写；rdu 无栈纪律，零原语/零动态内存）
- `skills/`：tie-dev 开发技能（SKILL.md，面向开发者与 AI 助手）
- `editor/vscode-tie/`：VSCode 扩展（语法高亮 + LSP 诊断）
- `compiler/`：编译器全部 `.tie` 源码（已剪除 `.exe/.ll/.bc` 编译产物，便于检视与二次开发）

EN: The repo root of the package carries `README.md`, `NEW.md`, `CHANGELOG.md` and `LICENSE` (release docs + license at the package root); `docs/` ships the full documentation tree (language/ai-guide/prompt-pack/release, etc.); `examples/` ships example `.tie` sources; `std/`, `ext/` and `rdu/` are the standard library, extension library and embedded base layer (all written in tie; rdu follows stack-discipline with zero primitives/zero dynamic memory); `skills/` ships the tie-dev development skill; `editor/vscode-tie/` ships the VSCode extension (syntax highlighting + LSP diagnostics); `compiler/` ships all compiler `.tie` sources with build artifacts pruned.

> 2026.2 变化：发行目录下设 `src/`，**将上述全部源码（compiler/std/ext/rdu/examples/skills/editor）收拢到 `src/` 下**；发行时另附一个**只带 `src/` 目录的源码包**（`tie-{版本}-src.zip`）。
> EN (2026.2): a `src/` directory is added under the release layout; **all of the above sources (compiler/std/ext/rdu/examples/skills/editor) are gathered under `src/`**, and a **source-only archive containing just `src/`** (`tie-{version}-src.zip`) is shipped alongside.

### 3.3 2026.2 完整形态（Shipyard）
*EN: Full form in 2026.2 (Shipyard)*

2026.2 除 Keel 架构重构后的编译器外，工具链补齐下列组件，随发行版一体交付：

- **trm**（运行时）：动态库延迟绑定 + system 域（terminal/process/fs/env/session/clock/net/data）
- **UI 框架**：tiu 独立自研 UI（窗口/绘制/事件 + 组件树/布局组合式框架；不依赖 trm，可与 trm 同用）
- **tiedb**（数据库）：tieDB 完整形态（列式持久化 + 向量检索 vecsearch，zd 格式底座）
- **tiwi**（安装器）：tie 安装程序制作器（**完全 tie 自研重构**——GUI 用 tiu、逻辑全 tie 语言、自解压 setup，六边形架构）

EN: In 2026.2, in addition to the Keel-restructured compiler, the toolchain is completed with: **trm** (runtime: dynamic-library lazy binding + the system domain terminal/process/fs/env/session/clock/net/data); the **UI framework** **tiu**, an independent in-house UI (window/drawing/events + composable component tree/layout; not depending on trm, usable together with trm); **tiedb** (the database in full form: columnar persistence + vecsearch over the zd format); and **tiwi** (the tie installer builder, fully rebuilt with tie's own stack — GUI via tiu, logic entirely in tie, self-extracting setup, hexagonal architecture).

### 3.4 仓库组织与发行版位置（2026.2 多仓拆分）
*EN: Repository organization and release-artifact location (multi-repo split in 2026.2)*

2026.2 起 tie-lang org 下按组件拆为独立仓库（清单与迁移清单见
`docs/plans/2026-09-11-p721-repo-split.md`）：

- **tie-main**：聚合/发行仓——保留 `dist/` 发行产物与**当前版本文档** + 仓库级文件
  （README / CHANGELOG / LICENSE / NEW / CONTRIBUTING / ROAD 等）；其余内容按
  迁移清单移往组件仓
- **组件仓库**：各组件（编译器 tiec、数据互联 tink、LSP 服务 tsp、运行时 trm、
  UI 框架 tiu、数据库 tiedb、安装器 tiwi、包管理器 pkg、编辑器扩展 vscode-tie、
  tie-dev 技能等）各自独立仓，独立演进与发布

组件仓库清单（2026-09-11 定稿）：

| 组件 / Component | 独立仓建议名 / Suggested repo | 职责边界 / Responsibility |
|---|---|---|
| 编译器（源码 + driver + keel + std/ext/rdu + repl + scripts） | `tie-lang/tiec` | 自举编译器全源码、Keel 架构、语言标准/扩展/精简库、REPL、构建回归脚本；发行 `tiec` 组件 |
| 数据互联 tink | `tie-lang/tink` | 通用数据流互联服务（语言无关）：zd v2 帧协议、模块.函数(字节进→字节出) ABI、管道编排器 `tink pipe` |
| LSP 服务器 tsp | `tie-lang/tsp` | language server（`tie --lsp`），编辑扩展的后端 |
| 运行时 trm | `tie-lang/trm` | JVM 式可选 VM（字节码 + 运行时 VM + 引擎级 GC），可插拔后端，不捆绑编译器 |
| UI 框架 tiu | `tie-lang/tiu` | 独立自研 UI（窗口/绘制/事件 + 组件树/布局），高性能跨平台、不依赖 trm |
| 数据库 tiedb | `tie-lang/tiedb` | tieDB 完整形态（列式持久化 + 向量检索 vecsearch，zd 底座） |
| 安装器 tiwi | `tie-lang/tiwi` | tie 安装程序制作器（完全 tie 自研：GUI 用 tiu、逻辑全 tie、自解压 setup） |
| 包管理器 pkg | `tie-lang/tie-pkg`（或并入 tink/聚合工具） | 依赖解析 + tie.lock + registry 交互（p.9.2.2 正式落地） |
| 编辑器扩展 | `tie-lang/vscode-tie` | VSCode 扩展（语法高亮 + LSP 诊断） |
| 开发技能 | `tie-lang/tie-dev` | tie-dev AI 开发技能（SKILL.md） |
| 历史文档归档 | `tie-lang/old_docs` | 过时文档与历史版本归档（已存在） |
| 示例与分发 | 随 `tiec` 仓 | `examples/` 示例源码随源码仓与发行包分发 |

> EN: From 2026.2 the tie-lang org splits into per-component repositories. The
> inventory above (finalized 2026-09-11, detail in the p.7.2.1 planning doc) maps
> each component to its suggested repository and responsibility boundary:
> **tiec** (compiler sources + keel + std/ext/rdu + repl + build scripts), **tink**
> (language-agnostic data-flow interop: zd v2 framing, module.function(byte-in→byte-out), `tink pipe`),
> **tsp** (LSP server), **trm** (optional JVM-style VM, never bundled), **tiu**
> (independent UI framework), **tiedb** (database/vecsearch), **tiwi** (installer),
> **tie-pkg** (package manager), **vscode-tie** (editor extension), **tie-dev**
> (AI development skill), **old_docs** (archives).

发行物：

- `dist/` 仍为发行产物目录（package.tie 产出），但**发行物出仓**——zip 等产物不再进 git 跟踪，经 GitHub / GitCode Release 附件分发
- tie-main 保留当前版本的发行物与文档；历史版本由 Release 历史承担
- 过渡期（迁移未完成前）：tie-main 仍物理保留组件源码目录，随迁移清单逐项搬出；
  期间 README/ROAD 保持「聚合/发行仓定位 + 组件索引」以对齐目标态

EN: Release artifacts: `dist/` remains the artifact directory (produced by
package.tie), but artifacts **leave the git tree** — zips are distributed as
GitHub/GitCode Release assets instead of being tracked. tie-main keeps the
current release artifacts and docs; historical versions are carried by the
Release history. During the transition, tie-main still physically holds the
component source directories while README/ROAD already reflect the target
aggregation-repo positioning.

### 3.5 组件独立发行（2026.2）
*EN: Component-independent releases (2026.2)*

组件仓独立演进与发布，遵循统一机制：

**版本号策略**：组件与主仓共享双轨——开发号 `p.x.y.z` / `r.x.y.z`，正式号
`年份.修订号`（如 `1.2.3` 组件内版本号 × `2026.2` 聚合版本号；组件内部维护
自己的 semver 或年份.修订号，随组件的发布节奏独立推进）。组件可各自发
preview：`tie-<component>-<版本>-preview.N` 标识预览段。

**发行物出仓**：zip 等产物**不进 git**，经 GitHub / GitCode Release 附件分发；
仓库内只保留打包入口（脚本）与产物清单（指纹）。

**artifact 命名约定**：

```
tie-<component>-<version>-<platform>-<arch>.zip
    组件名      版本        win-x64 等
```

**组件发行清单模板**（每组件仓一份，随组件 Release 附上；release-notes 双语，
无内部回归内容、无内部版本号）：

```markdown
# tie-<component> <version>  发行说明 / Release Notes

## 本版变化 / Changes
* 列出新增（EN 对应描述 / Feature + EN line）
* 修复 / Fixes

## 安装 / Install
* 解压 zip 并将 bin/ 加入 PATH；TIE_LLVM_HOME 指向捆绑 LLVM（如需要）

## 校验 / Verify
* 解压后运行 bin/ 下组件可执行并检查版本输出
* 指纹清单 .zd.fp（如分发 zd 数据）用 tiepkg/keelaud 校验
```

**打包脚本约定**（scripts/package.tie 单组件打包评估，2026-09-11 结论）：
主仓 `scripts/package.tie` 为**整套工具链聚合打包器**（自举验证 + 全组件组装 +
zip，p.7.2.4 起增设 `src/` 收拢与 `-src.zip`）。为其增加「单组件打包」子模式
成本评估：打包器目前以**仓库整树路径**为源（compiler/repl/pkg/std/ext/rdu 等
按固定根路径复制）；组件分离后各组件源码位于**独立仓**，聚合打包器需改为
「按 `tie-versions` 约束拉取各组件产物 + 校验指纹」的聚合流程（p.7.2.3），
单组件打包职责转交**组件仓自身**打包入口（组件仓维护自己的 package 脚本 /
CI 步骤，产物命名遵循上表）。据此，`scripts/package.tie` 本轮**不新增单组件
模式**——组件打包约定按本文档施行，聚合改造随 p.7.2.3 落地。

EN: Component repositories evolve and release independently under one scheme:
**versioning** follows the dual track (dev numbers p.x.y.z / r.x.y.z; official
year.revision) — components may ship their own previews
(`tie-<component>-<version>-preview.N`); **artifacts leave the git tree** and
are distributed as release assets; **artifact naming**
`tie-<component>-<version>-<platform>-<arch>.zip`; a release-notes template and
verify steps are shipped with each component release. On the packager: the
repo-level `scripts/package.tie` stays the **full-toolchain aggregate packager**
(no single-component mode this round) — after the repo split, single-component
packaging moves into each component repo's own build/release entry, and the
aggregate packager is reworked along p.7.2.3 to consume per-component artifacts
plus fingerprints instead of repo tree paths.

## 4. 工程改造点
*EN: Engineering Modifications*

### 4.1 自举验证与二阶自举
*EN: Bootstrap verification and second-order bootstrap*

- 一阶：`tiec.exe compiler/driver.tie -o compiler/tiec2.exe`（自举编译零错误，产物生成判定成功）
- 二阶：新 tiec 再编自身，产出与一阶 byte-identical（自举不动点）
- 种子边界：编译用户程序、链接运行时、REPL 运行、解释器求值全部不触碰 Rust 产物
  （scripts/zero-rust-check.ps1 验证）

EN: First order: `tiec.exe compiler/driver.tie -o compiler/tiec2.exe` (bootstrap compile with zero errors, success judged by artifact generation). Second order: the new tiec compiles itself again, byte-identical to the first order (bootstrap fixed point). Seed boundary: compiling user programs, linking the runtime, running the REPL and interpreter evaluation never touch Rust artifacts (verified by scripts/zero-rust-check.ps1).

### 4.2 版本与代号
*EN: Version and codename*

- 发行版号与代号由打包参数注入、产物按 `tie-{版本}-win-x64.zip` 命名
  （如 `tie-Harbor-2026.1-preview.6-win-x64.zip`、`tie-2026.1-win-x64.zip`）
- `tiec --version` 输出版本与代号为后续增强项（当前 CLI 见 compiler/README.tie）

EN: The release version and codename are injected as packager arguments; artifacts are named `tie-{version}-win-x64.zip` (e.g. `tie-Harbor-2026.1-preview.6-win-x64.zip`, `tie-2026.1-win-x64.zip`). A `tiec --version` output of version+codename is a future enhancement (current CLI is documented in compiler/README.tie).

### 4.3 打包器
*EN: Packager*

`scripts/package.tie`（tie 语言自写，0-PowerShell，与旧 package.ps1 一一对应）：
1. 自举验证（tiec 编译 driver.tie → tiec2.exe）
2. repl.exe 自举（`skip-repl` 可跳过）
3. 组装 `dist/tie-{版本}/`（bin / bin/llvm / docs / examples / std·ext·rdu / skills / editor / compiler 源码 + 包根发行文档）
4. 打包 zip（Windows 自带 bsdtar：`tar -a -c -f`）

用法（tiec 不支持在源码后直传脚本参数，须先编译再运行）：
`compiler/tiec.exe scripts/package.tie -o dist/package.exe` 编译打包器，
再 `dist/package.exe 2026.2` 运行（`skip-repl` / `skip-llvm` 可选）。

> 2026.2 变化：组装时把源码（compiler/std/ext/rdu/examples/skills/editor）收拢到
> `dist/tie-{版本}/src/`，除全量包外另打 `tie-{版本}-src.zip`（只含 `src/`）。
> EN (2026.2): sources are gathered under `dist/tie-{version}/src/`, and a `tie-{version}-src.zip` containing only `src/` is produced in addition to the full archive.

EN: `scripts/package.tie` is the packager written in tie (0-PowerShell, one-to-one with the old package.ps1): 1. bootstrap verification (tiec compiles driver.tie → tiec2.exe); 2. repl.exe self-host build (`skip-repl` to skip); 3. assemble `dist/tie-{version}/` (bin / bin/llvm / docs / examples / std·ext·rdu / skills / editor / compiler sources + release docs at the package root); 4. zip via the Windows-bundled bsdtar (`tar -a -c -f`). compile the packager with `compiler/tiec.exe scripts/package.tie -o dist/package.exe`,
then run `dist/package.exe 2026.2` (optional `skip-repl` / `skip-llvm`).

### 4.4 README 路线图
*EN: README roadmap*

Harbor M0 里程碑 = 2026.1 正式发行版基础；Shipyard = 2026.2 完整形态（Keel 架构 + trm/UI/tiedb/tiwi）。

EN: The Harbor M0 milestone = the 2026.1 official-release foundation; Shipyard = the 2026.2 full form (Keel architecture + trm/UI/tiedb/tiwi).

### 4.5 主仓聚合发行（2026.2）
*EN: Aggregated release of the whole toolchain (2026.2)*

主仓 as 聚合/发行仓，发行「整套工具链聚合发行包」：

- **版本集编排**：`scripts/tie-versions.data.tie`（td 数据表，组件=版本约束，
  `compiler="1.2.3", tink="0.9.1", ...`）；聚合发行前按各组件实测版本更新。
- **聚合校验**：`scripts/agg-check.tie`（tie 语言自写，0-PowerShell）——
  校验各组件版本满足约束（td 清单逐项）、产物齐全（`dist/tie-{组件}-{版本}-win-x64.zip`）、
  指纹一致（产物旁 `.fp` 清单 tsha1f 比对，复用 std/tsha1）；`--self-test`
  内置自检断言「良性通过/篡改拦截/缺失检出」。
- **聚合发行目录布局**（`dist/tie-2026.2/`）：

```
dist/tie-2026.2/         聚合发行根
├── bin/                各组件可执行（tiec/repl/pkg/… + bin/llvm/ 捆绑精简 LLVM）
├── docs/               当前版本文档
├── examples/           示例源码
├── src/                全部源码（compiler/std/ext/rdu/examples/skills/editor，p.7.2.4 收拢）
├── README.md  NEW.md  CHANGELOG.md  LICENSE      包根发行文档 + 许可证
└── registry/           包注册中心（p.7.2.5 接口预留；聚合编排元数据落位处）
```

- **身份约束**：聚合包内组件按 `tie-versions` 约束互恰；校验不通过不得出包。
- **registry 对接**（p.7.2.5）：聚合发行元数据（组件=版本=指纹）可发布到 registry，
  `tie pkg publish/info/versions` 供客户端查询——本 §4.5 只预留接口，落地见 §4.6。

EN: The main repo ships a **full-toolchain aggregate release**: the version-set
orchestration lives in `scripts/tie-versions.data.tie` (td table of
component=version constraints); `scripts/agg-check.tie` (tie-written, 0-PowerShell)
verifies every listed component version satisfies the constraint, its artifact
`dist/tie-{component}-{version}-win-x64.zip` exists, and its fingerprint matches
the paired `.fp` manifest (tsha1f); a `--self-test` mode asserts the
benign/tamper/missing scenarios. The aggregate directory layout
`dist/tie-2026.2/` = bin (binaries + bundled LLVM) / docs / examples / src
(gathered sources, p.7.2.4) / package-root release docs / a `registry/` slot
(pre-reserved for p.7.2.5 metadata publication).

### 4.6 包注册中心 registry（2026.2，p.7.2.5 起步）
*EN: Package registry (2026.2, p.7.2.5 bootstrap)*

面向独立发行与聚合发行的存储端骨架（服务端不做，文件系统目录即最小存储端）：

- **registry 包格式**：复用 zdpub/keelaud 既有产物——发布单元 = `.zd`（zd v2 压缩）
  + `.zd.fp`（tsha1f 单文件指纹清单）+ 清单元数据（info.td，name/version/desc/
  fingerprint 等）。
- **客户端三操作**（新模块 `compiler/keel/keel_registry_cli.tie`，namespace
  `keelpkg`）：`publish <name> <version> <src.td>`（压缩 .zd + 指纹 + 元数据 +
  版本索引）、`info <name>`（查询元数据）、`versions <name>`（列出版本）。
- **存储布局**（默认注册根 `./.tie-registry`，可经 `--registry` 覆盖）：

```
.tie-registry/
└── <pkg>/
    ├── index.td           版本索引（td 表：版本串列表）
    └── <version>/
        ├── pkg.zd         发布单元（zd v2）
        ├── pkg.zd.fp      单文件指纹（tsha1f:<值>）
        └── info.td        元数据（name/version/desc/fingerprint）
```

- **CLI 整合**：`tie pkg publish|info|versions` 经 keel_cli 注册表分派（p.7.1.6
  机制），driver 侧 `keelcli_handle` 路由 pkg 子命令；真实三操作由 keelpkg 模块
  提供（探针验证），服务端/协议其余部分随 p.9.2.2 包管理器正式落地。
- **格式/协议文档**：存储在 `docs/designs/`（registry 条目，随 p.7.2.5 提交）。

EN: The registry bootstrap (p.7.2.5) provides a storage skeleton for independent
and aggregate releases: the package format reuses existing zdpub/keelaud
artifacts (`.zd` + `.zd.fp` fingerprint + metadata manifest `info.td`); a
minimal client (`compiler/keel/keel_registry_cli.tie`, namespace `keelpkg`)
implements publish / info / versions over a filesystem-directory registry
(root `.tie-registry` by default, overridable); `tie pkg publish|info|versions`
dispatch through the keel_cli registry; the server side is out of scope this
round (formalized with the package manager in p.9.2.2).

## 5. 发布流程
*EN: Release Process*

适配自 publish-release 技能（dotnet/Rust 版已随 0-Rust 迁移退役）：

EN: Adapted from the publish-release skill (the dotnet/Rust variant retired with the 0-Rust migration):

1. 推断版本号（年份.修订号，向用户确认）
2. 更新 CHANGELOG.md（按 CHANGELOG 写入规则，随提交即时记录）
3. 同步文档（README、language.md、ai-guide、release.md 代号表等）
4. `compiler/tiec.exe scripts/package.tie -- {版本}` 自举验证 + 打包生成 zip
5. 提交并推送 GitHub（`tie-main` remote = github；内部远端 git.franj2.top 已弃用，不再推送）
6. 打 git tag（裸版本号 `2026.1`）
7. 创建双平台 Release（GitHub / GitCode），上传压缩包（安装包自 2026.2 tiwi 起）

EN: 1. Infer the version number (year.revision, confirm with the user); 2. update CHANGELOG.md (per changelog-writing rules, recorded immediately with each commit); 3. sync the docs (README, language.md, ai-guide, the release.md codename table, etc.); 4. run `compiler/tiec.exe scripts/package.tie -- {version}` for bootstrap verification + zip packaging; 5. commit and push to GitHub (tie-main remote = github; the internal remote git.franj2.top is deprecated and never pushed anymore); 6. create the git tag (bare version `2026.1`); 7. create the dual-platform Release (GitHub / GitCode) and upload the archives (installers arrive with tiwi in 2026.2).

## 6. 既定决策
*EN: Established Decisions*

- 打包产物：**仅 zip 压缩包**（`tie-{版本}-win-x64.zip`）；安装器自 2026.2（tiwi）引入
- 编辑器扩展：**包含** `editor/vscode-tie`（随发行版分发）
- 目标平台：**仅 win-x64**（本机可验证；跨平台后续版本）
- LLVM：**捆绑精简工具链**（bin/llvm/，无需用户另装）
- 打包器：**tie 语言自写**（scripts/package.tie，0-PowerShell）
- 组件发行（2026.2）：组件仓独立打包/发布，artifact 命名 `tie-<component>-<version>-<platform>-<arch>.zip`，发行物出仓、进 Release 附件
- 仓库组织：**多仓拆分**——tie-main 聚合/发行仓（发行物 + 当前版本文档），其余组件独立仓
- 发行物：**出仓**——zip 经 GitHub / GitCode Release 附件分发，不进 git 跟踪
- 源码包（2026.2）：发行目录设 `src/` 收拢全部源码，另出只含 `src/` 的 `tie-{版本}-src.zip`

EN: Packaging artifacts: **zip archives only** (`tie-{version}-win-x64.zip`); installers arrive with tiwi in 2026.2. Editor extension: **included** — `editor/vscode-tie` (distributed with the release). Target platform: **win-x64 only** (verifiable on this machine; cross-platform comes in a later version). LLVM: **bundled as a minimal toolchain** (bin/llvm/, no separate install needed). Packager: **written in tie** (scripts/package.tie, 0-PowerShell). Repo organization: **multi-repo split** — tie-main is the aggregation/release repository (artifacts + current-version docs), other components live in their own repositories. Release artifacts: **leave the git tree** — zips are distributed as GitHub/GitCode Release assets.