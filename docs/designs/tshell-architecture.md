# tshell 命令行壳组件架构 —— tie 平台交互基础设施（定位与边界 + 架构层次 + 集成协议）
*EN: tshell Shell Component Architecture — the command-line shell & interactive infrastructure of the tie platform (position & boundary + architecture layers + integration protocols)*

**日期** / Date: 2026-09-12 · **类型** / Type: 架构设计（定位 / 边界 + 架构层次 + 集成协议；内部细节未讨论不落）
**依据** / Basis: 用户大胆想法（2026-09-12 定）：tie 语言的命令行壳 **tshell**——目标**全面优于 PowerShell**；tshell 是 **tedit 的根基**（tedit 终端模组的命令引擎）；tshell 同时是 **trm 的基础设施**（tieir 观测 / 调试 / 动态加载交互面）；**模块化可嵌入**——能力以独立模块交付，开发者把需要的模块嵌入自己的应用
**关联** / Related: `tedit-architecture.md`（tedit 终端模组 = tshell 前端，双形态协议）· `trm-final-design.md`（trm 引擎 Backend 接口 / 对象模型 / 反射 / tieir 类加载器 / 库层 terminal·process·session 域）· `tie-naming-convention.md`（组件仓 = `t+词缀`，tshell 合规）· `tie-format-api-family.md`（td↔zd 同源双态）· tink（帧协议：长度前缀 + CRC + tsha1f，值管道跨进程底座）· trm-lite（异步求值 / 作业调度）· tieapi（统一 API 契约）· tiec（前端 + tie-interp，现 repl 路径）
**版本** / Version: v0.2（v0.1 首稿 2026-09-12：三身份定位与边界 + 五层架构 + 双形态集成协议 · v0.2 2026-09-12：模块系统与可嵌入能力）

> EXEC BRIEF: tshell (repo `tie-lang/tshell`) is the command-line shell of the
> tie platform with three roles. (1) **Standalone shell**: REPL + script runtime
> + system-command execution with value pipelines, targeting a strictly better
> experience than PowerShell (ms-level startup, MB-resident, tie language as the
> script language). (2) **tedit foundation**: the command engine inside tedit's
> terminal module — dual integration modes, same-process over the tedit protocol
> bus (zd messages, no object references) by default, subprocess over tink frames
> as the escape hatch. (3) **trm infrastructure**: the interactive workbench trm
> lacks — tieir observation/disassembly, debugging front-end (breakpoints/steps/
> stack/object introspection via the trm object model & reflection), dynamic
> module loading interaction, and a configurable REPL eval backend (tie-interp
> default | trm engine via its Backend interface). Plus (4) **modular &
> embeddable**: capability delivered as independently embeddable modules
> (lineedit/complete/command/pipeline/render/session/repl/run/observe), hosts
> assemble only the subset they need — compile-time assembly by default,
> process-out embedding over tink frames for language-agnostic hosts; the
> standalone binary is just the default full assembly. Single engine, five
> layers; L0–L2 shared by all roles, only L3 (protocol adaptation) differs.
> Foundations: tiec front-end + tie-interp, trm, trm-lite, tink frames, td/zd,
> tieapi.

---

## 1. 定位 / Positioning

* **tshell = tie shell**（组件仓 `tie-lang/tshell`，待建）：tie 平台**命令行壳**与**交互基础设施**
* **三个身份，一个引擎**：独立命令行壳 · tedit 根基 · trm 基础设施——内核同一，配角不同
* **完全 tie 自研**：行编辑 / 补全 / 渲染 / 命令系统全 tie 写；执行复用 tiec 与 trm，不造新求值器
* **硬目标：全面优于 PowerShell**——对比见 §11，量化方向：毫秒级启动、MB 级常驻、值管道、语言即脚本
* **模块化可嵌入**：能力以独立模块交付，开发者把需要的模块嵌入自己的应用（§12）——独立命令行壳只是默认的**全量装配**形态

### 1.1 三个身份 / Three Roles（2026-09-12 定）

