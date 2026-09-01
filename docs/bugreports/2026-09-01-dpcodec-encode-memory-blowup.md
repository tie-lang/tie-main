# 缺陷报告：跨模块 struct 扩展后，encode 型大函数运行时内存无界增长

> 报告日期：2026-09-01
> 组件：tiec 编译后端（LLVM 生成路径）
> 归属仓库：tie-main（本仓库）
> 复现仓库：tie-jcc-core（闭源，可提供最小化用例）
> 严重度：高（大数据量下 4 秒内内存冲到 3–26 GB，进程不可用）

## 一、现象

`tie<logic>` 程序 `jcc-pack` 在构建 S19 数据包时（65 棋子 / 35 羁绊 / 157 装备，棋子记录含数百字符中文技能文本，整体输入约 150 KB）：

- 内存曲线呈「平台期 → 无界递增」：前 ~2.5 s 线性增长到 ~237 MB（正常，校验和阶段）；随后每 0.5 s 再 +2 GB，实测峰值 26 GB 后进程被强制终止。
- 同一可执行文件构建小数据集（testsrc，若干 KB）0.4 s 完成、内存正常。
- 1 条棋子数据的变体构建 1.7 s 完成、内存正常 → 与数据规模正相关。

`byte_write` 阶段标记（在关键函数前后落盘哨兵文件）精确定位：

```
S1..S7 ✓  →  S7-S8 ✗  卡在 dpcodec.encode_pack(filled)
```

zstd 压缩尚未执行（`.jcc` 压缩在 S9）。排除压缩环节。

## 二、最小触发条件（已精确到语义形态）

**触发形态**：**跨模块 struct（在 `model.tie` 定义、被 `dpcodec.tie`/`main.tie` 跨文件访问）增加字段**，且该 struct 的记录在**大循环里被高频构造 + 表 push + 逐字段赋值**。

证据链（全部实测，同机同数据，仅改一处）：
1. `ChampRec` 4 字段（`id/cost/cn/traits`）→ encode_pack 正常（62 s 完成 S17 全量，历史基线）。
2. `ChampRec` 扩到 7 字段（新增 `skill_name/skill_desc/stats`，其中含数百字符中文字符串）→ encode_pack 内爆内存。
3. 扩字段**但完全不接线**（新增字段读取代码注释掉，struct 声明留着）→ 同样爆。
4. 扩字段 + 注释掉**新增字段的编译产物**（struct 完全回退 4 字段）→ 恢复正常。
5. 仅新增**一个**字段（`skill_name`，短字符串）→ 同样爆。
6. 通过「新增独立 struct `SkillRec` + 独立段编码（平行表），`ChampRec` 保持 4 字段」重构 → 仍然爆（同模块新增编译单元即触发）。
7. 把 encode_pack 本体恢复为「8 段原样」+ 技能段用独立外部函数 `pack_skills` 追加（不触碰 encode_pack 源码）→ 仍然爆。

**结论**：缺陷不是运行时逻辑问题，而是**编译器对「某模块内存在结构化数据 + 多表 push 交错」代码形态的机器码生成不稳定**——即使相关路径在运行时不被执行，仅「同模块增加了这类编译单元」就足以让 `encode_pack`（及调用方）的生成代码产生无界堆分配。

## 三、实验矩阵（维护者可复现）

| # | 改动 | build 结果 | 内存/耗时 |
|---|------|-----------|----------|
| 基线 | `ChampRec` 4 字段（commit `e1ff921` 前逻辑） | 正常 | ~62 s / 数百 MB |
| A | `ChampRec` 7 字段 + 读取接线（commit `2d831a1`） | 卡死 | 3.9 s / 3.4 GB+ 被护栏终止 |
| B | 仅声明 7 字段、读取注释 | 卡死 | 4.1 s / 峰值增长 |
| C | 位置构造器替代逐字段赋值 | 卡死 | 4.1 s / 3.7 GB |
| D | 拆成单类小函数（build_champs/traits/items 分拆） | 卡死 | 4 s / 2.4 GB |
| E | 独立 `SkillRec` 旁路 + 平行表段 10 | 卡死 | 4.1 s / 3.2 GB |
| F | encode_pack 原样 8 段 + 外部 `pack_skills` 追加段 10 | 卡死 | 3.9 s / 3.4 GB |
| G | testsrc 小数据（任何形态） | 正常 | 0.4 s / 数十 MB |
| H | 1 条棋子变体（index 只列 1 条目） | 正常 | 1.7 s / 低内存 |

