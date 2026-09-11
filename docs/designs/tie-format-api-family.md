# tie 生态格式与 API 家族规范
*EN: tie Ecosystem Format & API Family Specification*

**日期** / Date: 2026-09-12 · **类型** / Type: 生态规范（跨领域；统一格式谱系与 API 契约）
**依据** / Basis: 用户梳理（2026-09-12 定）：tie 生态 API 家族——tieapi（库）· td（人类可读，语法属 tie）· zd（人类不可读）…… · tieapi = **统一 API 规范层**（2026-09-12 定）
**关联** / Related: zd v2 规范（已定稿）· tink 帧协议 · tieir 格式 · 各组件资产格式 · tedit 模组协议 · ROAD p.9.x 各组件
**版本** / Version: v0.4（2026-09-12 落盘 tac 生成器实现细节）· v0.3 绑定生成策略 · v0.2 对外互操作 · v0.1 谱系与契约

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

## 3. 对外互操作 / Foreign-language Interop（2026-09-12 定）

> 问题：其他语言（Python/R/C++/C#/JS/Rust/Go/Java…）怎么使用 tie 生态？——**语言无关边界三件套 + 四通道**。

### 3.1 语言无关边界三件套 / Language-agnostic Trio
* **zd 数据**：语言无关的二进制序列化格式（任何语言可独立实现 zd 编解码）
* **tink ABI**：模块.函数（字节进 → 字节出），组件以 zd 帧提供服务（长度前缀 + CRC + tsha1f 强校验）
* **tieapi 契约**：值语义 + 诊断码（统一 API 规范，§1.1）——各语言绑定库按其习惯适配

### 3.2 对外四通道 / Four Interop Channels
| 通道 | 形态 | 适用 |
|---|---|---|
| **tink 多语言库**（tink-xxx，已存在 20+ 语言） | 函数级调用 tie 组件（zd 帧协议） | 深度集成 · 高频调用 |
| **CLI / tink pipe** | 子进程调用 tie 命令行（tiec/tie 等）· 管道编排 | 任意语言零依赖接入 |
| **WASM 模块**（p.9.6.2 规划） | tie 编译 wasm，宿主/浏览器加载调用 | 跨语言最强通用面 · 浏览器 |
| **trm 嵌入**（p.9.5.3 规划） | C ABI 嵌入宿主程序（脚本化） | 宿主集成 · 嵌入式 |

* **tink-xxx 绑定库** = tieapi 契约在目标语言的适配层（Python 用 dict/list、C 用结构体、Rust 用类型安全 API……）

### 3.3 反向：tie 使用外部库 / Reverse Direction
* **unsafe FFI**（C ABI）：tie 调用外部 C 库（已实现，unsafe 门禁）
* **tink 对称调用**：tie 组件调用其他语言实现的 tink 服务（模块.函数，对称双向）

### 3.4 原则 / Principles
* **数据中立**：跨语言只交换 zd（不传对象/指针）
* **契约中立**：tieapi 是语言无关 API，绑定库只是适配层
* **通道自选**：集成深度 vs 接入成本由开发者选（函数级 → 子进程 → WASM → 嵌入）

### 3.5 tink-xxx 绑定库自动生成策略 / Binding Codegen（2026-09-12 定）

> 核心：**组件作者只写一份 tieapi 定义（真实 td），生成器产出 20+ 语言绑定库**——"一次定义，多语言落地"（同源双态哲学在 API 层的延伸）。

#### 3.5.1 流程 / Pipeline
`tieapi 定义（td）→ API IR（类型表+签名表）→ tieapi 生成器（tie 写，codegen backend 每语言一个）→ tink-xxx 绑定库`

#### 3.5.2 tieapi 定义（真实 td 语法，依据现存 td 文件形态）
```td
// tieapi 定义 —— tsci.linalg
type tie<data>
api = [
    [ "id": "tsci.linalg", "version": "0.1.0",
      "types": [
          [ "name": "mat", "kind": "record",
            "fields": [
                [ "name": "rows", "type": "i64" ],
                [ "name": "cols", "type": "i64" ],
                [ "name": "data", "type": "table<f64>" ],
            ],
          ],
      ],
      "funcs": [
          [ "name": "mat_mul",
            "in":  [ [ "name": "a", "type": "mat" ], [ "name": "b", "type": "mat" ] ],
            "out": [ "type": "mat" ],
          ],
      ],
    ],
]
```
* 语法对齐真实 td：`type tie<data>` 头 · 命名表 `api = [...]`（无 var）· 记录 = 字符串 id 表 · 嵌套表为值内 `[...]` · `//` 注释
* 类型集：基础（i64/f64/string/bool/表/记录）+ 组件自定义类型（值语义描述）

#### 3.5.3 类型映射 / Type Mapping（值语义 → 各语言习惯）
* `f64 → double` · `i64 → int64/long` · `string → str/String` · `table<T> → list/vector/数组` · `record → struct/class/dict`（Python dict、C struct、Rust struct）
* 映射规则 = 每语言 codegen 的一张映射表（可配）

