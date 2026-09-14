# tie 语言基元与运算符（设计 v0.2 / ROAD p.9.13）

*EN: tie language primitives & operators (design v0.2 / ROAD p.9.13)*

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

## 5. 并行数据流图（全新并行书写）/ Parallel dataflow graph (v0.2: graph as first-class value)

* **graph 新值类型**（v0.2 定案）：并行图是一等数据值——先构造、可存储/传递/组合，再执行。
  内部 = 节点表（fn 值）+ 边表（前向/分叉/汇合/回边记录）+ 入口/出口标记；以现成表/struct 表达，
  语言只做类型封装 + 检查（边类型一致性、回边有界性）。
* 图语法（图内运算符）：
  * 节点 = 模块（普通 tie 函数、或 `{ v -> expr }` 匿名单参块）；
  * **图值字面量** `{ A } - { B -> ~ A }`：花括号=节点模块，`-` 并行分叉，`~` 汇合/回边
    （`a -> ~ b`：a 的尽头汇回 b 作为其新一波输入；多入边节点自动 join = 所有入边到齐才放行）。
    **`=>` 不出现**（已随单箭头统一移除，§1），图入口即"执行"。
  * **执行** = 统一箭头送值 `x -> g`（图 = 可运行的数据流函数值，波次 SDF 语义见下）。
  * **组合**：`g1 - g2` 并行组合两图、`g1 -> g2` 串联、`~` 回边并入 g1 内表达式——都是值语义，返回新图。
* **执行模型（定案：波次 SDF）**：
  * 入口节点每吐一个值启动一波；回边把结果带回前节点作为下一波输入；
  * 收敛由「节点条件 + 入口流长度」自然决定（如 B 判定 ≥10 丢弃即该流线收敛）；入口排空 → 全图结束；
  * 用户无需写波次上限（无 `~(N)` 记法），有界性由输入流驱动；静态不可证处，运行期有界守护兜底。
* **图出口**：并行图表达式的值 = 各末端节点（无汇合时）末波结果组成的表；汇合点取 join 值。落地版再冻结细则。
* **安全默认（v0.2 加强：graph 默认不可变）**：
  * **graph 正常代码中不可被声明为可变/不可原地改结构**——只能整体替换（重新赋值新图值）或组合（运算符返回新图）；
  * **unsafe 内可声明可变 graph**，并配有"改变 graph 的强大语法"：unsafe 块内复用同一批运算符
    （`+ {..}` 追加节点、`- {..}` 追加分叉、`-> ~ b` 追加回边、结构化删除/改线原语）作**原地图变异**；
  * 节点捕获白名单：只许标量/不可变/按值拷贝；捕获共享可变表引用 → 编译期诊断；
  * 边 = 有界队列 + 背压（复用 `ch_send_block`）；join = 同步屏障；
  * 调度归 trm-lite work-stealing；与既有 actor/async/ppool/channel 是同一执行层，图只是其表达层。
* 落地范围：先最小内核（入口 → 分叉 → 前进 → 汇合/回边 → 出口），再扩展嵌套图/边类型。

*EN: v0.2 — parallel graph is a first-class `graph` value (constructed, storable/composable, then
executed). Literal `{ A } - { B -> ~ A }` (`-` fan-out, `~` join/back-edge; multi-in join waits
all inputs). Execution = unified-arrow value feed `x -> g` (graph = runnable dataflow function).
Composition (`g1 - g2`, `g1 -> g2`, `~ in g1`) are value semantics returning new graphs —
no graph entry `=>` anywhere (consistent with single-arrow unification). Execution = wave SDF
(entry emits a wave per input; back edge feeds next wave; convergence from node condition +
input stream length; drain ends; no explicit wave-count; runtime boundedness guard where static
proof impossible). Graph value = table of end-node wave results / join value. Safety-by-default:
**graph is immutable in safe code** — no mutable declaration, no in-place structural change
(only whole-value replacement or compositional new graphs); **inside unsafe, graph may be declared
mutable with the same operator set (`+`, `-`, `~`…) acting as in-place graph mutation ("powerful
graph-altering syntax")**; plus node capture whitelist (shared mutable table capture →
compile-time diagnostic), bounded backpressured edges (`ch_send_block`), join barriers, trm-lite
scheduling. Land minimal kernel first.*

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