# tie 语言基元与运算符（设计 v0.4 / ROAD p.9.13）

*EN: tie language primitives & operators (design v0.4 / ROAD p.9.13)*

## 定位 / Positioning

面向**人**的书写体验（本设计明确不为 AI 生成优化）。三个目标：
* 常用且平台无关的函数**进语言**（免 import、免前缀、裸名可用）；
* 高频操作**进入语法**（运算符与箭头，而非方法链）；
* 探索一条**全新的并行书写方式**（数据流图 + 波次执行），开发极快且默认安全。

基线：p.8.2.8 箭头定则 · p.9.11 语法糖两波 · p.9.12 缺陷批次 · trm-lite 调度/actor/信道。

*EN: This design targets HUMAN writing experience (explicitly NOT AI-driven codegen). Three goals: (1) common platform-independent functions become language primitives (no import, no prefix, bare names); (2) high-frequency operations become syntax (operators & arrows, not method chains); (3) a brand-new parallel writing model (dataflow graph + wave execution) that is fast to write and safe by default. Base: p.8.2.8 arrow rules, p.8/p.9.11 sugar waves, p.9.12 fixes, trm-lite scheduler/actor/channel.*

## 1. 单箭头统一（先决，破坏性）/ Single-arrow unification (breaking)

* `->` 成为 tie **唯一箭头**，统一五处语义：数据流管道（p.8.2.8）、函数/宏返回位、match 臂 `pat -> expr`（原 `=>`）、宏形参/返回（`macro m(x: code) -> code`）、块管道绑定 `{ v -> expr }`。
* `=>`（lex_fatarrow）**删除**，不给兼容别名（对齐彻底迁移纪律）。存量代码迁移验收 `grep "=>"` 清零。
* 消歧定则（写进 parser）：块管道 `x -> { v -> expr }` 内，**首个 `->` 前的裸标识符即为绑定名**，其后整个表达式（可含管道）为结果；与 match 臂 `pat -> expr` 同构，无需额外关键字。

*EN: `->` becomes the single arrow covering five roles (pipeline / return-position / match arm / macro types / block-pipe binding). `=>` (lex_fatarrow) is removed with no compat alias; migration verified by grep-zero. Disambiguation: inside block pipes, the bare identifier before the first `->` is the binding name; everything after is the result expression — structurally identical to match arms.*

## 2. 基元前置 / Primitive prelude (L1)

* 机制：编译器级**隐式前置基元**——精选平台无关函数由编译器预注为全局裸名（免 import、免前缀）；**同名用户定义优先遮蔽**，前置不拦截；实现落 std（tie 写）或内联原语；OS 无关（Windows/Linux 一致）。
* 首批清单（约 30 个，横跨四域）：
  * 字符串：trim / upper / lower / split / join / contains / starts_with / ends_with / find / replace / repeat / substr（按码点）
  * 表/容器：copy / sort / reverse / contains / index_of（len 已有）
  * 数学与转换：min / max / abs / clamp / floor / ceil / round / pow / sqrt / to_i / to_f（to_string 已有）
  * 调试输出：println / print / assert / dump（结构化打印表/字符串）

*EN: Prelude mechanism — compiler-registered bare-name primitives, no import/prefix, user definitions shadow them (no interception), std-backed or inline, OS-neutral. ~30 entry list across four domains (string / containers / math & conversion / debug output).*

## 3. 运算符扩展 / Operator extensions (L2)

* `in` / `not in`（中缀布尔）：右 string→子串包含；右 table→元素包含（按类型比较）；右 map→键包含（O(1)）。优先级：比较与逻辑之间。`not in` 为一词法组合，`in` 复用既有保留字。
* `+` 语义扩展（原数字/string+string 语义不变）：string+标量→自动 `to_string` 拼接；table+table→**值语义新表**（全拷，性能裁决同 p.9.11.6 `with`，大表慎用并文档化）；map+map→合并新表。
* `**` 幂（右结合，高于 `*`；int 幂走快速幂、f64 走 libc pow）；`//` 整除（int 族截断；f64 走 floor-div）；补 `%%` f64 取余成对。全部 desugar 到既有原语，零新运行期依赖。

*EN: `in`/`not in` membership (string substring / table element / map key); `+` extensions (string+scalar concat, value-semantics table concat, map merge — original semantics unchanged); `**` power (right-assoc above `*`), `//` integer/floor division, paired `%%` f64 modulo. All desugar to existing primitives.*

## 4. 箭头续扩 / Arrow extensions

* 匿名块管道：`x -> { v -> expr }`（复用单箭头，绑定名显式）。
* 管道进容器/字段/解构：`t -> [i]`、`p -> .field`、`t -> (a, b)`。
* 管道接基元/运算符：`t -> in xs`、`t -> + [x]`、`s -> upper`。
* 条件管道：`x -> cond ? f : g`（管道接选择）。
* 管道声明临时单参函数：`f = t -> expr`（接 p.9.11.17 fn 值；块管道产出的本就是函数值）。
* 反向解构：`(a, b) <- t`（对称复用 `<-`）。

