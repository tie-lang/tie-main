# 确定性 / 可复现构建审计（T0.2）
*EN: Deterministic / Reproducible Build Audit (T0.2)*

> 目的：自举 v2 计划（`.omo/plans/self-hosting-v2.md`）要求新编译器（tiec）两轮编译输出逐字节一致（**G2 Gate**），并产出可复现 `.exe`。本审计排查所有可能破坏确定性的因素，为 T0.5（map 排序二分）与 T3.3（可复现构建）提供证据清单。
> 方法：只读调查 + 临时目录实验。**未修改任何 crates/、std/、ext/ 源码。**
> 基准：当前工作区状态（`git status` 显示 `crates/tie-frontend/src/semantic.rs`、`crates/tie-interp/src/lib.rs` 有未提交修改，行号按当前工作区计）。
> 结论速览：编译期（IR 文本 / `.exe`）**零熵源、顺序稳定**；两处破坏点均为 **REPL 路径**（map 打印顺序、`rand/time` 运行时输出）；`.exe` 复现需补 `-Wl,/BREPRO`。

EN: Purpose: The self-hosting v2 plan (`.omo/plans/self-hosting-v2.md`) requires the new compiler (tiec) to produce byte-for-byte identical output across two compilation runs (**G2 Gate**) and to produce a reproducible `.exe`. This audit examines every factor that could break determinism, providing an evidence checklist for T0.5 (map sorted binary search) and T3.3 (reproducible builds).
EN: Method: read-only investigation + experiments in a temporary directory. **No source under crates/, std/, ext/ was modified.**
EN: Baseline: current workspace state (`git status` shows uncommitted changes in `crates/tie-frontend/src/semantic.rs` and `crates/tie-interp/src/lib.rs`; line numbers are counted against the current workspace).
EN: Quick summary: at compile time (IR text / `.exe`) there are **zero entropy sources and stable ordering**; both defect points are on the **REPL path** (map print order, `rand`/`time` runtime output); reproducible `.exe` output requires adding `-Wl,/BREPRO`.

---

## (a) map / 表迭代顺序依赖
*EN: (a) Map / Table Iteration Ordering Dependency*

### 调查方法
*EN: Investigation Method*

1. `grep Value::Map|HashMap|RandomState` 定位 `crates/tie-interp/src/lib.rs` 全部 map 使用点，逐个读源码确认是否遍历输出。
2. `grep HashMap|BTreeMap|.keys()|.values()|.iter()` 扫描 `crates/tie-frontend/src/semantic.rs`、`crates/tie-llvm/src/ir.rs`，确认哪些是"查表"、哪些是"遍历输出"。
3. `grep map`（含 `*.tie`）扫描 `std/`、`ext/`、`pkg/` 中的 tie 语言级键值表用法。
4. 通读 `ir.rs` 的模块头/函数发射/renumber 三处主输出路径，确认迭代来源。

EN: 1. Use `grep Value::Map|HashMap|RandomState` to locate all map use sites in `crates/tie-interp/src/lib.rs`, and read each source to confirm whether it outputs by iterating.
EN: 2. Use `grep HashMap|BTreeMap|.keys()|.values()|.iter()` to scan `crates/tie-frontend/src/semantic.rs` and `crates/tie-llvm/src/ir.rs`, confirming which are "lookups" and which are "iterate-and-output".
EN: 3. Use `grep map` (including `*.tie`) to scan tie-language-level key-value table usage in `std/`, `ext/`, and `pkg/`.
EN: 4. Read through the three main output paths of `ir.rs` — module header, function emission, and renumber — to confirm the iteration source.

### 证据
*EN: Evidence*

**① REPL 路径（不稳定点）：interp 的 `Value::Map` = 默认 RandomState 的 Rust HashMap**

EN: ① REPL path (unstable point): interp's `Value::Map` = a Rust HashMap with default RandomState

`crates/tie-interp/src/lib.rs:3694-3697`：

```rust
/// 键值表（E3）：键恒为字符串，值为任意类型
Map(std::collections::HashMap<String, Value>),
```

默认 `HashMap` 使用 `RandomState`，**每次进程随机种子** → 迭代顺序既非插入序也非排序，且每次运行不同。

EN: The default `HashMap` uses `RandomState`, **a per-process random seed** → the iteration order is neither insertion order nor sorted order, and it differs on every run.

**② map 打印/序列化（唯一遍历输出点）**

EN: ② map printing / serialization (the only iterate-and-output point)

`crates/tie-interp/src/lib.rs:3743-3750`（`to_print_string`，`println` 路径）：

```rust
// 键值表：输出键值集合（仅 REPL 展示）
Value::Map(m) => format!(
    "{{{}}}",
    m.iter()
        .map(|(k, v)| format!("{k}: {}", v.to_print_string()))
        .collect::<Vec<_>>()
        .join(", ")
),
```

`crates/tie-interp/src/lib.rs:3755-3760`（`to_repl_string`，REPL 结果展示）：

```rust
pub fn to_repl_string(&self) -> String {
    match self {
        Value::Bool(b) => if *b { "true" } else { "false" }.to_string(),
        other => other.to_print_string(),
```

