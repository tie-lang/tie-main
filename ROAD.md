# ROAD — tie 开发计划（2026.2）

*EN: ROAD — tie Development Plan (2026.2)*

> **定位**：2026.2 采用「预发布 → 正式版」两段式开发，延续 2026.1 的双轨模式。
> 与 2026.1 不同，2026.2 发布**多个预发布档**（preview 线段）：**p.7 → p.8 → p.9 → …
> → r.2**，每档完成一部分新功能并发布一个预览版（preview.N）；**架构性变化必做于
> 第一档（p.7）**，后续档在其上叠加。档位只代表先后顺序，全部在 2026.2 内完成。
>
> - **预发布段（p.7/p.8/p.9/…）**：全部新功能按档完成，开发号 **P.x.y.z**
>   （即 CHANGELOG 中的 p.x.y.z；x=档号，y=模块，z=子项）。
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
development numbers P.x.y.z (p.x.y.z in the CHANGELOG; x=tier, y=module, z=sub-item).
The stable stage (r.2) starts after the last preview tier, introduces NO new features —
only optimization/stability — numbered R.x.y.z; the two tracks number independently.
Codename: **Shipyard (2026.2)**; compiler restructure is the **Keel Architecture** era.
The 2026.1 ROAD was archived to tie-lang/old_docs (2026.1/ROAD.md). All 2026.2
development happens on branch p.7.

### p.7 档（架构先行）

> 架构性变化第一档：编译器重构、仓库模型、运行时定调——后续档全依赖此三件套落地。
>
> EN: Tier p.7 — architecture first: the following tiers depend on these landing.

**编译器彻底重构 + 插件化（p.7.1，Keel 龙骨架构）**

> 依据：docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（定稿）+ docs/designs/keel-architecture.md。
> 核心只余机制层（注册表/审计器/加载器/执行骨架，零行为），一切行为皆为注册项；
> 落地编号以本 ROAD 为准，设计稿原步骤编号作废。
>
> EN: Basis: the finalized Keel design (plugin-kernel-design.md + keel-architecture.md).

- [x] p.7.1.1 核心微内核化：pipeline 5 槽 → 注册表执行骨架 + 内建引导集（默认管线注册项）；passmanager 接入 pipeline（验收：tiec 自举 hash 不变 + 回归基线保持）——**已落地 2026-09-11**：keel_registry/boot/executor 三新文件 + driver 真实 5 pass 接线，tiecA==tiecB 不动点 + .ll 逐字节等价 + 回归 104 PASS
- [x] p.7.1.2 id+version 注册方案：注册项 schema 表驱动 + 同 id 异 version 仲裁（验收：注册冲突负例正确拦截）——**已落地 2026-09-11**：register_v/version 列/优先级仲裁/check_version，探针 5 断言全过
- [x] p.7.1.3 tieir 消费入口：import tieir 包（消费方免前端）（验收：包 .tieir → 编译运行通过）——**已落地 2026-09-11**：keel_tieir_in 消费协议（tieir.read 还原 IR → 自包含后端门产出 .ll），探针 11 断言；llvmgen 直连需 driver 勾挂点（后续）
- [x] p.7.1.4 data→zd 发布转换：publish 压缩 + 指纹计算（验收：zd 包加载运行与 data 等价）——**已落地 2026-09-11**：zdpub.publish/load + tsha1f 指纹 + .zd.fp 清单，篡改拒绝探针过
- [x] p.7.1.5 安全审计链：TSHA1 指纹（文件 tsha1f + 包树根 tsha1x）+ 凭证/指纹审计链，去中心化信任锚（验收：篡改/冒名包负例全拦截）——**已落地 2026-09-11**：keelaud 指纹树/验签 ed25519/TOFU 锚，篡改/冒名/换钥负例全拦截
- [x] p.7.1.6 CLI 子命令注册化 + 库树收敛（std/ext/rdu ↔ lib_v1 定位）（验收：全命令行按注册项分派）——**已落地 2026-09-11**：keel_cli 注册表 + boot 13 cli:xxx + driver tie<cmd> 层按表分派（tiec 参数层不动）；库树收敛文档；探针 + 实机 tie pack/verify 命中
- [x] p.7.1.7 安全算法底座：哈希/MAC/对称/KDF/非对称/后量子分类入 std/ext/rdu，TSHA1 优先（审计链前置依赖）——**已落地 2026-09-11**：清单核对 25 已有/7 缺失/6 建议迁移，文档化缺口
- [x] p.7.1.8 TSHA（tsha1 代）四档家族落地：f/b/x/r，位平面 trit + 24/48 基，KAT 向量 + 交叉验证——**已落地 2026-09-11**：四档核实齐全，补固化 24/32 KAT，109 断言全过

