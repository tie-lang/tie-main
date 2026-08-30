# TSHA1 u32 通道准备分析（u32-channel-prep，A5 掩码最小化）

- **日期**：2026-08-31
- **状态**：A5 核心已落地（分支 feat/tsha1-a5-mask，7ac6ada）；本文档量化掩码热点、证明 32 位
  不变量、分类剩余掩码，为 tiec 后端 u32 类型/向量化通道（perf-design §7）铺路。
- **关联**：[2026-08-30-tsha1-perf-design.md](./2026-08-30-tsha1-perf-design.md) §7 独立跟踪。

## 1. 背景与目标

perf-design §1 已实证：TSHA1 位平面 ring 数学（tadd2/tmul2/quant3 + 旋转 + 64 字节 trit 化）
在现 tiec 后端（i64 全量掩码、无 u32/向量化通道）下，每块成本 ≈ sha256 的 150×。§7 明确：
**位平面 32 位运算若获得 u32 类型与 SIMD 支持，TSHA1 每块成本可望趋近 sha256 同量级**。

"开拓道路" = 在 u32 通道落地前：
1. **A5 掩码最小化**（语义不变、KAT 零变更）：删除可证明高位为零的 `& 0xFFFFFFFF`——既是
   独立收益，也消除 u32 化时的冗余截断（u32 语义下这些掩码天然消失）。
2. **本文档**：量化掩码热点、证明 32 位不变量、给掩码分类、定 u32 后端落地路线。

## 2. 32 位不变量（核心论证，A5 删掩码的依据）

**不变量**：所有进入位平面数学（tadd2/tmul2/quant3/rotlane）的操作数恒为 32 位值（高位为 0），
且 lanes / S / Pw / h / IV / rcon 表在算法全生命周期保持 32 位。

证明链（std/tsha1.tie）：

1. **lane 初始化 32 位**（compress）：
   - `lanes[2*i] = h[i] & 0xFFFFFFFF`（h 每块经 `& 0xFFFFFFFF` 更新，见第 4 点）
   - `lanes[2*i+1] = rotlane(h[...], 7, half)`（rotlane → rr32/rrp16 内部 `& 0xFFFFFFFF`）
   - IV/计数器/末块：`(… ^ (iv & mplan)) & 0xFFFFFFFF`（mplan = 0xFFFFFFFF 或 0xFFFF）
2. **lane 写入路径全 32 位**：
   - ring_mix：`lanes[...] = S[...]`（S 来自 tadd2 输出）；`lanes[...] ^ pm/maj`（^ 两个 32 位）
   - couple/lfsr_mix/absorb：`(… ^ …) & 0xFFFFFFFF`
   - 唯一无掩码写回是 ring_mix 的 `lanes[2*i] = S[2*k]`——S 32 位（第 3 点），故自洽
3. **位平面数学输出 32 位**：tadd2/tmul2/quant3 内部**纯 `&/|/^` 链**（无 `+`/`<<`/`*`），
   位宽不增长——32 位输入 → 32 位输出。rotlane 经 `& 0xFFFFFFFF` 强制 32 位。
   → 这就是 A5 删除其内部掩码的依据（KAT 逐字不变）。
4. **h / IV / rcon 32 位**：h 每块 `& 0xFFFFFFFF` 更新；IV/rcon 由 parse_hex32（逐字节
   `(v << 4 | nib) & 0xFFFFFFFF`）构造。
5. **skey / Pw 32 位**：skey 每步 `(skey * 3 + dig) & 0xFFFFFFFF`；Pw 由 `1 << (j&31)`/`(b>>biti)&1` 构造。

**结论**：只要上述不变量成立，任何"纯 `&/|/^` 链 + 32 位输入"的掩码均可删除而不改变值。

## 3. 掩码热点量化（std/tsha1.tie，`& 0xFFFFFFFF`）

原始 37 处，A5 核心删 4 + A5-b 删 24 = 28 处，剩余 9 处（8 必要 + 1 注释，已合并入 main）：

| 函数 | 原始 | 已删 | 剩余 | 类别 |
|------|------|------|------|------|
| tadd2 | 2 | 2 | 0 | 纯位运算（A5 核心） |
| tmul2 | 2 | 2 | 0 | 纯位运算（A5 核心） |
| quant3 | 1 | 1 | 0 | 纯位运算（A5 核心） |
| rr32 / rl32 | 2 | 0 | 2 | **必要**（`<<`，n=0 边界） |
| parse_hex32 | 1 | 0 | 1 | **必要**（`<< 4`） |
| block_planes_skey | 2 | 1 | 1 | skey `*3+` **必要**；M/N 返回已删 |
| digest 计数器 | 4 | 0 | 4 | **必要**（`+` 进位） |
| compress | 7 | 7 | 0 | 初始化/h 更新已删（A5-b） |
| compress48 / fin_synth | 4 | 4 | 0 | 已删（A5-b） |
| absorb | 2 | 2 | 0 | 已删（A5-b） |
| couple | 4 | 4 | 0 | 已删（A5-b） |
| lfsr_mix | 7 | 7 | 0 | 已删（A5-b） |
| **合计** | **37** | **28** | **9** | 必要 8 / 注释 1 |