→ map 走 `to_print_string` 同一遍历路径，同样不稳定。

EN: → the map goes through the same `to_print_string` iteration path, likewise unstable.

**③ map 字面量构造（顺序无关，但打印仍受 RandomState 影响）**

EN: ③ map literal construction (order-independent, but printing is still affected by RandomState)

`crates/tie-interp/src/lib.rs:2330-2340`：

```rust
if has_str_id {
    let mut m = std::collections::HashMap::new();
    for cell in cells {
        let Some(TableId::Str(key)) = &cell.id else { ... };
        let v = self.eval_expr(&cell.value)?;
        m.insert(key.clone(), v);
    }
    Ok(Value::Map(m))
```

**④ 编译路径（tie-llvm）：无任何 map 遍历输出 —— 顺序稳定**

EN: ④ compile path (tie-llvm): no map iteration output at all — ordering is stable

- 函数发射按 AST 源码顺序：`ir.rs:183-189` `for stmt in &self.program.stmts`；命名空间递归 `gen_ns_fns` 同按 stmts（`ir.rs:503-521`）；全局变量按 stmts（`ir.rs:471-496`）。**全部 Vec 顺序，非 HashMap 顺序。**
- `renumber_ir` 按文本行序处理，HashMap 仅作 `%N → %N'` 查表：`ir.rs:4323-4374`（`for line in ir.lines()` + `map.entry(n).or_insert_with(...)` 按首次出现分配），不遍历输出。
- `used_externs` 是 `Vec<String>`（`ir.rs:73/98`，`mark_used` 去重收集，`ir.rs:4558`）→ 按首次使用顺序。
- ir.rs 全部 HashMap 用法均为 `.get()` 按键查表（`fmt_cache`/`ty_cache`/`scope`/`sigs`/`sem.*`，如 `ir.rs:474/659/901/1925/2097`），**零 `.iter()` 输出**。
- 编译路径中 map 是 `DynTable`（`tie_map_new/get/set/get_string/set_string`，`lib.rs:739-834`）：`tie_map_set`（`lib.rs:794-810`）键存在覆盖原位置、不存在**追加到末尾** → **插入顺序存储** + 线性查找。tie 语言**没有** map 遍历/序列化原语 → 编译产物不含 map 顺序信息。

EN: - Function emission follows AST source order: `ir.rs:183-189` `for stmt in &self.program.stmts`; the namespace recursion `gen_ns_fns` likewise follows stmts (`ir.rs:503-521`); globals follow stmts too (`ir.rs:471-496`). **All Vec order, not HashMap order.**
EN: - `renumber_ir` processes in text-line order; the HashMap only serves as a `%N → %N'` lookup: `ir.rs:4323-4374` (`for line in ir.lines()` + `map.entry(n).or_insert_with(...)` assigned on first appearance); no iteration-based output.
EN: - `used_externs` is a `Vec<String>` (`ir.rs:73/98`; `mark_used` collects with dedup, `ir.rs:4558`) → in first-use order.
EN: - All HashMap usage in ir.rs is `.get()` key-based lookup (`fmt_cache`/`ty_cache`/`scope`/`sigs`/`sem.*`, e.g. `ir.rs:474/659/901/1925/2097`), **zero `.iter()` output**.
EN: - On the compile path the map is `DynTable` (`tie_map_new/get/set/get_string/set_string`, `lib.rs:739-834`): `tie_map_set` (`lib.rs:794-810`) overwrites an existing key in place and **appends a new key to the end** → **insertion-order storage** + linear search. The tie language has **no** map iteration/serialization primitive → the compiled output contains no map-order information.

**⑤ 语义层（tie-frontend）HashMap：查表为主，一处迭代与输出无关**

EN: ⑤ semantic layer (tie-frontend) HashMap: lookup-oriented; the single iteration is irrelevant to output

`crates/tie-frontend/src/semantic.rs:35-59`：`funcs`/`expr_types`/`tables`/`table_vars`/`classes`/`fn_full_names`/`resolved_calls`/`globals` 均为 HashMap。语义层不产文本；IR 侧全部按键查表。
唯一迭代：`semantic.rs:736` `let names: Vec<String> = self.result.classes.keys().cloned().collect();`（拍平 struct 用）。拍平每个 struct 独立递归（`flatten_struct`），**结果与迭代顺序无关**；错误一次性报告，不构成字节依赖。

EN: In `crates/tie-frontend/src/semantic.rs:35-59`, `funcs`/`expr_types`/`tables`/`table_vars`/`classes`/`fn_full_names`/`resolved_calls`/`globals` are all HashMaps. The semantic layer produces no text; the IR side does key-based lookups only.
EN: The only iteration: `semantic.rs:736` `let names: Vec<String> = self.result.classes.keys().cloned().collect();` (used for flattening structs). Each struct is flattened in an independent recursion (`flatten_struct`), so **the result is independent of iteration order**; errors are reported all at once and do not form a byte dependency.

**⑥ tie 语言级 map（std/ext/pkg）：无遍历打印逻辑**

