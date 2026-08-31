# tie:script——tie 脚本模块协议
*EN: tie:script — the tie script-module protocol*

> 状态：**已实现**（Harbor M2.2 引入模块协议基础，M3 起自举链路全面投入使用）
> 所属：tie 语言执行体系（解释器层）
> 一句话：**约定入口函数 + 字符串值直传调用**——让「tie 程序」能在宿主进程内被
> 动态注册、用源码文本当输入、拿文本当输出，从而用 tie 语言自身扩展 tie 工具链。

> EN: Status: **implemented** (Harbor M2.2 introduced the module-protocol foundation; from M3 the self-hosting chain puts it to full use)
> EN: Belongs to: the tie language execution system (interpreter layer)
> EN: In one sentence: **a conventional entry function + direct value-passing of a string** — letting a "tie program" be dynamically registered inside
> a host process, taking source text as input and producing text as output, thereby extending the tie toolchain with tie itself.

## 1. 它是什么
*EN: 1. What it is*

`tie:script` 是一份**模块执行协议**：约定一个 `.tie` 源文件可以作为「脚本模块」
在解释器会话（`tie_interp::Session`）中被动态加载与调用。核心只有两条：

EN: `tie:script` is a **module execution protocol**: it specifies that a `.tie` source file can be dynamically loaded
and invoked as a "script module" in an interpreter session (`tie_interp::Session`). The core consists of only two things:

1. **注册**：把模块源码整体交给 `eval` 执行，顶层 `func` / `namespace` 定义被
   收进会话的函数表（`funcs`），跨多次调用保持；
2. **调用**：用 `eval_call("入口函数全名", 文本)` 以**字符串值**直传一个字符串实参，
   拿回函数返回的字符串。

EN: 1. **Register**: hand the module source as a whole to `eval`; top-level `func` / `namespace` definitions are
   collected into the session's function table (`funcs`) and persist across multiple calls;
EN: 2. **Invoke**: call `eval_call("入口函数全名", 文本)` to pass a string argument directly as a **string value**,
   and get back the string the function returns.

协议本身不规定模块里写什么逻辑——它只提供「宿主（Rust 程序或另一个 tie 程序）
↔ tie 脚本」之间的**双向管道**，模块可以是转换器、分析器、代码生成器、
协议处理器……任何「一段文本进、一段文本出」的处理单元。

EN: The protocol itself does not dictate what logic the module contains — it only provides a **two-way pipe** between
the host (a Rust program or another tie program) and the tie script. A module can be a transformer, analyzer, code generator,
protocol handler, ... any unit that "takes a piece of text in and yields a piece of text out".

### 为什么用「字符串」作为协议边界
*EN: Why "string" is used as the protocol boundary*

- `eval_call` 的实参**直接绑定为字符串值**（`Value::Str`），不经源码文本转义——
  多行内容、引号、换行原样直传，不会出现「转义地狱」；
- 返回值同理：模块 `return` 一个字符串即完成输出（`void` 入口返回空串）；
- 跨语言边界零结构体依赖，协议文本（见 §4）可承载结构化数据。

- EN: the argument to `eval_call` is **bound directly as a string value** (`Value::Str`), not escaped through source text —
  multi-line content, quotes, and newlines pass through as-is, avoiding "escape hell";
- EN: the return value works the same way: a module `return`s a string and the output is complete (a `void` entry returns an empty string);
- EN: zero struct dependencies across language boundaries; the protocol text (see §4) can carry structured data.

### 三个落地场景（既有实现）
*EN: Three real-world scenarios (existing implementations)*

| 场景 | 位置 | 说明 |
| --- | --- | --- |
| 预处理器自举 | `prep/core.tie` + `tie-prep` Rust 壳 | 预处理核心逻辑全部 tie 语言化，Rust 仅解释执行（M3 阶段一） |
| CLI 转换器扩展 | `tie-prep --module <file.tie>` | 命令行挂载任意 tie 转换器，Rust 零改动（M3 阶段一） |
| 程序内动态执行 | tie 语言 `eval` / `eval_call` 内置函数 | REPL 与普通 tie 程序也能加载/调用模块（M2.2 起） |

