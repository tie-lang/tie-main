---
name: tie-dev
description: 用 tie 语言开发软件——tie 语法与类型系统、文件角色与头声明、编译运行（tiec）、数据互联（tink/zd）、表运算、标准库、包管理器、工程化工作流。在 F:\Projects\tie 仓库或任何 tie 项目中编写 .tie 应用代码时加载。
whenToUse: 编写 tie 源文件（.tie）、编译运行 tie 程序、使用 tink 帧协议/zd 序列化、使用标准库（std/）、组织多文件项目、使用包管理器（pkg/）时使用。
---

# tie 开发技能（用 tie 写软件）

tie：静态类型、四段式编译（预处理→前端→中端→后端 LLVM）的通用编程语言。
目标：全领域通用——写逻辑、写界面、写数据库、当数据交换格式。
编译器 **tiec 由 tie 100% 自写**（自举闭环，0-Rust）；发布包内置精简 LLVM 工具链，解压即用。
本文档是**应用开发者向**：用 tie 写程序，不涉及编译器内部开发。
并发（preview.5+）：内置 actor 原语 + channel 消息通道（p.6.5.7/6.5.8）；复杂形态
`import trm-lite`（work-stealing 调度 + 并发三色 GC 分代/整理 + mailbox，p.6.5.x 完整落地）。

## 1. 快速开始

```bash
compiler\tiec.exe examples\hello.tie    # 编译 → examples\hello.exe（默认 -O2）
examples\hello.exe                       # 运行
compiler\tiec.exe                        # 无参数 → 进入 REPL 交互模式
compiler\tiec.exe repl\repl.tie          # 构建 REPL 外壳
```

* 输入 `.tie` 源文件，输出本机可执行文件（logic/script 角色）或静态库 `.a`（class 角色）；

* 发行 zip 内置 `bin/llvm/`（clang/opt/llvm-ar/lld-link），设置 `TIE_LLVM_HOME` 指向它即可开箱即用，无需单独安装 LLVM；

* 纯程序零运行时依赖：`exec_code`/`get_env`/`time_now` 已内联到 libc，`std/runtime.a` 已退役；只用这些内置的程序不链接任何运行时库；用 tie-interp 桥（file/regex 等）才链 Rust `tie_interp.lib`；

* LLVM 工具发现顺序：`TIE_LLVM_HOME\bin` → tiec.exe 同目录 `llvm\bin` → `PATH` → 固定目录（`D:\LLVM\bin` 等）；

* 发行打包：`compiler\tiec.exe scripts\package.tie -- <版本号>`（tie 语言自写打包器，产出 `dist/tie-<版本>-win-x64.zip`；`skip-repl`/`skip-llvm` 可跳过对应步骤）。

## 2. 文件角色（头声明）

源文件**最前面几行**用 `type tie<X>` 声明角色，角色决定编译行为：

| 头部声明                            | 角色       | 编译行为                   |
| ------------------------------- | -------- | ---------------------- |
| `type tie<logic>`（默认）           | 逻辑代码     | 可执行文件，须含 `func main()` |
| `type tie<script>`              | 脚本       | 可执行文件                  |
| `type tie<class>` / `type tie`  | 类/库      | 静态库 `.a`，不生成 main      |
| `type tie<data>`                | 数据交换     | 纯数据（类似 JSON），可被 import |
| `type tie<ir>`                  | IR       | 直接生成 `.ll`，不继续链接       |
| `type tie<port>`                | 接口       | 端口/对外接口声明              |
| `type tie<ui>` / `type tie<db>` | 界面 / 数据库 | 对应工具链未实现，勿用            |

* 未声明头按 `logic` 处理；文件名 `xxx.<角色>.tie` 可作默认角色，但头部声明优先；

* 角色体系支持**自定义插件化**（S3.4）：通过构建配置 `config.data.tie` 的 `roles` 段或项目 `roles.data.tie` 注册自定义基础/修饰角色与参数（`kind`/`params`/`output=lib|check|exe`），与内建角色依序合并；**包可扩展编译器（纯数据声明）、不可扩展加载器**（字段白名单 + `[audit]` 审计拦截）；

* 头只允许出现在文件头部；优化级别 / 交叉编译目标**仅 CLI**（`-O2` / `--target`），不放头部；

* 头部与内容之间允许空行分隔。

## 3. 类型系统

基本类型：`i8 i16 i32 i64 i128 u8 u16 u32 u64 u128 f32 f64 bool trit char string void`。
复合类型：`table<T>`（动态数组）、`map`（键值表）、元组 `(T1, T2)`、struct、enum、`fn(A)->R`（函数类型）、`code`（编译期代码片段，宏用）、`any`（P2c 动态装箱）。

```tie
var x = 5                    // 推导 i64（整数字面量默认 i64）
var f = 3.14                 // f64
var n: i32 = 1               // 显式标注
const s: string = "hi"       // 不可变
var t: table<i64> = [1, 2, 3]
var m: map = ["a": 1, "b": 2]
var p: trit = zero           // 平衡三进制 -1/0/+1（true/zero/false）
```

窄整数后缀：`42i32 / 7u8 / 1.5f32`；转换 `as_*`；溢出检查 `checked_*` 族；
**f64↔i64 位重解释**：`bitcast_f64_i64(f) -> i64` / `bitcast_i64_f64(i) -> f64`（zd 序列化层支柱，字节级重解释非数值转换）。

