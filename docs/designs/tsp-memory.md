# 设计定稿：tsp 内存优化（LSP 服务器三线内存工程）
*EN: Design Finalization: tsp Memory Optimization (Three-line LSP Memory Engineering)*

> 状态：**设计定稿**（2026-09-17 讨论对齐）
> 关联里程碑：**p.9.16 编译器与 LSP 内存工程**（tsp 内存优化 + 前端 AST 生命周期）。
> 主线：**三线全做**——①**按需 lazy + AST 释放** ②**状态去冗余** ③**常驻生命周期治理（LRU）**；
> 前端静态表 `s_*`/`intern` 的 AST 释放接口由 **tiec/frontend 侧**引入。
> 设计基线：2026-09-17 现场核读 `tsp` 仓（`analyze.tie` 的三重复状态表 + `server.tie`
> 主循环 + 前端 `s_*` 静态列式表常驻）。tsp 为 tie 写的 LSP 服务器，`tie --lsp` 启动，
> 后端诊断复用编译器前端（`parser.parse_ast` + `semantic.check_ast`）。

> EN: Status: **Design finalized** (2026-09-17 discussion alignment). Milestone **p.9.16 —
> compiler & LSP memory engineering** (tsp memory optimization + frontend AST lifecycle).
> Three lines, all in scope: ①**lazy evaluation + AST release** ②**state de-duplication**
> ③**resident lifecycle governance (LRU)**. The frontend static-table `s_*`/`intern` AST
> release interface is introduced from the **tiec/frontend side**. Baseline: read of the
> `tsp` repo on 2026-09-17.

---

## 一、现状与内存画像

tsp 每打开文档保留全套状态，且每次编辑全量重跑编译管线：

1. **每次 `didChange` 全量重跑整条编译管线**：`an.analyze` → `parser.parse_ast(整文档)`
   + `semantic.check_ast` 全量重建；引用/语义令牌方法又经 `run_check` 再跑一遍。
   **每次按键都物化整棵前端 AST**（`s_*` 列式静态表 + `intern` 池），峰值高、CPU 亦浪费。
2. **每个文档同时持有 5+ 份冗余状态**：全文 `g_txts` + 诊断 JSON 缓存 `g_diag_json` +
   符号索引 `g_i*`（每符号一条签名串）+ import 图 `g_dep` + server 侧**重复**的
   `g_sym_names/g_sym_sigs`（`rebuild_syms` 行扫描又建一份）。同文件文本/签名被复制多份。
3. **前端静态表 `s_*`/`intern` 常驻"最后分析文档"的完整 AST**：跨请求不释放，占住最大
   文件整棵树；`didChange` 后被新树替换，仍保留替换峰值。
4. **字符串值语义**：`substr_at`/`str_sub`/`+` 拼接制造大量 transient 拷贝（代码多处已
   自述改为字节级规避 O(n²)）。
5. **无内存预算/闲置回收**：文档一打开即常驻全套；仅 `didClose` 才 `drop_doc`（重建表
   释放）。长驻会话随打开文档数线性增长。

> 定位裁决：CPU 与内存同源（全量重解析）。**一源三治**：抓随时物化 AST 的根，去冗余，
> 定常驻回收边界。

---

## 二、目标与定界

- **降峰值**：把"编辑→全树物化"改为按需 lazy，重型能力用完即释放 AST。
- **降稳态**：去重复状态 + 常驻上限 + 闲置文档 LRU 回收。
- **不纳入**（接口预留）：
  * 单符号/AST 内部细粒度增量解析（tie 前端为整文档 AST，不做节点级增量；用"按需 + 缓存"
    取代）。
  * 后台线程/异步诊断（tsp 当前单线程同步，本期不引入并发，避免与 p.9.15 并行交织）。
  * 改变 LSP 协议语义/诊断行为（只改内存持有与求值时机）。

---

## 三、方案总览

一源三治，三线并进：

1. **按需 lazy + AST 释放**：诊断走现有指纹缓存（文本未变即复用）；引用/语义令牌/大纲等
   "重型 AST 能力"改为按需跑完整管线、**用后调前端释放接口**；`didChange` 可选防抖合并。
2. **状态去冗余**：剔除 server 侧重复符号索引，诊断懒构建，符号段与签名串瘦身。
3. **常驻生命周期（LRU）**：分析后释放 AST，常驻仅留文档索引+诊断；闲置文档 LRU 回收
   全文/索引；内存/文档数上限可配置。

---

## 四、详细设计

### 4.1 前端 AST 生命周期接口（tiec/frontend 侧）

- 目标：让调用方（tsp）在"不再需要 AST"时显式释放前端静态表。
- 实现：frontend 暴露**重置接口** `release_ast()`（语义上把 `s_tags/s_names/s_children/
  s_coff/s_nchild/s_aux/s_lines/s_cols` 列式表与 `intern` 池回退到空始态），供 LSP 在
  lazy 分析用后调用；与 p.9.15（缓存/并行）共用"单次分析生命周期"概念。
- 约定：`release_ast()` 后先前 `s_*` 句柄全部失效；tsp 只保存脱离 `s_*` 的
  平面索引/诊断，不保存句柄。接口以 tiec 编译产物能力交付（纯 tie，无运行时新增）。

