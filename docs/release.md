# 正式发行版设计规划
*EN: Official Release Design Plan*

> 本文档定义 tie 语言**正式发行版（Release）**的版本规则、内部代号、
> 工具链合集组成、工程改造点与发布流程。
> 实施依据：README 路线图 Harbor M0（正式发行版基础）。

EN: This document defines the **official release** rules for the tie language: versioning, internal codenames, the toolchain-collection composition, engineering modifications, and the release process. Implementation basis: the Harbor M0 milestone (official-release foundation) in the README roadmap.

## 1. 版本命名规则
*EN: Version Naming Rules*

正式发行版版本号格式：`年份.修订号`，例如 `2026.1`。

EN: The official-release version format is `year.revision`, e.g. `2026.1`.

- **年份**：发行年份（4 位数字），如 `2026`。
- **修订号**：该年内的发行序数，从 1 递增（`2026.1` → `2026.2` → …）。
- 版本号与 git tag 一致：`2026.1`（裸版本号，不带 `v` 前缀）。
- Cargo crate 版本号与发行版号**保持一致**：
  `2026.1` 本身是合法 semver（主版本 2026，次版本 1），可直接用于 Cargo。

EN: **Year**: the release year (4 digits), e.g. `2026`.
EN: **Revision**: the release ordinal within that year, incrementing from 1 (`2026.1` → `2026.2` → …).
EN: The version matches the git tag exactly: `2026.1` (a bare version without a `v` prefix).
EN: The Cargo crate version **stays identical** to the release version: `2026.1` is itself valid semver (major 2026, minor 1), so it can be used directly in Cargo.

## 2. 内部代号（架构代号）
*EN: Internal Codenames (architecture codenames)*

每个正式发行版配一个内部代号，代表该版本的架构特征或主题。

EN: Each official release is assigned an internal codename that represents the architectural feature or theme of that version.

| 版本 | 内部代号 | 含义 |
| --- | --- | --- |
| 2026.1 | **Harbor 港湾** | 首个正式版 = 工具链第一次靠岸停泊，形成可交付的稳定形态 |
| 2026.2 | **Drydock 干船坞** | 编译器彻底重构 = 进入 **Keel 龙骨架构**时代：核心只余机制层（注册表/审计器/加载器/执行骨架，零行为），一切行为皆为注册项；插件/包经 tieir 分发与审计链入港 |

EN: The table above lists each release version, its internal codename, and its meaning: 2026.1 is codenamed **Harbor 港湾**, where the first official release = the toolchain's first docking and berthing, forming a deliverable, stable shape.
EN: 2026.2 is codenamed **Drydock 干船坞**, marking the complete compiler restructure into the **Keel 龙骨架构** era: the core retains only the mechanism layer (registry/auditor/loader/execution skeleton, zero behavior), and all behavior is a registration item; plugins/packages dock via tieir distribution and the audit chain.

代号仅用于宣传/文档/产物命名（如安装包名），不进入版本号。

EN: The codename is used only for promotion, docs, and artifact naming (e.g. installer names); it does not enter the version number.

## 3. 工具链合集组成
*EN: Toolchain Collection Composition*

正式发行版是一套**工具链的合集**：把当前分散的 6 个 crate 二进制
+ REPL 外壳 + 文档打包为一个可安装、可分发的整体。

EN: An official release is a **collection of a toolchain**: it packages the current 6 scattered crate binaries + the REPL shell + the documentation into a single installable, distributable whole.

### 3.1 二进制组件（bin/）
*EN: Binary components (bin/)*

| 组件 | 源 | 职责 |
| --- | --- | --- |
| `tie.exe` | crates/tie | 总入口（四段式调度器 + REPL 启动） |
| `tie-prep.exe` | crates/tie-prep | 预处理（清理代码 + 识别文件角色） |
| `tie-frontend.exe` | crates/tie-frontend | 前端三阶段（词法/语法/语义，调试用） |
| `tie-llvm.exe` | crates/tie-llvm | 编译（IR 生成 + opt/clang/lld 后端） |
| `tie-lsp.exe` | crates/tie-lsp | 语言服务器（LSP over stdio） |
| `tie-interp.exe` | crates/tie-interp | 解释执行 |
| `repl.exe` | repl/repl.tie | REPL 外壳（tie 语言自写，自举产物） |

