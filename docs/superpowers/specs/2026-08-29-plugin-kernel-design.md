# 设计：tie 全平台插件化（核心 + 插件）

> 状态：**设计定稿**（2026-08-29 讨论定稿，S1 起逐步实现）
> 关联：角色模型（role-model.md，S3.4 插件化）、包模型（package-model.md，tieir 分发 L2/P5c）、
> tieir 格式（tieir-format.md）、动态库（dynamic-library.md，M5）、编译解耦（compiler-decouple.md）。

## 1. 目标与决策汇总

**目标**：tie 平台完全插件化——分为**核心**与**插件**。核心只负责**加载**插件；
核心（机制层）**不可被插件修改**；编译管线本身亦可扩展。

| 决策点 | 结论 |
|---|---|
| 架构方案 | **B：统一注册表微内核**。核心 = 加载器 + 总注册表 + 审计器 + 执行骨架，零行为；一切行为皆为注册项 |
| 插件形态 | **数据 + 代码**混合；以**包**分发，包使用 **tieir**（中间表示）分发 |
| 管线扩展 | 管线 = 注册项（数据），支持锚点插入/替换 pass；核心执行骨架零行为 |
| 管理和版本化 | 每个注册模块（插件/包）携带稳定 **id** 与 **version**（双版本：语言版本 + 包版本） |
| 配置形态 | 开发态 `tie:data`（明文）；分发态 `tie:zd`（压缩变体，体积小 + 增加修改难度） |
| 凭证 | 每个包自带凭证（类似签名、与代码无关的包属性）；**去中心化**信任锚（无官方 registry 亦安全） |
| 指纹 | 每次发行以 BLAKE2 家族生成特征记录包中：**单文件 BLAKE2s-256，整包树根 BLAKE2b-512** |

## 2. 架构：核心边界

**核心不变量**：核心不含任何"行为"（无硬编码管线、无内置函数实现、无角色清单、
无 CLI 子命令），只含**机制**——注册表、审计器、加载器、执行骨架、tieir 读取器、
IR/类型内核、安全哈希底座。一切行为一律是注册项。

```
核心微内核（机制层，无行为）
├── boot         引导加载器（双阶段注册）
├── registry     通用注册表（名称/字段 → kind → 实现引用）
├── auditor      安全审计器（字段白名单 / 未知字段拦截 / 版本+哈希+验签）
├── executor     管线执行骨架（按注册的管线数据分派已注册 pass）
├── lib/blake2   BLAKE2s-256 + BLAKE2b-512（审计链底座，纯 tie 实现）
├── tieir 读取器 / dispatch 分派表 / columnar / interner / types
└── 内建引导集（随二进制嵌入，boot 最先注册——保证自举无外部依赖）
```

**引导安全（bootstrap）**：内建引导集（默认管线定义 + 内建函数族注册项 + 内建角色表 +
内建 CLI 骨架）作为一个**启动插件**内嵌随二进制；boot 阶段最优先注册。tiec 编译自身时
无需任何外部插件，注册序列照常，自举安全；外部插件只是更多注册项，无法抢占已注册的
内建项（先注册者优先）。

## 3. 注册表与 id/version

**注册项 schema**（核心机制，唯一固定结构）：

```
注册项 = {
  id:       string        // 全局唯一模块标识，如 "pkg:my_pkg::pass_inliner"
  kind:     pass | pipeline | builtin | role | cli | lib | ...
  version:  semver        // 包版本，如 1.2.3
  tie:      ">=2026.1"    // 语言版本约束（P1b 双版本）
  impl:     fn 值 | 数据表 | tieir 引用 | port 导出表 | 管线定义数据
  deps:     [依赖模块 id + 版本约束]   // 显式声明，审计器校验可解析
  meta:     { 来源: 内建|config|项目|依赖包, 注册序 }   // 审计与优先级
}
```

**三条不变式**：

1. **id 持久稳定，与内部序号解耦**：dispatch 登记序号、pass_registry 行号-id 只是内部
   映射可重建；外部世界只能以 `id+version` 引用模块。同 id 同 version 幂等忽略；同 id
   异 version 按优先级仲裁（内建 < config < 项目 < 依赖包）；`dependencies` 显式约束
   （tie.pkg `{mod: ^1.2}`）优先于注册序。
2. **版本门禁**：审计阶段校验 IR 版本（tieir 格式版本 ≠ 编译器 IR 版本 → 拒绝）、语言
   版本（`tie` 约束 vs 当前 tiec）、依赖图可解析性。
3. **id/version 自身受审计**：id 段名符合白名单（`[a-z0-9_]+(\.[a-z0-9_]+)*`，禁止
   `hook/script/exec` 等恶意段名沿用）；version 必须是合法 semver；未知字段拦截。

**管线 = 注册项 + 锚点扩展**：默认管线定义是 `pipeline:default` 注册项（数据：有序 pass
引用列表）。外部插件声明 `extends: pipeline:default, anchor: <pass>` 在指定锚点前后插入/
替换 pass——走同一注册与审计通道。核心执行骨架只"读管线数据 → 按引用查 pass → 执行"。