EN: The table above (with Chinese descriptions) lists three existing real-world scenarios: preprocessing bootstrap (`prep/core.tie` + the `tie-prep` Rust shell, with the whole preprocessing core logic in tie and Rust only interpreting it, M3 phase one); CLI transformer extension (`tie-prep --module <file.tie>` mounting arbitrary tie transformers with zero Rust changes, M3 phase one); and in-program dynamic execution (the tie language `eval`/`eval_call` built-ins letting the REPL and ordinary tie programs load/invoke modules, since M2.2).

## 2. 核心机制
*EN: 2. Core mechanism*

### 2.1 `eval`——注册或执行的统一入口（`Session::eval`）
*EN: 2.1 `eval` — the unified entry for registration or execution (`Session::eval`)*

```
eval(代码字符串) -> 结果字符串
```

`Session::eval` 有两段逻辑（跟 REPL 一致）：

EN: `Session::eval` has two pieces of logic (consistent with the REPL):

1. **先尝试顶层解析**：如果代码是顶层定义（`func` / `namespace` / `class` / `import`），
   注册到会话状态（函数进 `funcs` 表并递归注册命名空间），返回
   `已定义 N 个函数`；
2. **否则按表达式/语句执行**：把代码自动包装成 `func main() { ... }` 执行，
   返回最终表达式的可打印字符串。

EN: 1. **Try top-level parsing first**: if the code is a top-level definition (`func` / `namespace` / `class` / `import`),
   register it into session state (functions go into the `funcs` table, namespaces registered recursively) and return
   `已定义 N 个函数`;
EN: 2. **Otherwise execute as an expression/statement**: the code is auto-wrapped into `func main() { ... }` and executed,
   returning the printable string of the final expression.

会话状态（`globals` + `funcs`）跨 `eval` 调用**持久保存**——先 `eval` 注册模块，
后 `eval_call` 调用，正是靠这一点。

EN: Session state (`globals` + `funcs`) is **persisted across** `eval` calls — registering a module via `eval` first
and then calling it via `eval_call` relies exactly on this.

### 2.2 `eval_call`——调用已注册函数（`Session::eval_call`）
*EN: 2.2 `eval_call` — invoking a registered function (`Session::eval_call`)*

```
eval_call(函数全名, 字符串参数) -> 结果字符串
```

行为约束（与 `tie_eval_call` C ABI 同源）：

EN: Behavioral constraints (same origin as the `tie_eval_call` C ABI):

1. **函数必须已注册**（否则报 `eval_call: 未定义的函数 'xxx'`）；
2. **形参约定**：必须恰好接收 1 个**字符串参数**（必选参数 ≤ 1；其余可以是带
   默认值的可选参数，默认值表达式在调用点补齐）。0 参函数或 2+ 必选参数 → 报错
   「必须恰好接收 1 个字符串参数」；
3. 实参**值直传**：第一个参数直接绑定 `Value::Str(arg)`；可选参数用其默认值求值补齐；
4. **命名空间支持**：入口函数可放在 `namespace` 里，用全名 `mod::upper` 调用
   （`::` 分隔）；函数体内部裸调用同样按该命名空间前缀补全；
5. **作用域隔离**：被调函数内声明的变量不污染调用者（新作用域 + `scope_base` 隔离）；
6. 返回：`return expr` → 值的可打印字符串；void（无返回）→ 空串。

EN: 1. **The function must be registered** (otherwise `eval_call: 未定义的函数 'xxx'` is reported);
EN: 2. **Parameter convention**: it must accept exactly 1 **string parameter** (required params ≤ 1; the rest may be
   optional params with defaults, whose default-value expressions are filled at the call site). A 0-param function or 2+ required params → error
   "必须恰好接收 1 个字符串参数";
EN: 3. arguments are **passed by value**: the first argument is bound directly to `Value::Str(arg)`; optional params are filled by evaluating their defaults;
EN: 4. **namespace support**: the entry function may live in a `namespace`, invoked by its full name `mod::upper`
   (separated by `::`); bare calls inside the function body are likewise completed with that namespace prefix;
