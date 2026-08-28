# 规划：tie-install-builder（通用安装程序制作工具）

> 状态：**规划定稿**（2026-08-28 设计对齐）
> 目标：用 tie 语言开发面向 Windows 的**应用安装程序制作工具**，
> 内置多种预设（TRM 捆绑策略）与三种分发负荷（binary / tieir / llvmir）。
> 关联：`docs/designs/trm-final-design.md`（trm 运行时父契约）、
> `docs/plans/tieir-format.md`（tieir 字节码契据）、`docs/plans/package-model.md`
> （包模型 / 签名 P5c）、`docs/cli.md`（tiec / pkg 用法）。

## 0. 契约决策（Contract Decision）

- **Surface**：Windows 应用安装程序的生产工具（构建期）与引导器（目标机运行期）；
  安装描述清单、四种预设、三种负荷格式为对外契约面。
- **Compatibility class**：清单 schema、预设语义、负荷格式均为长期契约，
  采用**只增不改（additive）+ 格式版本号**演进；禁止借字段复用改变语义。
- **选型前提（父契约）**：tie 双路线 —— 路线 A 纯编译零依赖
  （`tie 源码 → LLVM → 原生 exe`）；路线 B `import trm` 后
  `tiec → tieir 字节码 → trm 引擎`。本工具的分发格式契约与父契约对齐。
- **Primary risks**：① 负荷格式对目标机前置条件差异大（binary=零依赖 vs
  llvmir=必须现场编译）；② TRM 版本语义（`major` 变 = ABI 破坏）直接决定
  "检测-安装"预设判定；③ 安装动作非幂等造成重跑/修复失败；④ 内嵌载荷被篡改。

## 1. 定位与目标

一个用 tie 语言写成的工具集，产出**两类产物**：

| 产物 | 谁在用 | 形态 | 职责 |
| --- | --- | --- | --- |
| `tie-install-builder`（构建期） | 应用作者 | tie 编写的 CLI（`type tie<logic>`） | 读安装清单 → 按预设展开安装计划 → 收集负荷 → 生成 `setup-core.exe`（骨架 + 尾部附加载荷） |
| `setup.exe`（目标机运行期） | 终端用户 | .NET 壳（可选） + tie 核心 | 探测目标机 → 解压/校验 → 安装 → 注册 → 事务回滚；支持 `install/repair/uninstall` |

**目标**
- 四预置开箱即用：`bare`（不带 trm）/ `trm-bundled`（带 trm）/
  `trm-detect`（带 trm + 检测复用）/ `runtime-toolchain`（精简工具链）。
- 三种分发负荷：二进制 / tieir / llvmir。
- 引导器提供 CLI（含 `--silent`）与 .NET GUI 壳双前端；核心逻辑 100% tie。
- 全部组件 tie 实现，复用 `std/` 与 `pkg/`（fs/path/args/process/crypto/json/version）。

**非目标**：不做跨平台安装器（第一版目标 win-x64，沿用仓库发行版定位）；
GUI 前端不引入独立运行时（.NET Framework 4.7.2+，Win10 内置）。

## 2. 术语表

| 术语 | 定义（与仓库文档一致） |
| --- | --- |
| TRM | tie runtime suite，路线 B 运行时套件：interp 前端 + 可替换后端 + 引擎级 GC + M:N 协程 + 平台桥 |
| tieir | tie-IR 分发格式，7 段二进制（`TIEIR` 魔数 + 版本，模块头/类型表/符号表/IR 主体/导出表/span） |
| llvmir | `.ll` 文本中间表示，经 `opt` + `clang` + `lld-link` 现场编成原生 exe |
| IR 版本 | tieir 模块头里 u32 IR 版本；`< 当前` 走迁移，`> 当前` 无法降级 |
| `C:\tie` | 目标机 TIE_HOME（主机级安装根，TRM/工具链落位处） |
| `min_tiec` / `abi` | tie.pkg 声明的编译器底线与 ABI，运行期 `trm.init()` 校验 |

## 3. 总体架构与数据流

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

