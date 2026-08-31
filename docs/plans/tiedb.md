# 规划：tieDB——tie 语言自写的数据库接口库
*EN: Plan: tieDB — a self-written database interface library in the tie language*

> 状态：**规划**（架构已定，分批实现）
> 所属：Harbor（2026.1）数据库能力
> 背景：tie 需要数据库能力（关系型 + 向量检索"一把抓"）。tieDB **不是独立数据库程序**，
> 而是 tie 语言自写的**库集合**：核心交付 `tiedbapi`（与其他数据库软件交互的统一 API）
> 与 **tie:data 压缩**（tie:zd）。
>
> EN: Status: **Plan** (architecture decided, implemented in batches)
> EN: Belongs to: Harbor (2026.1) database capability
> EN: Background: tie needs database capability (relational + vector retrieval "all-in-one"). tieDB is **not a standalone database program**, but a **collection of libraries** written in tie: the core deliverable `tiedbapi` (a unified API for interacting with other database software) and **tie:data compression** (tie:zd).

## 0. 架构总览（LLVM 式分层）
*EN: 0. Architecture Overview (LLVM-style Layering)*

LLVM 式开发 = 底层核心库 + 模块化 + 顶层工具。tieDB 对应：**tiedbapi 核心 + 后端适配层
+ 压缩持久化 + 工具**，每层独立模块、接口清晰、可替换。

EN: LLVM-style development = low-level core library + modularization + top-level tools. tieDB corresponds to: **tiedbapi core + backend adaptation layer + compressed persistence + tools**, where each layer is an independent module with clear, replaceable interfaces.

```
┌─ 用户程序（任意 tie 代码）───────────────────────────┐
│  import "../../ext/dbapi/api.tie"                 │
│  var db = tiedb.connect("sqlite://app.db")         │
│  var users = db.collection("users")                │
│  users.insert([...]) / users.query([...])          │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  ext/dbapi —— tieDB 的对外 API 库（tiedbapi 前端）     │
│    Connection/Collection 两级对象                    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  tieDB（tieDB/ 目录，tie 语言自写库集合，LLVM 式模块化）│
│  ┌─ tiedbapi 核心 ──────────────────────────────┐   │
│  │  api.tie     统一 API（Connection/Collection）│   │
│  │  query.tie   查询执行（条件/检索请求→执行）    │   │
│  ├─ 后端适配层 backend/ ────────────────────────┤   │
│  │  local.tie   本地载体：std/db（tie:data）      │   │
│  │  sqlite.tie  SQLite 适配（Rust 桥，后续）      │   │
│  │  pg.tie      PostgreSQL 适配（Rust 桥，后续）  │   │
│  │  mongo.tie   MongoDB 适配（Rust 桥，后续）     │   │
│  │  vec.tie     向量检索：接入 ext/vecsearch      │   │
│  ├─ 压缩 persist/ ──────────────────────────────┤   │
│  │  zd.tie      tie:data ↔ tie:zd（zstd/brotli） │   │
│  └─ 工具 tools/ ────────────────────────────────┤   │
│     compact.tie CLI：zd 压缩/解压（data↔zd）      │   │
└──────────────────┬──────────────────────────────────┘
                   │ 复用（保持不变）
┌──────────────────▼──────────────────────────────────┐
│  std/db（载体：tie:data 解析/序列化）                  │
│  ext/vecsearch（向量索引：Flat/HNSW/IVF-PQ/DiskANN）  │
│  rdu/rdb（嵌入式：tieDB API 小部分功能）                │
└──────────────────────────────────────────────────────┘
```

## 1. 职责划分
*EN: 1. Responsibility Division*