**仓库分离 + 发行模型（p.7.2）**

- [x] p.7.2.1 多仓拆分：tie-main 变聚合/发行仓（dist 发行产物 + 当前版本文档），compiler/tink/tsp/trm/tiu/tiedb/tiwi 等组件独立仓——**已落地 2026-09-11**：release.md §3.4 组件清单定稿 + docs/plans/2026-09-11-p721-repo-split.md 双语规划（保留/迁移清单，本轮只规划不移动）
- [x] p.7.2.2 组件独立发行：各仓独立版本 + Release 附件分发，发行物出仓（zip 不进 git）——**已落地 2026-09-11**：release.md §3.5 组件发行小节（版本策略/artifact 命名/发行清单模板/打包约定）
- [x] p.7.2.3 主仓聚合发行：整套工具链聚合发行包（版本集编排 + 互恰校验）——**已落地 2026-09-11**：scripts/tie-versions.data.tie（td 版本约束）+ scripts/agg-check.tie（聚合校验，--self-test 三断言全过）+ release.md §4.5 聚合布局
- [x] p.7.2.4 发行目录 2026.2 改造：发行下设 `src/` 收拢全部源码 + 另出 `tie-{版本}-src.zip`——**已落地 2026-09-11**：package.tie 5 步改造，实测打包 dist/tie-2026.2（bin/docs/src + 包根文档）+ 两个 zip，解包跑通 hello
- [x] p.7.2.5 包注册中心 registry 起步（为独立发行/聚合发行提供存储端）——**已落地 2026-09-11**：keel_registry_cli.tie（keelpkg publish/info/versions）+ 探针 10 断言 ALL PASS + `tie pkg` 按注册表分派；格式文档 release.md §4.6
- [x] p.7.2.6 更新 README：仓库分离后主仓定位（聚合/发行仓 + 组件独立仓导航）、发行模型、组件索引对齐新仓储结构——**已落地 2026-09-11**：README 双路径快速开始 + 发行模型 + 结构/组件索引；tiecA==tiecB 自举不动点 + 回归 104 PASS/0 FAIL/2 SKIP + .ll 逐字节等价
- [x] p.7.2.7 多仓拆分执行落地：compiler/lsp → `tie-lang/tsp`、pkg → `tie-lang/tpkg`、tieDB → `tie-lang/tdb`、skills/tie-dev → `tie-lang/tie-dev`、editor/vscode-tie → `tie-lang/vscode-tie`、compiler 其余 + prep/std/ext/rdu/repl/scripts/tests/examples/diagdocs/sys/archive → `tie-lang/tiec`——**已落地 2026-09-12**：六仓全部 `git subtree split` 保留完整历史建仓推送（README 组件索引已指向新仓），tie-main 删除对应目录并同步文档引用/聚合脚本收敛清单

**trm 重定位（p.7.3，JVM 式可选 VM）**

> 定位（2026-09-11 定）：可用可不用、不捆绑编译器（import trm 走路线 B，编译器默认原生
> 路线 A）；不提供语言层多线程（并发归 trm-lite）与语言对象/表内存 GC（归 trm-lite
> 引用计数）；保留**引擎级 GC**（管 tieir 运行时 Object/Value 生命期）；协程移交 trm-lite。
>
> EN: trm (2026-09-11): optional JVM-style VM — import trm = Route B, otherwise pure
> compilation Route A (zero dependency); no language-level multithreading / no table GC
> (trm-lite); engine-level GC kept; coroutines move to trm-lite.

