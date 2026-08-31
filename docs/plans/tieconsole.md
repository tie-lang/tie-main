# 规划：tieconsole（对标 PowerShell 的对象化 shell）
*EN: Plan: tieconsole (an Object-Oriented Shell Modeled on PowerShell)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> EN: Status: **Plan** (design discussion finalized 2026-08-15, not yet implemented)
> 本文档定义 tieconsole——对标 PowerShell 理念（非语法兼容）的
> 对象化命令行 shell，跨平台一致。
> EN: This document defines tieconsole — an object-oriented command-line shell modeled on the PowerShell philosophy (not syntax-compatible), consistent across platforms.
> 决策汇总：
> EN: Decision summary:
> **P**（管道运算符 `->`，语言级，左结合最低优先级）+ **C**（命令预先定义：
> EN: **P** (the `->` pipeline operator, language-level, lowest-precedence left-associative) + **C** (commands predefined:
> cmdlet 声明 + 预定义命令集）+ **S**（跨平台层 = tie 运行时套件 **trm**）
> EN: cmdlet declarations + a predefined command set) + **S** (cross-platform layer = the tie runtime suite **trm**)
> + **F1+F2+F3**（自动表格 + 自定义视图 + 结构化输出 zd/json）
> EN: + **F1+F2+F3** (auto-table + custom views + structured zd/json output)
> + **I1+I2+I3**（行编辑/历史/多行 + LSP 补全 + ANSI 语法高亮）
> EN: + **I1+I2+I3** (line editing / history / multi-line + LSP completion + ANSI syntax highlighting)
> + **A1+A2**（profile 脚本 + zd 状态持久化）。
> EN: + **A1+A2** (profile scripts + zd state persistence).
> 待办：1. trm 设计（tie 运行时套件）2. LSP 增强设计。
> EN: To-dos: 1. trm design (the tie runtime suite) 2. LSP enhancement design.
> 关联：字符串模型（ESC 转义前置）、闭包模型（格式函数）、trm 架构
> EN: Related: string model (ESC-escape prerequisite), closure model (format functions), trm architecture
> （tie 运行时套件，吸收原 tucore）、序列化规范（通信用 zd）、LSP（tie-lsp 已有）。
> EN: (the tie runtime suite, absorbing the former tucore), serialization spec (zd for communication), LSP (tie-lsp already exists).

## 1. 定位
*EN: 1. Positioning*

tieconsole = **对象化 shell**（对标 PowerShell 理念）：
EN: tieconsole = an **object-oriented shell** (modeled on the PowerShell philosophy):
- 命令输出结构化对象，管道传对象非文本
  EN: Commands output structured objects; the pipeline passes objects, not text.
- 语言 = shell（tie 既是脚本语言又是交互语言，零切换）
  EN: The language = the shell (tie is both a scripting language and an interactive language, with zero switching).
- 跨平台一致（Windows/Linux/macOS 同一体验）
  EN: Cross-platform consistency (the same experience on Windows/Linux/macOS).
- 随 tie 发行，独立产品形态
  EN: Distributed with tie as an independent product form.

## 2. 管道模型（P：`->` 运算符）
*EN: 2. Pipeline Model (P: the `->` Operator)*

### 2.1 语言级管道（脚本 + 交互一致，无双轨）
*EN: 2.1 Language-Level Pipeline (script + interactive consistent, no dual tracks)*

```tie
// a -> f = f(a)，链式左结合：a -> b -> c = c(b(a))
Get-Process() -> Where-Object(is_running) -> Format-Table()

// 交互 shell 中同样用 ->（与脚本完全一致）
> fs.list(".") -> filter(name_contains("tie")) -> format_table()
```

### 2.2 `->` 的三个角色（解析规则）
*EN: 2.2 The Three Roles of `->` (Parsing Rules)*

