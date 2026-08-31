# 规划：tie-install-builder（通用安装程序制作工具）
*EN: Plan: tie-install-builder (A General-Purpose Installer-Builder Tool)*

> 状态：**规划定稿**（2026-08-28 设计对齐）
> EN: Status: **Plan finalized** (design aligned 2026-08-28)
> 目标：用 tie 语言开发面向 Windows 的**应用安装程序制作工具**，
> 内置多种预设（TRM 捆绑策略）与三种分发负荷（binary / tieir / llvmir）。
> EN: Goal: build a Windows-facing **application-installer builder** in tie, with several built-in presets (TRM bundling strategies) and three distribution payload formats (binary / tieir / llvmir).
> 关联：`docs/designs/trm-final-design.md`（trm 运行时父契约）、
> EN: Related: `docs/designs/trm-final-design.md` (the trm runtime parent contract),
> `docs/plans/tieir-format.md`（tieir 字节码契据）、`docs/plans/package-model.md`
> EN: `docs/plans/tieir-format.md` (the tieir bytecode charter), `docs/plans/package-model.md`
> （包模型 / 签名 P5c）、`docs/cli.md`（tiec / pkg 用法）。
> EN: (package model / signing P5c), `docs/cli.md` (tiec / pkg usage).

## 0. 契约决策（Contract Decision）
*EN: 0. Contract Decision*

- **Surface**：Windows 应用安装程序的生产工具（构建期）与引导器（目标机运行期）；
  安装描述清单、四种预设、三种负荷格式为对外契约面。
  EN: **Surface**: the production tool for Windows app installers (build time) and the bootstrapper (target-machine runtime); the install-description manifest, four presets, and three payload formats form the external contract surface.
- **Compatibility class**：清单 schema、预设语义、负荷格式均为长期契约，
  采用**只增不改（additive）+ 格式版本号**演进；禁止借字段复用改变语义。
  EN: **Compatibility class**: the manifest schema, preset semantics, and payload formats are all long-term contracts, evolving via **additive-only + a format version number**; reusing fields to change semantics is forbidden.
- **选型前提（父契约）**：tie 双路线 —— 路线 A 纯编译零依赖
  （`tie 源码 → LLVM → 原生 exe`）；路线 B `import trm` 后
  `tiec → tieir 字节码 → trm 引擎`。本工具的分发格式契约与父契约对齐。
  EN: **Prerequisite (parent contract)**: tie's two routes — Route A, purely compiled with zero dependencies (`tie source → LLVM → native exe`); Route B, `import trm` then `tiec → tieir bytecode → trm engine`. This tool's distribution-format contract aligns with the parent contract.
- **Primary risks**：① 负荷格式对目标机前置条件差异大（binary=零依赖 vs
  llvmir=必须现场编译）；② TRM 版本语义（`major` 变 = ABI 破坏）直接决定
  "检测-安装"预设判定；③ 安装动作非幂等造成重跑/修复失败；④ 内嵌载荷被篡改。
  EN: **Primary risks**: ① payload formats differ greatly in target-machine prerequisites (binary = zero dependencies vs llvmir = must compile on-site); ② TRM version semantics (`major` change = ABI break) directly determine the "detect-install" preset decision; ③ non-idempotent install actions cause re-run/repair failures; ④ the embedded payload is tampered with.

## 1. 定位与目标
*EN: 1. Positioning and Goals*

一个用 tie 语言写成的工具集，产出**两类产物**：
EN: A toolset written in tie that produces **two kinds of artifacts**:

| 产物 | 谁在用 | 形态 | 职责 |
| --- | --- | --- | --- |
| `tie-install-builder`（构建期） | 应用作者 | tie 编写的 CLI（`type tie<logic>`） | 读安装清单 → 按预设展开安装计划 → 收集负荷 → 生成 `setup-core.exe`（骨架 + 尾部附加载荷） |
| `setup.exe`（目标机运行期） | 终端用户 | .NET 壳（可选） + tie 核心 | 探测目标机 → 解压/校验 → 安装 → 注册 → 事务回滚；支持 `install/repair/uninstall` |