| 层 | 归属 | 职责 |
| --- | --- | --- |
| API 前端 | `ext/dbapi` | tieDB 的对外库：Connection/Collection 两级对象；调 tieDB tiedbapi |
| **tiedbapi 核心** | `tieDB/` | **与其他数据库软件交互的统一 API**：connect 按 url 分派后端、CRUD、查询、检索 |
| 后端适配 | `tieDB/backend/` | SQLite / PostgreSQL / MongoDB 适配层（Rust 桥：rusqlite/postgres/mongodb）+ 本地载体（std/db） |
| 向量检索 | `tieDB/backend/vec.tie` | 接入 `ext/vecsearch`（不变） |
| 压缩 | `tieDB/persist/zd.tie` | **tie:data 压缩**：data 文本 ↔ zd 字节（zstd/brotli）；CLI compact/decompress |
| 载体库 | `std/db`（不变） | tie:data 解析/序列化（纯数据格式） |
| 向量索引 | `ext/vecsearch`（不变） | Flat/HNSW/IVF-PQ/DiskANN 算法 |
| 嵌入式 | `rdu/rdb`（不变） | 嵌入式 MCU 场景，tieDB API 小部分子集 |

EN: This table lists the division of responsibilities: the API frontend (`ext/dbapi`), the tiedbapi core (`tieDB/`), backend adapters (`tieDB/backend/`), vector retrieval (`tieDB/backend/vec.tie`), compression (`tieDB/persist/zd.tie`), the carrier library (`std/db`, unchanged), vector index (`ext/vecsearch`, unchanged), and the embedded subset (`rdu/rdb`, unchanged).

> tieDB **不提供网络服务**（非独立服务器）。与其他数据库软件的交互走后端适配层
> （进程内桥：SQLite/PG/Mongo 驱动），而非 TCP。
>
> EN: tieDB **does not provide network services** (it is not a standalone server). Interaction with other database software goes through the backend adaptation layer (in-process bridges: SQLite/PG/Mongo drivers), not TCP.

## 2. tie:zd 文件类型（tieDB 核心，二进制序列化格式）
*EN: 2. The tie:zd File Type (tieDB Core, Binary Serialization Format)*

> **实现原则（用户决策）**：**tie:zd 必须用 tie 实现，tie 实现是第一优先级**——不用 Rust
> 压缩库。**设计思路参考 MessagePack**（自描述二进制：类型标签 + 紧凑编码），
> **并参考 Protobuf**（varint 变长整数 + 字段编号 wire type）。zd 是 tie 数据
> （标量/表/map/元组/record）的**紧凑二进制序列化格式**，非"压缩文本"。
>
> EN: **Implementation principle (user decision)**: **tie:zd must be implemented in tie, and the tie implementation is top priority** — no Rust compression library. **The design is inspired by MessagePack** (self-describing binary: type tags + compact encoding) **and by Protobuf** (varint variable-length integers + field-number wire types). zd is a **compact binary serialization format** for tie data (scalars/tables/maps/tuples/records), not "compressed text".

- **声明方式**：`type tie<zd>` 头部声明；因内容不可读，**主要用文件名** `xxx.zd.tie` 声明（角色后缀约定）
  - EN: **Declaration**: `type tie<zd>` header declaration; since the content is unreadable, **the file name** `xxx.zd.tie` is mainly used to declare it (role-suffix convention)
- **格式（MessagePack 分区思路）**：每值 = 类型标签 + 值字节
  - EN: **Format (MessagePack partitioning idea)**: each value = type tag + value bytes
  - 正整数 `0x00-0x7f`（fixint，1 字节）；负整数 `0xe0-0xff`（-32..-1）
    - EN: positive integer `0x00-0x7f` (fixint, 1 byte); negative integer `0xe0-0xff` (-32..-1)
  - 定宽整数：`0xcc`uint8 / `0xcd`uint16 / `0xce`uint32 / `0xcf`uint64 / `0xd0`int8 / `0xd1`int16 / `0xd2`int32 / `0xd3`int64
    - EN: fixed-width integers: `0xcc`uint8 / `0xcd`uint16 / `0xce`uint32 / `0xcf`uint64 / `0xd0`int8 / `0xd1`int16 / `0xd2`int32 / `0xd3`int64
  - 浮点：`0xca`float32 / `0xcb`float64；布尔 `0xc2`false / `0xc3`true
    - EN: floats: `0xca`float32 / `0xcb`float64; booleans `0xc2`false / `0xc3`true
  - 字符串：`0xa0-0xbf`fixstr(≤31) / `0xd9`str8 / `0xda`str16 / `0xdb`str32（UTF-8 字节）
    - EN: strings: `0xa0-0xbf`fixstr(≤31) / `0xd9`str8 / `0xda`str16 / `0xdb`str32 (UTF-8 bytes)
  - 数组：`0x90-0x9f`fixarray(≤15) / `0xdc`array16 / `0xdd`array32
    - EN: arrays: `0x90-0x9f`fixarray(≤15) / `0xdc`array16 / `0xdd`array32
  - map：`0x80-0x8f`fixmap(≤15) / `0xde`map16 / `0xdf`map32
    - EN: maps: `0x80-0x8f`fixmap(≤15) / `0xde`map16 / `0xdf`map32
  - **tie 扩展标签**（自定义区 `0xc4-0xc9`）：`0xc4`char / `0xc5`trit / `0xc6`tuple
    - EN: **tie extension tags** (custom zone `0xc4-0xc9`): `0xc4`char / `0xc5`trit / `0xc6`tuple