| 身份               | 内涵                                                        | 能力来源                                                       |
| ------------------ | ----------------------------------------------------------- | -------------------------------------------------------------- |
| **命令行壳**（独立价值） | tie 语言的交互环境 + 系统壳：REPL、脚本运行时、系统命令混合、值管道      | L0–L4 全部层 · tie 语言本身                                      |
| **tedit 根基**     | tedit「工作环境」中**终端模组**的命令引擎——tedit 不自己解析命令，只渲染与对接 | 双形态协议层（§9）· tiu 终端部件（前端，tedit 侧）             |
| **trm 基础设施**   | trm 缺失的交互面：tieir 观测台 / 调试前端 / 动态加载交互 / 可配置执行后端 | trm 引擎 Backend 接口 · 对象模型 · 反射 · tieir 类加载器（§10） |

* **统一于一个引擎**：三个身份共享 L0–L2；L3（协议适配层）按身份选择，L4（入口）按场景分派——这是"根基"不膨胀、"基础设施"不重复的保证

### 1.2 可嵌入性 / Embeddability（2026-09-12 定）

* tshell 不止是独立命令行工具，更是**可嵌入的 shell 引擎库**——每个能力单元是独立模块，开发者把需要的模块**装进自己的应用**（游戏内控制台 / 应用内 REPL / 数据加工工具 / trm 宿主调试面板 / 测试驱动）
* **模块 = 编译期/嵌入期装配的库级能力单元**（`use tshell.lineedit` 等），区别于 tedit 的运行期模组（manifest / 生命周期 / 权限）——两种抽象不混用：tshell 交付"可拆能力"，tedit 交付"可装功能"
* **独立壳只是默认装配**：standalone 二进制 = 全模块聚合；嵌入者取子集，体积/内存随工作集（§12）

## 2. 边界 / Boundary

* **本组件负责**：REPL 循环 · 命令解析（tie 表达式优先 → 内建 → 外部回退）与内建命令集 · 值管道与渲染（表 / 文本 / 结构化出口）· 行编辑 / 补全 / 历史 / 别名 / 配置（td 资产）· 脚本执行器（-f / shebang / -e · 脚本内联内建命令函数式调用）· 作业控制（后台 / 挂起 / 恢复，异步经 trm-lite）· 双形态 tedit 对接（§9）· tieir 观测 / 调试 / 动态加载交互面（§10）· **模块系统与嵌入 API**（能力模块化交付 + 开发者按需嵌入，§12）
* **本组件不负责**：tie 编译与求值内核（tiec 前端 + tie-interp，或 trm 引擎——均外部组件，tshell 只对接不实现）· 并发调度（trm-lite）· 跨进程帧协议本体（tink）· 终端模拟器 UI（tiu / 浏览器终端，tedit 等前端持有）· 系统 pty / 终端平台细节（薄适配，可接 `trm:terminal` 库层）· tie 标准库（tiec）

## 3. 架构层次 / Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│ L4 宿主层：[host] 入口（repl / run / -e / --stdio）· 装配器 · 信号 │
├──────────────────────────────────────────────────────────────┤
│ L3 协议适配层：[srv] 同进程 zd 内存总线（tedit，默认）            │
│                [srv] | 子进程 zd 帧（tink 帧，逃生口/远程/WASM） │
├──────────────────────────────────────────────────────────────┤
│ L2 会话层：[lineedit] 行编辑 · [complete] 补全 · [session] 历史/  │
│            配置/别名 · [render] 渲染 · 配置（td 热加载）         │
├──────────────────────────────────────────────────────────────┤
│ L1 命令层：[command] 解析（tie → 内建 → 外部）· 内建命令 · 作业    │
│            [pipeline] 值管道 / 重定向 / 结构化格式（fmt）        │
├──────────────────────────────────────────────────────────────┤
│ L0 语言层：[repl] 求值循环·续行·异常捕获 ─┬─ tie-interp（默认）    │
│              [run] 脚本运行时           └─ trm 引擎（Backend）   │
│            [observe] tieir 观测/调试（反汇编/断点/栈帧内省）      │
└──────────────────────────────────────────────────────────────┘
底座复用：trm-lite（异步取值/作业调度）· tink 帧协议（跨进程）
          · td/zd 同源双态（配置/历史/数据）· tieapi（对外统一契约）
          · trm 库层（terminal/process/session，路线 B 可接）
