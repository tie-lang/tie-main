# tiec 结构化输出与 tinker 设计文档（调试信息一等公民）

*EN: tiec Structured Output & tinker Design — debug info as a first-class citizen.*

* 日期：2026-09-25

* 状态：**已实现（2026-10-10，p.9.22.1-13 全量落地；实现注记见文末 §12）**
* 状态历史：已批准（2026-09-25 用户对齐定稿：tinker=tiec 内嵌；符号表落点=伴生文件+tieir 段都要；数据模型=列式 record；符号表内容=全量含 xref；发送/接收目标=stdout 帧/文件/hub 全量）

* 仓库：`tie-lang/tiec`（实现）+ `tie-main`（本设计文档）

* ROAD：p.9.22（2026.2）

* 关联：zd v2（`2026-08-31-zd-v2-design.md`）· td 语法与 td→zd（`2026-08-31-td-data-compiler-design.md`）· tink（`2026-08-31-tink-design.md`）· tie 生态格式家族（`docs/designs/tie-format-api-family.md`）· tieir 格式（`docs/plans/tieir-format.md`）· tdiag 诊断码

> EN EXEC BRIEF: tiec gains (1) a structured-output family (`compiler/dbug/dbgem*`,
> fully modularized per the p.9.21 discipline — no big files, no big functions) that
> dumps any pipeline stage (tokens/AST/symbol table/diagnostics) as columnar records
> in td (row-reconstructed readable projection) or zd (columnar direct write, reusing
> the zdw primitives); (2) a bidirectional tink transport family (`compiler/tinker/`,
> namespace tinker) that wraps those records as tink frames and sends (stdout stream /
> frame file / hub reserved) and receives (stdin stream with CRC rejection + envelope
> kind dispatch); (3) full symbol tables (declarations + types + scopes + cross-refs)
> both as a companion `.sym.zd` file for artifacts and as segment 8 inside `.tir`
> (TIEIR v3). Debug info becomes a first-class citizen: human-readable errors are a
> projection of structured diagnostics; LSP/debugger/tooling consume the same records.

## 1. 背景与定位

tiec 的阶段数据（tokens/AST/符号表/诊断）目前只以人类文本形态输出（报错打印、`--dump-docs` 摘要），调试信息不是一等公民。本设计给 tiec 补三件事：

* **结构化输出器（dbgem）**：任意阶段数据以 td/zd 双形态输出——td 可读可 diff（人/golden），zd 二进制（机器/管道）；
* **tinker（内嵌 tiec）**：把这些数据（及任意段产物）用 tink 帧协议包装**双向**收发——tiec 天然成为 tink pipe 节点；
* **产物符号表**：编译产物携带全量语义符号表（声明+类型+作用域+xref）——伴生文件与 `.tir` 内嵌段两个落点都做。

> EN: Three additions: dbgem (per-stage structured dumps, td/zd), tinker (embedded
> bidirectional tink framing), and full symbol tables on artifacts (companion file +
> tieir segment 8).

## 2. 架构纪律（先例与硬约束）

* **完全模块化（p.9.21 纪律）**：0 大文件（≤800 行）、0 大函数（≤300 行）；主文件持顶层全局 + import 树 + 分派薄壳，拆出文件只含函数（`driver/cli_args.tie` 先例）；零依赖叶模块自持全局（`lex_symtab.tie` 先例）；增长按 `_p1`/`_q1` 后缀再拆。**小函数是硬约束**——tdzd 头注释实证：大函数多分支多 push 触发寄存器分配缺陷。
* **自包含不 import std**：dbgem / tinker 家族沿用 zdw 纪律（被 driver 链式引入，重复 import 令 str 命名空间重复定义）；CRC32 查表在 `tinker_frame.tie` 内自实现。
* **列式即现状**：AST 9 平行表（`frontend/ast.tie`）与符号表平行表（`frontend/sstate.tie`）本就是列式——dump 是直拷，不是变换。
* **确定性**：无时间戳、无哈希序遍历；同输入字节级一致（golden 可做）。

> EN: Architecture discipline: p.9.21 modularization rules (file ≤800 lines, function
> ≤300, main file holds globals + dispatch shell, split files hold functions only),
> zdw-style self-containment (no std imports; CRC32 self-implemented), columnar
> direct-copy dumping (AST and symtab are already columnar), deterministic output.

## 3. record 模型与字段号分区

一切结构化输出 = **列式 record**：zd 按列直写（字段号只追加）；td 为**行重建的可读投影**（列 → 每节点/符号/诊断一行的表字面量，人可读可 diff；golden 测试走 zd）。