EN: The table above lists each binary component, its source crate, and its responsibility: `tie.exe` (crater `/tie`) is the main entry (four-stage dispatcher + REPL startup); `tie-prep.exe` (crates/tie-prep) does preprocessing (code cleanup + file-role recognition); `tie-frontend.exe` (crates/tie-frontend) is the front-end three stages (lexing/parsing/semantics, for debugging); `tie-llvm.exe` (crates/tie-llvm) compiles (IR generation + opt/clang/lld back end); `tie-lsp.exe` (crates/tie-lsp) is the language server (LSP over stdio); `tie-interp.exe` (crates/tie-interp) does interpretation; `repl.exe` (repl/repl.tie) is the REPL shell (self-written in tie, a bootstrap artifact).

### 3.2 文档（doc/）
*EN: Documentation (doc/)*

- `README.md`（工程入口）
- `docs/language.md`（语法规范）
- `docs/ai-guide.md`（AI 教学指南）
- `docs/prompt-pack.md`（Prompt 包）
- `CHANGELOG.md`（版本变更记录）
- `LICENSE`（自创通用宽松许可证 Open Source License v1.0，覆盖 tie 官方全部仓库）

EN: `README.md` (project entry); `docs/language.md` (language spec); `docs/ai-guide.md` (AI teaching guide); `docs/prompt-pack.md` (Prompt pack); `CHANGELOG.md` (version changelog); `LICENSE` (the original permissive license Open Source License v1.0, covering all official tie repositories).

### 3.3 示例（examples/）
*EN: Examples (examples/)*

全部示例 `.tie` 源文件（hello / wide / table / tuple / oop / m4_ops 等）。

EN: All example `.tie` source files (hello / wide / table / tuple / oop / m4_ops, etc.).

### 3.4 编辑器扩展（editor/vscode-tie）
*EN: Editor extension (editor/vscode-tie)*

VSCode 扩展（`editor/vscode-tie`）随发行版一起分发，提供语法高亮与
LSP 诊断支持（配合 `tie-lsp`）。

EN: The VSCode extension (`editor/vscode-tie`) is distributed with the release, providing syntax highlighting and LSP diagnostics support (in conjunction with `tie-lsp`).

### 3.5 前置依赖（不随包分发）
*EN: Prerequisite dependencies (not shipped with the package)*

编译链路调用外部 LLVM 工具链：`opt` / `clang` / `llvm-ar`。
发行版**不捆绑** LLVM（体积过大），依赖用户机器已安装 LLVM（PATH 或
`D:\LLVM\bin` 等常见位置）。安装文档与 `tie --version` 输出中说明此依赖。

EN: The compilation chain invokes an external LLVM toolchain: `opt` / `clang` / `llvm-ar`. The release does **not bundle** LLVM (too large), relying on LLVM already installed on the user's machine (in PATH or at common locations such as `D:\LLVM\bin`). This dependency is stated in the installation docs and in the `tie --version` output.

## 4. 工程改造点
*EN: Engineering Modifications*

### 4.1 Cargo 版本号统一
*EN: Unified Cargo version numbers*

- 根 `Cargo.toml` 的 `[workspace.package]` 增加 `version = "2026.1"`。
- 6 个 crate 的 `Cargo.toml` 改为 `version.workspace = true`（消除版本号散落）。

EN: Add `version = "2026.1"` to the root `Cargo.toml`'s `[workspace.package]`.
EN: Change the `Cargo.toml` of the 6 crates to `version.workspace = true` (eliminating scattered version numbers).

### 4.2 tie --version
*EN: `tie --version`*