（方括号 = 独立嵌入模块；开发者按需取子集装配，见 §12）
```

* **L4 宿主层**：统一入口分派——交互式 `tshell` · 脚本 `tshell script.tie` · 单行 `tshell -e "…"` · 协议服务 `tshell --stdio`；信号处理（Ctrl-C 打断前台任务 / Ctrl-D EOF）
* **L3 协议适配层**：唯一按身份分叉的层——tedit 同进程走内存 zd 消息总线；子进程/远程走 tink 帧（§9）；stub 模式供测试驱动
* **L2 会话层**：tie 自研行编辑（多行续行 / 括号自动补全 / readline 兼容键集）· 可插拔补全源 · 历史持久化 · 别名 · 表/文本渲染 · 配置 td 资产热加载（`reload`）
* **L1 命令层**：输入先按 tie 表达式/语句解析（成功即 REPL 求值，未完成语法自动续行）；解析失利回退内建命令 → 外部命令（PATH 查找）→ 拼写纠错提示；值管道在命令间传 **tie 值**（§5）
* **L0 语言层**：**求值内核接口**——默认 `tie-interp`（现 repl.tie 同款路径，快速启动零依赖），可配置切 `trm 引擎`（走 trm 的 `Backend` 接口 compile/execute/invoke，获得引擎级 GC / 反射 / 统一对象身份）；脚本文件加载；**tieir 观测/调试服务**：反汇编 / 断点 / 单步 / 栈帧与对象内省（经 trm 对象模型与反射，§10）

## 4. 命令模型 / Command Model

* **解析优先级**（一行输入，顺序判定）：
  1. **tie 表达式/语句**：语法成立 → REPL 求值（`sqrt(2)`、`var x = 1; x + 1`）
  2. **内建命令**：短一致命名表（`cd` `pwd` `ls` `mv` `cp` `rm` `cat` `set` `alias` `history` `source` `exec` `help` `exit` …）
  3. **外部命令**：PATH 查找子进程执行（文本流为主）；`*.tie` 脚本在 PATH 内直接当命令（脚本运行时集成，语言与命令统一命名空间）
  4. **纠错引导**：真实命令拼写错误 → did-you-mean 提示（对齐 tiec 诊断规范，不静默吞错）
* **内建命令原则**：短、一致、与 tie 语法无歧义；全部可 `--help`；环境上下文（PATH / 当前目录 / 环境变量 / 最后退出码 `$?`）
* **脚本内调用**：脚本文件里内建命令即函数式调用（`ls()`、`cd(dir)`），语言与命令同一个命名空间，无两条语法

## 5. 值管道与渲染 / Value Pipeline & Rendering

* **管道传值不传文本**：命令间管道传递 **tie 值**（表 / 标量 / 行流），表为结构主体——对标 PowerShell 对象管道但**去重去黑箱**
* **同进程传值不序列化**：管道值机内直接传递（引擎管生命期）；**跨模组 / 跨进程边界自动 zd 帧**（值语义、指纹校验）——对齐 tedit 铁律与 tink 帧协议
* **谓词即语法**：`ls | filter { $x.size > 1024 }`、`cat x.data.td | parse | count`——管道下游用 tie 表达式（闭包糖）作筛选/变换
* **重定向**：`> file`（文本 / `> zd:` 结构化二进制 / `> td:` 可读源）；`2>` 错误流分离
* **渲染**：表值 → 对齐表格（终端宽度自适应、超宽列截断可展开）；标量 → 文本；`| fmt json|zd|td` 显式结构化出口（对齐 tieapi 契约，下游可继续管）
* **流式**：大输出流式渲染不整块缓冲（对齐性能纪律）

## 6. 脚本运行时 / Script Runtime

* `tshell script.tie` 与 shebang `#!/usr/bin/env tshell` → 整文件按 **tie 程序**执行，注入壳服务：argv / env / cwd / 退出码 / 信号
* `tshell -e "expr"` 单行执行；`tshell -i` 强制交互；`tshell -c file` 执行（对齐生态 CLI 惯例）
* 脚本即交互：脚本可用全部 REPL 能力（内建命令、值管道、作业），REPL 可用全部脚本能力——**同一引擎，两种入口**