EN: The table lists the two artifacts: `tie-install-builder` (build-time; the application author reads the manifest, expands the install plan by preset, collects payload, and produces `setup-core.exe`) and `setup.exe` (target-machine runtime; the end user detects the machine, unpacks/verifies, installs, registers, rolls back transactions; supports `install/repair/uninstall`).

**目标**
EN: **Goals**
- 四预置开箱即用：`bare`（不带 trm）/ `trm-bundled`（带 trm）/
  `trm-detect`（带 trm + 检测复用）/ `runtime-toolchain`（精简工具链）。
  EN: Four presets work out of the box: `bare` (no trm) / `trm-bundled` (with trm) / `trm-detect` (with trm + detect/reuse) / `runtime-toolchain` (slim toolchain).
- 三种分发负荷：二进制 / tieir / llvmir。
  EN: Three distribution payloads: binary / tieir / llvmir.
- 引导器提供 CLI（含 `--silent`）与 .NET GUI 壳双前端；核心逻辑 100% tie。
  EN: The bootstrapper offers a dual frontend — a CLI (including `--silent`) and a .NET GUI shell; the core logic is 100% tie.
- 全部组件 tie 实现，复用 `std/` 与 `pkg/`（fs/path/args/process/crypto/json/version）。
  EN: All components are implemented in tie, reusing `std/` and `pkg/` (fs/path/args/process/crypto/json/version).

