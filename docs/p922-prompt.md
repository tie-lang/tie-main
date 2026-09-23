# p.9.22 执行提示词 —— 模块缓存消费 + tsh REPL 语义修复 / p.922 Execution Prompt

> 交接自 p.9.21.6/p.9.21.7（2026-09-24 收官）。执行者无需读任何历史对话——
> 本文件自包含。先读本文 + `tiec/docs/p9216-findings.md`（上阶段发现与 tsh
> 语义实测备忘 §4），再动手。所有 commit 一律英文。

## 0. 开工前基线核验（不做完不许动代码）

0.1 固定点核验：`compiler\tiec.exe` 现值应为 SHA256 **7b7d8886bf15bdad608a3a631775cadf36f63a5320d04d3b70a9afdaa2d08dd1**（certutil 直核）。不符 → 先查 git log 再继续，禁止盲目重编。
0.2 自举配方核验：**bootstrap-fp.tsh.tie 必须双参数调用**（tsh 单参数赋值有静默失效缺陷，已加固但约定不变）：
  `tsh_main.exe -f scripts\bootstrap-fp.tsh.tie ..\_tiec_verify\fp_check fresh` → 期望 FIXED-POINT OK 且打印哈希 = 7b7d8886。
0.3 回归基线核验：`tsh_main.exe -f scripts\regress-s21.tsh.tie` → 期望 **PASS=157 FAIL=8 SKIP=2**（FAIL/SKIP 集合与基线一致才算绿，不是只看数字）。
0.4 库自检核验（全 exit 0）：`tieir_test` / `passes_test` / `ir_test` / `lex_test`（lex_test 基线 2026-09-24 重录）。trm 侧：`trm\tests\s3pure\run_tiec.exe <任一 .tir>` → add/sub/mul 全 PASS。
0.5 三仓分支核验：tiec `p.7`、tie-main `p.7`、trm `main`，HEAD 分别 ≥ deda0e5 / 6489f85 / f6b0e20。

## 1. 背景与现状（已落地的地基）

* **p.9.21.6**（模块级增量编译证据层）已落地：模块边界元数据（`g_file_base` + `sg_mod/gb_mod/st_mod` + `file_id_of_node`）；模块级 tieir 片段缓存（`middle/tieir_slice.tie` 的 `write_mod_slice`，重映射表版，兼容菱形导入非连续布局；键 = 源指纹+盐+t 档+目标；**默认关，`TIEC_MODCACHE=1` 开**）；driver 挂点在 `kpass_irgen` 末尾（`cache_drv.mod_attribution_fill` + `mod_cache_update`）。
* **p.9.21.7**（D1-D4 闭环）已落地：`tieir.deserialize` 值空间重映射（文件=原交错序，重建=参数前缀序）；trm loader 同步重映射 + 布局自动探测 + `byte_read` 直读二进制 + interp `alloca/load/store`；扩展名 **`.tieir` → `.tir`**（格式名 tieir 不变，`--tieir-out` 旗标不变）；bootstrap-fp 取参加固（`resolve_out()` 每使用点现调）。
* 提速现状（driver 自举基准 -l2 -t0）：全量 26.8s；单元依赖缓存命中 15.1s（1.8×）；**模块片段目前只做证据（命中判定/ABI 形态），不跳任何编译工作**——本轮就是把它变成真消费。
* 缓存目录：`%USERPROFILE%\.tiec-cache\mods\`（片段 `<key>.tir`）；验收探针：`tests\_modcache_probe` + `scripts/verify-modcache.tsh.tie`（文件证据法；tsh 语义坑见 findings §4）。

## 2. 铁律（每条都有一票否决权）

1. **自举不动点门控**：任何编译语义/上限/诊断类改动 → 先落改动 → 三阶自举（`bootstrap-fp.tsh.tie <out> fresh`）→ 升格 n3 → `regress-s21` FAIL/SKIP 集合与基线一致 → 才算完成。纯测试/脚本/文档改动不需要自举。**每步一次 commit**。
2. **工具链纯 tie**：scripts/tools 只允许 tie/tshell（`type tie<tsh>` / `type tie<logic>`），100% 禁止 .py/.sh/.ps1 入库。单文件 ≤800 行（gen 豁免）、单函数 ≤300 行。
3. **事实验证**：动手前写探针核实现状，不靠 grep 推断；一切「应为真」都要有可重跑的验收命令。库自检沿用 `<lib>_test.tie` 范式（`check(ok, what)` + 失败 exit(1)，不定义本地常量，只 import 被测库链）。
4. **推送**：`git push origin <branch>` 在本环境静默失败（exit 128）——用 `git push https://$(gh auth token)@github.com/<owner>/<repo>.git HEAD:refs/heads/<branch>`（token 只留内存，输出落盘前脱敏）。tie 工具链推 org `tie-lang`。
5. **tsh 脚本必读**（findings §4 实测）：exec_code 异步返回（读产物前 sleep/轮询）；list_dir/file_read/file_exists 进程内按路径缓存（换路径拼写绕开）；exec_output 对裸内部命令返回空（显式 `cmd /c` 包装）；**变量赋值同轮运行不稳定**（bootstrap-fp 的 resolve_out 每使用点现调范式）；哈希一律产物直核复核。