- **record/struct 编码（Protobuf 思路）**：每字段 = `tag(varint: field_number<<3 | wire_type)` + 值；
  wire_type：0=varint、1=64bit、2=len-delimited、5=32bit；字段编号 1..15 单字节；
  **向前兼容**——新增字段加编号，旧数据照常解析
  - EN: **record/struct encoding (Protobuf idea)**: each field = `tag(varint: field_number<<3 | wire_type)` + value; wire_type: 0=varint, 1=64bit, 2=len-delimited, 5=32bit; field numbers 1..15 single byte; **forward compatible** — new fields get new numbers, old data still parses
- **tie 实现**：`tieDB/persist/zd.tie`（namespace zd，纯 tie，字节操作用 `&`/`>>` 位运算 + byte 表）：
  - EN: **tie implementation**: `tieDB/persist/zd.tie` (namespace zd, pure tie, byte operations use `&`/`>>` bitwise ops + byte tables):
  - 原语：`write_varint` / `read_varint`（Protobuf 7 位分组）、`encode_i64/f64/bool/char/string/table/map/tuple`、
    `decode_*(bytes, pos) -> (值, 新位置)`（元组返回，标签校验）
    - EN: primitives: `write_varint` / `read_varint` (Protobuf 7-bit grouping), `encode_i64/f64/bool/char/string/table/map/tuple`, `decode_*(bytes, pos) -> (value, new position)` (tuple return, tag validation)
  - 文件：`zd.save(path, bytes)` / `zd.load(path) -> table`（byte_write/byte_read，含魔数 `"TIEDBZD"` 头）
    - EN: files: `zd.save(path, bytes)` / `zd.load(path) -> table` (byte_write/byte_read, with magic number `"TIEDBZD"` header)
  - 组合：tiedb 层按 schema 逐字段编码（record = 字段编号编码）
    - EN: composition: the tiedb layer encodes field by field according to the schema (record = field-number encoding)
- **工具**：`tiedb compact in.data.tie -o out.zd.tie` / `decompress`（tie 实现）
  - EN: **tools**: `tiedb compact in.data.tie -o out.zd.tie` / `decompress` (tie implementation)
- **消费**：读 zd → 校验头 → decode → tie 结构 → 建索引
  - EN: **consumption**: read zd → validate header → decode → tie structure → build index

## 3. 统一 API（ext/dbapi，两级对象）
*EN: 3. Unified API (ext/dbapi, Two-Level Objects)*

```tie
var db = tiedb.connect("tiedb://127.0.0.1:7788")   // Connection 对象
db.create("users", ["id": "i64 pk", "name": "string"])   // 0-SQL 建集合
var users = db.collection("users")                 // Collection 对象（存变量即可寻址）
users.insert(["id": "1", "name": "张三"])
var rows = users.query(["name": "张三"])            // 关系查询
var vecs = db.collection("vectors")
vecs.insert(["id": "1", "vec": [0.1, 0.2]])
var hits = vecs.search([0.1, 0.2], 10)             // 向量 ANN
db.save("app.data.tie") / db.save("app.zd.tie")    // 持久化（明文/压缩）
db.close()
```
EN: This `tiedb.connect(...)` API is the two-level object model (Connection + Collection): connect creates a Connection, `db.collection(...)` returns a Collection object for relational queries and vector ANN search, and `db.save(...)` persists data in plain text (`tie:data`) or compressed (`tie:zd`) form.

