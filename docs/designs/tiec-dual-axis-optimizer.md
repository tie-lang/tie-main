# tiec 双轴优化器设计 —— -l（LLVM/clang）× -t（tiec 中端）

*EN: tiec dual-axis optimizer design — -l (LLVM/clang) × -t (tiec middle-end)*

**日期** / Date: 2026-09-21 · **类型** / Type: 设计（定稿）
**依据** / Basis: 用户决策（2026-09-21 对齐：短长参数并存、默认 l2/t0、`-O` 硬移除、ROAD 排 p.9.20）
**关联** / Related: `docs/designs/tiec-parallel-build.md`（p.9.15 缓存键）·
`tiec/docs/2026-09-18-compile-perf-regression-diagnosis.md`（自举性能基线）·
`tie-main` 差距分析（中端零优化为最大内核缺口）· ROAD p.9.20

---

## 1. 背景与问题 / Background

现有 `-O0..-O3` 只映射到 **LLVM 侧**（`opt` 子进程档 + clang 代码生成档），
tiec 中端（tie-IR 层）**零优化**。两个结构性问题：

1. **语义混淆**：`-O` 名义上是"tiec 的优化级别"，实际全是 LLVM 的；
   用户无法表达"关 LLVM 优化但开 tiec 优化"（反之亦然）。
2. **后端不对称**：trm 字节码 / WASM 后端没有 LLVM 优化器——
   中端优化是它们未来唯一的优化层，需要一个与后端无关的开关面。

EN: The existing `-O0..-O3` only maps to the LLVM side (opt subprocess level +
clang codegen level); the tiec middle end (tie-IR layer) has zero optimization.
Two structural problems: ① `-O` is nominally "the tiec optimization level" but is
entirely LLVM's — users cannot express "LLVM optimization off, tiec optimization
on" or vice versa; ② backend asymmetry: the trm/WASM backends have no LLVM
optimizer — the middle end is their only future optimization layer, so the switch
surface must be backend-independent.

## 2. 双轴模型 / Dual-Axis Model

| 轴 | 参数 | 语义 | 落点 |
|---|---|---|---|
| **LLVM/clang 轴** | `-l <0-3>` | opt 子进程档 + clang 代码生成档（原 `-O` 语义原样平移） | toolchain.opt / link |
| **tiec 中端轴** | `-t <0-3>` | tie-IR pass 管道（新），挂 irgen 之后、llvmgen 之前 | middle-end passes |

- 优先级链不变：**CLI 显式 > config（含 profile 激活）> 默认**。
- 两轴独立组合，互不钳制（`-l0 -t3` 合法：LLVM 关、tiec 全开）。
- `--mem-limit`（>0）仅作用 l 轴（l3→l2 降档平移现状）；t 轴不受内存上限影响。

EN: `-l <0-3>` = LLVM/clang axis (opt subprocess + clang codegen, semantics of
the old `-O` moved verbatim). `-t <0-3>` = tiec middle-end axis (new tie-IR pass
pipeline, hooked after irgen, before llvmgen). Priority chain unchanged:
explicit CLI > config (profile-activated) > default. The two axes combine
freely (`-l0 -t3` is legal). `--mem-limit` affects only the l axis.

## 3. CLI 规格 / CLI Specification

| 形式 | 示例 | 说明 |
|---|---|---|
| 短参数（粘连） | `-l0` `-l1` `-l2` `-l3` / `-t0`..`-t3` | 主形式 |
| 长参数（= 赋值） | `--llvm-opt=2` `--tie-opt=3` | 可读别名，等价短参数 |
| 旧 `-O0..-O3` / 裸 `-O` | — | **硬移除**：报错并提示新用法（对齐 p.9.0 破坏性变更无兼容期纪律） |

- 非法值（`-l9`、`--tie-opt=x`）→ 诊断报错，退出码非 0。
- 不支持分离式（`-l 2`）——与 `-O2` 粘连传统一致，负例明确报错。
- 帮助文本同步更新。