**CLI 子命令**：每条命令（`tie test/bench/...`）也是注册项（`cli:test`），核心只保留最小
命令分派骨架；未注册命令报"未知命令"。

## 4. 配置形态：tie:data → tie:zd

**开发态**：配置以 `tie:data` 角色明文书写（可读、可 diff）。
**分发态**：`tie publish` 将 data 转换为 `tie:zd` 压缩变体（`xxx.zd.tie`，二进制、人类不可读）。

- 体积：zstd/lz4 压缩（ext/codec 已具备，零新依赖）
- "增加修改难度"：压缩即混淆——文本不可读、难以手工篡改；真正的防改依赖加载器审计链
  （指纹 + 凭证）
- 实现落点：driver 已识别 `.zd.tie` 为 tie:data 的二进制压缩变体并预留 tiedb
  compact/decompress 原语（compiler/driver.tie）
- 加载器对 data/zd 一视同仁：`zd` 先解压再走全链审计；格式封装在加载器，插件永远不
  知道自己在被审计的是明文还是压缩体——加载器不可被扩展（S3.4 三层分离）

## 5. 安全模型：凭证 + 指纹（双正交）

### 5.1 指纹（发了什么）——防篡改，无中心

```
fingerprint = {
  perfile: { "src/a.tie": BLAKE2s-256, "data.zd": BLAKE2s-256, ... },  // 单文件哈希
  root:    BLAKE2b-512(tree_hash)                                      // 包树根哈希，签名对象
}
```

- 发行时（`tie publish`）：递归计算 BLAKE2 写入 `tie.pkg hash` + tie.lock 固化
- 加载时：加载器重算文件哈希与 fingerprint 比对；不符 → [audit] 拦截（定位到具体文件）
- **BLAKE2s-256**（32 字节，32 位优化、快）用于单文件级海量小哈希；
  **BLAKE2b-512**（64 字节，64 位优化、抗碰撞最强）用于整包树根与凭证签名对象
- 无 MD5/SHA-1 碰撞弱点、无长度扩展攻击面；BLAKE2s/b 共享轮函数（实现量适中）
- 实现归属：核心 `lib/blake2.tie`（审计链第①道不可绕过；放 std 会破坏核心单向依赖）；
  发布侧复用同一实现（两侧算法不漂移）

### 5.2 凭证（谁发的）——认证，去中心化

凭证 = 包自带的发布者身份属性，与代码内容无关（标识"谁发布的"，不评价内容好坏）。

```
tie.pkg（凭证区，包自带）
├── publisher: my_pkg_org
├── pubkey:    <Ed25519 公钥>       # 随包走（自包含）
├── pubkey_fp: a1b2…c3d4 (16B)      # 公钥指纹（身份锚）
└── package.sig                     # 签名块：私钥对 root(BLAKE2b-512) 的签名
```

**验证链（无官方 registry 亦安全）**：

1. 指纹树重算（内容原样，无需任何外部信任）
2. 包内自带 pubkey 验签 package.sig 对 root 的签名（身份自洽）
3. **TOFU 信任锚**：首次加载经 ①② 通过后，向用户呈现 `pubkey_fp`（16 字节十六进制）
   确认信任 → 固化进 `tie.lock`；后续比对 fp 一致才继续；**同 id 不同 fp → [audit] 拦截**
   （疑似冒名/换钥）

- 无 registry 时的安全：攻击者无发布者私钥，无法对新包伪造与锚一致的签名；首次信任
  由用户人工核对 fp（发布者可于官网/README 公布 fp 供外带核对）
- 密钥轮换：换钥 = 新 pubkey → 新 fp → 触发③重新确认，无需撤销列表

### 5.3 验证顺序（完整审计链，任一环失败即拦截）

```
① 指纹树重算（BLAKE2s per-file + BLAKE2b root）
② 包内验签（pubkey 对 root 签名）
③ fp 与 tie.lock 锚一致性（首次 = 提示信任）
④ IR 版本 → ⑤ id/version 合法性 → ⑥ 字段白名单 → ⑦ 依赖解析 → ⑧ 注册冲突仲裁
```

### 5.4 与既有资产对齐

| 现有资产 | 对齐方式 |
|---|---|
| S3.4 三层分离 | 验签 + 指纹 + 字段审计全部收敛进加载器审计链；插件无感知、无回调 |
| P5c（签名/哈希校验，已定稿未实现） | 本设计即 P5c 落地形态，实现时回填 package-model.md |
| tieir_ser.hash_bytes（FNV-1a） | 仅保留为 tieir 段完整性低强校验；安全哈希统一走 BLAKE2（职责分离） |
| std/crypto（crc32/fnv1a） | 非密码学安全，不进安全链；BLAKE2 新建于核心 lib/ |
| ext/codec（zstd/lz4/brotli） | zd 压缩继续用 codec |

## 6. 落地顺序与验收（对齐先小任务后回归的工作流）