## 4. 安装描述清单（schema，`tie:<data>`）

对外契约面一号。字段全部**可选默认 + 只增不改**：

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

## 5. 四大预设（决策矩阵）

| 预设 | 负荷适配 | 目标机前置 | 运行时安装行为 | 典型场景 | 体积 |
| --- | --- | --- | --- | --- | --- |
| `bare` | binary（推荐） | 无 | 不装 TRM | actor/纯逻辑/编译器系零依赖产物 | 最小 |
| `trm-bundled` | tieir（推荐） | 无 | **无条件**安装捆绑 TRM 到 `C:\tie\trm/{version}/` | UI/系统应用（路线 B 程序） | 中 |
| `trm-detect` | tieir（推荐）；llvmir | 无 | 探测主机 TRM → 满足 `require` 则**复用**，否则安装捆绑 TRM；动作幂等 | 同一 TRM 支撑多个 tie 应用 | 中 |
| `runtime-toolchain` | 三种均可 | 无 | 安装"运行相关工具集 + 按负荷裁剪" | 面向"运行 tie 程序"而非开发 | 大 |

**工具链范围定义（契约面二号）**——运行相关 vs 开发/调试所需：

| 组件 | 运行(R) | 开发/调试(D) | 说明 |
| --- | --- | --- | --- |
| trm 引擎（interp + 平台桥） | ✔ | | 路线 B 执行核心 |
| tieir 加载 / verify / dump 工具 | ✔ | | `tie verify`/`dump-irt` 同族 |
| REPL 外壳 | ✔ | | 会话交互（决策 D4：运行相关） |
| 极简 LLVM 编译单元 | ◆ | | **仅 llvmir 负荷时**计入 R（opt 固定 pass 闭包 + clang + lld-link） |
| tiec / 前端三件套 | | ✔ | 开发编译 |
| tie-lsp / 调试器 / llvm-ar | | ✔ | 开发调试 |

裁剪是**确定性规则**：built-in catalog 声明每组件 R/D 分类 + 依赖闭包；
builder 按 `preset + payload.format` 自动推导组件集，`include/exclude` 显式覆盖。

## 6. 三种分发负荷的契约与前置条件矩阵

| 负荷 | 生成方式（构建期） | 目标机执行所需 | setup 行为 | 版本风险 |
| --- | --- | --- | --- | --- |
| `binary` | 路线 A：`tiec app.tie`（默认 -O2） | 无（零依赖） | 校验和 → 落位 → 注册 | 无（原生） |
| `tieir` | `tiec --tieir-out app.tieir`（默认 strip） | **trm 引擎**（捆绑/检测复用） | 验签 + 哈希 → 落位 → 生成**启动器 shim**（thin exe，调 trm 加载 `@appdir/*.tieir`） | IR 版本：`==` 直载 / `<` 迁移 / `>` 需升级 |
| `llvmir` | `tiec --emit-ir`（或 `--keep-ir`） | **LLVM 工具链** | `target` 模式现场 `opt -O2 → clang → lld-link`；`build` 模式构建期 AOT 预编 | LLVM 最低版本显式拦截 |

**llvmir 双策略（决策 D2）**：清单 `payload.compile: "target" | "build"`（默认
`target`）。`target` = setup 在目标机现场编译（保留"分发 llvmir"的意义、源码可审
计）；`build` = 构建器 AOT 预编后分发 exe（`.ll` 仅归档）。两种模式对最终交付物
都**只认 exe + 校验和**，不存在"装了份编不出来的半成品"。

**启动器 shim（契约面三号）**：tieir 负荷不直接分发可执行文件，由 builder 生成
极小原生 shim（默认 `@appdir/app.launcher.exe`）。职责：定位 TRM home → `trm.init()`
（ABI 校验）→ 加载入口 tieir → 转发进程参数。shim 行为固定，不可被清单字段改写
（防投放）。

## 7. 目标机探测协议（probe）

运行期先探测、后决策，探测结果并入事务日志。

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
**契约：探测失败永远优先于写盘。**