- [x] p.7.3.1 trm 定稿修订：对齐新分工（无语言层多线程/无表内存 GC、引擎级 GC 保留、协程移交 trm-lite）——修订 docs/designs/trm-final-design.md——**已落地 2026-09-11**：定稿对齐 ROAD 分工 + release.md §3.3/§3.4/§3.5 发行衔接（独立仓 tie-lang/trm + artifact tie-trm-<版本>-<平台>-<arch>.zip）+ 里程碑按 p.7.3.x 落地 + 内部阶段编号清理，双语文档
- [x] p.7.3.2 tieir 字节码 + interp 前端 + 可替换后端（LLVM ORC JIT | wasm/AOT）+ 类加载器 + 反射 + 引擎级 GC（路线 B 实现）——**已落地 2026-09-11**：分期 p.7.3.2-a..f 全部完成（a tieir 加载/校验 + InterpBackend 纯函数执行；b 库层 min 域 + C1 环平台桥（fs/env）；c 引擎级 GC（精确根扫描 + mark-sweep + 周期回收负例）；d Backend 三接口 + 热点提升跟踪 + JIT 未接入确定性回退；e 反射/内省 + 动态 invoke + 诊断；f 四端平台表 + 域/契约矩阵 + wasm/aot 登记），6 期探针 ALL PASS
- [x] p.7.3.3 编译器侧 trm 目标接线：trm 字节码后端作可插拔后端接入 tiec（默认不启用，不捆绑）——**已落地 2026-09-11**：driver 新增 `--target trm` / `--backend trm` 走独立 pipeline_trm（front→irgen→trmemit 产出 .tieir 字节码）；默认 pipeline_real 全程不动，自举不动点 tiecA==tiecB + 回归 104 PASS/0 FAIL/2 SKIP + .ll 逐字节等价；探针验证 --target=trm 产物可被 trm 引擎加载校验 + 函数按名可查

### p.8 档（语言）

> 在 p.7 架构上铺语言层：特性加糖两开花。
>
> EN: Tier p.8 — the language layer on top of the new architecture.

**语言特性（p.8.1）**

- [x] p.8.1.1 const fn 编译期求值（编译期常量折叠更强能力，可行静态元编程）——**已落地 2026-09-12**：tiec 仓 31e8bcd
- [x] p.8.1.2 错误处理统一：Option/Result 泛型增强 + `?` 解包深化，无异常保持——**已落地 2026-09-12**：tiec 仓 37fb523（泛型 enum 模板参数 Result/Option + ? 链）
- [x] p.8.1.3 泛型增强：约束 / 特化 / 变长泛型——**已落地 2026-09-12**：tiec 仓 14ec83c（infer_type_args 变长 ...T）
- [x] p.8.1.4 模式匹配增强：enum payload 结构化解构 / 穷尽检查 / 守卫（联动 p.8.2）——**已落地 2026-09-12**：tiec 仓 5d90ff6（多字段解构/穷尽检查 check_enum_exhaustive/when 守卫）
- [x] p.8.1.5 可空类型（路线 2：增强 Option，不引入 `T?`，保「无 null」安全目标）：`?.` 安全调用 / `?:` 默认值 / `a?[i]` 安全索引 / unwrap 语法糖——**已落地 2026-09-12**：tiec 仓 ba9221d（与 p.8.2.1 同提交）
- [x] p.8.1.6 表删除/缩表原语：动态表 `pop` / 截断缩表（现仅 `table_push` + 下标写，无删除/缩表，删除靠重建表模拟）——**已落地 2026-09-12**：tiec 仓 8df05a7（ECS 支撑前置达成）
- [x] p.8.1.7 enum payload 白名单扩展：放开 `table/f64` payload（现白名单排除；联动 p.8.1.4 结构化解构）——**已落地 2026-09-12**：tiec 仓 90dbdca + bdf5912（ECS 支撑前置达成）

**语法糖批量（p.8.2）**

> 现状盘点：已有元组解构 `var (a,b)`、switch 解构/区间/守卫、`for i in 0..10`、标签、
> 默认参数、语句级宏（p.6.2.3）、`?` 解包、闭包、数据流箭头 `->`/`<-`（P1 已实现）。
>
> EN: Current sugar inventory and planned additions below.