- `tie --version` 输出版本与代号：
  ```
  tie 2026.1 (Harbor)
  ```
- 版本号读取自 `CARGO_PKG_VERSION`（编译期注入），代号为编译期常量。
- 各子工具（tie-prep / tie-frontend / tie-llvm / tie-lsp / tie-interp）
  同步支持 `--version`（复用同一模式）。

EN: `tie --version` outputs the version and codename:
EN: `tie 2026.1 (Harbor)` (the output text above, shown as-is).
EN: The version number is read from `CARGO_PKG_VERSION` (injected at compile time); the codename is a compile-time constant.
EN: Each sub-tool (tie-prep / tie-frontend / tie-llvm / tie-lsp / tie-interp) also supports `--version` (reusing the same pattern).

### 4.3 打包脚本
*EN: Packaging script*

新增 `scripts/` 目录：

EN: Add a `scripts/` directory:

- `scripts/package.ps1`：Windows 打包脚本。
  1. `cargo build --release`（全 workspace，验证 0 错误）
  2. 复制 6 个 exe + repl.exe 到 `dist/tie-2026.1/bin/`
  3. 复制文档与示例到 `dist/tie-2026.1/`
  4. 复制 VSCode 扩展（editor/vscode-tie）到 `dist/tie-2026.1/editor/vscode-tie/`
  5. 压缩为 `dist/tie-2026.1-win-x64.zip`

EN: `scripts/package.ps1`: the Windows packaging script — 1. `cargo build --release` (the whole workspace, verified with 0 errors); 2. copy the 6 exes + repl.exe into `dist/tie-2026.1/bin/`; 3. copy the docs and examples into `dist/tie-2026.1/`; 4. copy the VSCode extension (editor/vscode-tie) into `dist/tie-2026.1/editor/vscode-tie/`; 5. compress into `dist/tie-2026.1-win-x64.zip`.

### 4.4 README 路线图
*EN: README roadmap*

Harbor M0 里程碑 = 正式发行版基础，规划内容如上。

EN: The Harbor M0 milestone = the official-release foundation, planned as described above.

## 5. 发布流程
*EN: Release Process*

适配自 publish-release 技能（原面向 dotnet，此处 Rust 化）：

EN: Adapted from the publish-release skill (originally for dotnet, here Rust-ified):

1. 推断版本号（年份.修订号，向用户确认）
2. 同步 Cargo 版本号（workspace + `--version` 输出）
3. 更新 CHANGELOG.md
4. 同步文档（README、language.md、ai-guide 等）
5. `cargo build --release` 验证（0 错误）
6. 运行打包脚本生成 zip（+ 可选安装包）
7. 提交并推送（git.franj2.top）
8. 打 git tag（裸版本号 `2026.1`）
9. 创建双平台 Release（GitHub / GitCode），上传安装包与压缩包

EN: 1. Infer the version number (year.revision, confirm with the user); 2. sync the Cargo version numbers (workspace + `--version` output); 3. update CHANGELOG.md; 4. sync the docs (README, language.md, ai-guide, etc.); 5. verify with `cargo build --release` (0 errors); 6. run the packaging script to generate the zip (+ optional installer); 7. commit and push (git.franj2.top); 8. create the git tag (bare version `2026.1`); 9. create the dual-platform Release (GitHub / GitCode), uploading the installer and the zip.

## 6. 既定决策
*EN: Established Decisions*

- 打包产物：**仅 zip 压缩包**（`tie-2026.1-win-x64.zip`），安装包后续版本再做
- 编辑器扩展：**包含** `editor/vscode-tie`（随发行版分发）
- 目标平台：**仅 win-x64**（本机可验证；跨平台后续版本）

EN: Packaging artifacts: **zip archives only** (`tie-2026.1-win-x64.zip`); installers come in a later version. Editor extension: **included** — `editor/vscode-tie` (distributed with the release). Target platform: **win-x64 only** (verifiable on this machine; cross-platform comes in a later version).