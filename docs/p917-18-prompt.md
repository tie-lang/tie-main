# p.9.17 + p.9.18 执行提示词 —— 解释器性能 + 嵌入式解释器（合并档）/ Execution Prompt

> 交接自 p.9.21.6/p.9.21.7（2026-09-24 收官）。执行者无需读任何历史对话——
> 本文件自包含。先读本文 + `tiec/docs/p9216-findings.md`（上阶段发现与 tsh
> 语义实测备忘 §4）+ 两份设计定稿：`docs/designs/interp-performance.md`、
> `docs/designs/embedded-interpreter.md`。所有 commit 一律英文。
>
> **为什么合并**：p.9.17.2/9.17.3（拆箱/直驱）与 p.9.18.1/9.18.2（面 A 拆箱/
> 直驱）是**同一份工作**（同一个 tree-walking 解释器 `compiler/interp`），
> ROAD 已消重：拆箱/直驱唯一立项处在 p.9.17.2/9.17.3，p.9.18.1/9.18.2 只
> 承担面 A 附加交付（嵌入裁剪/内存报告）。p.9.21 收尾（p.9.21.8 池过滤、
> p.9.21.9 组装消费）与 tsh 语义修复（p.9.3.9）并入本阶段为**前置收尾**
> （tsh 就是面 A 的 REPL/脚本执行器，其语义修复属于面 A 一等工作）。
>
> **执行顺序** = 本文各节先后：前置收尾 → 字符串原语 → 拆箱+值池 → 直驱 →
> 面 B trm 嵌入面 → 双面统一接口 → 分级 JIT → 合并验收。

## 0. 开工前基线核验（不做完不许动代码）

* 固定点直核：`compiler\tiec.exe` 应为 SHA256 **7b7d8886bf15bdad608a3a631775cadf36f63a5320d04d3b70a9afdaa2d08dd1**（certutil）。不符 → 先查 git log，禁止盲目重编。
* 自举配方：**bootstrap-fp.tsh.tie 必须双参数调用**（tsh 单参数赋值静默失效缺陷，已加固但约定不变）：`tsh_main.exe -f scripts\bootstrap-fp.tsh.tie ..\_tiec_verify\fp_check fresh` → FIXED-POINT OK 且哈希 = 7b7d8886。
* 回归基线：`tsh_main.exe -f scripts\regress-s21.tsh.tie` → **PASS=157 FAIL=8 SKIP=2**（FAIL/SKIP 集合与基线一致才算绿）。
* 库自检（全 exit 0）：`tieir_test` / `passes_test` / `ir_test` / `lex_test`（基线 2026-09-24 重录）。trm：`trm\tests\s3pure\run_tiec.exe <任一 .tir>` → add/sub/mul 全 PASS。
* 三仓分支：tiec `p.7` ≥ deda0e5；tie-main `p.7` ≥ 本文提交；trm `main` ≥ f6b0e20。

## 1. 铁律（每条都有一票否决权）

1. **自举不动点门控**：编译语义/上限/诊断类改动 → 落改动 → 三阶自举 → 升格 n3 → 回归 FAIL/SKIP 集合一致 → 才算完成。纯测试/脚本/文档改动不需要自举。每步一次 commit。
2. **工具链纯 tie**：scripts/tools 只允许 tie/tshell，100% 禁止 .py/.sh/.ps1 入库。单文件 ≤800 行（gen 豁免）、单函数 ≤300 行。
3. **事实验证**：动手前先跑基准拿数字、写探针核实现状；一切「应为真」都要有可重跑的验收命令。
4. **推送**：`git push origin <branch>` 本环境静默失败——用 `git push https://$(gh auth token)@github.com/<owner>/<repo>.git HEAD:refs/heads/<branch>`（token 只留内存，输出脱敏）。tie 工具链推 org `tie-lang`。
5. **tsh 脚本必读**（findings §4 实测）：exec_code 异步返回；list_dir/file_read/file_exists 进程内路径缓存；exec_output 裸内部命令返回空；变量赋值同轮运行不稳定（resolve_out 每使用点现调范式）。这些正是 **p.9.3.9 要修的缺陷**——修好前的脚本沿用 workaround 范式。
6. **确定性硬门禁**：解释器/tsh/任何执行路径改动，同一输入输出与现状逐字节恒等（性能优化不许改变可观测行为）。

