# tiu 绘制 API 库实施计划 —— 无遗留闭环
*EN: tiu Drawing API Implementation Plan — closed-loop, no leftovers*

**日期** / Date: 2026-09-12 · **类型** / Type: 实施计划（任务分解 + 契约定稿；交付可执行清单，不含挂起项）
**依据** / Basis: `docs/designs/tiu-drawing-api.md` v0.2（§9 模块路线、§10 范围归属）· `docs/designs/tiu-render-engine.md`（§4 绘制表 IR、§7 预编译组合、§9 资源）
**关联** / Related: `docs/designs/tiu-ui-widgets.md`（UI 层按本计划 §2 协议对接）· `docs/designs/tiu-event-system.md`（事件轴，不输入本库）
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Turns the API-library module roadmap (drawing-api §9) into an
> executed task list with zero open tails. Every cross-layer dependency is
> **frozen in this plan** (§2), not negotiated mid-implementation. The API shape
> follows tie's current grammar and requests no new language features (§3). Any
> item the design doc calls "later work / separate doc / pending" is either
> closed here as a concrete deliverable or assigned to an owner document that
> already exists. The repo itself is created up front (task Z1, TPL 2.0 per org
> convention). Acceptance is per-task probes plus an end-to-end gold IR /
> golden-frame integration gate (TP1–TP3). Execution order is top-to-bottom;
> each task ships one commit.

---

## 1. 任务清单 / Task List

执行顺序自上而下；**每个任务一个提交**（英文 message）；每模块完成即自验证（探针全绿）。

### 零任务：开仓（前置，不推后）
* **Z1 创建 `tie-lang/tiu` 独立仓**：`LICENSE`（TPL 2.0 标准全文）+ `README.md`（## License 链接 + 定位）+ `.gitignore`（惯例），经 `gh repo create tie-lang/tiu --public --source . --push`（工作流作用域令牌已在账）
* Z2 `docs/designs/tiu-drawing-api.md` v0.2 与本文档置入仓内 `docs/` 收拢（从 tie-main 复制，tie-main 侧保留原件）

### 模块一：对象模型
* **T1.1** 图元 / Path / Paint / Layer 数据记录定义（值语义、不可变）；record 字段对齐引擎 §4（op/key/geo/paint/clip/meta）
* **T1.2** Paint 效果栈默认范围闭合并落表：实色 / 线性、径向、扫描渐变 / 图像平铺 / 透明度 / 颜色矩阵 / 模糊 / 阴影 / 标准混合集（src-over 等）；超集组合不登记——由引擎 §7 降级拆分承载（不设"扩展清单"）
* **T1.3** 不可变构建 + 结构共享；单测：不变性 / 共享 / 别名安全
* **验收门**：T1.1–T1.3 探针全绿（gold record、结构共享断言）

### 模块二：IR 编码器
* **T2.1** record 字节布局终稿（对齐引擎 §4；本任务产出即**冻结**，修订只走版本表回写）
* **T2.2** 稳定 key 派生算法：`op · geo-hash · paint-hash · 变换分级`（视图级/逐项级），指纹用 TSHA 族（复用 tie 密码学底座）
* **T2.3** 增量段协议定稿：子树 key 前缀 + dirty rect 段（UI 层唯一差分原语；本任务产出即**冻结**，UI 库模块四按此对接）
* **T2.4** gold IR 比较器 + 变化区隔离探针（key 稳定性）
* **验收门**：gold IR 匹配；隔离探针——改一处其余段字节不变

### 模块三：双模式入口与会话
* **T3.1** `Canvas` 会话（窗口 / 离屏 / 图像三种目标；分辨率/DPI/色彩空间，色彩空间固定引擎工作空间）
* **T3.2** `record / submit / replay` + immediate 合成（submit 即所有权转移）；重放引用路径
* **T3.3** 双模式等价探针：immediate 图像 == retained 重放图像
* **验收门**：T3.1–T3.3 全绿