## 7. 行编辑与补全 / Line Editing & Completion

* **tie 自研行编辑**（对齐生态自研纪律，零外部 readline 依赖）：多行续行（括号/字符串未闭合自动等待）、括号自动补全、历史搜索（Ctrl-R）、readline 兼容键集（Ctrl-A/E/W/U、Tab、Up/Down…）
* **可插拔补全源**：内建命令 → PATH 可执行 → tie 标识符（当前作用域）→ 文件路径 → td/zd 资产（补全源注册接口，对齐 tedit 贡献点思路，生态组件可扩展）
* **非 tty 降级**：检测非交互环境（管道/脚本）自动关闭行编辑，行为稳定可预测

## 8. 历史与配置 / History & Config

* **td 资产**（可读可校验，同源双态纪律）：`~/.tshell/history`（历史与会话）· `~/.tshell/config.td`（变量 / 别名 / PATH / 渲染选项 / 补全开关 / 执行后端选择）
* **热加载**：`reload` 命令即时生效，用户操作即写文件（配置纪律）

## 9. 与 tedit 集成（根基职责）/ tedit Integration

* 铁律：**tedit 终端模组 = tiu 终端部件（前端）+ tshell 引擎（后端）**；前端与引擎**只换协议数据，不穿对象引用**
* **同进程模式（默认）**：引擎嵌入 tedit 终端模组进程，zd 消息走 **tedit 协议总线**（Command / Event / RPC / Document / Asset / Selection 同一套）；输入行 / 补全请求 / 输出流 / 任务事件全部协议化；值管道机内传值，跨模组边界才序列化（零拷贝热路径）
* **子进程模式（逃生口，可配置）**：`tshell --stdio` 起 **tink 帧协议服务**（长度前缀 + CRC + tsha1f 强校验），stdin/stdout 上跑 zd 帧——崩溃隔离（安全敏感/性能关键模组）、远程 shell、手机 / WASM 后端（对齐 p.9.6.2 与 tedit 模组隔离的可选逃生口）
* **两模式复用 L0–L2 全部核心**，仅 L3 不同——"双形态可配置"即此

## 10. 作为 trm 基础设施 / trm Infrastructure

> trm 定位"调试友好 + 跨平台一致"（trm-final-design.md），引擎已备（interp/后端/类加载器/对象模型/反射），**交互面由 tshell 补齐**——对照 JVM 生态即 jshell + jdb + javap 合一。

| trm 基础设施职责       | 内容                                                          | JVM 类比 |
| ---------------------- | ------------------------------------------------------------- | -------- |
| **tieir 观测台**       | 加载 / 校验 / 反汇编 tieir 字节码，指令级查看与签名校验（对齐 p.7.3.2-e 诊断） | javap    |
| **调试前端**           | 断点 / 单步 / 步过，栈帧 / 变量 / 对象内省——经 trm 对象模型与反射底座        | jdb      |
| **动态加载交互面**     | 模块装载 / 卸载 / 热更的交互驱动（配合 trm 反射 + tieir 类加载器）           | jshell 动态加载 |
| **REPL 执行后端可配置** | `set eval-backend interp|trm`：tie-interp 快速路径（默认）\| trm 引擎（Backend 接口 execute/invoke，统一对象身份 GC） | jshell 对接 VM |

* **可替换后端哲学对齐**：trm 引擎侧后端可替换（interp / ORC-JIT / wasm-AOT），tshell 侧执行后端亦可替换（tie-interp / trm）——两层可替换，契约一致（interp 为语义基准，对齐 trm §7.4 契约矩阵）
* **自举自洽**：tshell 自身走路线 B 时可 import trm 库层（`trm:terminal` 的 TTY/ANSI、`trm:process`、`trm:session` 的历史/配置），同时保留路线 A 纯编译回退——与"双层非对称"哲学一致；**tshell 用 trm 构建自己，又反过来是 trm 的基础设施**（同 jshell 是 JVM 应用同理）

