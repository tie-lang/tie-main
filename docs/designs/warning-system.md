# 设计定稿：警告系统独立与性能优化
*EN: Design Finalization: Warning System Independency & Performance Optimization*

> 状态：**设计定稿**（2026-09-17 讨论对齐）
> 关联里程碑：**p.9.14 警告系统独立与性能优化**（复用腾出号——原 p.9.14「tie 模组开发一等
> 支持/自动 JVM.NET 后端」已从 ROAD 删除，本工作接其号）。
> 主线四项：①**独立警告 pass**（编译期非阻塞、可裁剪、逐条开关）②**结构化警告事件、去
> `;W:` 文本往返**（性能主因）③**tdiag 收束**（目录/标号 W#####/归一化/渲染移至独立诊断面，
> 对齐 p.9.0.1 tdiag 与 tieapi 统一诊断契约）④**编译期独立检测**（--no-warn 全关、清单化）。
> 设计基线：2026-09-17 现场核读 `tiec` 警告发射链——`semantic.tie` `sm_warn_add`
> （semantic/sinfer/scheck 内联发射）、OK 协议 `;W:l c msg` 文本组装、`driver.print_warns`
> 文本再解析、`diagcode.render_warning` 二次归一化 + 渲染。

> EN: Status: **Design finalized** (2026-09-17 discussion alignment). Milestone **p.9.14 —
> warning system independency & performance optimization** (reusing the vacated number; the
> former p.9.14 "tie modding / managed JVM-.NET backends" tier was removed from ROAD). Four
> lines: ①independent warning pass (compile-time, non-blocking, prunable, per-warning switch)
> ②structured warning events — remove the `;W:` text round-trip (the perf driver) ③fold into
> **tdiag** (catalog / W##### codes / normalization / rendering move to the independent
> diagnostics surface, aligned with p.9.0.1 tdiag & the tieapi unified diagnostic contract)
> ④compile-time independent detection (`--no-warn` full off, cataloged). Baseline: read of the
> tiec warning chain — `sm_warn_add` (inline in semantic/sinfer/scheck), `;W:` OK-protocol text
> assembly, `driver.print_warns` text re-parse, `diagcode.render_warning` re-normalize + render.

---

## 一、现状与性能画像

- **内联发射在热路径**：`sm_warn_add(line,col,msg)` 散落在语义/类型推断（sinfer/scheck/
  semantic）检查点（W00001–29），每次编译都跑全部警告检查；**零警告文件也照付分析成本**。
- **双文本往返**：semantic 把警告序列化进 OK 协议 `;W:l c msg`（string `+` 拼接）→
  `print_warns` find/strsub 再解析 → `diagcode.render_warning` 对每条**二次 `normalize()`**
  + `+` 重建字符串。双重文本成本 + 每条重复归一化。
- **目录/渲染嵌 tiec 前端**（diagcode.tie）：警告目录、标号、归一化、渲染都在编译器内，
  未独立成可裁剪面；配套仓 tdiag 仅承载文档（warnings.md），代码面未独立。

> 定位裁决：性能主因=警告以文本协议把检测、序列化、解析、二次归一化串成低效链路，且检测
> 内联进每次编译热路径。**一源三治**：去文本往返、拆独立非阻塞 pass、目录/渲染收束诊断面。

---

## 二、目标与定界

- **提速**：消除 `;W:` 文本往返与重复归一化；零警告/不启用场景不再付全量检查成本。
- **独立**：警告检出为编译期非阻塞独立 pass，可裁剪、逐条开关；目录/标号/渲染归独立诊断面
  tdiag（对齐统一诊断契约）。
- **不纳入**（接口预留）：运行期/动态防御警告（需数据探针，另期）；改变警告码/语义
  （W##### 目录不变，仅结构/载体变）。

---

## 三、方案总览

一源三治，三线并进：

1. **结构化警告事件、去文本往返**：警告改为 `(code,line,col,params)` 结构化事件直接发，
   删 `;W:` 序列化→解析→二次归一化；渲染仅在输出端一次。顺带让 tsp（p.9.16）免于解析
   `;W:` 文本。
2. **独立警告 pass**：从语义/类型推断热路径解耦成独立可裁剪 pass，`--no-warn` 全关、
   目录清单逐条开关；零警告文件不付全量检查。
3. **tdiag 收束**：警告目录、标号 W#####、归一化、渲染移至独立诊断面 tdiag（p.9.0.1），
   对齐 tieapi 统一诊断契约；tiec 对诊断面只发结构化事件。

---

## 四、详细设计

### 4.1 结构化警告事件（去文本往返）

- 警告载体从 OK 协议 `;W:` 文本改为**结构化事件**：`(code W#####, line, col, params)`，
  语义/类型推断直接产代码（`warn_reg` 已分配 W#####），不在 OK 串拼文本、不经 `;W:`
  再解析。
