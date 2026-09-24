# p.9.17/9.18 主体完成档执行提示词 —— 装配收口 + 面 A 低内存 + 面 B 嵌入 / Execution Prompt

> 交接自 p.9.17-18 合并档首批（2026-09-24，基线核验 + 前置收尾三件 + p.9.17.1
> 中期已落地）。执行者无需读任何历史对话——本文件自包含。先读本文 +
> `tiec/docs/p9216-findings.md`（**§7-§10 为本批新发现：确定性口径、装配勘
> 察、str_char 缓存设计/坑/回滚全记录**）+ 两份设计定稿：
> `docs/designs/interp-performance.md`、`docs/designs/embedded-interpreter.md`。
> 所有 commit 一律英文。
>
> 执行顺序 = 本文各节先后：装配收口 → str_char 收口 → 拆箱+值池 → 直驱 →
> 面 B → 双面接口 → JIT → 合并验收。

## 0. 开工前基线核验（不做完不许动代码）

* 固定点直核：`compiler\tiec.exe` 应为 SHA256
  **6e836504c0d60e1208b5e56af8c413cbfd2990016929aa9d586ecc437310b6be**。
  不符 → 先查 git log，禁止盲目重编。
* 自举配方：**bootstrap-fp.tsh.tie 必须双参数调用**：
  `tsh_main.exe -f scripts\bootstrap-fp.tsh.tie ..\_tiec_verify\fp_check fresh`
  → FIXED-POINT OK（脚本内打印哈希现已可信，仍须产物 certutil 直核）。
* 回归基线：`regress-s21` → **PASS=158 FAIL=7 SKIP=2**（157→158 为 p.9.3.9
  语句序修复后的良性基线变更；7 项 FAIL 集合跨三版 tiec 稳定：generics /
  proc_createprocessw_pipe / std_httpc_probe / std_net_bytes / std_net_text /
  std_sse_probe / table_struct_elem，均为网络/FFI/泛型类已知项）。
* 库自检（全 exit 0）：`tieir_test` / `passes_test` / `ir_test` / `lex_test`
  （用 `compiler\tiec.exe <test.tie> --no-warn -o <exe>` 编译运行）。
* trm 探针：`tiec --tieir-out` 编译 `trm\tests\s3pure\tiecabi.tie`（**配源是
  tiecabi.tie，pure.tie 无 sub/mul**）→ `run_tiec.exe <.tir>` → add/sub/mul
  全 PASS。
* 三仓分支：tiec `p.7` ≥ **050c8c9**；tie-main `p.7` ≥ 本文件提交；
  trm `main` ≥ f6b0e20。

## 1. 铁律（每条都有一票否决权）

1. **自举门控 + 连锁陷阱**：编译语义/上限/诊断类改动 → 落改动 → 三阶自举 →
   升格 n3 → 回归 FAIL/SKIP 集合一致 → 才算完成。**新陷阱（本批实测）**：
   bootstrap [2/4] 写 driver 片段 → [3/4] 全命中触发**装配路径**——改动
   irgen/llvmgen 后必须验证三阶链闭环，仅测单次编译不够。
2. **工具链纯 tie**：scripts/tools 只允许 tie/tshell，100% 禁止 .py/.sh/.ps1
   入库。单文件 ≤800 行、单函数 ≤300 行。一次性分析脚本放仓外
   `_tiec_verify`（不入库）。
3. **事实验证（本批最大教训）**：动手前先跑基准拿数字——prompt/设计文档的
   性能数字可能过时或半对半错（str_char 的 360µs 数字与实测半符；span 段
   「恒空」结论有半错）。基准脚本已就绪：`_tiec_verify/bench_50k.tie`（50K
   码点 char-wise）、`bench_mb.tie`（多字节）、`bench_tsh3.tie`（interp）。
4. **推送**：`git push origin <branch>` 静默失败——用
   `git push https://$(gh auth token)@github.com/<owner>/<repo>.git
   HEAD:refs/heads/<branch>`（token 只留内存，输出脱敏）。tie 工具链推
   org `tie-lang`。
5. **tsh 语义已修复（p.9.3.9，tiec cfde2de）**：语句序根因（split_top var
   提升）已除，sleep workaround **全删且禁再加**——再遇脚本时序玄学，先怀疑
   语句顺序与状态污染，不是 exec 异步/缓存。
6. **确定性门禁（口径已修，findings §7/§8.2）**：exe 层链接器非确定（同 -o
   两次编译哈希不同，既有现象）——产物对比在 **.tir 层**做；装配路径口径 =
   段 2/4/6/7 逐字节 + 段 5 大小一致 + **dump_text 语义对比 IDENTICAL**
   （池 id 为进程内句柄，池序不可恢复；探针工具 `_tiec_verify/tir_dump.tie`）。
