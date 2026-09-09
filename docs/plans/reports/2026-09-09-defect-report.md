# tie 缺陷 / 漏洞 / Bug 报告（2026-09-09 汇总）
# EN: tie Defect / Vulnerability / Bug Report (2026-09-09 consolidated)

> 状态 / Status: 汇总报告（修复追踪用，逐条完成后勾选）
> 来源 / Sources: ① Mantle p.0.1 ABI 冒烟实测（tie DLL → Java FFM）；② trm-lite README/CHANGELOG
> 已知限制（preview.3）；③ tie-main compiler/std 源码标注；④ docs/designs/concurrency-model.md 设计待决项。
> 分级 / Priority: P0=会造成数据错误/产物不正/已实测踩中；P1=能力缺失/未验证；P2=已文档化设计边界；待决=设计拍板项。
> 修复纪律 / Fix discipline: 每修一条以最小用例 + 回归语料闭环；编译器改动维持 tiec 二阶自举不动点；English commit。

---

## P0 · 高优（数据错误 / 产物不正 / 已实测踩中）

| # | 缺陷 Defect | 定位 Location | 修复方向 Fix direction | 复查勾选 Done? |
|---|---|---|---|---|
| 1 | tiec `--shared` 不自动链接 trm_lite.a（DLL 模式用内置 spawn/ch/wg 缺符号，实测需手工 `clang -shared` + trm_lite.a） | `compiler/driver.tie`（`link_shared` 未传 `g_used_trmlite`，仅 `link_exe` 传入） | link_shared 补同一 trm-lite 判定并传链参 | ☐ |
| 2 | 标量全局初值静默丢弃（`var g: i64 = 4` 实际为 0；表全局 `= []` 却正常） | 编译器 IR 期全局初始化（trm-lite README L158 已记录） | 全局标量初值正确落位（静态存储/运行时初始化）；补回归语料 | ☐ |
| 3 | 全局表字面量初始化受 IR 缺陷限制（只允许空表 `[]`；字面量表直接赋全局不被支持） | `compiler/proto/lexer.tie:327`、`compiler/proto/parser.tie:32`（空嵌套字面量 `[0 x i64]` 与 ptr 不符） | 修正空嵌套字面量 IR 类型生成 + 全局表静态初始化路径 | ☐ |
| 4 | 嵌套表复绑定缺陷（代码被迫扁平化为 table<i64> 规避） | tiec 表运行时/IR（trm-lite `core/gc/gc.tie:7` 注释为规避而扁平） | 复现最小用例 → 修嵌套表重绑定语义；事后允许回退扁平规避 | ☐ |
| 5 | 闭包字面量解析缺陷：`func() -> i64 {}` 在 var 初始化/实参位置历史性不稳，spawn 暂只能传命名函数 | parser/semantic（trm-lite CHANGELOG L269） | 复现 + 修闭包字面量位置解析；补 spawn 闭包语料 | ☐ |
| 6 | 混合表元素类型推断缺陷（`table_push(ref参数, v)` 误选 string 桥；同模块混合表 ref push 推断错） | std 规避密集：`std/collection.tie:33,138`、`std/sort.tie:17,27` | 统一 push 类型推断（按目标表元素静态类型而非值启发） | ☐ |
| 7 | 全局 `table<fn() -> i64>` 惰性 `= []` 重赋值缺陷（fn 元素路径崩溃） | trm-lite CHANGELOG L253 | 复现 + 修全局函数表重绑定 | ☐ |

EN / P0: 1) --shared link misses trm_lite.a (link_shared neglects g_used_trmlite); 2) scalar global initializer silently dropped; 3) global-table literal init limited by IR defect (empty nested literal [0 x i64] vs ptr); 4) nested-table rebind defect (code flattens to avoid); 5) closure-literal parsing defect in var-init/arg positions (spawn uses named fns); 6) mixed-table element type-inference defect (table_push picks string bridge wrongly); 7) global table<fn() -> i64> lazy re-assign defect.

## P1 · 中优（能力缺失 / 未验证）

