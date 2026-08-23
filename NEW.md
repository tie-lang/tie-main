# NEW — 发行版新鲜事

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

**内部代号**：Harbor 港湾（2026.1 正式版代号，首个正式版 = 工具链第一次靠岸停泊）
**本版**：Harbor-2026.1-preview.4
**对比基线**：Harbor-2026.1-preview.3

---

在本次预览版中，我们聚焦编译器性能与语言能力：自举提速 61×，并一次性落地**原生并发 actor**、**凭据安全模型（guard/goto）**、**128 位整数**、**动态库编译**等一批新语法与工程能力。

## 亮点速览

| 🧩 **宏/元编程**      | 过程宏、语句级宏、跨文件宏、宏错误传播                         |
| ----------------- | ------------------------------------------- |
| 🧊 **动态库编译**      | tie 库 → .dll/.so + dllexport 导出面，C 语言可运行期加载 |
| 🛟 **原生并发 actor** | tie语言原生功能，1:1 OS 线程，零运行时依赖                  |
| 🛡️ **unsafe加强**  | 凭证模型 + goto                                 |
| ⚙️ **编译器**        | 解耦 + 性能提升（上不封顶）                             |
| 🧱 **其他**         | 编译器解耦，128位整型，SSO优化，闭包后置，更好的错误处理             |

---


## 语言特性

### 原生并发 actor（一期，零运行时）

原生并发原语：`actor Name { var 私有字段 … pub func m() / pub async func m() }`，`run Typed()` 建句柄。
1:1 OS 线程 + 互斥/条件变量，**纯编译期降到 LLVM，零运行时依赖**。

```tie
actor Counter {
    var count: i64 = 0
    pub func inc(by: i64) -> i64 { count = count + by; return count }   // 同步 RPC：阻塞等应答
    pub async func bump(by: i64) { count = count + by }                // async：投递即返回
}
var c = run Counter()
var v = c.inc(5)     // 同步返回 5
c.bump(3)            // async 不阻塞
```

- 同步 RPC / fire-and-forget async / 方法 dispatch / 私有状态字段；句柄可复制（Erlang PID 式）；
- 消息方法支持**多标量参数**（2-3+，sync+async 均支持）；
- 处理器 panic → 调用方原地 raise。参考 `tests/m6_actor/`、concurrency-model §5。

### 凭据模型 guard 与 goto（三期 A 组）

越界能力收敛为可持有的 `guard<cap>` 凭据（cap = share/mem/ext）：

```tie
var g = unsafe.get(share)             // 取凭据（move-only）
unsafe use g { shared.buf[0] = x }    // 持证越界
var g2 = g.delegate(share)            // 委派：同域派生，最小权限移交
#[unsafe.share] fn agg() -> i64 { }   // 函数级便捷（点号属性）
```

- 通用 `#[]` 属性通道：`#[unsafe.share/trm/mem/ext]`；`#[tag.x]` 标签 + `unsafe goto #x` 无条件跳转；
- 本版落地 `guard<cap>.delegate` 同域派生第 1 批（含 `guard<cap>` 类型语法）。

### 128 位整数 i128/u128（全链路）

`i128`/`u128` 前后端全链路（字面量后缀 `42i128`/`7u128`、算术、转换、stage0 自举晋升）。

### volatile / slice_of / asm! 条件编译

- `volatile_load` / `volatile_store`：MMIO 语义（禁止优化合并/删除）；
- `slice_of(表)`：动态表 → 连续内存切片；
- `asm!(target("arch"))`：按目标架构分支的条件汇编。

### 闭包后置

闭包模型补齐：**嵌套捕获**（闭包内再闭包捕获外层）、**fn×泛型**、**C 回调**（函数值传 extern 边界）。

### 错误处理增强

- `switch r { case Result.Ok(v): … }` 变体载荷解构；
- `catch_panic`（可捕获 panic，unsafe 上下文 setjmp/longjmp → 可控结果）；
- Result/Option 组合子（unwrap/map/and_then…）。

### 宏三大方向落地

过程宏（`#[macro]` + token 流 API）、语句级宏（自定义循环/守卫）、跨文件宏（pub + 未导入报错）、`compile_error` 宏错误传播。

---

## 语言地基

### 去 Rust 桥：核心容器与字符串原语 tie 内联

表容器（`s21_table_*`）、字典（`s21_map_*`）、字符串码点（`str_len/char_code/str_from_code/str_char`）、
数字转串（`to_string`）、`parse_int/parse_trit` 等逐批改为 **irgen 内联**；`std/runtime.a` 退役，
`exec_code/get_env/time_now` 内联 libc → 纯程序可**零运行时依赖**（不链 tie_interp.lib）。

### SSO 短串池

短串运行时构造走静态池**零分配**（dev33 批次3）。

### extern 返回 char* 自动扫串

FFI 接收方向 `extern` 返回 `char*` 自动扫描为字符串（零拷贝边界）。

### 字符串二进制安全模型与布局健壮性

长度头 + 边界自动 NUL（`{ptr,len}` 二进制安全模型）；字面量/分配统一 32 字节尾部填充，修复向量化宽读越界闪崩（漏洞 B）。

---

## 编译器

### 自举性能 61× + emit 提速

自举编译 **1281s → 21s（61×）**（前端/全局平方热点清剿）；emit 提速 53%（查询区间索引化）。

### M5 动态库编译

tie 库 → `.dll`/`.so` + dllexport 导出面，C/其他语言可 `LoadLibrary`/`dlopen` 运行期加载；符号 `ns$fn`、边界规则（表/struct 不跨库）。

### compiler 自举化解耦重构

irgen 按 LLVM 风格分层（`tig_*`、拆 builder/字面量/表达式/调用/vtable/闭包/rt 等子文件）、前端/中端多文件分区，为后续扩展打底。

### 并发 / trm 设计定稿

原生 actor + 凭据门禁的 `concurrency-model.md`、`trm` 运行时最终设计、T 系列扩展定稿。