EN: ⑥ tie-language-level map (std/ext/pkg): no iterate-and-print logic

`grep map`（含 `*.tie`）结果：`std/` 全部文件 **零 map 匹配**；`ext/registry.tie`、`pkg/*.tie` 零 map 匹配；`ext/ml.tie:118-123` 的 `depth_map` 实为 `table_new_i64()`（动态表 Vec，顺序稳定）；唯一 map 演示 `examples/table_enhance_demo.tie` 只按键取值（`symtab["main"]`），不遍历打印。

EN: `grep map` (including `*.tie`) results: all `std/` files have **zero map matches**; `ext/registry.tie` and `pkg/*.tie` have zero matches; the `depth_map` in `ext/ml.tie:118-123` is actually `table_new_i64()` (dynamic table Vec, stable order); the only map demo `examples/table_enhance_demo.tie` only does key-based looks-up (`symtab["main"]`), no iterate-and-print.

**⑦ tie-lsp（非 G2 范围，备注）**：`crates/tie-lsp/src/diagnostics.rs:738` `for name in sem.classes.keys()` 遍历 HashMap 输出补全/诊断 → 补全列表顺序不稳定，但 LSP 是交互服务，不参与编译字节一致。

EN: ⑦ tie-lsp (out of G2 scope, for the record): `crates/tie-lsp/src/diagnostics.rs:738` has `for name in sem.classes.keys()` iterating a HashMap to emit completions/diagnostics → the completion list order is unstable, but LSP is an interactive service and is not part of compile byte-identity.

### 影响评估
*EN: Impact Assessment*

| 点 | 破坏字节一致（G2 .ll/.exe）？ | 影响列号/错误文本对齐？ | 影响 REPL golden（G3）？ | 影响可复现 .exe？ |
|---|---|---|---|---|
| interp `to_print_string` map 分支（3744-3750） | **否**（编译路径不走 REPL 展示） | 否 | **是**：REPL 中打印 map 每次运行顺序不同 | 否 |
| interp `to_repl_string`（3756） | 否 | 否 | **是**（同上，map 转 print） | 否 |
| 编译路径 DynTable map（739-834） | 否（插入序 + 无遍历输出，确定性） | 否 | 否 | 否 |
| semantic/ir 的 HashMap 查表 | **否**（无遍历输出，IR 发射全按 AST 顺序） | 否 | 否 | 否 |
| std/ext/pkg 无 map | — | — | — | — |
| tie-lsp diagnostics.rs:738 | 否（非编译产物） | 否 | 否（非编译产物） | 否 |

EN: Impact of each point on byte-identity (G2 .ll/.exe), column/error-text alignment, REPL golden (G3), and reproducible .exe.

**结论**：当前 Rust 编译器对同一输入生成的 `.ll`/`.exe` **不受 map 顺序影响**（G2 无直接障碍）；唯一 map 顺序不稳定点是 **interp REPL 路径的 map 打印**（影响 G3 REPL parity，而非 G2）。但注意——**tie 新编译器（T1.3 起）符号表按计划使用 `map<i64,i64>`**，未来 tiec 内部一旦出现"迭代 map 输出"（错误消息收集、IR 生成、`llvmgen`），就会引入随机顺序；`map` 改排序二分（T0.5）后 tie 语言级 map 为排序迭代，可根治。

EN: **Conclusion**: the current Rust compiler's `.ll`/`.exe` for the same input is **not affected by map order** (no direct G2 obstacle); the only map-order-unstable point is **map printing on the interp REPL path** (affects G3 REPL parity, not G2). But note — **the new tie compiler's symbol table (from T1.3) plans to use `map<i64,i64>`**; should any "iterate-map-and-output" (error-message collection, IR generation, `llvmgen`) appear inside the future tiec, it would introduce random ordering. Once `map` is changed to a sorted binary search (T0.5), the tie-language-level map iterates in sorted order, which fundamentally fixes this.

### 结论 / 建议（调用点清单，交 T0.5）
*EN: Conclusion / Recommendations (call-site checklist, hand off to T0.5)*

需要改为排序迭代的调用点：

EN: Call sites that must be changed to sorted iteration:

1. **[R1] `crates/tie-interp/src/lib.rs:3744-3750`** `to_print_string` 的 `Value::Map` 分支 —— `m.iter()` 改按键排序（收集 `Vec<(&k,&v)>` 后 `sort_by`，或直接改用 `BTreeMap`）；此为 **REPL map 打印顺序不稳定根因**。
2. **[R2] `crates/tie-interp/src/lib.rs:3755-3760`** `to_repl_string` —— 经 R1 修复后自动稳定（map 走 print），无需单独改；确认即可。
3. **[R3] 未来 tiec（T2.8 `llvmgen` / T2.6 semantic）**：符号表若迭代输出，一律排序迭代或维护有序结构；错误消息收集顺序固定为源码顺序（按 span）而非 map 顺序。
4. **[R4] `crates/tie-frontend/src/semantic.rs:736`** `classes.keys()` —— 当前无输出依赖，**无需改**；若未来按 struct 名顺序输出诊断才需排序（备注即可）。
5. **[R5] `crates/tie-lsp/src/diagnostics.rs:738`**（非 G2）—— 补全列表顺序可排序，低优先级。

