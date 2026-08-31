# tie 语言内置功能对比报告

*EN: tie Language Built-in Feature Comparison Report*

> 对比对象：42 种编程语言（全景表）+ 16 种重点语言（特性矩阵）
> EN: Comparison subjects: 42 programming languages (panorama table) + 16 key languages (feature matrix)

> 范围：**语言内置功能**（语言特性 + 标准库，不含第三方生态）
> EN: Scope: **language built-in features** (language features + standard library, excluding third-party ecosystems)

> **目标定位：工业级全栈开发框架**——从 UI、后端到数据库等场景全面覆盖
> EN: **Positioning: an industrial-grade full-stack development framework**—comprehensive coverage of scenarios ranging from UI and backend to database

> 结论导向：按全栈场景逐项列出 tie 缺少什么、缺到什么程度（语言级缺失 / 库级可补 / 设计取舍）
> EN: Conclusion-oriented: itemizes what tie lacks per full-stack scenario and to what degree (language-level gap / fillable at library level / design trade-off)

> 日期：2026-08-14（v3：工业级全栈定位，对标对象重排）
> EN: Date: 2026-08-14 (v3: industrial-grade full-stack positioning, benchmark list reordered)

---

## 1. 概述

*EN: 1. Overview*

tie 的定位是**伸缩自如的全栈语言——丰俭由人**：从极简到工业级连续覆盖，
用多复杂、由使用者决定——

*EN: tie is positioned as a **scalable full-stack language—rich or lean as you choose**: featuring continuous coverage from minimal to industrial-grade. How complex to make it is up to the user—*

- **简单端**：可当脚本用（REPL、小工具、数据交换），语法克制、无需复杂概念即可上手；
- *EN: Simple end**: usable as a scripting language (REPL, small tools, data exchange); restrained syntax, easy for beginners without requiring complex concepts;
- **复杂端**：具备工业级全栈能力——UI、后端、数据库、数据交换全面覆盖，四段式架构
  （预处理 → 前端 → 中端 → 后端）与角色头（`logic` / `ui` / `db` / `data` / `library`）
  即为该目标的语言级设计，同一 `.tie` 文件按角色声明自动进入对应工具链。
- *EN: Complex end**: industrial-grade full-stack capability—comprehensive coverage of UI, backend, database, and data exchange. The four-stage architecture (preprocessing → frontend → middle → backend) and role headers (`logic` / `ui` / `db` / `data` / `library`) are the language-level design for this goal; the same `.tie` file automatically enters the corresponding toolchain by role declaration.

对标参照因此是一条**连续谱**：简单端参考 Lua（优雅克制）、工程端参考 Go / Python
（务实可靠）、全栈端参考 TypeScript / Dart / C#（能力覆盖）。tie 不求最小化，也不求
特性堆砌，而是**按需伸缩**——简单场景不付复杂性的代价，复杂场景不缺工业级能力。

*EN: The benchmark reference is therefore a **continuous spectrum**: the simple end references Lua (elegant and restrained), the engineering end references Go / Python (pragmatic and reliable), and the full-stack end references TypeScript / Dart / C# (capability coverage). tie neither pursues minimalism nor feature accumulation, but instead **scales on demand**—simple scenarios do not pay the cost of complexity, and complex scenarios do not lack industrial-grade capability.*

取舍说明：tie 用**命名空间 + 约定**替代 OOP/接口/泛型等编译期抽象，用 **bool/错误码**
替代异常与 Result，用 **UTF-8 字符串 + C ABI 桥**替代指针与手动内存。这些取舍服务于
“语言可自举、行为可预期”，但**全栈覆盖所需的并发、网络、数据库、UI 工具链**仍是当前
的主要缺口。

*EN: Trade-off note: tie replaces compile-time abstractions such as OOP/interfaces/generics with **namespaces + conventions**, replaces exceptions and Result with **bool/error codes**, and replaces pointers and manual memory with **UTF-8 strings + C ABI bridge**. These trade-offs serve “a self-hosting language with predictable behavior,” but the **concurrency, networking, database, and UI toolchains required for full-stack coverage** remain the main gaps today.*

---

