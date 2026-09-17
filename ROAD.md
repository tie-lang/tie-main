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

- [x] p.7.2.1 多仓拆分：tie-main 变聚合/发行仓（dist 发行产物 + 当前版本文档），compiler/tink/tsp/trm/tiu/tdb/twi 等组件独立仓——**已落地 2026-09-11**：release.md §3.4 组件清单定稿 + docs/plans/2026-09-11-p721-repo-split.md 双语规划（保留/迁移清单，本轮只规划不移动）
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
- [ ] p.8.1.8 enum payload 白名单二批：放开 **struct / fn** payload（一批 f64/table<T>/map<V>/string 已落，p.8.1.7）+ `table<Enum>` 自引用递归探针 + i64/i128 解构确认——tiu Elem 判别和/修饰符 Common 与 ECS/事件类型同族受益（tiu-ui-widgets.md §15.1/§15.5/§15.6）

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

**actor 缺口补全（p.8.3，并发语言层）**

> 依据：docs/designs/concurrency-model.md §5.7（字段显式初值捕获）+ §9（async 结果回传）。
> 两项均为 2026-09-16 定稿的 2026.2 语言层收口：语法不变、补语义，纯编译零运行时。
>
> EN: p.8.3 — actor gap closure (concurrency language layer), per concurrency-model.md
> §5.7 (explicit field initial values) + §9 (async result return). Both finalized
> 2026-09-16 as 2026.2 language-layer closures: syntax unchanged, semantics added,
> pure compilation with zero runtime.

- [ ] p.8.3.1 actor 字段显式初值捕获：`var count: i64 = 0` 的 `= N` 写入 `run Typed()`
  record 初始化（启动工作线程前按字段序 store，常量折叠进 init 块；初值限字面量，
  规则集同函数默认值参数 language.md §6.1；整数字面量赋 f64/f32 走既有收窄路径；
  消息槽布局不变；不引入 `init()` 方法）（验收：全类型初值 / 零值混排 / f64 收窄
  探针 + 非字面量与类型不匹配负例 + 自举不动点 + 回归基线不劣化）
- [ ] p.8.3.2 async 结果回传：`pub async func m(...) -> R` 合法化 + `future` 值
  （{record_ptr, slot_id, seq} 三元组，复用同步 RPC 应答槽，可复制/可选 move）+
  `await f` 阻塞取值（结果 move 回调用方；panic 在 await 点原地 raise；未 await 允许
  丢弃不告警；无返回值 async 保持 fire-and-forget；安全路径消息参数仍限标量）
  （验收：延迟取值 / 多 future 乱序完成按 seq 回取 / panic 传播 / 丢弃 / 与同步 RPC
  混用探针 + 回归基线不劣化）

### p.9 档（其余全部）

> 库、工具链、UI、生态、平台在语言层之上补齐，全部在 2026.2 内。
> 
> EN: Tier p.9 — the rest: libraries, toolchain, UI, ecosystem, platforms. All within 2026.2.

**命名迁移（p.9.0，最先做）**

> 尽早（趁组件未发行改名零成本）+ 彻底（不留旧名兼容期）。依据 tie-naming-convention.md v0.2。
> 
> EN: p.9.0 naming migration — early (zero cost pre-release) + thorough (no legacy-name grace period).

- [x] p.9.0.1 tie-diag → **tdiag**（诊断配套，文档为主，影响面最小）
- [x] p.9.0.2 tie-pkg → **tpkg**（包管理器，未建仓）
- [x] p.9.0.3 tiwi → **twi**（安装器，未完成）
- [x] p.9.0.4 tiedb → **tdb**（数据库，引用面最大，最后做）
  - 执行计划（2026-09-12）：`docs/plans/2026-09-12-naming-migration.md`（每仓迁移内容/顺序/彻底性验收/执行记录）
  - 状态：**已落地 2026-09-13**；每仓一提交、grep 旧名=0（豁免历史 CHANGELOG + 映射描述）验收

**内置库补全 + 编译体验（p.9.1）**

- [x] p.9.1.1 更多内置库——**已落地 2026-09-13**：tiec 1765147+ 5 批次（清单扩至 21 项，20 项已实现纯 tie——zlib/gzip·WebP(VP8L)·datetime·GIF·JSON5·WAV·regex-pro·xlsx·color·rng-adv·QR 解码·BMP·bytes·process 管道/超时·fs·zip·mono 时钟·regex；.3 AVIF 登记待环境 libavif、.8 视频容器待专项）（一库一子项，清单与优先级在库补全设计中定；候选含多媒体编解码 WebP/AVIF/音频/视频）
- [x] p.9.1.2 编译资源可调——**已落地 2026-09-13**：tiec 5a4beee（`--mem-limit <MB>` 超限 O3 自动降 O2 + `--jobs` 并发预留 + 分配档位 CLI>配置>默认）：内存上限 / 并发度 / 优化档位可配置（利好老电脑）
- [x] p.9.1.3 编译速度提升——**已落地 2026-09-13**：tiec ddc173d（编译缓存：源哈希+参数+盐为键 → ~/.tiec-cache；`--no-cache`；脚本 verify-cache.ps1）：增量编译 / 并行编译 / 编译缓存

**工具链（p.9.2）**

- [x] p.9.2.1 崩溃诊断——**已落地 2026-09-13**：tiec ec41436（crashdiag：interp panic backtrace 符号化 + 崩溃日志，配合诊断标号）：backtrace + 符号化 + 崩溃日志（配合诊断标号体系）
- [x] p.9.2.2 包管理器正式落地——**已落地 2026-09-13**：tpkg 4c41e3e（依赖解析 MVS/tie.lock + 版本约束 x.y.z·^·>=·* + TSHA1-f 指纹上传拉取，文件注册表后端）（s3.2-package 转正）：依赖解析 / 版本约束 / 上传拉取
- [x] p.9.2.3 DAP 调试器——**已落地 2026-09-13**：tiec 7627a63（tiedap DAP 适配器服务驱动 interp：断点/单步/调用栈/变量 + VS Code 最小扩展）：断点 / 单步 / 变量 / 调用栈 + VS Code 客户端
- [x] p.9.2.4 剖析器 profiler——**已落地 2026-09-13**：tiec 6be21eb（profiler：运行期调用采样 + 折叠栈 + ASCII 火焰图）：CPU / 内存剖析 + 火焰图
- [x] p.9.2.5 脚手架 tie new——**已落地 2026-09-13**：tpkg 15f31e9（`tpkg new` 项目模板 + 初始化，hello 编译跑通）：项目模板 + 初始化