**非目标**：不做跨平台安装器（第一版目标 win-x64，沿用仓库发行版定位）；
GUI 前端不引入独立运行时（.NET Framework 4.7.2+，Win10 内置）。
EN: **Non-goals**: no cross-platform installer (v1 targets win-x64, following the repository's distribution positioning); the GUI frontend introduces no standalone runtime (.NET Framework 4.7.2+, built into Win10).

## 2. 术语表
*EN: 2. Glossary*

| 术语 | 定义（与仓库文档一致） |
| --- | --- |
| TRM | tie runtime suite，路线 B 运行时套件：interp 前端 + 可替换后端 + 引擎级 GC + M:N 协程 + 平台桥 |
| tieir | tie-IR 分发格式，7 段二进制（`TIEIR` 魔数 + 版本，模块头/类型表/符号表/IR 主体/导出表/span） |
| llvmir | `.ll` 文本中间表示，经 `opt` + `clang` + `lld-link` 现场编成原生 exe |
| IR 版本 | tieir 模块头里 u32 IR 版本；`< 当前` 走迁移，`> 当前` 无法降级 |
| `C:\tie` | 目标机 TIE_HOME（主机级安装根，TRM/工具链落位处） |
| `min_tiec` / `abi` | tie.pkg 声明的编译器底线与 ABI，运行期 `trm.init()` 校验 |

EN: Glossary: TRM = the Route-B runtime suite; tieir = the 7-section tie-IR binary; llvmir = the `.ll` text IR; IR version = the u32 in the tieir module header (lower migrates, higher cannot downgrade); `C:\tie` = target-machine TIE_HOME; `min_tiec`/`abi` = the compiler floor and ABI declared in tie.pkg, checked by `trm.init()` at runtime.

## 3. 总体架构与数据流
*EN: 3. Overall Architecture and Data Flow*

```
构建期（builder，tie 编写）:
  安装清单（install.pkg, type tie<data>）
      │  §4 解析/校验
      ▼
  plan/derive —— 按 preset 展开安装计划（文件映射 + 运行时组件集 + 注册动作）
      ▼
  pack/collect —— 负荷收集: binary 直取 / tiec --tieir-out 产 tieir / --emit-ir 产 .ll
                   + 按 preset 裁剪工具链 catalog
      ▼
  build/setup —— 编译引导器核心（setup_main.tie）并追加载荷（payload 段）
      ▼
  setup-core.exe（tie 自包含：骨架 + [manifest + payload + signature]）
      ▲ 可被 .NET 壳（setup.exe GUI）以子进程调起
      ▼
目标机运行期（setup-core / setup.exe）:
  probe（TRM/LLVM 探测, §7）
      ▼
  transaction（事务日志 + 校验和 + 安装/回滚, §9）
      ▼
  install（文件落位 + registry + uninstall 注册, §8）
```

**关键决策 D1：两段式产物。** builder 只负责打包；setup 核心是自包含单文件
（骨架 + 尾部附加载荷），GUI 壳为可替换前端。成因：tie 的 `trm.ui` /
`tie<ui>` 尚未落地，GUI 先行用 .NET 壳，核心逻辑不受影响。
EN: **Key decision D1: two-piece artifacts.** The builder only packages; the setup core is a self-contained single file (skeleton + trailing appended payload), and the GUI shell is a replaceable frontend. Rationale: tie's `trm.ui` / `tie<ui>` are not yet in place, so the GUI first uses a .NET shell while the core logic is unaffected.

## 4. 安装描述清单（schema，`tie:<data>`）
*EN: 4. Install-Description Manifest (schema, `tie:<data>`)*

对外契约面一号。字段全部**可选默认 + 只增不改**：
EN: Contract surface #1. All fields are **optional-with-default + additive-only**:

```
[
  "format": 1,                      // 清单格式版本（additive 演进起点）
  "app":  [ "id": "com.x.app", "name": "...", "version": "1.0.0", "publisher": "..." ],
  "preset": "trm-detect",           // bare | trm-bundled | trm-detect | runtime-toolchain
  "payload": [
    "format": "tieir",              // binary | tieir | llvmir
    "compile": "target",            // llvmir 专用: target(目标机现场) | build(构建期 AOT)
    "entry": "app/main.tieir",      // 入口文件或目录
    "strip": true,                  // tieir 去 span/文档段（--strip）
    "optimize": "-O2",              // llvmir 现场编译优化级别
  ],
  "trm": [
    "require": "^0.8",              // semver 约束，缺省 = 不要求（major 绑定 ABI）
    "bundle": true,                 // 是否把 trm 打包进载荷（preset 决定，可覆盖）
    "home": "C:\\tie\\trm",         // 主机级 TRM 落位（默认）
  ],
  "toolchain": [                    // runtime-toolchain 预设专用
    "include": ["trm", "tieir-tools", "repl", "llvm-min"],
    "exclude": ["tiec", "lsp", "debug"],
  ],
  "files": [  [ "from": "build/app.exe", "to": "@appdir/app.exe", "exec": true ], ... ],
  "shortcuts": [ [ "name": "...", "target": "@appdir/app.exe" ], ... ],
  "env":     [ [ "name": "PATH", "append": "@appdir" ], ... ],
  "assoc":   [ [ "ext": ".data", "cmd": "@appdir/app.exe %1" ], ... ],
  "uninstall": [ "cmd": "@appdir/app.exe --uninstall" ],
]
```

**演进规则**：`format` 递增时，旧值必须在新 builder 上仍按旧语义解析
（只加段/字段，不改既有字段含义）。字段重解释 = 必须升 `format`。
builder 对未知段**忽略并提示**（容忍读取），不崩溃。
EN: **Evolution rule**: when `format` increments, old values must still parse under the old semantics on the new builder (only add sections/fields; never change existing field meanings). Reinterpreting a field = must bump `format`. The builder **ignores with a note** unknown sections (tolerant reading) rather than crashing.

## 5. 四大预设（决策矩阵）
*EN: 5. The Four Presets (Decision Matrix)*

| 预设 | 负荷适配 | 目标机前置 | 运行时安装行为 | 典型场景 | 体积 |
| --- | --- | --- | --- | --- | --- |
| `bare` | binary（推荐） | 无 | 不装 TRM | actor/纯逻辑/编译器系零依赖产物 | 最小 |
| `trm-bundled` | tieir（推荐） | 无 | **无条件**安装捆绑 TRM 到 `C:\tie\trm/{version}/` | UI/系统应用（路线 B 程序） | 中 |
| `trm-detect` | tieir（推荐）；llvmir | 无 | 探测主机 TRM → 满足 `require` 则**复用**，否则安装捆绑 TRM；动作幂等 | 同一 TRM 支撑多个 tie 应用 | 中 |
| `runtime-toolchain` | 三种均可 | 无 | 安装"运行相关工具集 + 按负荷裁剪" | 面向"运行 tie 程序"而非开发 | 大 |

EN: The four-preset matrix: `bare` (binary, no TRM, smallest); `trm-bundled` (unconditional bundled-TRM install); `trm-detect` (reuse a compatible host TRM or install the bundle, idempotent); `runtime-toolchain` (installs a run-related, payload-trimmed toolset, largest).

**工具链范围定义（契约面二号）**——运行相关 vs 开发/调试所需：
EN: **Toolchain-scope definition (contract surface #2)** — run-related vs development/debugging needs:

| 组件 | 运行(R) | 开发/调试(D) | 说明 |
| --- | --- | --- | --- |
| trm 引擎（interp + 平台桥） | ✔ | | 路线 B 执行核心 |
| tieir 加载 / verify / dump 工具 | ✔ | | `tie verify`/`dump-irt` 同族 |
| REPL 外壳 | ✔ | | 会话交互（决策 D4：运行相关） |
| 极简 LLVM 编译单元 | ◆ | | **仅 llvmir 负荷时**计入 R（opt 固定 pass 闭包 + clang + lld-link） |
| tiec / 前端三件套 | | ✔ | 开发编译 |
| tie-lsp / 调试器 / llvm-ar | | ✔ | 开发调试 |

EN: Component classification: the trm engine, the tieir load/verify/dump tools, and the REPL shell are Run (R); an ultra-minimal LLVM compile unit counts as R only for llvmir payloads (◆); tiec / the frontend trio and tie-lsp / debugger / llvm-ar are Dev (D).

裁剪是**确定性规则**：built-in catalog 声明每组件 R/D 分类 + 依赖闭包；
builder 按 `preset + payload.format` 自动推导组件集，`include/exclude` 显式覆盖。
EN: Trimming is a **deterministic rule**: a built-in catalog declares each component's R/D class plus its dependency closure; the builder auto-derives the component set from `preset + payload.format`, and `include/exclude` overrides explicitly.

## 6. 三种分发负荷的契约与前置条件矩阵
*EN: 6. Contract and Prerequisite Matrix for the Three Distribution Payloads*

| 负荷 | 生成方式（构建期） | 目标机执行所需 | setup 行为 | 版本风险 |
| --- | --- | --- | --- | --- |
| `binary` | 路线 A：`tiec app.tie`（默认 -O2） | 无（零依赖） | 校验和 → 落位 → 注册 | 无（原生） |
| `tieir` | `tiec --tieir-out app.tieir`（默认 strip） | **trm 引擎**（捆绑/检测复用） | 验签 + 哈希 → 落位 → 生成**启动器 shim**（thin exe，调 trm 加载 `@appdir/*.tieir`） | IR 版本：`==` 直载 / `<` 迁移 / `>` 需升级 |
| `llvmir` | `tiec --emit-ir`（或 `--keep-ir`） | **LLVM 工具链** | `target` 模式现场 `opt -O2 → clang → lld-link`；`build` 模式构建期 AOT 预编 | LLVM 最低版本显式拦截 |

EN: Payload matrix: `binary` needs nothing on the machine; `tieir` needs the trm engine (bundled or detected) and produces a launcher shim; `llvmir` needs the LLVM toolchain — on-site compilation in `target` mode or build-time AOT in `build` mode.

**llvmir 双策略（决策 D2）**：清单 `payload.compile: "target" | "build"`（默认
`target`）。`target` = setup 在目标机现场编译（保留"分发 llvmir"的意义、源码可审
计）；`build` = 构建器 AOT 预编后分发 exe（`.ll` 仅归档）。两种模式对最终交付物
都**只认 exe + 校验和**，不存在"装了份编不出来的半成品"。
EN: **llvmir dual-strategy (decision D2)**: manifest `payload.compile: "target" | "build"` (default `target`). `target` = setup compiles on-site on the machine (preserving the meaning of "distributing llvmir" with auditable source); `build` = the builder AOT-precompiles and distributes an exe (`.ll` is only archived). Both modes accept **only exe + checksum** as the final artifact — there is never a "half-finished thing you cannot compile".

**启动器 shim（契约面三号）**：tieir 负荷不直接分发可执行文件，由 builder 生成
极小原生 shim（默认 `@appdir/app.launcher.exe`）。职责：定位 TRM home → `trm.init()`
（ABI 校验）→ 加载入口 tieir → 转发进程参数。shim 行为固定，不可被清单字段改写
（防投放）。
EN: **Launcher shim (contract surface #3)**: a tieir payload does not distribute an executable directly; the builder generates a tiny native shim (default `@appdir/app.launcher.exe`). Its duties: locate the TRM home → `trm.init()` (ABI check) → load the entry tieir → forward process arguments. The shim's behavior is fixed and cannot be overridden by manifest fields (anti-tamper).

## 7. 目标机探测协议（probe）
*EN: 7. Target-Machine Probe Protocol (probe)*

运行期先探测、后决策，探测结果并入事务日志。
EN: At runtime, probe first, then decide; probe results are merged into the transaction log.

```
probe:
  1) TRM:    TRM home(主, C:\tie\trm\{v}\_) → ~/.tie/trm/{v}/（父契约原路径）
             → 语言捆绑版本（随宿主安装）
             判定: 版本 major == 清单 trm.require 的 major 且 >= 声明最小 → OK
                   major 不同 → MISMATCH（detect 预设 = 触发安装捆绑）
  2) LLVM:   按发现序找 opt/clang/lld-link；取版本 → 与 payload 声明的 min-LLVM 对标
             （TIE_LLVM_HOME\bin → setup 同目录 llvm\bin → PATH → 固定目录）
  3) 权限:   C:\tie 可写性预检（主机级安装需提权）→ 不具备 + 未提权 → E_ACL
```

探测结果三态：`SATISFIED`（复用）/ `MISSING`（安装捆绑）/
`UNSATISFIABLE`（major 冲突且用户拒绝装 → 明确报错，不装成"跑不起来的应用"）。
EN: Probe results have three states: `SATISFIED` (reuse) / `MISSING` (install the bundle) / `UNSATISFIABLE` (major conflict and the user refuses to install → report clearly; never install a "won't-run application").
**契约：探测失败永远优先于写盘。**
EN: **Contract: probing failures always take precedence over writing to disk.**

**对父契约的偏差点（需上游确认）**：trm-final-design §7.3 的加载路径是
`~/.tie/trm/{v}`。本设计引入主机级 `C:\tie\trm`（`TIE_HOME`），加载路径扩展为
`TIE_TRM_HOME → ~/.tie/trm → 捆绑`，安装时写入 `TIE_TRM_HOME` 环境变量。
该扩展作为独立改动提交上游对齐，不在本工具内部静默替换父契约。
EN: **Deviation from the parent contract (needs upstream confirmation)**: trm-final-design §7.3's load path is `~/.tie/trm/{v}`. This design introduces a host-level `C:\tie\trm` (`TIE_HOME`), extending the load path to `TIE_TRM_HOME → ~/.tie/trm → bundled`, writing the `TIE_TRM_HOME` env var at install. This extension is submitted upstream as a separate change for alignment; it does not silently replace the parent contract inside this tool.

## 8. 错误模型（稳定错误码面）
*EN: 8. Error Model (Stable Error-Code Surface)*

| 错误码 | 含义 | Retryable | 客户端动作（用户可自救） |
| --- | --- | --- | --- |
| `E_LOAD` | 载荷解析失败（魔数/段/清单） | 否 | 校验安装包源文件 |
| `E_SIG` | tieir 签名/哈希校验失败 | 否 | 拒绝重下，防篡改 |
| `E_TRM_MISSING` / `E_TRM_MISMATCH` | 无兼容 TRM / major 冲突 | 是（detect 自动安装） | 重跑或手动装 TRM |
| `E_LLVM_MISSING` / `E_LLVM_TOO_OLD` | llvmir 负荷缺 LLVM / 版本过低 | 是（装精简套件） | 装 LLVM 或换构建策略 |
| `E_DISK` / `E_ACL` | 磁盘空间 / 写权限（含 C:\tie 提权） | 是 | 修复后 repair / 提权重跑 |
| `E_COMPILE` | llvmir 现场编译失败（stderr 摘要） | 是 | 修环境后重跑 |
| `E_PARTIAL` | 中途失败，已回滚 | 是 | 重跑（幂等） |

EN: Error-code table: each code lists its meaning, whether it is retryable, and the client action. Output is unified as an exit code + an stderr machine code + human-readable details.

错误输出统一：退出码 + stderr 机器码 + 人类可读详情，**不输出未脱敏路径/环境变量**。
EN: Errors are uniformly output as an exit code + an stderr machine code + human-readable details; **no unsanitized paths/environment variables are printed**.

## 9. 幂等、事务与回滚（可靠性核心）
*EN: 9. Idempotency, Transactions, and Rollback (The Reliability Core)*

- **事务日志驱动**：安装前在 staging 区记录 `.txn`，每步前置校验和、执行、落账。
  setup 重跑（检测到残留 txn）→ 自动转 **repair 模式**（校验已有文件，增量补齐），
  而非重复安装。
  EN: **Transaction-log driven**: before install, record `.txn` in the staging area; each step pre-checks its checksum, executes, and logs. A setup re-run (detecting a leftover txn) automatically switches to **repair mode** (verify existing files, incrementally fill gaps) rather than reinstalling.
- **回滚点策略**：所有写盘先落临时 staging 目录并备份旧文件（仅覆盖场景），
  失败按日志逆序恢复；`E_PARTIAL` 后系统保证"要么全装上，要么全不装"。
  `C:\tie\*` 的写入纳入同一事务（回滚含已建目录清理）。
  EN: **Rollback-point strategy**: all writes first land in a temp staging directory with backup of old files (overwrite scenarios only); on failure, restore in reverse log order; after `E_PARTIAL` the system guarantees "either everything is installed, or nothing is". Writes to `C:\tie\*` join the same transaction (rollback includes cleaning up created directories).
- **安装动作幂等**：文件落位 = 内容哈希相同则跳过；环境变量/文件关联/快捷方式
  先查后写，避免重复追加。
  EN: **Install actions are idempotent**: file placement skips if the content hash matches; env vars / file associations / shortcuts are check-then-write to avoid duplicate appends.
- **卸载契约**：`uninstall` 可声明自定义命令；默认 = 删除安装目录 + 撤销注册项 +
  （预设装过的）TRM **不回收**——TRM 是共享依赖，按加分策略保留，记入卸载日志。
  EN: **Uninstall contract**: `uninstall` may declare a custom command; the default = delete the install directory + revoke registration + **do not reclaim** TRM (installed by a preset) — TRM is a shared dependency, kept per an additive policy, recorded in the uninstall log.

## 10. 兼容性矩阵与演进（契约面四号）
*EN: 10. Compatibility Matrix and Evolution (Contract Surface #4)*

| 元素 | 演进规则 | 兼容性类别 |
| --- | --- | --- |
| 清单 `format` | 只增不改段/字段；旧值新解器容忍读取 | additive |
| tieir IR 版本 | `==` 直载 / `<` 提示迁移 / `>` 需升级 | 条件兼容 |
| TRM major | `major` 变更 = ABI 破坏；应用声明 `^x`，探测按 major 对齐 | breaking（父契约） |
| 预设语义 | 四预设名不可变；新增预设 = 新枚举值 + 新安装行为 | additive |
| 启动器 shim | 行为固定，仅随工具链版本内部升级 | additive（实现） |
| llvmir + LLVM 版本 | min-LLVM 只升不降；降级 = `E_LLVM_TOO_OLD` 显式拦截 | breaking 显式拦截 |
| progress 行协议 | GUI 壳与 core 之间的 `progress|<stage>|<percent>` 输出格式固定 | additive（契约面五号） |

EN: Compatibility matrix: additive for the manifest `format`, preset semantics, launcher shim, and the progress-line protocol; conditionally compatible for tieir IR versions; breaking for TRM major changes and llvmir-with-LLVM downgrades (explicitly intercepted).

**Deprecation 规则**：任何被弃用的字段/预设，先进入兼容读取期（新 builder 仍按
旧语义工作），版本跨度 >= 1 个大版本后再移除，移除即 `format` 变更。
EN: **Deprecation rule**: any deprecated field/preset first enters a compatible-reading period (the new builder still works by old semantics), is removed only after >= 1 major-version span, and removal itself is a `format` change.

## 11. 安全与审计
*EN: 11. Security and Audit*

| 面 | 要求 |
| --- | --- |
| 载荷完整性 | 全载荷（manifest + payload + signature）构建期算 SHA-256 + 可选签名（复用 tieir P5c 公钥验签范式：包名一致性 + 哈希比对）；setup 首验后解压 |
| 防篡改 | 骨架与载荷分离定位、签名口径为"整包"（单一签名面） |
| 提权最小化 | 默认用户级；仅当写 `C:\tie\*` / Program Files / 服务时触发 UAC，默认豁免 |
| 敏感数据 | 环境变量写入清单需显式声明；错误输出脱敏（不打印完整路径/环境值） |
| 审计 | setup 写入 `txn.log`（步骤 + 签名结果 + 探测结果），卸载保留审计摘要 |

EN: Security table: payload integrity via SHA-256 + optional signing (reusing the tieir P5c public-key verification pattern); anti-tamper via bundle-separated location and "whole-package" signing; minimal privilege escalation (UAC only for `C:\tie\*` / Program Files / services); sensitive data requires explicit env-var declaration and sanitized error output; audit via `txn.log`.

## 12. 项目结构与 tie 模块划分（文件角色）
*EN: 12. Project Structure and tie Module Division (File Roles)*

```
install-builder/
  main.tie                 type tie<logic>    CLI 入口（init/build/strip/version）
  inspect/                 type tie<class>    清单解析/校验（容忍读取）
  plan/derive.tie          type tie<class>    preset → 安装计划展开（组件裁剪规则表）
  pack/tieir_pack.tie      type tie<class>    调 tiec --tieir-out / --dump-irt 校验
  pack/llvmir_pack.tie     type tie<class>    --emit-ir 收集 + opt/clang/lld 命令构造
  pack/collect.tie         type tie<class>    载荷收集 + 工具链 catalog 依赖闭包裁剪
  tpl/setup_main.tie       type tie<logic>    引导器核心骨架（编译成 setup-core.exe）
  tpl/launcher_main.tie    type tie<logic>    启动器 shim 骨架
  rt/probe.tie             type tie<class>    目标机 TRM/LLVM 探测（编译进 setup）
  rt/txn.tie               type tie<class>    事务日志/回滚/幂等
  rt/registry.tie          type tie<class>    快捷方式/环境变量/关联/卸载注册
  rt/ipc.tie               type tie<class>    progress 行协议（契约面五号）
  shell/                   .NET 壳（WPF）      setup.exe GUI（子进程调 setup-core）
```

模块依赖单向：`main → inspect → plan → pack → build`；`rt/*` 仅被 tpl 引用。
class 角色编译为 `.a` 静态库，由 main/tpl 链接。
EN: Module dependencies are one-way: `main → inspect → plan → pack → build`; `rt/*` is referenced only by tpl. Class roles compile into `.a` static libraries, linked by main/tpl.

## 13. 测试与验收（矩阵）
*EN: 13. Testing and Acceptance (Matrix)*

- **组合矩阵**：4 预设 × 3 负荷 = 12 主场景；附加：`llvmir × {target,build}`、
  `setup × {GUI, silent}`、无 TRM / mismatch major / 无 LLVM / 断电注入 /
  重跑 repair / 卸载再装 / `C:\tie` 无权限。
  EN: **Combination matrix**: 4 presets × 3 payloads = 12 main scenarios; extras: `llvmir × {target,build}`, `setup × {GUI, silent}`, no TRM / mismatch major / no LLVM / power-cut injection / re-run repair / uninstall-reinstall / no permission on `C:\tie`.
- **验收断言**：① 每场景安装后 `tie verify`/校验和全绿；② tieir 负荷经 shim 直跑；
  ③ `E_PARTIAL` 注入后磁盘无残留新文件；④ 重跑与首次安装最终状态一致（哈希级）；
  ⑤ 签名篡改一字节 → `E_SIG` 拦截。
  EN: **Acceptance assertions**: ① `tie verify`/checksums all green after each scenario installs; ② tieir payload runs directly through the shim; ③ no leftover new files on disk after `E_PARTIAL` injection; ④ the final state of a re-run equals the first install (at hash level); ⑤ tampering one signature byte → `E_SIG` interception.
- 用仓库现有回归范式：`tests/*_probe` 探针工程 + `std/assert` 断言。
  EN: Use the repository's existing regression paradigm: `tests/*_probe` probe projects + `std/assert`.

## 14. 里程碑分期
*EN: 14. Milestone Phasing*

| 里程碑 | 内容 | 验收 |
| --- | --- | --- |
| M0 | 清单 schema + `bare`/`trm-bundled` + binary/tieir 分发 + 事务回滚 | 12 矩阵 4 场景绿 |
| M1 | `trm-detect` 探测 + 幂等安装/repair + 卸载契约 | 探测复用/安装/回滚绿 |
| M2 | 启动器 shim + tieir 签名/哈希 + `runtime-toolchain` 裁剪（含 REPL/极简 LLVM） | shim 直跑 + 篡改拦截 |
| M3 | llvmir 双策略 + LLVM 探测 + .NET 壳 + 错误码全量 | 无 LLVM/版本过低分叉正确 |
| M4 | `TIE_TRM_HOME` 上游对齐 + 打包/发布流程（复用 pkg publish 范式） | 双端推送 + 回归全绿 |

EN: Milestones: M0 manifest schema + basic presets + binary/tieir distribution + transaction rollback; M1 trm-detect probe + idempotent install/repair + uninstall contract; M2 launcher shim + tieir sign/hash + runtime-toolchain trimming; M3 llvmir dual-strategy + LLVM probe + .NET shell + full error codes; M4 `TIE_TRM_HOME` upstream alignment + packaging/release flow.

## 15. 决策记录（ADR 摘要）
*EN: 15. Decision Record (ADR Summary)*

| # | 决策点 | 结论 | 备选 |
| --- | --- | --- | --- |
| D1 | 产物形态 | 两段式（builder + setup 核心单文件附加载荷，GUI 壳可替换） | 目录结构安装包 |
| D2 | llvmir 编译时机 | 双策略：`compile: target\|build`，默认 target | 仅现场 / 仅 AOT |
| D3 | TRM 安装级别 | 主机级 `C:\tie\trm\{v}`（需提权）+ 提权最小化 | 用户级 `~/.tie/trm` |
| D4 | 精简工具链边界 | 含 REPL + tieir 工具 + 极简 LLVM（opt 固定 pass 闭包）；不含 tiec/lsp/调试器/llvm-ar | 全量捆绑 |
| D5 | 引导器形态 | 双前端：tie 核心（CLI/--silent）+ .NET 壳（子进程 + progress 行协议） | 纯 CLI / 单 GUI |
| D6 | TRM 卸载 | 共享依赖不回收，只记审计 | 随应用删除 |
| D7 | 错误面 | 稳定错误码 + 脱敏输出 | 自由文本 |

EN: ADR summary: D1 two-piece artifacts; D2 llvmir dual-strategy with target default; D3 host-level `C:\tie\trm\{v}` with minimal privilege escalation; D4 a slim toolchain (REPL + tieir tools + ultra-minimal LLVM; no tiec/lsp/debugger/llvm-ar); D5 dual-frontend bootstrapper; D6 TRM not reclaimed on uninstall; D7 stable error codes + sanitized output.

## 16. 待决 / 后续细化
*EN: 16. To Be Decided / Later Refinements*

1. `TIE_TRM_HOME` 主机级加载路径与 trm-final-design §7.3 的对齐（提交上游）。
   EN: Aligning the `TIE_TRM_HOME` host-level load path with trm-final-design §7.3 (submit upstream).
2. .NET 壳的框架目标（4.7.2 vs 6+ 单文件）与提权交互 UX。
   EN: The .NET shell's framework target (4.7.2 vs 6+ single-file) and the privilege-escalation interaction UX.
3. 极简 LLVM 的 pass 清单精确裁剪（只留 -O2 pipeline）。
   EN: Precisely trimming the ultra-minimal LLVM pass list (keeping only the -O2 pipeline).
4. MSI 形态（WiX 桥接）是否纳入 M4（当前未承诺）。
   EN: Whether the MSI form (WiX bridge) enters M4 (currently uncommitted).