**统一信封（公共字段 1-4）**：

| 字段 | 内容 | 形态 |
| --- | --- | --- |
| 1 | schema 版本（记录级演进，=1） | i64 |
| 2 | stage 枚举（1=tokens 2=ast 3=symtab 4=diag） | i64 |
| 3 | 源单元路径 | string |
| 4 | 字符串池（interner 池全量，id=下标；消费者无需 tiec 即可解析） | string 数组 |

**阶段列分区（百位段，只追加，防冲突）**：

* **ast：100-119**——100-108 = ast/node 池 9 列直拷（tags/names/vals/aux/child_off/nchild/children/lines/cols）；109 = file_ids（节点→源文件，多文件单元）；110-119 保留。
* **symtab：150-199**（含 xref，清单见 §4）。
* **diag：200-219**——200 codes（tdiag 码）· 201 severity（E/W）· 202-205 line/col/end_line/end_col · 206 arg_off + 207 args（扁平参数段）· 208 fix_hints（修正提示串池 id）· 210-219 保留。文本报错从此只是诊断 record 的一种渲染投影。
* **tokens：300-309**——300 kinds · 301 text_ids · 302-303 line/col。

> EN: Columnar record model — envelope fields 1-4 (schema/stage/unit/string pool),
> stage columns in per-stage hundred-blocks: ast 100-119 (direct copy of the 9 node-pool
> columns), symtab 150-199, diag 200-219, tokens 300-309; append-only field numbers.
> td = row-reconstructed readable projection; zd = columnar direct write.

## 4. 全量符号表与 xref 侧表

**全局注册表直拷（150-172, 175-186）**——`sstate.tie` 现成表：

| 字段段 | 列 |
| --- | --- |
| 函数 150-153 | fn_names · fn_sig_ids · fn_def_nodes · fn_mods |
| 签名 154-159 | sg_nparams · sg_required · sg_ret · sg_pub · sg_off · sg_gen |
| 参数段 160-163 | sp_tys · sp_refs · sp_defs · sp_vars |
| struct 165-169 | st_names · st_parent · st_fldoff · st_nfld · st_reprc |
| 字段 170-172 | fld_names · fld_tys · fld_defs |
| enum 175-183 | en_names · en_nvar · en_varoff · en_nslot · en_vnames · en_vtags · en_vfldoff · en_vnfld · en_ftys |
| alias 185-186 | alias_names · alias_nodes |

**作用域与交叉引用（188-199）**——sstate 现只有全局注册表，局部作用域在 scheck/sinfer 栈内，不可查询。新增**零依赖叶模块 `frontend/xref.tie`**（namespace xref，自持三张 append-only 侧表）：

| 字段 | 列 | 语义 |
| --- | --- | --- |
| 188 | scope_parent | scope id → 父 scope id（-1=根） |
| 189 | scope_owner | scope id → owner 节点 id |
| 190-196 | decl_name · decl_kind · decl_type · decl_scope · decl_node · decl_line · decl_col | 每个命名声明一行 |
| 197-198 | use_node · use_decl | 每处标识符使用一行（行/列经 ast 节点表 107-108 取，不冗余存） |

* **登记点**：sinfer 标识符解析成功处一行 `xref.reg_use(...)`；声明登记处（scollect/check_fn 族）一行 `xref.reg_decl(...)` / `xref.push_scope(...)`——scollect/reg_fn 同款登记风格，sstate/scheck 既有拆分文件不动。
* **常开无开关**：每标识符一次 O(1) append，成本可忽略；「调试一等公民」不该有开关遗漏的坑。

> EN: Full symbol table = direct copies of sstate registries (fields 150-186) + new
> zero-dependency leaf `frontend/xref.tie` holding three append-only side tables
> (scopes 188-189, declarations 190-196, uses 197-198; use line/col derived from AST
> node columns). Registration is one-line call sites in sinfer/scollect; always on,
> no flag.

## 5. tinker（compiler/tinker，namespace tinker，双向）

**家族（6 文件）**：

```
compiler/tinker/
  tinker.tie        主文件：全局（出口/入口状态）+ import 树 + send/recv 分派薄壳
  tinker_frame.tie  帧编解码（零依赖叶，纯函数）：frame_encode / frame_next / frame_skip
                    + CRC32-IEEE 查表自实现——与 std/tink 逐函数字节级对齐
  tinker_env.tie    tink 信封 record 编解码（依赖 zdw）
  tinker_sink.tie   发送出口：stdout 帧流 / 帧文件 / hub 预留（每出口一小函数集）
  tinker_recv.tie   接收入口：stdin 帧流解析（见下）
  tinker_test.tie   自检：收发往返 + 与 std/tink 互验 + 损坏帧注入
```

