# 设计定稿：嵌入式解释器（低内存执行面，双面并立）
*EN: Design Finalization: Embedded Interpreter (Low-RAM Execution Surface, Dual-Face)*

> 状态：**设计定稿**（2026-09-17 讨论对齐）
> 关联里程碑：**p.9.18 嵌入式解释器**（独立档；与 p.9.17 解释器 JIT 分开）。行动基线：
> **JIT 太重**（外部 clang/LLVM 工具链 + 动态加载 + 编译缓存 + 内存/体积开销），不适合
> 嵌入式；**老解释器保留为嵌入门面的一等交付**。研读 `docs/designs/trm-final-design.md`
> （2026.2 p.7.3 修订）：trm 已改为「引擎层执行 tieir 字节码 + interp 前端为语义基准 +
> 可替换后端(ORC-JIT/wasm/AOT) + 引擎级统一 GC + `trm-embedded` 静态子集 + 无 LLVM 退
> 纯 interp」，j以对齐嵌入式接入。
> 交付：**双面并立**——面 A=老解释器（源码级 AST 树遍历，服务 REPL/脚本/DAP，零外部）；
> 面 B=trm tieir-interp 嵌入式执行面（tieir 紧凑表示 + Backend 接口 + 统一对象身份/GC，
> `trm-embedded`）。低内存攻坚：拆箱标量 + 值池/常量池复用 + 紧凑表示。验收：**兼顾**
> （确定性门禁 + 体积/内存报告 + 性能参考）。

> EN: Status: **Design finalized** (2026-09-17 discussion alignment). Milestone **p.9.18 —
> embedded interpreter** (independent tier; separate from p.9.17 JIT). Rationale: JIT is too
> heavy (external clang/LLVM toolchain + dynamic loading + compile cache + memory/footprint
> cost) for embedded; the legacy interpreter is kept as a first-class embedded surface.
> Studied `docs/designs/trm-final-design.md` (2026.2 p.7.3 revision): trm is now engine-layer
> tieir-bytecode execution + interp front-end as the semantic baseline + replaceable backends
> (ORC-JIT/wasm/AOT) + engine-level unified GC + `trm-embedded` static subset + no-LLVM
> falls back to pure interp. Deliverable: **dual-face** — Face A = legacy interpreter
> (source-level AST tree-walk, REPL/script/DAP, zero external); Face B = trm tieir-interp
> embedded surface (tieir compact representation + Backend interface + unified object
> identity/GC, `trm-embedded`).

---

## 一、背景与定位

- **嵌入约束**：低 RAM、小体积、零外部工具链（无 clang/LLVM/动态加载）、低首调延迟、
  确定性。JIT（外部 clang + 动态加载 + 编译缓存）与这些约束冲突。
- **老解释器保留**：`compiler/interp` 源码级 AST 树遍历解释器，服务 REPL/tshell、DAP
  单步、崩溃诊断 —— 零外部、确定、可裁剪，天然适配嵌入。
- **trm 新架构**（p.7.3 修订）：引擎层执行 tieir 字节码；**interp 前端为跨端语义基准**；
  后端接口可替换（ORC-JIT 默认热点 | wasm/AOT | 移动临时）；**interp 也实现 Backend 接口、
  可热切换**；GC 独立成层、interp/JIT 共堆统一对象身份；无 LLVM 退纯 interp；分发含
  `trm-embedded` 静态子集。
- **决策**：双面并立。面 A（AST 级老解释器）这是以零外部为硬约束的咀嚼嵌入；面 B
  （trm tieir-interp）对接 trm 引擎的嵌入面，本期同时落地。

---

## 二、目标与定界

- **低内存**：拆箱标量 + 值池/常量池复用 + 紧凑表示。
- **双面**：面 A（AST 级，REPL/脚本/DAP）与面 B（tieir-interp，trm 嵌入手）均为一等交付，
  同接口可切换。
- **兼顾验收**：确定性硬门禁 + 体积/内存对比报告 + 性能参考。
- **不纳入**（接口预留）：单符号/AST 细粒度增量解析；线程内并发求值（并行随 p.9.15）；
  与 p.9.17 JIT 的合并（本期分开，JIT 为社会可选上层）。

---

## 三、方案总览

- **低内存三件**：拆箱标量（int/float/bool/trit/char 直接值）+ 值池/常量池复用 + 紧凑
  表示（面 B=tieir 字节码；面 A 以池化/直驱削减）。
- **双面并立、统一接口**：面 A 与面 B 各自执行面，暴露同一执行接口，可热切换；接入
  trm/WASM 嵌入面。
- **共用基建**：字符串/容器原语优先优化（p.9.17.1 全局线）供两面共享。

---

## 四、详细设计

### 4.1 低内存共同手段

- **拆箱标量**：标量直接值，不做 per-value 10 表 push/寻址；容器/字符串仍盒装。
- **值池/常量池复用**：值节点池与常量池按需复用（避免会话内只增不减），字符串去重
  intern；消除长会话负面缓存局部性。