**命令行壳 tshell（p.9.3，交互基础设施，先行开发）**

> 定位（2026-09-13 定，设计文档 v0.2）：tie 命令行壳三身份——独立壳（REPL + 脚本运行时 + 系统命令混合 + 值管道，目标全面优于 PowerShell）· **tedit 根基**（终端模组命令引擎，同进程 zd 协议总线 + 子进程 tink 帧双形态）· **trm 基础设施**（tieir 观测台 / 调试前端 / 动态加载交互，执行后端 interp|trm 可配置）；**模块化可嵌入**——能力以九模块交付，开发者把需要的模块嵌入自己的应用（静态 / 动态 / 进程外三形态）；组件仓 `tie-lang/tshell`
> 
> EN: p.9.3 — tshell command-line shell & interactive infrastructure: three roles (standalone PS-killer shell; tedit terminal-module engine with dual protocol modes; trm interactive infra), modular & embeddable (nine modules, three embedding forms), repo tie-lang/tshell.

- [x] p.9.3.1 壳核心——**已落地 2026-09-13**：tshell 179def3（REPL 复用 tiec interp.eval + 命令解析/纠错 + 值管道）：REPL 求值循环（tie-interp 执行后端）+ 命令解析（tie 表达式 → 内建 → 外部回退 + 拼写纠错）+ 值管道与渲染（L0–L1，`repl`/`command`/`pipeline`/`render` 模块）
- [x] p.9.3.2 会话层——**已落地 2026-09-13**：tshell e3885b3（行编辑/补全源/历史/td 配置热加载）：tie 自研行编辑 / 可插拔补全源 / 历史 / 配置（td 资产热加载）（L2，`lineedit`/`complete`/`session` 模块）
- [x] p.9.3.3 脚本运行时——**已落地 2026-09-13**：tshell 48e33c3（`-e`/`-f`/shebang/内建函数式调用）：`-e` / `-f` / shebang / 脚本内内建命令函数式调用（`run` 模块）
- [x] p.9.3.4 双形态协议层——**已落地 2026-09-13**：tshell 679c322（zd 帧编解码 + `--stdio` tink 帧服务）：同进程 zd 内存总线（tedit 嵌入）+ `--stdio` tink 帧（子进程 / 远程 / WASM 后端）（L3，`srv` 模块）
- [x] p.9.3.5 trm 基础设施——**已落地 2026-09-13**：tshell 7d97de2（observe 模块骨架 + `set eval-backend interp|trm`；tieir 观测待 trm p.7.3 接入）：tieir 观测台 / 调试前端 / 动态加载交互 / `set eval-backend interp|trm` 执行后端可配置（`observe` 模块，对齐 p.7.3.2）
- [x] p.9.3.6 模块化交付——**已落地 2026-09-13**：tshell 8c693e1（九模块清单冻结 + 装配器 + 三嵌入形态 + tedit 子集）：模块清单冻结 / 装配器 / 三种嵌入形态 / 接 tedit 终端模组嵌入子集（§12 设计）
- [x] p.9.3.7 tsh 脚本运行时补全（0-Rust 自举后**运行时缺陷**，2026-09-13 实测登记；库级能力已剥离至内置库清单 p.9.1.1.15–21——bytes 增强/process 管道与超时/fs 增强/zip/单调时钟/regex 语义）：①interp 函数内多局部变量与 exec_* 内建共存缺陷（局部槽丢失）②递归 re-entrancy 残边（递归调用后两 var 场景；活动段计数已修未完全）③file_exists/mkdir_all 运行期新建路径陈旧伪值（需盘上实查）④var 偶发 command-not-found 扰行；验收=待补运行时缺陷清零 + 依赖库落地（p.9.1.1）后剩余 .ps1（package×2 / verify-tiedap）改写完成，grep .ps1=0
- [x] p.9.3.8 Rust 桥基线测试退役——**已落地 2026-09-13**：tiec 471bde4（0-Rust 后删除 6 个依赖 tie-*.exe/tie_interp.lib 的对比测试：regress-driver-lite/bench/test-errors/regenerate-golden/repl-parity/run-interp-tests，引用同步清扫；脚本迁移另见 tsh 角色 .tsh.tie 替换：tiec 10 门 + tshell/tpkg/tink/trm/tdiag 全仓共约 20 个 .ps1→.tsh.tie，保留 regress-s21/package×2/verify-tiedap）
  - 设计文档（2026-09-12）：`docs/designs/tshell-architecture.md` v0.2（三身份 + 五层架构 + 双形态集成协议 + 模块系统与嵌入）
  - 状态：**先行开发（优先启动）**——tshell 作为 tedit（p.9.9.7）根系，**先于 tedit 等组件完成开发**；依赖仅 tiec repl 路径（现货）与 tink 帧协议；trm 侧能力（observe）随 p.7.3 异步接入；**tie 命令行入口由 tshell 承载**（原 p.9.2 tie 命令行条目并入本档）

**tiu UI 框架（p.9.4）**

> 定位（2026-09-11 定）：独立自研、高性能、跨平台、**不依赖 trm**；可与 trm 同用。
> 
> EN: tiu (2026-09-11): independent in-house UI framework — high-performance,
> cross-platform, NOT depending on trm; usable alone or with trm.

- [ ] p.9.4.1 tiu 运行时底座：窗口/绘制/事件/资源管理（独立于 trm）——**第一闭环已落地 2026-09-14**（tiu 仓 `engine/` `api/`：API M1 对象模型 / M2 IR 编码器（布局冻结+key 派生+增量段）/ M3 Canvas 双模式会话，引擎 E1 IR loader + 软件光栅 rect/纯色/文本位图字形 + gold ≤1/255 + 双模式像素一致；剩余引擎 E2-E7 与 API T4/T5 待续）
  - 设计文档已落盘（2026-09-12）：`docs/designs/tiu-render-engine.md`（渲染引擎七层）· `docs/designs/tiu-drawing-api.md`（绘制 API 库）· `docs/designs/tiu-event-system.md`（事件轴）；上层 `docs/designs/tiu-ui-widgets.md`（UI 库，p.9.4.2 输入）
  - API 库实施计划已落盘（2026-09-12）：`docs/plans/2026-09-12-tiu-api-impl.md`（任务分解 + 契约冻结 + 无遗留闭环）
  - 渲染引擎实施计划已落盘（2026-09-12）：`docs/plans/2026-09-12-tiu-render-impl.md`（任务分解 + 契约冻结 + 后端落地顺序 + 无遗留闭环）