EN: 5. **scope isolation**: variables declared inside the called function don't leak into the caller (a new scope + `scope_base` isolation);
EN: 6. return: `return expr` → the printable string of the value; void (no return) → empty string.

### 2.3 字符串值直传（关键设计）
*EN: 2.3 Direct string-value passing (a key design)*

`eval_call` 的实参**不是**把 `arg` 丢回一个解析器——它就是 `Value::Str` 本体。
所以：

EN: The argument to `eval_call` is **not** fed back into a parser — it is the `Value::Str` itself.
Therefore:

```
eval_call("process", "line1\nline2")   // 多行原样传入，无需转义
```

模块内部拿到的 `src` 是完整文本值，`str_len(src)` 是码点数、`str_char(src, i)` 逐字符
访问——与源码文本的字节/转义表示无关。

EN: Inside the module, the `src` received is a complete text value; `str_len(src)` gives the codepoint count
and `str_char(src, i)` accesses characters one by one — independent of the source text's byte/escape representation.

> 编码约定：`len` 返回 UTF-8 **字节数**（如 `len("你好") == 6`），`str_len` 返回
> **码点数**（如 `str_len("你好") == 2`）。`str_char` 按码点索引——含中文等
> 多字节字符的字符串，遍历边界必须用 `str_len`（用 `len` 会越界返回空串，
> 导致 trim 尾随空白残留、slice 截取错位）。

> EN: Encoding convention: `len` returns the UTF-8 **byte count** (e.g. `len("你好") == 6`), while `str_len` returns
> the **codepoint count** (e.g. `str_len("你好") == 2`). `str_char` indexes by codepoint — for strings containing multi-byte
> characters such as Chinese, traversal boundaries must use `str_len` (using `len` overflows and returns empty strings,
> leaving trailing whitespace after trim and misaligning slice cuts).

## 3. 模块约定
*EN: 3. Module conventions*

一个 tie:script 模块 = 任意 `.tie` 源文件，满足：

EN: A tie:script module = any `.tie` source file that satisfies:

### 3.1 入口约定
*EN: 3.1 Entry convention*

顶层必须有一个可被 `eval_call` 调用的入口函数，**约定名 `process`**：

EN: The top level must have an entry function callable via `eval_call`, **conventionally named `process`**:

```c
func process(src: string) -> string {
    // …对 src 做处理，返回字符串结果
}
```

- 入口名不强制为 `process`（`eval_call` 接受任意已注册函数名），但 `process` 是
  **框架/CLI 约定名**：`--module` 挂载与 `run_module` 都默认调 `process`；
- 入口也可以放进 `namespace`，用全名 `ns::process` 调用；
- void 入口允许（收到空串返回），适合「纯副作用」模块。

- EN: the entry name is not required to be `process` (`eval_call` accepts any registered function name), but `process` is
  the **framework/CLI conventional name**: both `--module` mounting and `run_module` call `process` by default;
- EN: the entry may also be placed in a `namespace`, invoked by its full name `ns::process`;
- EN: a void entry is allowed (it returns an empty string), suitable for "pure side-effect" modules.

### 3.2 自包含约束（重要）
*EN: 3.2 Self-containment constraint (important)*

**模块不能依赖 `import`**——解释器 `eval` 不支持 `import`（REPL v1 限制）。因此：

EN: **A module cannot rely on `import`** — the interpreter `eval` does not support `import` (a REPL v1 limitation). Therefore:

- 模块内部只能用**语言底座原语**（`str_char` / `str_len` / `len` / 字符串拼接 /
  `table_new_*` / 数学/文件等内嵌函数）；
- 需要字符串工具的模块需自备最小实现（如 `prep/core.tie` 内联
  `trim` / `slice` / `is_whitespace` 等，与 `std/string.tie` 等价但不 import）。
