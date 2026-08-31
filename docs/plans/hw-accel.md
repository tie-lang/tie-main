# 规划：tie 硬件加速可行性（GPU 检索 + Intel NPU 推理 + SIMD/并行）
*EN: Plan: tie Hardware-Acceleration Feasibility (GPU Retrieval + Intel NPU Inference + SIMD/Parallel)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> EN: Status: **Plan** (design discussion finalized 2026-08-15, not yet implemented)
> 本文档分析 GPU/NPU/SIMD/多核加速 tie 编译与 tieDB 的可行性，及定稿路线。
> EN: This document analyzes the feasibility of using GPU/NPU/SIMD/multi-core to accelerate tie compilation and tieDB, and the finalized roadmap.
> 决策汇总：
> EN: Decision summary:
> **编译器不做 GPU 加速**（串行依赖负载不适合）；**tieDB 向量检索做 GPU**
> EN: **The compiler does not use GPU acceleration** (unsuitable for serial-dependency workloads); **tieDB vector retrieval uses GPU**
> （trm.gpu extern 桥，10-50x 预期）；**NPU 瞄准 Intel 家用 CPU 内置 NPU**
> EN: (trm.gpu extern bridge, expected 10-50x); **NPU targets the Intel consumer-CPU built-in NPU**
> （trm.npu，OpenVINO 桥，embedding 推理）；**统一原则**：extern 桥 +
> EN: (trm.npu, OpenVINO bridge, embedding inference); **unified principle**: extern bridge +
> 自动降级（可插拔加速器）。
> EN: automatic fallback (pluggable accelerators).
> 关联：trm 架构（可选 opt-in/域粒度）、unsafe 模型（extern 桥）、
> EN: Related: trm architecture (optional opt-in / domain granularity), unsafe model (extern bridge),
> tieDB（vecsearch Flat 索引）、ext/ml、序列化规范（zd）。
> EN: tieDB (vecsearch Flat index), ext/ml, serialization spec (zd).

## 1. 分析框架：负载特征决定适配度
*EN: 1. Analysis Framework: Workload Characteristics Determine Fitness*

| 负载类型 | 特征 | 适合硬件 |
| --- | --- | --- |
| 数据并行（吞吐型） | 大量独立同构计算 | GPU/NPU/SIMD |
| 延迟敏感（串行依赖） | 分支密集、内存跳转 | 不适合 GPU |
| 小批量高延迟 | 依赖链长 | 多核 CPU 更优 |

EN: The table classifies the three workload archetypes (data-parallel / latency-sensitive / small-batch-high-latency) by their characteristics and the hardware best suited to each.

## 2. 编译器加速（结论：不做 GPU，强化 CPU 并行）
*EN: 2. Compiler Acceleration (Decision: No GPU; Strengthen CPU Parallelism)*

### 2.1 各阶段负载特征
*EN: 2.1 Per-Stage Workload Characteristics*

| 阶段 | 计算特征 | GPU 适配度 |
| --- | --- | --- |
| 预处理 prep | 文本处理、字符判断 | ❌ 串行依赖、分支密集 |
| 词法 lexer | 状态机、最长匹配 | ❌ 强串行（token 流依赖） |
| 语法 parser | 递归下降、AST 构建 | ❌ 强串行 |
| 语义 semantic | 符号表查插、类型推断 | ❌ 哈希表/图遍历，内存跳转密集 |
| 单态化 | 泛型实例化 | 🟡 可并行（实例独立）——多核 CPU 足够 |
| IR 生成 | AST → 列式表 | 🟡 函数级独立——多核 CPU 足够 |
| LLVM opt | 优化 pass | 🟡 LLVM 自身已多线程 |
| 链接 | lld | ✅ lld 已多线程 |

EN: The table rates each compiler stage for GPU fitness. Frontend/semantic stages are marked ❌ (serial, branch/memory-hop heavy); monomorphization and IR generation are 🟡 (parallelizable, multi-core CPU suffices); LLVM opt and lld are 🟡/✅ (already threaded).