- [x] p.9.4.2 组件树与组合式布局框架——**已落地 2026-09-14**：tiu 仓 `ui/src/` 五模块（tree 骨架 / build 声明式构建与三类复用 / layout 约束式组合布局 / diff 差分桥 / hit 事件轴对接）+ 探针全绿；差分消费 API T2.3 增量段冻结件（子树 key 前缀 + dirty rect）
- [x] p.9.4.3 release.md 修订：tieui/trm.ui 关系对齐 tiu 独立定位——**已落地 2026-09-14**：docs/release.md（代号表 §2、§4.4）与 README 组件索引明确 tiu 独立自研定位（不依赖 trm，可与 trm 同用）

**trm-lite 协程（p.9.5）**

> 定位（2026-09-11 定）：部分协程加入 trm-lite（生成器式）；trm 不保留协程。
> 
> EN: (2026-09-11) partial coroutines join trm-lite (generator-style); trm keeps none.

- [x] p.9.5.1 生成器式协程：`yield 值` 产出 + 惰性迭代/流（惰性序列、管道、无限流）——**已落地 2026-09-14**：trm-lite `core/gen/tl_gen.tie`（trm_lite_gen：惰性源 counter/infinite + 惰性管道 fmap/filter/take 无中间表 + from_table 桥接 tiec yield 表 + 并发原子拉取 pull/pull_id），探针 gen_probe 全绿（10 万 range 惰性证明 map 仅调 5 次、无限流截断）；**语言侧契约差异如实登记**：tiec f04962d 的 yield = 急切攒表（无运行期挂起/恢复调用点），真惰性协程需 tiec 侧补 yield 挂起调用点（待后续语言档）
- [x] p.9.5.2 与既有调度整合：生成器任务可迁移/可窃取，复用 P-段双端队列（p.6.5/p.6.7 底座）——**已落地 2026-09-14**：流状态存全局注册表不绑定 worker → S-deque 窃取/迁移后继续消费不破坏惰性语义；探针 gen_mig_probe（2 worker × 8 任务共享消费 0..63/0..99 精确无重复遗漏、stolen>0、池复用）全绿

**生态应用（p.9.6）**

- [ ] p.9.6.1 tdb 完整实现：列式持久化 + 向量检索 vecsearch（zd 底座，Shipyard 四件套之一）
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

- [ ] p.9.8.1 twi 安装器：**完全 tie 自研重构**——GUI 用 tiu（自定义）、逻辑全 tie 语言、自解压 setup（六边形架构；2026.2 收尾点，最后落地）

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
- [ ] p.9.10.10 dec 真小数（精确十进制数值类型：快径 96-bit 系数内联 24B 零堆 + 慢径任意精度自动升位；加减乘恒精确、除/根/负幂可尽则精确否则显式舍入——零偏差契约；性能基准门对 Python decimal/Java BigDecimal/rust_decimal/C# decimal；科学计算域数值底座，tsci 前置；tlib 库级 `/std/dec.tie`，非组件仓；字面量后缀 `d` 待内核落地后立项语言档）
  - 设计文档（2026-09-16）：`docs/designs/dec-true-decimal.md`（两条硬约束 · 表示与零偏差契约 · 性能工程与基准协议 · 分期 p.9.10.10.1–.5）
- [ ] p.9.10.11 big 大整数底座（tlib `/std/big.tie`：基 10^18 单内核 · 加减乘除模/gcd/lcm/pow · 任意基串化（tie 连续字符台）· op_ 全套；dec（p.9.10.10）慢径改挂其上；数值底座唯一大数内核——算法族地基，后续算法模块一模块一立项持续扩展（2026-09-16 用户定））
  - 设计文档（2026-09-16）：`docs/designs/numeric-substrate.md`（分层架构 · big/进制/素数三模块定案 · base48 事实标准并入 · 分期）
- [ ] p.9.10.12 进制转换器（big 整数域 + dec 小数域双向 parse/to_str；基 2..48 默认 tie 连续字符台前缀——base48 与 std/b48 全台逐字符互认——+ 自定义字母表；跨基零偏差契约：目标基可尽则精确否则陷阱/显式 ctx）
- [ ] p.9.10.13 primes 素数寻找器（tlib `/std/primes.tie` 全套：u64/i128 确定性 Miller-Rabin + big BPSW 判定 · next/prev/nth（wheel-30）· 分段筛 yield 惰性流 · primes_between · factorize（Pollard-Brent）· π(x)（Lehmer）；基准门对 Python sympy/gmpy2 关键路径 ≥10×）

**语言功能与语法糖第二轮（p.9.11，语言层补全）**

> p.8 档（语言第一轮 21 项）闭环后的第二轮语言层；全部能力纳入当前架构、仅区分落地
> 顺序（用户 2026-09-13 全选确认）。设计文档：`docs/designs/tie-lang-round2-design.md`。
> 联动：yield 语法↔trm-lite p.9.5.1；#cfg↔p.9.7 平台移植；inline↔p.9.1.2 编译资源可调。
> 
> EN: Round-2 language layer after p.8 closed (confirmed by user 2026-09-13, full set);
> design in docs/designs/tie-lang-round2-design.md; ties to p.9.5.1/p.9.7/p.9.1.2.