| 角色 | 语法 | 上下文区分 |
| --- | --- | --- |
| 函数签名返回类型 | `func f(x: i64) -> i64` | func 签名上下文 |
| 闭包字面量返回类型 | `var f = func(x) -> i64 { ... }` | func 字面量（后跟 `{`） |
| 管道运算符 | `a -> f` = `f(a)` | 表达式上下文 |

EN: The table shows `->`'s three roles (return type in a func signature, return type in a closure literal, pipeline operator) and the context that distinguishes each.

**区分依据**：
EN: **Disambiguation basis**:
1. `->` 后跟**类型保留关键字**（i64/f64/bool/string/table...）= 返回类型
   （保留字不能作表达式）
   EN: If `->` is followed by a **type-reserved keyword** (i64/f64/bool/string/table...) = return type (reserved words cannot be expressions).
2. parser 状态机：func 签名上下文 vs 表达式上下文
   EN: The parser state machine: func-signature context vs expression context.
3. 闭包后必须跟 `{`；管道后跟表达式
   EN: A closure must be followed by `{`; a pipeline is followed by an expression.

### 2.3 结合性与优先级
*EN: 2.3 Associativity and Precedence*

- **左结合**：`a -> b -> c` = `c(b(a))`（流式）
  EN: **Left-associative**: `a -> b -> c` = `c(b(a))` (streaming).
- **最低优先级**（低于比较）：`a + 1 -> f` = `f(a + 1)`——管道是"最后一步"
  EN: **Lowest precedence** (below comparisons): `a + 1 -> f` = `f(a + 1)` — the pipeline is the "last step".
- 与 `|`（位或）无 token 冲突（多字符 token，最长匹配）
  EN: No token conflict with `|` (bitwise-or) (multi-character token, longest-match).

## 3. 命令模型（C：预先定义）
*EN: 3. Command Model (C: Predefined)*

### 3.1 cmdlet 声明（预先定义，PowerShell 风格）
*EN: 3.1 cmdlet Declaration (predefined, PowerShell style)*

```tie
// 命令预先定义：名称 + 参数元数据 + 实现
cmd Get-Process {
    param(name: string, id: i64)      // 命名参数
    // 实现：返回对象表
    return ps.list_processes(name, id)
}

cmd Where-Object {
    param(filter: fn(Obj) -> bool)    // 函数参数 = 过滤器闭包
    return input -> filter            // 管道输入
}
```

- **预先定义**：命令集在启动/加载时注册（内置命令 + 包命令），
  支持补全/帮助/参数校验（元数据驱动）
  EN: **Predefined**: the command set is registered at startup/load (built-in commands + package commands), supporting completion/help/parameter validation (metadata-driven).
- 内置预定义命令集：文件/进程/环境/文本/网络（fs 系/ps 系/env 系/str 系/http 系）
  EN: Built-in predefined command set: file/process/environment/text/network (fs/ps/env/str/http families).
- 包命令：namespace pub func 自动注册为命令（C1 融合——函数即命令 + cmd 元数据）
  EN: Package commands: namespace pub funcs auto-register as commands (C1 fusion — function-as-command + cmd metadata).
- 外部进程命令：PATH 查找（输出文本，需手动 parse——PowerShell 同款）
  EN: External-process commands: PATH lookup (text output, must be parsed manually — same as PowerShell).

### 3.2 参数绑定
*EN: 3.2 Parameter Binding*

- 位置参数 + 命名参数（`Get-Process -id 42`）
  EN: Positional + named parameters (`Get-Process -id 42`).
- 参数类型检查（string/i64/bool/fn 闭包）
  EN: Parameter type checking (string/i64/bool/fn closures).
- 管道输入绑定：`input` 特殊参数（管道对象流）
  EN: Pipeline-input binding: the `input` special parameter (the pipeline object stream).

## 4. 跨平台层（S：tie 运行时套件 trm）
*EN: 4. Cross-Platform Layer (S: the tie Runtime Suite trm)*