*EN: piped anonymous blocks `x -> { v -> expr }`; pipe into index/field/destructure `t -> [i]` `p -> .field` `t -> (a,b)`; pipe into primitives/operators `t -> in xs` `t -> + [x]`; conditional pipe; pipe-as-temporary-single-arg-function `f = t -> expr`; reverse destructure `(a,b) <- t`.*

## 5. 并行数据流图（全新并行书写）/ Parallel dataflow graph (v0.3: graph value + unsafe magic + graph-theory suite)

* **graph 新值类型**（v0.2 定案）：并行图是一等数据值——先构造、可存储/传递/组合，再执行。
  内部 = 节点表（fn 值）+ 边表（前向/分叉/汇合/回边记录）+ 入口/出口标记；以现成表/struct 表达，
  语言只做类型封装 + 检查（边类型一致性、回边有界性）。
* 图语法（图内运算符）：
  * 节点 = 模块（普通 tie 函数、或 `{ v -> expr }` 匿名单参块）；函数名即节点名，匿名块自动编号；
  * **图值字面量** `{ A } - { B -> ~ A }`：花括号=节点模块，`-` 并行分叉，`~` 汇合/回边
    （`a -> ~ b`：a 的尽头汇回 b 作为其新一波输入；多入边节点自动 join = 所有入边到齐才放行）；
  * **执行** = 统一箭头送值 `x -> g`（图 = 可运行的数据流函数值，波次 SDF 语义见下）；
  * **组合**：`g1 - g2` 并行组合、`g1 -> g2` 串联、`~` 并入 g1 内——值语义，返回新图。
* **执行模型（定案：波次 SDF）**：入口节点每吐一个值启动一波；回边把结果带回前节点作为下一波输入；
  收敛由「节点条件 + 入口流长度」自然决定；入口排空 → 全图结束；无显式波次上限，静态不可证处运行期有界守护兜底。
* **图出口**：图的值 = 各末端节点末波结果组成的表；汇合点取 join 值。落地版再冻结细则。
* **安全模型（v0.2：默认不可变）**：
  * 安全区：graph 不可声明可变、不可原地改结构——只能整体替换或组合（返回新图）；读模式 `g[A]`/`len(g)` 可用；
  * **unsafe 强大魔法（v0.3 定案）**：
    * 声明：`unsafe { var g: graph = { A } - { B -> ~ A } }`（安全区写 `var g: graph` → 诊断）；
    * 节点寻址 `g[name]`（读=节点 fn 值；写=换体）；
    * **原地变异 = 与图字面量同构的写模式**（全运算符，无新保留字）：
      `g[A] = { v -> … }` 换体 · `g[A] - { C }` 分叉加节点 · `g[C] -> g[D]` 加前向边 · `g[B] -> ~ g[A]` 加回边 ·
      `g[A] -|` 断全部出边 · `g[A] <-|` 断全部入边 · `g[A] ->x g[B]`/`g[A] ~x g[B]` 删特定边 ·
      `g[A] -><` 删节点（连带边，悬空自动清理，残留引用诊断）；
    * **波界生效（定案）**：结构性变异只在**波次边界**生效——图执行中冻结，改动排队到下一波重排落地；
      并发安全来自调度同步点而非锁；
    * unsafe 内捕获白名单放宽（开发者担责），有界守护保留。
* **graph 图论算法套件（v0.3 定案，基元函数形态，免 import）**——graph 同时是"可算的图结构"：
  * 结构分析：`cycle(g)` 环检测（回边合法性/收敛性校验）· `topo(g)` 拓扑序（无环行走序/可行执行序）·
    `conn(g)` 连通分量 · `reach(g, a, b)` 可达性；
  * 路径与工期：`shortest(g, a, b)` 加权最短路径（BFS/非负 Dijkstra）· `critpath(g)` 关键路径 CPM（最长耗时链）；
  * 流与匹配：`maxflow(g, s, t)` 最大流 / `mincut(g, s, t)` 最小割（Dinic）；
  * 双重用途：① 图自身分析（回边环合法、拓扑可行序、关键路径 → 供波次调度器静态分析/收敛证明/并行度上界）；
    ② 纯图计算模拟（依赖图、状态机、网络/供应链、资源分配）。