- [x] p.9.11.1 match/switch **表达式**——**已落地 2026-09-13**：tiec 4192249（N_SWITCH_EXPR，表达式位 switch，`=>` 新 token lex_fatarrow，phi 汇合取值，复用穷尽检查）：模式匹配表达式位取值 `let v = when x { 1 => "a" _ => "b" }`（复用穷尽检查）
- [x] p.9.11.2 **if-let** 解构条件——**已落地 2026-09-13**：tiec 61f6c68（desugar 到 switch case/default，支持 else/else-if 链）：`if let Some(x) = opt { }`（可带 else），Option/Result 解包惯用法
- [x] p.9.11.3 **try 块** 错误聚合——**已落地 2026-09-13**：tiec 00538b2（纯语法分组+内联直发，块内 `?` 传播到当前函数，块末表达式取值）：`try { a? b? }` 块内 `?` 早退传播，无异常语义
- [x] p.9.11.4 **defer** 资源释放——**已落地 2026-09-13**：tiec 61658b9（编译期注册表+运行期 LIFO 标志链，覆盖 return/break/`?`，continue/panic 注明不触发）：`defer { f.close() }` 作用域退出逆序执行（tie 无 RAII 的钥匙）
- [x] p.9.11.5 **映射/记录字面量**——**已落地 2026-09-13**：tiec bacd0ba（`{` 消歧：首元素标识符/字符串+冒号即记录；desugar 键化表 map，rec.k 走 map 读取）：`{name: "x", age: 3}`（真实缺口，花括号消歧设计：首元素标识符/字符串+冒号即记录）
- [x] p.9.11.6 **表不可变更新**——**已落地 2026-09-13**：tiec f83c3e2（`with` 保留字 token，复制+合并产新表，多键/链式）：`t2 = t1 with {k: v}` 值语义新生表、未变部分零拷贝共享
- [x] p.9.11.7 **切片/区间糖**——**已落地 2026-09-13**：tiec b5c877b（左闭右开，越界 clamp，表拷贝/字符串子串）：`t[1..3]`/`t[..n]`/`t[n..]`/`t[..]`（表+字符串）
- [x] p.9.11.8 **剩余解构**——**已落地 2026-09-13**：tiec 0cc26b2（末位 `...rest` 收集为表，desugar 索引+切片，非末位诊断）：`var (a, ...rest) = t` rest 收集为表
- [x] p.9.11.9 **checked 运算**——**已落地 2026-09-13**：tiec e87b860（`+? -? *?` 整数溢出运行期可捕获 panic，普通运算零变化）：`a +? b` 溢出即诊断；普通 `+` 零变化；策略可配置
- [x] p.9.11.10 **inline 标注**——**已落地 2026-09-13**：tiec 8734803（LLVM 定义附加 alwaysinline，普通函数零变化）：`inline fn hot()` 内联提示（联动优化档位）
- [x] p.9.11.11 **immut 只读形参**——**已落地 2026-09-13**：tiec 14f19c2（变量重写/自增自减/字段与下标写编译期拒绝，零运行期开销）：`fn f(immut t)` 防误写/降拷贝
- [x] p.9.11.12 **@注解/属性**——**已落地 2026-09-13**：tiec 44993dd（`@name(@args)` 挂 func/struct/enum 编译期元数据 + pann 查询注册表，悬空/重复/非字面量诊断）：`@component class X` 声明式注解（联动 Keel 注册表/tieapi/tdiag）
- [x] p.9.11.13 **#cfg 条件编译**——**已落地 2026-09-13**：tiec 4658c9a（词法前按行裁剪 #cfg(键=值)/#else/#end，键 os/target/debug/release，未闭合/嵌套诊断）：`#cfg(os=linux)`/`#else` 目标求值裁剪（平台移植钥匙）
- [x] p.9.11.14 **import 别名/重导出**——**已落地 2026-09-13**：tiec 66ffb38（`as` 别名登记+重复诊断，`pub import` 重导出标记，内联模型零成本）：`import x as y`（解析层糖）
- [x] p.9.11.15 **yield 生成器语法**——**已落地 2026-09-13**：tiec f04962d（yield 标记生成器函数，签名 table&lt;elem&gt;，for 直接消费；惰性协程运行期归 p.9.5.1）：`func gen() { yield v }`（语言侧 tiec，运行时 trm-lite p.9.5.1）
- [x] p.9.11.16 **迭代器协议 + 惰性序列**——**已落地 2026-09-13**：tiec 8e39eee（has_next/next 两方法协议，for/推导式消费分派，接收者求值一次）：iterable 协议 + 惰性链（性能导向，与 p.9.5 同源）
- [x] p.9.11.17 **函数类型一等公民**——**已落地 2026-09-13**：tiec 522033e（四位承载验证 + fn 字段调用改写为函数值间接调用）：`fn(i64)->bool` 类型写法（与闭包/尾随闭包配套）
- [x] p.9.11.18 **多行表达式续行**——**已落地 2026-09-13**：tiec 6cd00f2（行尾 `\` 续行，行尾 |/-> 由 ASI 天然续行；行首运算符延续留候选）：行尾 `\`/流水线延续（修补实测缺口）
- [x] p.9.11.19 **数值字面量加强 + raw 字符串**——**已落地 2026-09-13**：tiec f323d77（数字分隔 _/0x_FF/0b，raw r"..." 免转义无插值）：`1_000_000`/`0b`/`r"..."`
- [x] p.9.11.20 **enum 关联方法**——**已落地 2026-09-13**：tiec 846e346（namespace 绑定+接收者自动引用，obj.method() 分派 &lt;Enum&gt;::method，payload 解构可用）：enum 类型方法定义（与 struct 方法约定一致）
- [x] p.9.11.21 **interface/trait 轻量化**——**已落地 2026-09-13**：tiec 5fdaf39（`interface Name { }` 结构性接口，struct/enum 命名空间方法签名兼容即隐式实现（免 impl 块），自动合成 impl 记录复用 vtable/提升/泛型约束全套机制，缺方法/签名不匹配诊断）：`interface Drawable { fn draw(); }` + 实现检查（tiu/t3d/tge 受益）
- [ ] p.9.11.22 **fn 值捕获语义白名单**：安全区捕获面（可捕获什么）/ 可变捕获标注 / 与事件循环线程的交互——tiu 控件动作参数位冻结等待此档（tiu-ui-widgets.md §15.4/§15.6）
- [ ] p.9.11.23 **命名实参 × 默认值打通**（掩码预计算）——依据 `docs/designs/param-system-design.md` §3：默认值声明连续居尾不变，命名实参可跳过居尾默认段任意子集（`f(x: 1, z: 3)` 合法）；声明侧预计算默认值常量表 + 可选位掩码入符号表，调用点 O(1) 查表补齐（顺手替换现有 O(n²) 名字匹配）；验收：跳过/乱序/混用/区间与变参负例探针 + 自举不动点 + 回归不劣化
- [ ] p.9.11.24 **默认值 const 白名单**——依据 param-system-design.md §4：放宽到字面量 + const 引用 + 常量算术/比较/拼接 + const fn 调用（p.8.1.1 底座）；声明侧求值一次存符号表，调用点 O(1) 读缓存；struct 字段默认值共用同一 evaluator 同步放宽；排除引用形参（运行期默认值）与运行期任意表达式；验收：const fn/算术/引用探针 + 非白名单负例 + 求值次数断言
- [ ] p.9.11.25 **方法默认值 + 命名实参解锁**——依据 param-system-design.md §5：`obj.method(...)` → `命名空间函数(obj, ...)` 转发中接收者首参不参与重排/补齐，其余规则同普通函数；actor 方法仍限标量；清除 language.md §6.1「方法默认值参数留待 M3」悬空项
- [ ] p.9.11.26 **参数传递约定矩阵**——依据 param-system-design.md §6：值拷贝（默认）/ `ref` 可写借用 / `immut` 只读借用 / `move` 所有权转移四约定统一为参数位唯一声明面（immut×ref 互斥诊断、move 后使用走 smove 检查）；先归位声明面与诊断，`ref` 扩展非表类型随后；验收：约定 × 值类别矩阵探针 + 大表 immut 免拷贝基准
- [ ] p.9.11.27 **编译期值参数**（泛型系统扩展，方向定稿）——`[const N: i64]` 式编译期值参数：固定尺寸定长容器零堆、t3d/tsci 数值场景受益；详细设计（实例化缓存/与变长泛型组合/诊断）另出设计稿，依据 param-system-design.md §7
- [x] p.9.11.28 **return 可省**（等号体 + 单表达式体）——依据 `docs/designs/return-elision-design.md`：`func f(x: i64) -> i64 = x * 2` 等号体与「体恰一条表达式语句」隐式返回两种形式（desugar 等价，复用 when/try 块值 phi 机制）；闭包纳入（体长 1 触发）、void 允许值丢弃、`?` 收尾允许、返回类型强制显式标注（泛型提升/递归自引用/宽类型落型三复杂度源零新增）；尾随闭包语义不动；明确排除 Rust 式任意块末隐式（ASI 词法层跨层耦合 + 分号语义坑）与 Ruby/Julia 全隐式；验收：形式 × 函数类别 × 返回/void/`?` 矩阵探针 + 混用与体长 2 负例 + 自举不动点 + 回归不劣化；**[已落地 2026-09-17，tiec 0786441：等号体 + 单表达式体，含负例诊断]**
- [x] p.9.11.29 **doc 注释 `///`**——依据 `docs/designs/round3-sugar-safe-std-design.md` §3：声明前连续 `///` 行附着为文档字符串，入诊断元数据注册表（p.9.11.12 @注解同路）落盘，tsp LSP hover/补全直接消费；纯编译期零运行时；**[已落地 2026-09-17，tiec 0786441：doc 注册表 + pdoc_* 查询接口 + `--dump-docs`]**
- [x] p.9.11.30 **多行字符串三引号**——依据 round3 设计 §2：`"""..."""` 跨行免转义 + 闭引号行基准缩进剥离（Swift 对齐语义）+ 复用 p.8.2.3 插值拼接链；**[已落地 2026-09-17，tiec 9d81a86：三引号多行 + margin 剥离 + raw 语义 + 插值]**
- [x] p.9.11.31 **选择性导入**——依据 round3 设计 §6：`import x.{a, b}` 按名登记，desugar 到现有 import 机制，`pub import` 组合合法，零新诊断码
- [x] p.9.11.32 **类型别名 `alias`**——依据 round3 设计 §4：透明别名（语义层展开，无标称区分），支持泛型参数 `alias Pair<T> = (T, T)`；`type` 已被文件头占用故取 `alias`
- [x] p.9.11.33 **struct 的 `with`**——依据 round3 设计 §5：`p = p with {x: 1}` 值语义复制 + 指定字段覆盖 + 未提及字段编译期共享；复用 p.9.11.6/p.9.11.5 机制；不做 Rust `..base` 形式；**[已落地 2026-09-17，tiec 9da7672：struct `with` 值语义复制 + 字段覆盖]**
- [ ] p.9.11.34 **短闭包 `it`**（与 p.9.11.22 捕获白名单同批）——依据 round3 设计 §1：闭包体未声明 `it` 绑定为唯一隐式参数（类型由上下文 fn 类型推定，无上下文报诊断），与 p.9.11.28 单表达式隐式返回咬合 `arr.map({ it * 2 })`；尾随闭包升级（无参 void → 可带参可返回）同批定；多参 fn 上下文不支持
- [ ] p.9.1.4 **unsafe 安全封装库**——依据 round3 设计 §7（用户指令：高频 unsafe 安全写法进标准库）：①CStr/FFI 所有权桥（`c_str` 注册 defer 收尾自动 free / `from_c_str` 拷入并释放源，NUL/非 UTF-8 可捕获负例）②slice 安全视图函数族（`view`/`view_len`/`view_get` 越界可捕获/`view_sub`/`view_copy_into`，纯 tie 收拢 slice_of 散装帮手）；alloc(n) 暂不立 Buffer（动态表连续缓冲代偿，随 bytes 库观察）；atomic/volatile/asm/unsafe goto 明确不封装（专家向，封装模糊危险边界）；验收：封装库单测（含负例）+ FFI 实战回放 + 安全路径免 unsafe 上下文验证
- [ ] p.9.11.35 **安全 unsafe 重分类**——依据 `docs/designs/safe-unsafe-reclassification.md`（用户指令：安全的 unsafe 踢出 unsafe；判定准则 = 不可能引发 UB）：`atomic<T>` 全家、`slice<T>` 下标/len/slice_of（边界防护转正）、`ptr<T>` 声明/比较/传参、`#[repr(C)]` 声明 → 安全；`*p` 解引/指针算术、`alloc(n)`、`addr_of`、`extern` 调用、volatile/asm/unsafe goto 维持 unsafe（同一类型两访问面两门禁，Rust 安全切片 vs 裸指针同构）；凭据门禁面正交不动；落地时同步修订 language.md §14/§16 标注；验收：正负例门禁探针 + 越界 panic 行为逐字节一致（纯门禁移动零运行期变化）+ 自举不动点 + 回归不劣化
- [ ] p.9.11.36 **unsafe 凭据双锁**——依据 `docs/designs/unsafe-credential-lock.md`（用户指令：凭证系统推广到全体 unsafe，最后一道安全锁）：unsafe = 门禁上下文 + 域凭据双锁缺一不可；五域定稿 `mem`（解引/算术/alloc/addr_of）·`ext`（extern 全链）·`share`（§7.1.1 A 组）·`trm`（C 组）·`raw`（新增：asm!/MMIO/unsafe goto 裸机器面）；持证三形态（函数级 `#[unsafe.<域>]` 隐式持证 / 块级 `unsafe use`·`unsafe.with` / 文件级 `type tie<logic> + unsafe[域]`）；guard<cap> move-only 拷贝即诊断、挂空凭据告警；产出 unsafe-audit 清单入 Keel 指纹树（p.7.1.5 审计链）；破坏性变更无兼容期（对齐 p.9.0 纪律），自举链 unsafe 位同批迁移作完备性实证；验收：五域正负例 × 三持证形态矩阵探针 + 审计清单逐行对账 + 自举零裸 unsafe + 回归不劣化
- [ ] p.9.1.5 **rdu 扩充**（嵌入式基础层第二批）——依据 `docs/designs/rdu-expansion-design.md`（用户指令：扩充 rdu + 定位定稿「默认仅 rdu 即够，不学 std/ext/sys」）：无栈纪律 v1.1（调用方预分配缓冲可传参）+ v1.2（零堆型原语精确化：volatile/atomic 准入）；批一 `rdu/encode`（hex/base64 无查表/varint LEB128）+ `rdu/control`（PID 抗饱和 + EMA + lerp/map/constrain，f64 与 Q16.16 双变体）+ `rdu/fixmath`（fixed_sqrt Newton + CORDIC 无查表 sin/cos/atan2）；批二 `rdu/hash`（xxHash32/64 增量 + Adler-32 + sum8/xor/LRC）+ `rdu/bitfield`（位段 pack/unpack/sget/sset）+ `rdu/reg`（volatile 寄存器安全面，模块内持 raw 凭据对外免 unsafe，芯片映射归厂商包）+ `rdu/time`（tick 换算/回绕安全 uptime）；批三 `rdu/vec3`/`rdu/quat`（struct 值语义 IMU 姿态）+ `rdu/ring`（RingState + 调用方 backing）；批四候选 `rdu/sha256`（OTA 固件校验）；**自足清单九能力域 = rdu 完成定义**（数值/校验/编码/控制/姿态/缓冲/寄存器/时间/位段），清单外（GUI/网络栈/RTOS）明示不在默认面；加密仍走 std/ext、动态容器仍调用方自持；验收：RFC/官方 KAT + CORDIC 角度扫描误差门 + PID 阶跃探针 + freestanding 链接验证 + 纪律 grep 门（v1.2 后含 volatile 白名单）
- [ ] p.9.1.6 **sys 扩充**（平台层二期，用户指令：扩充 sys）——依据 `docs/designs/sys-expansion-design.md`：定位定稿「桌面/系统级开发的平台默认面，OS 深度集成不手写 extern」；全库纪律 = 库内持凭据对外安全面（p.9.11.36 落地后用户面零 unsafe）+ 平台能力清单九域（进程线程/动态库/文件元数据卷/输入/电源/shell 通知/高精度时间/网络枚举/硬件枚举，逐平台打勾 win32/posix/darwin）；批一 `sys/dynlib`（LoadLibraryW+dlopen 双后端 + extern 签名绑定 helper，泛化 rng-adv BCrypt 模式，解锁 iphlpapi，句柄 defer 收尾）+ win32 二期核心（proc_launch 完整版/shell_open/qpc 纳秒级/磁盘卷/文件元数据）；批二 `sys/input`（GetAsyncKeyState 键鼠 + win_enum + 显示器枚举，tiu 引擎与输入轴取数口）+ `sys/power`（电量/阻睡眠/用户空闲）+ `sys/net` 转正（iphlapi 动态加载，net_adapters 弃注册表代理）；批三 `sys/posix`（dlopen 双后端并入/poll-epoll/procfs/mmap/signal 可捕获）+ `sys/darwin` 登记（挂 p.9.7.1）；不进 sys：GUI 面（归 tiu）、网络栈（归 std-http/tink）、加密（std/ext）、驱动内核面；验收：存在断言式探针（仿一期 21 条范式）+ dynlib 实测加载 BCrypt/iphlapi + net_adapters 与注册表代理值对账 + 用户面零 unsafe 验证
- [ ] p.9.1.7 **std 扩充**（应用默认层，用户指令：扩充 std + 生态裁决「td/zd 取代 json」）——依据 `docs/designs/std-expansion-design.md`：**生态内数据格式 = td/zd，json 降级外部边界适配器并冻结**（std/json 与 JSON5 停止增强，文档显式标注「生态内数据交换用 td/zd」）；批一 `std/td`（td 文本↔表/map/struct 双向编解码 + 行列定位诊断）+ `std/zd`（keel zdpub 五件套用户面化：publish/load/fingerprint/integrity，应用持久化默认 zd）+ `std/tds`（td schema 校验，对标 JSON Schema 生态位）+ `std/log`（结构化日志，行格式用 td 非 json，收编 ext/log）；批二 `std/q`（table/map 内存集合查询 group_by/join/agg/order_by，管道箭头组合位）+ `std/path`（跨平台路径算术零 IO）+ `std/cli`（子命令/旗标/用法生成，tsh 同风格）；批三 `std/xml`（边界适配，路径取值子集）+ `std/uuid`（v4 csprng 底座/ULID）+ `std/env`（跨平台统一面，确立 std 可依赖 sys 层序）；不进 std：toml（生态配置已定 td）、yaml/json 增强（冻结）、ORM（tdb 定位）；验收：td↔表全类型 roundtrip 矩阵 + zd 与 keel zdpub 同指纹互通 + tds 校验负例集 + SQL 心算对账样例 + 双语文档一语义一名

