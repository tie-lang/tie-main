# NEW — 发行版新鲜事

> 这里记录 tie 语言**当前发行版**的新功能与特色（面向读者：想快速知道"这个版本
> 有什么新东西"的人）。完整变更流水账见 [CHANGELOG.md](CHANGELOG.md)，
> 工程全貌与用法见 [README.md](README.md)。

**内部代号**：Harbor 港湾（2026.1 正式版代号，首个正式版 = 工具链第一次靠岸停泊）
**本版**：Harbor-2026.1-preview\.5
**对比基线**：Harbor-2026.1-preview\.4

***

在本次预览版中，我们聚焦**数据流互联与数据能力，与语言基础能力**：落地语言无关的 tink 帧协议与
zd v2 序列化规范，tie 编译器可直接把数据文件压成 `.zd`；同时深化表运算（复合元素表、
异构表、高阶函数、集合与映射）、铺开完整哈希/密码算法谱系，并完成内置库的 library-v2
统一重构与自定义角色插件化。

## 亮点速览

| 🧩 **数据互联**   | tink 节点帧协议 + zd v2 二进制序列化 + tiec --compress-data   |
| ------------- | -------------------------------------------------- |
| 🗃️ **表运算深化** | any 装箱/异构表、复合元素表（struct/fn/enum）、高阶函数 HOF、set/map  |
| 🧮 **哈希/密码**  | TSHA1 家族（f/b/x/r）性能内核 + 全谱系 hash/crypto/大数标准库      |
| ⚙️ **编译器**    | f64↔i64 bitcast、-compress-data、自定义角色插件化、library-v2 |
| 🧱 **其他**     | const 全局整数初值修复、跨文件 struct 修复、闭包解析修复、trit 原语        |

***

## 语言特性

### 表运算三阶深化（P1–P2）

以社区调研为纲，表数据能力分阶段落地：

* **P1 数据流箭头**：`->`/`<-` 传参与赋值；

* **P2 复合元素表**：`any` 一等待类型（函数参数/返回值/struct 字段/map 键值），
  struct/enum/fn → any 堆装箱 + `as_*` 拆箱 + `switch` 类型匹配取用，调用表达式
  `t[0](5)`、`t[i].field` 可寻址读写；

* **P2 高阶表运算**：`coll` 库的 map/filter/reduce/foreach、count\_if/any/all/
  find\_index、sort\_f64 与均值/中位数/方差/标准差、reverse/to\_string/sum/product、
  `set` 集合库（有序表 + 二分）、map\_keys/map\_values/map\_contains。
  参考探针 `tests/_p2b_probe/`、`tests/s22_probe/`。

### 整数窄化与 bitcast

* **整数窄化**：i64 传 u32 形参/变量初始化自动窄化（extern 边界双重转换修复、调用前转换
  提前），为 TSHA1 u32 通道与国际化表铺路；

* **f64↔i64 bitcast**：`bitcast_f64_i64 / bitcast_i64_f64` 原语入编译器（i64 字节级
  重解释，zd/序列化层支柱）。

### 自定义角色插件化（S3.4 v2）

角色体系彻底表驱动：内建默认表 + config roles + 项目 `roles.data.tie` + 依赖包角色定义
依序合并；安全模型＝**包可扩展编译器（纯数据声明）**、**不可扩展加载器**（字段白名单 +
\[audit] 审计拦截）；依赖发现由 `tie.pkg` 清单驱动。

### trit 三值逻辑

`-1t/0t/1t` 字面量后缀、`to_trit / trit_val` 转换原语、单目 `-t / !t`（TSHA1 trit 位平面
输出基石）。

***

## 数据互联：tink 与 zd

### tink 节点帧协议（std/tink.tie）

tink 是语言无关的通用数据流互联服务：任何组件遵守统一字节级帧协议即可作为独立进程
接入 tink 管道。帧格式定稿：

```
帧 = [ len: u32 BE ][ payload: len 字节 ][ crc: u32 BE ]
crc = CRC32-IEEE(payload)（多项式 0xEDB88320）
校验向量：crc32("123456789") == 0xCBF43926
```

* `tink.crc32 / frame_encode / frame_next / frame_skip` 四函数，纯函数表进出不碰 IO；

* 多语言库共生（Rust/C/Python/JS/Go/Zig/Lua…，`tink-<语言>` 仓库，API 与校验向量一致）；

* 探针 `std/tink_probe.tie` 全通过。

### zd v2 通用二进制序列化

语言无关、任何语言可独立实现的二进制规范：10 字节头（`TIEDBZD` 魔数 + base-48 版本 +
flags）；核心类型 i64/u64/f64/string/bool/array/map/bytes/blob/null + ext 扩展类型；
字符串字典/列式容器优化，v1 兼容读取；扩展名统一 `.zd`。

### tiec `--compress-data`

把 `.data.tie`（tie 表字面量，含 type 头与可选表名）经 DFS 平铺 + 平行表
（kind/key/value/child\_count）转为 zd record 输出 `.zd`（tdzd.tie/zdwrite.tie 驱动），
探针全通过——编译器内部 config 等数据文件可走同一条统一定义路径。

***

## 哈希 / 密码 / 大数（std 谱系）

* **TSHA1 性能内核**：状态随输出位长（state-per-n）、F1 熵完整注入、W 特化 n=48/64 内核、
  位平面标量化（标量微基准多档 3–8×）；f/b/x 三轨海绵 + r 嵌入式；

* **安全哈希**：sha256/sha512/sha3/blake2/blake3/shake128-256/merkle 树 mshake；

* **遗留/非加密哈希**：md5/sha1（遗留兼容）、siphash-2-4、xxh3-64；

* **MAC/KDF**：hmac-sha256、poly1305、ascon\_mac（+ rdu 嵌入式版）、hkdf/pbkdf2/scrypt/
  argon2id；

* **非对称**：ed25519/x25519（Curve25519 标量乘）、ecdsa P-256（extern）；

* **大数 bigint**：变长 limb 加减乘除/模幂/模逆收集库；

* **base-48**：无歧义编码原语（TSHA1 默认 48 进制输出，字符集 0-9a-zA-L）；

* **性能治理**：字符串拼接 O(n²)→StringBuilder O(n)，TSHA1 全家族基准报告就位。

所有算法纯 tie 实现（除注明 extern），均带 KAT/向量探针。

***

## 语言地基与内置库

### library-v2 三层内置库重写

按 [library-v2](docs/plans/library-v2.md) 重写 std/rdu/ext：`math` 泛型化
（`abs<T>/max<T>/min<T>`）、rdu `crc/rnd` struct 状态封装、表数据接口全面换真表参数、
`fs.read_text/json.parse_file/http.get` 用 `Result<string|i64, string>` 错误表达、
`expect_eq<T>` 泛型合并；一语义一名清理别名。旧版 v1 归档至 `tie-lang/lib_v1`。

### 健壮性修复

* 顶层 const 整数全局初值（全部整数类型）；

* 跨文件 struct 字段收集错位（按索引反查名字）；

* 闭包字面量解析：`expect_stmt_end` 统一语句结束符；

* 字节原语 byte\_read/write/concat、bit\_read/write 零 Rust 原生重写（修运行崩溃）；

* repr(C) struct 对齐（生成模块补 target datalayout）。

***

## 编译器

### 自定义角色与管线分派

角色体系表驱动（见上），driver 头部扫描前经 config 分层合并加载注册表，管线按
`output=lib/check/exe/pass` 查表分派。

### 挑战与回退记录

字符串拼接就地追加优化（子代理实测 300×）因别名安全自举不稳已回退，详见
docs/language.md 性能节记录。