| # | 缺陷 Defect | 定位 Location | 修复方向 Fix direction | Done? |
|---|---|---|---|---|
| 8 | wg_count 非内置（仅 wg_new/add/done/wait；ABI 冒烟被迫镜像计数） | tiec 内置表（wg 原语集） | 补 wg_count 观察内置 | ☐ |
| 9 | tie string 跨 FFM 返回布局未验证（冒烟以 i64 版本码替代 version()） | Java FFM ↔ DLL string 返回 | 设计并验证 string 返回 ABI（指针+长或 SSO 约定）；补跨语言探针 | ☐ |
| 10 | `const 全局表` 暂不支持（需 main 运行时创建，无法静态初始化） | `compiler/proto/semantic.tie:1374` | 决策：支持或报错文案更明确 | ☐ |
| 11 | json/yaml `\uXXXX` 仅支持 ASCII 码点，`\b \f` 无法构造 | `std/json.tie:32,288`、`std/yaml.tie:33` | 字符串构造原语放宽至任意码点 | ☐ |

EN / P1: wg_count not builtin (mirror count used); tie-string-return ABI across FFM unverified; const global tables unsupported; json/yaml \uXXXX ASCII-only.

## P2 · 设计边界（已文档化，暂按现状可跑）

* 复杂形态（import tl_runtime_ctx）函数参数 `fn()->i64` 不能跨 DLL 边界（导出面校验设计如此）——Java 侧需标量包装 shim 或独立进程形态（Mantle p.0.1.2 结论）。
* channel 非阻塞降级：ch_recv 空→0 / ch_send 队满→1；Go 阻塞语义需语言级挂起能力（trm-lite README L151）。
* channel 消息仅标量 i64（对象/表消息需 root 登记承载，p.6.5.8）。
* 协作抢占非 OS 硬抢占（gosched + 时间片 S_SLICE_LIMIT=8 之间不可打断）。
* 经典时序断言 demo（ctx_ws_demo 等）宿主噪声下偶发 FAIL（验收以确定性探针 + stdout 逐字节一致为准，非回归）。
* 精确根保守口径（任务 env 即根；未显式登根的运行期临时对象依赖无任务窗口）。
* tie 语言怪癖四条：to_string(bool) 输出 -1/0；单行块须以 `;` 结尾；顶层 table 全局须 `= []`；REPL v1 不支持 struct/enum/import/using/goto（`compiler/interp/interp.tie` 多处标注）。
* 多模块聚合 import 重编译受 LLVM opt 同模块 declare+define 冲突约束（tl_chan_lib 独立构件缓解）。
* 未完成特性（非缺陷）：driver 对 ui/db/port/cycle 角色文件「转交工具链」v0.1 未实现（driver.tie:1043-1051）。
* `std/tink_v2.tie:418`：stream 返回「拼接帧字节表」——无动态嵌套表构造的妥协点（协议无碍）。

EN / P2: fn()-param across DLL rejected; channel non-blocking degraded (0/1); scalar-i64 channel messages; cooperative (non-OS) preemption; legacy timing-assert demos host-noise flaky; conservative precise-root; four tie quirks (to_string(bool)=-1/0, `;` blocks, global table `= []`, REPL v1 gaps); multi-module import LLVM declare/define conflict; v0.1 role-file toolchains unimplemented.

## 待决 / 待实现（设计拍板后落地）

* actor `run` 的 1:1 线程入口 ABI（cb_ptr thunk）——concurrency-model 一期待实现点。
* 通用 `#[]` 属性解析器（#[macro] 兼容 + #[unsafe.x] + #[tag.x] 消歧）——三期。
* `reentrant` 默认关闭是否过严（纯数据 actor 是否自动开重入）——决策。
* `Mutex/RwLock` 是否随 `guard<share>` 进正式 API——决策。

EN / Open: actor-run thread-entry ABI (cb_ptr thunk); generic #[] attribute parser; reentrant default; Mutex/RwLock API.

## 防回归备忘（已修复记录）

* 标记栈缺陷（table_push 只追加不删除 → g_stack[g_sp-1] 语义错）已修复（trm-lite CHANGELOG L203），回归语料保留。
* tiec 自举二阶不动点（tiec 编译自身字节一致）是编译期改动回归门禁，改动后重验。
* O(n²) 教训：std 热路径禁逐位字符串拼接（`s = s + "x"`），改 string_builder/sb_append_byte 批量构建；复查 std 内残余拼接热路径。

EN / Regression: fixed mark-stack defect kept its corpus; tiec second-order self-host fixpoint gates compiler changes; O(n²) ban on per-char string concat in hot std paths.