* **与 table / trit 联动（v0.4 定案）**：
  * **table ↔ graph**：
    * 建图：`graph(edge_tbl)` / `graph(node_tbl, edge_tbl)` 基元函数用表批量构图（边表 = (from, to, kind) 平行列或行池 `table<EdgeRow>`）；
    * 导出：`nodes(g)` → 节点名表 · `edges(g)` → 边表（from/to/kind 平行列）——结果可接 §2 表基元（`in`/`join`/`sort`）；
    * 算法结果天然表承载：`topo(g)` → 序表 · `conn(g)` → 分量表 · `shortest(g,a,b)` → (路径表, 总权) · `maxflow(g,s,t)` → 流量表；
    * 行池协同：`table<R>` 字段可持 graph 句柄（i64 号入列）；graph 元素数组/嵌套 v1 不做。
  * **trit ↔ graph**：
    * 节点/边标记可用 trit（-1 阻塞 / 0 待定 / 1 就绪）——依赖图三态传播、状态机图三态驱动；
    * 图算法输出可带 trit 语义：`reach(g,a,b)` 三态可达（-1 不可达 / 0 未知 / 1 可达）· `cycle(g)` 可用 trit 表达
      （0 无环 / 1 有环），为模拟场景保留"未定态"表达；
    * 波次 SDF 收敛条件可直接用 trit：回边收敛 = 节点末波输出 trit 到齐判定（与 §3 trit 类型一致）。
* 落地范围：先最小内核（graph 类型 + 字面量 + 执行 + 波次 SDF + 安全默认），再 unsafe 魔法，最后图论套件 + table/trit 联动。

*EN: v0.4 — `graph` is a first-class value (construct via literal `{A}-{B}`, execute `x -> g`,
compose `g1-g2`/`g1->g2`). Execution = wave SDF (entry emits a wave per input; back edge feeds
next wave; convergence from node condition + input-stream length; runtime boundedness guard
where not statically provable). Graph value = table of end-node wave results. Safety-by-default:
graph immutable in safe code (only whole-value replacement / composition; reads `g[A]`/`len(g)`
allowed). **Unsafe powerful magic (v0.3): `unsafe { var g: graph = … }`; node addressing
`g[name]`; in-place mutation fully via operators** — `g[A] = { v -> … }` rewire body, `g[A] - { C }`
fork-add node, `g[C] -> g[D]` add forward edge, `g[B] -> ~ g[A]` add back edge, `g[A] -|` drop
out-edges, `g[A] <-|` drop in-edges, `g[A] ->x g[B]`/`g[A] ~x g[B]` delete edge, `g[A] -><` delete
node+edges (no new reserved words). **Structural mutations take effect only at wave boundaries**
(graph frozen while running; changes queue to next-wave rewire; concurrency safety from
scheduler sync points, not locks). Capture whitelist relaxed inside unsafe; boundedness guard kept.
**Graph-theory suite (v0.3, bare-name builtins): cycle/topo/conn/reach/shortest+critpath
(maxflow/mincut)** — dual use: analyzing the executable graph (cycle legality, topological order,
critical path for wave-scheduler analysis) and pure graph computation/simulation (dependency
graphs, state machines, networks/supply chains, resource allocation).*

## 6. 边界 / Bounds

* 平台相关（文件/进程/网络/时钟/会话）不进基元层；
* 方法链不加（保持现状）；AI 专用糖不做；
* 性能裁决：`+` 表拼接 = 值语义全拷（文档明示）；`in` 表元素 O(n)、map 键 O(1)；`**` int 用快速幂避免浮点化；
* 一切新语法可 desugar 到既有原语/内建，不引入新运行期负担。

*EN: No platform-specific entries; no method chains; no AI-specific sugar; performance rulings (table `+` full copy, `in` O(n) vs map O(1), fast int pow); everything desugars to existing primitives.*

## 7. 落地档拆分 / Landing items (p.9.13)

* p.9.13.1 单箭头统一 + `=>` 移除与存量迁移（grep 清零）
* p.9.13.2 基元前置：机制 + 首批清单 + 遮蔽验证
* p.9.13.3 运算符批：`in`/`not in`、`+` 扩展、`**`/`//`/`%%`
* p.9.13.4 箭头续扩批：块管道/进容器·字段·解构/接基元·运算符/条件管道/临时函数/反解构
* p.9.13.5 并行数据流图：图内核 + 波次 SDF 执行 + 安全护栏 + 探针
* p.9.13.6 文档/示例/迁移说明（含匹配示例改写）

*EN: p.9.13.1 single-arrow unification + `=>` migration; p.9.13.2 primitive prelude; p.9.13.3 operator batch; p.9.13.4 arrow extensions; p.9.13.5 parallel dataflow graph (wave SDF + safety guards); p.9.13.6 docs/examples/migration notes.*

## 8. 验收总则 / General acceptance

* 每子项：正/负例探针矩阵 + 迁移 grep 清零 + 既有代码零回归；
* 编译器：自举两阶段不动点（SHA 记录、tiec.exe 提升）+ 回归基线不劣化（test-diagcodes FAILS=7 · regress-s21 159P/6F/2S · regress-m5 8P/0F）。

*EN: per-item probe matrices + migration grep-zero + zero regression; self-host fixed point + unchanged regression baselines.*