### 3.1 `any` 动态类型与异构数据（P2c）

`any` 是一等值类型：struct / enum / fn 装箱为 any（堆分配），可作函数参数/返回值、struct 字段、`map` 键值。

```tie
func store(v: any) -> any { return v }        // 函数参数/返回值
var m: map<any> = ["k": 123, "s": "hi"]       // map 键值异构
var t: table<any> = [1, "x", 3.5]             // 异构元素表（P2b）
```

* 装箱自动（标量/struct/enum/fn 传 any 处自动装箱）；`println(any)` 运行时分派打印；

* **拆箱**：`as_i64 / as_f64 / as_string / as_struct<T> / as_enum<T>`（`as_*` 运行时 tag 检查）；

* `switch` 类型匹配取用 any：`case T: …`（按动态类型分派）；

* 复合元素表：`t[0](5)`（fn 值表达式间接调用）、`t[i].field` 可寻址读写（struct/enum 元素）、`map_keys / map_values / map_contains` 内置。

### 3.2 高层表运算（P1–P2，std/collection 库）

```tie
import "../../std/collection.tie"  using coll;
var xs: table<i64> = [5, 3, 8, 1]
coll.map(xs, func(x: i64) -> i64 { return x * 2 })        // 高阶 map
coll.filter(xs, func(x: i64) -> bool { return x > 2 })    // filter
coll.reduce(xs, 0, func(acc: i64, x: i64) -> i64 { ... }) // reduce
coll.count_if(xs, pred) / coll.any(xs, pred) / coll.all(xs, pred)
coll.find_index(xs, pred) / coll.contains(xs, v)
coll.sort_f64(xs)                                          // 排序
coll.mean(xs) / coll.median(xs) / coll.variance(xs) / coll.stdev(xs)
coll.reverse(xs) / coll.to_string(xs) / coll.join(xs, ",")
coll.sum(xs) / coll.product(xs) / coll.max(xs) / coll.min(xs)
```

集合：`std/set.tie`（`set_*` 有序表 + 二分，i64/string）；map 查询：`map_keys(m)` / `map_values(m)` / `map_contains(m, k)`。
高阶函数语法（P1）：数据流箭头 `->`/`<-` 传参与赋值简化链式调用。

## 4. 控制流

```tie
if x > 3 { } else if x > 1 { } else { }
while i < 10 { i = i + 1 }
for i in 0..10 { }                       // 范围：含 0 不含 10
for item in arr { }                      // 遍历表
for c in s.chars() { }                   // 字符串码点迭代：逐字符（Unicode 安全）
switch n {
    case 1, 2:                           // 多值：任一相等即命中（逗号分隔）
        println("one or two")
    case 3..7:                           // 区间：3 ≤ n < 7（整数/字符，左闭右开）
        println("three to six")
    case 8 when flag:                    // 守卫：值相等 且 flag 为真
        println("eight and flag")
    case string:                         // 类型匹配：宽类型/any/动态容器
        println("a string")
    default:                             // 可省略
        println("other")
}
```

* `case` 值支持整数、字符、布尔、负数、字符串、区间、多值组合（`case 1, 3..5 when cond:`）；

* `switch` 对 `any` 用 `case T:` 类型匹配取用（P2b-T4）；

* **无 break、无 fallthrough**：一个 case 执行完自动跳出；守卫不满足落入下一个 case；

* 浮点区间不支持；普通静态类型变量上做类型匹配 → 语义层报错；

* `&&` / `||` 短路求值：条件里带副作用的调用须嵌套 if；

* **字符串码点迭代** `for c in s.chars()`：按 Unicode 码点逐字符遍历（中文/emoji 一次迭代得完整字符）；随机码点索引用 `utf.to_chars(s)`，码点数用 `utf.codepoint_count(s)`。

## 5. 函数

```tie
func add(a: i64, b: i64) -> i64 { return a + b }        // 返回类型可省略（默认 void）
func greet(name: string, prefix: string = "Hello") { }  // 默认值参数（须连续排在必选之后）
func sum(xs: ...i64) -> i64 { ... }                     // 变参
func main() { println(add(1, 2)) }
```

### 5.1 ref 表参数（按引用传递，仅限表）

```tie
func fill(x: ref table<i64>) {
    table_push(x, 99)      // 内容修改写回调用方
    x[0] = 42
}
func replace(x: ref table<i64>) {
    x = table_new_i64()    // 重绑定也写回调用方实参槽
}
var t = table_new_i64()
fill(t)                    // len=3, t[0]=42
```

规则：实参必须是**可寻址的动态表变量**（表字面量/下标/调用结果不可取地址 → 编译错误）；非 ref 表参数保持值语义。

### 5.2 extern 函数声明（调用 libc / C 符号）

```tie
extern fn system(cmd: string) -> i32;    // 仅文件顶层；参数/返回仅标量
extern fn rand() -> i32;
println(rand())
println(system("exit 0"))
```

REPL / 解释路径不支持调用 extern（仅编译路径）。

### 5.3 多值返回（元组）