**对父契约的偏差点（需上游确认）**：trm-final-design §7.3 的加载路径是
`~/.tie/trm/{v}`。本设计引入主机级 `C:\tie\trm`（`TIE_HOME`），加载路径扩展为
`TIE_TRM_HOME → ~/.tie/trm → 捆绑`，安装时写入 `TIE_TRM_HOME` 环境变量。
该扩展作为独立改动提交上游对齐，不在本工具内部静默替换父契约。

## 8. 错误模型（稳定错误码面）

| 错误码 | 含义 | Retryable | 客户端动作（用户可自救） |
| --- | --- | --- | --- |
| `E_LOAD` | 载荷解析失败（魔数/段/清单） | 否 | 校验安装包源文件 |
| `E_SIG` | tieir 签名/哈希校验失败 | 否 | 拒绝重下，防篡改 |
| `E_TRM_MISSING` / `E_TRM_MISMATCH` | 无兼容 TRM / major 冲突 | 是（detect 自动安装） | 重跑或手动装 TRM |
| `E_LLVM_MISSING` / `E_LLVM_TOO_OLD` | llvmir 负荷缺 LLVM / 版本过低 | 是（装精简套件） | 装 LLVM 或换构建策略 |
| `E_DISK` / `E_ACL` | 磁盘空间 / 写权限（含 C:\tie 提权） | 是 | 修复后 repair / 提权重跑 |
| `E_COMPILE` | llvmir 现场编译失败（stderr 摘要） | 是 | 修环境后重跑 |
| `E_PARTIAL` | 中途失败，已回滚 | 是 | 重跑（幂等） |

错误输出统一：退出码 + stderr 机器码 + 人类可读详情，**不输出未脱敏路径/环境变量**。

## 9. 幂等、事务与回滚（可靠性核心）

- **事务日志驱动**：安装前在 staging 区记录 `.txn`，每步前置校验和、执行、落账。
  setup 重跑（检测到残留 txn）→ 自动转 **repair 模式**（校验已有文件，增量补齐），
  而非重复安装。
- **回滚点策略**：所有写盘先落临时 staging 目录并备份旧文件（仅覆盖场景），
  失败按日志逆序恢复；`E_PARTIAL` 后系统保证"要么全装上，要么全不装"。
  `C:\tie\*` 的写入纳入同一事务（回滚含已建目录清理）。
- **安装动作幂等**：文件落位 = 内容哈希相同则跳过；环境变量/文件关联/快捷方式
  先查后写，避免重复追加。
- **卸载契约**：`uninstall` 可声明自定义命令；默认 = 删除安装目录 + 撤销注册项 +
  （预设装过的）TRM **不回收**——TRM 是共享依赖，按加分策略保留，记入卸载日志。

## 10. 兼容性矩阵与演进（契约面四号）

| 元素 | 演进规则 | 兼容性类别 |
| --- | --- | --- |
| 清单 `format` | 只增不改段/字段；旧值新解器容忍读取 | additive |
| tieir IR 版本 | `==` 直载 / `<` 提示迁移 / `>` 需升级 | 条件兼容 |
| TRM major | `major` 变更 = ABI 破坏；应用声明 `^x`，探测按 major 对齐 | breaking（父契约） |
| 预设语义 | 四预设名不可变；新增预设 = 新枚举值 + 新安装行为 | additive |
| 启动器 shim | 行为固定，仅随工具链版本内部升级 | additive（实现） |
| llvmir + LLVM 版本 | min-LLVM 只升不降；降级 = `E_LLVM_TOO_OLD` 显式拦截 | breaking 显式拦截 |
| progress 行协议 | GUI 壳与 core 之间的 `progress|<stage>|<percent>` 输出格式固定 | additive（契约面五号） |

**Deprecation 规则**：任何被弃用的字段/预设，先进入兼容读取期（新 builder 仍按
旧语义工作），版本跨度 >= 1 个大版本后再移除，移除即 `format` 变更。

## 11. 安全与审计