## 3. 任务清单（按序执行；每任务含验收）

### T1 片段池过滤 + 模块缓存默认开

现状：片段携带 interner 全量快照 → 大单元写放大（27s→68s 实测，故门控）。
* 在 `tieir_slice.write_mod_slice` 内做**引用收集**：从选中函数的名字/参数类型/块名/指令（opcode 无池引用，const_str 的 kind=2 操作数①是池 id、kind=3 全局名是池 id、符号表/导出/依赖行）收集被引用的池 id 集合 → 池按**原序过滤重编号**（保序压缩，id 重映射写入时同步替换；`interner.len()` 段写过滤后大小）。
* 注意：重建侧（tieir.deserialize / trm loader）按「池 id 即下标」重建——过滤后片段自洽即可，跨片段池不一致是**预期行为**（片段独立成单元）。
* 摘掉 `pipeline.tie` 的 `TIEC_MODCACHE` 门控，模块缓存默认开（`--no-cache` 仍整体关闭）。
* 验收：①driver 自举基准全量编译（片段写 200+ 模块）耗时回到 ≈27s（±10%）；②`verify-modcache.tsh.tie` 四步验收语义不变（冷启 +4 / 重编 +0 / 叶子 +1 / 产物逐字节一致）；③tieir_test 片段 roundtrip 用例在过滤池下仍绿（需给测试模块的构造加 const_str/全局名操作数覆盖）；④自举 + 升格 + 回归 157/8/2。

### T2 tsh REPL v1 语义修复（基础设施，T4 的测量前提）

代码在 `tshell/`（独立仓，main 分支）。目标不是重写解释器，是修四个已实钻的语义点：
* **T2.1 exec_code 异步返回**：改为同步等待子进程退出（或提供 `exec_code_wait`），保留兼容。验收：脚本内 exec_code 后立即 file_read 重定向产物，内容完整（bootstrap-fp/regress 的 sleep 可移除而不破坏）。
* **T2.2 list_dir / file_read / file_exists 的进程内缓存**：同一路径重复观测必须返回新鲜结果（缓存只允许显式 API 或纯函数级 memo）。验收：创建文件 → list_dir 计数变化；探针在 `tshell/tests/`。
* **T2.3 变量赋值稳定性**：同轮运行内 `x = expr` 后所有后续语句必须看到新值（实测反例：bootstrap-fp 中哨兵见默认目录、编译见参数目录、[4/4] 又见默认——复现脚本保留在 findings §4 描述的 bootstrap-fp 历史行为里，先写最小复现探针再修）。验收：`resolve_out` 变量中转范式在 bootstrap-fp 中恢复可用且结果正确。
* **T2.4 exec_output 裸内部命令**：无 `cmd /c` 前缀时自动包装（或文档化 + 显式报错）。
* 约束：tshell 自身改动后，`tiec` 三阶自举不受影响（tshell 不进 driver 编译单元）；trm/回归脚本全量重跑一遍确认无行为漂移；tshell 仓独立 commit + push。
* **若 T2.3 根因涉及表达式求值器深层结构，允许降级**：只做 T2.1/T2.2/T2.4 + 文档化 T2.3 的安全范式（现状已是安全范式）——如实写进 ROAD，不许静默跳过。

