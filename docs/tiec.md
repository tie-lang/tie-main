# tiec —— tie 自举编译器
*EN: tiec — the tie self-hosting compiler*

> ⚠️ **早期开发阶段**：tiec 为自举 v2 的产物，随实现持续演进，功能与限制以本文件与源码为准。

> EN: ⚠️ **Early development stage**: tiec is a product of bootstrap v2 and keeps evolving with the implementation; features and limitations are as documented in this file and in the source.

tiec 是 tie 语言 **100% 自写**的完整命令行编译器，是自举 v2 计划（`compiler/` 目录）的最终交付物。
它由 tie 语言自身编写，经 stage0 入库二进制引导后可以编译自身，形成自举闭环（0-Rust）。
其命令行行为与消息格式对齐 Rust 老编译器（已归档至 [tiec_rust](https://github.com/tie-lang/tiec_rust)），可作为其替代品使用。

EN: tiec is a complete command-line compiler **100% written in tie**, and the final deliverable of the bootstrap v2 plan (the `compiler/` directory).
It is written in tie itself and, once bootstrapped by the checked-in stage0 binary, can compile itself to form a self-hosting loop (0-Rust).
Its command-line behavior and message format align with the old Rust compiler (archived at [tiec_rust](https://github.com/tie-lang/tiec_rust)), so it can be used as a drop-in replacement.

## 1. tiec 是什么
*EN: 1. What tiec is*

tiec（tie compiler）是一套完整的前端到后端编译流水线，全部代码用 tie 语言编写：

EN: tiec (tie compiler) is a complete front-to-back-end compilation pipeline, with all of its code written in the tie language:

| 能力 | 说明 |
| --- | --- |
| 语言 | 全部源码为 `.tie` 文件（`compiler/` 目录），零 Rust 代码 |
| 前端 | 词法分析（lexer）、语法分析（parser）、语义分析（semantic/checker） |
| 中端 | tie-IR 中间表示（列式表）、AST 到 tie-IR 生成（irgen）、LLVM IR 文本生成（llvmgen） |
| 后端 | 调用 LLVM 工具链（`opt` / `clang` / `llvm-ar` / `lld`）完成优化、汇编与链接 |
| 附赠 | tie 自写解释器（`compiler/interp/`）与 REPL（`compiler/repl.tie`） |
| 行为对齐 | 参数解析、角色分派、消息格式、退出码对齐 Rust 老编译器（tiec_rust 归档） |

EN: The table above (with Chinese descriptions) outlines the capabilities of tiec: it is written entirely in `.tie` files with zero Rust; its frontend covers lexer / parser / semantic analysis; its middle end covers the tie-IR representation, AST-to-tie-IR generation (irgen) and LLVM IR text generation (llvmgen); its backend uses the LLVM toolchain (`opt`/`clang`/`llvm-ar`/`lld`) for optimization, assembly and linking; it also bundles a tie-written interpreter and REPL; and its argument parsing, role dispatch, message format, and exit codes align with the archived Rust compiler (tiec_rust).

编译流水线：

EN: Compilation pipeline:

```
源码 .tie
   │
   ▼
┌──────────────┐   ┌─────────────────────────┐   ┌──────────────────┐
│ frontend     │ → │ middle + backend 前段    │ → │ backend toolchain │
│ lexer→parser │   │ irgen → llvmgen          │   │ opt / clang / ar  │
│ →semantic    │   │ （tie-IR → LLVM IR 文本） │   │ → 可执行 / .a     │
└──────────────┘   └─────────────────────────┘   └──────────────────┘
```

tiec 把 `.tie` 源文件编译为原生可执行文件（`logic`/`script` 角色）或静态库（`class`/`type` 角色），
中间产物经 `opt` 优化、`clang` 汇编链接，最终落在目标平台的可执行文件上。

EN: tiec compiles `.tie` source files into native executables (`logic`/`script` roles) or static libraries (`class`/`type` roles);
intermediate products are optimized by `opt`, assembled and linked by `clang`, and finally land as executables for the target platform.

## 2. 与老工具链的关系与自举链
*EN: 2. Relationship with the old toolchain and the self-hosting chain*

tie 语言现有编译器体系（Rust 参考编译器已归档至独立仓库
[tiec_rust](https://github.com/tie-lang/tiec_rust)，2026-08-15 从主仓库剔除）：

EN: The current compiler family of the tie language (the Rust reference compiler has been archived to its own repository
[tiec_rust](https://github.com/tie-lang/tiec_rust), removed from the main repo on 2026-08-15):

| 名称 | 实现语言 | 角色 |
| --- | --- | --- |
| `tiec.exe` | tie（`compiler/driver.tie` 编译而来） | 当前编译器，自举 v2 产物（0-Rust） |
| tiec_rust（归档） | Rust | 历史种子/参考编译器（bootstrap seed），已移至独立仓库 |

EN: The table above (with Chinese descriptions) lists the compiler family: `tiec.exe` is implemented in tie (compiled from `compiler/driver.tie`), is the current compiler and a bootstrap v2 artifact (0-Rust); tiec_rust (archived) is implemented in Rust, serving as the historical seed/reference compiler (bootstrap seed), now moved to its own repository.

自举链（bootstrap chain）如下：

EN: The bootstrap chain is as follows:

```
① tiec.exe（stage0 入库）编译 compiler/driver.tie  ──► tiec2.exe（二阶，自举闭环）
② tiec2.exe 编译 compiler/driver.tie               ──► tiec3.exe（再自举验证）
```

- **tiec.exe 已入库（阶段 A 升格）**：作为 stage0 引导二进制版本化随仓库分发
  （`.gitignore` 已豁免 `/compiler/tiec.exe`），clone 即用、无需先构建；此后 tiec
  始终由自身编译 driver.tie 产生（自举闭环），源码变更后重新自举并提交同步更新；
- **bootstrap 界限（历史）**：首次产生 tiec.exe 曾需要 Rust 种子（Rust 版
  tie-llvm.exe 编译 driver.tie，历史性接触点）；2026-08-15 起 Rust 参考编译器
  归档至 tiec_rust 独立仓库，主仓库 0-Rust；
- **第 ① 步**：tiec 编译自身成功，证明自举闭环；
- **第 ② 步**（T5.2 实测打通）：tiec2 再次编译自身并正确编译 `hello.tie`，二阶闭环验证通过；
- **阶段 A 升格（2026-08-13）**：`repl.exe` / `pkg.exe` 自举已由 tiec 承担
  （`scripts/package.ps1` 第 2 步用 tiec 编译 `repl/repl.tie`；`pkg/main.tie` 用 tiec
  编译）。irgen 补全 map 下标赋值/读取桥（`tie_map_set*` / `tie_map_get*`，E3 键值表）
  并修正 table 元素类型完整推断链后，tiec 可完整编译 pkg 包管理器；
- **G3 闸门（0-Rust）验证 PASS**：种子界限之后，编译、运行、REPL 全链路不再依赖 Rust。

- EN: **tiec.exe has been checked in (stage-A promotion)**: it is versioned and distributed with the repo as a stage0 bootstrap binary
  (`.gitignore` exempts `/compiler/tiec.exe`), usable right after clone without building first; thereafter tiec
  is always produced by compiling driver.tie with itself (self-hosting loop), and after source changes it is re-bootstrapped and the update committed in sync;
- EN: **bootstrap boundary (historical)**: producing the first tiec.exe once required a Rust seed (the Rust
  tie-llvm.exe compiled driver.tie, a historical point of contact); since 2026-08-15 the Rust reference compiler
  has been archived into the separate tiec_rust repo, making the main repo 0-Rust;
- EN: **Step ①**: tiec successfully compiles itself, proving the self-hosting loop;
- EN: **Step ②** (verified in practice at T5.2): tiec2 compiles itself again and correctly compiles `hello.tie`, passing the second-order loop verification;
- EN: **stage-A promotion (2026-08-13)**: bootstrapping `repl.exe` / `pkg.exe` is now handled by tiec
  (step 2 of `scripts/package.ps1` compiles `repl/repl.tie` with tiec; `pkg/main.tie` is compiled with tiec).
  After completing the map index assign/read bridges in irgen (`tie_map_set*` / `tie_map_get*`, E3 key-value tables)
  and fixing the full table element type inference chain, tiec can fully compile the pkg package manager;
- EN: **G3 gate (0-Rust) verification PASS**: after the seed boundary, the full chain of compile, run, and REPL no longer depends on Rust.

## 3. 快速开始
*EN: 3. Quick start*

### 发布包内已含编译好的二进制
*EN: The release package ships prebuilt binaries*

发布包 `bin/` 下已附带现成的 `tiec.exe`（约 2.5 MB）与 `tiec2.exe`（约 2.5 MB），
均已通过冒烟验证（编译 `examples/hello.tie` 并运行输出正确）。解包后可直接使用：

EN: The release package ships ready-made `tiec.exe` (about 2.5 MB) and `tiec2.exe` (about 2.5 MB) under `bin/`,
both smoke-tested (compiling `examples/hello.tie` and running it produces correct output). After unpacking, they can be used directly:

```bash
bin\tiec.exe examples\hello.tie     # 生成 examples\hello.exe
examples\hello.exe                  # 运行
```

发行 zip 同时内置精简 LLVM 工具链（`bin/llvm/`：clang / opt / llvm-ar / lld-link、
头文件与许可文本），解压即用，无需单独安装 LLVM。

EN: The release zip also bundles a minimal LLVM toolchain (`bin/llvm/`: clang / opt / llvm-ar / lld-link,
header files and license text), usable right after extraction without installing LLVM separately.

### 从源码构建 tiec
*EN: Building tiec from source*

前置依赖：LLVM 工具链（`opt`、`clang`、`llvm-ar`、`lld`）。无需 Rust（Rust 参考
编译器已归档至独立仓库 [tiec_rust](https://github.com/tie-lang/tiec_rust)）。

EN: Prerequisites: the LLVM toolchain (`opt`, `clang`, `llvm-ar`, `lld`). Rust is not needed (the Rust reference
compiler has been archived to its own repository [tiec_rust](https://github.com/tie-lang/tiec_rust)).

```bash
# ① 用已入库的 stage0 tiec.exe 编译自身（自举）
compiler\tiec.exe compiler\driver.tie -o compiler\tiec2.exe

# ② 二阶验证：tiec2 再编译自身
compiler\tiec2.exe compiler\driver.tie -o compiler\tiec3.exe
```

LLVM 工具发现顺序：`TIE_LLVM_HOME\bin` → tiec.exe 同目录 `llvm\bin` → `PATH`
→ 固定目录（`D:\LLVM\bin`、`C:\Program Files\LLVM\bin`、`C:\LLVM\bin`）。
发行版 zip 内置精简 LLVM（`bin/llvm/`），`TIE_LLVM_HOME` 指向它即开箱即用。
链接时若缺少运行时静态库，需要先构建 `std/runtime.a`（见第 5 节）。

EN: LLVM tool discovery order: `TIE_LLVM_HOME\bin` → `llvm\bin` next to tiec.exe → `PATH`
→ fixed directories (`D:\LLVM\bin`, `C:\Program Files\LLVM\bin`, `C:\LLVM\bin`).
The release zip bundles a minimal LLVM (`bin/llvm/`); pointing `TIE_LLVM_HOME` at it works out of the box.
If the runtime static library is missing at link time, build `std/runtime.a` first (see section 5).

## 4. CLI 用法
*EN: 4. CLI usage*

```
tiec <input.tie> [-o <out>] [-O0|-O1|-O2|-O3] [--target <三元组>]
                 [--emit-ir] [--keep-ir] [--prep-only] [--config <f>] [--help]
```

### 选项
*EN: Options*

| 选项 | 说明 |
| --- | --- |
| `<input.tie>` | 输入源文件（必需） |
| `-o <file>` | 输出文件路径。logic/script 角色默认输出输入同名 `.exe`，class/type 角色默认输出同名 `.a` |
| `-O0` / `-O1` / `-O2` / `-O3` | 优化级别，映射到 `opt -O{0..3}`，默认 `-O2` |
| `--target <三元组>` | 交叉编译目标（如 `x86_64-pc-windows-msvc`），默认本机 |
| `--emit-ir` | 只生成 LLVM IR（`.ll`），不继续编译 |
| `--keep-ir` | 保留中间 IR 文件（`.ll` / `.opt.ll`） |
| `--prep-only` | 只做头部识别并打印识别结果，不编译 |
| `--config <f>` | 协调统筹配置文件（单文件编译时暂忽略） |
| `--help` / `-h` | 显示帮助 |

EN: The table above (with Chinese descriptions) documents the CLI options: `<input.tie>` is the required input source; `-o <file>` sets the output path (executables default to the input name with `.exe` for logic/script, `.a` for class/type); `-O0..-O3` map to `opt -O{0..3}` with a default of `-O2`; `--target <三元组>` sets a cross-compilation target (default native); `--emit-ir` emits LLVM IR (`.ll`) only; `--keep-ir` keeps intermediate IR files (`.ll` / `.opt.ll`); `--prep-only` only does header recognition and prints the result without compiling; `--config <f>` selects a coordination config file; and `--help`/`-h` shows help.

### 退出码
*EN: Exit codes*

| 退出码 | 含义 |
| --- | --- |
| `0` | 编译成功 |
| `1` | 编译失败（源码读取失败 / 语法错误 / 语义错误 / 后端错误） |
| `2` | 参数错误（非法选项、缺少参数等） |

EN: The table above lists the exit codes: `0` on successful compilation, `1` on compilation failure (source read failure / syntax error / semantic error / backend error), and `2` on argument errors (invalid option, missing argument, etc.).

### 角色识别
*EN: Role recognition*

tiec 通过**头部扫描**识别源文件角色：读取源文件最前面的连续前导行，
查找 `type tie` / `type tie<X>` 声明（不依赖 prep 模块的 import 机制）。

EN: tiec identifies the source-file role by **header scanning**: it reads the leading consecutive lines at the top of the source
and looks for a `type tie` / `type tie<X>` declaration (independent of the prep module's import mechanism).

| 头部声明 | 角色 | 行为 |
| --- | --- | --- |
| `type tie<logic>` / `type tie<script>` | 逻辑 / 脚本 | 编译为可执行文件 |
| `type tie<class>` / `type tie` | 类/库 / 泛型入口 | 编译为静态库 `.a` |
| `type tie<ir>` | IR | 直接生成 LLVM IR（`.ll`），不继续 opt/clang 链接（等价 `--emit-ir`） |
| `type tie<data>` / `type tie<ui>` / `type tie<db>` / `type tie<port>` | 数据 / 界面 / 数据库 / 端口 | 提示对应工具链未实现 |

EN: The table above (with Chinese descriptions) shows role recognition: `type tie<logic>`/`type tie<script>` compile to an executable; `type tie<class>`/`type tie` compile to a static library `.a`; `type tie<ir>` emits LLVM IR directly (equivalent to `--emit-ir`); and `type tie<data>`/`type tie<ui>`/`type tie<db>`/`type tie<port>` report that the corresponding toolchain is not implemented.

未声明头时按 `logic` 处理。
文件名为 `xxx.<角色>.tie` 时可作为默认角色（如 `lib_math.class.tie`），但头部声明
优先——文件名与头部不一致时**警告并采用头部声明**。

EN: If no header is declared, the file is treated as `logic`.
A file name like `xxx.<角色>.tie` can serve as the default role (e.g. `lib_math.class.tie`), but the header declaration
takes priority — when the file name and header disagree, tiec **warns and follows the header declaration**.

### opt / target 仅 CLI
*EN: opt / target are CLI-only*

```
CLI 显式（-O0..-O3 / --target）  >  默认（-O2 / 本机）
```

优化级别与交叉编译目标**不再支持头部指令**（旧 `// tie:opt=` / `// tie:target=`
已随 `// tie:xxx` 注释指令体系一并移除）：只在命令行显式指定，缺省回落默认值。

EN: Optimization level and cross-compilation target **no longer support header directives** (the old `// tie:opt=` / `// tie:target=`
were removed together with the whole `// tie:xxx` comment-directive system): they are only specified explicitly on the command line, falling back to defaults when omitted.

### 示例
*EN: Examples*

```bash
tiec hello.tie                  # 编译 → hello.exe（默认 -O2）
tiec hello.tie -o out.exe -O0   # 指定输出与关闭优化
tiec lib_math.tie               # class 角色（type tie<class>）→ lib_math.a
tiec hello.tie --emit-ir        # 只生成 hello.ll
tiec hello.tie --keep-ir        # 编译并保留中间 IR
tiec hello.tie --prep-only      # 只打印角色识别结果
tiec --help                     # 帮助
```

## 5. 运行时依赖
*EN: 5. Runtime dependencies*

tiec 链接用户程序时需要一个运行时静态库：

EN: When linking user programs, tiec needs a runtime static library:

| 产物 | 说明 |
| --- | --- |
| `std/runtime.a` | tie 自写运行时静态库（T4.5）。由 `std/runtime.tie` 编译而来，提供 `tie_exec_code` / `tie_get_env` / `tie_time_now` 等桥符号，顶层裸函数不 mangle，与语言底座 `extern fn` 声明字节级匹配 |
| `tie_interp.lib` | 历史回退（Rust tie-interp 静态库）。`std/runtime.a` 不存在时作为备选链接 |

EN: The table above lists the runtime artifacts: `std/runtime.a` is the tie-written runtime static library (T4.5), compiled from `std/runtime.tie`, providing bridge symbols such as `tie_exec_code` / `tie_get_env` / `tie_time_now`, with top-level bare functions unmangled and byte-for-byte compatible with the language base `extern fn` declaration; `tie_interp.lib` is a historical fallback (Rust tie-interp static library) used only when `std/runtime.a` is absent.

**G3 闸门验证**：移走 Rust `tie_interp.lib` 后，tiec 仍能编译并运行
`exec_code` / `time_now` / `get_env` 程序，运行时栈 Rust-free 检查通过。
`std/runtime.a` 是 0-Rust 链路的关键一环，链接用户程序时必需。

EN: **G3 gate verification**: after removing the Rust `tie_interp.lib`, tiec can still compile and run
`exec_code` / `time_now` / `get_env` programs, and the Rust-free runtime-stack check passes.
`std/runtime.a` is a key link in the 0-Rust chain and is required when linking user programs.

### LLVM 工具链依赖
*EN: LLVM toolchain dependencies*

- **工具发现顺序**：`TIE_LLVM_HOME\bin` → tie.exe/tiec.exe 同目录 `llvm\bin`（Rust 侧）→
  `PATH` → 固定目录（`D:\LLVM\bin`、`C:\Program Files\LLVM\bin`、`C:\LLVM\bin`）；
- **vendored 发行说明**：发行版 zip 内置精简 LLVM 工具链（`bin/llvm/`，含 clang / opt /
  llvm-ar / lld-link 与头文件），`TIE_LLVM_HOME` 指向 `bin/llvm` 即开箱即用，无需单独安装 LLVM；
- **`-fuse-ld=lld` 仅 vendored 场景生效**：clang 来自随包 LLVM（`TIE_LLVM_HOME` 已设置 / 命中
  同目录 `llvm\bin`）时，链接命令加 `-fuse-ld=lld`，让随包的 lld-link.exe 在无 MSVC/VS 的机器上
  完成链接；普通开发机（clang 来自 PATH / 固定目录，VS link.exe 可用）保持默认链接器。原因：
  lld 解析 Rust 静态库 tie_interp.lib 存在 CRT 缺陷（`undefined symbol: printf`），开发机必须保留 link.exe；
- **已知限制**：vendored 且无 MSVC/VS 的环境下，链接使用 tie-interp C ABI 桥的程序（REPL 内建
  read_line / eval，或由 Rust 静态库 tie_interp.lib 支撑的 std 函数）会因 lld 的 CRT 解析缺陷报
  `undefined symbol: printf`；普通程序（不经过 interp 桥）用随包 lld 链接正常。随包的
  repl.exe / pkg.exe 在打包机（装有 VS）上预构建，终端用户不受影响——该限制只影响在无 VS 环境下
  重编 interp 桥程序；
- **LLVM 许可**：`third_party/llvm/LICENSE.TXT` 保存 LLVM 官方许可（Apache-2.0 with LLVM
  Exceptions），随包分发为 `bin/llvm/LICENSE.txt`。

- EN: **tool discovery order**: `TIE_LLVM_HOME\bin` → `llvm\bin` next to tie.exe/tiec.exe (Rust side) →
  `PATH` → fixed directories (`D:\LLVM\bin`, `C:\Program Files\LLVM\bin`, `C:\LLVM\bin`);
- EN: **vendored release note**: the release zip bundles a minimal LLVM toolchain (`bin/llvm/`, containing clang / opt /
  llvm-ar / lld-link and header files); pointing `TIE_LLVM_HOME` at `bin/llvm` works out of the box without installing LLVM separately;
- EN: **`-fuse-ld=lld` applies only in the vendored scenario**: when clang comes from the bundled LLVM (`TIE_LLVM_HOME` is set / the sibling
  `llvm\bin` is hit), the link command adds `-fuse-ld=lld`, letting the bundled lld-link.exe do the linking on machines without MSVC/VS;
  normal dev machines (clang from PATH / fixed dirs, VS link.exe available) keep the default linker. Reason:
  lld has a CRT defect parsing the Rust static library tie_interp.lib (`undefined symbol: printf`), so dev machines must keep link.exe;
- EN: **known limitation**: in vendored environments without MSVC/VS, linking programs that use the tie-interp C ABI bridge (REPL built-in
  read_line / eval, or std functions backed by the Rust static library tie_interp.lib) fails with
  `undefined symbol: printf` due to lld's CRT parsing defect; ordinary programs (not going through the interp bridge) link fine with the bundled
  lld. The bundled repl.exe / pkg.exe are prebuilt on the packaging machine (which has VS), so end users are unaffected — this limitation only affects
  recompiling interp-bridge programs in a VS-less environment;
- EN: **LLVM license**: `third_party/llvm/LICENSE.TXT` holds the official LLVM license (Apache-2.0 with LLVM
  Exceptions), distributed in the package as `bin/llvm/LICENSE.txt`.

## 6. 架构与模块
*EN: 6. Architecture and modules*

编译器源码位于 `compiler/` 目录，全部为 tie 语言文件：

EN: The compiler source lives in the `compiler/` directory, all of it tie language files:

```
compiler/
├── driver.tie          CLI 完整编译器入口（T3.2）→ 编译为 tiec.exe
├── driver-lite.tie     T2.9 临时入口（组装验证用，gen_src 路径）
├── repl.tie            REPL 主循环（T4.3）→ 编译为 repl.exe
├── lib/                基础库：interner（字符串池）/ columnar（列式表）/ dispatch（分派表）
├── frontend/           前端：lexer（词法）→ parser（语法）→ semantic（语义，AST 为列式 tag 表 arena）
├── middle/             tie-IR（列式函数/块/指令表）+ pass 管线（AnalysisManager 惰性 + 失效追踪）
├── backend/            后端：irgen（AST → tie-IR）+ llvmgen（tie-IR → LLVM IR 文本，单调 %N 直生）
│                       + toolchain.tie（opt / clang / llvm-ar / lld 驱动）
├── interp/             tie 自写树遍历解释器（value / session / interp / env，T4.1–4.2）
├── proto/              各阶段原型（T1–T2 期间探索用，正式版不依赖）
├── tests/              测试套件：错误 golden 语料 / pass 测试 / interp 行为测试（11 文件 198 断言）/ 运行器
├── tiec.exe / tiec2.exe  编译产物（种子版 / 自举版）
└── README.tie          目录说明（架构注释）
```

### 各模块职责
*EN: Module responsibilities*

| 模块 | 职责 |
| --- | --- |
| `driver.tie` | CLI 壳：参数解析、角色分派、消息格式、退出码。组装 frontend（parse_ast / check_ast）+ irgen.gen_ast / llvmgen.emit + backend/toolchain |
| `frontend/lexer` | 词法分析：token 化 + 字符串池 intern |
| `frontend/parser` | 语法分析：生成内存 AST（列式 tag 表），build_protocol 序列化（driver-lite 路径用） |
| `frontend/semantic` | 语义分析：符号表 / 类型检查，输出 check_impl 后的内存状态供 irgen 复用 |
| `middle/` | tie-IR 列式表表示与 pass 基础设施 |
| `backend/irgen` | AST → tie-IR 生成（T5.3 起主路径走 gen_ast 内存态，避免重复前端） |
| `backend/llvmgen` | tie-IR → LLVM IR 文本生成（自举后端单调编号） |
| `backend/toolchain.tie` | 工具链驱动：工具发现、`opt -O{0..3} -S`、`clang` 链接（含 `--target` 交叉、`-Wl,/Brepro` 可复现）、`clang -c` + `llvm-ar rcs` 库编译、进程退出码与 stderr 捕获 |
| `interp/` | 树遍历求值器：Value 编码（节点 id + 平行表）、Session（globals/funcs/AST 归档池）、eval/eval_call、C ABI 桥 tie 化（env.tie） |
| `tests/` | 错误 golden 语料（63 触发）、interp 行为测试、行为等价回归 |

EN: The table above (with Chinese descriptions) details module responsibilities: `driver.tie` is the CLI shell (argument parsing, role dispatch, message format, exit codes) composing frontend + irgen.gen_ast / llvmgen.emit + backend/toolchain; `frontend/lexer` tokenizes and interns into the string pool; `frontend/parser` builds the in-memory AST (columnar tag tables) and serializes build_protocol (for the driver-lite path); `frontend/semantic` does symbol-table/type checking and outputs post-check_impl in-memory state for irgen; `middle/` provides the tie-IR columnar representation and pass infrastructure; `backend/irgen` generates AST → tie-IR (running the main path through the gen_ast in-memory state since T5.3 to avoid a repeated frontend); `backend/llvmgen` generates tie-IR → LLVM IR text (monotonic numbering in the self-hosting backend); `backend/toolchain.tie` drives the toolchain (tool discovery, `opt -O{0..3} -S`, `clang` linking incl. `--target` cross and `-Wl,/Brepro` reproducibility, `clang -c` + `llvm-ar rcs` library compilation, process exit codes and stderr capture); `interp/` is the tree-walking evaluator (Value encoding, Session, eval/eval_call, tie-ified C ABI bridge via env.tie); and `tests/` covers error golden corpora, interp behavior tests, and behavior-equivalence regressions.

### 性能要点（T5.3）
*EN: Performance highlights (T5.3)*

- 主路径使用 `gen_ast()` 复用前端内存态，**消除前端重复执行**（`gen_src` 仅留给 driver-lite）；
- `build_protocol` 分治 join，`O(n²)` 降到 `O(n log n)`；
- 字符串池 intern 二分定位 + 位移插入，省去冒泡交换；
- AST 内存直拷（copy_ast_tables / append_ast_mem），消除文本协议往返。

- EN: the main path uses `gen_ast()` to reuse the frontend in-memory state, **eliminating repeated frontend execution** (`gen_src` is left only for driver-lite);
- EN: `build_protocol` uses divide-and-conquer join, reducing `O(n²)` to `O(n log n)`;
- EN: string-pool intern uses binary-search positioning + shift insertion, avoiding bubble swaps;
- EN: AST tables are copied directly in memory (copy_ast_tables / append_ast_mem), removing the text-protocol round trip.

## 7. 自举 v2 进度
*EN: 7. Bootstrap v2 progress*

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| T1.1–T1.5 | 词法/语法原型 + G1 性能闸门 | ✅ 完成 |
| T2.4–T2.6 | 完整词法 / 语法 / 语义分析器（正式版，tie 重写前端） | ✅ 完成 |
| T2.7 | 错误 golden corpus（63 触发 + 语义检查补齐） | ✅ 完成 |
| T2.8 | LLVM IR 文本生成端到端（irgen + llvmgen，opt + clang 编译运行） | ✅ 完成 |
| T2.9 | tiec 组装（driver-lite）+ 行为等价回归（等价率 100%） | ✅ 完成 |
| T3 | tiec 完整编译器：工具链驱动 + CLI + 可复现构建（Brepro） | ✅ 完成 |
| T4.1–T4.4 | 解释器 tie 化：core（eval/eval_call）+ 环境原语 + REPL parity + 测试移植（11 文件 198 断言） | ✅ 完成 |
| T4.5–T4.6 | tie 运行时静态库（`std/runtime.a` 替代 Rust interp 链接）+ G3 闸门（0-Rust） | ✅ 完成 |
| T5.1 | tiec 前端全局表修复（自编译成功）+ G4 性能基准建立 | ✅ 完成 |
| T5.2 | irgen 扩展修复 13 个自举编译 bug + 自举链二阶闭环打通（tiec → tiec2 → tiec3） | ✅ 完成 |
| T5.3 | tiec 性能优化（消除重复前端 / AST 内存传递 / intern 二分 / build_protocol 分治 / print_err 清理），G4 总比 6.9 → 1.09，hello 反超 Rust 种子 | ✅ 完成 |
| T5 后续 | irgen 最小集扩展（前端已就绪，扩展后 G4 覆盖自动扩全） | 📋 进行中 |

EN: The table above (with Chinese descriptions) tracks the bootstrap v2 progress: stages T1.1 through T5.3 are complete (✅), covering lexical/syntax/semantic analyzers, end-to-end LLVM IR text generation, tiec assembly with 100% behavior equivalence, the full CLI + reproducible builds, the tie-ified interpreter with REPL parity and test porting, the tie runtime static library with the G3 gate, the self-compilation fix, the second-order self-hosting loop closure, and the T5.3 performance optimizations (G4 total ratio 6.9 → 1.09, hello outperforming the Rust seed). The T5 follow-up (irgen minimal-set extension) is in progress (📋).

## 8. 已知限制与当前状态
*EN: 8. Known limitations and current status*

- **角色支持**：当前只编译 `logic`/`script`（可执行）与 `class`/`type`（静态库）、`ir`（直接产出 `.ll`）；`data` / `ui` / `db` / `port` 角色提示挂接点未实现；
- **T5 后续进行中**：irgen 最小集扩展仍在推进；**enum 已实现（2026-08-15，无数据/带数据/泛型变体 + 构造/匹配全链路）**，函数指针方向的 C1 规划仍待覆盖；
- **解释器桥限制**：需要指针类型的桥函数（如 file_read / str_char / rand_range / arg_*）无法 tie 化，仍走 Rust 底座转发；
- **自举细节**：tiec 由 stage0 入库二进制自举（曾由 Rust 种子编译，历史 bootstrap 界限），此后 0-Rust；Rust 参考编译器已归档至 tiec_rust 独立仓库。

- EN: **role support**: currently only `logic`/`script` (executable), `class`/`type` (static library), and `ir` (emit `.ll` directly) are compiled; the `data`/`ui`/`db`/`port` roles report that their hooks are not implemented;
- EN: **T5 follow-up in progress**: the irgen minimal-set extension is still ongoing; **enum is implemented (2026-08-15, data-less / data-carrying / generic variants + full construction/matching path)**, while the C1 plan toward function pointers remains to be covered;
- EN: **interpreter-bridge limitation**: bridge functions that require pointer types (e.g. file_read / str_char / rand_range / arg_*) cannot be adopted into tie and still go through the Rust backend;
- EN: **self-hosting detail**: tiec is bootstrapped from the checked-in stage0 binary (once compiled by the Rust seed — a historical bootstrap boundary), and has been 0-Rust since; the Rust reference compiler has been archived into the separate tiec_rust repo.

---

本文档随发布包分发，与 `docs/language.md`（语法规范）配合使用。
编译链路、CLI 细节与里程碑更新见根目录 `README.md` 与 `CHANGELOG.md`。

EN: This document is distributed with the release package and is meant to be used together with `docs/language.md` (the syntax specification).
For compilation-pipeline details, CLI details, and milestone updates, see the root `README.md` and `CHANGELOG.md`.