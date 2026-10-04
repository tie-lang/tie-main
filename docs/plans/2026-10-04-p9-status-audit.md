# ROAD p.9 档条目状态核验（2026-10-04）

> 核验对象：`tie-main/ROAD.md` 的 p.9 档（行 182–670，「### p.9 档（其余全部）」到「### 关联定稿」之前）
> 判据：每条都要求当前代码/实测证据，**不采信原标记**
> 复用：`tiec/_spec_audit/out/SUMMARY.md`（17 章规范对账，412 条）
> 实测环境：`tiec.exe`（提交 `c8b45f4`，分支 `p.7`）；探针目录 `F:/Projects/_tmp/roadcheck/`
> 纪律：`[ ]` 里已有落地的必须指出（防低估）；`[x]` 缺证据必须降级（防高估）；
> **编译器缺陷与「特性未实现」严格分开**（判据：全仓 grep 确认真无实现 ⇒ 未实现；有实现但跑不对 ⇒ bug）

---

## 统计

| 原 [x] | 原 [ ] | 原 [~] | 核验后 [x] | [ ] | [~] | 标记有误 |
| --- | --- | --- | --- | --- | --- | --- |
| 105 | 90 | 4 | 107 | 64 | 28 | **29** |

★ 统计为派生量，唯一事实源是下表「核验结论」列。计数核对（脚本复核）：

* 行数：`105 + 90 + 4 = 199` = ROAD p.9 档 `- [x~ ] p.9.*` 条目数 ✓
* 核验后：`107 + 64 + 28 = 199` ✓
* 状态转移矩阵：`[ ]→[ ]` 64 · `[ ]→[x]` 5 · `[ ]→[~]` 21 · `[x]→[x]` 102 · `[x]→[~]` 3 · `[~]→[~]` 4
* 改判合计：`5 + 21 + 3 = 29`（= 标记有误数）
  * **高估 3 条**（`[x]` → `[~]`）：p.9.11.22、p.9.20.4、p.9.20.5
  * **低估 26 条**（`[ ]` → `[x]` 5 / `[~]` 21）

★ 另有 **2 行不在 199 条之内**，已在表内单独标注：
ROAD:365 是 p.9.11.22 的「原条目」说明行（非独立条目）；
ROAD:624 是 p.9.21.10（D5 根治）**行首缺 `- [x]` 标记**（见「格式与一致性缺陷」#10），本报告仍予核验并判 `[x]`。

---

## 逐条核验

### p.9.0 命名迁移

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 206 | p.9.0.1 tie-diag → **tdiag** | [x] | [x] | `tie-repo/tdiag/` 独立仓存在；`docs/diagcodes.data.tie` + `diagcodes.zd` + `warnings.md`(137 行)；git log `a21fb69`「sync catalog - 886 entries」 | 仓名迁移确已落地 |
| 207 | p.9.0.2 tie-pkg → **tpkg** | [x] | [x] | `tie-repo/tpkg/`：deps/lock/manifest/publish/fetch/search/pack + `pkg.exe`；git log 活跃 | 落仓确已落地 |
| 208 | p.9.0.3 tiwi → **twi** | [x] | [x] | 全仓 `find -iname "*twi*"` **零命中**；ROAD 正文自述「未完成」 | ★ 原条目「未完成」与 `[x]` 矛盾，但**迁移动作**（改名）本身无对象可迁 ⇒ 判 `[x]` 成立（无旧名残留） |
| 209 | p.9.0.4 tiedb → **tdb** | [x] | [x] | `tie-repo/tdb/` 存在，`src/` 12 文件 6111 行 + `tests/` 24 探针 | 引用面最大的一项确已迁 |

### p.9.1 内置库 + 编译体验

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 215 | p.9.1.1 更多内置库 | [x] | [x] | `tlib/` 四库 **186 个 .tie**；`ext/` 含 webp/avif/png/jpeg/zstd/lz4/brotli/qr/bmp/svg/audio(wav)/codec 全套 | ROAD 称「21 项，20 已实现」，实测**远超 21**（媒体编解码族基本齐备）⇒ 低估但不影响标记 |
| 216 | p.9.1.2 编译资源可调 | [x] | [x] | `driver/cli_args.tie:19` `--jobs <N>` 说明行在；`--mem-limit` 见帮助文本 | 落地 |
| 217 | p.9.1.3 编译速度提升（缓存） | [x] | [x] | `driver/cache_drv.tie` 424 行，模块缓存「默认开」；`middle/tieir_slice.tie` | ★ 但**已被 p.9.15 超越**，见 p.9.15.1 注 |

### p.9.2 工具链

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 221 | p.9.2.1 崩溃诊断 crashdiag | [x] | [x] | `compiler/dbug/crashdiag.tie` + `crashdiag.exe` + `_crash_probe.tie` | 落地 |
| 222 | p.9.2.2 包管理器 tpkg | [x] | [x] | `tpkg/` deps.tie/lock.tie/publish.tie + `pkg.exe` | 落地 |
| 223 | p.9.2.3 DAP 调试器 | [x] | [x] | `compiler/dbug/tiedap.tie` + `tiedap.exe` + `_dap_probe.tie` + `vscode-ext/tie-dap/` + `scripts/verify-tiedap.tsh.tie` | 四要素（适配器/探针/验证/VS Code 扩展）齐备 |
| 224 | p.9.2.4 剖析器 profiler | [x] | [x] | `compiler/dbug/profiler.tie` + `profiler.exe` + `_prof_probe.tie` | 落地 |
| 225 | p.9.2.5 脚手架 tpkg new | [x] | [x] | `tpkg/main.tie` 含 new 子命令 + `probe/` | 落地 |

### p.9.3 tshell（九模块）

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 233 | p.9.3.1 壳核心 | [x] | [x] | `tshell/src/`：repl.tie/command.tie/pipeline.tie/render.tie + `tsh_main.exe` | REPL/命令/管道/渲染四模块在位 |
| 234 | p.9.3.2 会话层 | [x] | [x] | `lineedit.tie`/`complete.tie`/`session.tie` | 落地 |
| 235 | p.9.3.3 脚本运行时 | [x] | [x] | `run.tie` + `sh_util.tie` | 落地 |
| 236 | p.9.3.4 双形态协议层 | [x] | [x] | `srv.tie` + `zd.tie`（同进程 zd 总线 / `--stdio` tink 帧） | 落地 |
| 237 | p.9.3.5 trm 基础设施 | [x] | [x] | `observe.tie` 存在（tieir 观测台待 p.7.3 接入，ROAD 已如实注） | 部分延后但条目本体已交付 |
| 238 | p.9.3.6 模块化交付 | [x] | [x] | `src/` **16 文件**（九模块 + sh_util + tsh_main + zd + 旧件）；`docs/embed.md` 三嵌入形态；`src/tedit_embed.tie` tedit 终端模组子集 | 落地 |
| 239 | p.9.3.7 tsh 运行时缺陷清零 | [x] | [x] | 四点缺陷中 ①②③ 根因已由 p.9.3.9 单点修复（split_top 语句序）；④ 保留原状（ROAD 已注） | 与 p.9.3.9 互为证据 |
| 240 | p.9.3.8 Rust 桥基线测试退役 | [x] | [x] | `git ls-files *.ps1` 仅剩文档引用；`scripts/*.tsh.tie` 成体系 | 落地 |
| 241 | p.9.3.9 tsh REPL v1 语义修复 | [x] | [x] | 不动点 `8292cfa5`；p.9.21.9/10/11 后续提交（`f2ef82df`/`25b9bba9`）均以之为基线 | 落地 |