## 11. 对比 PowerShell / vs PowerShell

* **目标：全面优于 PowerShell**——量化方向如下表（落地时以基准测试验收）：

| PowerShell 痛点            | tshell 对策                                                     |
| -------------------------- | --------------------------------------------------------------- |
| 启动秒级、内存大（.NET 常驻）| 原生零依赖，毫秒级启动、MB 级常驻（老电脑友好）                     |
| 命令冗长、别名混乱（Get-ChildItem vs ls） | 内建短命令一致命名 + tie 语法自然表达，无第二套语法                 |
| 对象管道强大但黑箱（类型/格式化复杂） | 值管道透明（tie 值即表，自渲染自描述），显式结构化出口（`fmt zd/json`） |
| 脚本语言与命令行手感割裂   | 同一引擎：REPL = 脚本 = 命令行，语言与命令一个命名空间              |
| 平台割裂、移动端缺席       | 跨平台（win/linux/macos）+ WASM/移动可部署（双形态协议天然支持远程） |

## 12. 模块系统与嵌入 / Modular System & Embeddability

> **原则**：tshell = **核心 + 可拆卸能力模块**；模块即**嵌入单元**——开发者按需取子集装进自己的应用，不强制全壳。独立命令行壳只是默认装配。

* **与 tedit 模组的区别（不混用）**：tshell 模块 = **编译期/嵌入期装配的库级能力单元**（tie 源码模块，`use tshell.*` 即取，体积随工作集）· tedit 模组 = **运行期装卸**（manifest / 生命周期 / 权限，tedit-architecture §5）——tshell 交付"可拆能力"，tedit 交付"可装功能"

### 12.1 模块清单（对齐五层，每模块独立可嵌入）

| 模块      | 职责                                                          | 独立嵌入场景示例                              |
| --------- | ------------------------------------------------------------- | --------------------------------------------- |
| `lineedit` | 多行行编辑、键集、自动续行（tie 自研，零 readline）          | 任意文本输入部件（对话框 / 搜索框）           |
| `complete` | 可插拔补全源与补全协议                                      | 代码编辑补全、数据录入辅助                    |
| `command`  | 命令解析（tie → 内建 → 外部）+ 内建命令集 + 拼写纠错          | 游戏内控制台、调试命令系统                    |
| `pipeline` | 值管道 / 重定向 / 结构化格式（fmt zd·json·td）               | 数据加工工具、端到端测试驱动                  |
| `render`   | 表 / 文本 / 流式渲染（输出流可注入）                         | 报表、日志格式化、CI 输出                     |
| `session`  | 历史持久化 / 配置 schema（td）/ 别名                         | 应用会话记忆、配置管理                        |
| `repl`     | 求值循环 / 多行续行 / 异常捕获 / 结果渲染（执行后端可注入）   | 应用内 REPL（调试台 / notebook / 控制台）     |
| `run`      | 脚本运行时（argv / env / exit / shebang）                    | 嵌入式脚本引擎、批处理                        |
| `observe`  | tieir 观测 / 调试（反汇编 / 断点 / 栈帧内省，经 trm 对象模型）| trm 宿主调试面板、性能观察工具               |

### 12.2 模块契约（依赖方向）

* 每模块：**单一职责 + 明确接口**（tieapi 契约风格：值语义数据 + td/zd I/O + 诊断码）
* **下层不依赖上层**：渲染不依赖具体终端（输出流注入）· 行编辑不依赖 REPL（独立输入部件）· `observe` 只依赖 trm 对象模型 · `repl` 的执行后端可注入（interp / trm 二选一）
* 模块间通过**值语义接口**交换（表 / 记录），适配器可注入（输出流 / 输入源 / 执行后端）——对齐"模组间只走协议数据"铁律
* **事件流可记录回放**（对齐 tedit 事件纪律）→ 嵌入方录制 / 回放驱动（测试 / 宏）