**语言缺陷修复批次（p.9.12，tiu/tsp 实战驱动）**

> 2026-09-14 从 tiu 落地 9 条坑与 tsp LSP 帧损坏中收敛的编译器缺陷修复（用户排期）。源问题：tiu 坑复盘（无 struct 数组/引用共享/ns 禁 const/f64 默认值崩溃/enum 分隔/越界写静默/保留字/无码点字符）+ tsp「未定义函数」误报（实际为 tiec 长串折叠丢内容导致 LSP 帧损坏）。
>
> EN: p.9.12 — compiler defect fixes driven by tiu landing & tsp LSP frame corruption.

- [x] p.9.12.1 长字符串常量折叠/发射丢内容（tsp LSP 帧损坏根因）——**已落地 2026-09-14**：tiec 64b69a7（RC1：全局初始化引用先前折叠全局 S_N_VAR 不折叠→空/零，补 global_init_fold VAR 分支 + llvmgen.global_folded_of；RC2：字面量 `}}`→`}` 无条件折叠损坏 JSON 花括号，lex_scan 只保留 `{{`→`{`、插值段花括号转义移 pexpr 折叠）：>500B 全局拼接逐字节正确、长串+尾、`}}` 保留；自举不动点 B4C69459；tsp initialize 帧 json.loads VALID（frame_dump.py）
- [x] p.9.12.2 表下标写越界静默丢弃 → 自动扩容——**已落地 2026-09-14**：tiec 32d497b（s21_table_set 重写：i≥len 按元素零值逐槽扩容 max(len,i+1) 后回写；新增 s21_index_raise 负下标诊断 + s21_elem_zero 空串修复）：空表 t[5]=42→len6、连续写、t[1000] 零填、string/f64/bool 扩容、复合赋值、局部/全局表全过；越界读语义不动；自举不动点 D5F239DA（ECS/tiu 对象池稀疏寻址前置）
- [x] p.9.12.3 struct 字段 f64 默认值整数字面量 irgen 崩溃——**已落地 2026-09-14**：tiec 87115fe（tig_struct_construct 缺省路径 vt 改为 tig_expr 实际发射类型，统一走 S1.3 收窄 sitofp/trunc）：f64=5/f32=3/u16=7/bool/R(2)/R(3.0) 全 PASS；自举不动点 A15E9980
- [x] p.9.12.4 命名空间体内 const 声明——**已落地 2026-09-14**：tiec f45060e（parse_namespace 加 lex_const 分支；scollect_port 全名登记 gb_*；sinfer gb_find_ns 前缀补全；scheck const 只读拦截；irgen/llvmgen @ns$NAME 发射）：ns::NAME 引用/跨 ns/顶层同名不冲突/重赋值拒绝 13/13 PASS；自举不动点 AC4DDCA4（tiu 常量归位）
- [x] p.9.12.5 enum 变体分隔符放宽——**已落地 2026-09-14**：tiec 2554c34（parse_enum 硬 expect(lex_semi) 改可选 `;`/`,`/无空格，AST 零变化）：同行空格/逗号/混用/payload 同行/尾随逗号 29/29 PASS；自举不动点 4DDCAB21；既有换行写法零破坏
- [x] p.9.12.6 `table<R>` 结构化行池（tiu 坑 #1 定案：表元素由仅内建扩展为 struct 行池、按 id 稀疏寻址、行级自动扩容；复用 p.9.12.2 自动扩底座；零新增关键字）——**已落地 2026-09-14**：tiec 57ee7e8（列表达式已天然可编码，非 struct 表路径单句柄假设为阻塞点；新增 rp_* 系列——列 alloca 登记/字段默认构造复刻 tig_struct_construct/单列零值扩+set/负下标诊断+多列同步扩逐字段写/逐字段读+聚合构造越界返默认行；边界：返回值/形参/全局行池 v1 拒绝、table_push 拒绝、`t[i].f=` 就地写 v1 走整行 RMW）：写读回环/稀疏大 id 前驱默认行/零行/多字段含表字段/复写/行间值拷贝/越界读默认行/非 struct 表零变化 全 PASS；自举不动点 7620C884；回归 s21 159P/6F/2S 同基线（tiu DrawList 列式手写可随即替换为行池）
- [x] p.9.12.7 单函数多路字符串拼接 → LLVM「PHI 未分组」崩溃——**已落地 2026-09-14**：tiec 9da5eec（根因：llvmgen_inst 字符串 phi（op33）的 str_cat（op56）incoming 在合并块 phi 处临时发射 inttoptr——插 phi 前致未分组、分支块值不支配合并块致不支配；修复：op56 在**定义块内**补 `%spN = inttoptr` companion、to_ptr/typed_ref 返回之，phi 恒居块顶；opt InstCombine 折叠零开销）+ 76b06bf（自举不动点 53F899D8）；phi_probe（2/3 臂 if·多臂 switch·嵌套·return·管道）7 项 PASS；回归 s21 158P·7F·2S / diag ALL PASS / m5 8P·0F 与旧同（7F=6 环境+1 既有边界）；注：编译缓存键不含 import 文件（改后端命中旧缓存）建议另开子项