- [x] p.8.2.1 可空链语法：`?.` 安全调用 / `?:` 默认值 / `a?[i]`（联动 p.8.1.5）——**已落地 2026-09-12**：tiec 仓 ba9221d（与 p.8.1.5 同提交）
- [x] p.8.2.2 常用糖集：for..in 解构迭代 / 级联调用 / 命名参数 / 链式比较——**已落地 2026-09-12**：tiec 仓 c5a7ad8（for..in 解构/命名参数重排/链式比较 desugar）
- [x] p.8.2.3 字符串插值：`"Hello, {name}"` 模板（现仅宏/准引用插值）——**已落地 2026-09-12**：tiec 仓 411ae6b + 397515e + 5571d62（lexer 拆段 + parser 拼接链 + to_string irgen；含 2 个 RCA 修复：插值 lbrace 独立 tag、前瞻收紧 ASCII 表达式起始）
- [x] p.8.2.4 运算符重载：struct 自定义 `+ - * / ==` 等（向量/矩阵/复数/日期运算钥匙）——**已落地 2026-09-12**：tiec 仓 e78b779（op_add/op_sub/op_mul/op_div/op_mod/op_eq/op_ne/op_lt/op_le/op_gt/op_ge/op_neg 方法约定，左置右回调度的确定性裁决表；两侧内置不重载、未声明 op_ 的 struct 走原路径零变化）
- [x] p.8.2.5 集合速写：表/映射推导式 `[x * 2 for x in arr if cond]`——**已落地 2026-09-12**：tiec 仓 2ebdbe3（首个 cell 后跟 `for` 即推导式；单 for + 可选 if，支持 for..in 解构迭代；desugar 复用建表/append；tie 无映射表字面量故只做数组推导）
- [x] p.8.2.6 泛型糖：泛型默认类型参数 / 泛型约束简化——**已落地 2026-09-12**：tiec 仓 9c27f07（`<T, U=默认>` 默认类型参数，优先级 显式>推断>默认；`<T, U: 约束>` 约束回填糖；未使用零变化）
- [x] p.8.2.7 属性 getter/setter：struct 计算属性（UI/领域建模）——**已落地 2026-09-12**：tiec 仓 6f28a1c（方法约定 `<Struct>::attr` getter + `attr_set` setter；字段优先、getter 探测兜底；只读属性写报诊断；普通字段零变化）
- [x] p.8.2.8 数据流箭头 `->`/`<-` 增强与推广（tie 风格管道，P1 已实现基础上扩展）——**已落地 2026-09-12**：tiec 仓 0519b78（链式/方法/完整调用/反向/与尾随闭包组合语义鉴定并锁定，D1–D6 确定性规则 + dataflow_arrow2 探针；主体能力 P1 已承载，本轮推广锁定）
- [x] p.8.2.9 尾随闭包：`arr.map { ... }` 免括号——**已落地 2026-09-12**：tiec 仓 d45cce0（调用/方法/链式末位实参写裸 `{ }` → 无参 void 闭包；控制流条件解析加守卫计数防块歧义）
- [x] p.8.2.10 展开/解包调用：`f(args...)`——**已落地 2026-09-12**：tiec 仓 6b92240（实参 `expr...` 按运行期长度展开进变参区，与 p.8.1.3 变长形参衔接；非泛型普通变参函数）
- [x] p.8.2.11 guard 早退：`guard cond else { return }` 前置条件——**已落地 2026-09-12**：tiec 仓 e869dc4（= if not(cond) desugar；scheck 强制 else 块尾跳转；guard 非保留字，语句位语境识别）
- [x] p.8.2.12 宏升级：语句级宏 → 完整元编程（卫生宏/声明式宏，边界待定）——**已落地 2026-09-12**：tiec 仓 aa806b1（声明式模板/AST 片段宏 `macro name(a,b){体}` + `__` 前缀卫生唯一化跨展开单调 + 与既有语句级宏双轨共存；边界：完整模式匹配/递归/卫生闭包语义注明后续）

### p.9 档（其余全部）

> 库、工具链、UI、生态、平台在语言层之上补齐，全部在 2026.2 内。
>
> EN: Tier p.9 — the rest: libraries, toolchain, UI, ecosystem, platforms. All within 2026.2.

**命名迁移（p.9.0，最先做）**

> 尽早（趁组件未发行改名零成本）+ 彻底（不留旧名兼容期）。依据 tie-naming-convention.md v0.2。
>
> EN: p.9.0 naming migration — early (zero cost pre-release) + thorough (no legacy-name grace period).

