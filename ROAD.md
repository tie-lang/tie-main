# ROAD — tie 开发计划（2026.2）

*EN: ROAD — tie Development Plan (2026.2)*

> **定位**：2026.2 采用「预发布 → 正式版」两段式开发，延续 2026.1 的双轨模式。
> 与 2026.1 不同，2026.2 发布**多个预发布档**（preview 线段）：**p.7 → p.8 → p.9 → …
> → r.2**，每档完成一部分新功能并发布一个预览版（preview.N）；**架构性变化必做于
> 第一档（p.7）**，后续档在其上叠加。档位只代表先后顺序，全部在 2026.2 内完成。
>
> - **预发布段（p.7/p.8/p.9/…）**：全部新功能按档完成，开发号 **P.x.y.z**
>   （即 CHANGELOG 中的 p.x.y.z；x 即档号，如 p.7.x 属 p.7 档）。
> - **正式版段（r.2）**：最后一个预发布档发布后启动，**基于预发布段**开发——
>   **不引入任何新功能**，只做优化与稳定性；开发号 **R.x.y.z**。两轨独立编号、
>   不互相延续。
> - **当前状态（2026-09-11）**：2026.1（Harbor）已正式发布；p.7 分支已创建
>   （基于 main），2026.2 开发在 p.7 分支上进行。
> - **内部代号**：2026.2 = **Shipyard 造船厂**；编译器彻底重构进入 **Keel 龙骨架构**
>   时代（docs/release.md、docs/designs/keel-architecture.md）。
> - **历史路线图**：2026.1 ROAD 已归档至 [tie-lang/old_docs](https://github.com/tie-lang/old_docs)
>   （2026.1/ROAD.md）。

EN: 2026.2 follows the two-stage "preview → stable" model, continuing the dual-track
scheme of 2026.1, but ships **multiple preview tiers**: **p.7 → p.8 → p.9 → … → r.2**,
each tier completing some new features and releasing a preview (preview.N).
**Architectural change always lands first (p.7)**; later tiers stack on it. Tiers
indicate order only — everything is delivered within 2026.2. The preview stage uses
development numbers P.x.y.z (p.x.y.z in the CHANGELOG; x = tier, e.g. p.7.x belongs to
tier p.7). The stable stage (r.2) starts after the last preview tier, introduces NO new
features — only optimization/stability — numbered R.x.y.z; the two tracks number
independently. Codename: **Shipyard (2026.2)**; compiler restructure is the **Keel
Architecture** era. The 2026.1 ROAD was archived to tie-lang/old_docs (2026.1/ROAD.md).
All 2026.2 development happens on branch p.7.

### p.7 档（架构先行）

> 架构性变化第一档：编译器重构、仓库模型、运行时定调——后续档全依赖此三件套落地。
>
> EN: Tier p.7 — architecture first: the following tiers depend on these landing.

**编译器彻底重构 + 插件化（Keel 龙骨架构）**

- [ ] Keel 核心微内核化：核心只余机制层（注册表/审计器/加载器/执行骨架，零行为），一切行为皆为注册项；管线=注册项+锚点扩展
- [ ] id+version 注册方案 + tieir 消费入口（import tieir 包，消费方免前端）+ data→zd 发布转换（publish 压缩 + 指纹）
- [ ] 安全审计链：TSHA1 指纹（文件 tsha1f + 包树根 tsha1x）+ 凭证/指纹审计链（去中心化信任锚）；CLI 子命令注册化
- [ ] 安全算法底座：哈希/MAC/对称/KDF/非对称/后量子分类入 std/ext/rdu + TSHA（tsha1 代）四档家族（f/b/x/r）
  - 依据：docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（定稿）+ docs/designs/keel-architecture.md；落地编号一律 p.7.x.y，设计稿原步骤编号作废

**仓库分离 + 发行模型**

- [ ] 多仓拆分：tie-main 变聚合/发行仓（dist 发行产物 + 当前版本文档），compiler/tink/tsp/trm/tiu/tiedb/tiwi 等组件独立仓
- [ ] 组件独立发行（各仓独立版本 + Release 附件分发）+ 主仓聚合发行整套工具链（版本集编排互恰）+ 发行物出仓（zip 不进 git）+ 发行目录 src/ 收拢源码
- [ ] 包注册中心 registry 起步（为独立发行/聚合发行提供存储端）

**trm 重定位（JVM 式可选 VM）**

- [ ] trm 定稿修订 + 实现：可用可不用、不捆绑编译器（import trm 走路线 B，编译器默认原生路线 A）
- [ ] tieir 字节码 + interp 前端 + 可替换后端 + 类加载器 + 反射 + 引擎级 GC（语言层多线程/表内存 GC 不归 trm，协程移交 trm-lite）

### p.8 档（语言）

> 在 p.7 架构上铺语言层：特性加糖两开花。
>
> EN: Tier p.8 — the language layer on top of the new architecture.

**语言特性**

- [ ] const fn 编译期求值 / 错误处理统一（Option/Result + `?` 深化，无异常保持）/ 泛型增强（约束/特化）/ 模式匹配增强（payload 结构化解构/穷尽/守卫）
- [ ] 可空类型（路线 2：增强 Option，不引入 `T?`，保「无 null」安全目标）：`?.` `?:` `a?[i]` unwrap 语法糖

**语法糖批量**

- [ ] 可空链 / for..in 解构迭代 / 级联调用 / 命名参数 / 链式比较
- [ ] 字符串插值（`"Hello, {name}"` 模板）/ 运算符重载（struct 自定义 + - * / ==）/ 集合速写（推导式）/ 泛型糖（默认类型参数）/ 属性 getter-setter
- [ ] 数据流箭头 `->`/`<-` 增强推广（tie 风格管道，P1 已实现基础上扩展）/ 尾随闭包 / 展开·解包调用 `f(args...)` / guard 早退
- [ ] 宏升级：语句级宏 → 完整元编程（卫生宏/声明式宏，边界待定）

### p.9 档（其余全部）

> 库、工具链、UI、生态、平台在语言层之上补齐，全部在 2026.2 内。
>
> EN: Tier p.9 — the rest: libraries, toolchain, UI, ecosystem, platforms. All within 2026.2.

**内置库补全 + 编译体验**

- [ ] 更多内置库（一库一子项，清单与优先级在库补全设计中定；候选含多媒体编解码 WebP/AVIF/音频/视频）
- [ ] 编译资源可调（内存/并发/优化档位可配置，利好老电脑）+ 编译速度提升（增量/并行/缓存）

**工具链**

- [ ] tie 命令行（基于 tink 管道编排器，形态 A tink pipe）+ 包管理器正式落地（s3.2 转正）
- [ ] DAP 调试器（断点/单步/变量/调用栈 + VS Code 客户端）/ 剖析器 profiler（CPU/内存 + 火焰图）/ 脚手架 tie new / 崩溃诊断（backtrace + 符号化）

**tiu UI 框架**

- [ ] tiu 独立自研框架落地：高性能、跨平台、不依赖 trm（可与 trm 同用）；窗口/绘制/事件基础 + 组件树/布局组合式框架

**trm-lite 协程**

- [ ] 生成器式协程（`yield 值` + 惰性迭代/流）+ 与既有调度整合（可迁移/可窃取，复用 P-段双端队列）

**生态应用**

- [ ] tieDB 完整实现（列式持久化 + 向量检索 vecsearch，zd 底座）/ 去中心化网络（DHT + 打洞 + 志愿 relay）/ 嵌入式脚本（宿主嵌入 tie）

**平台**

- [ ] macOS 平台移植 / WASM 目标后端 / GPU·X11·SkParagraph 图形收尾 / PQC 后量子 / hw-accel 硬件加速

**安装器（最后做）**

- [ ] tiwi 安装器（FLTK GUI + 自解压 setup，六边形架构）——2026.2 收尾点，最后落地

### 关联定稿（修订项）

> 以下既有定稿在 2026.2 按本 ROAD 对齐修订（就地改，不另立档）：
> - docs/designs/trm-final-design.md（对齐 trm 重定位：无语言层多线程/无表内存 GC、引擎级 GC 保留、协程移交 trm-lite）
> - docs/release.md（tiu 独立定位、多仓拆分与聚合发行、发行物出仓）
> - docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（落地编号对齐 p.7.x.y）

EN: Existing finalized docs to be aligned during 2026.2 (revised in place, no separate
tier): trm-final-design.md, release.md, plugin-kernel-design.md.