### 2.2 结论：编译器不适合 GPU
*EN: 2.2 Conclusion: The Compiler Is Not Suited to GPU*

1. 编译器是**延迟敏感 + 强串行依赖**负载（lexer→parser→semantic 流水依赖，
   符号表哈希/树结构内存跳转密集）——GPU 最不擅长的负载
   EN: The compiler is a latency-sensitive, strongly serial-dependency workload (pipelined lexer→parser→semantic dependencies; symbol-table hash/tree memory hops abound) — precisely the load GPUs handle worst.
2. 工业界无 GPU 加速编译器成功先例（研究收益不成比例）
   EN: There is no proven industry precedent for GPU-accelerated compilers (research payoff is disproportionate).
3. tie 已有 **M3 多文件三阶段并行**（多核 CPU）——已抓住主要并行度
   EN: tie already has **M3 multi-file three-stage parallelism** (multi-core CPU) — the dominant parallelism is already captured.

### 2.3 编译器正确的 CPU 加速路径（按收益排序）
*EN: 2.3 The Compiler's Correct CPU Acceleration Path (Ranked by Payoff)*

1. **M3 并行继续增强**（文件级并行是最大收益）
   EN: **Keep strengthening M3 parallelism** (file-level parallelism gives the largest payoff).
2. **单态化/IR 生成的函数级并行**（tie 并发模型落地后，纯数据并行）
   EN: **Function-level parallelism for monomorphization/IR generation** (pure data parallelism once the tie concurrency model lands).
3. **SIMD 自动向量化**：LLVM -O2 已有；热点（字符串扫描/哈希）asm! 补（I1 已定）
   EN: **SIMD auto-vectorization**: LLVM -O2 already provides it; hotspots (string scan/hash) are covered with asm! (I1 already decided).
4. **增量编译缓存**（M3 cache LRU 已有——tieir 缓存命中零成本）
   EN: **Incremental-compilation caching** (M3 cache LRU exists — a tieir cache hit costs nothing).

## 3. tieDB 加速（真正的 GPU 场景）
*EN: 3. tieDB Acceleration (The Real GPU Scenario)*

### 3.1 各操作负载特征
*EN: 3.1 Per-Operation Workload Characteristics*

| 操作 | 计算特征 | GPU 适配度 |
| --- | --- | --- |
| **向量检索（vecsearch Flat）** | **数据并行**：n 条向量 × d 维点积/距离 | ✅✅ **GPU 理想场景**（FAISS 同款） |
| zd 编解码 | 字节流变长解码 | 🟡 块级可并行，CPU 够 |
| 排序/过滤 | 比较密集 | 🟡 多核 CPU 足够 |
| 事务/索引 | 哈希/树/B+树 | ❌ 延迟敏感 |
| 查询规划 | 图搜索 | ❌ |

EN: For tieDB operations, vector retrieval (vecsearch Flat) is the standout GPU ideal (data-parallel), while zd encode/decode and sort/filter are 🟡 (CPU fine) and transactions/indexes/query planning are ❌ (latency-sensitive).

### 3.2 GPU 加速向量检索：可行性高，价值最大
*EN: 3.2 GPU-Accelerated Vector Retrieval: High Feasibility, Greatest Value*

- `cosine = Σ(xᵢ·yᵢ) / (|x||y|)`——n 条向量相互独立，纯数据并行
  EN: `cosine = Σ(xᵢ·yᵢ) / (|x||y|)` — the n vectors are mutually independent, purely data-parallel.
- FAISS 已证明：GPU 比 CPU 快 **10-50x**（百万级向量）
  EN: FAISS has proven GPU runs **10-50x** faster than CPU (million-scale vectors).
- tieDB 的 vecsearch Flat 精确索引 = 暴力全量计算——**GPU 天然加速**
  EN: tieDB's vecsearch Flat exact index = brute-force full computation — **naturally accelerated on GPU**.