```tie
func divmod(a: i64, b: i64) -> (q: i64, r: i64) { return (a / b, a % b) }
var (q, r) = divmod(17, 5)     // 解构：q=3, r=2
var p = (x: 3, y: 4)           // 命名元组
println(p.x)                   // 命名访问；t.x / t.Item1 / t.0 三种形式等价
```

## 6. 数据结构

### 6.1 table（动态数组）与 map（键值表）

```tie
var arr: table = [1, 2, 3]
table_push(arr, 4)             // 追加（t[i] = v 在 i ≥ len 时静默失败，追加必须 table_push）
var e = arr[1]                 // 下标读（越界索引赋值无效，不追加）
for item in arr { }            // 遍历
var m: map<string> = ["x": "hi"]
var v = m["a"]                 // 下标读
m["c"] = 3                     // 下标写：不存在则插入
var k = len(m)                 // 条目数
```

* map 键恒为字符串，值类型全表一致，按键 **strcmp 字节序**有序存储（查找 O(log n)）；

* map 输出/打印按键排序，不依赖插入序；

* **map 不能作全局变量**（语法层拒绝）；仅 `table<T>` 支持顶层全局（`var g: table<i64>;`，跨函数持久）；

* 表字面量：`[1, 2, 3]`；二维表 `[1,2;3,4]` 语法可解析但语义报错，勿用；

* **字符串二进制安全**：`std/bytes.tie` 提供字节表读写（`bytes.read/write/concat` 等，0-Rust 内联实现，往返二进制安全）；tink/zd 序列化即以字节表为媒。

### 6.2 struct（纯数据 + 命名空间方法）

```tie
struct Point {
    var x: i64 = 0             // 字段：var name[: Ty] [= 默认值]
    var y: i64 = 0
}
namespace Point {
    pub func dist(p: Point) -> i64 { return p.x * p.x + p.y * p.y }  // 实例方法（首参=接收者，按引用）
    pub func origin() -> Point { return Point(0, 0) }                 // 静态风格
}
var p = Point(3, 4)            // 构造（按字段声明顺序传参）；Point() / Point(1) 缺省用默认值
p.x = 5                        // 字段直写
println(p.dist())              // 方法转发 → Point::dist(&p)
```

* struct 是值类型（LLVM 内联布局，无 GC）；逻辑放**命名空间函数**，`obj.method()` 自动转发；

* **寄存器中的 struct 值不可直接访问字段/调方法**：`Point(0).x` / `make().dist()` 报「需要可寻址」——必须先 `var o = Point(0)` 存入变量；

* 方法函数必须 `pub`（否则被私有拦截）；

* 继承：`struct Dog extends Animal`（字段拍平，子在前父在后），方法沿继承链查找（子→父），无虚表/无动态分派；

* 子 struct 字段必须跨继承链唯一；继承环 / 字段重名 → 编译错误。

### 6.3 enum（ADT，tag + payload）

```tie
enum Color { Red Green Blue }                  // 无数据变体
enum Shape { Circle(i64) Rect(i64, i64) }      // 带 payload
enum Option<T> { Some(T) None }                // 泛型 enum
var c = Shape.Circle(5)                        // 构造
switch c {
    case Shape.Circle: println("circle")       // tag 匹配（case 名 → tag 整数比较链）
    case Shape.Rect:   println("rect")
    default: ...
}
```

* 静态结构体布局（tag + payload 槽），可作 struct 字段/函数参数/返回值；可装箱 any 后经 `as_enum<T>` 拆箱；

* payload 目前支持 i64 等标量（string/f64 等宽类型暂不支持）。

### 6.4 泛型

```tie
func max<T>(a: T, b: T) -> T { if a > b { return a }; return b }   // 调用点推断
struct Box<T> { var v: T }
Box<i64>(42)           // 显式类型实参
max<i64>(9, 4)
pick<A, B>(a: A, b: B) -> A   // 多类型参数
```

编译期单态化展开 + 符号 mangling（`max$i64`）+ 嵌套类型实参（`Box<table<i64>>`）。

## 7. 面向接口：port（S2.4，已实现）

```tie
port Drawable {
    pub func draw(self, ctx: i64) -> string
    pub func bounds(self) -> i64
}
struct Button { var label: string; var w: i64; var h: i64 }
impl Drawable for Button {
    pub func draw(self, ctx: i64) -> string { return "Button(" + self.label + ")" }
    pub func bounds(self) -> i64 { return self.w * self.h }
}
// 泛型约束静态分发：T 实参化时校验「必须 impl Drawable」，编译期绑定具体实现
func render_all<T: Drawable>(d: T, ctx: i64) {
    println(d.draw(ctx))       // 单态化 → Button::draw / Text::draw
}
// 动态分发：unsafe 块把 struct 装箱为 port 值（data + vtable），异构容器 table<Drawable>
unsafe { var d: Drawable = button; d.draw(ctx) }   // 走 vtable 间接调用
```

* 静态分发（泛型约束）零开销；动态分发需要 `unsafe` 装箱 + 全局 vtable；

* `impl` 完整性检查：缺方法 → 编译错误。

## 8. 闭包与函数值

