# 规划：tieir 格式细节（二进制序列化 + 版本迁移转换器）
*EN: Plan: tieir Format Details (Binary Serialization + Version Migration Converter)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> 本文档定义 tieir（tie-IR 分发格式）的格式细节。
> 决策汇总：**S3**（二进制序列化 + dump 工具）+ **V3**（版本迁移转换器）。
> 基础：compiler/middle/ir_meta.tie 已实现 sym_table/export_table/inst_span/
> 模块头元数据——tieir 骨架已存在（注释明确"pkg 字符串源序列化为二进制 IR，
> 产出 .tieir 序列化（T6.1）"）。
> 关联：包模型（tieir 分发 L2、签名 P5c）、接口模型（L4b port 即接口）、
> 库模型（依赖图/版本）。
>
> EN: Status: **Plan** (design discussion finalized on 2026-08-15, not implemented)
> EN: This document defines the format details of tieir (the tie-IR distribution format).
> EN: Decision summary: **S3** (binary serialization + dump tool) + **V3** (version migration converter).
> EN: Foundation: compiler/middle/ir_meta.tie already implements sym_table/export_table/inst_span/ module-header metadata — the tieir skeleton already exists (comment states "pkg string source serialized to binary IR, producing .tieir serialization (T6.1)").
> EN: Related: package model (tieir distribution L2, signature P5c), interface model (L4b port-as-interface), library model (dependency graph/version).

## 1. 现状基础（ir_meta.tie 已有能力）
*EN: 1. Current Foundation (Existing ir_meta.tie Capabilities)*

| 已有结构 | 内容 | tieir 用途 |
| --- | --- | --- |
| inst_span | 指令/符号 id → 文件/行/列 | 段 7（调试信息） |
| sym_table | 函数/struct/命名空间/全局 + 签名 + 可见性 + span | 段 4（符号表） |
| export_table | 公共 API 清单 | 段 6（导出表） |
| doc_comment | 符号 → 文档字符串 | 段 7（文档） |
| 模块头 | 名称/版本/依赖图/IR 版本/编译器版本 | 段 2（模块头） |
| 列式表 | ir_funcs_*/ir_blocks_*/ir_insts_*/ir_ops | 段 5（IR 主体） |

EN: This table maps the existing structures in ir_meta.tie to their tieir sections: inst_span → Section 7 (debug info), sym_table → Section 4 (symbol table), export_table → Section 6 (export table), doc_comment → Section 7 (documentation), module header → Section 2 (module header), and the columnar tables → Section 5 (IR body).

**结论：tieir 不是从零设计——是现有结构的序列化 + 封装。**

EN: **Conclusion: tieir is not designed from scratch — it is serialization + wrapping of existing structures.**

## 2. 序列化格式（S3：二进制 + dump 工具）
*EN: 2. Serialization Format (S3: Binary + dump Tool)*

### 2.1 二进制布局（compact）
*EN: 2.1 Binary Layout (compact)*

```
.tieir 文件布局：
┌─────────────────────────────────────┐
│ 1. 魔数 + 格式版本                   │  "TIEIR" + u32 版本（0x01）
├─────────────────────────────────────┤
│ 2. 模块头                            │  名称/版本/语言版本/依赖图/IR 版本/编译器版本
├─────────────────────────────────────┤
│ 3. 类型表                            │  types 编码 id（i64=3 等）+ struct/enum 布局
├─────────────────────────────────────┤
│ 4. 符号表（sym_table）               │  函数/struct/命名空间/全局 + 签名 + 可见性
├─────────────────────────────────────┤
│ 5. IR 主体（列式表）                 │  ir_funcs_*/ir_blocks_*/ir_insts_*/ir_ops
├─────────────────────────────────────┤
│ 6. 导出表（export_table）            │  公共 API 清单（L4b port 即接口的载体）
├─────────────────────────────────────┤
│ 7. span/文档段（inst_span/doc）      │  源码位置 + 文档注释（--strip 可去）
└─────────────────────────────────────┘
```

- 二进制紧凑（比文本小 3-5x）、解析快、与签名/哈希天然配合
  - EN: binary is compact (3-5x smaller than text), fast to parse, and works naturally with signatures/hashes
- 字符串全部 id 化（interner）：字符串表随段 4/5 携带
  - EN: all strings are interned to ids (interner): the string table is carried with sections 4/5

### 2.2 dump 工具（可读性）
*EN: 2.2 dump Tool (Readability)*