```tie
// 异构计算层：trm.gpu 域（extern 桥，tie 不写 GPU 内核）
namespace trm.gpu {
    // extern 桥：CPU 侧调用，GPU 侧执行（CUDA/OpenCL/oneAPI 后端）
    unsafe extern fn gpu_distance_matrix(vectors: ptr<f64>, n: i64, d: i64, out: ptr<f64>) -> i64
    unsafe extern fn gpu_topk(dists: ptr<f64>, n: i64, k: i64, out_idx: ptr<i64>) -> i64
}

// tieDB 查询路径（编译期/运行期选择，与 P4b backend 同思路）：
//   有 GPU → trm.gpu 路径（extern 桥）
//   无 GPU → CPU 路径（现有 vecsearch，纯 tie）
```

**关键决策**：tie 不写 GPU 内核（CUDA/OpenCL 内核非 tie 可表达）——走 extern
桥接成熟库/自写少量 C 内核。GPU 是"加速器外设"，如同显卡驱动。
EN: **Key decision**: tie does not write GPU kernels (CUDA/OpenCL kernels cannot be expressed in tie) — it extern-bridges mature libraries or hand-writes a small amount of C kernel code. GPU is an "accelerator peripheral," like a graphics driver.

## 4. NPU 加速（Intel 家用 CPU 内置 NPU）
*EN: 4. NPU Acceleration (Intel Consumer-CPU Built-in NPU)*

### 4.1 方向修正（2026-08-15）
*EN: 4.1 Direction Correction (2026-08-15)*

**NPU 瞄准 Intel 集成在家用 CPU 的 NPU**（Intel AI Boost）：
EN: **NPU targets the NPU that Intel integrates into consumer CPUs** (Intel AI Boost):
- Core Ultra（Meteor Lake 2023）起全系内置，Lunar Lake/Arrow Lake 增强——
  **随家用 CPU 普及，非碎片化嵌入式生态**
  EN: Built into the whole lineup since Core Ultra (Meteor Lake 2023) and enhanced in Lunar Lake/Arrow Lake — **it proliferates with consumer CPUs, not a fragmented embedded ecosystem**.
- 统一软件栈：**OpenVINO**（Intel 官方，C API 可 extern 桥）——单一入口
  EN: Unified software stack: **OpenVINO** (Intel official; its C API can be extern-bridged) — a single entry point.
- Windows 侧还有 DirectML/WinML 路线，OpenVINO 是主通道
  EN: Windows also offers DirectML/WinML routes; OpenVINO is the primary channel.
- 修正：之前"NPU 生态碎片化、无价值"结论作废
  EN: Correction: the earlier conclusion that "the NPU ecosystem is fragmented and worthless" is hereby voided.

### 4.2 NPU 本质：NN 推理加速器（非通用计算）
*EN: 4.2 NPU Essence: an NN Inference Accelerator (Not General-Purpose Compute)*

| 场景 | NPU 适配 | 说明 |
| --- | --- | --- |
| **embedding 模型推理**（文本→向量） | ✅✅ 主场景 | 语义检索前置：tieDB 向量入库前文本→向量 |
| LLM 本地推理（AI PC） | ✅ | 本地 AI 应用 |
| 图像/音频推理 | ✅ | OpenVINO 全模型覆盖 |
| 向量检索本身 | ❌ | 数据并行计算，NPU 不适合——GPU/CPU 的事 |

EN: The table maps scenarios to NPU fit: embedding-model inference is the primary ✅✅ scenario, local LLM and image/audio inference are ✅, while vector retrieval itself is ❌ (data-parallel — the job of GPU/CPU).

### 4.3 关键洞察：NPU + GPU 互补的完整链路
*EN: 4.3 Key Insight: A Complete Pipeline Where NPU + GPU Complement Each Other*

```
tieDB 语义检索全链路：
  文本 ──▶ embedding 模型（NPU，OpenVINO 桥）──▶ 向量
  向量 ──▶ 检索（GPU 加速，trm.gpu 桥）──────▶ top-k 结果
  CPU 编排：tie 逻辑 / zd 编解码 / 事务
```

