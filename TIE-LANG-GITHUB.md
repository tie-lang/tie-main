## What We Do

我们在做一门叫 **tie** 的语言——一门全栈通用编程语言。
We're building a language called **tie** — a full-stack, general-purpose programming language.

目标简单：全领域通用，Python 的体验，Rust 的性能与安全。
Simple goal: universal across every domain — the experience of Python, the performance and safety of Rust.

我们来真的，不是 PPT：
This is real work, not a slide deck:

- **tiec 是自举编译器**，用 tie 100% 写自己，0-Rust，自举产物逐字节复现，闭环跑得通。
  **tiec is a self-hosting compiler**, written 100% in tie itself, 0-Rust; the bootstrap output reproduces byte-for-byte and the loop runs end to end.
- **泛型已落地**，编译期单态化全链路打通。
  **Generics shipped**, with the full pipeline of compile-time monomorphization.
- **标准库自给自足**：字符串/编码（string、utf、json、regex）、数据结构与算法（sort、collection、crypto、graph、linalg、math）、IO 与系统（fs、http、net、db、time）。
  **Self-sufficient standard library**: strings/encoding (string, utf, json, regex), data structures & algorithms (sort, collection, crypto, graph, linalg, math), IO & system (fs, http, net, db, time).
- **配套齐全**：prep 预处理器、包管理器 pkg、REPL、tieDB 数据库接口库、rdu 嵌入式基础层。
  **Full toolkit**: prep preprocessor, pkg package manager, REPL, tieDB database layer, rdu embedded low-level layer.

语言还在快速迭代，语法随时可能变，暂不建议上生产。
The language is still iterating fast and the syntax can change anytime — not recommended for production yet.

## About Us

我们由广大社区开发者与FranJ2核心成员组成。
We're made up of the wider community of developers and the core FranJ2 members.

## Repositories

tie-main：编译器，预处理器，核心库，REPL，数据库，包管理器，一些示例程序
tie-main: the compiler, preprocessor, core libraries, REPL, database, package manager, plus some examples.

tie-rust：种子编译器
tie-rust: the seed compiler.

## How to Help

- **试一把，然后把话说得难听点**。编译器早期最缺的不是夸，是真实的报错。你跑崩了、报错看不懂、文档没讲清 —— 直接提 issue，越具体越好。
  **Give it a try — and be blunt.** An early compiler needs real bug reports more than praise. Crashed, cryptic errors, unclear docs — file an issue; the more specific, the better.
- **提 issue / 建议**：某个语法你用着别扭、某个标准库缺函数、想支持某个特性，都可以提。我们会看，会权衡，但不保证都能马上做。
  **File issues / suggestions**: an awkward syntax, a missing stdlib function, a feature you want — all welcome. We'll read them and weigh in, but no promise it ships right away.
- **贡献代码**：给 PR 之前，先看看 docs/ 和 README，语言还在变，先对齐再动手，别白写。改完记得跑回归，自举编译器容错没那么好。
  **Contribute code**: check docs/ and README before opening a PR. The language is still changing — align first, don't write blindly. Run the regression after your changes; the self-hosting compiler tolerates errors less kindly.
- **点个星**：哪怕只是觉得方向有趣，也帮我们撑撑场面。
  **Star us**: even just finding the direction interesting helps us keep the lights on.

语言还年轻，路还长，你能来搭把手，我们挺高兴的。
The language is young, the road is long — and we're glad if you lend a hand.

欢迎各位开发者前来围观、试用、共建 —— tie 的大门随时敞开。
Developers are welcome to drop by, try it out, and build with us — tie's door is always open.