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

- `doc/`：README、CHANGELOG、LICENSE + `docs/` 文档全目录（language/ai-guide/prompt-pack/release 等）
- `examples/`：示例 `.tie` 源码（hello / wide / table / tuple / oop / m4_ops 等）
- `std/` `ext/` `rdu/`：标准库、扩展库与嵌入式基础层（全部 tie 语言自写；rdu 无栈纪律，零原语/零动态内存）
- `skills/`：tie-dev 开发技能（SKILL.md，面向开发者与 AI 助手）
- `editor/vscode-tie/`：VSCode 扩展（语法高亮 + LSP 诊断）
- `compiler/`：编译器全部 `.tie` 源码（已剪除 `.exe/.ll/.bc` 编译产物，便于检视与二次开发）

EN: `doc/` ships README, CHANGELOG, LICENSE plus the full `docs/` tree (language/ai-guide/prompt-pack/release, etc.); `examples/` ships example `.tie` sources; `std/`, `ext/` and `rdu/` are the standard library, extension library and embedded base layer (all written in tie; rdu follows stack-discipline with zero primitives/zero dynamic memory); `skills/` ships the tie-dev development skill; `editor/vscode-tie/` ships the VSCode extension (syntax highlighting + LSP diagnostics); `compiler/` ships all compiler `.tie` sources with build artifacts pruned.

> 2026.2 变化：发行目录下设 `src/`，**将上述全部源码（compiler/std/ext/rdu/examples/skills/editor）收拢到 `src/` 下**；发行时另附一个**只带 `src/` 目录的源码包**（`tie-{版本}-src.zip`）。
> EN (2026.2): a `src/` directory is added under the release layout; **all of the above sources (compiler/std/ext/rdu/examples/skills/editor) are gathered under `src/`**, and a **source-only archive containing just `src/`** (`tie-{version}-src.zip`) is shipped alongside.

### 3.3 2026.2 完整形态（Shipyard）
*EN: Full form in 2026.2 (Shipyard)*

2026.2 除 Keel 架构重构后的编译器外，工具链补齐下列组件，随发行版一体交付：

- **trm**（运行时）：动态库延迟绑定 + system 域（terminal/process/fs/env/session/clock/net/data）
- **UI 框架**：trm.ui 窗口/绘制/事件基础 + tieui 组件树/布局组合式框架
- **tiedb**（数据库）：tieDB 完整形态（列式持久化 + 向量检索 vecsearch，zd 格式底座）
- **tiwi**（安装器）：tie 安装程序制作器（FLTK GUI + 自解压 setup，六边形架构）

EN: In 2026.2, in addition to the Keel-restructured compiler, the toolchain is completed with: **trm** (runtime: dynamic-library lazy binding + the system domain terminal/process/fs/env/session/clock/net/data); the **UI framework** (trm.ui window/drawing/events + the tieui composable component tree/layout); **tiedb** (the database in full form: columnar persistence + vecsearch over the zd format); and **tiwi** (the tie installer builder: FLTK GUI + self-extracting setup, hexagonal architecture).

### 3.4 仓库组织与发行版位置（2026.2 多仓拆分）
*EN: Repository organization and release-artifact location (multi-repo split in 2026.2)*

2026.2 起 tie-lang org 下按组件拆为独立仓库：

- **tie-main**：聚合/发行仓——保留 `dist/` 发行产物与**当前版本文档**；其余内容全部搬出
- **组件仓库**：各组件（编译器 tiec、运行时 trm/UI、tiedb、tiwi 等）各自独立仓，独立演进与发布

发行物：

- `dist/` 仍为发行产物目录（package.tie 产出），但**发行物出仓**——zip 等产物不再进 git 跟踪，经 GitHub / GitCode Release 附件分发
- tie-main 保留当前版本的发行物与文档；历史版本由 Release 历史承担

EN: From 2026.2 the tie-lang org splits into per-component repositories:
- **tie-main** is the aggregation/release repository: it keeps the `dist/` release artifacts and the **current-version documentation**; everything else moves out.
- **Component repositories**: each component (compiler tiec, runtime trm/UI, tiedb, tiwi, …) lives in its own repository, evolving and releasing independently.

Release artifacts:
- `dist/` remains the artifact directory (produced by package.tie), but artifacts **leave the git tree** — zips are distributed as GitHub/GitCode Release assets instead of being tracked.
- tie-main keeps the current release artifacts and docs; historical versions are carried by the Release history.

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
  （如 `tie-Harbor-2026.1-preview.5-win-x64.zip`、`tie-2026.1-win-x64.zip`）
- `tiec --version` 输出版本与代号为后续增强项（当前 CLI 见 compiler/README.tie）

EN: The release version and codename are injected as packager arguments; artifacts are named `tie-{version}-win-x64.zip` (e.g. `tie-Harbor-2026.1-preview.5-win-x64.zip`, `tie-2026.1-win-x64.zip`). A `tiec --version` output of version+codename is a future enhancement (current CLI is documented in compiler/README.tie).

### 4.3 打包器
*EN: Packager*