同机环境：Windows 11，tiec 自举版，`TIE_INTERP_LIB=tie_interp.lib`，`TIE_TRM_LITE_LIB=trm_lite.a`，LLVM 目标 `x86_64-pc-windows-msvc`。

## 四、内存增长特征（利于后端定位）

对运行中进程每 0.5 s 采样 WorkingSet（MB）：

```
27, 49, 70, 99, 237, 1351, 3032, 5515, 7752, 10003, 12287, 14220, ...
```

两个关键特征：
1. **先平台期（校验和/读取阶段稳定）→ 进入 encode_pack 后斜率骤变**：+2 GB / 0.5 s。
2. 斜率恒定（线性、不停顿）→ 符合「每次迭代产生新分配且从不释放」的行为（例如：alloca 逃逸为堆分配但 GC 未登记 / 大表重复拷贝的中间版本被留存 / 别名分析失误导致写放大）。

> 注：该特征与项目内已有记录一致——tiec 后端在「循环内地址逃逸 alloca 逐次迭代累积」与「读跨模块全局访问器 + 交错多表 push/树遍历损坏值」两类已知缺陷（此前在 std/exmath、tiedb 中触发，规避手段为拆小函数）。本次在更大用户数据量下成为硬性阻塞。

## 五、建议排查方向

1. **逃逸分析 / 栈提升（SROA）**：`build_*_seg` 循环体中对 `ChampRec`/`table` 的访问是否被错误提升为重复栈/堆申请（每次迭代独立逃逸）。
2. **GC / 内存登记**：表 `table_push` 扩容路径在「大 struct 表」组合下是否漏登记新分配（泄漏式增长）。
3. **struct 布局/跨模块常量**：跨模块 struct 字段偏移计算在多字段情形下是否被后端以错误 stride 遍历（写偏移灾难）。
4. **寄存器分配 / 别名**：函数本地大对象 + 长循环的 RPO 或别名结果在新增编译单元后漂移。
5. 建议生成该函数的 LLVM IR / 汇编做前后对比（4 字段正常 vs 7 字段爆炸），或直接提供指定函数的 `-print-after-all`。

## 六、最小复现用例（roadmap）

已具备最小化差异：
- 正常：`ChampRec` 4 字段（`tie-jcc-core` commit `e1ff921`）。
- 触发：`ChampRec` 7 字段（commit `2d831a1`）。
- 精简复现（不依赖 jcc 私有数据）可提供：一个仅定义 `struct X { a,b,c,d,e,f,g }` + 循环 `100k` 次构造/push 的 `tie<logic>` 程序，与 4 字段对比内存曲线。

需要提供最小复现 tie 源、IR 对比或更多定位信息，请直接回复本仓库文档路径即可。

---

## 七、补充实验（2026-09-01，修复提交 `2652451` 验证）

维护者的 `2652451 feat(irgen): auto StringBuilder hoist for in-loop string self-append` 已自举验证（tiec2==tiec3 不动点），**但未解决本场景**。追加决定性证据：

**逐段定位（encode_pack 内 per-段 byte_write 哨兵）**：卡在 **`build_champ_seg(p)`**（`_e2` 存在、`_e3` 缺）——即「65 条 record 的连续表 push 循环」，与字符串自拼接无关。

**交叉矩阵（同一数据源 official-s19，仅列局部结论）**：

| 编译器 | champ_to_rec 字段 | 结果 |
|--------|------------------|------|
| tiec (09:12，修复前) | 7 字段 | 卡死 3.7GB / 4s |
| tiec2（含 2652451） | 7 字段 | 卡死 3.7GB / 4s |
| tiec2（含 2652451） | 4 字段（技能字段不编码） | 卡死 2.7GB / 4.4s |
| tiec (09:12) | 4 字段 | 卡死 3.3GB / 3.6s |
| tiec (09:12) | 4 字段 + 数据源 official-s17-seed | 卡死 2.8GB / 14s |

- `zd.concat` → 自行实现的逐字节 `table_push` 拼接（`capp`，57 处全替换）**无效**。
- testsrc（1 条）任意组合 0.4s 正常；1 条变体 1.7s 正常。
- 历史「62 s 构建 S17」在当前构建链路上**不可复现**。

**最新追加（10:50）——推翻「record 数组形态」假设**：`build_champ_seg` 改为 **tpl 同款纯平行表**（9 列 ids/costs/cns/traits_len/traits_flat/skill_names/skill_descs/stats_len/stats_flat，全部小元素 push，无任何 record 字节拼接），**仍卡死在 build_champ_seg**（每 0.5s +2GB）。tpl 段（同形态）65 条 10KB+ 灰度一直接正常 → **触发与段内容无关，与「函数读取跨模块表字段（p.champions[i]）+ 循环内多表 push」的代码生成有关**。