- NPU 干推理（文本→向量，NN 负载）
  EN: NPU handles inference (text→vector; NN workload).
- GPU 干检索（向量距离，数据并行）
  EN: GPU handles retrieval (vector distance; data-parallel).
- CPU 干编排（逻辑/序列化/事务）
  EN: CPU handles orchestration (logic/serialization/transactions).

### 4.4 接入方案（OpenVINO 桥）
*EN: 4.4 Integration Approach (OpenVINO Bridge)*

```tie
// trm.npu 域：OpenVINO 推理桥（C API → extern）
namespace trm.npu {
    unsafe extern fn ov_compile_model(model_path: string, device: string) -> i64
    unsafe extern fn ov_infer_text(model: i64, text: ptr<u8>, len: i64, out_vec: ptr<f64>) -> i64
    unsafe extern fn ov_free(model: i64)
}

// tieDB embedding 路径：
//   有 NPU → trm.npu 推理（OpenVINO，device 自动选 CPU/GPU/NPU）
//   无 NPU → OpenVINO CPU 后端 or 纯 tie 经典模型
```

**OpenVINO 红利**：device 参数自动选择（CPU/GPU/NPU）——同一套代码三端可跑，
tie 侧无需感知 NPU 存在，只需声明"用 OpenVINO"。与"可插拔加速器"原则一致。
EN: **OpenVINO dividend**: the device parameter is auto-selected (CPU/GPU/NPU) — the same code runs on all three backends; tie never needs to know an NPU exists, only to declare "use OpenVINO." This is consistent with the "pluggable accelerator" principle.

### 4.5 新增价值
*EN: 4.5 Added Value*

- tieDB 从"向量数据库"升级为**语义检索数据库**（embedding + 检索全本地）
  EN: tieDB upgrades from a "vector database" to a **semantic-retrieval database** (embedding + retrieval, fully local).
- AI PC 场景杀手级组合：本地 AI 能力（embedding/LLM）+ tie 脚本/应用
  EN: A killer combination for the AI-PC scenario: local AI capability (embedding/LLM) + tie scripts/applications.

## 5. 其他硬件
*EN: 5. Other Hardware*

| 硬件 | 场景 | 结论 |
| --- | --- | --- |
| **SIMD（AVX/NEON）** | CPU 内向量化 | ✅✅ 零额外硬件、收益即时：LLVM 自动向量化 + asm! 热点补 |
| FPGA | 定制加速 | ❌ 开发成本极高、不可通用 |
| DPU/SmartNIC | 网络 | ❌ 边缘场景 |
| 多核 CPU | 通用 | ✅ 已用（M3），继续加强 |

EN: SIMD (✅✅) and multi-core CPU (✅) are adopted; FPGA and DPU/SmartNIC are rejected (❌) as too costly or edge-case-only.

## 6. 定稿路线
*EN: 6. Finalized Roadmap*

```
P1（立即，零成本）：SIMD 自动向量化 + M3 并行增强
  · LLVM -O2 已有；热点（vecsearch 距离/zd/哈希）确认向量化，缺口 asm! 补
  · 编译器自身：M3 并行继续 + 单态化函数级并行（并发模型落地后）

P2（中期，高价值）：tieDB 向量检索 GPU 加速（trm.gpu extern 桥）
  · CPU 路径保留（无 GPU 自动降级）；预期 10-50x（百万级向量）

P3（中期偏后，家用普及）：Intel NPU 推理加速（trm.npu，OpenVINO 桥）
  · 场景：tieDB embedding（语义检索全链路）、AI PC 本地应用
  · 依赖：OpenVINO 库（C API extern）；无 NPU 自动降级 CPU 后端/纯 tie
```

## 7. 统一原则（所有加速）
*EN: 7. Unified Principles (for All Acceleration)*