**帧协议**：`[len u32 BE][payload][crc u32 BE]`（v1 CRC32-IEEE 先行；tsha1f v2 强校验为后续小任务）。帧载荷 = **tink 信封 record**：

| 字段 | 内容 |
| --- | --- |
| 1 | kind（1=hello 2=hello-ack 3=stage 4=artifact 5=diag） |
| 2 | stage 枚举（同 §3 信封） |
| 3 | name（单元名/产物名） |
| 4 | payload（zd record 字节，`--emit` 同一套 record 换出口再发，不新造数据） |

**发送（sink）**：`--tink` stdout 变帧流（人读文本全部改走 stderr，退出码语义不变）；`--tink-file <f>` 写帧流文件（离线回放与在线管道同一格式）；hub 形态 B 预留（信封 kind/路由字段现在就带）。

**接收（recv）**：`--tink-in` stdin 变帧流。解析纪律对齐 tink 设计 §8：逐帧 `frame_next`，CRC 失败**拒帧报错退出非 0**，不静默传递损坏数据；长度越界同样拒绝；帧间零耦合。信封 kind 分派（每 kind 一个小函数）：

| kind | 动作 |
| --- | --- |
| hello | 回 hello-ack 帧（hub 预留） |
| stage | 按 `--tink-save <dir>` 落文件或透传下一出口 |
| artifact | 落文件后可接 `--dump-irt` 既有读取路径 |
| diag | 渲染 stderr 或透传 |
| 未知 kind | 前向兼容：跳帧计数，收尾摘要报告（不致命） |

**组合**：`--tink --tink-in` 双开 = 全双工管道节点（stdin 收、stdout 发，hub 形态 B 的进程内基础）；`--tink-in-file <f>` 读帧文件——收发共用一条解析路径。

> EN: tinker = bidirectional tink transport embedded in tiec (namespace tinker,
> 6 files). Frame = len + payload + CRC32 (v1 first, tsha1f v2 later). Frame payload =
> tink envelope record (kind/stage/name/payload) reusing the very same records as
> --emit. Send: stdout stream / frame file (hub reserved). Receive: stdin stream with
> CRC rejection (no silent corruption pass-through) and per-kind dispatch (hello/stage/
> artifact/diag/unknown-skip). Dual-open = full-duplex pipe node.

## 6. 产物符号表（两个落点）

**A. 伴生文件**：library/class 编译默认产出 `<out>.a.sym.zd`（symtab record 含 xref；`--no-sym` 关闭；exe 经 `--emit symtab:*` 显式要）。消费者：调试器/LSP/工具链。

**B. tieir 段 8**（`middle/tieir_ser.tie`）：

* `TIEIR_VERSION` 2 → **3**；段 8 = 语义符号表（symtab 列组同构：列数 + 每列「列 id + 行数 + 载荷」；字符串复用段 3 池，不重复带）；
* 反序列化放宽：段号 > 已知最大段 → 读「段号 + 段长」整体跳过（v2 读者读 v3 的自然兼容路径）；
* `content_hash` 覆盖范围扩至段 8（存在时）；
* tieir-format.md §2.1 段表与 §7 校验规则同步修订（ROAD p.9.22 收口项）。

> EN: Companion `.sym.zd` by default for library/class builds (--no-sym to disable),
> plus tieir segment 8 (semantic symbol table, v3 bump, skip-unknown-segment tolerance,
> hash coverage extended).

## 7. CLI 面（driver/cli_args.tie 增量）

| 选项 | 语义 |
| --- | --- |
| `--emit <stage>:<fmt>` | stage ∈ tokens\|ast\|symtab\|diag；fmt ∈ td\|zd；可重复；落 `<input>.<stage>.<fmt>`；与编译并存 |
| `--emit-only` | 只 dump 不继续编译（`--dump-docs` 先例） |
| `--no-sym` | 关闭 library/class 默认伴生 `.sym.zd` |
| `--tink` | stdout 帧流发送（人读文本 → stderr） |
| `--tink-in` | stdin 帧流接收 |
| `--tink-file <f>` / `--tink-in-file <f>` | 帧流文件写 / 读（回放共用解析路径） |
| `--tink-save <dir>` | 收到的 stage/artifact 载荷落盘目录 |

