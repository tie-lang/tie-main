# tie 生态格式与 API 家族规范
*EN: tie Ecosystem Format & API Family Specification*

**日期** / Date: 2026-09-12 · **类型** / Type: 生态规范（跨领域；统一格式谱系与 API 契约）
**依据** / Basis: 用户梳理（2026-09-12 定）：tie 生态 API 家族——tieapi（库）· td（人类可读，语法属 tie）· zd（人类不可读）…… · tieapi = **统一 API 规范层**（2026-09-12 定）
**关联** / Related: zd v2 规范（已定稿）· tink 帧协议 · tieir 格式 · 各组件资产格式 · tedit 模组协议 · ROAD p.9.x 各组件
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Defines the unified format & API family of the tie ecosystem —
> one coherent lineage instead of per-component formats. **tieapi** is the
> unified API specification layer: every component's public API (tsci/tstat/
> tge/...) follows one contract — value-semantics data, td/zd I/O, unified
> error model with diagnostic codes; developers get a consistent experience
> across all components. **td** (human-readable, grammar belongs to tie =
> table literals) and **zd** (binary, human-unreadable) are the **same-source
> dual form** (tdzd conversion); every config/data/asset has a td source and a
> zd runtime form. Specialist formats (tieir, tink frame protocol, component
> assets, tedit module protocol, tink ABI) are carriers layered on td/zd.
> The tie language itself is the substrate (td grammar = tie literals; tieapi
> = tie functions/structs, value semantics). Family discipline: everything is
> td-source → zd-runtime; every API is value-semantics + diagnostic codes.

---

## 1. 家族成员 / Family Members

### 1.1 tieapi（统一 API 规范层） / Unified API Specification Layer
* **定位**：所有组件（tsci/tstat/tsim/tgeo/timg/tvid/tvfx/tplot/trg/t3d/tiu/tink/taud/tanim/tphy/tge…）对外 API 遵循的**统一契约**
* **契约内容**：
  * **值语义数据**：API 出入参为值语义数据（表/记录/标量），无隐式共享突变
  * **td/zd 输入输出**：API 的持久化/传输输入输出统一 td 源 ↔ zd 运行时
  * **统一错误模型**：可检查结果（非异常流）+ **诊断标号体系**（W/E 码，复用 tie 诊断）
  * **可记录回放**：API 调用序列可记录重放（确定性/测试/调试）
* **价值**：开发者面对任意组件 API 体验一致（类比 Julia Base / numpy 全家桶一致性）；新组件按契约实现即生态一等公民

### 1.2 td（人类可读源） / Human-readable Source
* 语法**属 tie**（表字面量 `{ key: value }`、`[1,2,3]`）——可读写、可 diff、可版本控制
* 一切数据/配置/资产（tge 场景/prefab · tanim clip/骨架/状态机 · tphy 材质 · tiedb 数据 · tsim 模型 …）的**可读源形态**

### 1.3 zd（二进制变体） / Binary Variant
* 人类不可读、二进制、即时读取、低内存；td 的**同源双态**（`tiec --compress-data` tdzd 转换）
* 发布/运行时的标准形态；v2 规范已定稿（10 字节头 + 字段协议）

### 1.4 专项格式 / Specialist Formats（载体，基于 td/zd）
* **tieir**：编译器 IR（模块头/类型表/符号表/列式 IR 体/导出表）
* **tink 帧协议**：跨进程/网络（长度前缀 + CRC + tsha1f 强校验）
* **组件资产**：各组件 zd 资产（tanim 三件套 / tphy 材质表 / tge 场景 · prefab …）
* **tedit 模组协议**：编辑器模组间（zd 序列化，同进程协议隔离）
* **tink ABI**：组件互联（模块.函数 字节进 → 字节出，zd 帧）

### 1.5 语言本体 / The Language
* tie 语言是底层基座：td 语法 = tie 表字面量（同源）· tieapi 库 = tie 函数/结构（值语义）· 编译 → LLVM 原生 / trm 字节码 / WASM
* 确定性 · 性能 · 无 GC 值语义

## 2. 家族纪律 / Family Discipline

1. **同源双态**：一切数据/配置/资产 = td 源 + zd 运行时（tdzd 转换，单源不分裂）
2. **API 统一契约**：一切对外 API = 值语义 + td/zd I/O + 诊断码 + 可回放（tieapi 规范）
3. **专项格式不外造**：帧/IR/资产/协议一律以 td/zd 为底座，不发明独立格式
4. **可读优先**：开发态 td（可 diff/审阅），运行态 zd（性能/内存）——人类与机器各得其所

## 3. 边界 / Boundary

* 本规范约束**跨组件接口与数据形态**；各组件内部实现不受限
* 不替代 zd v2 规范（二进制细节）与 tieir 规范（IR 细节）——本规范是**谱系与契约层**

## 4. 未讨论项（不落为结论） / Not Yet Concluded

* tieapi 规范的具体**接口形态**（错误类型/结果类型/td-zd 助手的标准签名）· 诊断码在 API 层的统一编号段分配 · 组件资产的 td 语法模板（各组件资产 td 示例）——**均未推演**，推演完成后在本文档补章

---

## 附录 / Appendix

* 术语 / Terms：同源双态（same-source dual form，td 源 ↔ zd 变体）· tieapi（统一 API 规范层）· 专项格式（specialist format，基于 td/zd 的载体）
* 演进：本文档为谱系与契约层；接口细节随生态组件实现回写（版本表）