```tie
var d = func(x: i64) -> i64 { return x * 2 }          // 无捕获闭包
func apply(f: fn(i64) -> i64, x: i64) -> i64 { return f(x) }  // 高阶
var g: fn(i64) -> i64 = add1                           // 命名函数提升
func make() -> fn(i64) -> i64 { ... return func(x: i64) -> i64 { ... } }  // 闭包返回
```

闭包值 = `{env, entry}` 聚合，捕获变量 move 进 env（堆分配），调用走 call\_indirect；嵌套捕获（闭包内再闭包）支持。

## 9. 错误处理

```tie
import "../../std/result.tie"        // 预置 Result<T,E> / Option<T>
func div(a: i64, b: i64) -> Result<i64, string> {
    if b == 0 { return Result.Err("z") }
    return Result.Ok(a / b)
}
var v = div(10, 2) ?                 // ? 解包：Err 提前 return，Ok 解包 payload
panic("致命错误")                      // 打印 + exit(1)
```

`?` 仅限返回 Result/Option 的函数内使用。`fs.read_text/json.parse_file/http.get` 等返回 `Result<string|i64, string>`（错误带上消息）。

## 10. 宏 / 元编程

```tie
macro double(x: code) -> code {
    return `( ($x) * 2 )
}
macro make_getter(field: code) -> code {
    var nm = gensym("get")
    return `{
        func $nm() -> i64 { return self.$field }
    };
}
var v = double(3 + 4)    // 表达式宏：14
```

* code 三形态：准引用（`` ` ``）/ 插值（`$x`）/ gensym（`gensym("名")` 防命名冲突）；

* 函数式宏展开 pass（mexpand）；语句级宏 / 跨文件宏 / 过程宏为遗留项；

* 宏体里准引用末尾的 `}` 后要加分号（防 ASI 吞掉闭合）。

## 11. 模块化：import / 命名空间 / 标准库

```tie
import "./lib_math.tie" as math    // 导入其他 tie 文件（相对路径）
using math;                        // 引入命名空间：公有函数可裸调用
```

* 命名空间内函数默认**私有**（仅同命名空间可见），`pub func` 显式导出；顶层函数恒公有；

* `import "x.tie" as f2`：别名是唯一入口（原前缀被屏蔽）；

* 多 using 同名函数 → 裸调用歧义报错；

* 函数递归加载内联、重复导入去重；跨文件语义（命名空间调用）不误报未声明变量；

* **标准库 import 路径**：工程根下直接 `import "std/string.tie"`（或仓库内 `import "../../std/xxx.tie"`），随后 `using xxx;`。

### 标准库（std/，library-v2 三层重构后）

```
文本/编码：string / ascii / utf / bytes / format / regex / json / csv / encoding / base48
数据结构：sort / collection / set / deque / graph / linalg / optsearch / radix
数学：math（泛型 abs<T>/max<T>/min<T>/clamp<T>）/ exmath / random / bigint
IO/系统：fs / path / args / process / time / version / intern / assert
网络：net / http / http_server
哈希/密码：sha1 / sha256 / sha512 / sha3 / blake2 / blake3 / shake / md5（遗留）/
          siphash / xxh3（非加密）/ hmac / poly1305 / ascon_mac / hkdf / pbkdf2 /
          ed25519 / x25519 / tsha1 / tsha1_w48（TIE Secure Hash，state-per-n）
数据互联：tink（帧协议）/（zd 序列化见下方）
其他：crypto / db / result / tink_probe
```

扩展库（ext/）：aes / chacha20 / ascon\_aead / ecdsa / scrypt / argon2 / compress /
jpeg / lz4 / zstd / brotli（codec）/ ml / registry / log / bench / cache / config / pretty / test / tui。
嵌入式基础层（rdu/，无栈纪律）：ascii / bits / crc（Crc8/16/32/Fnv1a）/ fixed / math / rdb / rnd / rdu\_ascon\_mac / rdu\_poly1305。

常用：

```tie
import "../../std/string.tie"  using string;
import "../../std/fs.tie"      using fs;
import "../../std/process.tie" using process;

