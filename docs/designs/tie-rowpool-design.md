# tie 行池 —— table<R> 结构化行池（设计定案 v0.1）

*EN: tie row pool — table<R> structured row pool (design v0.1, finalized)*

## 定位 / Positioning

新语言能力（ROAD **p.9.12.6**），解决 tiu 落地坑 #1「表元素仅内建类型，无 struct 数组」：
现有规避是手写「列式平行表 + 对象池」（如 tiu DrawList 一列一列 push、Paint/Path 池
逐列登记），样板重且易错。本设计把该模式**语法化为语言一级能力**：`table<R>`（R 为
struct）由编译期拒绝改为支持，成为**按 id 稀疏寻址的结构化行池**。

*EN: New language capability (ROAD p.9.12.6) fixing tiu gotcha #1 (tables hold only builtin
element types — no struct arrays). Current escape is hand-written "columnar parallel tables +
object pools" (tiu DrawList pushing one column at a time, Paint/Path pools). This design lifts
that idiom into the language: `table<R>` (R a struct) changes from compile-time rejection to a
supported **id-addressable sparse row pool**.*

## 语义定案 / Semantics (frozen)

* `table<R>`（R 为 struct）声明一个**行池**：每行是一个 R 的**值**，以 i64 **id（下标）**寻址，允许稀疏。

* 写 `rows[id] = r`：id 为负 → 编译/运行期诊断（复用 p.9.12.2 负下标裁决，不作静默）；
  id ≥ `len(rows)` → **整行自动扩容**到 `id+1`（新增空行用 R 的字段默认值/零值填充——
  底层单列越界自动扩已由 p.9.12.2 提供，此处扩展为**行级原子扩**：所有字段列同步扩），
  然后逐字段写入。复写 `rows[id] = r2` 覆盖该行。

* 读 `var r = rows[id]`：返回 R **值**（逐字段拷贝；id ≥ len 返回「字段默认值构造的行」，
  与既有越界读返零语义一致）；`len(rows)` = 最大写过 id + 1（各字段列恒齐平）。

* 行是值语义：`rows[a] = rows[b]` 逐字段拷贝，互不影响。

*EN: `table<R>` (R a struct) is a row pool: each row is a value of R addressed by i64 id
(sparse allowed). Write `rows[id]=r`: negative id diagnosed; id≥len auto-grows the whole row
to id+1 (rows filled with R's field defaults — single-column auto-grow from p.9.12.2 extended
to row-atomic growth across all columns), then field-wise write; overwrite replaces the row.
Read `r=rows[id]` returns an R value (field-wise copy; out-of-range returns a default-filled
row, consistent with existing out-of-range read). `len(rows)` = max written id+1 (columns stay
aligned). Rows are value semantics: `rows[a]=rows[b]` is a field-wise copy.*

## 语法与存储 / Syntax & storage

* 语法零新增关键字：复用 `table<R>`。元素类型首版仅限 **struct**（字段类型可为内建/表/
  引用）。类型编码天然可表达（table 段 = 1<<40 | 元素 id，元素为 struct id = 3<<40|idx）。

* 存储：编译期把 `table<R>` 变量降为 R 各字段的**平行列**（每字段一根 `table<i64|f64|string|bool>`，
  加上共享行数），列式 SoA，与 tiu 手写 DrawList 同构但由语言生成。行池变量的表示 = 多列
  指针聚合（字段列各自独立 ptr），替代现有「单表 ptr」假设——**首版行池仅存在于符号存储位**，
  表达式上的行池值不做面向值传递（见边界）。

* 读写发射：写 = 逐字段 `set`（越界先扩全列再写）；读 = 逐字段取 + 聚合构造 R。

*EN: Zero new keywords — reuse `table<R>`. Element type v1: struct only (fields may be
builtin/table/ref). Type encoding is naturally expressible (table = 1<<40 | elem id). Storage:
a `table<R>` variable lowers to per-field parallel columns (columnar SoA, same shape as tiu's
hand-written DrawList but language-generated). Representation = multi-column pointer aggregate.
Row-pool values exist only in symbol storage; no by-value row-pool passing (see bounds).*

## 边界 / Bounds (v1 not supported)

* 嵌套 `table<StructWithTable>` 中的外层仍可（字段可为表），但**嵌套表本身再作行池**（
  `table<table<…>>` 元素是 table 而非 struct）不支持；
* `table<R>` 作**函数返回值 / ref 形参** / 传入导出边界（FFI/tink）不支持（行池是编译期
  降形，无运行期值形态）；
* `table_push` / 表字面量 / 数组推导式作用于行池 → 诊断（行池无"追加"概念，只有按 id 写）；
* `map<struct>` 不做；并发跨线程归 trm-lite 引用计数约定。

*EN: v1 NOT supported: nested row-pool (element-of-table is a table, not a struct);
table<R> as function return value / ref parameter / FFI-tink boundary (row pool lowers at
compile time, no runtime value form); table_push / table literals / comprehensions on a row
pool (diagnose — a row pool has no "append", only id-writes); map<struct>; cross-thread
concurrency follows trm-lite ref-count conventions.*

## 验收 / Acceptance

* 探针矩阵：写读回环、稀疏大 id（如写 id=1000 后 len=1001 且 0..999 为默认行）、零行、
  多字段类型（i64/f64/string/bool/表字段）、复写覆盖、`rows[a]=rows[b]` 值拷贝、
  负下标写拒绝、读越界返回默认行；
* 既有非 struct 元素表（`table<i64>` 等）行为零变化（p.9.12.2 扩容语义保持）；
* 自举两阶段不动点 + 回归基线不劣化（test-diagcodes FAILS=7 / regress-s21 159P·6F·2S / regress-m5 8P·0F）。

*EN: probe matrix (write/read roundtrip, sparse large id with default-filled predecessors,
zero rows, mixed field types incl. table field, overwrite, value copy between rows, negative-id
rejection, out-of-range read default row); no behavior change for existing non-struct tables;
self-host fixed point + regression baselines unchanged.*