> EN: CLI surface — repeatable `--emit stage:fmt`, `--emit-only`, `--no-sym`,
> `--tink`, `--tink-in`, frame-file in/out, `--tink-save`.

## 8. 与既有组件的关系

| 组件 | 关系 |
| --- | --- |
| zdw（zdwrite.tie） | 列式 record 的 zd 编码原语直接复用，零新增编码器 |
| sstate / ast 列式表 | dump 数据源（直拷）；xref 侧表独立成叶，既有拆分文件不动 |
| tieir_ser | 段 8 追加 + v3 升版；片段缓存/装配器（p.9.21.8-10）不感知段 8（跳过规则覆盖） |
| tink / tink-xxx | 帧协议字节级对齐；tinker 使 tiec 成为标准 tink 节点 |
| tdiag | diag record 的码源；文本渲染降级为投影 |
| tshell / tiedap / LSP | 结构化输出的消费方（后续接线，不在本设计内） |

## 9. 测试策略（probe）

| 探针 | 覆盖点 |
| --- | --- |
| ast 往返 | 9 列直拷 → zd → 读回逐列比对；含中文/嵌套/多文件单元 |
| diag 投影 | 构造 E/W 各类诊断 → record 列完整性 + td 行重建一致 |
| symtab 直拷 | sstate 表 → record 列逐一比对；td/zd 双形态等价 |
| xref | scope 嵌套/同名遮蔽/跨 ns 引用 → use→decl 解析正确 |
| tinker 往返 | tinker 自发自收字节一致；与 std/tink 交叉互验（tinker 编码 std 解、std 编码 tinker 解） |
| 损坏帧 | 翻转 payload 字节 → 必须拒帧退出非 0 |
| tieir v3 | 段 8 roundtrip；v2 读者跳段 8；hash 覆盖断言 |
| 确定性 | 同输入两次编译 dump 字节级一致 |
| 端到端 | `tink pipe "tiec:compile --tink | 消费者"` 产物与直接编译一致 |

> EN: Probe matrix — roundtrips per stage, xref correctness (shadowing/cross-ns),
> tinker self-roundtrip + std/tink cross-verification + corruption rejection, tieir v3
> roundtrip + v2-reader skip, determinism, end-to-end pipe.

## 10. 里程碑与小任务序列（一次一个小任务）

ROAD 编号 p.9.22.1-13（2026.2）；每个小任务带探针，绿了才进下一个。

| 内容 | 产物 |
| --- | --- |
| p.9.22.1 dbgem 骨架①：dbgem_env.tie 信封 + dbgem.tie 分派薄壳 + `--emit` 解析 | 模块立起 |
| p.9.22.2 dbgem 骨架②：dbgem_colzd.tie（一列一函数）+ dbgem_coltd.tie（行重建） | 双形态编码绿 |
| p.9.22.3 ast dump：9 列直拷 + td/zd + 往返探针 | ast 绿 |
| p.9.22.4 diag dump：诊断列式投影 + 探针 | diag 绿 |
| p.9.22.5 symtab dump①：全局注册表直拷 + 探针 | symtab（全局）绿 |
| p.9.22.6 symtab dump②：frontend/xref.tie 叶模块 + 登记点 + 作用域/xref 列 + 探针 | 全量符号表 |
| p.9.22.7 产物符号表 A：library/class 伴生 `.sym.zd` 默认产出 | 伴生绿 |
| p.9.22.8 产物符号表 B：tieir 段 8（v3 + 跳段 + hash 扩展 + roundtrip） | .tir 内嵌绿 |
| p.9.22.9 tinker①：tinker_frame.tie 帧 + CRC32 + std/tink 互验探针 | 帧协议绿 |
| p.9.22.10 tinker②：tinker_env.tie 信封 + tinker_sink.tie（stdout/文件） | 发送绿 |
| p.9.22.11 tinker③：tinker_recv.tie（stdin + 拒帧 + kind 分派）+ 往返/损坏注入探针 | 接收绿 |
| p.9.22.12 端到端：tink pipe 双向节点 + hub 预留接线 | 管道绿 |
| p.9.22.13 文档收口：tiec.md CLI 表 · tieir-format.md 段表/校验 · format-api-family 回写 · G7 自检清单（dbgem_test / tinker_test / xref 计入） | 落盘 |

> EN: Milestones p.9.22.1-13, one small task at a time, each gated by probes.

## 11. 非目标（YAGNI，本阶段不做）