**最小触发形态（最终修订）**：函数体 = `while i < len(p.any_table_of_struct) { read p.table[i].field; push into ≥2 local tables }`，当循环 ≥ ~50 次时内存无界增长。建议维护者用他本地机器直接编译本仓库 `pack/dpcodec.tie` + 构造 65 条数据的最小 tie 程序，并对该函数出 LLVM IR/汇编对比 N=1 与 N=65 的分配模式。

**最新追加（11:00，最窄触发面）**：
- 全段「单层循环 + `&& i < 8` 截断」→ **build 完整通过**（8.2s / 峰值 842MB）；`cap=12`（champ 段，trait/item 未截）→ 爆。
- 改为「分块双层循环」（外层 `while start<total` 纯表 concat，内层 8 次 struct 访问）→ **也爆**（3.3GB）。
- 即：**安全上界 ≤8 次/单函数；任何「两层及以上」的循环展开都会触发**，与是否访问 struct、是否 concat 无关——疑似（L）oop 派生的地址逃逸/SROA 对「多循环体函数」的误判，建议直接对比 `cap=8 单循环`与`分块双层`两版函数的 IR。

**修订后的最小触发形态**：`<table<i64>>` 累积式 push 循环（每条含跨模块 struct 访问 + `zd.encode_*` 输出 push），当总量约 5–6 万个元素时内存无界增长（每 0.5s +2 GB，斜率恒定 → 每次迭代的新分配未回收）。修复建议聚焦**表 push/扩容路径的调用约定或生命周期标注**，而非字符串拼接；可提供 65 条×~1KB record 的独立最小 tie 程序协助定位。

---

## 八、维护者实机验证（2026-09-01，局部结论——根因确认并根治）

主仓库实机验证（同一 jcc-pack 源码 `dpcodec.tie`/`main.tie`，同一数据源 `official-s19`）确认根因是**编译产物层字节表累积拼接的 O(n²) 无名分配**，而非表 push/扩容路径缺陷，修复为编译器自动提升：

**对照实验（同机同源同数据，仅编译器不同）**

| 编译器 | build 结果 | 峰值内存 |
|--------|-----------|---------|
| tiec（修复前，09:12 产物） | 3.7s 内 4.5GB+ 被护栏终止，无输出 | 4579 MB ✗ |
| tiec2（含字节表自加提升，cbs） | build 完整通过（65 棋子/35 羁绊/157 装备） | **232 MB ✓** |

**根因**：`build_champ_seg`/`champ_to_rec` 内 `body = byte_concat(body, seg)` 逐迭代新建 |body| 级整表、旧表永不释放（tie 无 GC）→ O(n²) 无名分配；jcc-pack 数据规模（65 条×~1KB record + 数百字符中文文本）放大量变后 4s 内冲 3–26 GB。`zd.concat` 是 `byte_concat` 的薄包装（同族），报告 §七 中「capp 逐字节 push 替换无效」的观测与根因定位不完全一致——经逐段哨兵复核，卡点仍停留在字节表累积拼接段内。

**修复**：p.6.1.4 延伸——irgen 循环入口预扫 AST（`cbs_scan`），对满足安全形态的 `t = byte_concat(t, seg)` 自动提升：循环前拷贝到私有累积表 acc（唯一引用），循环内 `tbl_ensure+memcpy+set_len` 就地追加（摊销 O(1)），循环出口写回 t 槽。与原语义逐字节等价；旧 t 表只读不写，无别名污染。既有字符串自加 StringBuilder 提升（2652451）同族覆盖 string 路径。

**探针**（`tests/hoist_probe/cbs_encode_repro.tie`，不依赖 jcc 私有数据）：复用 `model.tie` 跨模块 7 字段 struct，合成 4000 条含数百字符中文文本的记录，按 `encode_pack` 同形态循环累积（blob 长度前缀 + rec 字节 concat）。双编译器对比：修复前 2.5GB+ 被护栏终止；修复后 PASS（长度 + 尾部计数自检）。`tests/hoist_probe/cbs_edge.tie` 边界探针（单循环/多循环链/break/非纯净引用/空表入口）全绿。自举不动点 tiec2==tiec3 通过；tiec_fix 与 tiec2_self 编译探针产物 SHA256 逐字节一致。