var s = string.trim("  hi  ")            // 去空白
process.exec_code("exit 0")              // 0（libc system 退出码）
process.exec_output("echo hello")        // "hello\n"（stdout+stderr 合并捕获）
intern.intern("abc")                     // 字符串 → 稳定整数 id（std/intern.tie）
```

注意：`std/db.tie` 参数名用 `txt`；`len(s)` 是字节数，`str_len(s)` 按 Unicode 码点（中文 1 字 = 3 字节 1 码点，遍历用 `str_len`）。

### 11.1 std 常用 API（按模块）

**string（str 命名空间）**：`trim/trim_start/trim_end`、`slice(s,start,end)`、`contains/find/starts_with/ends_with`、`replace`、`split(s,sep)->table`、`to_upper/to_lower`、`join(items,sep)`、`repeat(s,n)`、`clone`。
**utf**：`codepoint(ch)->i64`、`from_code(n)->string`、`to_chars(s)->table`、`codepoint_count(s)`、`utf8_bytes(cp)`、`byte_len`、`is_ascii/is_letter`。
**ascii**：`is_digit/is_alpha/is_alnum/is_lower/is_upper/is_print/is_space`、`to_lower/to_upper(cp)->i64`、`to_code(c)->i64`、`to_char(cp)->string`。
**bytes**：`read(path)->table<i64>`、`write(path,t)->bool`、`concat(a,b)`、`bit_read/bit_write`、`to_ascii/from_ascii`。
**encoding（enc）**：`base64_encode/decode`、`hex_encode/decode`、`url_encode/decode`。
**base48（b48）**：`encode(bytes_hex)->string`、`decode(s)->string`。
**radix**：`digits(base)`、`to_str(v,base)`、`parse(s,base)`（2..36）。
**collection（coll）**：堆 `heap_push/pop/peek/size`；栈 `stack_*`；KMP `kmp_find/contains/count`；高阶 `map_i64/map_string、filter_*、reduce_*、foreach_*`、`count_if_*、any_*、all_*、find_index_*、contains_*`；统计 `mean_*/median_*/variance_*/stddev_*`（i64/f64 各一组）、`sum/product/max/min`（i64）；变换 `reverse_*/concat_*/slice_*/copy_*/dedup_*、to_string_i64/join`；集合 `set_new/add/contains/remove/size/union/intersect/diff`（i64/string 后缀）。
**sort**：`sort_i64/sort_string/sort_f64`、`insert_sorted_*`、`index_of_i64`、`contains_*`。
**set（散列集合）**：`new/add/remove/contains/size/union/intersect/diff/to_table`（i64）；`new_str/add_str/...`（string）。
**deque（双端队列）**：`new/push_back/push_front/pop_back/pop_front/front/back/size/clear`。
**math**：泛型 `abs<T>/max<T>/min<T>/clamp<T>`、`gcd/lcm`、`pow_i`、`is_odd/is_even`、`sign_i`、`avg_f`、`deg_to_rad/rad_to_deg`。
**exmath**：`huffman_build/encode/decode`、`is_prime/sieve`、`pow_mod`、`fib/factorial/binom`、`mean/variance/lerp/lagrange/diff/integrate`、`monte_carlo_pi`、`euler/rk4`（ODE）、`fit_line`。
**linalg**：`mat_mul/mat_trans`、`det/gauss/mat_inv/lu_decompose/eigen_power`（f64 方阵，n 维参数）。
**bigint**：大整数表表示；`from_hex/to_hex`、`add/sub/mul/divrem/div/mod`、`cmp`、`and/or/shl_bits/shr_bits/bitlen`、`powmod/invmod`、`is_zero`。
**graph**：`dijkstra/floyd/bellman_ford`（邻接表+距离表）、`prim_mst`、`max_flow`、`bipartite_match`。
**optsearch（opt）**：`merge_sort/quick_sort`、`max_subarray`、`n_queens`、`subset_sum`、`knapsack`。
**fs**：读 `read_text->Result<string,string>/read_bytes->table<i64>/read_lines`；写 `write_text/append_text/write_lines->bool`；元数据 `exists/is_file/is_dir/size`；删 `remove/remove_all`；`create_dir_all/read_dir/walk/copy_dir/copy/rename`；归档 `untar_gz/unzip`。
**path**：`join/basename/dirname/abs/normalize/ext/stem/cwd`。
**process**：`exec_code(cmd)->i32`、`exec_output(cmd)->string`。
**net**：`tcp_listen/tcp_accept/tcp_connect/tcp_send/tcp_recv`、`udp_bind/udp_send/udp_recv`、`close`。
**http_server**：`listen/accept`、`read_request(conn)->Request`、`header(req,name)`、`send(conn,status,ctype,body)`、`close`。
**http**：`get(url)->Result<string,string>`、`get_file(url,path)->bool`。
**json**：`parse(s)->i64`（句柄）、`parse_file->Result<i64,string>`、`to_str`、`type_of/is_null/is_bool/...`、`int_val/float_val/str_val`、`arr_len/arr_at/obj_keys/obj_get`。
**csv**：`read(path)->table<string>`、`cells(line,sep)`、`write(path,lines)`。
**db**：`to_data_i64/f64/str(t,name)->string`、`parse_data_f64`。
**format**：`format_int/format_pad/format_int_hex/format_bool`、`sprintf(fmt,args)`。
**time**：`now()->i64`、`now_ms`、`tick_start/tick_ms/elapsed_ms`、`seconds`。
**random（rnd）**：`int(min,max)`、`flip`、`pick/pick_str`、`shuffle`。
**args**：`count/get(i)/has(flag)/value(flag)`。
**assert**：`assert(cond)`、泛型 `assert_eq<T>/assert_neq<T>`。
**result**：预置 `Result<T,E>`/`Option<T>` 类型（无函数）。
**regex**：`is_match/find/find_all/group/replace`。
**intern**：`intern(s)->i64`、`lookup(id)`、`interned_len`。
**version**：`compare(a,b)->i64`、`satisfies(v,constraint)`。
**crypto（crc 命名空间）**：`crc32(s)`、`fnv1a(s)`、`crc32_table`。

哈希/密码族（全部 hex 输入输出）：`sha256.sha256`、`sha512.sha512/sha512_bytes`、`sha1.sha1_hex`、`sha3.sha3_256/sha3_512`、`shake.shake128/shake256(msg_hex,outlen)`、`md5.md5_hex`、`blake.blake2s/blake2b`、`blake3.blake3_256`、`hmac.hmac_sha256(key,msg)`、`pbkdf2.pbkdf2_hmac_sha256(p,s,iter,dklen)`、`hkdf.extract/expand/derive`、`poly.poly1305(key,msg)`、`ascon_mac.ascon_mac128(key,msg)`、`siph.sip24(k0,k1,s)`、`xxh3.xxh3_64(xxh3->i64/hex)`、`ed25519.keygen/sign/verify`、`x25519.keygen/dh`、`tsha.tsha1f/b/x/r(msg,n,base=48)`。

### 11.2 ext 扩展库 API（`import "../../ext/xxx.tie"`）

- **aes**：`encrypt_ecb/decrypt_ecb(key,block)`、`encrypt_cbc/decrypt_cbc(key,iv,msg)`（hex）。
- **chacha20（chacha）**：`chacha20_encrypt(key,nonce,counter,msg)`（hex，加解密同函数）。
- **ascon_aead**：`encrypt/decrypt(key,nonce,assoc,msg)`（hex）。
- **argon2**：`argon2id(passwd_hex,salt_hex,t,m_kib,p,outlen)`。
- **scrypt**：`scrypt(passwd_hex,salt_hex,n,r,p,dklen)`。
- **ecdsa**：`keygen/sign(key,hash)/verify(key,hash,sig)`（P-256，hex，extern）。
- **compress**：`lz77/lz77_decode`、`lzw/lzw_decode`（序列串）。
- **codec/brotli|lz4|zstd**：各 `compress(s)/decompress(seq_s)/to_bytes/from_bytes`；**codec/jpeg**：`encode_pixels/decode_pixels(px,w,h)`。
- **ml**：`svm_train/svm_predict`、`tree_train/tree_predict`（线性 SVM + 决策树）。
- **vecsearch（vecsearch/flat）**：`l2/cosine`、`flat_add/remove/get/search`、`flat_size`。
- **config（cfg）**：`parse_kv/parse_ini/parse_file`、`get/get_int/get_bool/has`。
- **registry**：`set_registry/get_registry`、`pkg_url/index_url`（M6 包台账）。
- **cache**：`set_root/get_root`、`pkg_path/hit`（包缓存）。
- **log**：`error/warn/info/debug`（+`_f` 模板版）、`set_level/level`、`lang/set_lang/set_fallbacks`、`register/register_all/t`、`log.error.no_file`。
- **test**：`reset/group/expect/expect_eq<T>/expect_float_eq`、`pass_count/fail_count/summary/exit_code/done`。
- **bench**：`reset/start/end/elapsed/lap/summary`。
- **pretty**：`render/simple(headers,rows)`、`kv(key,value,width)`（文本表格）。
- **tui**：`line/hline/title/progress/box/pad/pad_center/indent`（纯文本装饰）。

### 11.3 rdu 嵌入式基础层 API（无栈纪律：纯标量，`import "../../rdu/xxx.tie"`）

- **rdu_ascii**：`is_digit/is_alpha/is_alnum/is_lower/is_upper/is_print/is_space`、`to_lower/to_upper(cp)`。
- **rdu_bits**：`set/clear/toggle/test`、`rol/ror`、`bswap16/32/64`、`popcount/clz/ctz`。
- **rdu_crc**（struct 状态 + 值回写）：`crc8_new/update/value`、`crc16_*`、`crc32_new/crc32_update/crc32_value`、`fnv1a_new/update/value`。
- **rdu_fixed**（Q16.16 定点）：`mul/div/floor/frac`。
- **rdu_math**：泛型 `abs<T>/max<T>/min<T>/clamp<T>`、`gcd/lcm/pow_i`、`is_odd/is_even/sign_i/avg_f`、`deg_to_rad/rad_to_deg`。
- **rdu_rdb**（嵌入式查询）：`cond_eq/cond_range/cond_gt/cond_lt`（+f 版）、`cmp_i64`。
- **rdu_ascon**：`ascon_mac128(key,msg)`；**rdu_poly**：`poly1305(key,msg)`。
- **rdu_rnd**（确定性 PRNG，值回写）：`new(seed)->Rng`、`next(r)->Rng`、`value(r)->i64`、`lcg(state,mul,inc)`。
- 用途：CRC32 增量（tink 复用）、无堆位运算、定点数、嵌入式 MAC——零动态内存/零递归/无全局状态。

## 12. 数据互联：tink 帧协议与 zd 序列化（preview\.5 核心）

### 12.1 tink 节点帧协议（std/tink.tie）

tink 是语言无关的通用数据流互联服务：组件遵守统一字节级帧协议即可接入管道。帧格式：

```
帧 = [ len: u32 BE ][ payload: len 字节 ][ crc: u32 BE ]
crc = CRC32-IEEE(payload)（多项式 0xEDB88320；校验向量 crc32("123456789")==0xCBF43926）
```

```tie
import "../../std/tink.tie"  using tink;
var p = table_new_i64()                  // payload = 字节表（元素 0..255）
table_push(p, 1)  table_push(p, 2)  table_push(p, 3)
var f = tink.frame_encode(p)             // 编码：len + payload + crc
var (payload, next_pos) = tink.frame_next(f, 0)   // 解析（校验 CRC）：失败 (空表, -1)
var skip = tink.frame_skip(f, 0)         // 跳过一帧（不校验）：返回 next_pos / -1
var c = tink.crc32(p)                    // 整段 CRC32
```

多语言库共生（Rust/C/Python/JS/Go/Zig/Lua…，`tink-<语言>` 仓库，API 与校验向量一致）。

### 12.2 zd v2 通用二进制序列化

语言无关二进制规范：10 字节头（`TIEDBZD` 魔数 + base-48 版本 + flags），核心类型
i64/u64/f64/string/bool/array/map/bytes/blob/null + ext 扩展类型，字符串字典/列式容器优化，
v1 兼容读取，扩展名统一 `.zd`。规范见 docs/superpowers/specs 的 zd v2 设计文档。

### 12.3 tiec `--compress-data`（td → zd）

```bash
tiec --compress-data in.data.tie -o out.zd    # 表字面量 → DFS 平铺 → zd record
```

把 `.data.tie`（tie 表字面量，含 `type tie<data>` 头与可选表名）经 DFS 平铺 + 平行表
（kind/key/value/child\_count）转为 zd record 输出 `.zd`；编译器内部 config 等数据文件
可走同一条统一定义路径。

## 13. 工程化

### 13.1 CLI 选项

```bash
tiec <input.tie> [-o <out>] [-O0|-O1|-O2|-O3] [--target <三元组>]
                [--emit-ir] [--keep-ir] [--prep-only] [--config <f>] [--help]