**语言基元与运算符（p.9.13，面向"人"的书写体验）**

> 设计文档（2026-09-14 定案）：`docs/designs/tie-primitive-op-design.md` v0.2。三大目标：常用平台无关函数进语言（免 import 基元前置）、高频操作进语法（运算符与单箭头，非方法链）、全新并行书写（graph 一等值类型 + 波次 SDF，默认安全）。先决：单箭头统一（`->` 唯一，`=>` 移除零兼容别名）。
>
> EN: p.9.13 — language primitives & operators for human writing ergonomics; single-arrow unification (breaking) precedes.

- [x] p.9.13.1 单箭头统一（先决破坏项）——**已落地 2026-09-14**：tiec c11884d（lexer 删 lex_fatarrow + 新诊断「`=>` 已移除，请用 `->`」，`>=` 等零影响；parser 臂分隔符换 `->` + parse_ternary/parse_case_arm_pattern 让 when 守卫与模式止于顶层 `->`）· 4ccb03d（存量 20 处迁移 + 探针）· d4815a0（自举不动点 B0689D5B）；grep `=>` 代码位=0（豁免：注释/诊断串/负例 fixture）；回归 s21 159P·6F·2S / diag FAILS=7 / m5 8P·0F 不劣化；tlib/tshell 无 `=>` 无需迁移
- [ ] p.9.13.2 基元前置：编译器级隐式前置（免 import 裸名、同名用户遮蔽），首批 ~30 词（字符串/容器/数学转换/调试输出）
- [ ] p.9.13.3 运算符批：`in`/`not in`（string 子串/table 元素/map 键）、`+` 扩展（string+标量、table+table 值语义、map 合并）、`**`/`//`/`%%` + `**?` checked 变体（溢出 panic 对齐 p.9.11.9）
- [ ] p.9.13.4 箭头续扩：块管道、进容器/字段/解构、接基元/运算符、条件管道、临时单参函数、`(a,b) <- t` 反解构
- [ ] p.9.13.5 并行数据流图：`graph` 一等值类型（字面量 `{A}-{B}`、`x -> g` 执行、组合 g1-g2/g1->g2）；**图即表**（graph 无独立存储=节点/边两表+共享读视图，表语法直接操图，表→图→表闭环）；`-` 分叉 `~` 汇合回边；波次 SDF 执行（输入流驱动收敛，回边=下一波，trit 收敛判定）；**graph 默认不可变**（安全区禁原地变异），unsafe 内可变 graph + 同批运算符作原地图变异（波界生效）；图论套件（cycle/topo/conn/reach/shortest+critpath/maxflow·mincut，算法=表变换全表化）；**trit 三态穿透全套**（标记 trit 字段、算法输出 trit 域、`tprop(g)` 三态传播原语 + unsafe 原地写标记）；安全分层（SAFE：构造/组合/执行/读视图/算法；UNSAFE：可变声明/变异运算符/捕获放宽/跨线程）+ 三裁决（读视图只读诊断 / `**?` checked / tprop 双形态）；捕获白名单 + 有界队列背压 + join 屏障 + trm-lite 调度
- [ ] p.9.13.6 文档/示例/迁移说明（含 `=>`→`->` 存量改写样例）
- [x] p.9.13.7 内置库独立仓 tlib（p.9.13 前置，先于 .1 执行）——**已落地 2026-09-14**：std/ext/rdu/sys 四目录 218 提交经 subtree add 迁入 **tie-lang/tlib**（TPL2.0 + 双语 README + 四层定位 std/ext/rdu/sys；tiec 4 笔：1ccc6d5 库根别名 import（`/std /ext /rdu /sys`，`TIE_LIB_ROOT`/`--lib-root` 取值）· 46a5e99 230 文件 import 迁移 · 988f38a 删四目录（git ls-files 四库=0）· b744369 fetch-lib.ps1 + 打包收口）；自举不动点 F0625533，回归 test-diagcodes FAILS=7 / s21 159P·6F·2S / m5 8P·0F 不劣化；release.md 组件清单加 tlib 行（tiec 内置库零副本）
- [x] p.9.13.8 tsh 脚本化（用户规则：禁用 .ps1，只用 tshell）——**已落地 2026-09-14**：tsh 本机可用（tiec p.9.13.7 重建 tsh_main/tsh_main+tedit_embed；interp 缺陷①-④探针全 PASS，已由 tiec 修复；tshell bed678c 收录探针）；tiec 5 个 .ps1 全量迁移 .tsh.tie（regress-s21/package/fetch-lib/m6_actor_regress/verify-tiedap，c689af0 已推；`git ls-files *.ps1`=0，豁免仅文档/注释文本引用）；门禁经 tsh 实测基线不劣化（s21 159P·6F·2S / diag FAILS=7 / m5 8P·0F / tiedap OK / package 端到端）；tsh interp 5 项限制已文档化（if 块重赋值读空·exit 顺序·逐帧 stdin 喂入等）