`scripts/package.tie`（tie 语言自写，0-PowerShell，与旧 package.ps1 一一对应）：
1. 自举验证（tiec 编译 driver.tie → tiec2.exe）
2. repl.exe 自举（`skip-repl` 可跳过）
3. 组装 `dist/tie-{版本}/`（bin / bin/llvm / doc / examples / std·ext·rdu / skills / editor / compiler 源码）
4. 打包 zip（Windows 自带 bsdtar：`tar -a -c -f`）

用法：`compiler/tiec.exe scripts/package.tie -- 2026.2`（`skip-repl` / `skip-llvm` 可选）。

> 2026.2 变化：组装时把源码（compiler/std/ext/rdu/examples/skills/editor）收拢到
> `dist/tie-{版本}/src/`，除全量包外另打 `tie-{版本}-src.zip`（只含 `src/`）。
> EN (2026.2): sources are gathered under `dist/tie-{version}/src/`, and a `tie-{version}-src.zip` containing only `src/` is produced in addition to the full archive.

EN: `scripts/package.tie` is the packager written in tie (0-PowerShell, one-to-one with the old package.ps1): 1. bootstrap verification (tiec compiles driver.tie → tiec2.exe); 2. repl.exe self-host build (`skip-repl` to skip); 3. assemble `dist/tie-{version}/` (bin / bin/llvm / doc / examples / std·ext·rdu / skills / editor / compiler sources); 4. zip via the Windows-bundled bsdtar (`tar -a -c -f`). Usage: `compiler/tiec.exe scripts/package.tie -- 2026.2` (optional `skip-repl` / `skip-llvm`).

### 4.4 README 路线图
*EN: README roadmap*

Harbor M0 里程碑 = 2026.1 正式发行版基础；Shipyard = 2026.2 完整形态（Keel 架构 + trm/UI/tiedb/tiwi）。

EN: The Harbor M0 milestone = the 2026.1 official-release foundation; Shipyard = the 2026.2 full form (Keel architecture + trm/UI/tiedb/tiwi).

## 5. 发布流程
*EN: Release Process*

适配自 publish-release 技能（dotnet/Rust 版已随 0-Rust 迁移退役）：

EN: Adapted from the publish-release skill (the dotnet/Rust variant retired with the 0-Rust migration):

1. 推断版本号（年份.修订号，向用户确认）
2. 更新 CHANGELOG.md（按 CHANGELOG 写入规则，随提交即时记录）
3. 同步文档（README、language.md、ai-guide、release.md 代号表等）
4. `compiler/tiec.exe scripts/package.tie -- {版本}` 自举验证 + 打包生成 zip
5. 提交并推送双端（git.franj2.top + GitHub）
6. 打 git tag（裸版本号 `2026.1`）
7. 创建双平台 Release（GitHub / GitCode），上传压缩包（安装包自 2026.2 tiwi 起）

EN: 1. Infer the version number (year.revision, confirm with the user); 2. update CHANGELOG.md (per changelog-writing rules, recorded immediately with each commit); 3. sync the docs (README, language.md, ai-guide, the release.md codename table, etc.); 4. run `compiler/tiec.exe scripts/package.tie -- {version}` for bootstrap verification + zip packaging; 5. commit and push to both remotes (git.franj2.top + GitHub); 6. create the git tag (bare version `2026.1`); 7. create the dual-platform Release (GitHub / GitCode) and upload the archives (installers arrive with tiwi in 2026.2).

## 6. 既定决策
*EN: Established Decisions*

- 打包产物：**仅 zip 压缩包**（`tie-{版本}-win-x64.zip`）；安装器自 2026.2（tiwi）引入
- 编辑器扩展：**包含** `editor/vscode-tie`（随发行版分发）
- 目标平台：**仅 win-x64**（本机可验证；跨平台后续版本）
- LLVM：**捆绑精简工具链**（bin/llvm/，无需用户另装）
- 打包器：**tie 语言自写**（scripts/package.tie，0-PowerShell）
- 仓库组织：**多仓拆分**——tie-main 聚合/发行仓（发行物 + 当前版本文档），其余组件独立仓
- 发行物：**出仓**——zip 经 GitHub / GitCode Release 附件分发，不进 git 跟踪
- 源码包（2026.2）：发行目录设 `src/` 收拢全部源码，另出只含 `src/` 的 `tie-{版本}-src.zip`

EN: Packaging artifacts: **zip archives only** (`tie-{version}-win-x64.zip`); installers arrive with tiwi in 2026.2. Editor extension: **included** — `editor/vscode-tie` (distributed with the release). Target platform: **win-x64 only** (verifiable on this machine; cross-platform comes in a later version). LLVM: **bundled as a minimal toolchain** (bin/llvm/, no separate install needed). Packager: **written in tie** (scripts/package.tie, 0-PowerShell). Repo organization: **multi-repo split** — tie-main is the aggregation/release repository (artifacts + current-version docs), other components live in their own repositories. Release artifacts: **leave the git tree** — zips are distributed as GitHub/GitCode Release assets.