tiec --compress-data <in.data.tie> -o <out.zd>     # td → zd（12.3）
```

| 选项                | 说明                                                    |
| ----------------- | ----------------------------------------------------- |
| `-o <file>`       | 输出路径（logic/script 默认输入同名 `.exe`；class/type 默认同名 `.a`） |
| `-O0..-O3`        | 优化级别（默认 `-O2`，映射 `opt`）                               |
| `--target`        | 交叉编译目标（如 `win-x64` / `x86_64-pc-windows-msvc`，默认本机）   |
| `--emit-ir`       | 只生成 LLVM IR（`.ll`），不继续编译                              |
| `--keep-ir`       | 保留中间 IR                                               |
| `--prep-only`     | 只做预处理（角色识别）并打印结果                                      |
| `--config <f>`    | 构建配置文件（分层合并：CLI > 项目 config > 用户 > 内置默认）              |
| `--profile <p>`   | 构建 profile（dev/release，Cargo 风格）                      |
| `--backend <b>`   | 后端选择（win32 唯一可用）                                      |
| `--compress-data` | td → zd 压缩数据子命令（表字面量 → DFS → zd record）               |
| `--lsp`           | 语言服务器模式（stdio）                                        |

退出码：`0` 成功 / `1` 编译失败 / `2` 参数错误。

### 13.2 库编译

```bash
tiec lib_math.tie                  # class 角色（type tie<class>）→ lib_math.a
tiec lib_math.tie -o lib_math.lib  # MSVC 兼容 .lib（同一 COFF 归档，不同扩展名）
```

导出符号为 `命名空间$函数`（如 `mathlib$add`），C/其他语言可链接消费。

### 13.3 包管理器（pkg/，tie 自写）

```bash
tiec pkg\main.tie -o pkg\pkg.exe    # 构建 pkg.exe
tie init <项目名>                    # 初始化（tie.pkg 清单 + main.tie 模板）
tie add path:./lib_math             # 本地源 / git+https://... / log@^1.2（registry 约束）
tie install                         # 解析 + 拉取依赖到 .tie/deps/，生成 tie.lock
tie build / tie run                 # 编译 / 编译并运行
tie publish                         # 打包发布（.tar.gz + git tag + push）
tie search <关键字> / tie info <包>  # 查询注册表
```

### 13.4 多文件并行编译与缓存

```tie
// tie.config（type tie<data>）
[
    "advanced": [ "enabled": true, "threads": 0 ],      // 0 = 按 CPU 核数
    "cache": [ "size": 268435456, "storage": "memory", "path": ".tie-cache" ],
]
```

## 14. 编译期会报错的写法（负例，勿生成）

| 场景                                              | 错误关键词                                    |
| ----------------------------------------------- | ---------------------------------------- |
| `Point(0).x` / `make().get()`（寄存器 struct 值直接访问） | 「需要可寻址」                                  |
| 方法函数未加 `pub` 被 `obj.method()` 调用                | 「私有函数…不可在命名空间之外调用」                       |
| 继承环 / 子字段与父字段重名                                 | 「struct 继承形成环」/「字段名必须跨继承链唯一」             |
| struct 体内定义方法                                   | 「struct 体不允许方法定义」                        |
| 字段无类型标注且无默认值                                    | 「字段必须标注类型或有默认值」                          |
| 函数体内定义 struct / import / 嵌套函数                   | 「顶层只允许…」                                 |
| const 变量重新赋值                                    | 「不可变变量不能赋值」                              |
| 类型不匹配（i64 赋给标注 i32）                             | 「类型不匹配」                                  |
| 元组空解构 `var () = ...`                            | 「空解构 () 不支持」                             |
| ref 实参非可寻址 / 非动态表 / 非表类型                        | 「ref 参数需要可寻址的表变量实参」等                     |
| const 全局表 / 顶层 map 全局变量                         | 「const 全局表暂不支持」/ 语法层拒绝                   |
| extern 参数为表或结构体 / 函数体内声明 / REPL 调用              | 「必须标量类型」/「只能出现在文件顶层」/「REPL 不支持调用 extern」 |
| 静态类型变量上做类型匹配（switch）                            | 语义层报错（类型恒定）                              |
| 浮点区间 case                                       | 语义层报错                                    |
| enum payload 为宽类型（string/f64/table）             | 「白名单暂不支持」                                |
| map 作为全局变量                                      | 语法层拒绝                                    |

## 15. 并发：actor（消息方法——多参标量 sync/async）

actor 是原生并发原语：编译期降到 OS 线程 + 互斥/条件变量，消息处理由 **trm-lite 承载**
（p.6.5.8：每条消息经 per-actor **channel mailbox** 入队 + 轻量任务取出执行，
`spawn`/`yield` 协作排空；`#[unsafe.trm]` 标注作为显式接入确认，语法零改动）。
`run Typed()` 建句柄，方法调用即消息投递。

