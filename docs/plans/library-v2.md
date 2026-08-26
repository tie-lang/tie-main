# 规划：三层内置库重写（library-v2）——新特性 + 统一风格 + 全新接口

> 状态：**规划（待确认）**
> 范围：`std/`（34 模块）+ `ext/`（12 顶层 + 4 子目录模块）+ `rdu/`（7 模块）全量重写
> 动机：Harbor preview.4/5 落地了一批新语言特性（泛型、`ref table` 参数、struct 命名空间方法、
> `Result/Option`、switch 模式匹配、命名元组）；而三层库大量接口仍是旧编译器约束下的妥协形态
> （逗号字符串编码表传参、`max_i/max_f` 成对、冗余前缀、重复别名）。本规划用新特性重写三层库，
> 统一风格，**接口全新设计**（破坏性变更，消费者同步更新）。
>
> 三层库定位不变：`std/` 无状态纯函数工具（可走堆）、`ext/` 有状态/应用级、`rdu/` 嵌入式无栈纯标量。
> 本规划只改接口形态与实现风格，不改变各层定位与不变量（rdu 无栈纪律保持不变）。

---

## 0. 实施纪要（2026-08-26：与编译器的差异修正与接口定稿）

实施过程中与编译器能力实测差异，均已落在最终代码：