EN: 1. **[R1] `crates/tie-interp/src/lib.rs:3744-3750`** the `Value::Map` branch of `to_print_string` — change `m.iter()` to sort by key (collect a `Vec<(&k,&v)>` then `sort_by`, or directly switch to `BTreeMap`); this is the **root cause of unstable REPL map print order**.
EN: 2. **[R2] `crates/tie-interp/src/lib.rs:3755-3760`** `to_repl_string` — becomes stable automatically once R1 is fixed (the map goes through print); no separate change needed; confirm only.
EN: 3. **[R3] future tiec (T2.8 `llvmgen` / T2.6 semantic)**: if the symbol table iterates for output, always use sorted iteration or maintain an ordered structure; keep error-message collection order fixed to source order (by span) rather than map order.
EN: 4. **[R4] `crates/tie-frontend/src/semantic.rs:736`** `classes.keys()` — currently no output dependency, **no change needed**; sorting is only required if future diagnostics are emitted in struct-name order (note only).
EN: 5. **[R5] `crates/tie-lsp/src/diagnostics.rs:738`** (not in G2) — the completion list order can be sorted; low priority.

已经稳定、无需处理：ir.rs 函数/全局发射（AST 顺序）、`renumber_ir`（文本序）、`used_externs`（Vec 首次使用序）、编译路径 DynTable map（插入序，无遍历原语）、std/ext/pkg（无 map 遍历）。

EN: Already stable, no action needed: ir.rs function/global emission (AST order), `renumber_ir` (text order), `used_externs` (Vec first-use order), the compile-path DynTable map (insertion order, no iteration primitive), and std/ext/pkg (no map iteration).

---

## (b) Rust semantic span 列号语义
*EN: (b) Rust semantic span column-number semantics*

### 调查方法
*EN: Investigation Method*

读 `crates/tie-frontend/src/lexer.rs` 的字符消费与列号递增逻辑；grep 全部 `col` 修改点；对照 span 测试断言。

EN: Read the character-consumption and column-advancement logic of `crates/tie-frontend/src/lexer.rs`; grep all `col` modification sites; cross-check the span test assertions.

### 证据
*EN: Evidence*

**① 词法源是 Unicode 标量迭代器（char，非字节）**

EN: ① The lexical source is a Unicode scalar iterator (char, not bytes)

`crates/tie-frontend/src/lexer.rs:300-307`：

```rust
pub struct Lexer<'a> {
    /// 源码字符序列
    chars: std::iter::Peekable<std::str::Chars<'a>>,
    /// 当前行号（从 1 开始）
    line: u32,
    /// 当前列号（从 1 开始）
    col: u32,
```

**② 列号递增唯一位置：每消费一个 char 加 1（码点计数）**

EN: ② The only place columns advance: +1 per consumed char (codepoint count)

`crates/tie-frontend/src/lexer.rs:387-397`：

```rust
/// 消费一个字符并推进行列号。
fn consume_char(&mut self) -> Option<char> {
    let c = self.chars.next()?;
    if c == '\n' {
        self.line += 1;
        self.col = 1;
    } else {
        self.col += 1;
    }
    Some(c)
}
```

grep 确认全文 `col` 修改点**仅此一处**（`lexer.rs:392` 换行重置、`lexer.rs:394` 每次 +1）。

EN: grep confirms the `col` modifications across the whole file are **only this one place** (`lexer.rs:392` resets on a newline; `lexer.rs:394` +1 each time).

**③ 测试佐证（1-based，ASCII 下与视觉列一致）**

EN: ③ Test evidence (1-based; matches the visual column under ASCII)

`crates/tie-frontend/src/lexer.rs:1241-1246`：

```rust
assert_eq!((toks[0].span.line, toks[0].span.col), (1, 1), "var");
assert_eq!((toks[1].span.line, toks[1].span.col), (1, 5), "x");   // var + 空格 = 4 → x 在 5
assert_eq!((toks[2].span.line, toks[2].span.col), (2, 1), "补出的分号");
```

### 影响评估
*EN: Impact Assessment*

**列号 = Unicode 码点计数（`char` 单位，1-based），不是字节偏移（UTF-8 字节数）。** 一个中文字符（UTF-8 占 3 字节）在 Rust lexer 中只占 **1 列**。

EN: **Column = Unicode codepoint count (`char` units, 1-based), not a byte offset (UTF-8 byte count).** A Chinese character (3 UTF-8 bytes) occupies only **1 column** in the Rust lexer.

| 影响 | 结论 |
|---|---|
| 破坏字节一致（G2）？ | 否（.ll/.exe 不含列号） |
| 影响列号对齐（错误文本 `@行:列` 逐字一致）？ | **是，且是决定性基准**：tiec（T2.4 全量 lexer、T2.6 semantic）的错误消息必须按 **码点列** 计列号，才能与 Rust 逐字一致 |
| 影响可复现 .exe？ | 否 |