| 步骤 | 内容 | 验收（每步自举零回归 + regress-s21 全绿） |
|---|---|---|
| S1 | 核心微内核化第一步：pipeline 5 槽 → 注册表执行骨架 + 内建引导集（默认管线注册项）；passmanager 接入 pipeline | tiec 自举 hash 不变；回归基线保持 |
| S2 | id+version：注册项 schema 表驱动 + 同 id 异 version 仲裁 | 注册冲突负例正确拦截 |
| S3 | tieir 消费入口：import tieir 包（消费方免前端） | 包 .tieir → 编译运行通过 |
| S4 | data→zd 发布转换（publish 压缩 + 指纹计算） | zd 包加载运行与 data 等价 |
| S5 | blake2 核心库（BLAKE2s-256/BLAKE2b-512，验证向量探针）→ 凭证+指纹审计链（指纹树→验签→fp 锚定 lock） | RFC 测试向量探针绿；篡改/冒名包负例全拦截 |
| S6 | CLI 子命令注册化 + 库树收敛（std/ext/rdu ↔ lib_v1 定位） | 全命令行按注册项分派 |

## 6.5 安全算法底座（并行于 S1–S6 的前置任务）

**目标**：先巩固安全底座——调研当前经典与新兴安全算法，分类纳入 std/ext/rdu 三库，
供插件审计链与平台应用使用。

**分类归属**（写入 tie-main 树，lib_v1 为 library-v1 不可变归档不作修改）：

| 类别 | 算法 | 归属 |
|---|---|---|
| 哈希/校验 | SHA-2 族、SHA-3（Keccak）、BLAKE2s/b、BLAKE3、XXH3、SipHash；MD5/SHA-1 仅兼容标注 | std |
| MAC | HMAC、Poly1305、Ascon-MAC（轻量） | std + rdu 复刻 |
| 对称加密 | AES（CBC/GCM/CTR/XTS）、ChaCha20、Ascon-128a/AEAD（NIST 轻量标准） | ext（AES）/std（ChaCha20）/rdu（Ascon） |
| KDF/口令 | HKDF、PBKDF2（std）；scrypt、Argon2id（内存硬，ext） | std/ext |
| 非对称 | Ed25519、X25519、ECDSA/P-256、RSA | ext |
| 后量子 | ML-KEM（FIPS 203）、ML-DSA（FIPS 204）、SLH-DSA（FIPS 205）；Falcon/HQC 待标准 | ext（评估后列） |
| TSHA 族 | 见 §6.6 | std（核心） |

**执行纪律**：实现委托子代理（每类一个，防上下文过长）；每步自举 + regress-s21 零回归；
BLAKE2 优先（S5 前置依赖）后按类推进。

## 6.6 TSHA（tie 自有哈希，tsha1 代）

**定位**：tie 平台自有通用安全哈希；ARX 轮函数（BLAKE 家族已验证构造，无查表、软件快、
状态小），与 BLAKE2 指纹底座同宗、实现可交叉验证。结构信任 BLAKE 族，自创仅限
参数/常量/轮数，不宣称新结构贡献；附带 security-notes 说明未经独立审计。

**家族（tsha1 代，三档 × 位长）**：

| 档位 | 名称 | 设计 |
|---|---|---|
| 快速 | `tsha1f-<n>` | ARX 轻量轮（BLAKE2s 同族 u32/u64 双线），速度优先；TSHA-512 用 G 函数 + ROTR{32,24,16,63}，轮 10（BLAKE2 为 7）；TSHA-256 轮 12（BLAKE2s 为 10） |
| 复杂 | `tsha1b-<n>` | 强化轮——更高轮数 + 混合置换（σ 置换/更多消息调度），抗现分析显著增强 |
| 加强 | `tsha1x-<n>` | **f 与 b 多次排列组合再计算**（对 f 与 b 的输出做多次排列组合混合再算），显著增加破解难度 |

**命名**：`tsha1<档>-<位长>`；位长对齐 256/512，后续代次递增（tsha1 → tsha2 → …）。

**IV/常量定制**：取标准种子 + PRNG 扩展固化（可复现、无主观 backdoor 选择）。

**验证**：已知答案向量（空串/abc/长消息/边界长度）逐变体生成；与 BLAKE2 交叉验证
G 函数正确性；同构性测试（同消息比对差异仅限参数层）。

## 7. 风险与未决

- **BLAKE2 纯 tie 实现性能**：编译器自举路径可能调用频繁；若慢，在 S5 前做基准与优化
  （对齐内存效率优先的用户偏好）
- **TOFU 的首次信任**：依赖用户核对 fp；文档需写明外带核对渠道（官网/README 发布 fp）
- **tieir 稳定格式版本**：S3 实现时冻结格式版本号，跨版本兼容策略按 tieir-format.md 推进
- **passmanager 与 pipeline 双轨消除**（S1）：审计 W1 警告要求二选一，S1 起以接入为主
- Ed25519 纯 tie 实现为独立大工程（S5 前置依赖），评估周期后决定自研或 extern 系统库