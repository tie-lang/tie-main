# p.9.21 tiec 模块化与库化 —— 执行提示词 / Execution Prompt

> 用途：新会话或子代理接手 p.9.21 工作时，将本文件全文作为上下文注入。
> EN: Inject this file as context when a fresh session or sub-agent takes over p.9.21 work.

---

## 一、常识 / Background

**项目**：tie 是自举编程语言（纯 tie 实现、禁 Rust、LLVM 后端）；tiec 是 tie 写的自举编译器。
**仓库**：编译器源码 `F:/Projects/tie-repo/tiec`（分支 p.7）；文档与 ROAD `F:/Projects/tie-repo/tie-main`（同分支）。**编译器源码在 tiec 仓，tie-main 只放 ROAD/docs/std**。
**当前状态**：p.9.20 双轴优化器已全链落地——`-l<0-3>` LLVM 轴 × `-t<0-3>` 中端轴（t1 折叠/化简/传播/DCE，t2 块内 CSE，t3 内联 + tail call），tiec.exe 已升格为 t3+tail 不动点版（sha `2cec594a`）。
**本工程设计已定稿**：`tie-main/docs/designs/tiec-modularization-design.md`（p.9.21，含 I1b 下放判定表与 L1-L5 选项菜单）。拍板：**D1 单文件 ≤800 行；D2 层 II 语言增强入 ROAD；D3 builtin_expr 两步制；D4 单函数 ≤300 行**。
**核心架构裁决**：**不用 frontend/backend 阶段桶**——tiec 重构为**方法分类的 16 个库**（`tie.interner/bytes/columnar/diag/types/ir/lex/ast/parse/sema/irgen/llvmgen/interp/passes/tieir/config`）+ 纯编排薄壳 driver；库之间是「使用」关系（调用图），编译管线只是 driver 的一种编排序列。
**下放裁决**：interner/columnar/diag 渲染/ast/lex/parse/sema/ir/tieir → **std**（语言规范资产，tiec 改为消费 std）；interp/config → **ext**；types/irgen/llvmgen/passes 留 tiec。tlib 源仓 `F:/Projects/tie-repo/tlib`（发行副本 `~/.tiec-lib/tlib`）。
**语言现状约束**：import = 文本内联（主文件+导入文件顶层语句并集）；同名 namespace 跨文件闭合并集是唯一模块边界；常量跨文件不可见；全局 var 必须文件顶层；pub 无强制。语言层优化 L1-L5（可见性梯度/pub const/import 升级/模块编译单元/函数引用）已设计，每项带**选项菜单**（六条通用性原则：opt-in、脚本友好、正交、后端无关、选项菜单、梯度可见性）。

## 二、目标 / Goals

1. **p.9.21.1**：`deps-check.tsh.tie` 库依赖矩阵门禁（16 库依赖图，禁止环）+ **sema→irgen 显式交接物契约**（当前 irgen 裸读 `sstate/node_types/scope_*` 全局，收敛为「注解 AST」数据契约）+ driver 拆分试点（cli_args/cfg_load）。
2. **p.9.21.2**：`irgen_expr.tie`（10,844 行）拆解——builtin_expr（单函数 2,688 行）两步制：①每分支提为 `bi_<name>(id)` 独立函数；②builtin_expr 变表驱动调度器（`lib/dispatch.tie` 已有字符串分派基建）；按内置域分文件。
3. **p.9.21.3**：全仓 ≤800 行/文件（`diagcode_cat.gen` 豁免）、≤300 行/函数；driver 全拆（cli_args/cfg_load/pipeline/cache_drv/diag_out）。
4. **p.9.21.4-6**：语言 L1 可见性梯度（先诊断警告后强制错误）→ L2 pub const → L4 模块级增量编译；tiec dogfood。
5. **内置库**：下放前先修 `coll.kmp_find` 边界 bug（审计第一例：20 万字符找存在的串返回未找到）+ 正确性回归；下放库必须带基准与性能预算（实测：heap_push 3× 裸 push；158 文件含拼接表达式；ext/nn.tie 热循环 as_f64 装箱）。

## 三、纪律 / Discipline

**工作流**：
- 小任务逐个交付：完成一个 = 一次提交（commit message 英文）+ regress 全绿；全部完成再总回归。
- 遇 bug 必做 RCA 并直接修复，不绕过、不掩盖；RCA 结论写进提交与注释。
- 不交付已知缺陷：探针过但 driver 级失败的 pass 必须门控（t3 先例：00dd649 门控 → dbbcc92 解封）。
- 文档双语、列表用 `*`、禁 "P1"/"F1" 无意义标签；**回归细节不进对外文档**。
- 严禁后台运行命令；单命令 ~120s 上限（超时被 SIGTERM）；清编译缓存用 `mv ~/.tiec-cache <backup>`，**禁止 rm -rf**（本机删除走回收站会被 120s 杀）。
- 禁止向 git.franj2.top 推送；tie-main 的远端名是 `github`。

