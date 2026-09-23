# p.9.21 II3 及之后 —— 自包含交接提示词 / Handoff Prompt (II3 and beyond)

> 交接时点：2026-09-23，p.9.21 的 G1-G8 与 II1/II2 已落地（见 ROAD p.9.21.0-9.21.5）。
> 本文件是剩余工作的自包含交接：II3 模块级增量编译、G9 性能报告与总验收、G7 余量库自检、
> 语言项收尾。执行者不需要读本轮对话，本文件 + ROAD + 设计文档即可开工。
> EN: Self-contained handoff for the remaining p.9.21 work. Execution order, acceptance,
> and all hard-won constraints are inlined; no conversation context required.

## 0. 当前基线 / Baseline

* **不动点**：`c54f16101662ba670c3a4a9296c4b642cfd223f4d70e4e31645c6ce2318393ef`
  （compiler/tiec.exe 已升格到该版）。
* **回归**：157 PASS / 8 FAIL / 2 SKIP——FAIL/SKIP 集合是**已知基线**，任何改动后必须集合一致。
* **门禁**：deps-check.tsh.tie = 越界边 5 条 / 环节点 3 个 / 待修 0——剩余 5 边全部是
  前端求值环 parse↔sema↔interp，属层 II 收口项，**不要在层 I 放宽矩阵**。
* **全仓行数**：所有 .tie ≤800 行（仅 diagcode_cat.gen 豁免）；超 300 行函数 7 个
  （含 .gen），其中 6 个顺序流水线**用户已裁定不拆**。
* **推送状态**：交接时 tiec 领先远端 3 个提交（9c9e3cc II1 / d123b98 II2 / 本轮 II2 收尾），
  代理 502 持续；恢复后 `git push --no-thin https://$(gh auth token)@github.com/tie-lang/tiec.git HEAD:refs/heads/p.7`。

## 1. II3 模块级增量编译（p.9.21.6）/ Module-level incremental compilation

**目标**：模块 = 缓存单元。改一个文件只重编该模块（联动 p.9.15 缓存），增量正确性 + 提速数据。

**现状依赖（先读）**：
* 现有缓存：driver/cache_drv.tie + cache_key_str——键 = (源文件, L 档, T 档, target, M 段
  pass 版本)；粒度 = 整个 driver.tie 编译单元；`--no-cache` 关闭。
* tieir 序列化（S3.2）：tieir.write/read 已按"分发单元"落盘——模块化缓存的产物形态现成。
* import 是 text-inline（语义层把被导入文件顶层并入同一单元）——这是 II3 的核心难点：
  **单元内没有模块边界，缓存无法按文件切**。

**建议路径（三步，每步独立验收）**：
1. **模块边界显式化**：import 的文件 = 模块。语义层把每个导入文件的顶层符号登记进
   `模块名空间`（gb/sg 表加"来源模块"维度），为按模块失效做准备。验收：不改行为，
   全部回归 + 不动点不变。
2. **按模块缓存 tieir**：irgen 后按"根文件 + 各导入文件"分别序列化 tieir（--tieir-out 已有
   单元形态），缓存键加入各导入文件的哈希。验收：改一个叶子文件，其余模块缓存命中；
   产物与全量编译逐字节一致（确定性硬门禁，design §6）。
3. **提速数据**：报告增量 vs 全量的编译时间（tiec 自举 + 大型探针工程两个基准）。

**验收（总）**：改 driver 下的一个文件 → 只重编受影响模块；最终 .ll / .exe 与全量编译
逐字节一致；提速数据入 ROAD。

**已知约束**：
* 缓存键必须含编译器二进制版本（p.9.19.8 遗留：跨版本命中过期产物）——II3 第 2 步顺手补。
* pass 管线版本（g_pass_pipeline_ver）已在 tieir 单元头——增量缓存键必须带上。
* 确定性铁律：同 (源码, l, t, target) → 输出逐字节恒等；禁时间/地址/随机依赖。

## 2. G9 性能报告 + p.9.21 总验收 / Performance report and final acceptance

* 基准：三阶自举（scripts/bootstrap-fp.tsh.tie 的 n1/n2/n3 各阶时长）+ regress 全量 +
  大型探针工程（tests/language/ 16 文件 tokenize/compile）。
* 对照点：p.9.21 开工前（v3 世代 tiec_v3 归档）vs 收官。指标：编译时间（分阶段 TIEC_TIME=1）、
  产物大小、回归集合、门禁报告（5 边/3 环/0 待修——收官态重新评测并记录 5 边的层 II 归属）。
* 产出：docs/designs/tiec-modularization-design.md 追加「收官评测」一节 + ROAD 勾选。
* 总验收清单（对照设计 §验收）：层 I 各项（依赖方向 / 文件与函数上限 / 门禁 /
  库资格四项进度）+ 层 II 各项（II1/II2 已落地、II3 本文件第 1 节）+ 每库自检运行方式。