- [ ] p.9.0.1 tie-diag → **tdiag**（诊断配套，文档为主，影响面最小）
- [ ] p.9.0.2 tie-pkg → **tpkg**（包管理器，未建仓）
- [ ] p.9.0.3 tiwi → **twi**（安装器，未完成）
- [ ] p.9.0.4 tiedb → **tdb**（数据库，引用面最大，最后做）
  - 执行计划（2026-09-12）：`docs/plans/2026-09-12-naming-migration.md`（每仓迁移内容/顺序/彻底性验收/执行记录）
  - 状态：**待执行**；每仓一提交、grep 旧名=0 验收

**内置库补全 + 编译体验（p.9.1）**

- [ ] p.9.1.1 更多内置库（一库一子项，清单与优先级在库补全设计中定；候选含多媒体编解码 WebP/AVIF/音频/视频）
- [ ] p.9.1.2 编译资源可调：内存上限 / 并发度 / 优化档位可配置（利好老电脑）
- [ ] p.9.1.3 编译速度提升：增量编译 / 并行编译 / 编译缓存

**工具链（p.9.2）**

- [ ] p.9.2.1 崩溃诊断：backtrace + 符号化 + 崩溃日志（配合诊断标号体系）
- [ ] p.9.2.2 包管理器正式落地（s3.2-package 转正）：依赖解析 / 版本约束 / 上传拉取
- [ ] p.9.2.3 DAP 调试器：断点 / 单步 / 变量 / 调用栈 + VS Code 客户端
- [ ] p.9.2.4 剖析器 profiler：CPU / 内存剖析 + 火焰图
- [ ] p.9.2.5 脚手架 tie new：项目模板 + 初始化

**命令行壳 tshell（p.9.3，交互基础设施，先行开发）**

> 定位（2026-09-13 定，设计文档 v0.2）：tie 命令行壳三身份——独立壳（REPL + 脚本运行时 + 系统命令混合 + 值管道，目标全面优于 PowerShell）· **tedit 根基**（终端模组命令引擎，同进程 zd 协议总线 + 子进程 tink 帧双形态）· **trm 基础设施**（tieir 观测台 / 调试前端 / 动态加载交互，执行后端 interp|trm 可配置）；**模块化可嵌入**——能力以九模块交付，开发者把需要的模块嵌入自己的应用（静态 / 动态 / 进程外三形态）；组件仓 `tie-lang/tshell`
>
> EN: p.9.3 — tshell command-line shell & interactive infrastructure: three roles (standalone PS-killer shell; tedit terminal-module engine with dual protocol modes; trm interactive infra), modular & embeddable (nine modules, three embedding forms), repo tie-lang/tshell.

- [ ] p.9.3.1 壳核心：REPL 求值循环（tie-interp 执行后端）+ 命令解析（tie 表达式 → 内建 → 外部回退 + 拼写纠错）+ 值管道与渲染（L0–L1，`repl`/`command`/`pipeline`/`render` 模块）
- [ ] p.9.3.2 会话层：tie 自研行编辑 / 可插拔补全源 / 历史 / 配置（td 资产热加载）（L2，`lineedit`/`complete`/`session` 模块）
- [ ] p.9.3.3 脚本运行时：`-e` / `-f` / shebang / 脚本内内建命令函数式调用（`run` 模块）
- [ ] p.9.3.4 双形态协议层：同进程 zd 内存总线（tedit 嵌入）+ `--stdio` tink 帧（子进程 / 远程 / WASM 后端）（L3，`srv` 模块）
- [ ] p.9.3.5 trm 基础设施：tieir 观测台 / 调试前端 / 动态加载交互 / `set eval-backend interp|trm` 执行后端可配置（`observe` 模块，对齐 p.7.3.2）
- [ ] p.9.3.6 模块化交付：模块清单冻结 / 装配器 / 三种嵌入形态 / 接 tedit 终端模组嵌入子集（§12 设计）
  - 设计文档（2026-09-12）：`docs/designs/tshell-architecture.md` v0.2（三身份 + 五层架构 + 双形态集成协议 + 模块系统与嵌入）
  - 状态：**先行开发（优先启动）**——tshell 作为 tedit（p.9.9.7）根系，**先于 tedit 等组件完成开发**；依赖仅 tiec repl 路径（现货）与 tink 帧协议；trm 侧能力（observe）随 p.7.3 异步接入；**tie 命令行入口由 tshell 承载**（原 p.9.2 tie 命令行条目并入本档）

**tiu UI 框架（p.9.4）**