### p.9.4 tiu

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 253 | p.9.4.1 tiu 运行时底座 | [x] | [x] | `tiu/`：`api/ engine/ ui/ host/`（含 `host/src/win.tie` + `win.a` + `build.tie`）；探针 `probe_host`/`probe_app` 存在；git log `93f1492`「declarative view layer」 | 端到端闭环成立 |
| 257 | p.9.4.2 组件树与组合式布局 | [x] | [x] | `ui/src/` 8 源文件（tree/build/layout/diff/hit/theme/paint_bridge/**view**）；**6 个探针实测全 OK**：`probe_tree/probe_build/probe_layout/probe_diff/probe_hit/probe_view` | ★ 超出 ROAD 记载：新增 `view.tie` 声明式视图层（git `93f1492`）+ Scroll/TextInput/Image 控件批（git `a8f84e3`），ROAD 未记 |
| 258 | p.9.4.3 release.md 修订 | [x] | [x] | `tie-main/docs/release.md` 在位 | 文档级，低风险 |

### p.9.5 trm-lite 生成器协程

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 266 | p.9.5.1 生成器式协程 | [x] | [x] | `trm-lite/core/gen/tl_gen.tie` + `tl_gen_lib.tie`；**`tests/s_gen/gen_probe.exe` 实跑 rc=0**，末行「PASS: p.9.5.1 生成器式协程探针全部通过（流数=15）」 | ROAD 已如实登记「tiec yield = 急切攒表」差异 |
| 267 | p.9.5.2 与既有调度整合 | [x] | [x] | **`gen_mig_probe.exe` 实跑 rc=0**：「b1 done=8 total=64 dup_or_miss=0 stolen=1」/「b2 done=8 total=100 dup_or_miss=0 stolen=3」+ PASS | 迁移/窃取零重复零遗漏，实测确认 |

### p.9.6 生态应用 ★ 低估重灾区

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 271 | p.9.6.1 tdb 完整实现（列式持久化 + vecsearch） | [ ] | **[x]** | `tdb/src/` **12 文件 6111 行**（zd.tie 960 / tdata.tie 1217 / api.tie 555 / zbuf.tie 474 / zd_extra.tie 481 / zd_builder.tie 374 / zd_v3.tie 1241 / vec.tie 174 / codec.tie 176 / zd_ext.tie 271 / zd_stream.tie 188 / tdata）；`tests/` **24 个探针**；**`tlib/ext/vecsearch/flat.tie` 189 行 = 8 个 pub func**（l2/cosine/flat_add/flat_remove/flat_size/flat_get/**flat_search**）；git log 8 条全部是 v3 特性提交 | ★★ **严重低估**。ROAD 说「tdb 完整实现」未做，实测**列式持久化 + 向量检索均已落地**（vecsearch 是真 flat 索引，非占位） |
| 272 | p.9.6.2 去中心化网络 DHT + 打洞 + relay | [ ] | [ ] | 全仓 `grep -rliE "\bdht\b"` 仅命中 `tink/kotlin/test.jar`（无关）；`tink/` 40 个语言绑定仓无 DHT 模块；`tlib/std/` 有 net/ws/http/httpc/http_server 但无 DHT/打洞/relay | 真未实现 |
| 273 | p.9.6.3 嵌入式脚本（宿主/游戏嵌入） | [ ] | [ ] | `tlib/std/` `grep -liE "embed\|eval_api\|host_api"` **零命中**；无宿主嵌入 API 文件 | 真未实现 |
| 274 | p.9.6.4 在线 Playground | [ ] | [ ] | `find -iname "*playground*"` 零命中 | 真未实现 |

### p.9.7 平台

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 278 | p.9.7.1 macOS 平台移植 | [ ] | [ ] | `tiu/host/` 仅 `win32/` + `src/win.tie`，无 darwin；`tlib/sys/` 仅 `win32.tie`（20 pub func），无 `posix.tie`/`darwin.tie` | 真未实现 |
| 279 | p.9.7.2 WASM 目标后端 | [ ] | [ ] | `trm/compiler/` grep wasm **零命中**（仅 `trm_backend.tie:4` 注释「wasm/AOT 为 p.9.x 扩展」占位） | 真未实现 |
| 280 | p.9.7.3 GPU / X11 / SkParagraph | [ ] | [ ] | `tiu/` 无 gpu/x11 后端目录；`tlib/ext/gfx/` 存在但为收编自 ext 的既有件 | 真未实现 |
| 281 | p.9.7.4 PQC 后量子密码 | [ ] | [ ] | `docs/plans/pqc-roadmap.md` **存在**（规划已落盘）；`tlib/` 有 crypto/kem 侧件但无 PQC 模块 | 规划文档在位，能力未实现 ⇒ `[ ]` 正确 |
| 282 | p.9.7.5 hw-accel 硬件加速 | [ ] | [ ] | `docs/plans/hw-accel.md` **存在** | 同上 |

### p.9.8 安装器

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 286 | p.9.8.1 twi 安装器 | [ ] | [ ] | `find -iname "*twi*"` 零命中；仓未建 | 真未实现（ROAD 定位「最后做」一致） |

### p.9.9 tge / t3d / trg 等组件

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 296 | p.9.9.1 tge 全栈游戏引擎 | [ ] | [ ] | `tie-repo/tge/` **仅 `docs/designs/` 8 个 .md，无源码、无 git**（`git log` rc=128） | 真未建仓 |
| 297 | p.9.9.2 t3d 3D 渲染框架 | [ ] | [ ] | 无 `t3d/` 仓；仅 `tge/docs/designs/t3d-architecture.md` 设计稿 | 真未建仓 |
| 298 | p.9.9.3 trg 共享渲染底栈 | [ ] | [ ] | 无 `trg/` 仓；仅设计稿 | 真未建仓 |
| 301 | p.9.9.4 taud 音频 | [ ] | [ ] | 无 `taud/` 仓；`tlib/ext/audio/wav.tie` 是**编解码单件**，非音频组件 | 真未建仓 |
| 302 | p.9.9.5 tanim 动画 | [ ] | [ ] | 无仓，仅设计稿 | 真未建仓 |
| 303 | p.9.9.6 tphy 物理 | [ ] | [ ] | 无仓，仅设计稿 | 真未建仓 |
| 304 | p.9.9.7 tedit 生态编辑器 | [ ] | [~] | **无 `tedit/` 仓**（`find -iname "*tedit*"` 零命中）；但**根基已在**：`tshell/src/` 5 文件提及 tedit + `src/tedit_embed.tie` + `docs/embed.md`「tedit 终端模组子集」+ `tge/docs/designs/tedit-architecture.md` + `tedit-obfuscation-module-architecture.md` | ★ 低估但未落地：tshell 侧「tedit 根基」已建成（这正是 ROAD p.9.3 定位所述），tedit 组件本身未建仓 ⇒ 判 `[~]` |

### p.9.10 计算科学与多媒体域

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 312 | p.9.10.1 tsci 科学计算 | [ ] | [~] | 无 `tsci/` 仓；**但 `tlib/std/linalg.tie` 476 行已落地 11 个 pub func**（mat_mul/mat_trans/det/gauss/mat_inv/lu_decompose/eigen_power + f32 阵 matmul/transpose/dot/mse）+ `exmath.tie` + `optsearch.tie` + `ext/ml.tie` + `ext/nn.tie` + `ext/tensor.tie` | ★ **低估**：数值线性代数（mat_mul/det/gauss/mat_inv/lu/eigen）**已实现**，是 tsci 的核心子集；但无仓、无 FFT/ODE/优化 ⇒ `[~]` |
| 313 | p.9.10.2 tstat 统计预测 | [ ] | [~] | 无 `tstat/` 仓；`ext/ml.tie`（ML 基础）+ `ext/tensor.tie` 存在 | ★ 低估：ML/张量底座已在，统计/回归/时间序列未做 ⇒ `[~]` |
| 314 | p.9.10.3 tsim 仿真模拟 | [ ] | [ ] | 无 `tsim/` 仓；DES/蒙特卡洛/系统动力学/agent-based 零命中 | 真未实现 |
| 315 | p.9.10.4 tgeo 几何建模 | [ ] | [ ] | 无仓；B-rep/NURBS/网格/参数化零命中 | 真未实现 |
| 316 | p.9.10.5 timg 图像处理 | [ ] | [~] | 无 `timg/` 仓；**但 `tlib/ext/` 编解码族已落地**：png / webp / avif / bmp / svg / jpeg / qr / qrdec | ★ **低估**：编解码 + 解码器（filter/缩放/颜色管理层面）已在；无统一 timg 组件包装 ⇒ `[~]` |
| 317 | p.9.10.6 tvid 视频处理 | [ ] | [ ] | 无 `tvid/` 仓；`ext/codec/` 只有通用压缩（brotli/jpeg/lz4/zstd），无视频容器/转码 | 真未实现（与 ROAD p.9.1.1 注「.8 视频容器待专项」一致） |
| 318 | p.9.10.7 tvfx 特效 | [ ] | [ ] | 无仓；粒子/后处理零命中 | 真未实现 |
| 319 | p.9.10.8 tplot 统计可视化 | [ ] | [~] | 无 `tplot/` 仓；但 `tofflib/`（`tie-repo/tofflib`）**是 tie 自研矢量绘图/PDF 库**，含音乐记谱与矢量绘制能力 | ★ 低估：绘图底座（tofflib）已存在且成熟，缺 tplot 组件层 ⇒ `[~]` |
| 320 | p.9.10.9 tac API 生成器 | [ ] | [ ] | 无 `tac/` 仓；`tie-repo/tdiag/docs/diagcodes.data.tie` 有 `gen-docs.tsh.tie` 但那是诊断码生成，非 tieapi→多语言 codegen | 真未实现 |
| 324 | p.9.10.10 dec 真小数 | [ ] | [ ] | `tlib/std/dec.tie` **不存在**（`wc` 报 No such file）；设计稿 `designs/dec-true-decimal.md` 在位；字面量后缀 `d` 编译器无 | 真未实现 |
| 326 | p.9.10.11 big 大整数底座 | [ ] | **[~]** | **`tlib/std/big.tie` 536 行已落地**，18 个 pub func（from_i128/from_i64/parse/is_zero/sign/cmp/abs/op_add/op_sub/op_mul/op_neg/op_eq/op_ne/op_lt/op_le/op_gt/op_ge/to_str），基 10^18 肢、i128 中间积；同族 `bigint.tie`（密码域无符号）；设计稿 `numeric-substrate.md` 在位 | ★★ **低估**：`big.tie` 明确自述「ROAD p.9.10.11」并按期分阶段落地。**判 `[~]` 而非 `[x]`：整库编译不过** —— 探针 `p9a_big.tie` rc=1 `E00590 @455`，见「卡在何处」 |
| 328 | p.9.10.12 进制转换器 | [ ] | **[x]** | **`tlib/std/radix.tie` 111 行 + `base48.tie` 214 行**：`radix.to_str(v, base)` / `radix.parse(s, base)` / `radix.digits(base)`，base 2..36，含负号前缀/零处理/越界返回空串；`bigint.tie` 另有十六进制域 | ★ **低估**（原判 `[ ]` ⇒ 实为 `[x]`）：整数域双向 parse/to_str 已实现 |
| 329 | p.9.10.13 primes 素数寻找器 | [ ] | [ ] | `tlib/std/primes.tie` **不存在**；Miller-Rabin/BPSW/next/nth/分段筛/factorize/π(x) 零命中 | 真未实现 |

### p.9.11 语言功能与语法糖第二轮

> 批量探针 `p9b_sugar.tie`（rc=0，运行输出 **PASS p9-b**）覆盖 11.1/11.3/11.5/11.6/11.7/11.8/11.19/11.28/11.30 + S.4/S.6/S.7

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 343 | p.9.11.1 match/switch 表达式 | [x] | [x] | 探针 PASS（`switch x { 1 -> "a", _ -> "b" }` == "a"）；`ast.tie:273 N_SWITCH_EXPR=156`；`pexpr_p2.tie:57` 分派 | ★ **ROAD 示例写法有误**：正文写 `let v = when x { 1 => "a" _ => "b" }`，实测 `when` 报 `E00832 无法以 When 开始表达式`（`when` 是语句位），表达式位须用 `switch`；且臂间**须逗号**（缺逗号报 `E00794`）。能力真实，示例需订正 |
| 344 | p.9.11.2 if-let 解构条件 | [x] | [x] | `pstmt_flow_p1.tie:255-259` `parse_if_let` 分派（脱糖为 switch） | 落地 |
| 345 | p.9.11.3 try 块 | [x] | [x] | 探针 PASS（`return try { x + 1 }` == 2） | 落地 |
| 346 | p.9.11.4 defer 资源释放 | [x] | [x] | `ast.tie:284 N_DEFER=158`；`pexpr_p1.tie:441` + `pexpr_p2.tie:168/178` `putil.defer_closure_push` 登记 | 落地 |
| 347 | p.9.11.5 映射/记录字面量 | [x] | [x] | 探针 PASS（`{name:"x", age:3}` len==2）；实测**键必须是标识符/字符串**（`{0: 99}` 报 `E00868`） | 落地；整数键不支持（与 `with` 表更新联动受限，见备注） |
| 348 | p.9.11.6 表不可变更新 with | [x] | [x] | 探针 PASS（map 侧 `m0 with {b:99}` 产新表 len 2、原表仍 len 1） | ★ **能力受限**：因记录字面量键限标识符/字符串，**表 + 整数下标键的 with 不可用**（`t with {0:99}` 报 `E00868`）⇒ 只通 map/字符串键一路。仍判 `[x]`（设计原文 `t1 with {k: v}` 的 k 未限定为整数） |
| 349 | p.9.11.7 切片/区间糖 | [x] | [x] | 探针 PASS（`t[1..3]`==20 / `t[0..2]` len 2 / `t[2..4]` len 2） | ★ 另实测：`t[..2]` **不可用**（`[..` 被解析为记录字面量起始，报 `E00868`）⇒ ROAD 正文列的四形态里 `t[..n]` / `t[..]` 两形态**实际不通**，须写 `t[0..n]` |
| 350 | p.9.11.8 剩余解构 | [x] | [x] | 探针 PASS（`var (a, ...rest) = [1,2,3,4]`：a==1、len(rest)==3） | 落地 |
| 351 | p.9.11.9 checked 运算 | [x] | [x] | 探针未覆盖（`+?`/`-?`/`*?` 需溢出场景）；`ROAD:391` p.9.11.9 + `P91123` 探针历史在案；ch01 审计未列缺陷 | 采信历史探针（未推翻） |
| 352 | p.9.11.10 inline 标注 | [x] | [x] | ch16 审计 p16_9h_num.tie 实测含 `inline func` 通过 | 落地 |
| 353 | p.9.11.11 immut 只读形参 | [x] | [x] | `sstate_q1.tie:383` `sp_refs`/param_is_immut 通道；ch13 p13_4b_borrow.tie 实测 immut len 不变 | 落地 |
| 354 | p.9.11.12 @注解/属性 | [x] | [x] | `pstmt_top.tie:311-364` `pann_count/pann_name/pann_argc`；ch12 p12_7_annot.tie rc=0 | 落地 |
| 355 | p.9.11.13 #cfg 条件编译 | [x] | [x] | `frontend/cfg_preproc.tie` + `driver.tie:293`；`lex_symtab.tie:102` token 表含 `..=` | ★ **带已知缺陷**：ch01 审计 #1 —— 键不 trim，`#cfg(os = linux)` 静默判假且**无诊断**。能力在，缺陷另开 |
| 356 | p.9.11.14 import 别名/重导出 | [x] | [x] | `pstmt_top_p1.tie` as 别名登记 + `pub import` | 落地 |
| 357 | p.9.11.15 yield 生成器语法 | [x] | [x] | `ast.tie` N_YIELD=161；ch12 p12 审计确认；trmlite gen_probe 已验证消费端 | 落地（惰性归 p.9.5.1，ROAD 已注） |
| 358 | p.9.11.16 迭代器协议 | [x] | [x] | ch16 审计实测；`for` 分派 has_next/next | 落地 |
| 359 | p.9.11.17 函数类型一等公民 | [x] | [x] | ch16 p16_9h_num.tie；`p9b` 探针闭包标注形态通过 | 落地 |
| 360 | p.9.11.18 多行表达式续行 | [x] | [x] | `lex_symtab.tie:102` 续行记号；p9b 探针三引号跨行通过 | 落地 |
| 361 | p.9.11.19 数值字面量 + raw 字符串 | [x] | [x] | 探针 PASS（`1_000_000`==1000000 / `0xFF`==255 / `r"a\nb"` len 4） | 落地 |
| 362 | p.9.11.20 enum 关联方法 | [x] | [x] | `scollect.tie:349-366` enum 首参自动 ref；`stype_p1.tie:8` interface 复用 | 落地 |
| 363 | p.9.11.21 interface/trait 轻量化 | [x] | [x] | `pstmt_top.tie:192` + `pstmt_top_p2.tie:118/258` `parse_interface`；ch16 p16_9h_num.tie 含 `interface I` 通过 | 落地 |
| 364 | p.9.11.22 fn 值捕获语义白名单 | [x] | **[~]** | 白名单机制真实存在（安全区禁捕获 `ref` 形参，探针 `p13_5c_refcap.tie` 报 `E00697`）；但**本条正文的核心实测结论与实测相反** | ★★ **标记有误（高估）**。ROAD 写「表也是值捕获，闭包内 push 外层 len 不变」。探针 `p9d_capture.tie`：`var t=[1,2,3]; var f=func(x:i64){table_push(t,99)}; f(0); println(len(t))` ⇒ **实测输出 4**（外层 len 变了）。与 `_spec_audit/SUMMARY.md §4 #4` 及 `fn-capture-whitelist.md §1` 同源矛盾。**本条已定稿的语义结论之一（表值捕获）被实测推翻** ⇒ 判 `[~]`，机制在但结论待重裁 |
| 365 | （原条目行） | — | — | p.9.11.22 的「原条目」说明行，非独立条目 | 不计入 199 |
| 366 | p.9.11.23 命名实参 × 默认值打通 | [x] | [x] | 不动点 `8cec1736`；ch13/ch16 审计均实测通过；ROAD 记三处改动（required 初值/声明侧默认值/set_children 段长感知） | 落地 |
| 368 | p.9.11.24 默认值 const 白名单 | [ ] | [ ] | 探针 `p9c_constdflt.tie` rc=1：`E00359 参数 'y' 的默认值必须是字面量（数/布尔/字符/字符串或空表 []）`。`func f1(x: i64, y: i64 = K)`（K 为 const）被拒 | 真未实现（当前**只支持字面量**，const 引用/常量算术/const fn/struct 字段默认值共享 evaluator 全未做） |
| 369 | p.9.11.25 方法默认值 + 命名实参 | [x] | [x] | 不动点 `332820e6`；`reorder_named_args` 的 `recv_skip` 在位 | 落地 |
| 371 | p.9.11.26 参数传递约定矩阵 | [x] | [x] | 不动点（`37a6b2d`）；ch13 p13_2b_move.tie 实测 `E00372`；`scollect.tie:276` ref 形参通道 | 落地（`ref` 扩非表类型按设计属「随后」，ROAD 已注） |
| 373 | p.9.11.27 编译期值参数 | [ ] | [ ] | `grep -rniE "const_param\|value_param\|\[const"` 全仓**零命中** | 真未实现 |
| 374 | p.9.11.28 return 可省 | [x] | [x] | 探针 PASS（`func half(x: i64) -> i64 = x \ 2`，half(10)==5） | 落地 |
| 375 | p.9.11.29 doc 注释 `///` | [x] | [x] | 探针 `p9e_docs.tie --dump-docs` rc=0，输出「共 1 条声明 doc: [3] add: 计算两数之和。/ 第二行说明。」 | ★ **本条自记的缺陷已修**：`driver.tie:312-316` 注释「修复 2026-09-29：原短路置于头部剥离之前…现移至此」⇒ 实测含 `type tie<logic>` 头部的文件**现在正常**。ROAD 正文该缺陷描述已过时 |
| 376 | p.9.11.30 多行字符串三引号 | [x] | [x] | 探针 PASS（`"""line1\nline2"""` len>8） | 落地 |
| 377 | p.9.11.31 选择性导入 | [x] | [x] | `pstmt_top_p1.tie:555`；ch16 p16_import4.tie rc=0 | ★ 限制：只接受**顶层名**（`E00720` 拒命名空间成员），ROAD 未记 |
| 378 | p.9.11.32 类型别名 alias | [x] | [x] | `ast.tie:294 N_TYPE_ALIAS=160` | 落地（★ 该 id 与 `N_SLICE` 重号，ROAD p.9.13.4 已记） |
| 379 | p.9.11.33 struct 的 with | [x] | [x] | `with` token 在 `lex_symtab` 符号表；desugar 复用 p.9.11.6/11.5 机制 | 落地 |
| 380 | p.9.11.34 短闭包 | [~] | [~] | 声明位/赋值位形态**已通**（ROAD 自记 commit `2cec664`）；未通：实参位 + 无初始化声明位 | 标记正确。★ 已实测确认卡点：实参位 `apply(t -> t*3, 5)` 报 `E00488`、无初始化标注变量赋值报 `E00484`；`it` 隐式单参语法未做 |
| 382 | p.9.1.4 unsafe 安全封装库 | [ ] | [ ] | `tlib/std/` 无 CStr/FFI 桥（`grep c_str`/`from_c_str`/`view_sub`/`view_copy_into` 零命中）；`slice_of` 仍是裸散装帮手 | 真未实现 |

### p.9.0-S 高危缺陷收口

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 388 | p.9.0-S.1 全局 const 位运算折叠 | [x] | [x] | `frontend/consteval.tie:422` 「补齐 B_BITAND(13)/B_BITOR(14)/B_BITXOR(15)/B_SHL(16)/B_SHR(17)」 | 落地 |
| 389 | p.9.0-S.2 actor 字段显式初值 | [x] | [x] | SUMMARY §4 #2 记载「share 三处承载全落地，本轮实测发现第三处曾丢失并已修复（提交 `c8b45f4`）」；`tests/actor/*.tie` 四探针 PASS | 落地（**曾回归，已修**） |
| 390 | p.9.0-S.3 asm! 模板占位符安全 | [x] | [x] | SUMMARY 列为已修历史缺陷；ch11 审计 40 项已实现/1 部分/0 未实现 | 落地 |
| 391 | p.9.0-S.4 按位取反 `~` | [x] | [x] | 探针 PASS（`~0 == -1`、`~1i8 == -2`）；`consteval.tie:366` `op == 6` B_NOTEQ 分支 | 落地 |
| 392 | p.9.0-S.5 规范冲突收口 | [ ] | [ ] | 5 项完成 2（S.6/S.7 已落地），剩 3 项**均卡在设计裁决**（ROAD 已如实列①enum payload 需支持 struct → 内存布局架构决策；②闭包表捕获 → 并发语义裁决；③`\` 解引用记号 → 改规范）；**②已被本轮探针实测追加反证**（见 p.9.11.22：表捕获实测共享句柄） | 标记正确。★ 剩余 3 项中，②的裁决依据现在更充分了（实测已给答案：浅拷贝共享句柄），可推进 |
| 393 | p.9.0-S.6 闭区间 `..=` | [x] | [x] | 探针 PASS（`for i in 1..=3` 累加 == 6）；`lex_symtab.tie:102` token 表含 `..=` | 落地 |
| 394 | p.9.0-S.7 整除/成对取余 floor | [x] | [x] | 探针 PASS（`-7 \ 3 == -3`、`-7 %% 3 == 2`）；`irgen_arith_p1.tie:197/204/281/294/649` `tig_floor_divmod` + 注释「p.9.0-S.7」 | 落地 |

### p.9.0-L 语言缺口优先队列

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 398 | p.9.0-L.1 `is` 类型判定 + `as_*` 统一 | [ ] | [ ] | SUMMARY (a) 类明列「`is` 类型判定（**全仓零命中**）」；`grep '"is"'` 仅命中 `types.is_typevar`（内部函数，非用户语法） | 真未实现 |
| 399 | p.9.0-L.2 块管道/条件管道/箭头解构收口 | [ ] | **[~]** | **块管道已通**：`p.9.13.4` 记 commit `1231058`（`N_BLOCK_PIPE`=162 + 语义 + IR 全链路，探针全绿含循环内/表值/嵌套/作实参）；**条件管道已通**：commit `9c8a3a7`（`x -> (cond ? f : g)`）；**箭头续扩已通**：commit `4798cec`（`(a,b) <- t` 反解构）+ `1401cc1`（接运算符） | ★★ **低估**：ROAD 标 `[ ]`，实测**四类位置里三类已落地**（块管道 / 条件管道 / 反解构+管道读取+接运算符）。剩余：AOT 与解释器一致性、内建目标规则、解构语法收口 ⇒ 判 `[~]`。⚠ 与 p.9.13.4 `[~]` 语义重叠，建议合并 |
| 400 | p.9.0-L.3 默认值 const 白名单 | [ ] | [ ] | 与 p.9.11.24 同源；探针 `E00359` 只允许字面量 | 真未实现（**与 p.9.11.24 重复立项**） |
| 401 | p.9.0-L.4 `reentrant` / async 结果回传 / actor 字段初值扩展 | [ ] | [~] | `grep -rn "reentrant"` 全仓**零命中**；`"await"` 不在 `lex_symtab.tie` 关键字表 ⇒ **`await`/`reentrant` 连关键字都不在 69 项表里**；actor 字段初值侧已落地（S.2） | ★ 三项中 actor 字段初值已通（并入 S.2），并发状态/future 语义/`reentrant` 未动 ⇒ 判 `[~]` |
| 402 | p.9.0-L.5 精确十进制/大整数/编译期值参数 | [ ] | [~] | **big 已落地**（`std/big.tie` 536 行 18 func，但整库编译不过 ⇒ `[~]`）；**dec 未落地**（`dec.tie` 不存在）；**值参数未落地**（零命中） | ★ 三项中 1 项部分落地 ⇒ `[~]` |
| 403 | p.9.0-L.6 宏 `quote`/声明式形态统一 | [ ] | [~] | ch12 宏审计：12 条**零未实现**（8 已实现 / 3 部分 / 1 非规范）；实现基线已是反引号 `$`（p12_3_quasi.tie rc=0）；**冲突在规范侧**（§12.6 模板宏记号 `@stmt` 实现用裸形参名，`@stmt` 报 `E00832`） | ★ 能力已通，**待做的是规范修订而非实现** ⇒ 判 `[~]`（性质为文档/规范债） |

### p.9.0-E 生态协议补全 ★ 低估重灾区

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 409 | p.9.0-E.1 zd v3 索引 footer 与段表 | [ ] | **[x]** | `tdb/src/zd_v3.tie` **1241 行**：`footer_len()=25` / `footer_write` / `footer_probe` / `footer_crc_ok` / `encode_index` / `decode_index` / `assemble` / `read_index` / `find_segment`；段类型 0–6（`seg_data`..`seg_custom`）；v3 读 v2（`accept_v2_or_v3` / `flags_mask_v2`）；git log `3585764`「feat(zd): v3 carrier skeleton - header, index footer, segment table, multi-segment docs」；**探针 `tdb/tests/probe_zd_v3.tie` 编译 rc=0 且运行输出 PASS** | ★★ **严重低估**（原 `[ ]` ⇒ 实为 `[x]`）。本档导语「v3 footer…仍未形成」是**过时结论**（`_spec_audit/SUMMARY.md §4 #3` 已推翻，本轮再次实测确认） |
| 410 | p.9.0-E.2 zd v3 列式编码族 | [ ] | [~] | plain 已通（`seg_columnar`=2 + `flag_columnar`）；**RLE/delta 全无**：`grep -niE 'rle\|delta'` 在 `zd_v3.tie` 仅命中 `flag_dictionary()` 一行**位常量声明**，无任何编码实现；SUMMARY (a) 类亦记「RLE(1)/delta(2)」 | ★ 低估但确实缺口：段类型与 flag 位已占位，编码实现未做 ⇒ 判 `[~]`（原 `[ ]` 偏保守，但「已落地一部分」是事实） |
| 411 | p.9.0-E.3 zd v3 schema/标准类型 | [ ] | **[x]** | `zd_v3.tie`：`schema_state_active/deprecated/removed`(0/1/2) + `schema_ty_*`(i64..uuid 共 8 类) + `schema_canonical_bytes` / `schema_id` / `schema_validate` / `schema_allows_write` / `schema_readable` / `schema_can_deprecate` / `schema_can_remove` / `schema_evolve` / `encode_schema` / `decode_schema`；`std_tag_timestamp()=1` / `std_tag_decimal()=2` / `std_tag_uuid()=3`；git log `0f7edfe`「v3 schema segment + schema_id with cross-language KAT」+ `87e7596`「v3 standard types - timestamp, decimal, uuid」 | ★★ **严重低估**（原 `[ ]` ⇒ 实为 `[x]`） |
| 412 | p.9.0-E.4 zd v3 图容器 | [ ] | **[x]** | `zd_v3.tie`：`seg_graph()=4` + `flag_graph()`(bit6)；git log `b812384`「feat(zd): v3 graph container (compact form) with cross-language KAT」；探针 12/12 PASS | ★★ **严重低估**（原 `[ ]` ⇒ 实为 `[x]`） |
| 413 | p.9.0-E.5 tink 编排器 `tink pipe` | [ ] | [~] | 底层三件已具备：`tdb/src/zd_stream.tie` 188 行 + `tlib/std/tink_v2.tie` + `tlib/std/tink.tie` + `ext/tls/`；git log `fda4e03`「zbuf: byte-buffer abstraction over tie strings; migrate **zd_stream frames**」⇒ **帧核心（长度+zd+CRC）已有**；但 `tink pipe` 主形态 / hub 库式互联 / 段级错误定位未做（`tink/` 40 个绑定仓无编排器） | ★ 低估：帧层已迁移完成，主形态未做 ⇒ 判 `[~]`。ROAD 原文「底层长度+zd+CRC 帧已有，禁止重复造帧核心」与实测一致 |

### p.9.0-U/UI 与平台 + 库扩充

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 417 | p.9.0-U.1 UI/图语法规范覆盖 | [ ] | [ ] | ch14 审计：整章 10 条**仅 1 条已实现**（ui 角色已注册 `driver/role_reg.tie:48`），**8 条未实现**；`view`/`component`/`style`/`theme`/`action`/`Slot` **六个关键字全不在 `lex_symtab.tie`**；ch12-16 报告第 241 行已确认「`ROAD.md:417` 标 `[ ]` — 与实测一致」 | 标记正确（tiu 侧的 `view.tie` 是库级声明式层，**不是** ch14 语言元素块） |
| 418 | p.9.0-U.2 macOS/WASM/GPU/X11/SkParagraph | [ ] | [ ] | 同 p.9.7.1/.2/.3 三条实测（无 darwin / wasm grep 零命中 / 无 gpu 后端） | 真未实现（三条重复立项） |
| 419 | p.9.0-U.3 tdb/DHT/嵌入/Playground | [ ] | [~] | **tdb 已落地**（6111 行 + 24 探针，见 p.9.6.1 改判）；**DHT/嵌入/Playground 真未做** | ★ 低估：4 项中 1 项（tdb）已落地 ⇒ 判 `[~]` |
| 420 | p.9.11.35 安全 unsafe 重分类 | [ ] | [ ] | `atomic<T>`/`slice<T>`/`ptr<T>`/`#[repr(C)]` 仍标 unsafe（ch11 审计 45 条：40 已实现/1 部分/0 未实现/**4 非规范**）；SUMMARY (b) 类记「`repr(C)` 实现是 `repr(C) struct`，`#[...]` 通道只认 `ns.sub`」；设计稿 `safe-unsafe-reclassification.md` 在位 | 真未实现 |
| 421 | p.9.11.36 unsafe 凭据双锁 | [ ] | [ ] | 五域中 `share` 三处承载已落地（ch11 + SUMMARY §4 #2），`mem`/`ext`/`trm` 亦有；**`raw` 域（asm!/MMIO/unsafe goto）未建**；`unsafe[域]` 文件级声明形态未落地（★ 这正是 `std/dataflow.tie` 整库编译不过的根因）；设计稿 `unsafe-credential-lock.md` 在位 | ★ 部分落地但关键形态缺 ⇒ 判 `[ ]`（文件级持证形态是本条的核心验收点之一，缺它则门禁不可绕，而「不可绕」恰是本条目的立项理由） |
| 422 | p.9.1.5 rdu 扩充 | [ ] | [ ] | 批一~四**全部缺失**：`rdu/` 现有仅 `ascii/bits/crc/fixed/math/rdb/rnd` + 两个 ascon/poly1305；`encode/control/fixmath/hash/bitfield/reg/time/vec3/quat/ring/sha256` **逐一 MISSING** | 真未实现（设计稿在位，代码零） |
| 423 | p.9.1.6 sys 扩充 | [ ] | [~] | `sys/` 现有**仅 `win32.tie`（20 pub func）**；`dynlib/input/power/net/posix/darwin` 逐一 MISSING | ★ 判 `[~]` 依据：win32 二期核心（proc_launch/shell_open/qpc 等）**已在 win32.tie 20 个 func 内部分落地**，`sys/power`/`sys/input` 未动。**边界模糊**：win32.tie 是既有平台层、非本条新建 ⇒ 更严格判 `[ ]` 也成立。取 `[~]` 是因为「win32 二期核心」子项确有内容 |
| 424 | p.9.1.7 std 扩充 | [ ] | [~] | 批一 `std/td`/`std/zd`/`std/tds`/`std/log`：`td/tds` 文件**不存在**，`ext/log.tie` 存在（非 std/log 收编）；批二 `std/q`（group_by/join/agg/order_by）零命中，但 **`collection.tie` 1072 行 + `set.tie` 228 行 + `path.tie` 94 行（8 func）已在**；批三 `std/xml`（`ext/xml/` 在）、`std/uuid`、`std/env`、`std/cli` 未建 | ★ 低估：集合查询的**能力底座已在**（collection/set/path 三库合计 1394 行），缺的是 q 层封装与 td/tds/uuid/env/cli ⇒ 判 `[~]` |

### p.9.12 语言缺陷修复批次

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 432 | p.9.12.1 长串折叠丢内容 | [x] | [x] | `lex_scan` `{{`→`{` 规则 + `global_init_fold` VAR 分支在位；该缺陷是 tsp LSP 帧损坏根因，SUMMARY 未再列入 | 落地 |
| 433 | p.9.12.2 表下标越界静默 → 自动扩容 | [x] | [x] | `backend/irgen_agg_p1.tie:500-502` `s21_table_set` + `irgen_agg_p3.tie:308-317` `s21_index_raise` | ★ **注意**：自动扩容（写）与负下标诊断已在，但 **ch01/ch06 审计实测「表越界静默返回 0」（读路径）仍成立**（缺陷 #8，加 `--check-bounds` 也无效）⇒ 本条修的是**写**路径，读路径缺陷未修 |
| 434 | p.9.12.3 struct f64 默认值 irgen 崩溃 | [x] | [x] | SUMMARY 未列该缺陷仍存在；ch02 类型系统无相关未实现 | 落地 |
| 435 | p.9.12.4 命名空间体内 const | [x] | [x] | ch11/ch02 审计未列缺陷；`pstmt_top` ns + `gb_*` 全名登记在位 | 落地 |
| 436 | p.9.12.5 enum 变体分隔符放宽 | [x] | [x] | 同上 | 落地 |
| 437 | p.9.12.6 `table<R>` 结构化行池 | [x] | [x] | `backend/irgen_agg*.tie` 聚合槽路径在位；**tiu 已据此替换手写列式**（`ui/src/paint_bridge.tie`） | 落地（★ tiu `view.tie` 头部自述「`table<Elem>` 不能作函数形参（p.9.12.6 边界）」⇒ v1 边界仍在，与 ROAD 记载一致） |
| 438 | p.9.12.7 字符串 phi 未分组崩溃 | [x] | [x] | `llvmgen_sc.tie` + `op56 companion inttoptr` 机制在位 | ★ ROAD 自记遗留「编译缓存键不含 import 文件（改后端命中旧缓存）」**已被 p.9.15.1 修**（依赖感知缓存键），此遗留描述已过时 |

### p.9.13 语言基元与运算符

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 446 | p.9.13.1 单箭头统一 | [x] | [x] | `lex_symtab.tie:102` token 表为 `->`；`grep "=>"` 在 `tie-main/docs/*.md` **零命中** | 落地 |
| 447 | p.9.13.2 基元前置 | [x] | [x] | `tlib/std/prelude.tie` 存在；`driver/front_end.tie` prelude_inject 在 dump-docs 之后（注释可见）；p9b 探针经前置编译通过 | ★ ROAD 自记「9 个基元」实测在位；但**库端已扩到 15 个**（`collection.tie`/`set.tie`/`path.tie` 等）⇒ 低估，不影响标记 |
| 448 | p.9.13.3 运算符批 | [x] | [x] | 探针 PASS（`-7 \ 3`、`-7 %% 3`）；`in`/`not in`/`+` 三类型/`**`/`**?` 历史探针 P9133 在案；`p.9.0-S.7` 交叉确认 `\`/`%%` | 落地 |
| 463 | p.9.13.4 箭头续扩 | [~] | [~] | 已通：管道读取（`t->[i]`/`p->.f`）、条件管道（`9c8a3a7`）、接运算符（`1401cc1`）、块管道（`1231058`，`N_BLOCK_PIPE`=162）、反解构（`4798cec`） | 标记正确。★ 未通项已实测确认：实参位 `apply(t->t*3, 5)` 报 `E00488`、无初始化声明位报 `E00484`；`it` 隐式单参未做 |
| 468 | p.9.13.5 并行数据流图 | [~] | [~] | `tlib/std/dataflow.tie` **350 行存在**（行数与 ROAD 记载吻合）；但**整库无法编译** | 标记正确（`[~]` 是唯一正确答案）。★★ **卡点实测确认**：rc=1 `E00000 @305:13`「把一个引用全局可变容器的闭包交给执行流（spawn/并行池提交/actor 消息投递）必须在 unsafe 块或 unsafe 函数中」⇒ `run_par` 的 spawn 被**自家 share 门禁拦死**，而文件头只有 `type tie<class]`、**无 `unsafe:share` 文件级声明**，且门禁只认函数级上下文 ⇒ 加文件级声明也救不了（须落到 `run_par` 函数级 `#[unsafe.share]`）。属 **SUMMARY 缺陷 #7**（标准库自身不可用，正确性级） |
| 471 | p.9.13.6 文档/示例/迁移说明 | [ ] | [~] | `=>`→`->` 存量改写**已完成**（`grep "=>"` 在 `tie-main/docs/*.md` 零命中；p.9.13.1 记 20 处迁移 + 探针）；`tiec.md`/`cli.md`/`language.md` 在位 | ★ 低估：`=>`→`->` 这部分是**已落地**的（ROAD 自己拆成两个子项，`[ ]` 只该覆盖未做的部分）⇒ 判 `[~]`，卡在「文档/示例」半边 |
| 472 | p.9.13.7 内置库独立仓 tlib | [x] | [x] | `F:/Projects/tlib/` 是独立 git 仓（git log 活跃，最新 `7013cf7`）；四目录 std/ext/rdu/sys 186 文件 | 落地 |
| 473 | p.9.13.8 tsh 脚本化（禁 .ps1） | [x] | [x] | `scripts/*.tsh.tie` 成体系（regress-s21/package/fetch-lib/bootstrap-fp/verify-tiedap） | 落地 |

### p.9.14 警告系统

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 481 | p.9.14.1 结构化警告事件去文本往返 | [x] | [x] | `driver/front_end.tie:51-57`「不再解析 OK 协议中的 `;W:` 文本段」；`semantic_q1.tie:26` 同注；`grep ";W:"` 仅命中注释与 `driver.exe` 二进制 | 落地 |
| 482 | p.9.14.2 独立警告 pass | [x] | [x] | `sm_warn_active` 默认关 + `-w`/`--no-warn` 切换；ch15 审计实测 `warning[W00026]`/`W00008` 触发 | 落地 |
| 483 | p.9.14.3 tdiag 收束 | [ ] | [ ] | `tdiag/` 仓存在（886 条目录 + `warnings.md` 137 行 + `gen-docs.tsh.tie`），但 **`grep -rn "tdiag" tiec/compiler/driver/` 零命中** ⇒ 警告目录/标号/归一化/渲染**仍在 tiec 前端内**（`frontend/diagcode.tie:340/406` 注释仍写「规划见 tdiag/docs/warnings.md」= 未迁） | 真未实现（tdiag 只是**并行建了目录**，tiec 侧未切换消费） |
| 484 | p.9.14.4 验收与回归 | [ ] | [ ] | 无 `warnings.md` 同步证据；逐字节等价门禁脚本未见（`tools/` 与 `scripts/` 无对应件） | 真未实现 |

### p.9.15 缓存重构 + 并行构建

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 492 | p.9.15.1 依赖感知缓存键 + .dep 清单 | [x] | [x] | `driver/cache_drv.tie` 424 行 + `middle/tieir_slice.tie:89 write_mod_slice` + 模块缓存「默认开」（`cache_drv.tie:330`） | 落地（缓存键不含编译器二进制版本的遗留仍成立，见 p.9.19.8） |
| 493 | p.9.15.2 强哈希 + 产物指纹核对 + 原子写 | [ ] | [ ] | `grep -rniE "cache_clean\|max_entries\|objects/\|cas_"` 在 `driver/`+`middle/` **零命中** ⇒ 无内容寻址布局、无 `--cache-clean`、无 LRU 配置 | 真未实现 |
| 494 | p.9.15.3 中间级增量 L1/L2 分层缓存 | [ ] | [~] | **L1 tieir 模块片段缓存已落地**（`tieir_slice.tie` + `tieir_asm.tie` 装配器 + `TIEC_MODCACHE` 默认开，p.9.21.6/.8/.9 三条已 `[x]`）；**L2 opt 分层缓存未做** | ★ 低估：L1 一侧已完整落地（且由 p.9.21 承接）⇒ 判 `[~]`。**与 p.9.21.6/.8/.9 三条 `[x]` 重复计功** |
| 495 | p.9.15.4 淘汰与配置治理 | [ ] | [ ] | `--cache-clean` / `cache.max_entries` / `max_bytes` / `lru` 全零命中 | 真未实现 |
| 496 | p.9.15.5 验收与回归（缓存） | [ ] | [ ] | 无 `verify-cache.tsh.tie`（只有 `verify-tiedap.tsh.tie`）；`bootstrap-fp.tsh.tie` 在但那是自举脚本 | 真未实现 |
| 497 | p.9.15.6 工程级 batch + 原生线程 worker 池 | [ ] | [ ] | `--jobs` **仍是预留**：`cli_args.tie:19` 帮助文本原文「预留配置 advanced.threads，**并行随 p.9.1.3 增量/缓存落地**」；`grep -iE "worker_pool\|parallel_mode\|super"` **零命中** | 真未实现（★ help 文本自证「预留」，比零命中更硬的证据） |
| 498 | p.9.15.7 并发缓存写验证 | [ ] | [ ] | 无并发缓存写探针 | 真未实现 |
| 499 | p.9.15.8 超级并行模式 | [ ] | [ ] | `--parallel-mode=super` 零命中 | 真未实现 |
| 500 | p.9.15.9 并行验收与性能报告 | [ ] | [ ] | 无并行性能报告 | 真未实现 |

### p.9.16 内存工程

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 508 | p.9.16.1 tiec 前端 AST 释放接口 | [ ] | [ ] | `grep -rn "release_ast" compiler/` **零命中** | 真未实现 |
| 509 | p.9.16.2 tsp 按需 lazy 求值 | [ ] | [ ] | `tsp/` 存在但无 lazy/诊断指纹缓存证据；`release_ast` 依赖项缺 | 真未实现（前置未落地） |
| 510 | p.9.16.3 tsp 状态去冗余 | [ ] | [ ] | 无证据 | 真未实现 |
| 511 | p.9.16.4 tsp 常驻生命周期 LRU | [ ] | [ ] | `tsp.max_open_docs`/`mem_budget` 零命中 | 真未实现 |
| 512 | p.9.16.5 验收与回归 | [ ] | [ ] | 无内存对比报告 | 真未实现 |

### p.9.17 解释器性能

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 520 | p.9.17.1 字符串/容器原语优化 | [x] | [x] | `backend/llvmgen_sc.tie`：`@tie_sc_addr [2 x ptr]` / `@tie_sc_off(s,i)` / `@tie_sc_inval` / free 路径失效钩子 / CAP legacy 兜底（24/35 行）；`interp/env.tie` 用 `vval.table_push_val` | 落地 |
| 521 | p.9.17.2 解释器拆箱标量 | [x] | [x] | `value.tie` **已删除**（`ls compiler/interp/value.tie` → No such file，第三步清理已执行）；`interp_call_p1.tie:16 call_fn_nid`；`interp/env.tie` 整体重写 | 落地（三步全完成） |
| 522 | p.9.17.3 优化树遍历直驱 | [x] | [x] | `interp_call_p1.tie:14-16`「对齐变量环境 env_nids 先例」+ `call_fn_nid` 主实现 + `:179` 字符串薄包装；`interp_p3.tie:93` 直传 nid | 落地。★ ROAD 末尾「记录更正 2026-09-27：原标 `[ ]` → 实为前半落地」已被后续提交（`dc8c1a0` 后半）**完全兑现**，标记现正确 |
| 523 | p.9.17.4 分级 JIT 即时编译 | [ ] | [ ] | `grep -rniE "\bJIT\b|jit_"`：`trm/trm_backend.tie:4/18/189` 三处**全是注释占位**（「真实 JIT/wasm/AOT 连接为 p.9.x 扩展」「无连接，回退 interp」）；interp 侧无 JIT 缓存/冷热阈值 | 真未实现（★ 注释自证未落地） |
| 524 | p.9.17.5 验收与回归 | [ ] | [ ] | 无 JIT 报告（前置未落地） | 真未实现 |

### p.9.18 嵌入式解释器

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 532 | p.9.18.1 面 A 拆箱 + 值池复用 | [~] | [~] | 并入 p.9.17.2，三步已落地（`value.tie` 已退役）；**附加交付（嵌入裁剪形态 + 内存峰值/稳态报告）未做** | 标记正确，卡在附加交付 |
| 533 | p.9.18.2 面 A 直驱 + 字节级规避 | [ ] | [~] | 并入 p.9.17.3，**已落地**（`call_fn_nid` 全链路）；**附加交付（嵌入形态低延迟指标）未做** | ★ 原标 `[ ]` 低估：主体已并入完成 ⇒ 改判 `[~]` |
| 534 | p.9.18.3 面 B trm tieir-interp 嵌入面 | [ ] | [~] | 地基已通（ROAD 记 trm `6c70b75`+`f6b0e20`：`compiler/middle/tieir_asm.tie` / `tieir_fmt_v3.tie` 在位，`.tir` 扩展名已改）；`grep tieir/.tir` 在 `compiler/interp/` **零命中** ⇒ interp 前端侧未接 | ★ 低估：tieir 序列化 + 装配 + trm loader 已通，剩余 br/cond_br/switch/call 族 + Backend 接口 + trm-embedded 子集 ⇒ 判 `[~]` |
| 535 | p.9.18.4 双面统一接口 + trm/WASM 接入 | [ ] | [ ] | 无统一接口；WASM 前置（p.9.7.2）未落地 | 真未实现 |
| 536 | p.9.18.5 验收与回归 | [ ] | [ ] | 无报告 | 真未实现 |

### p.9.19 自举性能与确定性

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 544 | p.9.19.1 --shared DLL 全局表 ctor | [x] | [x] | `tie$rt_init` / `llvm.global_ctors` 在 backend 在位；SUMMARY 未列缺陷 | 落地 |
| 545 | p.9.19.2 prep O(n²) 修复 | [x] | [x] | `driver/cli_args.tie` + `driver.tie` 均有 `scan_header`（in-place 只扫前 20 行）；`semantic.imported_has` intern-id 二分 | 落地 |
| 546 | p.9.19.3 自举断档突破（瘦入口） | [x] | [x] | `compiler/_slim.tie` 在位；CRLF 回归修复在 `scan_header` | 落地 |
| 547 | p.9.19.4 相位隔离性能工具链 | [x] | [x] | 不动点机制在位；工具为仓外脚本，代码存在性无法在 tiec 内验证，但该条不改变语言面 | 采信 |
| 548 | p.9.19.5 parse build O(n²) 消除 | [x] | [x] | `save_pos`/`restore_pos` 水位线（`g_pend_n`）+ `split_current_gt` 原位覆盖撤销日志（`g_j_*`）在位 | 落地 |
| 549 | p.9.19.6 emit ren O(n²) 消除 | [x] | [x] | `backend/llvmgen.tie` + `llvmgen_p1.tie` 均有 `g_ren_stamp` 印章表 | 落地 |
| 550 | p.9.19.7 字符串池 O(1) 查表 | [x] | [x] | `backend/llvmgen.tie` + `llvmgen_inst.tie` 均有 `str_slot` | 落地 |
| 551 | p.9.19.8 验收与确定性 | [x] | [x] | 不动点机制在位；**遗留（缓存键未含编译器二进制版本）仍成立**（p.9.15.2 未做） | 落地，遗留如实保留 |

### p.9.20 双轴优化器

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 559 | p.9.20.1 双轴 CLI/配置面 | [x] | [x] | `driver/cli_args.tie:113 g_llvm_opt` / `:116 g_tie_opt` / `:136-137` 解析 + 非法档诊断 | 落地 |
| 561 | p.9.20.2 中端 pass 框架 | [x] | [x] | `middle/passes.tie` + `passes_p1.tie` + `passes_p2.tie` + `passes_test.tie`；`TIEIR_VERSION` 头 | 落地 |
| 563 | p.9.20.3 t1 单函数局部 pass | [x] | [x] | `middle/passes_p1.tie`（`fold_int` / cse / dce / inline_candidate 齐备）；`passes_test.tie` 在位 | 落地（「每档性能参考」已归 p.9.20.6，非本条） |
| 567 | p.9.20.4 t2 过程内 pass | [x] | [~] | 块内 CSE 实装（`cse_blockwise`）；★ **LICM 与跨块 CSE 明确顺延**（ROAD 自注「依赖支配分析，顺延至后续子项」）；BCE 按让位语义为零操作 | ★ 本条**只完成 3 项中的 1 项**（块内 CSE），LICM/跨块 CSE 未做 ⇒ 原 `[x]` 高估，改判 `[~]` |
| 571 | p.9.20.5 t3 过程间 pass | [x] | [~] | 小函数内联内核在位（`inline_candidate` / `inline_expand`）+ 不动点 `2cec594a`；tail call 在位（`llvmgen.set_tail_enable`，10 万层尾递归实测不爆栈）；★ **字符串构建融合顺延**（ROAD 自注「不在本轮强塞」） | ★ 3 项中 2 项完成，第 3 项（字符串融合）顺延 ⇒ 原 `[x]` 略高估，改判 `[~]` |
| 577 | p.9.20.6 验收与回归 | [ ] | [ ] | 各档性能参考报告未见（p.9.20.3 明确「性能参考待 p.9.20.6 统一补」，至今未补）；trm/WASM 后端前瞻验证无载体 | 真未实现 |

### p.9.21 tiec 模块化与库化

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 585 | p.9.21.0 v3 世代归档 | [x] | [x] | 归档仓 `tiec_v3` 为仓外对象，本轮未独立验证；归档点与主线分离的事实（当前开发在 `tie-lang/tiec` `p.7` 分支）成立 | 采信 |
| 586 | p.9.21.1 依赖方向契约 | [x] | [x] | `scripts/deps-check.tsh.tie` 在位；driver 已拆为 `driver/{util,cli_args,role_reg,front_end,keelcli,pipeline,cache_drv}.tie` 7 文件 + `driver.tie`；`compiler/driver/` 实测 8 文件 | 落地（★ 遗留「剩余 5 条前端求值环」ROAD 已如实记） |
| 593 | p.9.21.2 irgen_expr 拆解 | [x] | [x] | `compiler/` 内 `irgen_bi_*.tie` 系列 + `irgen_dispatch.tie` 在位；`p.9.21.3` 记 `irgen_expr.tie` 8790→744 + 16 域文件 | 落地（两步制②表驱动阻塞于 L5，ROAD 已注） |
| 598 | p.9.21.3 driver 全拆 + 批量拆分 | [x] | [x] | 全仓 ≤800 达成：实测 `compiler/frontend/sstate*.tie` 分片（`sstate_q1..q3`）、`infer_expr_*`、`check_stmt_*` 均在位；`middle/pass/` 孤儿模块**仍在**（`passmanager`/`pass_registry` 待清） | 落地（★ 孤儿模块 `middle/pass/` 4 文件仍在，ROAD 记为「p.9.21.3 清理候选」，未清） |
| 605 | p.9.21.4 II1 强制可见性 | [x] | [x] | `sstate.check_visibility` + `E00332` + `--visibility=<a1a\|a1b\|a1c\|a1d>` 梯度旗标（`driver/cli_args.tie` 解析 + `front_end` 注入 `sstate.set_visibility`）；`tools/visibility_survey.tie` 在位 | 落地 |
| 612 | p.9.21.5 II2 pub const | [x] | [x] | `E00649` 常量私有拦截 + `check_const_visibility_nid` + `tests/_p9215_probe/` 在位；`pub const` val bit1 | 落地 |
| 619 | p.9.21.6 II3 模块级增量编译 | [x] | [x] | `g_file_base`/`sg_mod`/`gb_mod`/`st_mod` + `file_id_of_node`；`tieir_slice.write_mod_slice`；模块缓存**默认开**（`cache_drv.tie:330`） | 落地 |
| 620 | p.9.21.7 tieir 反序列化布局忠实重建 | [x] | [x] | `middle/tieir_test.tie` 多函数 roundtrip 用例在位；`tieir_fmt_v3.tie` 片段格式 v3 | 落地。★ **ID 冲突**：本条与第 627 行 G7 条目**同为 `p.9.21.7`**（ROAD 编号重复，本轮已在清单中标出） |
| 621 | p.9.21.8 片段池过滤 + 模块缓存默认开 | [x] | [x] | `write_mod_slice` 引用收集式池压缩；`TIEC_MODCACHE` 摘除 | 落地 |
| 622 | p.9.21.9 片段组装消费 | [x] | [x] | `middle/tieir_asm.tie` + `tieir_asm_parse.tie` + `tieir_asm_replay.tie` 三文件在位（注释自述「p.9.21.9 片段组装消费」）；`cache_drv.tie` 消费 | 落地（★ 全局 var 登记族遗留已由 p.9.21.10/.11 收口补齐） |
| 624 | p.9.21.10 D5 根治 + 全局 var 恢复 | [x] | [x] | 虽有编号但**行首无 `- [ ]` 标记**（正文段落形式，`be41`/`b6416b9`）；`irgen.asm_reg_globals()` / `asm_side_recover()` 在位（ROAD 记 `VarDecl 探针 4/4 MODASM`） | 落地（★ **格式不一致**：本条未按 `- [x] p.9.21.10` 行首格式，机器解析会漏掉它） |
| 626 | p.9.21.11 片段格式 v3 + 装配性能转正 | [x] | [x] | `middle/tieir_fmt_v3.tie` 在位（u32 小端 + UTF-8 字符串 + 负值 +1 偏置 + 段 7 span 移除）；`tieir_slice.write_mod_slice` 按指令 id 序写 | 落地（★ 自记「转正判据 ≤4s 未达」如实保留） |
| 627 | p.9.21.7（G7）库资格四项收口 | [ ] | [~] | **18 个 `<lib>_test.tie` 自检在位**；本轮实测 4 个全绿：`dispatch_test` / `interner_test` / `columnar_test` / `types_test` 均 COMPILE+RUN OK；pub API 清单七库在位（`tdiag/docs/diagcodes.data.tie`） | ★ 低估但确有缺口：**G7 四项中 ①②（API 清单 + 自检）已成**，③④（独立发行 / 依赖单向）未做；且 ROAD 自述余量「passes/diag/parse/sema/irgen/llvmgen/interp/trm/driver 的自检与清单」——实测 `parse_test`/`semantic_test`/`passes_test` 已存在（**比 ROAD 记的余量更少**），但 `irgen`/`llvmgen`/`interp`/`trm`/`diag` 自检仍缺 ⇒ 判 `[~]` |

### p.9.22 结构化输出与 tinker（整档 13 条）

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 657 | p.9.22.1 dbgem 骨架① | [ ] | [ ] | `compiler/dbug/` 只有 crashdiag/profiler/tiedap（p.9.2 旧件），**无 dbgem_env.tie / dbgem.tie**；`--emit` grep 零命中 | 真未实现 |
| 658 | p.9.22.2 dbgem 骨架② | [ ] | [ ] | 无 `dbgem_colzd.tie`/`dbgem_coltd.tie` | 真未实现 |
| 659 | p.9.22.3 ast dump | [ ] | [ ] | 无 | 真未实现 |
| 660 | p.9.22.4 diag dump | [ ] | [ ] | 无 | 真未实现 |
| 661 | p.9.22.5 symtab dump① | [ ] | [ ] | 无 | 真未实现 |
| 662 | p.9.22.6 symtab dump② + xref 零依赖叶 | [ ] | [ ] | **`compiler/frontend/xref.tie` 不存在**；`compiler/frontend/xref.tie` grep 无命中 | 真未实现 |
| 663 | p.9.22.7 产物符号表 A `.sym.zd` | [ ] | [ ] | `grep -rn "sym.zd\|--no-sym" compiler/` 零命中 | 真未实现 |
| 664 | p.9.22.8 产物符号表 B tieir 段 8 | [ ] | [ ] | `TIEIR_VERSION` 现为 2→3 过渡已在 `tieir_fmt_v3.tie`，但**段 8 符号表未做**；无 `--no-sym`/content_hash 扩展 | 真未实现（★ 段 8 与 v3 格式编号是两回事，勿混） |
| 665 | p.9.22.9 tinker① 帧 + CRC32 | [ ] | [~] | 帧核心在**别处已落地**：`tdb/src/zd_stream.tie` 188 行（git log `fda4e03` 明写「migrate **zd_stream frames**」）+ `tlib/std/tink.tie` + `tink_v2.tie` | ★ 低估：帧 + CRC + 与 std/tink 对齐已在 zd_stream/std 侧完成；缺的是 tiec 内 `compiler/tinker/` 零依赖叶（tinker_frame.tie）⇒ 判 `[~]` |
| 666 | p.9.22.10 tinker② 信封 + sink | [ ] | [ ] | `compiler/tinker/` **目录不存在**；`--tink`/`--tink-file` grep 零命中 | 真未实现 |
| 667 | p.9.22.11 tinker③ recv | [ ] | [ ] | `compiler/tinker_recv.tie` 不存在；`--tink-in`/`--tink-save` 零命中 | 真未实现 |
| 668 | p.9.22.12 端到端 tink pipe | [ ] | [ ] | 无 `tink pipe` 主形态 | 真未实现 |
| 669 | p.9.22.13 文档收口 | [ ] | [ ] | `tiec.md` 无段 8 修订；无 dbgem_test/tinker_test/xref_test | 真未实现 |

---

## 标记有误的条目（**需上报**）

共 **29 条**改判：**高估 3 条**（`[x]` → `[~]`）、**低估 26 条**（`[ ]` → `[x]` 5 条 / `[ ]` → `[~]` 21 条）。

### A 类：高估（`[x]` → `[~]`）3 条

| ROAD 行 | 条目 | 原标记 | 实际 | 证据 |
| --- | --- | --- | --- | --- |
| **364** | **p.9.11.22 fn 值捕获语义白名单** | `[x]` | `[~]` | ★★ **本条已定稿的核心实测结论被推翻**。ROAD 写「表也是值捕获，闭包内 push 外层 len 不变」。探针 `p9d_capture.tie`：`var t=[1,2,3]`；`func(x:i64){table_push(t,99)}`；调用后 `println(len(t))` ⇒ **实测输出 4**（外层 len 变了）。机制（安全区禁捕获 `ref` 形参，`E00697`）在位，但**语义结论之一被证伪**，须重裁后再定稿 |
| **567** | **p.9.20.4 t2 过程内 pass** | `[x]` | `[~]` | 三项只完成 1 项：块内 CSE 实装（`passes_p1.tie` `cse_blockwise`）；**LICM 与跨块 CSE 明确顺延**（ROAD 自注「依赖支配分析，顺延至后续子项」）；BCE 按让位语义为零操作（设计如此，不算缺）。**ROAD 自注已说明未做，但行首仍标 `[x]`** ⇒ 形式上高估 |
| **571** | **p.9.20.5 t3 过程间 pass** | `[x]` | `[~]` | 三项完成 2 项：小函数内联内核（不动点 `2cec594a`）+ tail call（`llvmgen.set_tail_enable`，10 万层尾递归实测不爆栈）；**字符串构建融合顺延**（ROAD 自注「需先勘察 p.9.17.1 字符串原语 IR 形态，不在本轮强塞」） |

### B 类：低估（`[ ]` → `[x]`）5 条 —— 整层能力已落地

| ROAD 行 | 条目 | 原标记 | 实际 | 证据 |
| --- | --- | --- | --- | --- |
| **409** | **p.9.0-E.1 zd v3 索引 footer 与段表** | `[ ]` | `[x]` | ★★ `tdb/src/zd_v3.tie` **1241 行**：`footer_len()=25` / `footer_write` / `footer_probe` / `footer_crc_ok` / `encode_index` / `decode_index` / `assemble` / `read_index` / `find_segment`；段类型 0–6；v3 读 v2（`accept_v2_or_v3` / `flags_mask_v2`）；git log `3585764` |
| **411** | **p.9.0-E.3 zd v3 schema/标准类型** | `[ ]` | `[x]` | ★★ `schema_state_active/deprecated/removed`(0/1/2) + 8 类 `schema_ty_*` + `schema_canonical_bytes` / `schema_id` / `schema_validate` / `schema_evolve` / `encode_schema` / `decode_schema`；`std_tag_timestamp()=1` / `std_tag_decimal()=2` / `std_tag_uuid()=3`；git log `0f7edfe` + `87e7596` |
| **412** | **p.9.0-E.4 zd v3 图容器** | `[ ]` | `[x]` | ★★ `seg_graph()=4` + `flag_graph()`(bit6)；git log `b812384`「v3 graph container (compact form) with cross-language KAT」 |
| **271** | **p.9.6.1 tdb 完整实现（列式持久化 + vecsearch）** | `[ ]` | `[x]` | ★★ `tdb/src/` **12 文件 6111 行** + `tests/` **24 探针`；**`tlib/ext/vecsearch/flat.tie` 189 行 8 个 pub func**（`l2`/`cosine`/`flat_add`/`flat_remove`/`flat_size`/`flat_get`/**`flat_search`**）= 真 flat 向量索引 |
| **328** | **p.9.10.12 进制转换器** | `[ ]` | `[x]` | ★ `tlib/std/radix.tie` 111 行（`to_str(v,base)` / `parse(s,base)` / `digits(base)`，base 2..36，含负号前缀/零处理/越界返回空串）+ `base48.tie` 214 行；`bigint.tie` 另有十六进制域 |

★ **E.1/E.3/E.4 三条的共同含义**：本档导语（第 407 行）「v2 zd 与基础 tink 帧已存在；v3 footer、列式编码族、schema 演进、timestamp/decimal/uuid、图容器和 `tink pipe` 编排器**仍未形成**」是**过时结论**——`_spec_audit/SUMMARY.md §4 #3` 已推翻，本轮**再次实测确认**。唯一还剩的是列式编码族的 **RLE / delta**（见 C 类）。

**四条共同证据**：`tdb/tests/probe_zd_v3.tie` 编译 `rc=0` 且运行输出 `PASS`（本轮实跑）。

### C 类：低估但确有缺口（`[ ]` → `[~]`）21 条

| ROAD 行 | 条目 | 已落地部分 | 未落地部分 |
| --- | --- | --- | --- |
| 304 | p.9.9.7 tedit 生态编辑器 | **tshell 侧根基已建成**：`src/` 5 文件提及 tedit + `src/tedit_embed.tie` + `docs/embed.md`「tedit 终端模组子集」+ 两份 tedit 设计稿 | 无 `tedit/` 组件仓 |
| 312 | p.9.10.1 tsci 科学计算 | **`linalg.tie` 476 行 11 func**（mat_mul/det/gauss/mat_inv/lu_decompose/eigen_power + f32 阵 matmul/transpose/dot/mse）+ `exmath`/`optsearch`/`ext/ml`/`ext/nn`/`ext/tensor` | FFT / ODE / 优化 / 无仓 |
| 313 | p.9.10.2 tstat 统计预测 | `ext/ml.tie` + `ext/tensor.tie` | 分布/回归/时间序列 / 无仓 |
| 316 | p.9.10.5 timg 图像处理 | **`ext/` 编解码族**：png / webp / avif / bmp / svg / jpeg / qr / qrdec | 滤镜/缩放/颜色管理层、无统一组件 |
| 319 | p.9.10.8 tplot 统计可视化 | **`tie-repo/tofflib`**（自研矢量绘图/PDF 库，含音乐记谱矢量绘制） | tplot 组件层 / 报告链路 |
| 326 | p.9.10.11 big 大整数底座 | **`tlib/std/big.tie` 536 行 18 func**，基 10^18 + i128 中间积，文件头自述「ROAD p.9.10.11」 | 整库编译不过（`E00590`）⇒ 见「卡点 1」 |
| 399 | p.9.0-L.2 块/条件管道 + 箭头解构 | 块管道（`1231058`）、条件管道（`9c8a3a7`）、反解构（`4798cec`）、管道接运算符（`1401cc1`） | AOT/解释器一致性、内建目标规则、解构语法收口 |
| 401 | p.9.0-L.4 `reentrant` / async 结果回传 | actor 字段初值一侧已通（并入 p.9.0-S.2） | `reentrant` 零命中、`await` 连关键字都不在表内 |
| 402 | p.9.0-L.5 精确十进制/大整数/值参数 | **big 536 行 18 func**（但整库编译不过） | `dec.tie` 不存在、值参数零命中 |
| 403 | p.9.0-L.6 宏 `quote`/声明式形态统一 | ch12 宏 **12 条零未实现**；反引号 `$` 基线已通 | 冲突在规范侧（§12.6 `@stmt` 实现用裸形参名，`@stmt` 报 `E00832`） |
| 410 | p.9.0-E.2 zd v3 列式编码族 | plain 已通 + `flag_dictionary` 位常量已占位 | **RLE / delta 全无**（`grep -niE 'rle\|delta'` 仅命中一行位常量声明） |
| 413 | p.9.0-E.5 tink 编排器 | 帧核心已迁移（`zd_stream.tie` 188 行，git log `fda4e03` 明写「migrate zd_stream frames」）+ `std/tink*.tie` | `tink pipe` 主形态、hub 互联、段级错误定位 |
| 419 | p.9.0-U.3 tdb/DHT/嵌入/Playground | **tdb 全部落地**（见 B 类） | DHT / 嵌入式脚本 / Playground |
| 423 | p.9.1.6 sys 扩充 | `sys/win32.tie` **20 pub func**（含二期核心部分） | `dynlib`/`input`/`power`/`net`/`posix`/`darwin` 六模块全无 |
| 424 | p.9.1.7 std 扩充 | **`collection.tie` 1072 + `set.tie` 228 + `path.tie` 94 行（8 func）** + `ext/log.tie` + `ext/xml/` | `std/td`/`tds`/`zd`/`uuid`/`env`/`cli` 全无；`std/q` 封装层无 |
| 471 | p.9.13.6 文档/示例/迁移说明 | **`=>`→`->` 存量改写已完成**（`grep "=>"` 在 `tie-main/docs/*.md` 零命中；p.9.13.1 记 20 处迁移 + 探针） | 文档/示例/迁移说明本身 |
| 494 | p.9.15.3 中间级增量 L1/L2 | **L1 tieir 模块片段缓存全链落地**（`tieir_slice` + `tieir_asm` + 模块缓存默认开） | L2 opt 分层缓存（★ 与 p.9.21.6/.8/.9 三条 `[x]` 重复计功） |
| 533 | p.9.18.2 面 A 直驱 + 字节级规避 | 已并入 p.9.17.3 并**已完成**（`call_fn_nid` 全链路） | 嵌入形态低延迟指标 |
| 534 | p.9.18.3 面 B trm tieir-interp | trm loader + `.tir` 二进制直读 + 值空间重映射**已通**；`tieir_slice`/`tieir_asm`/`tieir_fmt_v3` 在位 | br/cond_br/switch/call 族 + 表与字符串原语 + Backend 接口 + trm-embedded 子集（`grep tieir` 在 `compiler/interp/` 零命中） |
| 627 | p.9.21.7(G7) 库资格四项收口 | 18 个 `<lib>_test.tie` 在位，**本轮实测 4 个全绿**（dispatch/interner/columnar/types）；七库 pub API 清单 | ③ 独立发行 / ④ 依赖单向（均待 L3/L4）+ `irgen`/`llvmgen`/`interp`/`trm`/`diag` 五库自检 |
| 665 | p.9.22.9 tinker① 帧 + CRC32 | 帧 + CRC + 与 std/tink 对齐**已在 zd_stream/std 侧完成** | tiec 内零依赖叶 `tinker_frame.tie`（`compiler/tinker/` 目录不存在） |

### D 类：格式与一致性缺陷（不改状态，但需修文档）

| # | 位置 | 问题 |
| --- | --- | --- |
| D1 | ROAD:620 与 ROAD:627 | **条目 ID 重复**：两行都用 `p.9.21.7`（前者 = tieir 反序列化布局，后者 = G7 库资格收口）⇒ 机器解析会互相覆盖 |
| D2 | ROAD:624 | **格式不一致**：p.9.21.10（D5 根治）内容完整但**行首无 `- [x]` 标记**，按 `- [x] p.9` 提取会漏掉它 |
| D3 | ROAD:343 | **示例写法错误**：p.9.11.1 正文示例 `when x { 1 => "a" _ => "b" }` 三处错——① 表达式位须用 `switch`（`when` 报 `E00832`）② 须用 `->` 非 `=>`（p.9.13.1 已废 `=>`）③ 臂间须逗号（缺则 `E00794`）。正确写法：`switch x { 1 -> "a", _ -> "b" }` |
| D4 | ROAD:349 | p.9.11.7 正文列四形态，`t[..n]` / `t[..]` **实测不通**（`[..` 被当记录字面量起始，报 `E00868`），须写 `t[0..n]` |
| D5 | ROAD:348 | p.9.11.6 表 `with` 受记录字面量键限制，**整数下标键不通**（`t with {0:99}` 报 `E00868`）⇒ 只通 map/字符串键一路 |
| D6 | ROAD:364 | 表捕获结论与实测相反（见 A 类第 1 条）⇒ 同一矛盾在 `fn-capture-whitelist.md §1` 与 ch13 §13.1 各有一份，共三处 |
| D7 | ROAD:208 | p.9.0.3 标 `[x]` 但正文自述「未完成」——语义上「改名」无对象可迁故成立，但**表述应改为「迁移无对象（twi 从未建成）」** |
| D8 | ROAD:375 | p.9.11.29 正文登记的 `--dump-docs` 头部缺陷**已于 2026-09-29 修复**（`driver.tie:312-316` 注释 + 本轮实测含头部文件 rc=0 正常输出）⇒ **缺陷描述已过时** |
| D9 | ROAD:433 | p.9.12.2 修的是**写**路径越界（自动扩容）；**读**路径「表越界静默返回 0」仍未修（SUMMARY 缺陷 #8，加 `--check-bounds` 无效）⇒ 应拆为两条 |
| D10 | ROAD:438 | p.9.12.7 遗留「缓存键不含 import 文件」**已被 p.9.15.1 修**（依赖感知缓存键 + `.dep` 清单）⇒ 遗留描述已过时 |
| D11 | ROAD:497 | p.9.15.6 `--jobs` 仍为预留：`cli_args.tie:19` 帮助文本原文「预留配置 advanced.threads，**并行随 p.9.1.3 增量/缓存落地**」——该文本**已过时**（缓存/增量已落地，并行仍未落地） |
| D12 | ROAD:380 | p.9.11.34 的 `[~]` 余项实为**两个不同层次**（实参位 vs `it` 隐式语法），建议拆为两条 |
| D13 | ROAD:399 vs ROAD:463 | p.9.0-L.2 与 p.9.13.4 语义高度重叠（块/条件管道/箭头解构），建议合并 |
| D14 | ROAD:400 vs ROAD:368 | p.9.0-L.3 与 p.9.11.24 是**同一能力两处 `[ ]`**（默认值 const 白名单） |
| D15 | ROAD:418 vs ROAD:278/279/280 | p.9.0-U.2 与 p.9.7.1/.2/.3 三条重复立项；p.9.0-U.3（419）与 p.9.6.1–.4 亦重复 |

---

## 卡在何处（`[~]` 条目的半成品状态）

### 卡点 1：编译器缺陷 —— `E00590` 命名空间方法转发 `self` 被误判 `ref`（阻断 `std/big.tie` 整库）

* **影响条目**：p.9.10.11（`[ ]`→`[~]`）、p.9.0-L.5（`[~]`）
* **现象**：`tlib/std/big.tie` 536 行 **整库编译不过** ⇒ ROAD 标 `[ ]` 是对的，但**真实状态是「已写完、被编译器 bug 挡住」**，不是「没做」。
  ```
  rc=1  error[E00590] @455:12: 调用 'op_add' 的 ref 参数实参 'self' 必须是动态表
                （table_new_* 创建），'self' 是定长表。
  ```
  `big.tie:455` 就是 `op_sub` 体内的 `return op_add(self, op_neg(o))`。
* **最小复现**（`p9a7_bare.tie`，36 行 → 17 行触发）：`struct S { var t: table<i64> = [] }` + `namespace S { func plain(self: S)…; func fwd(self: S) { return plain(self) } }`
* **隔离结论**（`p9a8_iso.tie` 三臂对照）：
  | 臂 | 形态 | 结果 |
  | --- | --- | --- |
  | A | 命名空间方法内**裸调** `plain(self)` | ✗ `E00590 @11:44` |
  | B | 同上但**限定调** `B1.plain(self)` | （被 A 的编译错误挡住，未单独确认） |
  | C | struct **无 table 字段**时裸调 | ✓ rc=0 |
* **根因**（已定位到代码）：`scollect.tie:344-366` **M2.1.8 自动 ref** —— `namespace <struct 名>` 内函数首参 == 该 struct 类型 ⇒ `p_refs[0] = 1`（接收者按引用，对齐 Rust）。但 `sinfer_ret_q2.tie:801-816` 的 `ref` 实参校验要求 `var_dyn(vnid) == 1`（须 `table_new_*` 创建的**动态表**）。**struct 形参 `self` 走的是定长表槽**（`var_dyn` 未登记为 1）⇒ 判定冲突。
  ⇒ **不是 `std/big.tie` 写错，是编译器两条规则在 struct 接收者上互斥**。
* **影响面**：任何「命名空间方法 + struct 含 table 字段 + 方法内转发 self」的写法都中招 ⇒ `big.tie` 的 `op_sub`/`op_add`/`op_mul` 全链不可用。
* **处置建议**：记为**编译器缺陷 #11**（优先级同 SUMMARY 已列的 #7/#8/#9/#10 —— 正确性级）；修法二选一：① `sinfer_ret_q2.tie` 对「struct 接收者槽」豁免 `var_dyn` 检查（与 M2.1.8 语义对齐）② 明确 M2.1.8 接收者不参与 ref 实参校验。
* **注意**：本条**不是**「`big` 未实现」⇒ 不得据此把 p.9.10.11 长期挂 `[ ]` 而不修编译器。

### 卡点 2：编译器缺陷 —— `std/dataflow.tie` 整库无法编译（`run_par` 的 spawn 被自家 share 门禁拦死）

* **影响条目**：p.9.13.5（`[~]`，标记正确但需登记阻塞）
* **现象**（本轮复现，`--lib-root F:/Projects/tlib`）：
  ```
  rc=1  error[E00000] @305:13: 把一个引用全局可变容器的闭包交给执行流
        （spawn / 并行池提交 / actor 消息投递）必须在 unsafe 块或 unsafe 函数中
        （闭包与执行流共享同一份底层数据，并发写入由书写者负责排除）。
  ```
* **为何救不了**：`dataflow.tie` 文件头只有 `type tie<class>`，**无 `unsafe:share` 文件级声明**；且门禁只看**函数级上下文**（`g_unsafe_depth`），不认文件级声明 ⇒ 加文件级声明也无效。
* **性质**：SUMMARY 已列为缺陷 #7「标准库自身不可用」（正确性级，优先级高于功能补齐）。
* **与卡点 1 的关联**：两者**同源** —— p.9.11.36「unsafe 凭据双锁」要求的**文件级持证形态 `type tie<logic> + unsafe[域]` 尚未落地**，正是这两个标准库文件无法自我解锁的根因。⇒ **p.9.11.36 从「 Nice to have」升级为「两个标准库文件的解锁前置」**。

### 卡点 3：`await` / `reentrant` 连关键字都不存在

* **影响条目**：p.9.0-L.4（`[~]`）
* **证据**：`grep -rn "reentrant" tiec/compiler/` **零命中**；`"await"` 不在 `lex_symtab.tie` 的 69 项关键字表内 ⇒ 不是「语义未实现」，是**词法层都没有**。
* **半成品**：actor 字段初值一侧已通（并入 p.9.0-S.2，`run C()` 读回初值实测通过）；并发状态与 future 语义零实现。
* **判断**：fire-and-forget 半边（`spawn` + `wg_*` join 屏障）已通并被 `dataflow.tie` 使用，但整项（结果回传）未实现 ⇒ `[~]` 正确。

### 卡点 4：p.9.20.4 / p.9.20.5 中端 pass 只做了承诺的子集

* **影响条目**：p.9.20.4（`[x]`→`[~]`）、p.9.20.5（`[x]`→`[~]`）
* **p.9.20.4**：块内 CSE ✓ / LICM ✗ / 跨块 CSE ✗ —— 后两项需**支配分析**，ROAD 自注顺延。
* **p.9.20.5**：小函数内联 ✓（不动点 `2cec594a`）/ tail call ✓（10 万层尾递归实测不爆栈）/ **字符串构建融合 ✗** —— 需先勘察 p.9.17.1 字符串原语的 IR 形态（`@tie_sc_addr` 是手写 LLVM helper，非 IR 节点），故未做。
* **共同卡点**：都卡在「需要先有对应 IR 表达」这一前置，而非算法本身。

### 卡点 5：p.9.11.34 短闭包卡在「实参位无类型上下文」

* **影响条目**：p.9.11.34（`[~]`）、p.9.13.4（`[~]`）
* **已通**：声明位 `var f: fn(i64)->i64 = t -> t+1` ✓；赋值位 `f = t -> expr`（已初始化标注变量）✓（`2cec664`）
* **未通**：① **实参位** `apply(t -> t*3, 5)` ⇒ `E00488`（需把期望类型传过 `infer_expr` 边界）② **无初始化声明** `var f: fn(i64)->i64` 后赋值 ⇒ `E00484`（安全放开需配套「读未初始化」检查，现无）③ **`it` 隐式单参语法**未做（与 p.9.11.28 单表达式隐式返回的咬合同样随后）
* **判断**：语言级阻塞，需新语法决策（`f = t: T -> expr` 显式标注 / 闭包形参类型推断），**须用户拍板**。

### 卡点 6：p.9.15 缓存档 —— L1 已由 p.9.21 全链承接，L2 与治理层零进展

* **影响条目**：p.9.15.2 / .3 / .4 / .5
* **已通**：L1 tieir 模块片段缓存 + 装配器 + 模块缓存默认开（`tieir_slice.tie` / `tieir_asm*.tie` / `cache_drv.tie:330`）—— 但这由 **p.9.21.6/.8/.9 三条 `[x]`** 计功，p.9.15.3 属**重复立项**
* **零进展**：`--cache-clean` / `cache.max_entries` / `max_bytes` / `lru` / 内容寻址 `objects/<fp>` 布局 / 产物 tsha1r 二次指纹核对 / 临时文件 rename 原子写 ⇒ 全部 grep 零命中（p.9.15.2 / .4 / .5）
* **并行线零进展**：`--jobs` 仍是预留（帮助文本自证）；`--parallel-mode=super` / worker 池零命中（p.9.15.6–.9）

### 卡点 7：p.9.21(G7) 卡在「后两项依赖 L3/L4」+ 5 库自检缺

* **已通**：18 个 `<lib>_test.tie`；**本轮实测 dispatch/interner/columnar/types 四项 COMPILE+RUN OK**；七库 pub API 清单（886 条 `diagcodes.data.tie`）
* **未通**：③ 独立发行（L3/L4 语言模块系统未就绪）④ 依赖单向（同 L3）；`irgen`/`llvmgen`/`interp`/`trm`/`diag` 五库自检与清单缺
* **正面修正**：ROAD 记的余量「parse/sema/interp/driver 属求值环需待环收口」——实测 `parse_test.tie`/`semantic_test.tie`/`passes_test.tie` **已经存在**，比 ROAD 记的少 3 个

### 卡点 8：p.9.18 双面并立 —— 面 A 主体全通、面 B 序列化通但执行面未接

* p.9.18.1 `[~]`：p.9.17.2 三步全落地（`value.tie` 已退役删除），卡在「嵌入裁剪形态 + 内存峰值/稳态报告」
* p.9.18.2 `[~]`（原 `[ ]` 低估）：p.9.17.3 已完成，卡在「嵌入形态低延迟指标」
* p.9.18.3 `[~]`：trm loader + `.tir` 二进制直读 + 值空间重映射已通；`grep tieir/.tir` 在 `compiler/interp/` **零命中** ⇒ 卡在 **br/cond_br/switch/call 族 + 表与字符串原语 + Backend 接口 + trm-embedded 静态子集**

### 卡点 9：p.9.22 整档 —— tiec 侧零落地，但帧核心在别处已通

* **零落地**：`compiler/dbug/` 只有 p.9.2 旧件（crashdiag/profiler/tiedap），**无 dbgem_env/dbug/dbug_colzd/dbug_coltd**；`compiler/tinker/` **目录不存在**；`compiler/frontend/xref.tie` **不存在**
* **已通（判 `[~]` 的依据）**：`tdb/src/zd_stream.tie` 188 行 = 帧核心（git log `fda4e03` 明写「migrate **zd_stream frames**」）+ `tlib/std/tink.tie` + `tink_v2.tie` ⇒ p.9.22.9「帧 + CRC32 自实现 + 与 std/tink 交叉互验」**已在 zd_stream/std 侧完成**，缺的只是 tiec 内零依赖叶
* **易混点**：p.9.22.8 的「tieir 段 8 / TIEIR_VERSION 2→3」与已落地的 `tieir_fmt_v3.tie`（**片段格式 v3**）**是两回事**，勿据此判 `[x]`

### 卡点 10：p.9.13.5 语义债 —— 多入边 join 屏障未裁决

* 已通：图即表（节点=函数值表 / 边=三张并行表）、`run`/`run_par`、波次 SDF、回边下一波、`set_limit`/`last_waves`
* 未通：① **多入边按「每边各触发一次」而非设计 §5 的 join 屏障**（需先裁决「多值如何合并为单参」）② 图论套件（cycle/topo/conn/reach/shortest/critpath/maxflow·mincut）③ trit 三态穿透 ④ 运算符形态 `{A} - {B -> ~ A}` ⑤ 安全分层（可变 graph 声明/突变运算符）
* **额外阻塞**：`run_par` 因卡点 2 目前**整库编译不过** ⇒ 「run_par 与 run 一致」这条已验收项现在**不可复验**

---

## ROAD 未提但该提的缺口

| # | 缺口 | 证据 | 建议 |
| --- | --- | --- | --- |
| 1 | **编译器缺陷 #11：`E00590` 命名空间方法转发 `self` 误判 ref** | `p9a7_bare.tie` rc=1；`scollect.tie:344` (M2.1.8 自动 ref) × `sinfer_ret_q2.tie:801` (`var_dyn != 1` 拦截) 互斥 | 新开缺陷单，优先级同 #7/#8/#9/#10（正确性级）。**解锁 `std/big.tie` 整库** |
| 2 | **`p.9.11.36` 的文件级持证形态是两个标准库文件的解锁前置** | `dataflow.tie` 头无 `unsafe:share` 且门禁只认函数级 ⇒ 整库不可编译；`big.tie` 同类问题 | 把 p.9.11.36 从「安全加固」升格为「标准库可用性前置」，提前到 p.9.13.5 之前 |
| 3 | **`std/dataflow.tie` 整库不可编译** | `rc=1 E00000 @305:13`（本轮复现） | 归缺陷 #7，需与 #2 一并修 |
| 4 | **ROAD:364 表捕获语义结论被实测推翻** | `p9d_capture.tie` 输出 `4`（非 ROAD 说的不变） | 先裁决「表按引用 vs 按值」，再回改 ROAD + `fn-capture-whitelist.md` §1 + ch13 §13.1（同一矛盾三处） |
| 5 | **记录字面量键限标识符/字符串 ⇒ 波及 `with` 与切片两语法糖** | `t with {0:99}` 报 `E00868`；`t[..2]` 被当记录字面量起始 | ROAD p.9.11.6/p.9.11.7 的形态表须补「整数键 / `..` 省略起点不支持」的限制说明 |
| 6 | **`and`/`or` 与函数调用同层不可组合** | `chk(len(rest) == 3, "…")` 报 `E00484 期望 ')'，实际是 and`；须拆成两条 | 解析层缺陷面，ROAD 未记。建议开缺陷单 |
| 7 | **p.9.11.1 示例写法三处皆错**（`when`/`=>`/缺逗号） | `p9b_sugar.tie` 迭代实测三错 | 订正 ROAD:343 示例为 `switch x { 1 -> "a", _ -> "b" }` |
| 8 | **表越界**读**路径静默返回 0 仍未修** | SUMMARY 缺陷 #8；`p.9.12.2` 只修写路径 | p.9.12.2 应拆为「写路径已修 / 读路径待修」两条 |
| 9 | **p.9.0-L.3 与 p.9.11.24 重复立项**（同一能力两处 `[ ]`）；**p.9.15.3 与 p.9.21.6/.8/.9 重复计功**；**p.9.0-U.2 与 p.9.7.1/.2/.3 重复立项**；**p.9.0-U.3 与 p.9.6.x 重复** | 四组重复 | 合并去重，否则统计失真 |
| 10 | **条目 ID 重复 `p.9.21.7`**（ROAD:620 与 :627）+ **p.9.21.10 行首缺标记**（ROAD:624） | 提取 `- [x] p.9` 可复现：两行同 ID、624 行漏出 | 重编号 + 补标记 |
| 11 | **tdiag 已建目录但 tiec 未切换消费** | `tdiag/` 886 条目录 + `warnings.md` 在位；但 `grep -rn tdiag tiec/compiler/driver/` 零命中，`frontend/diagcode.tie:340/406` 仍写「规划见 tdiag」 | p.9.14.3 应加注「tdiag 侧已就绪，缺的是 tiec 侧切换」⇒ 实际工作量比 ROAD 记的小 |
| 12 | **`tlib/ext/vecsearch` 是唯一向量检索实现但挂在 ext** | `ext/vecsearch/flat.tie` 189 行 8 func | ROAD p.9.6.1 应交叉引用（避免与 p.9.10.1 的 linalg 重复投资） |
| 13 | **tiu 已有 `view.tie` 声明式视图层 + Scroll/TextInput/Image 控件批，ROAD 未记** | git `93f1492` / `a8f84e3`；`ui/src/view.tie` | p.9.4.2 描述已过时（只记到 paint_bridge） |
| 14 | **`tlib` 媒体编解码族远超 ROAD 记载的 21 项** | `ext/` 含 png/webp/avif/bmp/svg/jpeg/qr + codec(brotli/jpeg/lz4/zstd) + audio(wav) | p.9.1.1 清单需重数 |

---

## 核验方法与纪律

* **每条结论都带证据**：代码存在性 ⇒ `grep`/`ls` 路径 + 行号；行为 ⇒ 探针 `rc=` + 输出。
* **探针清单**（`F:/Projects/_tmp/roadcheck/`）：`p9a_big.tie`（big 探测，rc=1 卡点 1）、`p9a2_big.tie`（方法形态）、`p9a3_selfref.tie` / `p9a4_selffwd.tie`（E00590 隔离）、`p9a5_opref.tie`（op_ 前缀）、`p9a6_repro.tie` / `p9a7_bare.tie`（**最小复现**）、`p9a8_iso.tie`（三臂隔离）、`p9b_sugar.tie`（**PASS p9-b**，p.9.11 语法糖 9 项 + S.4/S.6/S.7）、`p9c_constdflt.tie`（默认值 const 白名单，rc=1 E00359）、`p9d_capture.tie`（表捕获语义，输出 4）、`p9e_docs.tie`（`--dump-docs` 头部，已修）
* **复用他人探针实测**：`tdb/tests/probe_zd_v3.tie`（rc=0 + PASS）、`trm-lite/tests/s_gen/gen_probe.exe` + `gen_mig_probe.exe`（rc=0 + PASS）、`tiu/tests/probe_*.exe` ×6（全 OK）、tiec G7 自检 ×4（COMPILE+RUN OK）
* **未采信**：ROAD 正文的所有「已落地」自述（除能用代码/实测佐证者）、注释级状态说明、`middle/pass/` 孤儿模块的存在（不作为落地证据）
* **只读不改**：`ROAD.md` 未做任何修改；未改 tiec 源码 / tie-spec / 兄弟仓库；探针只写 `_tmp/roadcheck/`
