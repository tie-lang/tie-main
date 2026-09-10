# ROAD — tie 开发计划（2026.2）

*EN: ROAD — tie Development Plan (2026.2)*

> **定位**：2026.2 采用「预发布 → 正式版」两段式开发，延续 2026.1 的双轨模式。
>
> - **预发布段（p.7）**：全部新功能在 p.7.x 开发模块完成，开发号 **P.x.y.z**
>   （即 CHANGELOG 中的 p.x.y.z；模块 p.7.1=编译器重构 / p.7.2=编译资源可调 /
>   p.7.3=库补全 / p.7.4=仓库分离，后续按需扩展）。
> - **正式版段（r.2）**：p.7 发布后启动，**基于 p.7** 开发——**不引入任何新功能**，
>   只做优化与稳定性；开发号 **R.x.y.z**。两轨独立编号、不互相延续。
> - **当前状态（2026-09-11）**：2026.1（Harbor）已正式发布；**p.7 分支已创建**
>   （基于 main），2026.2 全部开发在 p.7 分支上进行。
> - **历史路线图**：2026.1 ROAD 已归档至 [tie-lang/old_docs](https://github.com/tie-lang/old_docs)
>   （2026.1/ROAD.md）。

EN: 2026.2 follows the two-stage "preview → stable" development model, continuing the
dual-track scheme of 2026.1. The preview stage (p.7) does all new features under p.7.x
modules, numbered P.x.y.z (p.x.y.z in the CHANGELOG). The stable stage (r.2) starts after
p.7 ships, is based on p.7, introduces NO new features — only optimization and
stability — and numbers its work R.x.y.z. The two tracks number independently. 2026.1
's ROAD was archived to tie-lang/old_docs (2026.1/ROAD.md). All 2026.2 development
happens on branch p.7.

### 开发计划（初始清单，待补充）

> 以下为 2026.2 开发方向起始清单（2026-09-11 立项），按优先级排序；模块编号、
> 子项拆分在逐项设计中细化。
>
> EN: Initial 2026.2 backlog, prioritized; module numbers and sub-item splits are
> refined per-item in design documents.

**编译器重构与插件化（p.7.1，方向 1）**

- [ ] 编译器彻底重构：模块化分层（前端/语义/中端/后端解耦），为插件化打基础

- [ ] 插件化架构：编译流水线步骤可插拔（自定义前端扩展/自定义后端/自定义 pass），
  插件接口与加载机制定型（参考 tink 帧协议做插件间通信）

**编译资源可调（p.7.2，方向 2，利好老电脑开发）**

- [ ] 编译时可调内存与性能：内存上限/并发度/优化档位可配置，老电脑可按需降低
  编译资源占用换可用性

**内置库补全（p.7.3，方向 3）**

- [ ] 更多内置库：清单与优先级在库补全设计中确定（延续 2026.1 一库一子项纪律）

**仓库分离（p.7.4，方向 4，工程重构）**

- [ ] 主仓库只留文档与发行版；编译器及其他独立工具各自独立仓库
  （tie-main → 文档/发行版；compiler/tdzd/tsp/trm-lite/tink 等按边界拆分独立仓）