7. **IR 内联渲染纪律（本批实测沉淀，写 irgen 内联前必读）**：store 必须
   **三操作数** [ty IMM, 值, 地址]；kind 3 全局直引**不可走 tig_p2i**（硬编码
   kind 0 渲染 %N）——手写 op24 ptrtoint + kind 3 操作数；cond_br 必须
   [cond, true, false] 全三操作数；**块创建序必须 = 控制流逻辑序**（llvmgen
   按块表序输出，值 id 回退 → opt numbering 错）；**依赖感知缓存会吞掉
   backend 源改动**——调试期一律 --no-cache 重编验证。
8. 半成品不 commit（str_char 中期回滚先例：调试中断 → findings 记录 + 工作
   树回滚）；每完成一项 commit；回归红着不许推。

## 2. 背景与现状（本批已落地的地基，执行者必读）

* **p.9.21.8 池过滤 + 模块缓存默认开**（tiec 5e93660）：write_mod_slice 引用
  收集式池压缩 + deserialize 池重映射（全量池主单元恒等）；写放大
  72.9s→44.4s（片段写增量 -68%）。TIEC_MODCACHE 门控已摘。
* **p.9.3.9 tsh 语句序根因**（tiec cfde2de）：split_top 曾把顶层 var 提升到
  定义段先于 main 体求值——四缺陷皆其表象；sleep 全删。
* **p.9.21.9 装配器核心**（tiec 2f0ee14 + 护栏 050c8c9）：`middle/tieir_asm.tie`
  ——片段解析（段 3/5）+ **g_extra_tops 序驱动重放**（值/块/指令 id 与
  ops_off/params_off 由创建序自然复现；**片段拼接序不成立**，g_extra_tops =
  源码级交错序）；kpass_irgen 全命中判跳 irgen+passes；MODASM h/n；llvmgen
  置位恢复（sso/wsock/catch 白名单引用检测）。**遗留：全局 var 登记族未恢复
  ——护栏**：asm_build_order 对含顶层 VarDecl（tag 100）单元返回空 order →
  诚实降级全量（driver 自举 [3/4] 即此场景）。
* **p.9.17.1 中期**（回滚，findings §10/§10.1）：str_char 缓存 helper 方案
  **已验证可行**（@tie_sc_off 手写 LLVM：phi 自环重建循环 + legacy 兜底；
  trace/acc/多字节全对；50K 遍历 9.2s→0.27s）；遗留两 bug 已定位：
  **phi 差一**（sc.rd 应存循环体 %nk 而非退出时 phi %k）与**交替串失效**
  （单槽缓存 + 非遍历调用场景，需最小复现后定多槽或调用点豁免）。
* **勘误清单**：write_mod_slice 段 7 span = 全 0 冗余（真实产物 span 恒空）；
  prompt 旧文「const_str 的 kind=2」应为 kind 0 + opcode 62/51/35/36/41；
  func_ret/param_ty 是类型 id 非池 id。
* 缓存目录 `%USERPROFILE%\.tiec-cache\mods`；探针工程 `tests/_modcache_probe`
  （菱形 d1→d2/d3→d4，**含 VarDecl 时装配被护栏拦截**）。

## 3. 装配收口（p.9.21.9 完成，先行）

**全局 var 登记族恢复**——摘除护栏的前置：
* 勘察 `irgen.tie tig_global_var`（driver 树顶层 VarDecl 登记路径）与
  `llvmgen.global_table_reg/global_scalar_reg/global_scalar_init/call_sym_reg/
  vtable_reg/tbl_inlined_check` 的调用点，列登记数据清单（哪些可从 AST
  g_extra_tops tag 100 + 语义层状态重放、哪些须片段头携带）。
* 首选：driver 装配路径**重放登记**（AST 仍在、语义层已跑；与
  asm_build_order 同源遍历）——避免改片段格式。llvmgen 置位恢复的既有范式
  （asm_flag_*）是模板。
* 验收：含 VarDecl 的探针工程（自建，含表全局 + 标量全局 + 命名空间 const）
  装配路径 exe 编译运行与全量一致（stdout 逐字节）+ 摘除护栏 + 三阶自举
  （[3/4] 装配触发且通过 = 门禁）+ regress 158/7/2。
* 跨片段常量折叠风险预案照 ROAD：片段头依赖段记被折叠常量来源模块、装配
  判脏（允许过度失效）。

## 4. str_char 收口（p.9.17.1 完成）

* **修 phi 差一**：sc.rd 的 `@tie_sc_n` 应存循环体 `%nk`（已写项数）而非退出
  时 phi `%k`——循环体尾部 store 或等价重排。**修交替串**：先最小复现
  （两串交替调用 str_char 的独立探针），再定方案（建议：**双槽**——按
  addr%2 选槽，零 LRU 成本覆盖交替对；或命中判定加 len 快速预筛）。
* 重上路径：回滚 diff 在 findings §10 + git 历史（050c8c9^ 的 irgen_bi_num/
  llvmgen/llvmgen_str/llvmgen_inst_p1 工作树版本可从本日会话重写——**设计
  已验证，勿改架构**：helper 手写体 + irgen call 3 块）。