- 字符串**码点级**遍历必须用 `str_len`（码点数）做边界：`len` 返回 UTF-8 字节数，
  `str_char` 按码点索引——中文等多字节字符下两者不等，用 `len` 做循环上界会
  越界返回空串导致 trim 尾随空白残留、slice 截取错乱（修复见 prep/core.tie）。

- EN: inside a module, only **language-base primitives** (`str_char` / `str_len` / `len` / string concatenation /
  `table_new_*` / built-in math, file, and other functions) can be used;
- EN: modules needing string utilities must supply their own minimal implementations (e.g. `prep/core.tie` inlines
  `trim` / `slice` / `is_whitespace` etc., equivalent to `std/string.tie` but without importing).
- EN: **codepoint-level** string traversal must use `str_len` (codepoint count) as the boundary: `len` returns the UTF-8 byte count
  and `str_char` indexes by codepoint — the two differ for multi-byte characters such as Chinese; using `len` as the loop upper bound
  overflows and returns empty strings, leaving trailing whitespace after trim and misaligning slice cuts (fixed in prep/core.tie).

这是有意的设计取舍：模块**自包含** → 单文件即可运行 → 携带部署成本最低。

EN: This is a deliberate design trade-off: a **self-contained** module → runs as a single file → lowest portability and deployment cost.

### 3.3 最小示例
*EN: 3.3 Minimal example*

```c
// upper.tie —— 全部转大写（示意）
func process(src: string) -> string {
    var n: i64 = len(src)
    var out: string = ""
    var i: i64 = 0
    while i < n {
        var c: string = str_char(src, i)
        // 简化示例：仅转小写字母（'a'..'z'）
        if c >= "a" && c <= "z" {
            out = out + str_char("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 字符位置)
        } else {
            out = out + c
        }
        i = i + 1
    }
    return out
}
```

（生产示例见 `prep/indent.tie`：制表符 → 4 空格的缩进规范模块。）

EN: (For a production example, see `prep/indent.tie`: an indentation-normalizing module that converts tabs → 4 spaces.)

## 4. 协议文本格式（`prep` 专用）
*EN: 4. Protocol text format (for `prep`)*

`prep/core.tie` 的 `process` 返回**协议文本**，Rust 壳解析后还原预处理结果。
格式（每行一条，`\n` 结尾）：

EN: `prep/core.tie`'s `process` returns **protocol text**, which the Rust shell parses to restore the preprocessing result.
Format (one entry per line, ending in `\n`):

```text
ROLE:logic            ← 第 1 行：角色（type/script/data/ui/class/logic/port/db）
BODY:12               ← 第 2 行：正文码点数（str_len 语义，按 Unicode 码点计数）
<正文恰好 12 个码点>   ← 剩余恰好 m 个码点的正文（可含换行/任意内容）
```

声明错误时首行为 `ERROR:<message>`（Rust 壳检测后报出）。

EN: On a declaration error the first line is `ERROR:<message>` (reported by the Rust shell after detection).

- **正文按码点数精确截取**：不按行、不按 `\n` 拆分，正文内的任何字符都不会
  破坏协议（这是 `BODY:<m>` 用码点计数而不是行数的原因）；
- Rust 壳（`parse_protocol`）逐行识别 `ERROR:` / `ROLE:` / `BODY:` 前缀，其余内容
  全部视为正文，直到取够 `m` 个码点（`chars().take(m)`）；
- **旧头部指令已移除**：`HEADERS:` / `H:` 行随 `// tie:xxx` 注释指令体系一并删除——
  优化级别/编译目标不再进预处理协议（`opt`/`target` 仅 CLI），文件类型由头部
  `type tie` / `type tie<X>` 声明行表达。
- 编码约定：BODY 声明的是**码点数**而非字节数。字符串是 UTF-8 编码，
  `len` 返回字节数、`str_len`/`str_char` 按码点索引——中文等多字节字符下
  字节数 ≠ 码点数（一个汉字 3 字节、1 码点），字符串遍历必须用 `str_len`
  做边界，否则中文文本会错位（trim 尾随空白残留、slice 截取错乱等）。

- EN: **the body is truncated precisely by codepoint count**: it is not split by lines or `\n`, and no character inside the body can break
  the protocol (this is why `BODY:<m>` counts codepoints instead of lines);