### T3 片段组装消费（改叶子只重编该模块）

这是本轮主菜。分两个阶段交付，**阶段 A 是硬验收**：

**T3.A 装配层 + irgen 跳过（本轮必达）**
* 语义层（parse/semantic）仍是全单元——它需要全部文件的类型信息，成本保留；跳的是命中模块的 **irgen + pass + emit** 工作。
* 新增 `middle/tieir_asm.tie`（装配器，与 write_mod_slice 对偶）：输入 = 命中模块的 .tir 片段集合 + 新建模块的 irgen 产物，按 **g_extra_tops 展开序**（主文件 0 → 导入展开序 1..k，菱形导入下模块序 ≠ 函数表序，装配必须按展开序串联）重建完整 IR。
* 关键事实（上阶段实测）：函数/块/指令表按创建序布局且模块内连续；片段内已重映射为片段局部空间 → 装配时做**二级重映射**（片段局部 → 全局），值空间按「参数前缀 + 各函数结果段」分配（与 D1 的重建约定一致）。
* driver 流程改造：`kpass_irgen` 前查模块键 → 全命中的模块跳过 irgen（其函数/块/指令/符号/导出从片段装配）→ 未命中的模块正常 irgen → 装配 → pass 管道照跑（pass 在完整 IR 上）。
* 验收（硬门禁）：①探针工程改叶子文件 → 装配路径产物与全量重编译产物**逐字节一致**（SHA256）；②回归 157/8/2；③自举 + 升格；④`TIEC_INC=1` 打印装配统计（`MODASM h/n assembled`，ASCII）。
* 风险预案：若跨片段值引用（跨模块常量折叠进函数体）导致装配不等于全量，先在片段写入侧把「被折叠常量的来源模块依赖」记入片段头依赖段，装配时把这类模块也判为脏——允许过度失效，**不允许产物不一致**。

**T3.B 提速数据（复测入档）**
* 装配生效后复测：全量 / 单元缓存命中 / 模块装配命中 三组数据（driver 基准 + tests/language 前 30 文件），更新 tie-main `docs/designs/tiec-modularization-design.md` §7.2 表格与 ROAD。

### T4 顺延项（本轮不做，只在 ROAD 更新状态）

* A2b 跨文件 using 前缀补全的常量引用路径护栏接入（scheck_ie_ie1.tie:60 附近同款）。
* `tie:visibility=` 文件级声明入口（随 L3 评估）。
* trm interp 补 br/cond_br/call（真实函数调用图执行）+ 解释器性能优化（有真实负载后再测）。
* tie-main 侧模块 ABI 文档（.tir 格式 v2 权威文本，含两种布局的判定规则）。

## 4. 提交与推送纪律

* 一个小任务一次提交；tiec/tie-main 分支 `p.7`，trm `main`；推送用 gh token 拼 URL（铁律 4）。
* 每完成一个任务：先 commit 再继续下一个；回归红着不许推。
* 记忆纪律：每完成一个任务把（任务号/commit sha/交付物/结论）追加进工作记忆，双语。

## 5. 完成定义（本轮 Definition of Done）

1. T1 + T3.A 全部硬验收通过；T2 按其验收（或如实降级）。
2. tiec 不动点已重录并升格，regress 集合一致。
3. ROAD（tie-main）与 `tiec/docs/p9216-findings.md`（或新 findings 文件）反映最终状态。
4. 三仓全部推送 GitHub，工作树干净（探针产物不入库）。
5. 最终报告：结构化表格（任务/commit/验收结果/遗留），交给用户做 go/no-go。
