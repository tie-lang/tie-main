# td 语法与编译器 td→zd 设计文档

* 日期：2026-08-31

* 状态：待批准

* 仓库：`F:\Projects\tie-repo\tie-main`（编译器/语法层）

* 关联：dp 数据包体系（`jcc-core` specs `2026-08-31-dp-data-pack-design.md`）、zd v2（`2026-08-31-zd-v2-design.md`）、tink（`2026-08-31-tink-design.md`）

## 1. 背景与定位

dp 数据包的源数据文件（pack.data.tie / index.data.tie / 各分类数据）需要**可读、玩家可编辑**的格式。核心原则：

* **td 就是 tie 语言语法**——td 文件正文是 tie 表字面量，不引入 JSON 风独立语法（贯彻落实）；

* **解析做进编译器（tiec）**，不做进 std——td 语法由编译器背书；

* 产物统一为 zd（`.zd`）二进制，dp 包内全 zd。

## 2. td 语法（= tie 表字面量）

* 文件角色 `type tie<data>`；

* **正文 = tie 表字面量**：裸表 `[ ... ]`，或带可选表名（无 `var` 关键字，如 `pack = [ ... ]`）；**表名可有可无，缺失自动处理**；

* 支持：字符串（含中文 UTF-8）、整数、浮点、数组、键值表、嵌套表、`//` 注释；

* 示例：

```tie
// pack.data.tie —— type tie<data>
[
    "season": "S13",
    "season_id": "2026-08",
    "pack_id": "testsrc",
    "author": "tie-lang",
    "description": "示例数据包",
]
```

* tiec 语法层支持 data 文件的此形态（裸表/可选表名无 var），编译器自动识别处理。

## 3. 编译器接入（tiec）

* **语法/语义支持**：`type tie<data>` 文件顶层为 tie 表字面量（裸表/可选表名），编译器自动处理；

* **新子命令** **`--compress-data`**：

```
tiec --compress-data <in.data.tie> -o <out.zd>     # td → zd 扁平数据
```

* 编译器内部 data 文件（如 config.data.tie）统一走同一解析流程。

## 4. td→zd 扁平编码（DFS 平铺 + 平行表）

tie 运行时无法构造嵌套表 → 表字面量树按 **DFS 序平铺**为元素序列，用平行表描述：

| 列                                    | 说明                          |
| ------------------------------------ | --------------------------- |
| kind                                 | 0=表/数组，1=字符串，2=整数，3=浮点      |
| key                                  | 键名（无键空串）                    |
| value\_i64 / value\_f64 / value\_str | 标量值（按 kind 取对应列）            |
| child\_count                         | 表/数组的子元素数（消费者按此推进 DFS 遍历子树） |

* 编码为 zd record（字段号固定，只追加）；`tiec --compress-data` 输出即此 zd；

* **zd record 字段号（固定，只追加；已实现）**：

  | 字段号 | 内容                       | wire type | tag |
  | --- | ------------------------ | --------- | --- |
  | 1   | kind（zd i64 数组）          | 2         | 10  |
  | 2   | key（zd string 数组）        | 2         | 18  |
  | 3   | value\_i64（zd i64 数组）    | 2         | 26  |
  | 4   | value\_f64（zd f64 数组）    | 2         | 34  |
  | 5   | value\_str（zd string 数组） | 2         | 42  |
  | 6   | child\_count（zd i64 数组）  | 2         | 50  |

  文件 = zd v2 头（10 字节：`TIEDBZD` + `"02"` + flags 0）+ 依次 6 个字段（每字段 = varint tag + varint 载荷长度 + 载荷 zd 数组）。bool 归整数列（true=1/false=0）。

* 消费者（jcc-pack）按 kind/key/child\_count 遍历读取字段，无需自带 td 解析器。

## 5. 消费方

* **jcc-pack**（dp 制作器）读 `tiec --compress-data` 产出的 zd 产物，提取元信息/索引/记录 → 组装 dp 容器 → 压缩 `.jcc`；不再自带 td 解析器；

* **编排方式**：初始为脚本调 tiec；后续经 **tink**（管道编排器）调用，不再依赖 PowerShell 脚本（见 tink 设计）；

* config.data.tie 等编译器内 data 文件解析统一。

## 6. 错误处理

* td 解析失败（语法错/类型不匹配/清单与文件不一致）→ `--compress-data` 报错并退出非 0（不产 zd）；

* 读取端 zd 解析失败 → 沿用 zd 契约（版本哨兵/空表），不 panic。

## 7. 测试策略（probe）

| 探针       | 覆盖点                                              |
| -------- | ------------------------------------------------ |
| td→zd 往返 | 表字面量 → zd → 还原逐字段比对，含中文/嵌套/空表                    |
| 非法输入     | 语法错误 → 退出非 0                                     |
| 可选表名     | 裸表与 `name = [...]` 均解析一致                         |
| 消费者集成    | jcc-pack 读 --compress-data 产物组装 dp（端到端，随 dp 里程碑） |

## 8. 里程碑与小任务序列（一次一个小任务）

| 内容                                                          | 产物            |
| ----------------------------------------------------------- | ------------- |
| ✅ tiec 语法层支持 data 文件裸表/可选表名（无 var）+ 校验探针                    | tiec 识别 td 形态 |
| ✅ tiec `--compress-data` 子命令：表字面量 → DFS 平铺 → zd record + 探针 | td→zd 绿       |
| config.data.tie 等内部 data 文件统一走 --compress-data 解析 + 回归      | 内部统一          |
| jcc-pack 读 zd 产物替换自带解析器（随 dp 里程碑）                           | dp 集成绿        |

## 9. 非目标（YAGNI，本阶段不做）

* 不做 std 库解析器（解析归属编译器）；

* 不做 td 序列化（td→zd 单向，序列化方向由 zd→文本另议）；

* 不扩展 td 语法到代码（只数据文件）。