- EN: the Rust shell (`parse_protocol`) recognizes the `ERROR:` / `ROLE:` / `BODY:` prefixes line by line; everything else is
  treated as body until `m` codepoints are taken (`chars().take(m)`);
- EN: **old header directives have been removed**: `HEADERS:` / `H:` lines were deleted together with the `// tie:xxx` comment-directive system —
  optimization level / compile target no longer enter the preprocessing protocol (`opt`/`target` are CLI-only), and the file kind is expressed by the header
  `type tie` / `type tie<X>` declaration line.
- EN: encoding convention: BODY declares **codepoint count**, not byte count. Strings are UTF-8 encoded;
  `len` returns the byte count and `str_len`/`str_char` index by codepoint — under multi-byte characters such as Chinese,
  byte count ≠ codepoint count (one Chinese character is 3 bytes but 1 codepoint). String traversal must use `str_len`
  as the boundary, otherwise Chinese text becomes misaligned (trailing whitespace remains after trim, slice cuts misalign, etc.).

> 为何输出协议文本而非结构化对象：`eval_call` 只能返回一个字符串。
> 文本协议是「字符串为边界的互通」的自然延伸（对齐 §1 的设计）。

> EN: Why emit protocol text instead of a structured object: `eval_call` can only return a string.
> A text protocol is the natural extension of "interoperability bounded by strings" (aligned with the §1 design).

## 5. 三层调用入口
*EN: 5. Three layers of invocation entry points*

tie:script 模块可以从三个层面被调用：

EN: A tie:script module can be invoked from three layers:

### 5.1 `Rust 侧`：`tie_prep::run_module`
*EN: 5.1 `Rust side`: `tie_prep::run_module`*

```rust
// tie-prep 内部：加载模块源码 → 注册 → 以字符串直传入口调用
pub fn run_module(module_source: &str, entry: &str, source: &str) -> Result<String, String> {
    let mut session = tie_interp::Session::new();
    session.eval(module_source)?;      // 注册模块顶层定义
    session.eval_call(entry, source)   // 字符串值直传调用
}
```

`tie-prep` 的 `preprocess()` 就用它执行 `prep/core.tie`：

EN: `tie-prep`'s `preprocess()` uses it to run `prep/core.tie`:

```rust
let text = run_module(PREP_MODULE, "prep::process", &source)
    .unwrap_or_else(|e| panic!("预处理模块执行失败: {e}"));
parse_protocol(&text)   // 解析协议文本 → PreprocessResult
```

### 5.2 `CLI 侧`：`tie-prep --module`
*EN: 5.2 `CLI side`: `tie-prep --module`*

```bash
tie-prep <input.tie> --module <module.tie>
# 读出模块文件 → run_module(module_src, "process", 源码)
# 模块返回文本原样写 stdout，[tie-prep] 诊断写 stderr
```

验证（`prep/indent.tie`，VSCode 缩进规范化转换器）：

EN: Verification (`prep/indent.tie`, a VSCode indentation-normalizing transformer):

```bash
tie-prep examples/hello.tie --module prep/indent.tie
```

**扩展性证明**：新增一种「源文本转换器」 = 新增一个 `.tie` 模块文件，
`--module` 挂载即可——**不用改 Rust、不用重编工具链**。

EN: **Proof of extensibility**: adding a new "source-text transformer" is just adding a `.tie` module file
and mounting it via `--module` — **no Rust changes, no toolchain recompilation**.

### 5.3 `tie 程序/REPL 侧`：内置 `eval` / `eval_call`
*EN: 5.3 `tie program / REPL side`: built-in `eval` / `eval_call`*

tie 语言把 `eval` / `eval_call` 作为**内置函数**暴露（编译与解释路径都支持，
通过 tie-interp C ABI 桥，见 §6）：

EN: tie exposes `eval` / `eval_call` as **built-in functions** (supported in both the compiled and interpreted paths,
via the tie-interp C ABI bridge; see §6):