> **trm（tie runtime suite）待办 #1 详细设计**——本节点位：
> EN: **trm (the tie runtime suite) is To-do #1 for detailed design** — the positioning of this section:

- trm = tie 运行时套件：跨平台统一 API（终端/进程流/文件/环境/会话 + ui 域）
  EN: trm = the tie runtime suite: a unified cross-platform API (terminal / process stream / file / environment / session + the ui domain).
- tieconsole 依赖 trm 的 system 域（terminal/process/session 等）
  EN: tieconsole depends on trm's system domain (terminal/process/session, etc.).
- trm 已吸收原 tucore（tucore → trm.ui）：ui 域服务 tieui，system 域服务
  tieconsole，共享底层 extern
  EN: trm has absorbed the former tucore (tucore → trm.ui): the ui domain serves tieui and the system domain serves tieconsole, sharing the underlying extern.
- 详见 [trm-arch.md](trm-arch.md)（待办 #1 已落地）
  EN: See [trm-arch.md](trm-arch.md) (To-do #1 has landed).

## 5. 格式系统（F1+F2+F3）
*EN: 5. Format System (F1+F2+F3)*

```tie
// F1 自动表格：对象表 → 列宽自适应（i64 右对齐/string 左对齐）
> ps.list_processes() -> format_table()

// F2 自定义视图：闭包定制
> ps.list_processes() -> format(custom_view)

// F3 结构化输出：对象 → zd/json（通信用 zd，§1.4 决策）
> ps.list_processes() -> to_zd()
> ps.list_processes() -> to_json()
```

- F1 是默认输出（对象表自动格式化，PowerShell Format-Table 对标）
  EN: F1 is the default output (auto-format object tables; the PowerShell Format-Table counterpart).
- F2 用闭包（闭包模型 C2）
  EN: F2 uses closures (the C2 closure model).
- F3 衔接脚本管道（对象 → zd 持久化/传输）
  EN: F3 ties into the script pipeline (objects → zd persistence/transport).

## 6. 交互体验（I1+I2+I3）
*EN: 6. Interactive Experience (I1+I2+I3)*

```tie
// I1 行编辑 + 历史 + 多行
//    - 方向键历史/行内编辑（原始模式 + ANSI）
//    - 括号感知多行（parser 尝试解析，不完整则续行）
// I2 LSP 补全（tie-lsp 已有语义分析 → 命令/参数/变量补全）
// I3 ANSI 语法高亮（前置：ESC 转义词法支持，字符串模型待办）
```

- 补全复用 tie-lsp（待办 #2 LSP 增强）
  EN: Completion reuses tie-lsp (To-do #2: LSP enhancement).
- 高亮前置：词法层加 `\xHH` ESC 转义（ext/tui 升级同依赖）
  EN: Highlighting prerequisite: add `\xHH` ESC escapes at the lexer layer (the ext/tui upgrade shares this dependency).

## 7. 会话与配置（A1+A2）
*EN: 7. Session and Configuration (A1+A2)*

```tie
// A1 profile：~/.tie/profile.tie 启动自动执行（对标 PowerShell profile）
// A2 状态持久化：历史/别名/变量 → zd 存储（~/.tie/state.zd）
```

- profile 是 tie 脚本（语言 = shell 一致性）
  EN: A profile is a tie script (language = shell consistency).
- 状态用 zd（§1.4 通信用 zd 决策）
  EN: State uses zd (the §1.4 use-zd-for-communication decision).

## 8. 架构形态
*EN: 8. Architecture Shape*

```
┌─ tieconsole（shell 前端，tie 写）────────────────┐
│  命令解析（-> 管道）/ 补全(LSP) / 历史 / ANSI 高亮 │
├─ 命令层：cmdlet 预定义 + 包函数 + 外部进程         │
├─ 格式层：format_table / format / to_zd / to_json  │
├─ trm（tie 运行时套件，跨平台统一 API）───────────┤
│  终端（TTY/原始模式/ANSI）+ 进程流 + 文件/环境/会话 │
│  ↓ extern：Win32 / POSIX                          │
└───────────────────────────────────────────────────┘
```

## 9. 决策记录（讨论产物）
*EN: 9. Decision Record (Discussion Output)*

| 决策点 | 结论 | 备选（未选） |
| --- | --- | --- |
| 管道 | `->` 运算符（语言级，左结合最低优先级，三角色可区分） | `\|>`、`\|` 双轨 |
| 命令模型 | 预先定义：cmdlet 声明 + 内置命令集 + 包函数注册 | 运行时发现、纯函数即命令 |
| 跨平台层 | trm（tie 运行时套件，吸收 tucore，独立设计） | 并入 tucore |
| 格式 | F1 自动表格 + F2 自定义视图（闭包）+ F3 结构化输出（zd/json） | 单格式 |
| 交互 | I1 行编辑/历史/多行 + I2 LSP 补全 + I3 ANSI 高亮 | 纯文本 |
| 会话 | A1 profile 脚本 + A2 zd 状态持久化 | 无状态 |

EN: Decision table: pipeline via the `->` operator; command model via predefined cmdlet declarations + built-in set + package-fn registration; cross-platform layer via trm; format via F1 auto-table + F2 custom views + F3 structured output; interaction via I1 line-editing + I2 LSP completion + I3 ANSI highlighting; session via A1 profile scripts + A2 zd state persistence.

## 10. 待办
*EN: 10. To-Dos*

1. ~~**trm 设计**~~ **已落地**（2026-08-15）：tie 运行时套件，吸收 tucore，
   见 [trm-arch.md](trm-arch.md)
   EN: 1. ~~**trm design**~~ **landed** (2026-08-15): the tie runtime suite, absorbing tucore; see [trm-arch.md](trm-arch.md).
2. ~~**LSP 增强**~~ **已落地**（2026-08-15）：tsp（tie 语言服务器，R1 tie 重写 +
   全量 16 项能力），见 [tsp-lsp.md](tsp-lsp.md)
   EN: 2. ~~**LSP enhancement**~~ **landed** (2026-08-15): tsp (the tie language server; R1 tie rewrite + the full 16 capabilities); see [tsp-lsp.md](tsp-lsp.md).

## 11. 未决问题
*EN: 11. Open Questions*

1. **cmdlet 语法**：`cmd Name { param(...) ... }` 是语言新语法还是 namespace
   函数 + 元数据注释？（倾向：语言级 cmd 声明，编译器支持参数元数据）
   EN: **cmdlet syntax**: is `cmd Name { param(...) ... }` new language syntax or namespace functions + metadata annotations? (Leaning toward a language-level cmd declaration with the compiler supporting parameter metadata).
2. **管道输入类型**：`input` 特殊参数的静态类型（对象流 table<Obj>？泛型）
   EN: **Pipeline-input type**: the static type of the `input` special parameter (the object stream table<Obj>? generic?).
3. **ESC 转义前置**：词法层 `\xHH` 支持的排期（阻塞 I3 高亮与 ext/tui 升级）
   EN: **ESC-escape prerequisite**: the schedule for `\xHH` support at the lexer layer (blocks I3 highlighting and the ext/tui upgrade).
4. ~~**trm 与 tucore 的边界**~~ **已定案（2026-08-15）**：trm 吸收 tucore
   （tucore → trm.ui），trm = 单一运行时套件（见 [trm-arch.md](trm-arch.md)）
   EN: 4. ~~**trm/tucore boundary**~~ **settled (2026-08-15)**: trm absorbs tucore (tucore → trm.ui); trm = a single runtime suite (see [trm-arch.md](trm-arch.md)).
5. **外部进程命令的输出**：文本 → 对象转换（自动推断？还是手动 parse 函数）
   EN: **Output of external-process commands**: text → object conversion (auto-inference? or manual parse functions).