```tie
actor Counter {
    var count: i64 = 0
    pub func inc(by: i64) -> i64 { count = count + by; return count }   // 同步 RPC：阻塞等应答
    pub async func bump(by: i64) { count = count + by }                // async：投递即返回，须 void
}
var c = run Counter()
var v = c.inc(5)      // 同步：返回 5
c.bump(3)             // async：不阻塞
```

* 消息方法支持**多个标量参数**（2-3 及更多，sync/async 均可）；

* 同步方法可有返回值；`async` 必须 `void`（无返回值）；

* 私有状态字段为 actor 独占（串行消费免锁）；字段初值暂用**类型默认值**（如 i64=0）；

* 指针/slice 宽类型共享消息属 unsafe 门禁（`#[unsafe.share]` 等），安全路径限标量；

* actor 与 `import trm-lite`（复杂形态）混用 → 编译期报错（替代运行时路径）。
  复杂形态下 actor 消息同样经 mailbox 承载（同一 trm_lite.a）。

### 15.1 channel（mailbox 消息通道，p.6.5.7）

内置原语（简单形态，零 import）：

```tie
var ch = ch_open()          // 建通道（句柄 1 起）
var r = ch_send(ch, 42)     // 入队：0=成功 1=失败（已关闭或队列满）
var v = ch_recv(ch)         // 取队首：v=消息值 0=空(未关) -1=已关闭且排空
ch_close(ch)                // 置关闭位（幂等），唤醒等待者
```