**tie 模组开发一等支持（p.9.14，自 Subterra 计划移交）**

> 目标：tie 写模组达到与 Kotlin/C# 写模组同等体验——tiec 编译到目标平台**托管运行时**（JVM 字节码 / .NET IL），完整互操作宿主 API（调用、接口实现、注解/attribute、集合/字符串/枚举类型映射），与 tiec→DLL→FFM 桥互补：热点片段走原生 DLL，完整模组逻辑走托管。2026-09-16 自 Subterra 路线图整体移交（原编号 p.2.34.1–.6）：tie 本身的开发归 tie 轨道，消费平台不修改 tie 本身；消费侧衔接（api 契约 / devkit 接线）待后端落地后回给消费平台另行排期。
>
> EN: p.9.14 — first-class tie modding (transferred wholesale from the Subterra roadmap, orig. p.2.34.1–.6): tiec managed targets (JVM bytecode / .NET IL) with full host interop, complementary to the DLL/FFM bridge (hot paths native, full mod logic managed); consumer-side wiring is re-planned by the consuming platform once the backends land.

- [ ] p.9.14.1 tiec JVM 目标后端：tie → JVM 字节码（.class），在宿主 JVM 内直接运行（原 p.2.34.1，MC 模组主路径；模块化后端挂进 tiec，缺省仍原生目标，JVM 目标按需切换）
- [ ] p.9.14.2 tiec .NET 目标后端：tie → .NET IL（CIL），供 .NET 宿主、与 C# 写 .NET 程序同等体验（原 p.2.34.2，非 MC 路径的通用托管目标能力）
- [ ] p.9.14.3 JvmInterop 互操作层：方法绑定 / 接口实现 / 注解 / 集合、字符串、枚举类型映射（原 p.2.34.3；契约面随消费平台落地，本档锁定能力边界）
- [ ] p.9.14.4 DotnetInterop 互操作层：.NET API 调用 / 接口实现 / attribute / 类型映射（原 p.2.34.4，同上）
- [ ] p.9.14.5 tie 模组装配骨架：td 数据包 + tie 逻辑一体（以 tie 注册方块/物品/事件/配置），scaffold 生成 tie 模组工程（原 p.2.34.5）
- [ ] p.9.14.6 tie 模组探针 + E2E：tie 编写的模组在宿主内确定性运行 marker（原 p.2.34.6）

### 关联定稿（修订项）

> 以下既有定稿在 2026.2 按本 ROAD 对齐修订（就地改，不另立档）：
> 
> - docs/designs/trm-final-design.md（对齐 p.7.3 trm 重定位）
> - docs/release.md（对齐 p.7.2 多仓拆分与聚合发行、p.9.4 tiu 独立定位、发行物出仓）
> - docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（落地编号对齐本 ROAD p.7.1.x）

EN: Existing finalized docs to be aligned during 2026.2 (revised in place, no separate
tier): trm-final-design.md, release.md, plugin-kernel-design.md.