## 4. 掩码分类与处置

### 4.1 必要（`+`/`<<`/`*` 增长位宽，u32 通道落地前不能删）

| 位置 | 表达式 | 为什么必要 |
|------|--------|-----------|
| rr32/rl32 | `(v << (32-n))` | 左移产生高位（n=0 时 `v<<32`）；u32 语义下旋转原生 |
| parse_hex32 | `(v << 4 \| nib)` | 左移 4 位累积 |
| skey 链 | `(skey * 3 + dig)` | 乘法 + 加法 |
| digest 计数器 | `(t_lo + 64)`、`t_hi + ((t_lo+64)>>32)` | 64 位计数进位 |

### 4.2 可省防御性（^/| 两个 32 位值，A5-b 波可删，KAT 不变）

~21 处：absorb（sm/sn 写回）、couple（sm/sn/pm/pn 写回）、lfsr_mix（M0/N0/fb/rcon 异或写回，
含 `fb = (lanes>>16 ^ lanes)`——`>>16` 后高 16 位为 0）、compress 初始化与 h 更新、
fin_synth、block_planes_skey 返回 M/N（`1<<bit` 恒 32 位内）。

> 说明：A5 首波只删**最热路径**（位平面数学内层，每轮每元素执行）的 5 处；防御性写回
> 掩码（couple/lfsr_mix/absorb 等每轮/每块一次）收益低、改面大，留作 A5-b 独立小波。

### 4.3 u32 通道落地后（掩码全部消失）

若 tiec 引入 u32 类型（LLVM i32）与位平面 SIMD，则：
- `+`/`<<`/`*` 在 u32 语义下**自然回绕/截断**，全部 `& 0xFFFFFFFF` 删除；
- rr32/rl32 变原生 i32 旋转（LLVM 有 funnel shift 或组合）；
- 每轮掩码指令数：热路径 tadd2(2)+tmul2(2)+quant3(1)+rotlane(2) ≈ 7 → 0。

## 5. A5 落地（已完成，已并入 main 2bb742b）

- **改动**：A5 核心 tadd2/tmul2/quant3 删 5 处（o_pos/o_neg/amp/no/结果）+ A5-b 防御性写回 24 处。
- **依据**：§2 不变量（操作数 32 位 + 纯 `&/|/^` 链位宽不增长）。
- **验证**：f/r 探针 269 + b/x 271 项**全 PASS**（main F1 期望值），逐字不变；全量正例 52/52。

## 6. 后端 u32 通道落地路线（独立跟踪，perf-design §7）

| 步骤 | 内容 | 收益 |
|------|------|------|
| U1 | tiec 引入 u32 类型（types TK_U32 已有；LLVM i32 生成、算术回绕语义） | 掩码天然消除 |
| U2 | 位平面热路径函数改 u32 签名（tadd2/tmul2/quant3/rr32/rl32） | 每轮 -7 掩码指令 |
| U3 | 旋转向量化（LLVM funnel shift / 逐 lane 并行） | 每轮旋转并行 |
| U4 | 64 字节 trit 化单遍 SIMD（byte_tv 批量） | 块预处理加速 |
| 验证 | tsha1f/r/b/x 探针全 PASS + cmp-bench 重跑对照 §1 收口表 | 判定是否趋近 sha256 |

**U1 状态（已验证，2026-08-31）**：u32 类型后端完全可用（LLVM i32、算术回绕正确、
字面量/表支持）；微基准 i64 加法+掩码 30 亿次 2s vs u32 原生 <1s（≥2x）；u32 版位平面
数学（tadd2/tmul2/quant3/rr32）与 i64+掩码语义逐位等价（探针 PASS）。窄整数转换后端
bug 已修复（用户调用 trunc 不支配 + extern 双重转换，irgen_call.tie）。U2 依赖 A5/A5-b
掩码删除（已并入 main）与并行会话 F1 稳定。

> U1 是编译器后端改动（irgen/llvmgen/types），与 A5 分支无关，独立跟踪；U2-U4 依赖 U1。

## 7. 范围外

- A5-b（防御性写回掩码 24 处）：**已完成并并入 main（2bb742b）**。
- W17（n=92/96）struct 特化：perf-design §7 低优先，不改结论。
- skey 分片（B1）：语义变更，perf-design 已判定不启动。