```bash
tie dump-irt <pkg.tieir>          # 输出可读文本（复用 dump_meta）
tie dump-irt <pkg.tieir> --section 6   # 只看导出表
```
EN: The dump tool prints reader-friendly text for debugging/auditing/CI (export-surface diff), reusing the existing `ir_meta.dump_meta()` implementation.

- 调试/审计/CI 检查（导出面 diff）
  - EN: debugging/auditing/CI checking (export-surface diff)
- 与 ir_meta.dump_meta() 现有实现衔接
  - EN: links to the existing `ir_meta.dump_meta()` implementation

## 3. 模块头（段 2）
*EN: 3. Module Header (Section 2)*

| 字段 | 内容 | 用途 |
| --- | --- | --- |
| 名称 | 包名 | 消费方校验 |
| 版本 | 包版本（semver） | 依赖解析（P1b 双版本） |
| 语言版本 | 编译时 tie 版本 | 双版本校验 |
| IR 版本 | tie-IR 格式版本（u32） | 兼容检测（V3 触发条件） |
| 编译器版本 | tiec 版本 | 溯源 |
| 依赖图 | 依赖包名+版本列表 | 链接解析 |

EN: This table lists the module-header fields: name, version (semver), language version, IR version (u32), compiler version, and dependency graph, along with their contents and uses.

## 4. IR 主体序列化（段 5：列式表直写）
*EN: 4. IR Body Serialization (Section 5: Direct Columnar-Table Write)*

```
函数段：funcs: name_id / ret_ty / params_off / params_cnt / param_tys / entry / exported
块段：  blocks: func / name / start / end
指令段：insts: op / ty / val / ops_off / ops_cnt
操作数段：ops: 扁平 i64 + kind 表（OK_VALUE/OK_BLOCK/OK_IMM）
```

- 列式表 = 扁平 i64 数组，顺序写出即可（天然可序列化）
  - EN: the columnar table = a flat i64 array, written out in order (naturally serializable)
- 消费方：读出列式表 → 直接进入语义检查/链接流程（免前端）
  - EN: consumers: read the columnar table → go directly into semantic-check/link flow (no frontend needed)
- 定宽 i64 编码：每列一个计数 + 数据块；将来可加 varint 优化（后置）
  - EN: fixed-width i64 encoding: a per-column count + data block; varint optimization can be added later (deferred)

## 5. 导出表（段 6，L4b 载体）
*EN: 5. Export Table (Section 6, L4b Carrier)*

```text
export_table:
  func:   name / 签名（param_tys + ret）/ 可见性 pub / span
  struct: name / 字段布局（类型 + 偏移）      ← repr(C) 互操作需要
  enum:   name / 变体 + payload 类型
  port:   name / 方法签名集                    ← L4b：port 即接口
  const:  name / 值
```

- **导出范围（默认推荐，待确认）**：
  - EN: **Export scope (recommended by default, pending confirmation)**:
  - port 声明导出（L4b 信息隐藏的核心——消费方只见 port）
    - EN: port declarations exported (the core of L4b information hiding — consumers only see ports)
  - struct 布局导出（repr(C) 互操作、跨包传 struct 需要）
    - EN: struct layouts exported (needed for repr(C) interop and passing structs across packages)
  - impl 块**不导出**（实现隐藏，可替换）
    - EN: impl blocks are **not exported** (implementation hidden, replaceable)
- 消费方按导出表编译（接口依赖 P4b 的解析基础）
  - EN: consumers compile against the export table (the basis for resolving interface dependency P4b)

## 6. 版本策略（V3：版本迁移转换器）
*EN: 6. Version Strategy (V3: Version Migration Converter)*

```
版本号：IR 版本 = u32（模块头段 2）
消费方读取：
  IR 版本 == 当前编译器版本  → 直接加载
  IR 版本 < 当前版本         → 提示运行 tieir-migrate 转换
  IR 版本 > 当前版本         → "需升级编译器"（无法降级）
```

```bash
tieir-migrate v0x01.v0x02 pkg.tieir -o pkg_v2.tieir   # 旧 IR → 新 IR
```

- **V3 迁移转换器**：旧版本 IR → 新版本 IR 的转换工具
  （与"迁移脚本"总决策一致：tieir-migrate 也是迁移工具链一员）
  - EN: **V3 migration converter**: a tool that converts old-version IR → new-version IR (consistent with the general "migration script" decision: tieir-migrate is also a member of the migration toolchain)
- 转换器按版本对实现（v1→v2、v2→v3...），链式升级
  - EN: the converter is implemented per version pair (v1→v2, v2→v3...), chained upgrades