**技术铁律**：
- 禁 Rust；一切能力优先纯 tie；性能永远优先；开发期编译加 `--no-warn`，完成后专门跑一次警告检查。
- 自举是硬门禁：改 driver/irgen/llvmgen 后必须自举验证——配方：`tiec.exe compiler/driver.tie -l2 -t0 --no-warn` → tiec_n1 → tiec_n1 自编 → tiec_n2 → tiec_n2 自编 → tiec_n3；**SHA(n2)==SHA(n3) 即不动点**，`mv tiec_n3 compiler/tiec.exe` 升格；改被 import 的依赖前先 `mv ~/.tiec-cache`。
- regress-s21 基线 **157 PASS / 8 FAIL / 2 SKIP**（8 项既有失败）；判定回归必须用旧编译器跑同一套做对照。
- 涉及 llvmgen/irgen 语义的变更 = 有意的不动点变更，重录基线并在 ROAD 标注。
- 语言改动六原则：opt-in、脚本友好、正交、后端无关、选项菜单、梯度可见性；**先诊断后强制**；默认档 = 最接近现状。
- 每次代码 patch 后 **grep 核验标记存在**（Python replace / Edit 的 old_string 不匹配会静默跳过）；删大块调试代码后必须核验相邻 `var` 声明/函数仍在（本工程曾因清理调试块误删候选扫描段，损失半轮排查）。

**中端 pass 三铁律**：
1. `ir_ops` 里函数参数段与指令段交错——compact/inline 重建必须按「参数段→该函数指令段」搬移并重写 `params_off`；
2. llvmgen 按指令 id 序输出块，**块 id 序 ≠ 指令落位序**——重建必须按旧指令 id 线性保序，禁止按块 id 序重排；
3. 符号池槽陷阱：call/extern_call/call_vararg/const_f/const_str/const_global/inline_asm 的操作数① kind=OK_VALUE 但内容是池 id——传播/DCE/内联复制必须 `is_sym_slot` 跳过。

**内联三要点**：候选必须校验块数==1（多块函数直线展开炸 CFG）；vmap 生命周期按调用点隔离（wlog 精确复位）；块归属与主重建同源记录（n_blk），禁止事后重放。

**opcode 权威** = irgen + llvmgen 字面量（const_i=60、const_str=62 等）；元数据表已重建为 55 条（edd3eca），改 opcode 编号必须同步该表与 ir_test 断言。

**诊断工具（已常驻 passes.tie）**：依赖序自检（UNDEF/XREF + 形参白名单 + 函数名 + n_src 展开来源追踪），内联重建提交前执行；XREF/UNDEF 出现即内联不变量被破坏，先查归属与 vmap 生命周期。

**tlib 脚本**：一律 `.tsh.tie`（tshell），禁 .ps1/PowerShell。

## 四、避坑清单 / Pitfalls

- `fn(i64) -> i64` 函数类型参数已存在（collection 的 map_i64）——L5 是普及+性能确认，不是新增。
- std 库函数在 namespace 内（如 `coll.kmp_find`），调用须限定名。
- builtin_expr 表驱动可复用 `compiler/lib/dispatch.tie` 的字符串分派基建（自举 v2 T2.1 遗产）。
- tiec 内部高性能实现（字符串池 O(1)、sb_scan、irgen_regex 编译期解析+运行时 VM）是内置库重写的参考来源——下放 = 高质量实现随行。
- 性能审计方法：Python 正则扫描 `= x + y` 密度 + 循环上下文 + 实测微基准（库版 vs 手写同算法），静态 grep 判不准类型（整数自增无害）。

---

*EN summary: Self-contained briefing for p.9.21 (tiec modularization). Background: bootstrapped tie compiler, dual-axis optimizer landed, 16 method libraries architecture ruled (no stage buckets), placement to std/ext decided. Goals: deps-check gate + sema→irgen contract + driver split + irgen_expr decomposition + language L1-L5. Discipline: per-task commits with regress+fixed-point gates, RCA mandatory, no background commands, mv-cache, 157/8/2 baseline with old-compiler cross-check, three middle-end iron laws, inline three points, opcode authority, diagnostics resident in passes.tie. Pitfalls: fn types already exist, ns-qualified std calls, dispatch.tie reuse.*