| 项 | 原设计 | 实施定稿 | 原因 |
| --- | --- | --- | --- |
| enum payload 白名单 | `bytes.read` / `fs.read_bytes` / `fs.read_lines` / `csv.read` 返回 `Result<table<T>, string>` | 改回 `table<T>`（空表=失败哨兵，原语义）；仅 `Result<string,string>`（fs.read_text）/ `Result<i64,string>`（json.parse_file）可表达 | 编译器中 `enum` 变体 payload 白名单只允许整数族/bool/char/trit/**string**；table/f64 作 payload 编译即报错（scollect_port collect_enum_variants）。**编译器限制，未在本期放开** |
| rdu/crc 状态构造 | `new()` 分别返回 Crc8/16/32/Fnv1a（重载） | `crc8_new()/crc16_new()/crc32_new()/fnv1a_new()` + `*_update(s, byte) -> S` + `*_value(s) -> i64`（CRC 终值异或并入 value） | tie 无函数重载，同名不同返回类型不可行 |
| rdu/rnd 状态推进 | `new(seed)/next(r)/value(r)` 三个命名 | 与设计一致（`new/next/value` + 裸 lcg 保留） | . |
| exmath.huffman_build | `-> table<i64>` | `-> table<string>` | 霍夫曼表实际是「字符\|编码串」字符串表，`table<i64>` 破坏算法 |
| graph.bellman_ford | 语义不变 | 输入由三元组边表改为 n×n 邻接矩阵（无边=999） | 与 graph 其他算法统一为矩阵约定 |
| sort 原地写法 | `ref table` 直接 push/下标写 | 内部新建局部表操作，函数末尾 `t = 局部表` 重绑定写回 | 编译器后端对 ref 实参直接 push 的 IR 存在越界 bug（store ptr 误判），局部表 + ref 重绑定等效原地修改 |
| 泛型模板体整数字面量 | `abs<T>` 写 `x < 0` | `var tz = x - x`（T 型零值） | 模板体内整数字面量单态化时类型固化（T=f64 时 0 仍 i64，比较类型不匹配） |
| 编译器泛型修复 | 泛型函数在命名空间/跨文件不可用 | 已修复并自举不动点通过 | sinfer（命名空间分支补 `gt_find`）+ irgen_call（mangled 全名不再二次加前缀），tiec→tiec2→tiec3 逐字节一致 |

> 设计其余各节与上表无冲突，各模块接口以最终 `.tie` 源码为准。

---

## 1. 新特性采用矩阵（每个特性解决哪个旧痛点）

| 新特性 | 解决的旧妥协 | 涉及模块 |
| --- | --- | --- |
| 泛型 `<T>` | `max_i/max_f`、`abs/abs_f`、`clamp/clamp_i` 成对重复；`expect_eq/expect_str_eq/expect_float_eq` 三份 | std/math、rdu/math、ext/test |
| `ref table<T>` 参数 | 表数据被迫编码成**逗号分隔字符串**传参（sort/graph/linalg/exmath/optsearch/ml），
  函数内 parse 再 serialize 的样板代码 | std/sort、graph、linalg、exmath、optsearch、random、crypto、
  bytes、db、set、collection | 
| struct + 命名空间方法 | 状态（CRC/PRNG）裸 `i64` 手传，无类型区分；调用方持状态模式可读性差 | rdu/crc、rdu/rnd |
| `Result<T, E>` | 读取类函数失败用**空表/空串/哨兵 -1** + 全局 `err_msg()`，失败信息与值混用 | std/fs、json、bytes、csv |
| 类型标注补充 | 大量 `table` 参数/返回无元素类型标注（弱类型），调用方不知道里面装什么 | std/bytes、crypto、db、collection、set、format、ext/log、ext/ml、vecsearch、pretty、test、tui、cache |
| 去冗余前缀 | `fixed_mul` 在 `rdu_fixed` 命名空间内仍带 `fixed_` 前缀；`csv_*`、`table_to_data_*` 同 | rdu/fixed、std/csv、std/db |
| 去重复别名 | `fs.read_to_string/read_text`、`write/write_text`、`append/append_text`、`remove_file/delete`、
  `remove_dir_all/remove_all`、`string.clone/copy`、`http.url_encode` 与 `encoding.url_encode` 重复 | std/fs、std/string、std/http |

## 2. 三层统一风格约定（新代码一律遵守）

1. **命名空间 = 模块名**（std/ext）；rdu 保留 `rdu_*` 前缀命名空间（避免与 std/ext 撞名）；
2. **命名空间内函数无模块前缀**（`fixed_mul` → `mul`、`csv_read` → `read`、`table_to_data_i64` → `to_data_i64`）；
3. **一语义一名**：重复别名删除，不保留兼容别名（v1 无外部用户）；
4. **表参数/返回必须标注元素类型**：`table<i64>` / `table<string>` / `table<f64>`，绝不写裸 `table`；
5. **表数据不再编码成字符串**：凡数据形态是「数字序列/矩阵/样本集」的，一律用真表参数；
6. **失败路径**：读取类（返回数据）用 `Result<T, string>`；写/删类（原 bool）保持 bool；
   纯状态型保持 bool/i64 哨兵（如 is_file/exists）；
7. **成对数值函数泛型化**：运算符（`<` `-` 等）在 T 上可用的（i64/f64 语义一致）合并为泛型；
   语义有差异的（整数除 vs 浮点除）保留独立函数并加显式类型后缀（如 `avg_f`、`pow_i`）；
8. **入口注释统一**：文件头注释含「文件角色 / 模块定位 / 调用示例」三段；修改历史不进库文件；
9. **rdu 无栈纪律不变量保持不变**：零原语、零动态内存、无递归、无全局状态、`.a` 零运行时依赖
   （struct 是值类型、无堆，引入 struct 不违反纪律，规划 §5 明示）。

## 3. 泛型与 struct 的两个样板（新写法参照）

### 3.1 泛型数值函数（std/math、rdu/math）

```tie
// 泛型：abs/max/min/clamp 同时服务 i64 与 f64，调用点单态化
pub func max<T>(a: T, b: T) -> T {
    if a > b { return a }
    return b
}
pub func abs<T>(x: T) -> T {
    if x < 0 { return -x }   // i64/f64 均支持比较与取负，语义一致
    return x
}
```

注意：`avg_f` 保留（`(a+b)/2.0` 对 i64 是整除，语义不同）；`pow_i` 保留（浮点幂语义不同）。

### 3.2 struct 状态封装（rdu/crc、rdu/rnd）

```tie
// rdu 无栈纪律下 struct = 纯标量值类型（i64 字段），无堆、无运行时，仍满足 freestanding
struct Crc32 { var v: i64 = 0 }
namespace rdu_crc {
    // 实例方法（首参接收者，按引用）；值语义返回新状态，调用方回写
    pub func update(c: Crc32, byte: i64) -> Crc32 { ... }
    pub func value(c: Crc32) -> i64 { return c.v ^ 0xFFFFFFFF }   // crc32_final 语义并入 value
}
// 调用：c = rdu_crc.update(c, b)（方法转发写法 obj.update(b) 亦可，见 §语言规范）
```

--- 

## 4. std/ 逐模块新接口（34 模块）

> 表列「变更」：`★`接口破坏性变化（消费者要改）、`◎`仅类型标注/风格、`--` 保持。

### 4.1 文本 `string / ascii / utf / bytes / format / regex / json / csv / encoding`

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `string` | `trim / trim_start / trim_end / slice(s, st, ed) / contains(s, sub) / find(s, sub) / starts_with / ends_with / replace / split / to_upper / to_lower / join(items: table<string>, sep) / repeat / clone`。**删除 `copy`**（与 clone 重复）。**编译器依赖，其余签名保持** | ★删 copy、◎join 类型化 |
| `ascii` | 不变（已是统一风格） | -- |
| `utf` | 不变（**编译器依赖**） | -- |
| `bytes` | `read(path) -> Result<table<i64>, string>`、`write(path, t: table<i64>) -> bool`、`concat(a: table<i64>, b: table<i64>) -> table<i64>`、`bit_read(t: table<i64>, pos) -> i64`、`bit_write(t: table<i64>, pos, bit) -> bool`、`to_ascii(t: table<i64>) -> string`、`from_ascii(s) -> table<i64>` | ★read 返回 Result、◎类型化 |
| `format` | `format_int / format_pad / format_int_hex / format_bool(b) / sprintf(fmt, args: table)`。**改名 `format(b: bool)` → `format_bool`**（与 format_int 前缀区分、消除裸名歧义） | ★改名 format_bool |
| `regex` | `is_match / find / find_all / group / replace`（类型化返回） | ◎ |
| `json` | 句柄式保持：`parse(s) -> i64`、`parse_file(path) -> Result<i64, string>`、`to_str / type_of / is_* / int_val / float_val / str_val / arr_len / arr_at / obj_keys -> table<string> / obj_get / err_msg() -> string`。定位：`obj_keys` 类型化 | ★parse_file 返 Result、◎ |
| `csv` | `read(path) -> Result<table<string>, string>`、`cells(line, sep) -> table<string>`、`write(path, lines: table<string>) -> bool`。**`csv_read/csv_cells/csv_write` 去前缀** | ★去前缀 + read 返 Result |
| `encoding` | `base64_encode / base64_decode / hex_encode / hex_decode / url_encode / url_decode` 不变 | -- |

### 4.2 数据结构 `sort / collection / set / deque / graph / linalg / optsearch / radix`

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `sort` | **字符串编码 → 真表**：`sort_i64(t: ref table<i64>)`（原地冒泡）、`sort_string(t: ref table<string>)`、`insert_sorted_i64(t: ref table<i64>, v)`、`insert_sorted_string(t: ref table<string>, v)`、`contains_i64(t: table<i64>, v) -> bool`、`contains_string(t: table<string>, v) -> bool`、`index_of_i64(t: table<i64>, v) -> i64`。删除 parse/serialize 样板 | ★★全面换代 |
| `collection` | `heap_push(t: ref table<i64>, v) / heap_pop(t: ref table<i64>) -> i64 / heap_peek(t: table<i64>) -> i64 / heap_size / stack_push / stack_pop / stack_peek / kmp_find(s, sub) / kmp_contains / kmp_count`（类型化） | ◎ |
| `set` | `new() -> table<i64> / contains / add(s: ref, x) -> bool / remove(s: ref, x) -> bool / size / to_table / union / intersect / diff` + 字符串族 `new_str / contains_str / add_str / remove_str`（类型化 `table<string>`） | ◎ |
| `deque` | `new / push_back / push_front / pop_back / pop_front / front / back / size / clear`（ref 补齐） | ◎ |
| `graph` | **字符串矩阵 → 真表**：`dijkstra(adj: table<i64>, n, src) -> table<i64>`、`floyd(adj: table<i64>, n) -> table<i64>`、`prim_mst(adj: table<i64>, n) -> i64`、`bellman_ford(adj: table<i64>, n, src) -> table<i64>`、`max_flow(cap: table<i64>, n, s, t) -> i64`、`bipartite_match(adj: table<i64>, n, m) -> i64`。统一约定：n×n 矩阵展平，无边=999 | ★★全面换代 |
| `linalg` | **字符串矩阵 → 真表**：`mat_mul(a: table<f64>, b: table<f64>, n) -> table<f64>`、`mat_trans / det -> f64 / gauss / mat_inv / lu_decompose / eigen_power` | ★★全面换代 |
| `optsearch` | **字符串序列 → 真表**：`merge_sort(t: table<i64>) -> table<i64>`、`quick_sort(t: table<i64>) -> table<i64>`、`max_subarray(t) -> i64`、`subset_sum(t, target) -> i64`、`knapsack(items: table<i64>, cap) -> i64`、`lis(t) -> i64`、`n_queens(n)` 不变 | ★★全面换代 |
| `radix` | `digits(base) / to_str(v, base) / parse(s, base)` 不变 | -- |

### 4.3 数学 `math / exmath / random`

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `math` | **泛型化**：`abs<T> / max<T> / min<T> / clamp<T>`（替代成对函数）；保留 `avg_f / is_odd / is_even / sign_i / deg_to_rad / rad_to_deg / gcd / lcm / pow_i` | ★★泛型化（删 8 个成对函数） |
| `exmath` | **字符串序列 → 真表**：`mean(t: table<f64>) -> f64`、`variance(t: table<f64>) -> f64`、`lagrange(xs: table<f64>, ys: table<f64>, x) -> f64`、`diff(xs: table<f64>, ys: table<f64>, x, h)`、`integrate(xs: table<f64>, ys: table<f64>, a, b, n)`、`euler(xs: table<f64>, y0, x0, x1, h)`、`rk4` 同、`fit_line(xs: table<f64>, ys: table<f64>) -> (a: f64, b: f64)`（命名元组）、`huffman_build(s) -> table<i64>`（类型化）、`huffman_encode / huffman_decode`、`is_prime / sieve(n) -> table<i64> / pow_mod / fib / factorial / binom / monte_carlo_pi`。**删除 `sieve_to_string`**（sieve+to_string 可替） | ★★全面换代 |
| `random` | `int(min, max) / flip / pick(t: table<i64>) -> i64 / pick_str(t: table<string>) -> string / shuffle(t: ref table<i64>)`（原地） | ★shuffle 改 ref、◎类型化 |

### 4.4 IO/系统 `fs / path / args / process / time / version / intern / assert`

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `fs` | `read_text(path) -> Result<string, string>`、`read_bytes(path) -> Result<table<i64>, string>`、`read_lines(path) -> Result<table<string>, string>`、`write_text(path, content) -> bool`、`append_text(path, content) -> bool`、`write_lines(path, lines: table<string>) -> bool`、`exists / is_file / is_dir / size -> i64`、`remove(path) -> bool`、`remove_all(path) -> bool`、`create_dir_all(path) -> bool`、`read_dir(path) -> table<string>`、`walk(path) -> table<string>`、`copy(src, dst) -> bool`、`copy_dir(src, dst) -> bool`、`rename(src, dst) -> bool`、`untar_gz / unzip -> bool`。**别名去重**：删除 read_to_string/read_text 其一（保留 read_text）、write/write_text、append/append_text 之一、remove_file/delete → remove、remove_dir_all/remove_all → remove_all、mkdir_all/create_dir_all 之一、move/rename 之一 | ★★去别名 + read 返 Result |
| `path` | `join / basename / dirname / abs / normalize / ext / stem / cwd` 不变 | -- |
| `args` | `count / get / has / value` 不变 | -- |
| `process` | `exec_code / exec_output` 不变 | -- |
| `time` | `now / now_ms / tick_start / tick_ms / elapsed_ms / seconds` 不变 | -- |
| `version` | `compare / satisfies` 不变 | -- |
| `intern` | `intern / lookup / interned_len` 不变（**编译器依赖**） | -- |
| `assert` | **泛型化**：`assert(cond)`、`assert_eq<T>(a: T, b: T)`（合并 assert_eq/assert_eq_f64/assert_eq_str）、`assert_neq<T>(a, b)` | ★泛型化合并（消费方签名不变，兼容） |

### 4.5 其他 `crypto / db / result / net / http / http_server`

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `crypto` | `crc32(s) -> i64 / fnv1a(s) -> i64 / crc32_table() -> table<i64>`（类型化） | ◎ |
| `db` | `to_data_i64(t: table<i64>, name) -> string`、`to_data_f64(t: table<f64>, name)`、`to_data_str(t: table<string>, name)`、`parse_data_f64(txt) -> table<f64>`。**`table_to_data_*` 去前缀** | ★去前缀 |
| `result` | enum `Result<T,E> / Option<T>` 不变 | -- |
| `net` | `tcp_listen / tcp_accept / tcp_connect / tcp_send / tcp_recv / udp_bind / udp_send / udp_recv / close(handle) -> bool` 不变（句柄 + -1 哨兵） | -- |
| `http` | `get(url) -> Result<string, string>`、`get_file(url, path) -> bool`。**删除 `url_encode / url_decode`**（encoding 已有） | ★get 返 Result、删重复函数 |
| `http_server` | `listen / accept / read_request -> Request / header / send / close` 不变 | -- |

## 5. rdu/ 逐模块新接口（7 模块）

> 不变量保持：无栈纪律（无表/字符串/堆）全部继续满足——struct 为值类型（i64 字段），
> 泛型调用点单态化，均无运行时开销。rdb/rdb.tie 是 rdu 与 tieDB 的纯标量谓词，一并纳入。

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `bits`（rdu_bits） | 不变（已是模板：`set/clear/toggle/test/rol/ror/bswap16/bswap32/bswap64/popcount/clz/ctz`） | -- |
| `math`（rdu_math） | **泛型化**：`abs<T> / max<T> / min<T> / clamp<T>`（替代 abs/abs_f、max_i/max_f、min_i/min_f、clamp/clamp_i）；保留 `avg_f / is_odd / is_even / sign_i / deg_to_rad / rad_to_deg / gcd / lcm / pow_i` | ★★泛型化 |
| `ascii`（rdu_ascii） | 不变 | -- |
| `crc`（rdu_crc） | **struct 状态封装**：`struct Crc8 / Crc16 / Crc32 / Fnv1a`（各含 `var v: i64`）；
  `pub func new() -> Crc8/16/32/Fnv1a`、`pub func update(s, byte) -> S`（S=对应状态）、
  `pub func value(s) -> i64`（CRC 终值异或并入 value；FNV 直接取值）。
  删除 `crc8_init/crc16_init/crc32_init/crc32_final/fnv1a_init` 裸 i64 版 | ★★struct 化 |
| `fixed`（rdu_fixed） | **去前缀**：`mul(a, b)`、`div(a, b)`、`floor(a)`、`frac(a)`（原 fixed_mul/fixed_div/fixed_floor/fixed_frac） | ★去前缀 |
| `rnd`（rdu_rnd） | **struct 状态封装**：`struct Rng { var s: i64 }`；`new(seed) -> Rng`、`next(r) -> Rng`（xorshift64）、`next_i64(r) -> i64`（取当前状态值）。`lcg` 改为 Rng 法算法之一或保留裸函数 | ★★struct 化 |
| `rdb`（rdu_rdb） | `cond_eq / cond_range / cond_gt / cond_lt / cond_eq_f / cond_range_f / cmp_i64` 不变 | -- |

## 6. ext/ 逐模块新接口（12 顶层 + 4 子目录）

| 文件 | 新接口 | 变更 |
| --- | --- | --- |
| `bench` | `reset / start / end / elapsed / summary / lap` 不变（类型化返回） | ◎ |
| `cache` | `set_root / get_root / pkg_path / hit` 不变 | -- |
| `compress` | `lz77 / lz77_decode / lzw / lzw_decode` 不变（压缩字节流保持字符串内嵌格式） | -- |
| `config` | `parse_kv / parse_ini / get / get_int / get_bool / has / parse_file` 不变 | -- |
| `log` | `error / warn / info / debug` + `_f` 族、`set_level / level / lang / set_fallbacks / register_all / set_lang / register / t / no_file` 不变（类型化 table 参数） | ◎ |
| `ml` | `svm_train(xs: table<f64>, ys: table<i64>, n, m, iters, lr) -> string`、`svm_predict(model, x: table<f64>, n) -> i64`、`tree_train(xs: table<f64>, ys: table<i64>, n, m, depth) -> string`、`tree_predict(model, x: table<f64>, n) -> i64`。删除 `parse_f64 / parse_i64` 辅助（真表取代） | ★★字符串样本 → 真表 |
| `pretty` | `render / simple / kv` 不变（类型化） | ◎ |
| `registry` | `set_registry / get_registry / pkg_url / index_url` 不变 | -- |
| `test` | **泛型化**：`reset / group / expect / expect_eq<T>(a, b, name) / expect_float_eq / pass_count / fail_count / summary / exit_code / done`。删除 `expect_str_eq`（泛型合并） | ★泛型合并 |
| `tui` | `line / hline / title / progress / box / pad / pad_center / indent` 不变 | -- |
| `codec/brotli` | `compress / decompress / to_bytes / from_bytes` 不变 | -- |
| `codec/jpeg` | `encode_pixels / decode_pixels / parse_bytes` 不变（类型化） | ◎ |
| `codec/lz4`、`codec/zstd` | 同 brotli | -- |
| `vecsearch/flat` | `l2 / cosine / flat_add / flat_remove / flat_size / flat_get / flat_search` 不变（已是 ref + 类型化模板） | -- |

## 7. 消费者同步清单（接口破坏性变更的受力面）

| 消费者 | 涉及模块 | 处理 |
| --- | --- | --- |
| `compiler/`（5 文件：lex_tokdefs、proto/lexer、lib/interner、middle/tieir_ser、backend/llvmgen、interp/value、frontend） | string、intern、bytes、utf、assert | string/utf/intern 签名不变零改动；bytes 类型化不影响调用；assert 泛型化签名兼容 → **编译器预期零改动** |
| `tests/`（约 90 处 import） | sort、math、fs、graph、linalg、exmath、optsearch、json、bytes、csv、crypto、http、set、string、result、args、time、utf、ascii、intern、process、ext/* | 批量机械同步（字符串→真表、泛型化调用不变、去别名改名） |
| `examples/`（约 40 文件） | 同上 + ext 全部 | 同步 |
| `ext/` 内部互调 | ml/compress/config/log 依赖 std | 同步 |
| 文档 | tie-dev skill、language.md、ai-guide、README 工程结构、CHANGELOG、embedded-rdu.md、tiedb.md、README 库清单 | 同步 |
| `scripts/package.ps1` | 库目录列表 `@("std","ext","rdu")` | 不变 |

## 8. 实施顺序

1. **rdu 层**（最小、零依赖、有 rdu_demo 验收）→ 编译 rdu_demo 通过；
2. **std 层**按依赖序：底层无依赖纯函数（math/ascii/string/utf/radix/format/encoding/result/version/time/args/path）→ 数据模块（sort/collection/set/deque/bytes/crypto）→ 依赖底层的数据构造模块（graph/linalg/exmath/optsearch/json/csv/db）→ IO/系统（fs/process/intern/assert/random/net/http/http_server）；
3. **ext 层**（依赖 std）；
4. **消费者批量同步**（tests → examples → docs）、自举验证（tiec 改后重编 tiec 三连自举）；
5. 验收（§9）→ 提交推送。

## 9. 验收标准

- 三层全部编译零错误：每个模块 `// tie:library` 编译 `.a` 通过；tiec 自举不动点（tiec→tiec2→tiec3）；
- 全部 examples 编译运行通过（rdu_demo/std_demo/sort_demo/graph_demo/linalg_demo/exmath_demo/…）；
- 语言测试集回归全绿（tests/language/ + s*_probe + interp）；
- grep 零残留：无 `max_i`/`max_f`/`clamp_i`/`fixed_mul`/`csv_read`/`read_to_string`/`copy(` 旧名；
- rdu 无栈纪律静态审计通过：grep 无 `table_`/`str_`/`to_string`/`println` 等原语；demo 期望值全对；
- 文档（tie-dev skill/README/CHANGELOG）与新接口一致。

## 10. 不做（明确排除）

- **不改三层定位与层级依赖**（std 不依赖 ext、rdu 零依赖、ext 依赖 std）；
- **不做 C 回调/unsafe 化**：库保持安全代码，指针/切片不进库接口；
- **不引入运行时库依赖**：rdu 的 `.a` 仍零运行时链；
- **不迁移 `codec/*` 与 `compress` 的压缩字节流格式**（保持字符串内嵌，压缩算法与格式不动）；
- **不做大版本号/命名空间重构之需**：模块文件路径、命名空间名（除 rdu 内函数改名）不变。