# tie p.6.9 LSP 重写（tsp 落地：0-Rust 收官）

* 日期 / Date：2026-09-03

* 状态 / Status：规划已对齐，待执行（Aligned with user, pending execution）

* 基线 / Baseline：p.6.8 验收后（2026.1 内；LSP 与 Skia 相互独立，顺序可调）

* 依据 / Basis：`docs/plans/tsp-lsp.md`（tsp 全量设计定稿：R1 tie 重写 + 16 项能力 +
  增量分析 + 语义高亮 + tieconsole 复用 + LSP 用 JSON 协议）、`docs/plans/roadmap.md`
  （S3.4 LSP 重写）。

* 实现约束 / Implementation constraint：本模块全部工作**用 tie 语言完成**
  （服务端、协议层、分析引擎、探针、验收）；VSCode 客户端（TypeScript）为既有
  资产仅接线不改写。EN: All work in this module is done **in tie** (server, protocol
  layer, analysis engine, probes, acceptance); the VSCode client (TypeScript) is an
  existing asset, wired only, not rewritten.

***

## 1. 定位 / Positioning

p.6.9 落地 **tsp**——tie 语言服务器（Language Server），把自举链最后的 Rust
残留（Rust tie-lsp 已归档）替换为 **tie 重写 + 全量增强**（tsp-lsp.md 定稿）：
诊断/补全/hover/跳转/引用/重命名/签名/语义高亮/文档符号/工作区符号/折叠/格式化/
代码操作等 **16 项能力** + 增量分析 + 语义高亮 + tieconsole 复用。

EN: p.6.9 lands **tsp** — the tie Language Server, replacing the last Rust leftover in
the bootstrapping chain (the archived Rust tie-lsp) with a **tie rewrite + full
enhancement** (finalized in tsp-lsp.md): **16 capabilities** (diagnostics/completion/
hover/definition/references/rename/signatureHelp/semanticTokens/documentSymbol/
workspaceSymbol/foldingRange/formatting/codeAction, ...) + incremental analysis +
semantic highlighting + tieconsole reuse.

**核心优势（复用编译器前端）**：tsp 直接 import compiler/frontend（lexer/parser/
semantic 全 tie 写），分析引擎与编译器**同一份代码**——编辑器诊断 = 编译错误（永不
漂移），补全/跳转基于真实符号表。这是 0-Rust 自举链的收官（tiec/interp/trm 已 tie
化，LSP 是最后一块）。

EN: **Core advantage (compiler-frontend reuse)**: tsp imports compiler/frontend
directly (lexer/parser/semantic all in tie), so the analysis engine and the compiler
are **the same code** — editor diagnostics = compile errors (never drifting);
completion/jump are based on the real symbol table. This concludes the 0-Rust
bootstrapping chain (tiec/interp/trm already tie-ified; LSP is the last piece).

***

## 2. 策略校准 / Strategy Calibration

对编译器前端、std IO、LSP 协议面深挖得到四个事实，修正了「直接开写 16 能力」的
直觉设想：

EN: A deep dive into the compiler frontend, std IO, and the LSP protocol surface
yields four facts that correct the intuition "just write all 16 capabilities":

* **事实一：编译器 frontend 已 tie 化且可直接复用**。compiler/frontend
  （lexer/parser/semantic）+ compiler/middle/ir_meta.tie 的 sym_table（符号表：函数/
  struct/命名空间 + 签名 + 可见性 + **line/col 声明位置**）齐备 → tsp 直接 import，
  无需重复实现分析器；range/span 精度由 sym_table 提供。
  EN: **Fact 1: the compiler frontend is tie-ified and directly reusable.**
  compiler/frontend (lexer/parser/semantic) + compiler/middle/ir_meta.tie's sym_table
  (symbols: functions/structs/namespaces + signatures + visibility + **line/col
  declaration positions**) are ready → tsp imports them directly; no analyzer
  reimplementation; range/span precision comes from sym_table.

* **事实二：tie 无字节级 stdin/stdout 原语（关键前置缺口）**。std/fs 只有文件级
  read_bytes/read_lines；tink 的帧协议明确「IO 边界由调用方/桥负责」→ LSP 服务端
  （JSON-RPC over stdio）必须先补 `std/stdio` 字节原语（read/write/read_line + 缓冲），
  这是 p.6.9 的第一块砖。
  EN: **Fact 2: tie has no byte-level stdin/stdout primitive (a critical prerequisite
  gap).** std/fs only has file-level read_bytes/read_lines; tink's frame protocol
  explicitly says "IO boundaries are the caller's/bridge's job" → the LSP server
  (JSON-RPC over stdio) must first add a `std/stdio` byte primitive
  (read/write/read_line + buffering) — p.6.9's first brick.