## 2. 背景与现状（已落地的地基，执行者必读）

* **p.9.21.6/7** 已落地：模块边界元数据（`g_file_base` + `sg_mod/gb_mod/st_mod` + `file_id_of_node`）；模块级 tieir 片段缓存（`middle/tieir_slice.tie` 的 `write_mod_slice` 重映射表版，键 = 源指纹+盐+t 档+目标，**默认关 `TIEC_MODCACHE=1`**，挂点 `kpass_irgen` 末尾）；`tieir.deserialize` 值空间重映射（D1）；trm loader v2 闸 + 重映射 + 布局自动探测 + `byte_read` 直读二进制 + interp `alloca/load/store`（D2）；扩展名 **`.tir`**；bootstrap-fp `resolve_out()` 加固（D4）。
* **p.9.15.1**（依赖感知缓存键）已落地；p.9.15.2-8 未动；p.9.16（AST 生命周期/tsp）未动——JIT 缓存与 `release_ast()` 挂钩点届时再接，不阻塞本阶段。
* **关键性能事实（ROAD 定位原文）**：`str_char` ~360µs/char（逐码点 O(n²)）、per-value 10 表 push、会话内存只增不减。编译器侧成功先例可复制：`lexer.run_lex` 字节遍历 `utf8_seq_len/utf8_char_at` 重构（零堆分配 + `g_byte_starts` 哨兵表）。
* **trm interp 指令覆盖现状**（D2 后）：ret/算术/neg/not/const_i/icmp/select/alloca/load/store；**缺 br/cond_br/switch/call 族/表与字符串原语**——只能跑直线纯函数，面 B 主缺口。
* 缓存目录 `%USERPROFILE%\.tiec-cache\mods\`；验收探针 `tests\_modcache_probe` + `scripts/verify-modcache.tsh.tie`。

## 3. 前置收尾（p.9.21 消费 + tsh 语义）

**第一件：片段池过滤 + 模块缓存默认开（ROAD p.9.21.8）**
* `tieir_slice.write_mod_slice` 引用收集式池压缩：被引用池 id 来自函数名/参数类型/块名、const_str 的 kind=2 操作数①、kind=3 全局名、符号表/导出/依赖行 → 池保序压缩 + 写入时同步重映射；摘掉 `pipeline.tie` 的 `TIEC_MODCACHE` 门控。
* 验收：①driver 自编基准（200+ 片段）回到 ≈27s（±10%）；②`verify-modcache.tsh.tie` 四步验收语义不变；③tieir_test 片段 roundtrip 用例补 const_str/全局名操作数覆盖后仍绿；④自举 + 升格 + 回归 157/8/2。

**第二件：tsh REPL 语义修复（ROAD p.9.3.9，tshell 仓）**
* 按其 ROAD 条目四点执行；**若变量赋值稳定性根因在求值器深层，允许降级**为文档化安全范式并如实登记，不许静默跳过。
* 验收：bootstrap-fp/regress 移除 workaround sleep 后全绿；tshell 仓独立 commit/push（tiec 三阶自举不受影响——tshell 不进 driver 编译单元）。

**第三件：片段组装消费（ROAD p.9.21.9）**
* 新增 `middle/tieir_asm.tie`：命中模块 .tir 片段 + 新建模块 irgen 产物，按 **g_extra_tops 展开序**装配（菱形导入下模块序 ≠ 函数表序；二级重映射：片段局部 → 全局，值空间按「参数前缀 + 各函数结果段」分配，与 D1 重建约定一致）。语义层保持全单元（成本保留），跳的是命中模块的 irgen。
* 硬门禁：装配路径产物与全量重编译**逐字节一致**（SHA256）；回归 157/8/2；`TIEC_INC=1` 打印 `MODASM h/n assembled`。
* 风险预案：跨片段值引用（跨模块常量折叠）不一致 → 片段头依赖段记「被折叠常量来源模块」、装配时判脏——允许过度失效，**不允许产物不一致**。

## 4. 字符串/容器原语（ROAD p.9.17.1，先行全局受益）

* 串对象附带码点索引/字节偏移缓存（复用 lexer `g_byte_starts` 哨兵表范式）：`str_char`/`str_sub` 单次解码 O(n) 后 O(1) 定位；拼接预留容量；容器按值传参的复制遍历评估写时复制/移动语义。
* 三处实现同步改且**行为逐字节一致**：编译路径内置（`bi_str_char` 等，irgen 内联）、解释器路径（`interp/call_builtin_seg*`）、tsh 路径。
* 验收：micro-benchmark（1KB 串 char-wise 遍历前/后）+ regress 不劣化 + 不动点重录。

## 5. 拆箱标量 + 值池/常量池（ROAD p.9.17.2，兼任 p.9.18.1）

* `compiler/interp/value.tie`（~635 行 per-value 多表 push/寻址）重构：int/float/bool/trit/char 拆箱（tagged union 或 NaN-boxing，选定后写设计文档增补节）；值池/常量池复用与字符串 intern；会话内存只增不减治理。
* 验收：解释器 micro-benchmark 前/后；REPL/DAP/脚本行为逐字节恒等；内存峰值/稳态对比报告。

## 6. 树遍历直驱（ROAD p.9.17.3，兼任 p.9.18.2）

* `exec_stmt`/`gen_expr` 直分派 switch + 解码直驱（消灭每节点字符串比较/查表），作 JIT 冷路径基线。
* 验收：bench 前/后对比 + 确定性门禁。

## 7. 面 B：trm tieir-interp 嵌入面（ROAD p.9.18.3）

* D2 已通直线纯函数；本节补齐：`br/cond_br/switch`（控制流）、`call` 族（调用图+参数传递）、表/字符串原语（与字符串原语实现对齐）、聚合/struct 形态勘察；`trm-embedded` 静态子集裁剪清单；Backend 接口与统一对象身份/GC 按 `docs/designs/trm-final-design.md`（p.7.3）对齐——**接口先行，GC 可后置**。
* 验收：源码 → tiec → .tir → trm interp 跑通含控制流/调用/字符串的探针工程（`trm/tests/s3pure` 扩展）；与面 A 同输入逐字节恒等。

## 8. 双面统一接口（ROAD p.9.18.4）

* 面 A / 面 B 同接口热切换（Backend 接口收敛）；trm（p.9.5.3）与 WASM（p.9.6.2）嵌入面接入评估——接口就位即算，实现可顺延。

## 9. 分级 JIT（ROAD p.9.17.4，宿主可选上层，独立于嵌入）

* AST → LLVM IR → native 动态加载（复用 tiec 后端）；函数级 JIT 缓存挂钩 p.9.15 编译缓存；冷热阈值可配（小输入不走 clang 子进程）。p.9.15.2（强哈希/原子写）建议先行或同批。
* 验收：JIT 与解释器同输入逐字节恒等；冷/热路径性能报告；REPL/DAP 等价。

## 10. 合并验收（ROAD p.9.17.5 + p.9.18.5）

* 性能基准报告（各节前/后数据汇总入 `docs/designs/interp-performance.md` 增补节）+ 体积/内存对比报告（面 A/面 B）+ 确定性门禁全量重跑 + 回归不劣化 + 自举不动点复核。
* ROAD：p.9.17.1-5 与 p.9.18.1-5 按本文对应关系勾选（拆箱/直驱两边同步）。

## 11. 提交与推送纪律

* 一个小任务一次提交；tiec/tie-main 分支 `p.7`，trm `main`；推送用 gh token 拼 URL（铁律 4）。
* 每完成一项：先 commit 再继续下一项；回归红着不许推。
* 记忆纪律：每完成一项把（条目号/commit sha/交付物/结论）追加进工作记忆，双语。

## 12. 完成定义（Definition of Done）

1. 前置收尾三件 + 字符串原语 + 拆箱 + 直驱 硬验收全过（必须）；面 B 至少控制流+调用+字符串探针绿；双面接口/JIT 允许按边界顺延（如实写 ROAD）。
2. tiec 不动点已重录并升格，regress 集合一致；tshell 改动独立验证。
3. ROAD（tie-main）p.9.17/p.9.18/p.9.21.8/9/p.9.3.9 状态如实；findings 文档反映最终状态。
4. 三仓全部推送 GitHub，工作树干净（探针产物不入库）。
5. 最终报告：结构化表格（条目/commit/验收结果/性能数据/遗留），交给用户做 go/no-go。