```c
// 例子：名字包装器
var module = "func process(src: string) -> string {\n    return \"[\" + src + \"]\"\n}\n"
var reg = eval(module)                 // 注册 → "已定义 1 个函数"
var out = eval_call("process", "hi")   // "[hi]"
```

- `eval(code)`：注册或执行（与 §2.1 共识相同），返回结果字符串；
- `eval_call(name, arg)`：调用已注册函数，返回结果字符串；
- 命名空间全名 / void 入口行为见 §2.2；
- 端到端验证见 `examples/script_demo.tie`：
  - 多行字符串直传（`line1\nline2`），不被转义；
  - 命名空间入口（`mod::upper`）；
  - void 入口 → 空串。

- EN: `eval(code)`: registers or executes (same consensus as §2.1), returning the result string;
- EN: `eval_call(name, arg)`: invokes a registered function, returning the result string;
- EN: namespace full-name / void-entry behavior: see §2.2;
- EN: end-to-end verification: see `examples/script_demo.tie`:
  - EN: multi-line strings passed directly (`line1\nline2`), not escaped;
  - EN: namespace entry (`mod::upper`);
  - EN: void entry → empty string.

## 6. 编译路径与 C ABI 桥
*EN: 6. Compiled path and the C ABI bridge*

tie-llvm（编译路径）与 tie-interp（解释路径）共享同一套 `eval`/`eval_call`
语义，编译路径通过 interp 静态库（`tie_interp.lib`）的 C 导出实现：

EN: tie-llvm (compiled path) and tie-interp (interpreted path) share the same `eval`/`eval_call`
semantics; the compiled path implements them via the C exports of the interp static library (`tie_interp.lib`):

| 导出符号 | 作用 | 谁调用 |
| --- | --- | --- |
| `tie_eval_expr(code)` | 求值一段代码（回到 Session::eval） | IR 的 `eval(...)` 调用 |
| `tie_eval_call(name, arg)` | 调用已注册函数（Session::eval_call） | IR 的 `eval_call(...)` 调用 |
| `tie_free_result(p)` | 释放解释器返回的堆字符串 | IR 每次调用后清理 |

EN: The table above (with Chinese descriptions) lists the C exports: `tie_eval_expr(code)` evaluates a piece of code (back to Session::eval), called by the IR's `eval(...)`; `tie_eval_call(name, arg)` invokes a registered function (Session::eval_call), called by the IR's `eval_call(...)`; and `tie_free_result(p)` frees heap strings returned by the interpreter, called by IR after each invocation.

IR 生成逻辑（`crates/tie-llvm/src/ir.rs`）：

EN: IR generation logic (`crates/tie-llvm/src/ir.rs`):

- 内置 `eval` → `mark_used("tie_eval_expr")` + `tie_free_result`；
- 内置 `eval_call` → `mark_used("tie_eval_call")` + `tie_free_result`；
- 只有用到才 declare（`declare ptr @tie_eval_expr(ptr)` 等），未用不引入符号；
- 返回的堆指针按语义是否消费区分：非尾部表达式调用后立即 `tie_free_result`，
  尾部结果返回给调用方（由调用方释放）——REPL 会话级小泄漏可忽略。

- EN: built-in `eval` → `mark_used("tie_eval_expr")` + `tie_free_result`;
- EN: built-in `eval_call` → `mark_used("tie_eval_call")` + `tie_free_result`;
- EN: declared only when used (e.g. `declare ptr @tie_eval_expr(ptr)`); unused symbols are not introduced;
- EN: returned heap pointers are distinguished by whether the semantics consume them: after a non-tail expression call, `tie_free_result`
  runs immediately; a tail result is returned to the caller (released by the caller) — a small session-level leak in the REPL is negligible.

> 因此 tie 程序**编译运行**（`tie xxx.tie`）时也能用 `eval` / `eval_call`——
> `examples/script_demo.tie` 就是编译运行的端到端验证。

> EN: Therefore a tie program **compiled and run** (`tie xxx.tie`) can also use `eval` / `eval_call` —
> `examples/script_demo.tie` is the compiled-and-run end-to-end verification.