* **事实三：std/json 已有** → LSP 的 JSON-RPC 编解码（消息帧 + 方法载荷）直接复用
  std/json，无需新写序列化器。
  EN: **Fact 3: std/json exists** → LSP's JSON-RPC codec (message frames + method
  payloads) reuses std/json directly; no new serializer.

* **事实四：LSP 异步请求 vs tie 并发模型 M4 未落地** → v1 顺序处理 + 增量缓存补偿
  （tsp-lsp.md §10.1 已定）。请求量大时的流畅度由「文件级缓存 + 反向依赖索引」保证，
  不依赖协程。
  EN: **Fact 4: LSP async requests vs the un-landed M4 concurrency model** → v1 does
  sequential processing + incremental-cache compensation (per tsp-lsp.md §10.1).
  Smoothness under load comes from "file-level cache + reverse-dependency index", not
  coroutines.

***

## 3. 目标与范围 / Goals and Scope

1. **stdio 前置**：`std/stdio` 字节原语（stdin/stdout 读写 + 行读 + 缓冲），
   LSP 与 tink 桥共用。
   EN: **stdio prerequisite**: `std/stdio` byte primitive (stdin/stdout read-write +
   line read + buffering), shared by LSP and the tink bridge.

2. **协议层**：JSON-RPC over stdio（Content-Length 帧 + 编解码，复用 std/json）；
   消息类型 Initialize/Initialized/Shutdown/Exit + textDocument/*。
   EN: **protocol layer**: JSON-RPC over stdio (Content-Length framing + codec, reusing
   std/json); message types Initialize/Initialized/Shutdown/Exit + textDocument/*.

3. **分析引擎**：analyze（文档 → 编译流水线）+ index（sym_table + import 图正/反向）
   + diagnostics（semantic 错误 + 增量文件级缓存）。
   EN: **analysis engine**: analyze (doc → compile pipeline) + index (sym_table +
   forward/reverse import graph) + diagnostics (semantic errors + incremental
   file-level cache).

4. **16 项能力全量**：completion/hover/definition/references/rename/signatureHelp/
   semanticTokens/documentSymbol/workspaceSymbol/foldingRange/formatting/codeAction/
   documentHighlight + didOpen/didChange 同步。
   EN: **all 16 capabilities**: completion/hover/definition/references/rename/
   signatureHelp/semanticTokens/documentSymbol/workspaceSymbol/foldingRange/formatting/
   codeAction/documentHighlight + didOpen/didChange sync.

5. **服务端与集成**：server 主循环（stdio 循环 + 请求分发 + 增量补偿）；`tie --lsp`
   入口保留；VSCode 客户端接线；tieconsole 库模式 API（补全/高亮复用点）。

**非目标 / Non-goals**：工作区全量索引（按需加载，import 可达才建）、codeLens
（后置可选）、LSP 请求协程化（M4 后）、tieconsole 客户端本体（属 S4.4，本模块
只出库模式 API 面）、格式化与 prep 转换器的统一化（先做格式化功能，统一化后置）。

***

## 4. p.6.9 子项盘子 / Sub-item Plan

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.9.1 | `std/stdio` 字节原语：stdin/stdout 字节级 read/write + read_line + 缓冲；与 std/fs 对称；LSP 与 tink 桥共用 / std/stdio byte primitive: stdin/stdout byte read/write + read_line + buffering; symmetric with std/fs; shared by LSP and the tink bridge | 回显探针（stdin 字节 → stdout 字节逐字节一致）；read_line 探针 / Echo probe (stdin bytes → stdout bytes byte-identical); read_line probe |
| p.6.9.2 | protocol.tie：JSON-RPC over stdio（Content-Length 帧 + 编解码，复用 std/json）；消息类型 Initialize/Initialized/Shutdown/Exit + textDocument/* / protocol.tie: JSON-RPC over stdio (Content-Length framing + codec, reusing std/json); message types Initialize/... + textDocument/* | 与 vscode-languageclient 握手（initialize 往返）；py 客户端回环 / Handshake with vscode-languageclient (initialize round-trip); py client loopback |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.9.3 | analyze.tie：文档 → 编译流水线（lex/parse/semantic）→ AST + 符号 + 诊断；单文件错误隔离（坏文档不崩服务）/ analyze.tie: doc → compile pipeline (lex/parse/semantic) → AST + symbols + diagnostics; per-file error isolation (bad doc never crashes the server) | 错误文档返回诊断不崩溃；正常文档符号齐备 / Broken doc yields diagnostics without crash; healthy doc yields full symbols |
| p.6.9.4 | index.tie：复用 ir_meta sym_table + import 图（正/反向）；工作区按需加载（打开文件 + import 可达）/ index.tie: reuse ir_meta sym_table + import graph (forward/reverse); on-demand workspace loading (open files + import-reachable) | 跨文件符号索引正确；import 变更级联正确 / Cross-file index correct; import-change cascade correct |
| p.6.9.5 | diagnostics.tie：semantic 错误 → LSP 诊断（range 映射）+ 增量（文件级缓存，import 变更才级联）/ diagnostics.tie: semantic errors → LSP diagnostics (range mapping) + incremental (file-level cache; cascade only on import change) | 增量编辑诊断正确；缓存命中无重复分析 / Incremental-edit diagnostics correct; cache hit without re-analysis |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.9.6 | completion.tie + hover.tie：符号表补全（关键字/符号/参数/泛型实参）+ 文档注释 hover / completion.tie + hover.tie: symbol-table completion (keywords/symbols/params/generic args) + doc-comment hover | 补全/hover 探针（含 "." 触发）PASS / Completion/hover probes (incl. "." trigger) PASS |
| p.6.9.7 | definition.tie + reference.tie：跳转定义（跨文件，import 图）+ 引用查找（反向索引）/ definition.tie + reference.tie: go-to-definition (cross-file via import graph) + references (reverse index) | 跨文件跳转/引用探针 PASS / Cross-file definition/reference probes PASS |
| p.6.9.8 | signature.tie + symbol.tie：签名帮助（参数提示，复用签名元数据）+ 文档/工作区符号（大纲，复用 AST）/ signature.tie + symbol.tie: signatureHelp (param hints, reusing signature metadata) + document/workspace symbols (outline, reusing AST) | 签名/大纲探针 PASS / Signature/outline probes PASS |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.9.9 | semantic_tokens.tie + folding.tie：语义令牌（映射 VSCode 标准类型 keyword/type/variable/function/...）+ 折叠范围（AST 块结构）/ semantic_tokens.tie + folding.tie: semantic tokens (mapped to VSCode standard types) + folding ranges (AST block structure) | 语义令牌/折叠探针 PASS / Semantic-token/folding probes PASS |
| p.6.9.10 | rename.tie + documentHighlight + quickfix：跨文件重命名（import 图）+ 符号出现高亮 + 修复建议（缺分号/未定义变量）/ rename.tie + documentHighlight + quickfix: cross-file rename + occurrence highlight + fix suggestions (missing semicolon/undefined variable) | 重命名/高亮/修复探针 PASS / Rename/highlight/fix probes PASS |
| p.6.9.11 | format.tie：格式化（对齐 prep/indent 转换器思路）/ format.tie: formatting (following the prep/indent converter approach) | 格式化前后一致探针 PASS / Format round-trip probe PASS |

| 子项 / Item | 内容 / Content | 验收 / Acceptance |
| ----------- | -------------- | ----------------- |
| p.6.9.12 | server.tie：服务端主循环（stdio 循环 + 请求分发 + 增量缓存补偿）+ 生命周期（initialize/shutdown/exit）；`tie --lsp` 入口保留 / server.tie: server main loop (stdio loop + request dispatch + incremental-cache compensation) + lifecycle; `tie --lsp` entry kept | initialize/shutdown 往返；错误请求不崩 / initialize/shutdown round-trip; bad requests never crash |
| p.6.9.13 | VSCode 客户端接线：现有 TS 客户端（vscode-languageclient）指向 tsp；16 项能力矩阵联调 / VSCode client wiring: existing TS client points to tsp; 16-capability matrix integration test | 编辑器实测：诊断/补全/跳转/引用/重命名/语义高亮全通 / Editor-verified: diagnostics/completion/definition/references/rename/semantic highlighting all work |
| p.6.9.14 | 验收与发布：大项目（编译器自身 8 模块）编辑流畅 + 16 能力矩阵 + 零回归 + preview.5 收尾（README/CHANGELOG/双语文档/已知限制）/ Acceptance & release: smooth editing on a large project (the 8-module compiler itself) + 16-capability matrix + zero regression + preview.5 wrap-up | 全 PASS、exit 0、编辑不卡顿 / All PASS, exit 0, lag-free editing |

***

## 5. 依赖主线 / Dependency Line

p.6.9.1-6.9.2（stdio + 协议）→ p.6.9.3-6.9.5（分析引擎）→ p.6.9.6-6.9.8（核心交互）→
p.6.9.9-6.9.11（增强）→ p.6.9.12-6.9.14（集成验收）。p.6.9.3-6.9.5 内部 analyze →
index → diagnostics 串行；p.6.9.6-6.9.11 内部子项可并行（共享 index 基础，各能力
独立探针）；p.6.9.12-6.9.14 依赖前四全部。

EN: p.6.9.1-6.9.2 (stdio + protocol) → p.6.9.3-6.9.5 (analysis engine) →
p.6.9.6-6.9.8 (core interaction) → p.6.9.9-6.9.11 (enhancement) →
p.6.9.12-6.9.14 (integration/acceptance). Within p.6.9.3-6.9.5, analyze → index →
diagnostics are serial; p.6.9.6-6.9.11 items proceed in parallel (they share the index
base, each capability has independent probes); p.6.9.12-6.9.14 depends on all previous.

***

## 6. 风险与对策 / Risks & Mitigations

* **stdio 原语是新的 CRT 桥（编译器/运行时面）**：stdin 缓冲/读多字节易踩坑 →
  复用 std/fs read_bytes 的桥模式 + 回显/行读探针先行；读空/EOF 语义文档化。
  EN: the stdio primitive is a new CRT bridge (compiler/runtime surface) → reuse the
  std/fs read_bytes bridge pattern + echo/read_line probes first; EOF/empty-read
  semantics documented.

* **增量分析（import 级联）复杂**：全量级联会卡顿 → 文件级缓存起步，import 变更
  才级联；级联范围 = 反向依赖闭包。
  EN: incremental analysis (import cascade) is complex → file-level cache first;
  cascade only on import change; cascade scope = the reverse-dependency closure.

* **大文档解析慢**：编辑器首开大文件 → 单文件快路径 + 符号/诊断缓存；语义高亮按
  需段生成（v1 整文档可接受，缓存兜底）。
  EN: slow parsing of large docs → per-file fast path + symbol/diagnostic cache;
  semantic tokens generated on demand (whole-doc acceptable in v1, cache backs it).

* **span/range 精度不足**：LSP 需要精确位置 → 依赖 sym_table 的 line/col；不足处
  由 analyze 补充 AST 节点位置映射（folding/semanticTokens 用）。
  EN: insufficient span/range precision → rely on sym_table line/col; analyze fills
  AST-node position mapping where needed (for folding/semanticTokens).

* **16 能力面大**：一次全做完易失焦 → 按能力逐项独立探针，每项可独立交付；
  核心 8 项（诊断/补全/hover/跳转/引用/签名/符号/同步）优先，增强 8 项随后。
  EN: the 16-capability surface is broad → per-capability independent probes, each
  deliverable alone; the core 8 (diagnostics/completion/hover/definition/references/
  signature/symbols/sync) first, the enhanced 8 after.

* **vscode-languageclient 兼容**：协议细节（进度/取消）易漏 → 以官方 client 实测
  为验收标准，py 客户端回环先过协议层。
  EN: vscode-languageclient compatibility → official-client live testing as the
  acceptance standard; py-client loopback validates the protocol layer first.

***

## 7. 相关文档 / Related Documents

* `docs/plans/tsp-lsp.md`（设计定稿：R1 路线 / 16 能力 / 增量 / tieconsole 复用 /
  JSON 协议 / 决策记录——本模块的执行依据 / design final: R1 route / 16 capabilities /
  incremental / tieconsole reuse / JSON protocol / decision log — the basis of this
  module)

* `docs/plans/roadmap.md`（S3.4 LSP 重写 / S4.4 tieconsole）

* `docs/plans/tieconsole.md`（库模式 API 消费方 / library-mode API consumer）

* 落地仓库 / Landing repo：`tie-main/`（compiler/lsp/ 目录，命名空间 tsp；
  std/stdio.tie 入 std）

***

## 8. 决策记录 / Decision Log

| 决策点 / Point | 结论 / Conclusion | 备选（未选）/ Alternatives |
| -------------- | ----------------- | -------------------------- |
| 重写路线 | **R1：tie 重写**（0-Rust 收官，编译器前端直接复用）——沿用 tsp-lsp.md | Rust 保留增强 |
| 命名 | **tsp**（compiler/lsp/，namespace tsp）——沿用 | tlsp、tie-lsp |
| 增强范围 | **全量 16 项** + 增量 + 语义高亮——沿用 | 子集 |
| 增量分析 | 第一版做（文件级缓存 + 反向依赖级联）——沿用 | 后置 |
| 协议 | **LSP 标准 JSON**（Content-Length 帧，复用 std/json）——沿用 | zd |
| stdio 前置 | **新增 std/stdio 字节原语**（本模块 p.6.9.1 补齐，LSP/tink 共用） | 桥外置、文件暂存 |
| 并发 | v1 顺序处理 + 增量缓存补偿；M4 后协程化——沿用 | 协程 v1 |
| tieconsole 复用 | 出**库模式 API**（completion/semantic_tokens 纯函数面）；客户端本体属 S4.4 | 独立实现 |
| 能力优先级 | 核心 8 项先行，增强 8 项随后（同一 p.6.9 内） | 一次全做 |
