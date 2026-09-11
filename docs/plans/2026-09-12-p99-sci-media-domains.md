# p.9.9 计算科学与多媒体域布局 —— tie 生态扩展
*EN: p.9.9 Computational-Science & Media Domain Layout — tie ecosystem expansion*

**日期** / Date: 2026-09-12 · **类型** / Type: 领域布局规划（组件清单 + 依赖链 + 设计参考；各组件内部设计未推演不落）
**依据** / Basis: 用户布局要求（2026-09-12 定）：科学计算 · 统计预测（社会/经济等）· 仿真模拟 · 建模 · 图片处理 · 视频处理 · 特效——**参考 R / Matlab / Julia 等其他语言的设计习惯**
**关联** / Related: ROAD p.9.9 档 · `std/math`、`linalg`（已有数学底座）· `trg`（颜色空间）· `t3d`（特效视口）· `tphy`（物理仿真，与 tsim 区分）
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Lays out the tie ecosystem's expansion into computational science
> and media domains, two spines plus one cross-cutting component. **Computational
> science spine**: tsci (scientific computing) → tstat (statistics & forecasting,
> social/economic) → tsim (simulation). **Media spine**: timg (image) → tvid
> (video) → tvfx (VFX, standalone per decision). **Cross-cutting**: tgeo
> (geometric modeling), consumed by t3d/tphy/tanim and usable for CAD. Design
> reference: R (statistical idioms, dataframe mindset), Matlab (matrix as a
> first-class citizen), Julia (multi-dispatch, high-performance numeric,
> math-notation affinity) — tie's tables, pipe `->` and math syntax are the
> carriers. Components follow the one-component-one-repo convention; ROAD p.9.9
> registers them. Internal designs are NOT discussed yet.

---

## 1. 领域清单与依赖链 / Domains & Dependency Chain

**计算科学主轴**（自底向上）：
* **tsci 科学计算**（`tie-lang/tsci`）：数值线性代数（BLAS/LAPACK 类）· FFT · ODE/微分方程求解 · 优化 · 特殊函数——依赖已有 `std/math`、`linalg` 底座
* **tstat 统计预测**（`tie-lang/tstat`）：分布 · 回归 · 时间序列（ARIMA/ETS）· ML 基础（线性/逻辑回归、聚类、决策树）· 蒙特卡洛 · 贝叶斯基础——依赖 tsci；覆盖**社会/经济预测**
* **tsim 仿真模拟**（`tie-lang/tsim`）：离散事件仿真（DES）· 蒙特卡洛仿真 · 系统动力学 · agent-based（社会/经济/工程）——依赖 tsci+tstat
  * 与 tphy 区分：tphy = 刚体/碰撞微观物理引擎；tsim = 系统级/规则级仿真（显式区分）

**几何建模**（横跨）：
* **tgeo 几何建模**（`tie-lang/tgeo`）：B-rep · NURBS · 网格 · 参数化——**供 t3d（渲染几何）/ tphy（碰撞形状）/ tanim（骨骼网格）消费**；独立可服务 CAD/工程建模

**多媒体主轴**：
* **timg 图像处理**（`tie-lang/timg`）：编解码（PNG/JPEG/WebP/AVIF）· 滤镜 · 缩放/重采样 · 颜色管理——依赖 trg（颜色空间共享）
* **tvid 视频处理**（`tie-lang/tvid`）：编解码（H.264/H.265/AV1，重）· 转码 · 帧/流处理——依赖 timg
* **tvfx 特效**（`tie-lang/tvfx`，独立定案）：粒子系统 · 后处理特效 · 着色器特效库——依赖 t3d（视口/渲染），独立服务游戏+影视+通用

## 2. 设计参考：R / Matlab / Julia / Design Reference