* 验收：bench_50k 前后（9.2s→0.27s 基线保持）+ bench_mb 多字节一致 +
  逐字符 trace IDENTICAL + **交替串探针全对** + regress 158/7/2 + 三阶自举
  （str_char 改动触发连锁陷阱——护栏已护 VarDecl 单元，仍须全链验证）+
  不动点重录。
* **str_sub 同范式**：勘察其 irgen 实现（定位复用缓存表）；容器按值传参的
  COW/移动语义**仅出勘察结论**（设计增补节），不强行实施。

## 5. 拆箱标量 + 值池（p.9.17.2，兼任 p.9.18.1）

* `compiler/interp/value.tie`（~635 行 per-value 10 表 push/寻址）重构：
  int/float/bool/trit/char 拆箱（tagged union 或 NaN-boxing，选定后写设计
  文档增补节）；值池/常量池复用与字符串 intern；会话内存只增不减治理。
* 铁律 7 的渲染纪律在此不适用（纯 interp 层），但**确定性硬门禁**适用：
  REPL/DAP/脚本行为逐字节恒等。
* 验收：interp micro-benchmark 前/后（bench_tsh3 已就绪）+ 内存峰值/稳态
  对比报告 + regress。
* 注意 findings「解释器/tshell 性能优化裁定」段：tsh 语义已修（p.9.3.9），
  该前置已解除。

## 6. 树遍历直驱（p.9.17.3，兼任 p.9.18.2）

* `exec_stmt`/`gen_expr` 直分派 switch + 解码直驱（消灭每节点字符串比较/
  查表），作 JIT 冷路径基线。
* 验收：interp bench 前/后 + 确定性门禁（同输入输出逐字节恒等）。

## 7. 面 B：trm tieir-interp 嵌入面（p.9.18.3）

* D2 已通直线纯函数；补齐 `br/cond_br/switch`（控制流）、`call` 族（调用图
  +参数传递）、表/字符串原语（与 p.9.17.1 原语实现对齐）；聚合/struct 形态
  勘察；`trm-embedded` 静态子集裁剪清单；Backend 接口与统一对象身份/GC 按
  `docs/designs/trm-final-design.md`（p.7.3）对齐——**接口先行，GC 可后置**。
* trm 仓独立 commit/push（main 分支）。
* 验收：`trm/tests/s3pure` 扩展——源码 → tiec → .tir → trm interp 跑通含
  控制流/调用/字符串的探针工程；与面 A 同输入逐字节恒等。

## 8. 双面统一接口（p.9.18.4）

* 面 A / 面 B 同接口热切换（Backend 接口收敛）；trm（p.9.5.3）与 WASM
  （p.9.6.2）嵌入面接入评估——**接口就位即算，实现可顺延**（如实写 ROAD）。

## 9. 分级 JIT（p.9.17.4，宿主可选上层，独立于嵌入）

* AST → LLVM IR → native 动态加载（复用 tiec 后端）；函数级 JIT 缓存挂钩
  p.9.15 编译缓存；冷热阈值可配（小输入不走 clang 子进程）。p.9.15.2
  （强哈希/原子写）建议先行或同批。
* 验收：JIT 与解释器同输入逐字节恒等；冷/热路径性能报告；REPL/DAP 等价。
* 允许按边界顺延（如实写 ROAD）——DoD 第 1 条仅要求面 B 探针绿。

## 10. 合并验收（p.9.17.5 + p.9.18.5）

* 性能基准报告（各节前/后数据汇总入 `docs/designs/interp-performance.md`
  增补节）+ 体积/内存对比报告（面 A/面 B）+ 确定性门禁全量重跑（**.tir/dump
  口径**）+ 回归不劣化（基线 158/7/2）+ 自举不动点复核。
* ROAD：p.9.17.1-5 与 p.9.18.1-5 按对应关系勾选（拆箱/直驱两边同步）；
  p.9.21.9 与 p.9.3.9 状态如实（已完成项勿重复勾）。

## 11. 提交与推送纪律

* 一个小任务一次提交；tiec/tie-main 分支 `p.7`，trm `main`；推送用 gh token
  拼 URL（铁律 4）。
* 每完成一项：先 commit 再继续下一项；回归红着不许推。
* 记忆纪律：每完成一项把（条目号/commit sha/交付物/结论）追加进工作记忆，
  双语。

## 12. 完成定义（Definition of Done）

1. 装配收口（护栏摘除 + 含 VarDecl 工程闭环）+ str_char 收口（bench 前后 +
   交替串全对）+ 拆箱 + 直驱硬验收全过（必须）；面 B 至少控制流+调用+字符串
   探针绿；双面接口/JIT 允许按边界顺延（如实写 ROAD）。
2. tiec 不动点已重录并升格，regress 集合一致（基线 158/7/2 或如实登记的
   新基线）；tshell 改动独立验证。
3. ROAD（tie-main）p.9.17/p.9.18 状态如实；findings 反映最终状态。
4. 三仓全部推送 GitHub，工作树干净（探针产物不入库）。
5. 最终报告：结构化表格（条目/commit/验收结果/性能数据/遗留），交给用户做
   go/no-go。