## 7. 设计约束与限制
*EN: 7. Design constraints and limitations*

| 项 | 说明 |
| --- | --- |
| 模块不能 import | interp `eval` 不支持 import（REPL v1 局限）→ 模块必须自包含 |
| 类不支持 | `eval` 顶层 `class` 会拒绝（「REPL v1 暂不支持类定义」） |
| 函数参数约束 | 入口恰好 1 个必选字符串参数（可带可选参数） |
| 字符串边界 | 传输物是字符串：跨层结构化数据需自定文本协议（如 §4） |
| 无模块持久性 | `run_module` 每次新建 `Session`；跨调用持久化只存在于同一进程的同一 Session 内 |
| 错误传播 | 模块内错误（未定义函数/参数不符/求值错误）→ `eval_call` 返回 `Err`，
   `run_module` 透传；编译期调用方用 `?` 或 panic 处理 |

EN: The table above (with Chinese descriptions) lists design constraints: a module cannot `import` (interp `eval` doesn't support import, a REPL v1 limitation) and must therefore be self-contained; classes are unsupported (a top-level `class` in `eval` is rejected); the entry takes exactly 1 required string parameter (optional parameters allowed); the transport is a string, so cross-layer structured data needs a self-defined text protocol (e.g. §4); there is no module persistence (`run_module` creates a fresh `Session` each time, so cross-call persistence exists only within the same `Session` in the same process); and errors inside a module make `eval_call` return `Err`, which `run_module` passes through, with the compile-time caller handling via `?` or panic.

## 8. 影响范围与相关文件
*EN: 8. Scope of impact and related files*

| 组件 | 位置 | 说明 |
| --- | --- | --- |
| 协议定义 | 本文件（docs/tie-script.md） | 约定 + 三层调用入口 |
| interp API | crates/tie-interp/src/lib.rs | `Session::eval` / `Session::eval_call` |
| 内置函数 | 同 lib.rs `call_fn` 分发 | tie 语言的 `eval` / `eval_call` |
| C 桥 | lib.rs `#[no_mangle]` 导出的 `tie_eval_expr` / `tie_eval_call` / `tie_free_result` | 编译路径复用 |
| Rust 壳 | crates/tie-prep/src/preprocess.rs | `run_module` + `parse_protocol` |
| 核心模块 | prep/core.tie | 自举的预处理模块（tie 语言） |
| 转换器示例 | prep/indent.tie | 制表符 → 4 空格的独立转换器 |
| 端到端验证 | examples/script_demo.tie | 程序内动态 eval / eval_call |

EN: The table above (with Chinese descriptions) maps the scope: the protocol definition is this file (docs/tie-script.md) covering the conventions and three invocation entry points; the interp API is in crates/tie-interp/src/lib.rs (`Session::eval` / `Session::eval_call`); the built-in functions live in the same lib.rs `call_fn` dispatch; the C bridge is the `#[no_mangle]`-exported `tie_eval_expr` / `tie_eval_call` / `tie_free_result`, reused by the compiled path; the Rust shell is crates/tie-prep/src/preprocess.rs (`run_module` + `parse_protocol`); the core module is prep/core.tie (the self-hosting preprocessing module in tie); the transformer example is prep/indent.tie (a standalone converter from tabs → 4 spaces); and end-to-end verification is via examples/script_demo.tie (dynamic eval / eval_call inside a program).

## 9. 相关文档
*EN: 9. Related documentation*

- [docs/language.md](language.md) §2.4：预处理自举（协议文本 + eval_call 用法）
- [docs/plans/](plans/)：后续里程碑规划
- [CHANGELOG.md](../CHANGELOG.md)：[Harbor M2.2]（协议基础）与 [M3]（自举/挂载入口）

- EN: [docs/language.md](language.md) §2.4: preprocessing bootstrap (protocol text + eval_call usage)
- EN: [docs/plans/](plans/): future milestone planning
- EN: [CHANGELOG.md](../CHANGELOG.md): [Harbor M2.2] (protocol foundation) and [M3] (self-hosting/mount entries)