- **紧凑表示**：面 A=池化 AST/窄节点；面 B=tieir 字节码（本就紧凑）。

### 4.2 面 A：老解释器（AST 级，REPL/脚本/DAP）

- 保留源码级 AST 树遍历入口（eval/eval_script/eval_call 签名不变）。
- 叠加：拆箱标量 + 值池/常量池复用 + `exec_stmt`/`gen_expr` 直分派 switch + 解码直驱 +
  字节级字符串规避（复用 p.9.17.1 原语）。
- 硬约束：**零外部依赖、确定性**（同输入结果与现状逐字节恒等）。

### 4.3 面 B：trm tieir-interp 嵌入式执行面

- 执行 tieir 字节码，实现 trm 引擎 **Backend 接口**（`compile(module)->Executable`）与
  **统一对象身份/虚拟机 GC**（interp/JIT 共堆）；无 LLVM 环境即纯 interp。
- 覆盖 `trm-embedded` 静态子集：源码→tiec→tieir→interp 前端执行；压缩体积、低常驻。
- 语言/模板 p.9.16 `release_ast()` 边界：tieir 模块来自统一 AST 生命周期，用完释放。

### 4.4 双面统一接口 + 嵌入面接入

- 面 A / 面 B 暴露**同一执行接口**，宿主按场景选择/运行时热切换（对应对档 hot/cold）。
- 接入 **trm 嵌入（p.9.5.3，C ABI 宿主脚本化）** 与 **WASM（p.9.6.2，跨语言/浏览器）**
  嵌入面，作为嵌入式交付的一部分。

### 4.5 CLI 与配置

| 项 | 取值 | 说明 |
|----|------|------|
| `interp.embedded` | 新增默认 `on` | 嵌入模式（面 A 为主） |
| `interp.face` | 新增 `a`(AST)/`b`(tieir) | 选择执行面（可热切换） |
| `interp.unbox` | 新增默认 `on` | 拆箱标量开关 |
| `interp.pool` | 新增默认 `on` | 值池/常量池复用 |
| string 原语 | 复用 p.9.17.1 | 全局原语优化 |

---

## 五、排号与分期

**档位：p.9.18 嵌入式解释器（低内存执行面，双面并立）**

- p.9.18.1 **面 A 拆箱 + 值池/常量池复用**：老解释器标量拆箱、值池/常量池复用、字符串
  intern；消灭 per-value 10 表 push 与会话只增不减；零外部、确定性。
- p.9.18.2 **面 A 直驱 + 字节级规避**：`exec_stmt`/`gen_expr` 直分派 + 解码直驱 + 复用
  p.9.17.1 字符串原语；低延迟。
- p.9.18.3 **面 B trm tieir-interp 嵌入面**：tieir 紧凑表示 + Backend 接口 + 统一对象
  身份/GC + `trm-embedded` 静态子集；源码→tiec→tieir→interp 前端执行（衔接 p.7.3.2）。
- p.9.18.4 **双面统一接口 + trm/WASM 接入**：面 A/面 B 同接口热切换；接入 trm（p.9.5.3）
  与 WASM（p.9.6.2）嵌入面。
- p.9.18.5 **验收与回归**：兼顾——确定性门禁（两面同输入与现状逐字节恒等）+ 体积/内存
  对比报告 + 性能参考 + REPL/DAP/脚本等价 + 回归不劣化 + 脚本一律 `.tsh.tie`。

> 分期顺序原则：先面 A 低内存/性能（.1/.2）→ 面 B trm 嵌入面（.3）→ 双面统一+接入（.4）
> → 总验收（.5）。复用 p.9.17.1 字符串原语与 p.9.16 `release_ast()`；与 p.9.17（JIT）分开
> 独立排期，JIT 为宿主可选上层。

---

## 六、验收度量（兼顾）

- **确定性（硬）**：面 A/面 B 对同源输入结果与现状解释器**逐字节恒等**。
- **体积/内存（报告）**：嵌入式二进制体积、会话常驻内存相对现状下降（前/后对比）。
- **性能（参考）**：低延迟/吞吐相对现状基线（不作硬指标）。
- **功能**：REPL/脚本/DAP 行为等价；trm/WASM 嵌入面接入可用。
- **回归**：tiec 全套 s21/diagcodes/m5 不劣化；探针/冒烟全绿；脚本 `.tsh.tie`。

---

## 七、兼容性与迁移

- 面 A 保留现有 eval/eval_script/eval_call 签名，默认面 A，现有 REPL/脚本行为不变。
- 面 B 新增，不影响既有编译/解释路径；trm 面仅在 `import`/嵌入宿主显式启用。
- 与 p.9.17 JIT 保持独立：JIT 作为宿主具备工具链/空间时的可选上层，不牵动嵌入式约束。
- 拆箱/池复用/紧凑表示默认值保守，不劣化无参行为。

---

*本设计为嵌入式解释器（低内存执行面）的权威执行依据（tie-main 侧），配套 trm tieir-interp
嵌入面与 p.9.16 `release_ast()`；随 p.9.18 嵌入式解释器档执行。*