> 定位（2026-09-11 定）：独立自研、高性能、跨平台、**不依赖 trm**；可与 trm 同用。
>
> EN: tiu (2026-09-11): independent in-house UI framework — high-performance,
> cross-platform, NOT depending on trm; usable alone or with trm.

- [ ] p.9.4.1 tiu 运行时底座：窗口/绘制/事件/资源管理（独立于 trm）
  - 设计文档已落盘（2026-09-12）：`docs/designs/tiu-render-engine.md`（渲染引擎七层）· `docs/designs/tiu-drawing-api.md`（绘制 API 库）· `docs/designs/tiu-event-system.md`（事件轴）；上层 `docs/designs/tiu-ui-widgets.md`（UI 库，p.9.4.2 输入）
  - API 库实施计划已落盘（2026-09-12）：`docs/plans/2026-09-12-tiu-api-impl.md`（任务分解 + 契约冻结 + 无遗留闭环）
  - 渲染引擎实施计划已落盘（2026-09-12）：`docs/plans/2026-09-12-tiu-render-impl.md`（任务分解 + 契约冻结 + 后端落地顺序 + 无遗留闭环）
- [ ] p.9.4.2 组件树与组合式布局框架
- [ ] p.9.4.3 release.md 修订：tieui/trm.ui 关系对齐 tiu 独立定位

**trm-lite 协程（p.9.5）**

> 定位（2026-09-11 定）：部分协程加入 trm-lite（生成器式）；trm 不保留协程。
>
> EN: (2026-09-11) partial coroutines join trm-lite (generator-style); trm keeps none.

- [ ] p.9.5.1 生成器式协程：`yield 值` 产出 + 惰性迭代/流（惰性序列、管道、无限流）
- [ ] p.9.5.2 与既有调度整合：生成器任务可迁移/可窃取，复用 P-段双端队列（p.6.5/p.6.7 底座）

**生态应用（p.9.6）**

- [ ] p.9.6.1 tieDB 完整实现：列式持久化 + 向量检索 vecsearch（zd 底座，Shipyard 四件套之一）
- [ ] p.9.6.2 去中心化网络：DHT + 打洞直连 + 志愿 relay（网络去中心化总原则，tink v2 语义层）
- [ ] p.9.6.3 嵌入式脚本：宿主程序/游戏嵌入 tie（对接 Subterra 类项目）
- [ ] p.9.6.4 在线 Playground：网页写 tie 即时跑（WASM 后端落地后延伸，双语推广）

**平台（p.9.7）**

- [ ] p.9.7.1 macOS 平台移植（Linux 已在 r.1.6 闭环，补齐三大桌面平台）
- [ ] p.9.7.2 WASM 目标后端：tie 代码编译到 wasm，浏览器/嵌入式可跑
- [ ] p.9.7.3 GPU / X11 / SkParagraph 图形收尾（p.6.8 后置项）
- [ ] p.9.7.4 PQC 后量子密码（docs/plans/pqc-roadmap.md 已有规划）
- [ ] p.9.7.5 hw-accel 硬件加速（docs/plans/hw-accel.md 已有规划）

**安装器（p.9.8，最后做）**

- [ ] p.9.8.1 tiwi 安装器：**完全 tie 自研重构**——GUI 用 tiu（自定义）、逻辑全 tie 语言、自解压 setup（六边形架构；2026.2 收尾点，最后落地）

**tge 游戏引擎 / t3d / trg（p.9.9，规划中，潜力档位）**

> 定位（2026-09-12 定）：通用全栈游戏引擎，100% tie；立场中立（物理/网络/权威/中心化均为开发者可配置选项）。组装 t3d（3D 渲染框架）+ tiu（2D/UI）+ tink（多人）+ trg（共享渲染底栈）。
>
> EN: tge — general-purpose full-stack tie game engine, position-neutral; assembles
> t3d (3D), tiu (2D/UI), tink (networking), trg (shared rendering substrate).