- 第一版：编译器只支持当前版本（V1 硬校验语义），旧版经迁移转换器升级
  - EN: first version: the compiler only supports the current version (V1 hard-validation semantics); old versions are upgraded via the migration converter

## 7. 校验与安全（与 P5c 咬合）
*EN: 7. Validation and Security (Interlocking with P5c)*

```
发布：tieir + 内容哈希 + 签名（发布者私钥）
安装：校验哈希（完整性） + 公钥验签（真实性） + IR 语法校验（防伪造）
```

- 内容哈希：对段 2-7 计算（段 1 版本不计）
  - EN: content hash: computed over sections 2-7 (section 1 version excluded)
- 签名：哈希 + 签名者信息（P5c）
  - EN: signature: hash + signer information (P5c)
- **IR 语法校验**（消费方读取时）：列长度匹配、id 边界（value/block 引用在
  范围内）、类型引用存在（types 表内有定义）、opcode 合法——防损坏/伪造 IR
  - EN: **IR syntax validation** (when consumed): column-length matching, id bounds (value/block references within range), type references exist (defined in the types table), and valid opcodes — to prevent corrupted/forged IR
- 校验失败 = 安装报错（安全底线）
  - EN: validation failure = install error (security baseline)

## 8. span/文档段（段 7，可选）
*EN: 8. span/Documentation Section (Section 7, Optional)*

- **默认保留**（调试价值：错误定位、hover 文档、stack trace 文件行号）
  - EN: **kept by default** (debug value: error location, hover docs, stack-trace file/line numbers)
- `--strip` 编译选项：去掉 span/文档（体积 -30~50%，闭源场景防源码结构泄露）
  - EN: `--strip` compiler flag: removes span/docs (30-50% smaller, prevents source-structure leaks in closed-source scenarios)
- 与"源码保护"目标权衡：span 泄露行号结构——闭源发布用 --strip
  - EN: trade-off with the "source protection" goal: spans leak line-number structure — use --strip for closed-source releases

## 9. 编译器实现拆解（tiec 自举）
*EN: 9. Compiler Implementation Breakdown (tiec Self-Hosting)*

| 模块 | 改动 |
| --- | --- |
| 序列化器 | 列式表 + 元数据 → 二进制（段 1-7） |
| 反序列化器 | 二进制 → 列式表 + 元数据（含语法校验） |
| 版本检查 | 模块头 IR 版本比对 + 迁移提示 |
| dump 工具 | dump-irt 子命令（复用 dump_meta） |
| tieir-migrate | 版本转换器（vX→vX+1，链式） |
| 哈希/签名 | 内容哈希 + 验签集成（P5c） |
| --strip | span/文档段裁剪选项 |

## 10. 决策记录（讨论产物）
*EN: 10. Decision Log (Discussion Output)*

| 决策点 | 结论 | 备选（未选） |
| --- | --- | --- |
| 序列化 | S3：二进制 + dump 工具 | 纯文本、纯二进制 |
| 版本策略 | V3：版本迁移转换器（tieir-migrate） | V1 硬校验、V2 多版本支持 |
| 导出范围 | port 声明 + struct 布局导出，impl 隐藏（默认，待确认） | 全导出 |
| span 保留 | 默认保留 + --strip（默认，待确认） | 默认 strip |
| 基础 | 扩展 ir_meta（现有 sym/export/span 结构） | 全新格式 |

## 11. 未决问题
*EN: 11. Open Questions*

1. **导出范围确认**：port + struct 布局导出、impl 隐藏——确认？（见 §5）
   EN: **Export-scope confirmation**: export port declarations + struct layouts, hide impl — confirm? (see §5)
2. **span 保留确认**：默认保留 + --strip 选项——确认？（见 §8）
   EN: **span-retention confirmation**: keep by default + --strip flag — confirm? (see §8)
3. **字符串表编码**：id 化字符串的压缩（简单长度前缀 vs varint 优化，后置）
   EN: **string-table encoding**: compression of interned strings (simple length-prefix vs varint optimization, deferred)
4. **IR 语法校验的深度**：结构校验（第一版）vs 语义校验（类型引用有效性，
   是否消费方重新做）
   EN: **depth of IR syntax validation**: structural validation (first version) vs semantic validation (type-reference validity, whether consumers redo it)
5. **tieir 与源码双发布**：开源包同时发源码 + tieir（消费方自选），
   闭源只发 tieir（--strip）——发布选项形态
   EN: **dual release of tieir and source**: open-source packages ship both source + tieir (consumer's choice), closed-source ships only tieir (--strip) — the form of the release option