#### 3.5.4 生成器架构 / Generator Architecture（两层分离）
* **tieapi 生成器**（tie 写，tie 编译器家族）：读 td → API IR → codegen backend（每语言一个，插拔注册）
* **生成产物两层**：
  * **生成层**（从 tieapi 生成）：API 封装（模块.函数）+ **zd 编解码**（类型驱动，从类型表生成——protobuf 式 codegen）
  * **运行时层**（每语言写一次，稳定）：tink 帧协议（zd 帧 + CRC）、连接/管道、内存管理
* **变更只影响生成层**；运行时层稳定复用
* codegen backend = **模板 + 映射表**（每语言量小且可测）

#### 3.5.5 验证矩阵 / Verification Matrix
* **往返测试**：tie 服务端 ↔ 各语言绑定，同一 zd 帧编解码**字节一致**（gold）
* **gold 签名**：tieapi 定义 → 各语言 API 签名与基准一致（跨语言同一契约）
* **跨语言互调矩阵**：tie ↔ Python ↔ Rust ↔ C# 互相调用（协议中立证明）

#### 3.5.6 增量与版本 / Increment & Versioning
* tieapi 定义变更 → 重新生成生成层（版本化）；运行时层不动
* 绑定库随组件版本发布（pkg 分发）

### 3.6 tac 生成器实现细节 / tac Generator Internals（2026-09-12 定）

> **tac = tie api compiler**（组件仓 `tie-lang/tac`）：tie 编译器家族新成员——读 tieapi td 定义 → API IR → 各语言 codegen backend → tink-xxx 绑定库。

#### 3.6.1 内部流水线 / Pipeline
`解析器（td → 表结构）→ 校验器（诊断码 W/E）→ API IR → backend 分派（按语言注册）→ 每语言产物（生成层 + 运行时层）`

#### 3.6.2 API IR（tie 表数据，值语义）
* `module` 表（id/version）· `types` 类型表（name/kind: record|table|scalar / fields / elem）· `funcs` 签名表（name/in/out）
* IR 本身可序列化（zd）——缓存/调试/跨工具

#### 3.6.3 解析与校验 / Parse & Validate
* 解析器：读 `type tie<data>` 定义 → 表结构 → API IR
* 校验器（诊断码 W/E）：类型引用完整性 · 签名唯一性 · 版本合法性 · 未知字段拒绝（Keel 审计同思路）——**API 定义错误尽早报，含修正动作**

#### 3.6.4 codegen 架构（后端可插拔）/ Backend Architecture
* **backend 接口**（统一）：`generate(api_ir, lang_config) → files[]`——每语言一个 backend，Keel 式注册
* **每语言 backend = 映射表 + 模板**：
  * 映射表：tie 类型 → 目标语言类型（f64→double · record→struct/dict · table→list/vec…）
  * 模板：文件骨架 / 函数封装 / zd 编解码
* **模板机制用 tie 准引用宏**（`` `{...} `` + `$x` 插值）——tac 用 tie 写，模板即 tie 代码，天然自举

#### 3.6.5 zd 编解码生成（类型驱动）/ zd Codec Codegen
* 从类型表生成每语言 read/write（protobuf 式）——**类型即编解码规格**
* 基础类型直映 · record 递归字段 · table 长度前缀 + 元素循环
* 与运行时层分离：编解码在生成层，帧组装在运行时层

#### 3.6.6 首期语言集 / Initial Language Set
* **Python / Rust / C** 三语言先行（覆盖脚本 / 系统 / FFI 三类生态）→ 验证后铺 20+

#### 3.6.7 验证 / Verification
* 生成即测：往返字节一致 · gold 签名 · 跨语言互调（tie↔Python↔Rust↔C）——对齐 §3.5.5

## 4. 边界 / Boundary

* 本规范约束**跨组件接口与数据形态**；各组件内部实现不受限
* 不替代 zd v2 规范（二进制细节）与 tieir 规范（IR 细节）——本规范是**谱系与契约层**

## 5. 未讨论项（不落为结论） / Not Yet Concluded

* tieapi 规范的具体**接口形态**（错误类型/结果类型/td-zd 助手的标准签名）· 诊断码在 API 层的统一编号段分配 · 组件资产的 td 语法模板（各组件资产 td 示例）· **tac 实现细节**（API IR 精确字段定义 / 模板引擎形态 / backend 注册协议 / 首期语言集的模板骨架）· trm 嵌入的 C ABI 细节——**均未推演**，推演完成后在本文档补章

---

## 附录 / Appendix

* 术语 / Terms：同源双态（same-source dual form，td 源 ↔ zd 变体）· tieapi（统一 API 规范层）· 专项格式（specialist format，基于 td/zd 的载体）
* 演进：本文档为谱系与契约层；接口细节随生态组件实现回写（版本表）