- [ ] p.9.9.1 tge 全栈游戏引擎（ECS 骨架 / 帧模型 / 网络多路径；组件仓 `tie-lang/tge`）
- [ ] p.9.9.2 t3d 3D 渲染框架（Forward+ / Deferred 双路径 · 三档 GI · GPU-driven · PBR 单源；组件仓 `tie-lang/t3d`）
- [ ] p.9.9.3 trg 共享渲染底栈（帧图 / shader 预编译 / 资源管理；组件仓 `tie-lang/trg`）
  - 设计文档（2026-09-12，规划期落于 `F:\Projects\tie-repo\tge\docs\designs\`）：`tge-architecture.md` · `t3d-architecture.md` · `trg-architecture.md` · `taud-architecture.md` · `tanim-architecture.md` · `tphy-architecture.md`（建仓后迁入各组件仓）
  - 状态：**规划中，未建仓**；依赖 2026.2 基本闭环后择期启动
- [ ] p.9.9.4 taud 音频组件（独立音频系统，可单用/可被 tge 组装；组件仓 `tie-lang/taud`）
- [ ] p.9.9.5 tanim 动画组件（独立动画系统：骨骼/顶点/混合树/状态机/动画资产；可单用/可被 tge 组装；组件仓 `tie-lang/tanim`）
- [ ] p.9.9.6 tphy 物理组件（独立物理系统：刚体/碰撞/约束求解/确定性可配；可单用/可被 tge 组装；组件仓 `tie-lang/tphy`）
- [ ] p.9.9.7 tedit 生态编辑器（tie 生态共用模块化编辑器：薄壳 + 可拆卸模组，每组件贡献生态模组；性能/低内存/老电脑/跨平台/手机可用；终端模组基于 tshell（p.9.3）；组件仓 `tie-lang/tedit`）

**计算科学与多媒体域（p.9.10，规划中）**

> 定位（2026-09-12 定）：tie 生态扩展两大主轴 + 横跨组件——计算科学（tsci→tstat→tsim）+ 多媒体（timg→tvid→tvfx）+ 几何建模 tgeo + 统计可视化 tplot；**库生态靠 pkg/registry（CRAN/PyPI 模式），产出物靠 tplot 绘图 + tedit notebook 报告 + timg/tvid 导出（端到端"能画图、能出产物"）**；设计参考 R/Matlab/Julia。
>
> EN: p.9.10 — computational science & media domains (tsci→tstat→tsim, timg→tvid→tvfx, tgeo, tplot); library ecosystem via pkg/registry, outputs via tplot + tedit notebook + timg/tvid; design reference R/Matlab/Julia.

- [ ] p.9.10.1 tsci 科学计算（数值线性代数/FFT/ODE/优化；组件仓 `tie-lang/tsci`）
- [ ] p.9.10.2 tstat 统计预测（分布/回归/时间序列/ML 基础；社会/经济预测；依赖 tsci；组件仓 `tie-lang/tstat`）
- [ ] p.9.10.3 tsim 仿真模拟（DES/蒙特卡洛/系统动力学/agent-based；依赖 tsci+tstat；组件仓 `tie-lang/tsim`）
- [ ] p.9.10.4 tgeo 几何建模（B-rep/NURBS/网格/参数化；供 t3d/tphy/tanim；组件仓 `tie-lang/tgeo`）
- [ ] p.9.10.5 timg 图像处理（编解码/滤镜/缩放/颜色管理；依赖 trg；组件仓 `tie-lang/timg`）
- [ ] p.9.10.6 tvid 视频处理（编解码/转码/帧流；依赖 timg；组件仓 `tie-lang/tvid`）
- [ ] p.9.10.7 tvfx 特效（粒子/后处理/着色器特效；独立仓，依赖 t3d；组件仓 `tie-lang/tvfx`）
- [ ] p.9.10.8 tplot 统计可视化（图表/数据可视化；依赖 tiu+timg，产出物链路关键；组件仓 `tie-lang/tplot`）
- [ ] p.9.10.9 tac API 生成器（tie api compiler：读 tieapi td 定义 → API IR → 各语言 codegen backend → tink-xxx 绑定库；首期 Python/Rust/C；组件仓 `tie-lang/tac`）
  - 布局文档（2026-09-12）：`docs/plans/2026-09-12-p99-sci-media-domains.md`（领域清单/依赖链/库生态与产出物/R·Matlab·Julia 设计参考）
  - 状态：**规划中，未建仓**；依赖 2026.2 基本闭环后择期启动
  - 生态格式与 API 家族规范（2026-09-12）：`docs/designs/tie-format-api-family.md`（tieapi 统一 API 规范层 + td/zd 同源双态 + 专项格式谱系 + 家族纪律 + 对外互操作 + 绑定生成策略 + tac 实现细节）

**语言功能与语法糖第二轮（p.9.11，语言层补全）**

> p.8 档（语言第一轮 21 项）闭环后的第二轮语言层；全部能力纳入当前架构、仅区分落地
> 顺序（用户 2026-09-13 全选确认）。设计文档：`docs/designs/tie-lang-round2-design.md`。
> 联动：yield 语法↔trm-lite p.9.5.1；#cfg↔p.9.7 平台移植；inline↔p.9.1.2 编译资源可调。
>
> EN: Round-2 language layer after p.8 closed (confirmed by user 2026-09-13, full set);
> design in docs/designs/tie-lang-round2-design.md; ties to p.9.5.1/p.9.7/p.9.1.2.

- [ ] p.9.11.1 match/switch **表达式**：模式匹配表达式位取值 `let v = when x { 1 => "a" _ => "b" }`（复用穷尽检查）
- [ ] p.9.11.2 **if-let** 解构条件：`if let Some(x) = opt { }`（可带 else），Option/Result 解包惯用法
- [ ] p.9.11.3 **try 块** 错误聚合：`try { a? b? }` 块内 `?` 早退传播，无异常语义
- [ ] p.9.11.4 **defer** 资源释放：`defer { f.close() }` 作用域退出逆序执行（tie 无 RAII 的钥匙）
- [ ] p.9.11.5 **映射/记录字面量**：`{name: "x", age: 3}`（真实缺口，花括号消歧设计：首元素标识符/字符串+冒号即记录）
- [ ] p.9.11.6 **表不可变更新**：`t2 = t1 with {k: v}` 值语义新生表、未变部分零拷贝共享
- [ ] p.9.11.7 **切片/区间糖**：`t[1..3]`/`t[..n]`/`t[n..]`/`t[..]`（表+字符串）
- [ ] p.9.11.8 **剩余解构**：`var (a, ...rest) = t` rest 收集为表
- [ ] p.9.11.9 **checked 运算**：`a +? b` 溢出即诊断；普通 `+` 零变化；策略可配置
- [ ] p.9.11.10 **inline 标注**：`inline fn hot()` 内联提示（联动优化档位）
- [ ] p.9.11.11 **immut 只读形参**：`fn f(immut t)` 防误写/降拷贝
- [ ] p.9.11.12 **@注解/属性**：`@component class X` 声明式注解（联动 Keel 注册表/tieapi/tdiag）
- [ ] p.9.11.13 **#cfg 条件编译**：`#cfg(os=linux)`/`#else` 目标求值裁剪（平台移植钥匙）
- [ ] p.9.11.14 **import 别名/重导出**：`import x as y`（解析层糖）
- [ ] p.9.11.15 **yield 生成器语法**：`func gen() { yield v }`（语言侧 tiec，运行时 trm-lite p.9.5.1）
- [ ] p.9.11.16 **迭代器协议 + 惰性序列**：iterable 协议 + 惰性链（性能导向，与 p.9.5 同源）
- [ ] p.9.11.17 **函数类型一等公民**：`fn(i64)->bool` 类型写法（与闭包/尾随闭包配套）
- [ ] p.9.11.18 **多行表达式续行**：行尾 `\`/流水线延续（修补实测缺口）
- [ ] p.9.11.19 **数值字面量加强 + raw 字符串**：`1_000_000`/`0b`/`r"..."`
- [ ] p.9.11.20 **enum 关联方法**：enum 类型方法定义（与 struct 方法约定一致）
- [ ] p.9.11.21 **interface/trait 轻量化**（候选池排后）：`type Drawable { fn draw(); }` + 实现检查（tiu/t3d/tge 受益）

### 关联定稿（修订项）

> 以下既有定稿在 2026.2 按本 ROAD 对齐修订（就地改，不另立档）：
> - docs/designs/trm-final-design.md（对齐 p.7.3 trm 重定位）
> - docs/release.md（对齐 p.7.2 多仓拆分与聚合发行、p.9.4 tiu 独立定位、发行物出仓）
> - docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（落地编号对齐本 ROAD p.7.1.x）

EN: Existing finalized docs to be aligned during 2026.2 (revised in place, no separate
tier): trm-final-design.md, release.md, plugin-kernel-design.md.