EN: Impact summary: byte-identity (G2) and reproducible .exe are unaffected; column alignment of error text (`@line:col`) is affected and is the decisive baseline.

### 结论 / 建议
*EN: Conclusion / Recommendations*

- Rust 基准语义：`@行:列` 的 `列` = **该字符在行内的 Unicode 码点序号（1-based）**，`行` = 换行数 + 1（1-based）。
- **新 lexer（T1.1/T2.4）必须按码点计列**，不能按 UTF-8 字节偏移；`str_len` 语义（BODY 码点约定）与列号计数一致，可复用同一编码约定（见计划 §3.5 与 `docs/plans/self-hosting.md` BODY 码点数说明）。
- 错误消息 golden（T2.7）会自然覆盖多字节列号场景：建议在 golden 语料中加入含中文/emoji 标识符或注释的触发样例，锁定码点列行为。

EN: - Rust baseline semantics: in `@line:col`, `col` = **the character's Unicode codepoint index within the line (1-based)**, and `line` = newline count + 1 (1-based).
EN: - **The new lexer (T1.1/T2.4) must count columns by codepoint**, not by UTF-8 byte offset; the `str_len` semantics (BODY codepoint convention) are consistent with column counting, so the same encoding convention can be reused (see plan §3.5 and the BODY codepoint-count note in `docs/plans/self-hosting.md`).
EN: - The error-message golden (T2.7) naturally covers multi-byte column scenarios: it is recommended to add triggering samples containing Chinese/emoji identifiers or comments to the golden corpus, to lock in codepoint-column behavior.

---

## (c) 可复现链接
*EN: (c) Reproducible Linking*

### 调查方法
*EN: Investigation Method*