- 渲染只发生在**输出端一次**（CLI 终端格式 / IDE JSON）；每条事件只用一次归一化/查表，
  不再跨 `print_warns→render_warning` 二次 normalize。
- 消费方：CLI、IDE（vscode-tie）、tsp（p.9.16，n 免解析 `;W:` 文本）。

### 4.2 独立警告 pass（非阻塞、可裁剪）

- 警告检从语义/类型推断内联点解耦为**独立 pass**：对类型化 AST/语义结果做一次横切扫描，
  收集结构化警告事件；不掺入主编译流、可整体跳过。
- 开关：`--no-warn` 全关（保留）；目录清单**逐条开关**（每 W##### 可独立禁用，配置文件
  /CLI）；零警告或全部禁用时该 pass 不运行，零额外成本。
- 与 p.9.16 `release_ast()` 衔接：pass 依赖类型化 AST 生命周期，用完随 AST 释放。

### 4.3 tdiag 收束（独立诊断面）

- 警告**目录/标号/归一化/渲染**从 tiec 前端 `diagcode.tie` 迁至独立诊断面 **tdiag**
  （p.9.0.1 tdiag + 配套仓），tiec 只按其接口发结构化事件。
- 对齐 **tieapi 统一诊断契约**（2026-09-12 生态定稿：统一错误模型诊断码）：诊断码
  （E#####/W#####）为语言无关契约，独立组件（CLI/IDE/tdiag 工具）可自行实现消费。
- 保留 W##### 五位纯序号目录与 warnings.md（换入 tdiag 侧）。

### 4.4 检测时机与可配置性

- **编译期非阻塞独立 pass**（现状检测时机不变，仅解耦为非阻塞独立步骤）。
- 逐条开关由目录清单驱动（默认全开）；`--no-warn` 整体关闭；配置面默认保守，不改变无参
  行为。

### 4.5 CLI 与配置

| 项 | 取值 | 说明 |
|----|------|------|
| `--no-warn` | 已存在 | 整体关闭警告（保留） |
| `warn.<W#####>` | 新增（每警告开关） | 目录清单逐条启用/禁用 |
| 警告事件 | 结构化 `(code,line,col,params)` | 替代 `;W:` 文本协议 |
| tdiag | p.9.0.1 | 目录/标号/归一化/渲染收束面 |

---

## 五、排号与分期

**档位：p.9.14 警告系统独立与性能优化（复用原模组腾出号）**

- p.9.14.1 **结构化警告事件 + 去文本往返**：警告改 `(code,line,col,params)` 直接发，删
  `;W:` 序列化→解析→二次归一化；渲染移输出端一次；tsp（p.9.16）改消费结构化事件。
- p.9.14.2 **独立警告 pass**：从语义/类型推断热路径解耦为独立非阻塞 pass；`--no-warn`
  全关、目录清单逐条开关；零警告不付全量检查成本。
- p.9.14.3 **tdiag 收束**：警告目录/标号/归一化/渲染迁独立诊断面 tdiag（p.9.0.1），对齐
  tieapi 统一诊断契约；tiec 仅发结构化事件。
- p.9.14.4 **验收与回归**：警告逐字节等价门禁（新结构与既有渲染逐条一致）+ warnings.md
  同步 + s21/diagcodes/m5 回归不劣化 + 脚本一律 `.tsh.tie`。

> 分期顺序原则：先去性能主因（.1 结构化）→ 解耦热路径（.2 独立 pass）→ 收束诊断面（.3
> tdiag）→ 总验收（.4）。依赖 p.9.16 tsp 结构化消费对齐；与其他档无前置冲突、可并线。

---

## 六、验收度量

- **性能**：含/不含警告的编译前端耗时下降（`;W:` 文本往返与重复归一化消除后）；零警告/
  全禁用场景零额外检查成本。
- **等价**：警告渲染结果与改造前进逐字节恒等（硬门禁）；W##### 目录与 warnings.md 一致。
- **独立**：独立 pass 可整体跳过、逐条开关；tdiag 独立实现可消费同一契约。
- **回归**：tiec 全套 s21/diagcodes/m5 不劣化；探针/冒烟全绿；脚本 `.tsh.tie`。

---

## 七、兼容性与迁移

- 警告 **代码/语义不变**（W##### 目录同量同义），仅结构/载体变化；对外 CLI 文本格式不变
  （渲染层输出等价）。
- `;W:` 协议为内部载体，删除后仅影响内部调用方（driver/tsp），统一迁移到结构化事件。
- 新配置默认保守（每警告默认开、--no-warn 语义保留），无参行为不劣化。

---

*本设计为警告系统独立与性能优化的权威执行依据（tie-main 侧），配套 tdiag 收束与 tieapi
统一诊断契约；随 p.9.14 警告系统档执行（原 p.9.14 模组档已删）。*