| 参考语言 | 借鉴点 | tie 承载 |
|---|---|---|
| R | 统计建模习惯 · 数据框（dataframe）理念 · tidyverse 管道 | 表（table）≈ dataframe · 管道符 `->` |
| Matlab | 矩阵即一等公民 · 数值脚本习惯 · 向量化表达 | 表/数组值语义 · 推导式/切片 |
| Julia | 多重分派 · 高性能数值 · 数学记号亲和（π/矩阵语法） | tie 表式数据 + 编译性能（LLVM 后端） |

* **tie 承载原则**：不引入新语言特性——以表/管道/数学语法现有能力承载上述习惯；缺口（如矩阵专用语法糖）走 tie 语言增强轨道（ROAD p.8 语言档），不借道组件仓开口子

## 3. 库生态与产出物 / Library Ecosystem & Outputs（2026-09-12 用户洞察补充）

> **关键洞察**：R / Matlab / Julia（含 Python 的 numpy/scipy/pandas/matplotlib）应用广泛，**不在语言本身，而在庞大的库生态 + 能产出产物**（画图、报告、结果）。布局必须包含这两个维度。

### 3.1 库生态（pkg + registry 承载，CRAN/PyPI 模式）
* 每个领域组件 = **核心仓**（tsci/tstat/tsim/tgeo/timg/tvid/tvfx），其上**库包**按 pkg 分发、registry 注册（生态已有 `pkg` 包管理器 + keel registry）
* 例：`tstat` 核心 + 社区库包（金融时序、生物统计、社会调查…）——**库生态 = 组件的持续扩展面**，不靠组件仓无限膨胀

### 3.2 产出物（tie 生态内部闭环，不依赖外部绘图库）
* **tplot 统计可视化**（新组件 `tie-lang/tplot`）：基于 **tiu（2D 绘制引擎/绘制表）+ timg（图像输出）** 的图表库——ggplot2 / matplotlib 对应物
  * 统计图（散点/直方/箱线/折线/热力）· 数据可视化 · 交互图（tedit 视口）
  * **产出**：图像文件（timg 编码）/ tedit 内嵌视口 / zd 数据导出
* **报告/笔记产出**：tedit 的 **notebook 模组**——代码 + 图表（tplot）+ 文本 → 报告（RMarkdown / Jupyter 对应物）
* **结果导出**：timg（图）/ tvid（视频）/ zd（数据）——产出物全链路闭环

### 3.3 产出物链路 / Output Chain
* `tsci/tstat/tsim 计算 → tplot 绘图 → timg/tvid 导出 / tedit notebook 报告`
* 端到端"能画图、能出产物"——对齐 R/Python 应用广泛的根因

## 4. 边界 / Boundary

* 各组件**独立仓、独立发行、可单用**（生态惯例）
* 依赖链单向：tsci ← tstat ← tsim；timg ← tvid；tvfx → t3d；tgeo → 供 t3d/tphy/tanim；**tplot → tiu + timg**
* 与游戏引擎（tge）关系：tge 可按需组装 tgeo（场景几何）/ tstat-tsim（玩法数值/仿真），非必需依赖

## 5. 未讨论项（不落为结论） / Not Yet Concluded

* 各组件**内部机制**（tsci 线性代数内核形态 / tstat 统计模型集 / tsim 仿真引擎 / tgeo 几何内核 / timg·tvid 编解码自研范围 / tvfx 特效集 / **tplot 绘图内核**）——均未推演，推演完成后各自落盘
* 编解码自研范围（对齐 taud 纯自研定案？）——未定
* 与 tie 语言增强轨道的衔接点（矩阵语法糖等）——未定
* tedit notebook 模组的内部设计——未推演（归 tedit 模组推演）

---

## 附录 / Appendix

* 术语 / Terms：BLAS/LAPACK（线性代数标准库）· ARIMA/ETS（时间序列模型）· DES（离散事件仿真）· B-rep/NURBS（几何内核）· dataframe（R 数据框理念）
* 演进：本文档为领域布局；各组件设计推演后独立落盘（一组件一文档）