## 3. G7 余量库自检 / Remaining library self-checks

已覆盖 10 库（interner / columnar / core(dispatch) / types / ast / config / lex / ir /
tieir / diag，均含 pub API 清单）。余量按性价比排序：

1. **passes**：需专门的常量折叠 IR 探针——用 ir.new_* 构造"两常量相加"模块，
   `passes.run(1)` 后断言 rewrite_to_const 生效（t1 语义）+ run 前后 content_hash 记录 +
   pipeline_ver 稳定。读 middle/passes_p1.tie 的 P_CONST_I/P_IMM 常量先行。
2. **trm**：tieir.write → trm_loader 读回（模块 ABI 的第二消费者）；trm 无 LLVM 依赖，纯数据。
3. **irgen / llvmgen / interp**：属编排层，自检形态待层 II 收口后按模块入口设计
   （interp 的求值器已有 regress 覆盖，独立自检收益中等）。

## 4. 语言项收尾 / Language follow-ups（小项，顺手做）

* **A2b 护栏的目录码**：已用 E00649（手工按字节序插入 diagcode_cat.gen.tie）。
  gen-diagcodes.ps1 是 PowerShell——**按 100% tie 铁律应重写为 tsh.tie 生成器**
  （读诊断消息清单 → 产出排序目录；插入/再生成流程 tie 化）。
* **A2b 裸名补充**：ns 内裸名引用（前缀补全命中）已接入护栏；跨文件 `using` 前缀补全
  的常量引用路径（scheck_ie_ie1.tie:60 附近）建议同接入。
* **`tie:visibility=` 文件级声明**：作为 `--visibility=` 的补充入口，随 L3（import 语义
  升级）一并评估——文件级声明是模块化发行库（A1d）的必要形态。
* **lex_test golden 基线重录**：16 个测试语料的 token 总数已漂移（byref_table 期望 139
  实际 144 等），用 Rust tie-frontend --tokens 或新编译器实测重录。

## 5. 铁律与坑（全部实测，违反必返工）/ Hard rules

1. **100% tie**：工具/脚本只能用 tie（编译型 tie<logic>）或 tshell（scripts/*.tsh.tie）。
   禁 Python / shell（2026-09-23 用户拍板，Python 拆分器已全部移除）。
2. **自举次序**：改编译器语义/解析的代码 → 先落改动 → 三阶自举（scripts/bootstrap-fp.tsh.tie，
   断点续跑）→ 升格 compiler/tiec.exe → 再改依赖它的源码 → regress 集合必须一致。
3. **测新语法必须用新编译器**：改了解析器，旧 tiec 编译的探针跑不出新行为（本轮实测踩坑）。
4. **测试脚本必须确认编译成功再运行产物**：编译失败后跑陈旧 exe 会制造假象
   （II2 的"解析成兄弟常量值"假缺陷就是这么来的，实际真缺陷只有 == 1 等值判断）。
5. **tsh 解释器（REPL v1）**：不支持 str.xxx 限定调用（用内建 str_len/substr/split_lines/
   file_read/file_exists/exec_code/exec_output + 自写辅助）；不支持 fc/b 返回码与
   `cmd 管道 > 文件`（产 0 字节文件，哈希直用 exec_output("certutil -hashfile ...")）；
   `cmd /c` 命令以引号开头会剥首尾引号（路径一律不加引号）。
6. **单命令 120 秒 SIGTERM**：三阶自举脚本按 .done 标记断点续跑（exe 存在 ≠ 完成）。
7. **tie 语言**：`&&` 非短路（断言用嵌套 if）；无 break/continue；表按值传参；
   全局 var 必须在顶层（namespace 体内禁 var，E00449）；`str_char` 返回单字符字符串；
   `code` 是保留字；`//` 注释放调用行尾会吞掉右括号。
8. **bit 编码后全查等值判断**：新加 val bit（如 pub bit1）后必须全仓 grep 该节点的
   `s_vals[...] == 1` 型消费点改位测试（II2 实测：collect_global_var 的等值判断漏改会
   静默错值）。
9. **不交付已知缺陷**：语义缺陷宁可显式拒绝（清晰诊断）也不静默错值（II2 ns pub const
   曾如此门禁，修复后撤gate）。
10. **文档现状记述会过时**：II1（pub 无强制→已强制）、II2（const 跨文件不可见→可见）两处
    都是先探针实证再动手；每项开工前先写复现探针。

## 6. 执行顺序 / Execution order

1. 补推送（基线小节）。
2. II3 三步（每步独立验收 + 不动点）。
3. G9 性能报告 + 总验收（引用 II3 的提速数据）。
4. G7 余量（passes → trm）。
5. 语言小项（第 4 节）。
6. ROAD/design 收官勾选 + 归档宣告（对齐 p.9.21.0 的 v3 归档惯例，收官态打 tag）。