### 4.2 按需 lazy 求值

- **诊断路径**：保留现有文件级指纹缓存（`g_diag_fps/g_diag_json/g_diag_ok`）；
  文本未变即返回缓存，不动 `s_*`。
- **重型能力（references/semanticTokens/inlayHints/outline 等）**：改为按需调用
  `run_check`（跑一次完整管线）→ 立即产出 → **调用 `release_ast()` 释放**，不保留整树；
  仅把结果（符号索引/令牌 JSON）存入脱离 `s_*` 的持久表。
- **didChange 高频**：可选合并/防抖（同一定时间窗内的连续变更合成一次重析），降低
  AST 物化频率；默认值保守（文本未变必跳，防抖为可配置开关）。

### 4.3 状态去冗余

- 剔除 server 侧 `g_sym_names/g_sym_sigs/g_sym_uris`（`rebuild_syms`）重复索引——
  hover/outline 改复用 analyze 的 `g_i*`（同域唯一真相），删一份签名副本。
- 诊断 JSON 懒构建：仅在有符诊断/需推送时构建字符串，缓存按需淘汰（配合 LRU）。
- 符号段/签名串瘦身：不持有重复前缀、按文档段惰性拼接。

### 4.4 常驻生命周期（LRU）

- **AST**：lazy 分析后立即释放（见 4.2），常驻不存整树。
- **文档**：闲置文档（长时间无请求/未激活）按 LRU 回收，回收粒度可配（仅丢 AST →
  丢全文 → 丢诊断索引）；命中后冷启动按需重建。
- **上限**：新增配置 `tsp.max_open_docs`（文档数）与 `tsp.mem_budget`（内存预算，软
  指标），达限自动按 LRU 关闭最旧；默认值保守，不改变无参启动行为。

### 4.5 CLI 与配置

| 项 | 取值 | 说明 |
|----|------|------|
| `tsp.lazy` | 新增默认 `on` | 按需 lazy 求值开关 |
| `tsp.debounce_ms` | 新增（0=关） | didChange 重析合并窗口 |
| `tsp.max_open_docs` | 新增 0=不限 | 文档数上限（LRU 关最旧） |
| `tsp.mem_budget` | 新增 0=不限 | 内存预算软上限 |
| AST 释放 | tiec 侧 `release_ast()` | 前端静态表重置接口 |

---

## 五、排号与分期

**档位：p.9.16 编译器与 LSP 内存工程（tsp 内存优化 + 前端 AST 生命周期）**

- p.9.16.1 **tiec 前端 AST 释放接口**：`release_ast()` 重置 `s_*` 列式表与 `intern` 池；
  纯 tie、零新增运行时；供 tsp 用后释放。
- p.9.16.2 **tsp 按需 lazy 求值**：诊断指纹缓存保留；引用/语义令牌/大纲按需跑完整管线 +
  用后调 `release_ast()`；didChange 防抖合并（默认文本未变即跳）。
- p.9.16.3 **tsp 状态去冗余**：去 server 重复符号索引、诊断懒构建、符号段/签名瘦身。
- p.9.16.4 **tsp 常驻生命周期（LRU）**：闲置文档 LRU 回收（AST→全文→索引粒度可配）+
  `tsp.max_open_docs/mem_budget` 上限。
- p.9.16.5 **验收与回归**：内存峰值/稳态对比报告（前/后）+ `lsp_smoke*.py` 探针全绿 +
  编辑/引用/语义令牌功能等价 + 脚本一律 `.tsh.tie` + 回归不劣化。

> 分期顺序原则：先"释放能力"（.1 提供给 tiec）→ 再"少跑"（.2 lazy）→ "少存"（.3 去冗余）
> → "可回收"（.4 LRU）→ 总验收（.5）。依赖 tiec 侧能力先行，与 p.9.15（缓存/并行）无
> 前置冲突、可并线。

---

## 六、验收度量

- **峰值**：编辑大型文件时保留 AST 的峰值内存下降（对比报告）。
- **稳态**：多文档长驻会话内存不再线性激增（LRU + 去冗余生效）。
- **功能等价**：诊断/引用/语义令牌/大纲/跳转结果与改造前逐项一致（`lsp_smoke*.py` 全绿）。
- **CPU 辅助收益**：防抖/lazy 后高频编辑不再全量物化 AST（报告，不作硬指标）。
- **回归**：tsp 与 tiec 既有探针/冒烟不劣化；脚本 `.tsh.tie`。

---

## 七、兼容性与迁移

- `release_ast()` 为新增接口，缺省 caller 不调用即无影响，不影响既有编译器单次编译路径。
- 新增配置默认值保守（lazy 开、debounce 0、上限 0=不限），无参启动行为不变。
- `analyze`/`analyze_doc`/`run_check` 对外签名不变；仅在调用侧决定是否 lazy/释放。

---

*本设计为 tsp 内存优化的权威执行依据（tie-main 侧），配套 tiec 前端 AST 释放接口；
转让入 p.9.16 编译器与 LSP 内存工程档。*