* 环形缓冲 mailbox（互斥 + 条件变量），FIFO 有序；单通道容量 64，满后 `ch_send` 返回 1；
* 非阻塞语义（Go 阻塞 send/recv 的降级）：空 `ch_recv` 返回 0、满 `ch_send` 返回 1，
  调用方据此轮询/协商，避免语言无挂起能力下的死锁；
* 复杂形态（`import tl_runtime_ctx`）用 `ctx_ch_open/ctx_ch_send/ctx_ch_recv/ctx_ch_close/
  ctx_ch_len/ctx_ch_count`，语义与内置一致（同源 mailbox）。

## 16. unsafe、移动语义与三期限量语法（概览）

细节以 docs/language.md §13/14 与 docs/designs/concurrency-model.md §7 为准。

* 所有权：`var b = move a` 转移所有权，转移后 `a` 不可再用（编译期报错）——smove pass（S1.5）。

* `unsafe fn` / `unsafe { }`：解锁指针/切片 `ptr<T>` / `slice<T>`、`slice_of(表)`、
  `atomic<T>`、`volatile_load` / `volatile_store`、`asm!("...")`、`repr(C)`、extern 调用。

* 窄整数：`42i32` / `7u8` / `1.5f32` 后缀、`as_*` 转换、`checked_*` 溢出检查。

* 属性 `#[...]`：`#[macro]`（过程宏）、`#[repr(C)]`、`#[unsafe.share/trm/mem/ext]` 凭据、
  `#[tag.x]` 标签。

* goto：`#[tag.x]` 标签 + `unsafe goto #x` 无条件跳转。

* guard 凭据：`unsafe.get(share)` / `unsafe use g { }` / `unsafe.with(share) { }`
  （move-only `guard<share>`，破「状态私有」边界）。

## 17. 参考资料索引（写 tie 代码时查阅）

* `docs/language.md`：语法规范（权威）

* `docs/ai-guide.md`：AI 教学指南（语言全景 + 负例）

* `docs/cli.md`：CLI 用法速查（主入口 / 包管理器 / 库编译 / --compress-data）

* `docs/tiec.md`：tiec 编译器文档（角色识别 / 运行时依赖 / 已知限制）

* `docs/tie-script.md`：tie:script 模块协议（eval / eval\_call）

* `docs/prompt-pack.md`：可粘贴 Prompt 包（自包含简介）

* `docs/superpowers/specs/`：设计文档（tink / zd v2 / td 数据编译器 / tsha1 等）

* `examples/`：可运行示例（hello / lib\_math / switch\_pattern / pkg\_demo…）

* `tests/*_probe/`：真实可用代码样例（最新特性语法以此为准；P2 表运算见 tests/\_p2b\_probe）

* `NEW.md` / `CHANGELOG.md`：发行版新鲜事 / 版本变更记录