### 12.3 三种嵌入形态

1. **静态嵌入（路线 A，默认）**：`use tshell.lineedit` 等 tie 源码模块**静态编译进宿主**——零运行时依赖、随宿主尺寸；tiec 链接期按装配裁剪未用模块
2. **动态嵌入（路线 B）**：import trm 后经 trm Backend / 对象模型装配模块——获得引擎级 GC / 反射 / 热更
3. **进程外嵌入（语言无关）**：`tshell --stdio` tink 帧协议，任意语言宿主驱动（zd 值语义、CRC+tsha1f 强校验），无需 tie 运行时——对齐对外四通道（tink 多语言库 / CLI / 协议）

### 12.4 装配与最小化

* 宿主声明 `modules: [lineedit, command, session, render]`（td 配置）→ **装配器**只编入所选模块（裁剪，内存/体积随工作集，对齐老电脑约束与"模块=嵌入单元"）
* **standalone 二进制 = 默认全量装配**（入口即壳）；**tedit 终端模组嵌入 = 取 lineedit + command + session + render（+repl 可选）**，不装 observe / run 全量；trm 宿主调试面板 = 取 observe + repl
* 装配器本身作为 `host` 模块内置（L4），嵌入场景可自备宿主，只取能力模块（§12.1）

## 13. 依赖复用 / Reused Foundations

* tiec 前端 + tie-interp（现货 REPL 路径）· trm（Backend 接口 / 对象模型 / 反射 / tieir 类加载 / 库层 terminal·process·session）· trm-lite（异步求值 / 作业调度）· tink 帧协议（跨进程 zd 帧）· td/zd 同源双态（配置 / 历史 / 数据 / 管线值序列化）· tieapi（对外接口统一契约）· tedit 协议总线（集成）

## 14. 约束与对策 / Constraints

| 约束       | 对策                                                            |
| ---------- | --------------------------------------------------------------- |
| 性能好     | 热路径零分配（值管道机内传值不序列化）· 流式渲染不整块缓冲                 |
| 内存小     | MB 级常驻 · 组件按需加载（补全源等按首次使用载入）· 历史/配置惰性读写        |
| 老电脑友好 | 质量档可切 · 低内存模式（关高级补全、关历史高亮）                          |
| 跨平台     | 平台细节薄适配（可接 trm:terminal 库层）· WASM 后端出子进程模式 p.9.6.2      |
| 手机能用   | 双形态协议（子进程/远程）天然支持外部前端 · 触屏输入经 tedit 前端转协议      |

## 15. 未决 / 后续细化 / Open Questions

* 值管道与 tink 管道图（车间场景）的整合深度 · tiec repl 与 tshell 的未来关系（repl 是否并入 tshell）· 执行后端切换的求值语义一致性（interp 基准 + 契约矩阵如何覆盖双后端）· 补全源插件化协议细则 · 配置 schema 明细 · 诊断体系接入（E/W 标号，对齐 tiec 诊断规范）· 与 tieapi 契约的更细绑定（命令即 API？）· 发行模型（独立仓 tie-lang/tshell，对齐 release.md 组件发行；**嵌入交付形态**：是否随组件仓提供静态库 / 多语言绑定）· 模块装配协议细则（依赖关系 / 裁剪粒度：模块级 vs 函数级）· 手机 / WASM 终端前端形态——**均未推演，推演完成后在本文档补章**

---

## 附录 / Appendix

* 术语 / Terms：会话层（session，行编辑/历史/配置/渲染）· 值管道（value pipeline，命令间传 tie 值）· 双形态（同进程协议隔离 / 子进程帧协议）· 观测台（tieir 观测，反汇编/校验）· 调试前端（断点/单步/栈帧内省）· 模块（module，编译期/嵌入期装配的库级能力单元）· 装配（assembly，宿主按需选择模块子集）
* 演进：本文档为定位与边界 + 五层架构 + 集成协议 + 模块系统；L0–L4 各层内部细节（行编辑键集、补全协议、渲染算法、模块装配协议等）每层一节，讨论后补落