### 模块四：文本排版
* **T4.1** 字体句柄与度量（引用计数）
* **T4.2** 排版：行高 / 对齐 / 换行 → 布局输出记录进 IR（字形形状交由引擎 GPU 化，本库不生成字形位图）
* **T4.3** gold 排版断言（同输入同布局输出）
* **验收门**：gold 排版 + 句柄生命周期断言

### 模块五：资源句柄与缓存
* **T5.1** `Image / Font` 句柄、引用计数、失效诊断（可检查结果 + 诊断标号）
* **T5.2** 引擎资源接口契约定稿（acquire / retain / release / handoff 与引擎 §9 预算、LRU 的交互点；本任务产出即**冻结**）
* **T5.3** 跨线程探针：worker 并发构建 IR 与串行一致（无数据竞争）
* **验收门**：句柄生命周期 + 并发一致性

### 终点验收（全部模块完成后统一门禁）
* **TP1** 集成：一段绘制代码 → gold IR 字节匹配（§8 基准）
* **TP2** 与引擎「模块一」联调：绘制表 → 软件光栅 → 帧缓冲，gold 图 ≤1/255 容差（引擎 §12 同基准）
* **TP3** 文档回写：实现结论若有对象模型修订 → 更新设计文档版本表（维护义务，非挂起项）

---

## 2. 跨层契约定稿（当场冻结，实现期不谈判） / Frozen Contracts

| 契约 | 范围 | 冻结于 | 修订通道 |
|---|---|---|---|
| IR/wire | record 布局 + key 算法（对齐引擎 §4）| T2.1 / T2.2 | 版本表回写，需双方（引擎/API）同意 |
| 增量段协议 | 子树 key 前缀 + dirty rect 段（UI 层消费）| T2.3 | 同上（含 UI 库确认）|
| 资源句柄接口 | acquire/retain/release/handoff（引擎 §9 交互）| T5.2 | 同上（含引擎确认）|
| 事件通道 | 不经本库（事件走 tiu-event-system.md）| 本文档即定 | 不适用 |

> EN: Four contracts frozen in this plan: IR wire format + key algorithm
> (T2.1/T2.2), incremental-segment protocol (T2.3), resource-handle interface
> (T5.2), and the event channel which explicitly bypasses the API library.
> Revisions go through the version-table workflow with both sides consenting —
> never negotiated mid-implementation.

---

## 3. 语法约定 / Grammar Convention

* API 形态按 **tie 现行语法（p.7 状态）** 写作（样例见设计文档 §4）；本库**不主张任何新语言特性**
* 实现期若遇歧义：由 tie 既有语法规则裁决（优先级：tiec 现行实现 > tie 语法文档），**不产生新决策、不借道本库开口子**
* 若发现 tie 能力缺口（如不可变共享结构惯用法）→ 属 tie 语言/标准库演进轨道（另有规划文件，不复述），本库以 tie 现有能力（表值语义 + 结构化共享）落地，不阻塞

---

## 4. 无遗留清单 / No-leftover Checklist

下列事项在本计划内**当场闭合**，不发生：

* 不设"后期优化 / 另行规划 / 待定稿"挂起项——效果栈超集走引擎降级拆分（T1.2），语法按 §3，契约按 §2 冻结
* 契约不在实现中途再谈判——冻结表（§2）为唯一通道，修订走版本表回写
* 仓库与许可不推后——Z1 为第一个执行任务
* 与引擎/UI 的对接不"并行协商"——以冻结契约对接（T2.3 / T5.2 产出）
* 无限循环风险：每任务单提交、可回退；终点验收 TP1–TP3 有明确通过定义

## 5. 验收门禁汇总 / Gate Summary

* 每任务：该任务探针绿（黄金 IR / 断言），单提交
* 每模块：模块内任务全绿 = 模块完成
* 终点：TP1–TP3 全绿 = 本计划完成（**API 库实施闭环**）；TP2 联调只消费引擎「模块一」（引擎 §13 路线首个模块，既定先决条件）已交付能力，本计划不依赖引擎后续任何模块