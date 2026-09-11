# ROAD — tie 开发计划（2026.2）

*EN: ROAD — tie Development Plan (2026.2)*

> **定位**：2026.2 采用「预发布 → 正式版」两段式开发，延续 2026.1 的双轨模式。
>
> - **预发布段（p.7）**：全部新功能在 p.7.x 开发模块完成，开发号 **P.x.y.z**
>   （即 CHANGELOG 中的 p.x.y.z；模块 p.7.1=编译器重构与插件化 / p.7.2=编译体验 /
>   p.7.3=语言特性 / p.7.4=语法糖 / p.7.5=内置库补全 / p.7.6=trm 运行时 VM /
>   p.7.7=trm-lite 协程 / p.7.8=tiu UI 框架 / p.7.9=平台与后端 / p.7.10=工具链 /
>   p.7.11=生态应用 / p.7.12=仓库与发行）。
> - **正式版段（r.2）**：p.7 发布后启动，**基于 p.7** 开发——**不引入任何新功能**，
>   只做优化与稳定性；开发号 **R.x.y.z**。两轨独立编号、不互相延续。
> - **当前状态（2026-09-11）**：2026.1（Harbor）已正式发布；**p.7 分支已创建**
>   （基于 main），2026.2 全部开发在 p.7 分支上进行。
> - **内部代号**：2026.2 = **Shipyard 造船厂**；编译器彻底重构进入 **Keel 龙骨架构**
>   时代（详见 docs/release.md、docs/designs/keel-architecture.md）。
> - **历史路线图**：2026.1 ROAD 已归档至 [tie-lang/old_docs](https://github.com/tie-lang/old_docs)
>   （2026.1/ROAD.md）。

EN: 2026.2 follows the two-stage "preview → stable" development model, continuing the
dual-track scheme of 2026.1. The preview stage (p.7) does all new features under p.7.x
modules, numbered P.x.y.z (p.x.y.z in the CHANGELOG). The stable stage (r.2) starts after
p.7 ships, is based on p.7, introduces NO new features — only optimization and
stability — and numbers its work R.x.y.z. The two tracks number independently.
Codename: **Shipyard (2026.2)**; compiler restructure is the **Keel Architecture** era.
The 2026.1 ROAD was archived to tie-lang/old_docs (2026.1/ROAD.md). All 2026.2
development happens on branch p.7.

### 编译器重构与插件化（p.7.1，Keel 龙骨架构）

> 依据：docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（定稿）+ docs/designs/keel-architecture.md。
> 核心只余机制层（注册表/审计器/加载器/执行骨架，零行为），一切行为皆为注册项；
> 插件/包经 tieir 分发与审计链入港。落地顺序以本 ROAD 的 p.7.1.x 为准
> （原设计稿的步骤编号作废，一律 p.x.y.z）。
>
> EN: Basis: the finalized Keel design (plugin-kernel-design.md + keel-architecture.md).

- [ ] p.7.1.1 核心微内核化：pipeline 5 槽 → 注册表执行骨架 + 内建引导集（默认管线注册项）；passmanager 接入 pipeline（验收：tiec 自举 hash 不变 + 回归基线保持）
- [ ] p.7.1.2 id+version：注册项 schema 表驱动 + 同 id 异 version 仲裁（验收：注册冲突负例正确拦截）
- [ ] p.7.1.3 tieir 消费入口：import tieir 包（消费方免前端）（验收：包 .tieir → 编译运行通过）
- [ ] p.7.1.4 data→zd 发布转换（publish 压缩 + 指纹计算）（验收：zd 包加载运行与 data 等价）
- [ ] p.7.1.5 TSHA1 审计链接入（文件 tsha1f + 包树根 tsha1x + 凭证指纹审计链）（验收：篡改/冒名包负例全拦截）
- [ ] p.7.1.6 CLI 子命令注册化 + 库树收敛（std/ext/rdu ↔ lib_v1 定位）（验收：全命令行按注册项分派）
- [ ] p.7.1.7 安全算法底座：SHA-2/SHA-3/BLAKE/XXH3、MAC（HMAC/Poly1305/Ascon-MAC）、对称（AES/ChaCha20）、KDF（HKDF/PBKDF2/scrypt/Argon2id）、非对称（Ed25519/X25519/RSA）、后量子（ML-KEM/ML-DSA/SLH-DSA）分类入 std/ext/rdu；TSHA1 优先（审计链前置依赖）
- [ ] p.7.1.8 TSHA（tsha1 代）四档家族落地：f/b/x/r，位平面 trit + 24/48 基，KAT 向量 + 交叉验证

### 编译体验（p.7.2）

- [ ] p.7.2.1 编译资源可调：内存上限 / 并发度 / 优化档位可配置，老电脑可按需降低编译资源占用换可用性
- [ ] p.7.2.2 编译速度提升：增量编译 / 并行编译 / 编译缓存

### 语言特性（p.7.3）

- [ ] p.7.3.1 const fn 编译期求值：编译期常量折叠更强能力，可行静态元编程
- [ ] p.7.3.2 错误处理统一：Option/Result 泛型增强 + `?` 解包深化；tie 无异常保持
- [ ] p.7.3.3 泛型增强：约束 / 特化 / 变长泛型
- [ ] p.7.3.4 模式匹配增强：enum payload 结构化解构 / 穷尽检查 / 守卫（联动 p.7.4 语法糖）
- [ ] p.7.3.5 可空类型（路线 2：增强 Option）：不引入 `T?` 类型标记，保持「无 null」安全目标；`?.` 安全调用 / `?:` 默认值 / `a?[i]` 安全索引 / unwrap 语法糖（联动 p.7.4）

### 语法糖（p.7.4）

> 现状盘点：已有元组解构 `var (a,b)`、switch 解构/区间/守卫、`for i in 0..10`、标签、
> 默认参数、语句级宏（p.6.2.3）、`?` 解包、闭包、数据流箭头 `->`/`<-`（P1 已实现：
> `x <- data` / `data -> x` 传参与赋值，acceptance tests/_p2b_probe/p1_arrow.tie）。
>
> EN: Current sugar inventory and planned additions below.

- [ ] p.7.4.1 可空链语法：`?.` 安全调用 / `?:` 默认值 / `a?[i]`（联动 p.7.3.5）
- [ ] p.7.4.2 常用糖集：for..in 解构迭代 / 级联调用 / 命名参数 / 链式比较
- [ ] p.7.4.3 宏升级：p.6.2.3 语句级宏 → 完整元编程（卫生宏 / 声明式宏，边界待讨论）
- [ ] p.7.4.4 模式糖联动：enum payload 结构化解构 / 穷尽检查 / 守卫（联动 p.7.3.4）
- [ ] p.7.4.5 字符串插值：`"Hello, {name}"` 模板（现仅宏/准引用插值，缺普通插值）
- [ ] p.7.4.6 运算符重载：struct 自定义 `+ - * / ==` 等（向量/矩阵/复数/日期运算钥匙）
- [ ] p.7.4.7 let/const 增强：统一绑定语义深化
- [ ] p.7.4.8 集合速写：表/映射推导式 `[x * 2 for x in arr if cond]`
- [ ] p.7.4.9 泛型糖：泛型默认类型参数 / 泛型约束简化
- [ ] p.7.4.10 属性 getter/setter：struct 计算属性（UI/领域建模）
- [ ] p.7.4.11 数据流箭头 `->` / `<-` 增强与推广（tie 风格管道，P1 已实现基础上扩展：链式调用简化 / 与高阶函数衔接）
- [ ] p.7.4.12 尾随闭包：`arr.map { ... }` 免括号（高阶函数调用更顺）
- [ ] p.7.4.13 展开/解包调用：`f(args...)`（表展开为实参，与变参打包互逆）
- [ ] p.7.4.14 guard 早退：`guard cond else { return }` 前置条件，去嵌套化（如 Swift）

### 内置库补全（p.7.5）

- [ ] p.7.5.x 更多内置库：清单与优先级在库补全设计中确定（延续 2026.1 一库一子项纪律）；候选含多媒体编解码（WebP/AVIF/音频/视频，联动 p.7.11.3）

### trm 运行时 VM（p.7.6）

> 定位（2026-09-11 定）：**JVM 式可选 VM**——`import` trm 即选择路线 B（tiec 产 tieir
> 字节码 → trm 引擎执行），不 import 走纯编译路线 A（现状零依赖）。**可用可不用、
> 不捆绑编译器**（编译器默认原生目标，trm 目标作可插拔后端接入）。**不提供语言层
> 多线程**（并发归 trm-lite）；**不提供语言对象/表内存 GC**（表内存归 trm-lite
> 引用计数）；**保留引擎级 GC**（管 tieir 运行时的 Object/Value 生命期，属 trm 引擎自己）。
>
> EN: trm (2026-09-11 decision): optional JVM-style VM — Route B chosen by `import`,
> Route A pure compilation stays the zero-dependency default; optional, not bundled
> with the compiler; no language-level multithreading (trm-lite), no language
> object/table-memory GC (trm-lite refcounts), but engine-level GC kept (tieir runtime
> Object/Value lifetimes).

- [ ] p.7.6.1 trm 重定位实施：tieir 字节码 + interp 前端 + 可替换后端（LLVM ORC JIT | wasm/AOT）+ 类加载器 + 反射 + 引擎级 GC（路线 B，可用可不用）
- [ ] p.7.6.2 编译器侧 trm 目标接线：trm 字节码后端作为可插拔后端接入 tiec（默认不启用，不捆绑）
- [ ] p.7.6.3 trm 定稿修订：对齐新分工（无语言层多线程/无表内存 GC；引擎级 GC 保留；协程移交 trm-lite）——修订 docs/designs/trm-final-design.md

### trm-lite 协程（p.7.7）

> 定位（2026-09-11 定）：**部分协程加入 trm-lite**——生成器式；**trm 不保留协程**。
> trm-lite = 并行/并发运行时（调度 + yield + 生成器）；trm = VM 引擎（解析执行 + 引擎级 GC）。
>
> EN: Partial coroutines join trm-lite (generator-style); trm keeps none. trm-lite is
> the concurrency runtime (scheduler + yield + generators); trm is the VM engine.

- [ ] p.7.7.1 生成器式协程：`yield 值` 产出 + 惰性迭代/流式处理（惰性序列、管道、无限流）
- [ ] p.7.7.2 与既有调度整合：生成器任务可迁移/可窃取，复用 P-段双端队列（p.6.5/p.6.7 底座）

### tiu UI 框架（p.7.8）

> 定位（2026-09-11 定）：**独立自研 UI 框架——高性能、跨平台、不依赖 trm**；开发者可
> 单独用 tiu、单独用 trm、也可两者同用。与 release.md §3.3 中「tieui 挂 trm.ui」的旧
> 表述冲突，以本 ROAD 为准（修订 release.md）。
>
> EN: tiu (2026-09-11 decision): independent in-house UI framework — high-performance,
> cross-platform, NOT depending on trm; usable alone or together with trm. Supersedes
> the old "tieui on trm.ui" phrasing in release.md §3.3.

- [ ] p.7.8.1 tiu 运行时底座：自身窗口/绘制/事件/资源管理（独立于 trm）
- [ ] p.7.8.2 组件树与组合式布局框架（td? trm 旧 tieui 组件树/布局路径并入 tiu）
- [ ] p.7.8.3 release.md 修订：tieui/trm.ui 关系对齐 tiu 独立定位

### 平台与后端（p.7.9）

- [ ] p.7.9.1 macOS 平台移植（Linux 已在 r.1.6 闭环，补齐三大桌面平台）
- [ ] p.7.9.2 WASM 目标后端：tie 代码编译到 wasm，浏览器/嵌入式可跑（tiec 加目标三元组）
- [ ] p.7.9.3 GPU / X11 / SkParagraph 图形收尾（p.6.8 后置项）
- [ ] p.7.9.4 PQC 后量子密码（docs/plans/pqc-roadmap.md 已有规划）
- [ ] p.7.9.5 hw-accel 硬件加速（docs/plans/hw-accel.md 已有规划：哈希/加密/编解码硬件指令利用）

### 工具链（p.7.10）

- [ ] p.7.10.1 tie 命令行：基于 tink 管道编排器（形态 A：tink pipe），tie 命令行未来基于 tink
- [ ] p.7.10.2 包管理器正式落地（s3.2-package 转正）：依赖解析 / 版本约束 / 上传拉取；对接独立发行与 Keel 审计链
- [ ] p.7.10.3 DAP 调试器：断点 / 单步 / 变量 / 调用栈 + VS Code 客户端（LSP 之外的调试图）
- [ ] p.7.10.4 剖析器 profiler：CPU / 内存剖析 + 火焰图
- [ ] p.7.10.5 脚手架 tie new：项目模板 + 初始化（配合包管理器与独立发行）
- [ ] p.7.10.6 崩溃诊断：backtrace + 符号化 + 崩溃日志（配合诊断标号体系）

### 生态应用（p.7.11）

- [ ] p.7.11.1 tieDB 数据库完整实现：从接口层到存储引擎 / 查询 / 列式持久化 + 向量检索 vecsearch（zd 底座，Shipyard 四件套之一）
- [ ] p.7.11.2 去中心化网络：DHT + 打洞直连 + 志愿 relay（呼应网络去中心化总原则，tink v2 语义层）
- [ ] p.7.11.3 多媒体编解码：WebP / AVIF / 音频（wav/flac/ogg）/ 视频（p.6.8 PNG/QR/SVG 后扩展）
- [ ] p.7.11.4 嵌入式脚本：把 tie 嵌入宿主程序/游戏（对接 Subterra 类项目；tie 命令行再扩展）
- [ ] p.7.11.5 在线 Playground：网页写 tie 即时跑（WASM 后端落地后延伸，双语推广）
- [ ] p.7.11.6 包注册中心 registry：包管理器推拉库的存储端（与独立发行 / 主仓聚合发行配套）

### 仓库与发行（p.7.12）

> 定位（2026-09-11 定）：**每个组件仓库独立发行**（compiler/tink/tsp/trm/tiu/tiedb 等各自
> 版本与发行）；**主仓库聚合发行整套工具链**（把各组件按版本编排成互恰的版本集，打包
> 挂主仓发行——主仓无代码，是文档 + 整套工具链发行门户）。依据 release.md §3.4/§4.3。
>
> EN: (2026-09-11 decision) each component repo releases independently; the main repo
> aggregates and releases the whole toolchain (a consistent versioned set), keeping
> docs + full-toolchain distribution — no code in the main repo.

- [ ] p.7.12.1 仓库分离：多仓拆分（tie-main 聚合/发行仓——保留 dist 发行产物 + 当前版本文档；compiler/tink/tsp/trm-lite/tiu/tiedb/tiwi 等独立仓）
- [ ] p.7.12.2 组件独立发行：每仓独立版本号 + 独立 Release（GitHub / GitCode Release 附件分发，zip 出仓不进 git）
- [ ] p.7.12.3 主仓聚合发行：整套工具链聚合发行包（版本集编排 + 互恰校验）
- [ ] p.7.12.4 发行目录结构 2026.2 改造：发行下设 `src/` 收拢全部源码 + 另出 `tie-{版本}-src.zip`（release.md §3.2/§4.3）
- [ ] p.7.12.5 tiwi 安装器（**最后做**，Shipyard 四件套之一）：FLTK GUI + 自解压 setup，六边形架构

### 2026.2 关联定稿（修订项）

> 以下既有定稿文档在 2026.2 需按本 ROAD 对齐修订，不另立模块：
> - docs/designs/trm-final-design.md（对齐 p.7.6：无语言层多线程/无表内存 GC、引擎级 GC 保留、协程移交 trm-lite）
> - docs/release.md（对齐 p.7.8/p.7.12：tiu 独立定位、多仓拆分与聚合发行、发行物出仓）
> - docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（落地编号对齐本 ROAD p.7.1.x）
>
> EN: Existing finalized docs to be aligned with this ROAD during 2026.2 (revised
> in-place, no separate module): trm-final-design.md, release.md, plugin-kernel-design.md.