* hub 网络 IPC 实装（形态 B 只预留信封/路由字段）；
* tink v2 帧（tsha1f 强校验）——v1 CRC32 先行，v2 后置小任务；
* compile-request 服务模式（tiec 作为常驻编译服务收请求）；
* 增量 dump / dump 流式分块（大 AST 体积优化列式已覆盖首层，zstd 声明位留给 zd v2）；
* LSP/tiedap/tshell 的消费端接线（结构化输出是他们前置，接线各归其档）。

> EN: Non-goals — hub IPC implementation, tink v2 frames, compile-request serving,
> incremental/streaming dumps, consumer-side wiring (LSP/DAP/tshell).


## 12. 实现注记（2026-10-10，p.9.22.1-13 落地）

实现于 `tie-lang/tiec`（compiler/dbug/ + compiler/tinker/ + compiler/frontend/xref.tie + driver 接线）。与原设计稿的**已记录差异**与关键实现决定：

* **td 投影形态**：设计稿措辞为「每节点/符号/诊断一行」的行投影；实现取**逐列段投影**（同一份列数据 1:1 呈现——直拷保真、双形态等价可机械校验、列内 diff 友好）。记录内容不变；行重建为可选后续增强。
* **信封增补字段**：5 = files（文件表：0=主输入，k>=1=imports）；列段 120-126 = 全局/外部/返回表（gb/ext/tre——「全量符号表」必要面）；diag 209 = names（消息名）、210 = file_ids。均属「只追加」纪律内的实现增补。
* **xref 采集门（性能/内存纪律）**：登记**调用点**一律无条件（无「忘了开」的坑），门在叶子内部（默认关，首行短路零成本）；由 driver 单点开启（`--emit symtab*` / library|class 伴生 .sym.zd / `--tieir-out` / trm 目标）。实测（tiec 自编译 42.5s）：开启 +~1%（含 1.8MB 符号表落盘）；默认编译零开销。
* **xref 查找结构**：纯物理段模型（scope 段起点 = 压入时物理长度；pop 只回退游标）——局部段短扫描 + 全局有序表二分；闭包按登记时快照装载（捕获变量 use→decl 与语义层 cl_o* 同语义）。行号：声明侧登记时快照，use 侧不冗余存（消费方取 ast 107/108）。
* **tieir 段 8**：`set_sec8` 注入式（模块边界纪律：middle 不 import driver；字节 = 段头+段体，调用方经 dbgem 构建）；格式版本 2→3（**读侧接受 v2/v3**，尾部段循环对未知段按「段号+段长」跳过）；content_hash 覆盖 [13, len) 自动含段 8。段 8 列布局 = 「列数 + 每列（字段号+kind+行数+行值）」大端 i64；kind1 行值 = 池 id（读侧经 pool_remap 重映射）。
* **伴生符号表**：写入点 = 前端出口（library/class 且未 `--no-sym` 时）——缓存命中（front 仍跑）也产出；失败路径不写。
* **tinker**：帧/CRC 与 std/tink 逐字节一致（探针双向互验）；CRC32 查表自实现；`--tink` 模式人读文本经 `driver.txt`（dbg_txt）单一出口改走 stderr（编译路径 println 全量收敛）；diag 帧 name = 渲染文本（收侧直出 stderr）；落盘名白名单清洗（[A-Za-z0-9._-]，≤128，拒首点/分隔符——帧来自不受信来源，绝不写出 --tink-save 目录）。
* **验收证据（2026-10-10）**：三阶不动点 `167f60b9…`（n2==n3）升格；回归 252/10/2（FAIL 集合与改动前逐行一致——10 项全为既有）；`--emit` 六通道落盘 + 确定性（两次编译 md5 全同）+ td 经 `--compress-data` 解析回；use→decl 解析修复（物理段模型前 16/149 → 后 **149/149**，小样例）；`.sym.zd` 与 `--no-sym`；`.tir` 段 8 读回（dump 摘要报「语义符号表 51 列/1185 行」）；tinker 自往返/管道（产物字节一致）/损坏帧拒帧（rc=1）/std↔tinker 交叉互验（std 解 tinker 帧 + std 重编码 tinker 解，载荷逐字节一致）。
* **未做（原非目标 + 新增后续项）**：hub 网络 IPC（形态 B 预留）、tink v2 帧（tsha1f 强校验）、compile-request 服务、LSP/tiedap/tshell 消费端接线；td 行投影增强；回归夹具化（探针当前仓外运行，按仓库卫生纪律不入库）。