## 2. 语言全景（42 种，按首字母排序）

*EN: 2. Language Panorama (42 languages, sorted alphabetically)*

| 语言 | 分类 | 一句话定位 | tie 相关性 |
|---|---|---|---|
| Ada | 系统/安全 | 军工级安全强类型语言 | 低 |
| Assembly | 底层 | 机器码助记符 | 低 |
| Bash | 脚本/Shell | Unix 命令行脚本 | 低 |
| BASIC | 教育/商业 | 初学者语言鼻祖 | 低 |
| C | 系统 | 系统编程基石，FFI 对象 | 中（FFI 对象） |
| C++ | 系统/OOP | 高性能系统语言，模板/RAII/STL | 中（性能参考） |
| C# | 托管/OOP | **.NET 全栈**（Web/桌面/移动/游戏） | **高（全栈对标）** |
| COBOL | 商业 | 金融/商业存量霸主 | 低 |
| Clojure | 函数式/Lisp | JVM 上的 Lisp | 低 |
| Crystal | 系统/编译 | Ruby 语法 + 静态类型 + LLVM，可自举 | **高（同路线）** |
| D | 系统 | C++ 替代，GC+手动双模式 | 低 |
| Dart | 托管/OOP | **Flutter 全栈 UI**（跨端渲染） | **高（UI 对标）** |
| Delphi | 商业/GUI | Object Pascal，老牌 GUI | 低 |
| Elixir | 函数式/并发 | BEAM 后端，actor 容错 | **高（后端并发参考）** |
| Erlang | 函数式/并发 | 电信级 actor 并发鼻祖 | **高（后端并发参考）** |
| F# | 函数式 | .NET 上的 ML 家族 | 中（.NET 生态） |
| Fortran | 科学计算 | 数值计算鼻祖 | 低 |
| Gleam | 函数式 | BEAM 上的新函数式 | 低 |
| Go | 系统/并发 | **工业级后端**，goroutine/通道内建 | **高（后端对标）** |
| Groovy | 脚本/JVM | JVM 动态脚本 | 低 |
| Haskell | 函数式 | 纯函数式，类型类/惰性求值 | 中（类型系统参考） |
| Haxe | 多目标 | 一门语言编译到多后端 | 中 |
| Jai | 系统/游戏 | 游戏语言（未公开） | 低 |
| Java | 托管/OOP | **企业全栈**，JVM 常青树 | **高（企业后端对标）** |
| JavaScript | 脚本/动态 | Web 前端运行时 | **高（前端对标）** |
| Julia | 科学计算 | 多分派科学计算 | 低 |
| Kotlin | 托管/OOP | **JVM 全栈**（Android/服务端） | **高（全栈对标）** |
| Lisp | 函数式/Lisp | 代码即数据，宏鼻祖 | 低 |
| Lua | 脚本/嵌入式 | 极简嵌入式（Redis/游戏） | 中（简单端下限参考） |
| MATLAB | 科学计算 | 数值/矩阵计算 | 低 |
| Mojo | 科学计算/新 | Python 语法 + MLIR 性能 | 低 |
| Nim | 系统/编译 | Python 语法 + C 后端 + 元编程 | 中 |
| Objective-C | 托管/OOP | Apple 老牌，消息传递 | 低 |
| OCaml | 函数式 | ML 家族，模式匹配 | 低 |
| Odin | 系统/游戏 | 游戏/系统（Zig 同代） | 低 |
| Perl | 脚本/文本 | 文本处理老兵 | 低 |
| PHP | 脚本/Web | Web 后端主力 | 中（Web 后端参考） |
| PowerShell | 脚本/Shell | Windows 管理脚本 | 低 |
| Prolog | 逻辑 | 逻辑编程 | 低 |
| R | 科学计算 | 统计计算 | 低 |
| Ruby | 脚本/动态 | Web 后端（Rails 生态），元编程极强 | 中 |
| Rust | 系统/安全 | 所有权/借用，**工业级系统/后端** | **高（安全对标）** |
| Scala | 多范式 | JVM 函数式 + OOP | 低 |
| Scheme | 函数式/Lisp | 极简 Lisp | 低 |
| Solidity | 领域 | 区块链合约 | 低 |
| SQL | 领域 | 关系查询语言 | **高（数据库对标）** |
| Swift | 系统/OOP | Apple 现代语言，协议/ARC | 中（iOS/服务端） |
| TypeScript | 托管/类型化 | **全栈**（前端 + Node 后端） | **高（全栈对标）** |
| V | 系统/编译 | 极简系统语言 | 中（简单端参考，伸缩定位下可对照） |
| WebAssembly | 底层目标 | 字节码目标（非日常语言） | 中（多后端目标） |
| Zig | 系统 | 显式分配/comptime | 中 |