工具链查找（PATH → `D:\LLVM\bin` → `C:\Program Files\LLVM\bin` → `C:\LLVM\bin`）→ 版本确认 → 帮助搜索可复现标志 → **临时目录实际编译实验**（`C:\Users\Jiro\AppData\Local\Temp\opencode\reprotest\`，文件可留）。

EN: Toolchain lookup (PATH → `D:\LLVM\bin` → `C:\Program Files\LLVM\bin` → `C:\LLVM\bin`) → version confirmation → search help for reproducibility flags → **actual compilation experiments in a temporary directory** (`C:\Users\Jiro\AppData\Local\Temp\opencode\reprotest\`, files may be kept).

### 工具链（本机实测）
*EN: Toolchain (measured on this machine)*

```
clang version 18.1.8
Target: x86_64-pc-windows-msvc
InstalledDir: D:\LLVM\bin            # PATH 与 D:\LLVM\bin 均命中
opt (LLVM 18.1.8, Optimized build, Host CPU: alderlake)
lld is a generic driver → 实际走 lld-link (Windows 风格)
```

### 可复现标志搜索结果
*EN: Reproducibility-Flag Search Results*

| 工具 | 标志 | 结果 |
|---|---|---|
| `clang --help` | `--no-insert-timestamp` / `/BREPRO` | **均无**（clang 驱动层不提供；链接器标志需 `-Wl,` 透传） |
| `clang --help` | `-fbuild-session-timestamp=<sec>`（GCC 风格） | 存在，未实测（`/BREPRO` 已足够） |
| `lld-link --help` | `/BREPRO` / `/timestamp` | 帮助文本中未搜到（但实测可用，见下） |
| `ld.lld --help` | `--no-insert-timestamp` / `--reproduce` | 仅 `--reproduce=<file>`（调试 tar 包，非时间戳修复） |

EN: Search results of reproducibility flags across clang, lld-link, and ld.lld on this machine (LLVM 18.1.8).

### 实测实验记录（临时目录 `C:\Users\Jiro\AppData\Local\Temp\opencode\reprotest\`）
*EN: Record of Measured Experiments (temp dir `C:\Users\Jiro\AppData\Local\Temp\opencode\reprotest\`)*

最小 IR `min.ll`（`printf` + `main`），同一输入，各实验两次编译（间隔 3 秒模拟真实二次构建），比较 sha256：

EN: Minimal IR `min.ll` (`printf` + `main`); with the same input, each experiment is compiled twice (3 seconds apart to simulate a real second build) and the sha256 is compared:

| 实验 | 命令 | sha256(A) | sha256(B) | 相等 |
|---|---|---|---|---|
| **A 默认链接** | `clang min.ll -o a1.exe` / `-o a2.exe` | `FB3F2E81...B282` | `A75D610C...FDA3` | **否**（PE 链接时间戳随墙钟变化） |
| **B `/BREPRO`** | `clang min.ll -o b1.exe -Wl,/BREPRO` / `-o b2.exe` | `2DDAC94C...3049` | `2DDAC94C...3049` | **是 ✓**（可运行，输出 `Hello, world!`） |
| **C `/timestamp:0`** | `clang min.ll -o c1.exe -Wl,/timestamp:0` / `-o c2.exe` | `89E49E39...930` | `4EE83301...9F9` | 否（`LNK4044: 无法识别的选项 /timestamp:0`，无效） |
| **D opt 确定性** | `opt -O2 -S min.ll -o d1.opt.ll` / `-o d2.opt.ll` | `31C34B54...9D04` | `31C34B54...9D04` | **是 ✓**（IR 优化确定） |
| **E clang -c** | `clang -c min.ll -o e1.o` / `-o e2.o` | `17C2A2AC...D49` | `49171C14...564` | **否**（COFF `TimeDateStamp` 秒级差异：`0x6A797DC2` vs `0x6A797DC5`，`llvm-readobj --file-headers` 确认） |
| **F llvm-ar** | `llvm-ar rcs f1.a e1.o` / `-o f2.a`（同一 .o） | `FEA3969C...812F` | `FEA3969C...812F` | **是 ✓** |
| **G SOURCE_DATE_EPOCH=0** | `clang -c min.ll -o g1.o/g2.o`（SDE=0） | `B18DCF27...88FD` | `53F5D3C8...D51` | 否（SDE 不修复 COFF 对象时间戳） |
| **I 不同 .o → /BREPRO exe** | 用 E 的不同 e1.o/e2.o 分别 `clang <o> -o i1.exe -Wl,/BREPRO` | `2DDAC94C...3049` | `2DDAC94C...3049` | **是 ✓**（/BREPRO 重写/忽略输入对象时间戳） |

EN: Experiment results: default linking and `clang -c` are not reproducible (timestamps); `/BREPRO`, `opt -O2`, and `llvm-ar` produce identical sha256.

### 影响评估
*EN: Impact Assessment*

| 项 | 结论 |
|---|---|
| 默认链接是否带时间戳？ | **是**（PE 头时间戳随墙钟变化 → 两次构建 `.exe` 不同） |
| `/BREPRO` 是否可用？ | **可用且已验证**：两次 sha256 一致；不同 `.o` 输入下最终 `.exe` 仍一致；程序正常可运行 |
| 破坏字节一致（G2）？ | 当前 Rust 编译器 `.exe` 构建（`backend.rs link`）**未传 `/BREPRO`** → 两次链接不同 → 阻碍 `.exe` 字节一致（`.ll` 不受影响，见 (d)） |
| 影响列号对齐？ | 否 |

EN: Default linking embeds a wall-clock timestamp; `/BREPRO` is available and verified; the current `.exe` build does not pass `/BREPRO`, blocking byte-identity (`.ll` is unaffected).

### 结论 / 建议
*EN: Conclusion / Recommendations*

- **本机（LLVM 18.1.8 / lld-link）可复现标志为 `-Wl,/BREPRO`**（等价固定/归零时间戳 + 确定性输出），`/timestamp:0` 不可用，`SOURCE_DATE_EPOCH` 不修复 COFF 对象文件。
- **T3.1/T3.3 必须在链接命令加 `-Wl,/BREPRO`**：`crates/tie-llvm/src/backend.rs` `link()`（45-76 行，`clang input.ll -o output.exe`）补 `-Wl,/BREPRO`；`compile_object`（81-100）与 `archive`（105-115）的 `.o/.a` 中间产物为秒级时间戳差异，但已验证**不影响 `/BREPRO` 链接的最终 `.exe` 字节**，静态库路径（linklib）如需字节复现再补 `-fbuild-session-timestamp=0`（未实测，标记为可选项）。
- **G2 判定建议**：`.ll` 文本以 `--emit-ir` 输出 diff；`.exe` 以 sha256 判定（必须在 `/BREPRO` 生效后）。

EN: - **On this machine (LLVM 18.1.8 / lld-link) the reproducibility flag is `-Wl,/BREPRO`** (equivalent to fixing/zeroing the timestamp + deterministic output); `/timestamp:0` is unavailable and `SOURCE_DATE_EPOCH` does not fix COFF object files.
EN: - **T3.1/T3.3 must add `-Wl,/BREPRO` to the link command**: add `-Wl,/BREPRO` to `link()` in `crates/tie-llvm/src/backend.rs` (lines 45-76, `clang input.ll -o output.exe`); the `.o`/`.a` intermediates from `compile_object` (81-100) and `archive` (105-115) differ at second-level timestamps, but are verified **not to affect the final `.exe` bytes under `/BREPRO` linking**; if the static library path (linklib) also needs byte-level reproducibility, add `-fbuild-session-timestamp=0` (not measured; marked as optional).
EN: - **G2 verdict suggestion**: diff the `.ll` text via `--emit-ir` output; judge the `.exe` via sha256 (only after `/BREPRO` is live).

---

## (d) 熵源
*EN: (d) Entropy Sources*

### 调查方法
*EN: Investigation Method*

`grep rand_range|SystemTime|time|date|timestamp|env::|source_filename` 扫描 `crates/tie-interp` 与 `crates/tie-llvm`；确认 RandomState 使用面；读 driver.rs 的 .ll 写出路径。

EN: Use `grep rand_range|SystemTime|time|date|timestamp|env::|source_filename` to scan `crates/tie-interp` and `crates/tie-llvm`; confirm the RandomState usage surface; read the .ll write path in driver.rs.

### 证据
*EN: Evidence*

**① 运行时随机：`rand_range` = 系统时间播种的 xorshift（不参与编译期）**

EN: ① Runtime randomness: `rand_range` = xorshift seeded from system time (not involved at compile time)

`crates/tie-interp/src/lib.rs:241-265`：

```rust
thread_local! {
    static RNG_STATE: std::cell::Cell<u64> = std::cell::Cell::new(seed_rng());
}
/// 从当前时间（纳秒）初始化 RNG 种子
fn seed_rng() -> u64 {
    let t = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_nanos() as u64).unwrap_or(0);
    if t == 0 { 1 } else { t }
}
```

`tie_rand_range`（`lib.rs:272-281`）：`min + (next_rand() % span)`。→ **系统时间播种，两次运行不同序列**。但这是 **运行时 C ABI 桥**；编译路径 IR 侧仅发射 `call i64 @tie_rand_range(...)`（`ir.rs:3222-3243`），**编译期不调用、不进 IR 文本**。

EN: `tie_rand_range` (`lib.rs:272-281`): `min + (next_rand() % span)`. → **seeded from system time; a different sequence across two runs**. But this is a **runtime C ABI bridge**; on the compile path the IR side only emits `call i64 @tie_rand_range(...)` (`ir.rs:3222-3243`), **not called at compile time and not placed in the IR text**.

**② 哈希 RandomState：默认随机种子（仅经 map 打印泄漏）**

EN: ② Hash RandomState: default random seed (only leaks via map printing)

interp：`Value::Map`（`lib.rs:3697`）、REPL 作用域栈（`lib.rs:1679/1782/1964/1977/2182/3638`）、`globals`/`funcs`（`lib.rs:1581-1583`）、消息字典 `dict`（`lib.rs:334`，仅 `insert`/`get` 查表，`lib.rs:362/377/382`，不遍历）—— 全部默认 `RandomState`。
semantic/ir 的 HashMap（见 (a)）同样 RandomState，但全部按键查表、零遍历输出。
→ 随机种子唯一可观察出口 = **REPL 的 map 打印**（(a) R1/R2）。

EN: interp: `Value::Map` (`lib.rs:3697`), the REPL scope stack (`lib.rs:1679/1782/1964/1977/2182/3638`), `globals`/`funcs` (`lib.rs:1581-1583`), and the message dictionary `dict` (`lib.rs:334`, only `insert`/`get` lookups at `lib.rs:362/377/382`, no iteration) — all default `RandomState`.
EN: The semantic/ir HashMaps (see (a)) are likewise RandomState, but all do key-based lookups with zero iterate-and-output.
EN: → the only observable exit of the random seed = **REPL map printing** ((a) R1/R2).

**③ 时间戳：IR 模块头无时间戳（硬编码常量）**

EN: ③ Timestamps: the IR module header has no timestamp (hard-coded constant)

`crates/tie-llvm/src/ir.rs:113-116`：

```rust
fn run(&mut self) -> Result<(), IrError> {
    // 模块头
    self.out.push_str("; ModuleID = 'tie'\n");
    self.out.push_str("source_filename = \"input.tie\"\n\n");
```

- **推翻任务"已知线索"**：`source_filename` 不是 driver 传入的输入文件名，而是**硬编码常量 `"input.tie"`** → 不含绝对路径、不含时间。`.ll` 文本完全确定（实验 D 佐证：`opt` 对确定性输入两次输出一致；IR 源本身亦无随机）。
- `tie_time_now`（`lib.rs:229-235`，SystemTime Unix 秒）为运行时桥，不进 IR。
- grep 确认 ir.rs 无 `SystemTime`/`env!`/`file!()`/`current_dir` 出现在 IR 生成路径。

EN: - **Refutes the task's "known clue"**: `source_filename` is not the driver-supplied input filename but a **hard-coded constant `"input.tie"`** → it contains no absolute path and no time. The `.ll` text is fully deterministic (supported by experiment D: `opt` produced identical output twice on a deterministic input; the IR source itself also has no randomness).
EN: - `tie_time_now` (`lib.rs:229-235`, SystemTime Unix seconds) is a runtime bridge and does not enter the IR.
EN: - grep confirms ir.rs has no `SystemTime`/`env!`/`file!()`/`current_dir` appearing in the IR generation path.

**④ 环境变量 / 路径泄漏：`.ll` 文件名含用户路径，内容不含**

EN: ④ Env-var / path leakage: the `.ll` filename contains the user path; the content does not

`crates/tie-llvm/src/driver.rs:191`：`let ir_path = opts.input.with_extension("ll");` → `.ll` **文件落盘位置/文件名**继承用户输入路径，但 `.ll` **内容**（ModuleID/source_filename/符号/常量）不含路径。编译错误消息（`读取源码失败:`/`[后端]` 等）可能含路径字符串，但只进 stderr、不进 `.ll`/`.exe` 字节。

EN: `crates/tie-llvm/src/driver.rs:191`: `let ir_path = opts.input.with_extension("ll");` → the `.ll` **on-disk location/filename** inherits the user's input path, but the `.ll` **content** (ModuleID/source_filename/symbols/constants) contains no path. Compile error messages (`读取源码失败:`/`[后端]` etc.) may contain a path string, but they only go to stderr, not into the `.ll`/`.exe` bytes.

### 影响评估
*EN: Impact Assessment*

| 熵源 | 编译期（.ll/.exe 字节）？ | 运行期 / REPL？ |
|---|---|---|
| `rand_range` 系统时间播种（xorshift） | **无影响**（编译期不调用） | **影响**：含 `rand_range` 的 REPL 会话行输出不确定 → G3 golden 需按计划掩码 |
| `time_now`（SystemTime） | 无影响（不进 IR） | 影响：同上，golden 掩码 |
| HashMap RandomState 随机种子 | 无影响（零遍历输出，见 (a)） | 影响：仅 REPL map 打印（R1/R2） |
| IR 时间戳 / source_filename | **零熵**（硬编码常量） | — |
| 路径/环境泄漏 | 零（`.ll` 内容无路径；文件名不影响内容） | 编译错误消息含路径，与字节一致无关 |

EN: Entropy-source impact: none at compile time (.ll/.exe bytes); runtime/REPL is affected by `rand_range`, `time_now`, and RandomState printing (needs golden masking / R1/R2).

### 结论 / 建议
*EN: Conclusion / Recommendations*

- **编译期零熵源**：`.ll` 文本确定性已由"硬编码模块头 + AST 顺序发射 + 文本序 renumber"三重保证；`.exe` 确定性唯一缺口是链接时间戳 → 由 (c) 的 `-Wl,/BREPRO` 关闭。
- **G2 门无需处理随机**：`rand_range`/`time_now`/RandomState 均不进入 tiec 编译期输出。
- **G3 REPL parity**：含 `rand_range`/`time_now` 的 golden 行必须在 golden 文件中掩码（计划 T4.3 已注明）；REPL 打印 map 的稳定性依赖 (a) R1。
- **tie 新编译器侧（T1.3/T2.6 符号表 `map<i64,i64>`）**：符号表若用 tie 语言级 map 且未来需要迭代输出，必须依赖 T0.5 的排序 map（或用 `map<i64,i64>` 的下标访问而非遍历）；避免在 tiec 内部引入"插入序遍历 + 输出"组合。

EN: - **Zero entropy sources at compile time**: the `.ll` text determinism is guaranteed by the triple of "hard-coded module header + AST-ordered emission + text-order renumber"; the only remaining gap for `.exe` determinism is the link timestamp → closed by (c)'s `-Wl,/BREPRO`.
EN: - **The G2 gate needs no randomness handling**: `rand_range`/`time_now`/RandomState do not enter tiec's compile-time output.
EN: - **G3 REPL parity**: golden lines containing `rand_range`/`time_now` must be masked in the golden file (already noted in plan T4.3); the stability of REPL-printed maps depends on (a) R1.
EN: - **New-tie-compiler side (T1.3/T2.6 symbol table `map<i64,i64>`)**: if the symbol table uses a tie-language-level map and later needs iteration-for-output, it must rely on T0.5's sorted map (or use index access of `map<i64,i64>` instead of iteration); avoid introducing an "insertion-order iteration + output" combination inside tiec.

---

## 附录：变更后的建议联动点
*EN: Appendix: Suggested Linkage Points After the Changes*

- **T0.5（map 排序二分）**：消费 (a) R1/R2 调用点清单；`tie_map_set` 追加语义 → 二分插入（`lib.rs:794-810` 改 `memmove` 保序），`map_find_index`（`lib.rs:739-752`）改二分 + `strcmp` 直比；REPL 打印顺序随之变排序，与编译路径 DynTable 顺序语义统一（插入序 → 排序序需在 T0.5 行为测试中记录）。
- **T3.3（可复现构建）**：消费 (c) 结论 —— `backend.rs link()` 加 `-Wl,/BREPRO`；`selfhost-gate.ps1` 的 sha256 判定在 `/BREPRO` 生效后进行。
- **T2.4/T2.6（错误对齐）**：消费 (b) 结论 —— 码点列计数；golden 语料加多字节样例。

EN: - **T0.5 (map sorted binary search)**: consumes the (a) R1/R2 call-site checklist; `tie_map_set` append semantics → binary insertion (`lib.rs:794-810` changed to `memmove` to keep order); `map_find_index` (`lib.rs:739-752`) changed to binary search + direct `strcmp`; the REPL print order then becomes sorted, unified with the compile-path DynTable ordering semantics (insertion-order → sorted-order needs to be recorded in the T0.5 behavior tests).
EN: - **T3.3 (reproducible builds)**: consumes the (c) conclusion — add `-Wl,/BREPRO` to `backend.rs link()`; run `selfhost-gate.ps1`'s sha256 judgement after `/BREPRO` is live.
EN: - **T2.4/T2.6 (error alignment)**: consumes the (b) conclusion — codepoint-column counting; add multi-byte samples to the golden corpus.