EN: Short attached forms (`-l2`, `-t3`) are the primary form; long `= value`
aliases accepted; old `-O*` hard-removed with an error pointing to the new
flags (no compatibility period, aligned with the p.9.0 discipline). Invalid
values are diagnosed with a non-zero exit. Detached values (`-l 2`) are not
accepted.

## 4. 配置面 / Configuration

- config 顶层键：`opt` 拆为 **`llvm_opt`** 与 **`tiec_opt`**（旧 `opt` 键移除，
  出现即报错提示新键）。
- profiles：dev → `llvm_opt=0, tiec_opt=0`；release → `llvm_opt=2, tiec_opt=0`。
- 默认值：**`-l2 -t0`**（显式 CLI 未给时）。

EN: top-level config key `opt` splits into `llvm_opt` and `tiec_opt` (old key
removed with an error pointing to the new keys); profiles dev → l0/t0,
release → l2/t0; defaults l2/t0.

## 5. t 轴 pass 分期 / t-Axis Pass Tiers

| 档 | 内容 | 约束 |
|---|---|---|
| **t0** | 零 pass，irgen 产物直出 | 默认；自举不动点不变 |
| **t1** | 廉价单函数局部：常量折叠、代数化简、死值消除 | 确定性、单函数、线性 |
| **t2** | + 过程内：公共子表达式、循环不变外提、**边界检查消除**（`--check-bounds` 显式开启时让位） | 同上 |
| **t3** | + 过程间：小函数内联、tail call、字符串构建融合（sb 链） | 同上 |

**t 轴的独特价值**（与 LLVM 轴的分工）：①语言级信息只有 tiec 有（边界检查、
字符串模型、trit 语义）；②trm/WASM 后端无 LLVM 优化器，t 轴是它们唯一的
优化层；③分级可裁剪，与 p.9.17.1 字符串原语优化衔接。

EN: t1 = cheap intra-function locals (const fold / algebraic simplify / dead
value elimination); t2 = + intra-procedural (CSE / LICM / bounds-check
elimination, yielding to explicit `--check-bounds`); t3 = + inter-procedural
(small-function inlining / tail call / string-build fusion). Unique value of
the t axis: language-level info only tiec has; trm/WASM backends have no LLVM
optimizer; tiered and prunable.

## 6. 确定性硬门禁 / Determinism Gates

1. pass 集合与顺序**版本化固定**：同 (源码, l, t, target) → 输出逐字节恒等。
2. 缓存键：`O<level>` → **`L<level>` + `T<level>`** 两段（键变化 = 缓存一次性
   全失效，可接受）。
3. tieir 序列化（`--tieir-out`）单元头携带 t 级别。
4. 自举不动点：默认 l2/t0 下**不变**（`211b73e5`）；未来上调默认 t 档 =
   有意的不动点变更，须重录基线并在 ROAD 标注。
5. pass 实现禁用 Rust、纯 tie；禁止时间/地址/随机依赖。

EN: pass set & order version-pinned; cache key gains L/T segments; tieir
serialization carries the t level; the bootstrap fixed point is unchanged at
the l2/t0 default (any future default-t bump is an intentional fixed-point
change re-baselined in ROAD); passes are pure tie, no time/address/random
dependence.

## 7. 实施分期 / Implementation Stages

对齐 ROAD p.9.20.x：①CLI/配置面 + 缓存键（含 `-O` 移除）②中端 pass 框架
（管道挂点 + 注册 + t 门控 + tieir 头）③t1 ④t2 ⑤t3 ⑥验收（各档性能参考
报告 + trm/WASM 前瞻验证 + 回归不劣化）。

## 8. 决策记录 / Decision Record

| 决策点 | 结论（2026-09-21 用户拍板） |
|---|---|
| CLI 语法 | 短参数 + 长别名**并存** |
| 默认档 | **l2 / t0**（不动点不变） |
| 旧 `-O` | **硬移除**并报错提示 |
| ROAD 排号 | **p.9.20** 双轴优化器新档 |