*EN: This table lists 42 languages with their category, one-line positioning, and relevance to tie.*

> 相关度评级（工业级全栈视角）：**高** = 全栈对标（TS/C#/Kotlin/Go/Rust/Dart/Java/JS/Erlang/Elixir）
> 或同路线（Crystal）；中 = 局部参考（后端/性能/类型）；低 = 领域差异大或不对标（Lua/V 等极简派）。
> EN: Relevance rating (from an industrial full-stack perspective): **High** = full-stack benchmark (TS/C#/Kotlin/Go/Rust/Dart/Java/JS/Erlang/Elixir) or same path (Crystal); Medium = partial reference (backend/performance/types); Low = large domain differences or not benchmarked (minimalist schools such as Lua/V).

---

## 3. 重点语言特性对比矩阵（16 种）

*EN: 3. Key Language Feature Comparison Matrix (16 languages)*

### 3.1 类型系统

*EN: 3.1 Type System*

| 特性 | tie | C | C++ | Rust | Zig | Go | Swift | Crystal | Nim |
|---|---|---|---|---|---|---|---|---|---|
| 整数/浮点/bool/char | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 三值逻辑 trit | ✅ 独有 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 字符串 | ✅ | ◐ char* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数组/动态表 | ✅ table | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 键值表 map | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 元组 | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 结构体/记录 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 指针/引用 | ✗ 无指针 | ✅ | ✅ | ✅ | ✅ | ◐ | ◐ | ◐ | ✅ |
| 枚举 enum | ✗ 规划 tag 表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 可选 Option/nullable | ✗ 空串/错误码 | ✗ | ◐ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ |
| 错误 Result/异常 | ✗ bool+错误码 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 切片/范围 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 泛型 | ◐ 仅 table\<T\> | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 类型推断 | ◐ 部分 | ✗ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 所有权/借用 | ✗ by_ref 简化 | ✗ | ◐ RAII | ✅ | ✗ | ✗ | ✗ | ✗ | ◐ |

*EN: Type system comparison — tie vs C, C++, Rust, Zig, Go, Swift, Crystal, Nim.*

| 特性 | tie | Java | C# | Kotlin | Python | Ruby | JS | TS | Dart | Haskell | Elixir |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 整数/浮点/bool/char | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 字符串 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数组/动态表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 键值表 map | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Hash | ✅ | ✅ | ✅ | ✅ | ✅ |
| 元组 | ✅ | ✗ | ✅ | ✅ | ✅ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 结构体/记录 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 枚举 enum | ✗ | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 可选 Option/nullable | ✗ | ◐ | ✅ | ✅ 空安全 | ✅ | ◐ nil | ✅ | ✅ | ✅ | ✅ | ✅ |
| 错误 Result/异常 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 切片/范围 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 泛型 | ◐ | ✅ | ✅ | ✅ | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ |
| 类型推断 | ◐ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 模式匹配 | ◐ 部分 | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |

*EN: Type system comparison — tie vs Java, C#, Kotlin, Python, Ruby, JS, TS, Dart, Haskell, Elixir.*

### 3.2 函数与抽象

*EN: 3.2 Functions and Abstractions*

| 特性 | tie | C | C++ | Rust | Zig | Go | Swift | Crystal | Nim |
|---|---|---|---|---|---|---|---|---|---|
| 闭包/匿名函数 | ✗ 规划 C1 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 函数指针/一等函数 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 迭代器/生成器 | ✗ | ✗ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| 类/继承 | ✗ 组合替代 | ✗ | ✅ | ✗ 组合 | ✗ | ✗ 组合 | ✅ | ✅ | ✅ |
| 接口/trait | ✗ 命名空间 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 宏/元编程 | ✗ tie-prep 弱替代 | ✅ | ✅ | ✅ | ✅ comptime | ✗ | ✅ | ✅ | ✅ 极强 |
| 反射 | ✗ | ✗ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 变参函数 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 解构赋值 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 运算符重载 | ✗ | ✗ | ✅ | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ |
| 模块/命名空间 | ✅ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 包管理器 | ✅ M6 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*EN: Functions and abstractions comparison — tie vs C, C++, Rust, Zig, Go, Swift, Crystal, Nim.*

| 特性 | tie | Java | C# | Kotlin | Python | Ruby | JS | TS | Dart | Haskell | Elixir |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 闭包/匿名函数 | ✗ 规划 C1 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 函数指针/一等函数 | ✗ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 迭代器/生成器 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 类/继承 | ✗ 组合替代 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 类型类 | ✅ |
| 接口/trait | ✗ 命名空间 | ✅ | ✅ | ✅ | ◐ | ◐ mixin | ◐ | ✅ | ✅ | ✅ 类型类 | ✅ |
| 宏/元编程 | ✗ tie-prep 弱替代 | ✗ | ✅ | ✅ | ✅ | ✅ 极强 | ✗ | ✗ | ✅ | ✗ | ✅ |
| 反射 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✗ |
| 变参函数 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ |
| 解构赋值 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 运算符重载 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ |
| 模块/命名空间 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 包管理器 | ✅ M6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*EN: Functions and abstractions comparison — tie vs Java, C#, Kotlin, Python, Ruby, JS, TS, Dart, Haskell, Elixir.*

### 3.3 内存与并发

*EN: 3.3 Memory and Concurrency*

| 特性 | tie | C | C++ | Rust | Zig | Go | Swift | Crystal | Nim |
|---|---|---|---|---|---|---|---|---|---|
| 自动内存管理 | ✅ 表作用域释放 | ✗ | ◐ RAII | ✅ 所有权 | ✗ allocator | ✅ GC | ✅ ARC | ✅ GC | ✅ GC |
| 手动指针/unsafe | ✗ 有意缺失 | ✅ | ✅ | ◐ unsafe | ✅ | ◐ unsafe | ◐ | ✗ | ◐ |
| 多线程 | ✗ | ◐ libc | ✅ | ✅ | ✅ | ✅ goroutine | ✅ | ✅ | ✅ |
| async/await 协程 | ✗ | ✗ | ✅ | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ |
| 通道/消息传递 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ channel | ✅ | ✅ | ✅ |
| 原子操作/锁 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 并发安全类型系统 | ✗ | ✗ | ✗ | ✅ Send/Sync | ✗ | ✗ | ✗ | ✗ | ✗ |

*EN: Memory and concurrency comparison — tie vs C, C++, Rust, Zig, Go, Swift, Crystal, Nim.*

| 特性 | tie | Java | C# | Kotlin | Python | Ruby | JS | TS | Dart | Haskell | Elixir |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 自动内存管理 | ✅ 表作用域释放 | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC | ✅ GC |
| 手动指针/unsafe | ✗ 有意缺失 | ✗ | ◐ unsafe | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 多线程 | ✗ | ✅ | ✅ | ✅ | ◐ GIL | ✅ Thread | ◐ worker | ◐ worker | ◐ isolate | ✅ | ✅ actor |
| async/await | ✗ | ✅ | ✅ | ✅ | ✅ | ◐ Fiber | ✅ | ✅ | ✅ | ✅ | ✅ |
| 通道/消息传递 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ actor |
| 原子操作/锁 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 并发安全类型系统 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ actor 隔离 |

*EN: Memory and concurrency comparison — tie vs Java, C#, Kotlin, Python, Ruby, JS, TS, Dart, Haskell, Elixir.*

---

## 4. 标准库对比（重点语言）

*EN: 4. Standard Library Comparison (Key Languages)*

| 能力域 | tie | C | C++ | Rust | Go | Python | Ruby | Java | C# | JS | TS | PHP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 字符串处理 | ✅ 全 | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 集合类（堆/栈/队列） | ◐ 部分 | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 集合类（Set） | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 文件系统 | ✅ std/fs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 路径处理 | ✅ | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 进程/环境 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 网络 socket（TCP/UDP） | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HTTP 客户端 | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HTTP 服务端 | ✗ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数据库访问 | ✗ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 正则表达式 | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ |
| JSON | ✅ | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 时间/日期 | ◐ 计时为主 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 随机数 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 排序/查找 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 压缩/编码 | ✅ zstd/brotli/lz4 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数学库 | ◐ 基础+扩展 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 格式化 | ◐ sprintf 部分 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 日志 | ✅ ext/log | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ | ✅ |
| 测试框架 | ✅ ext/test | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ | ✅ | ✅ |
| 基准计时 | ✅ ext/bench | ◐ | ✅ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ◐ | ✅ | ✅ |
| 命令行参数解析 | ◐ 基础 args | ✅ | ✗ | ✅ | ✅ | ✅ | ✅ | ✗ | ✅ | ◐ | ✅ | ✅ |
| Unicode/UTF-8 | ◐ utf 基础 | ✗ | ✗ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*EN: Standard library capability comparison across tie and key languages (string, collection, I/O, network, DB, encoding, etc.).*

---

## 5. 按全栈场景评估 tie 缺口

*EN: 5. Assessing tie's Gaps by Full-Stack Scenario*

### 5.1 后端场景（logic / library 角色）

*EN: 5.1 Backend Scenario (logic / library roles)*

| 能力 | 状态 | 缺口分析 |
|---|---|---|
| 编译/静态类型 | ✅ 强 | 全栈语言中类型能力第一梯队（trit 独有） |
| 文件/进程/环境 | ✅ | std/fs 已补齐 UTF-8 安全 |
| HTTP 客户端 | ✅ | std/http |
| **HTTP 服务端** | ✗ | 需 `std/net`（TCP）+ HTTP 解析层；全栈后端必备 |
| **TCP/UDP socket** | ✗ | 最大纯库缺口；Rust `std::net` 桥 + tie 封装 |
| **并发（多线程/通道/原子）** | ✗ | 语言级缺口；服务端承载能力的前提 |
| **async/await 或事件循环** | ✗ | 高并发 IO 场景（对标 Go goroutine / TS 事件循环） |
| **数据库访问** | ✗ | `db` 角色头已定义未实现；SQLite/MySQL 桥 + 访问层 |
| **SQL/查询能力** | ✗ | tie 有 `db` 角色设计，对标 SQL |
| 错误处理（bool/错误码） | ◐ | 可先用约定，工业级需 Result 式传播 |
| 日志 | ✅ | ext/log（i18n 消息系统） |
| 测试/基准 | ✅ | ext/test + ext/bench |

*EN: Backend capabilities gap assessment — compiling/types are strong, while networking, concurrency, and database access remain open gaps.*

### 5.2 UI 场景（ui 角色）

*EN: 5.2 UI Scenario (ui role)*

| 能力 | 状态 | 缺口分析 |
|---|---|---|
| **UI 工具链** | ✗ | `ui` 角色头已定义未实现；对标 Dart/Flutter、TS/React |
| 终端 UI（TUI） | ◐ | ext/tui（进度条/文本框，无 ANSI 限制） |
| 跨端渲染 | ✗ | 需选定渲染后端（终端 / Web / 原生） |
| 事件循环/消息驱动 | ✗ | 依赖并发基础 |

*EN: UI capability gap assessment — the ui role and terminal UI are defined, but the full UI toolchain and cross-platform rendering are not yet implemented.*

### 5.3 数据库与数据场景（db / data 角色）

*EN: 5.3 Database and Data Scenarios (db / data roles)*

| 能力 | 状态 | 缺口分析 |
|---|---|---|
| **数据交换格式** | ✅ | tie:data 角色 + JSON 库 |
| **数据库访问层** | ✗ | 需桥（SQLite 最优先）+ 查询/迁移工具 |
| 数据建模 | ◐ | struct + 命名空间可表达 |

*EN: Database and data capabilities gap assessment — data exchange is covered, but database access and full data modeling tooling are missing.*

### 5.4 工程化能力（工业级必备）

*EN: 5.4 Engineering Capabilities (required for industrial grade)*

| 能力 | 状态 | 缺口分析 |
|---|---|---|
| 包管理器 | ✅ M6 | path/git/registry 三源 |
| 构建/发布 | ✅ | package.ps1 + 可复现构建（Brepro） |
| LSP/IDE 支持 | ✅ | tie-lsp + VSCode 扩展 |
| **格式化/静态分析工具** | ◐ | 有 tie-prep；缺 formatter/linter 全功能 |
| **文档系统** | ◐ | 缺内置文档生成（对标 rustdoc/jsdoc） |
| **调试器** | ✗ | 依赖 LLDB 等外部 |
| 跨平台 | ◐ | Windows 成熟；linux/mac 待验证 |
| 性能基准 | ✅ | G4 闸门 + bench |

*EN: Engineering capability assessment — package management, build/release, and LSP/IDE support exist, while formatter/linter, documentation generation, debugger, and cross-platform maturity remain partial or missing.*

---

## 6. 语言级缺失清单（需扩展 tie 语言本身）

*EN: 6. Language-Level Missing Features List (requires extending the tie language itself)*

| 缺失功能 | 全栈影响 | 可参考实现 | 备注 |
|---|---|---|---|
| **多线程/并发原语** | 服务端承载、UI 响应 | Go goroutine / Erlang actor / Java 并发包 | 最大缺口；需设计共享可变状态模型 |
| **async/await 协程** | 高并发 IO、UI 事件循环 | TS/C#/Kotlin；Lua 协程仅作机制参考 | 依赖并发模型 |
| **通道/消息传递** | 后端任务协作 | Go channel / Erlang 消息 | 随并发一并设计 |
| **原子操作/锁** | 共享状态安全 | 各语言 std | 同上 |
| **闭包/匿名函数** | 回调、路由注册、UI 事件 | TS 箭头函数 / Ruby block | 规划中（C1 字符串分派替代路线） |
| **函数指针/一等函数** | 策略模式、插件化 | C / TS | 同上 |
| **完整泛型** | 通用数据结构复用 | Java/Rust/Kotlin 泛型 | 当前仅 table\<T\>/map\<T\> |
| **enum + 完整模式匹配** | 状态机、协议解析 | Rust/Haskell/TS 判别联合 | 规划中（B1 tag 表） |
| **trait/接口** | 插件/抽象层 | Go interface / Rust trait | 命名空间约定替代（静态） |
| **Option/Result 错误类型** | 工业级错误传播 | Rust / Kotlin 空安全 | bool+错误码替代 |
| **宏/元编程** | ORM/序列化代码生成 | Nim / Ruby 元编程 | tie-prep 转换器弱替代 |
| **反射/运行时类型信息** | ORM、动态分发 | Java/C#/Go | 与自举编译器设计冲突 |
| **变参函数** | 通用 API（printf 风格） | C variadic / TS rest | 语言层可补，小工作量 |

*EN: Missing language-level features, their full-stack impact, reference implementations, and notes on the current workaround path for each.*

---

## 7. 路线图建议（工业级全栈导向，按优先级）

*EN: 7. Roadmap Recommendations (industrial full-stack oriented, by priority)*

| 优先级 | 事项 | 场景 | 类型 | 参考 | 工作量 |
|---|---|---|---|---|---|
| P0 | TCP/UDP 网络库（`std/net`） | 后端 | 库级 | Go net / Rust std::net | 小（桥模式已成熟） |
| P0 | **HTTP 服务端** | 后端 | 库级 | Go net/http | 中（依赖 std/net） |
| P0 | **SQLite 数据库访问**（`std/db`） | 数据库 | 库级 | Rust rusqlite 桥 | 中（首个 db 角色落地） |
| P0 | 集合补全（HashSet/VecDeque） | 通用 | 库级 | C++ STL / Ruby Set | 小 |
| P1 | **并发原语**（thread/sync/atomic/通道） | 后端/UI | **语言级** | Go goroutine / Erlang actor | 大 |
| P1 | **async/await 或事件循环** | 后端/UI | 语言级+库级 | TS 事件循环 / Kotlin 协程 | 大 |
| P1 | **UI 工具链**（`ui` 角色落地） | UI | 库级+工具链 | Dart/Flutter 分层 | 大（终端先行，Web 后续） |
| P2 | enum（B1 tag 表）+ 模式匹配完善 | 通用 | 语言级 | Rust enum / Haskell ADT | 中（已在规划） |
| P2 | 函数指针/闭包（C1 字符串分派） | 通用 | 语言级 | TS 箭头函数 | 中（已在规划） |
| P2 | 文档生成器 | 工程化 | 库级 | rustdoc / jsdoc | 中 |
| P3 | Option/Result 错误类型 | 通用 | 语言级 | Swift / Kotlin | 中（需泛型支持） |
| P3 | 变参函数 | 通用 | 语言级 | TS rest / C variadic | 小 |
| P3 | formatter/linter | 工程化 | 库级 | gofmt / prettier | 中 |

*EN: Prioritized roadmap items with scenario, type (library vs language level), reference, and estimated effort.*

---

## 8. 结论

*EN: 8. Conclusion*

- tie 的**类型与单线程应用层能力**已对齐全栈语言（字符串/文件/JSON/正则/压缩/HTTP 客户端齐全），
  `logic` / `library` 角色已可用于后端工具与库开发；
- *EN: tie's **type and single-threaded application-layer capabilities** already match full-stack languages (strings/files/JSON/regex/compression/HTTP client are all covered), and the `logic` / `library` roles are already usable for backend tooling and library development;
- **后端场景**：最大缺口是 `std/net`（TCP/UDP）+ HTTP 服务端 + 数据库访问（`db` 角色落地）——
  三者均为**库级**工作，桥模式已验证（std/fs 先例），可在并发之前快速补齐；
- *EN: **Backend scenario**: the biggest gaps are `std/net` (TCP/UDP) + HTTP server + database access (`db` role implementation)—all three are **library-level** work, and the bridge pattern is already proven (the std/fs precedent), so these can be filled quickly before concurrency;
- **UI 场景**：`ui` 角色头已定义未实现，是独立的工具链工程，建议终端 UI 先行、跨端渲染后续；
- *EN: **UI scenario**: the `ui` role header is defined but not implemented; it is a standalone toolchain effort, and it is recommended to tackle terminal UI first and cross-platform rendering later;
- **数据库场景**：`db` 角色 + SQLite 桥是“全栈覆盖”的最短路径，优先级应高于语言级扩展；
- *EN: **Database scenario**: the `db` role + SQLite bridge is the shortest path to “full-stack coverage” and should be prioritized above language-level extensions;
- **并发是唯一需要语言级设计的缺口**，参考 Go goroutine 与 Erlang actor 两条路线，
  建议在 B1/C1（enum/函数指针）之后启动，与 async 一并设计；
- *EN: **Concurrency is the only gap requiring language-level design**; referencing the two paths of Go goroutines and Erlang actors, it is recommended to start it after B1/C1 (enum/function pointers) and design it together with async;
- **对标结论**：tie 的对标是一条**伸缩谱（丰俭由人）**——简单端参照 Lua / V（优雅克制），
  工程端参照 Go / Python（务实可靠），全栈端参照 TypeScript / Dart / C#（能力覆盖）；
  Crystal 的自举路线可对照。tie 的目标不是“像谁”，而是**按需伸缩**：简单场景不付复杂
  代价，全栈场景不缺工业能力。
- *EN: **Benchmark conclusion**: tie's benchmark is a **scalable spectrum (rich or lean as you choose)**—the simple end references Lua / V (elegant and restrained), the engineering end references Go / Python (pragmatic and reliable), and the full-stack end references TypeScript / Dart / C# (capability coverage). Crystal's self-hosting path serves as a reference point. tie's goal is not “to be like anyone,” but to **scale on demand**: simple scenarios do not pay the cost of complexity, and full-stack scenarios do not lack industrial capability.*