## 4. tieDB CLI（工具，非服务）
*EN: 4. tieDB CLI (Tool, Not a Service)*

```
tiedb compact in.data.tie -o out.zd.tie        # tie:data → tie:zd（压缩）
tiedb decompress in.zd.tie -o out.data.tie     # tie:zd → tie:data（解压）
tiedb check in.data.tie                        # 校验 tie:data 结构
```

## 5. 高性能设计
*EN: 5. High-Performance Design*

- **LLVM 式完全模块化**：tiedbapi 核心 / backend 适配 / persist 压缩 / tools 四层独立模块，纯接口互调
  - EN: **LLVM-style full modularity**: four independent layers — tiedbapi core / backend adapters / persist compression / tools — communicating purely through interfaces
- **后端隔离**：SQL 三后端走 Rust 桥（rusqlite bundled / postgres / mongodb），接口一致（connect/exec/query/close），tieDB 侧统一
  - EN: **backend isolation**: the three SQL backends use Rust bridges (rusqlite bundled / postgres / mongodb) with identical interfaces (connect/exec/query/close), unified on the tieDB side
- **索引优先**：向量列建 vecsearch 索引（HNSW 默认）、关系列建 map 二分索引
  - EN: **index-first**: vector columns get a vecsearch index (HNSW by default), relational columns get a map binary-search index
- **批量写入**：`insert_many` 单次批量
  - EN: **batch writes**: `insert_many` for single batch inserts
- **压缩持久化**：zd 体积小、IO 快（zstd/brotli）
  - EN: **compressed persistence**: zd is small in size and fast on IO (zstd/brotli)
- **本地优先**：local:// 载体（std/db）零依赖先跑通，SQL 后端后置
  - EN: **local-first**: the local:// carrier (std/db) runs with zero dependencies first; SQL backends come later

## 6. 实施顺序
*EN: 6. Implementation Order*

| 阶段 | 内容 |
| --- | --- |
| 0 | tie:zd 文件类型：角色识别三处（prep/core.tie、crates/tie-prep、tiec driver）+ 文件名约定 |
| 1 | std/db 载体完备：tie:data 解析器（纯 tie，多种数据结构）+ 序列化 |
| 2 | tieDB 骨架：tiedbapi（api.tie/query.tie）+ local 后端（std/db）+ CLI check |
| 3 | zd 压缩：persist/zd（zstd/brotli）+ compact/decompress + db.save(zd) |
| 4 | 向量检索：vec 后端接入 ext/vecsearch（Flat 先行）→ search API |
| 5 | SQL 后端适配：SQLite 桥 → PostgreSQL → MongoDB（Rust 桥 + 适配层） |
| 6 | ext/vecsearch 算法分批：Flat → HNSW → IVF-PQ → DiskANN |
| 7 | rdu/rdb 嵌入式子集 |

EN: This table shows the staged implementation order: from the tie:zd file type and std/db carrier, through the tieDB skeleton, zd compression, vector retrieval, SQL backend adapters, ext/vecsearch algorithms, and finally the rdu/rdb embedded subset.

## 7. 相关文件
*EN: 7. Related Files*

| 文件 | 作用 |
| --- | --- |
| tieDB/ | 程序目录（tie 自写，对照 compiler/ 组织） |
| ext/dbapi/ | 客户端库（Connection/Collection + 协议） |
| ext/vecsearch/ | 向量索引算法（flat/hnsw/ivfpq/diskann） |
| std/db/ | tie:data 载体（解析/序列化） |
| rdu/rdb | 嵌入式 db 子集 |
| docs/language.md / README.md | 文件类型表 + 路线图同步 |

EN: This table lists the related files: the `tieDB/` program directory, the `ext/dbapi/` client library, the `ext/vecsearch/` vector index algorithms, the `std/db/` tie:data carrier, the `rdu/rdb` embedded DB subset, and the docs for file-type tables and roadmap sync.