1. **extern 桥**：GPU/NPU 加速 = extern 桥接（tie 不写内核/不改语言）
   EN: **extern bridge**: GPU/NPU acceleration = extern bridging (tie writes no kernels and does not change the language).
2. **自动降级**：加速器不存在就不链接（CPU 路径保留）——与 trm 可选
   opt-in（trm-arch §1.1）、P4b 实现选择一致
   EN: **Automatic fallback**: if an accelerator is absent it just is not linked (CPU path stays) — consistent with the trm optional opt-in (trm-arch §1.1) and the P4b implementation choice.
3. **可插拔**：加速是库层的事（trm.gpu / trm.npu 域），tie 语言不动
   EN: **Plug-in**: acceleration is a library-layer concern (trm.gpu / trm.npu domains); the tie language is untouched.
4. **编译期/运行期选择**：有加速器 → 加速路径；无 → CPU 路径（同 backend 思路）
   EN: **Compile-time/runtime selection**: accelerator present → accelerated path; absent → CPU path (same idea as the backend).

## 8. 决策记录（讨论产物）
*EN: 8. Decision Record (Discussion Output)*

| 决策点 | 结论 | 备选（未选） |
| --- | --- | --- |
| 编译器 GPU 加速 | 不做（串行依赖负载不适合） | 研究性尝试 |
| tieDB 加速 | GPU 向量检索（trm.gpu，FAISS 同款，10-50x） | CPU 并行 |
| NPU 方向 | **Intel 家用 CPU 内置 NPU**（AI Boost，OpenVINO 桥） | 嵌入式碎片化 NPU |
| NPU 定位 | embedding 推理（语义检索前置）+ AI PC 本地 AI | 通用计算 |
| 加速实现 | extern 桥 + 自动降级（可插拔加速器） | tie 写内核 |
| 优先级 | P1 SIMD/并行 → P2 GPU 检索 → P3 NPU 推理 | — |

EN: Decision matrix: no compiler GPU acceleration; tieDB gets GPU vector retrieval; NPU targets the Intel consumer-CPU built-in NPU for embedding inference; implementation is extern bridge + auto-fallback; priority is P1 SIMD/parallel → P2 GPU retrieval → P3 NPU inference.

## 9. 未决问题
*EN: 9. Open Questions*

1. **trm.gpu 域形态**：独立域（trm.gpu）还是 tieDB 内部 gpu.tie——
   倾向 trm.gpu（可插拔，与 trm.npu 并列）
   EN: **Form of the trm.gpu domain**: an independent domain (trm.gpu) or gpu.tie inside tieDB — leaning toward trm.gpu (pluggable, parallel to trm.npu).
2. **GPU 后端选择**：CUDA（N 卡）/ oneAPI（I 卡）/ OpenCL（通用）——多后端
   抽象（port 接口，P4b 选择）还是第一版单后端
   EN: **GPU backend choice**: CUDA (NVIDIA) / oneAPI (Intel) / OpenCL (generic) — abstract over multiple backends (port interface, the P4b choice) or a single backend for v1.
3. **OpenVINO 依赖形态**：随发行版打包（体积）vs 按需下载（与 LLVM 随包
   分发先例对比）
   EN: **OpenVINO dependency form**: bundled with the distribution (size) vs downloaded on demand (contrast with the LLVM-ships-with-the-distribution precedent).
4. **NPU 无感知设计**：tieDB 是否完全隐藏 NPU（embedding API 自动选设备）——
   倾向隐藏（用户只调 `tiedb.embed(text)`）
   EN: **NPU-transparent design**: whether tieDB fully hides the NPU (embedding API auto-selects the device) — leaning toward hidden (users only call `tiedb.embed(text)`).
5. **SIMD 热点清单**：vecsearch 距离/zd 解码/哈希的向量化确认（asm! 手写
   或 LLVM 自动）——实现时基准驱动
   EN: **SIMD hotspot list**: confirming vectorization of vecsearch distance / zd decode / hash (asm! hand-written or LLVM automatic) — benchmark-driven at implementation time.