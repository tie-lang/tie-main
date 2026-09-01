# 缺陷报告：含 hex 段（段9）容器的 extract 路径确定性 AV（0xC0000005），堆损坏与代码形态相关

> 报告日期：2026-09-01
> 组件：tiec 编译后端（LLVM 生成路径）
> 归属仓库：tie-main（本仓库）
> 复现仓库：tie-jcc-core（闭源，可提供最小化用例与独立探针）
> 严重度：高（jcc-pack extract 对含强化符文数据包必现崩溃，进程退出 0xC0000005）
> 关联：同族缺陷（编程时后端代码生成不稳定）——`2026-09-01-dpcodec-encode-memory-blowup.md` 已由 `2652451/476ac1b` 修复 encode 侧；本次为 decode/写盘侧同类表现（AV 而非内存无界增长）。

## 一、现象

`jcc-pack extract official-s19.jcc out_dir`（容器 = 65 棋子 / 35 羁绊 / 157 装备 / 258 强化符文 / index 含 258 条 hex_ids 清单，压缩 387 KB）：

- 进程无任何输出直接 AV（exit 0xC0000005）。
- 文件级哨兵定位：崩溃点发生在 `extract_champs` 循环第 7 次 `champ_txt` 调用期间（前 6 个棋子文件已正常落盘）。**相同数据的解码结果完全正确**（`info` 子命令逐字段打印 65 棋子 + 258 符文 id/cn/desc_len/level 全部正确）。
- 同一可执行文件 extract **不含 hex 的容器**（`_s19nohex.jcc`，185 KB，无段 9 / 无 index hex_ids 字段）→ 完整通过（65 棋子 + 35 羁绊 + 157 装备全部落盘）。
- 差异仅在于：容器内含段 9（258 条 hex 记录，含数百字符中文描述）与 index 字段 11（258 条 hex_ids）。

## 二、证据链（全部实测，同机同数据）

逐项对照实验（jcc-pack.exe，编译器 tiec 09:12 自举产物，含 2652451/476ac1b hoist 修复）：

| # | 改动 | 结果 |
|---|------|------|
| 基线 | extract 无hex包（`_s19nohex.jcc`） | 全过 |
| A | extract hex包，标准顺序（decode 完整 → pack.data.tie → index.data.tie → champs...） | 崩于 champs 第 7 个 |
| B | A 基础上 extract_hexes 提前到最前 | 258 hexes 全部写出成功，崩于 champs 第 13 个 |
| C | 双通道：decode_pack 跳过段9解析 + 跳过 index 字段11（首遍），第二遍完整解码 | 崩于 champs 第 13 个（首遍） |
| D | cap=8 单层循环 + 顶层顺序批次调用（无任何嵌套循环，encode 侧验证过的安全形态） | 崩于 champs 第 7 个 |
| E | 独立最小二进制 `jcc-unpack`（仅 dpcodec/zstd/zd + 写盘函数，无 build/compress 代码） | 立即崩（0 文件落盘） |

独立探针（`probe_hexext.tie`，仅 import dpcodec/zstd/zd + 自写 qs_clean/champ_txt/write_td，与 main 相同的解码+写盘步骤）：
- 解码完整 → 直接循环写 65 个棋子文本 → **全部完成**（头几次）
- 同一探针 + 在写棋子前先 write_td 一份 `index.txt`（index_txt 展开 258 hex_ids + 校验和）→ 崩于第 13 个棋子
- 同一探针禁掉 index.txt 写盘（仅保留 pack.txt 与 4 个空标记写）→ 崩于**第 4 个**棋子（更早！）

**结论性特征**：同一份解码数据 + 完全相同的 champ_txt/write_td 调用，仅改变无关邻接代码（增删一次 index 文本写盘、改变函数集合），崩溃位置在「第 4 / 第 7 / 第 13 个」之间乱移；任何形态下都无法完整跑完。这不是数据内容问题（解码值全对，且小数据量 testsrc 任意形态 0.4 s 正常），而是**编译产物级的不稳定——hex 批量字符串解码（258 条 + index 258 条）后的堆状态，使长循环「struct 字段读 + utf8 批量编码 + byte_write」的生成代码在固定分配次数后越界**。

## 三、疑似方向（供后端定位）

1. **堆损坏而非逻辑错误**：探针可复现且崩溃位置对无关代码形状敏感 → 疑似 hex 批量解码（258 条 record → 中文字符串表 + struct 表 push，扩容量级 256→512 等）在某种编译布局下写越界；随后的 `utf8_encode`/`table_push` 大分配触发。建议对比「解码 258 条」与「解码 ≥300 条」的表扩容路径生成代码。
2. **长循环 + string_builder + str_char 组合**的寄存器分配/别名漂移：与 encode 缺陷（§七「cap>8 单循环或任何两层循环」）同族但表现相反。
3. **write_td 的 `while i < len(body) { table_push(all, body[i]) }`**：逐字节累积 push 是 encode 侧 cbs hoist 提升的同类形态（但此处 `all` 不在循环外被 concat，是纯 push），也可能是该提升未覆盖的残留。

## 四、最小复现

独立探针 `tools/jcc-pack/probe_hexext.tie`（tie-jcc-core，闭源）约 130 行：import dpcodec + zstd.decompress_bytes + write_td 循环。可在提供最小化用例后直接编译复现；如需脱离 jcc 私有数据，可按 encode 报告 §六 方式合成 258 条含中文长文本的 hex 记录 + 65 条棋子记录构造容器。

维护者在实机验证后可直接回复本文档路径。修复确认后，jcc-pack extract 恢复单遍完整解码即可（当前代码已预留）。