| 面 | 要求 |
| --- | --- |
| 载荷完整性 | 全载荷（manifest + payload + signature）构建期算 SHA-256 + 可选签名（复用 tieir P5c 公钥验签范式：包名一致性 + 哈希比对）；setup 首验后解压 |
| 防篡改 | 骨架与载荷分离定位、签名口径为"整包"（单一签名面） |
| 提权最小化 | 默认用户级；仅当写 `C:\tie\*` / Program Files / 服务时触发 UAC，默认豁免 |
| 敏感数据 | 环境变量写入清单需显式声明；错误输出脱敏（不打印完整路径/环境值） |
| 审计 | setup 写入 `txn.log`（步骤 + 签名结果 + 探测结果），卸载保留审计摘要 |

## 12. 项目结构与 tie 模块划分（文件角色）

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

## 13. 测试与验收（矩阵）

- **组合矩阵**：4 预设 × 3 负荷 = 12 主场景；附加：`llvmir × {target,build}`、
  `setup × {GUI, silent}`、无 TRM / mismatch major / 无 LLVM / 断电注入 /
  重跑 repair / 卸载再装 / `C:\tie` 无权限。
- **验收断言**：① 每场景安装后 `tie verify`/校验和全绿；② tieir 负荷经 shim 直跑；
  ③ `E_PARTIAL` 注入后磁盘无残留新文件；④ 重跑与首次安装最终状态一致（哈希级）；
  ⑤ 签名篡改一字节 → `E_SIG` 拦截。
- 用仓库现有回归范式：`tests/*_probe` 探针工程 + `std/assert` 断言。

## 14. 里程碑分期

| 里程碑 | 内容 | 验收 |
| --- | --- | --- |
| M0 | 清单 schema + `bare`/`trm-bundled` + binary/tieir 分发 + 事务回滚 | 12 矩阵 4 场景绿 |
| M1 | `trm-detect` 探测 + 幂等安装/repair + 卸载契约 | 探测复用/安装/回滚绿 |
| M2 | 启动器 shim + tieir 签名/哈希 + `runtime-toolchain` 裁剪（含 REPL/极简 LLVM） | shim 直跑 + 篡改拦截 |
| M3 | llvmir 双策略 + LLVM 探测 + .NET 壳 + 错误码全量 | 无 LLVM/版本过低分叉正确 |
| M4 | `TIE_TRM_HOME` 上游对齐 + 打包/发布流程（复用 pkg publish 范式） | 双端推送 + 回归全绿 |

## 15. 决策记录（ADR 摘要）

| # | 决策点 | 结论 | 备选 |
| --- | --- | --- | --- |
| D1 | 产物形态 | 两段式（builder + setup 核心单文件附加载荷，GUI 壳可替换） | 目录结构安装包 |
| D2 | llvmir 编译时机 | 双策略：`compile: target|build`，默认 target | 仅现场 / 仅 AOT |
| D3 | TRM 安装级别 | 主机级 `C:\tie\trm\{v}`（需提权）+ 提权最小化 | 用户级 `~/.tie/trm` |
| D4 | 精简工具链边界 | 含 REPL + tieir 工具 + 极简 LLVM（opt 固定 pass 闭包）；不含 tiec/lsp/调试器/llvm-ar | 全量捆绑 |
| D5 | 引导器形态 | 双前端：tie 核心（CLI/--silent）+ .NET 壳（子进程 + progress 行协议） | 纯 CLI / 单 GUI |
| D6 | TRM 卸载 | 共享依赖不回收，只记审计 | 随应用删除 |
| D7 | 错误面 | 稳定错误码 + 脱敏输出 | 自由文本 |

## 16. 待决 / 后续细化

1. `TIE_TRM_HOME` 主机级加载路径与 trm-final-design §7.3 的对齐（提交上游）。
2. .NET 壳的框架目标（4.7.2 vs 6+ 单文件）与提权交互 UX。
3. 极简 LLVM 的 pass 清单精确裁剪（只留 -O2 pipeline）。
4. MSI 形态（WiX 桥接）是否纳入 M4（当前未承诺）。