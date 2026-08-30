type tie<data>
// ============================================================
// 设计：表复合元素 + 运行时整体迁入 trm-lite（P2a）
// 状态：**已实现**（2026-08-30，提交 31a05c6/26e4322/0979213/9c9878f）
// 决策：
//   - 表运行时字节层整体迁入 trm-lite（trm_lite.a），tiec 发 extern 调用
//   - 只用 trm-lite 即可承载 table 全部功能（不依赖 trm）
//   - 一步到位（不渐进）：标量 + 复合元素统一走 tl_tbl 容器
//   - 类型化 store/load 留编译器（类型是编译期概念）
//   - 自举闭环已验证：新 tiec 编译自身（tiec2，链 trm_lite.a）正常工作
// 验收：tests/language/table_{struct,fn,enum}_elem.tie + trm-lite tl_tbl 单测全过
// ============================================================

# 1. 背景与目标

tie 的表 `table<T>` 目前运行时（`s21_table_new/push/at/set/grow`）是编译器
**内联生成的 tie-IR**（compiler/backend/irgen_str.tie）。其字节层容器逻辑
（`{cap,len,data,esz}` 句柄、扩容、字节拷贝）属于运行时功能，应归入
trm-lite（轻量运行时，静态链接 trm_lite.a），与既有 spawn/yield/collect
模式一致。

同时 P2a 需要支持**复合元素表**（struct/enum/fn 元素），实测现状：

| 项目 | 现状 |
|------|------|
| 二维/三维嵌套表 | 已可用 |
| `table<i64/f64/string/bool>` | 已可用（单 64 位槽） |
| `table<Point>`（struct） | 声明✓，IRGEN 崩（槽按 i64 大小，struct 多字） |
| `table<Shape>`（enum） | IRGEN 崩（tag+payload 多字） |
| `table<fn(i64) -> i64>` | 类型实参解析失败 |
| `t[i].field` 读写 | 读报"需要可寻址"，写报"赋值目标必须是变量或对象字段" |
| 异构 `[1,"a",true]` | 语义层拒绝（P2b 范围） |

根因：编译器 `elem_size()` 只返回 1(bool)/8(其余)，槽类型选择只认
i64/string/f64/bool，多字元素（struct/enum/fn）没有正确尺寸与槽类型。

# 2. 总体架构（三层）

```
┌─ tiec 编译器（类型层，留编译器）────────────────────┐
│  elem_size(t) 复合类型真实尺寸（编译期静态已知）       │
│  类型化 GEP/store/load（struct/enum/fn 类型 id）      │
│  可寻址字段访问 t[i].field 读写                      │
│  table<fn(...)->...> 类型实参解析修复                 │
│  extern 调用生成（tig_trmlite_call → tl_tbl$...）     │
└──────────────────────────────────────────────────┘
         ↓ extern 调用（符号 tl_tbl$...）
┌─ trm-lite（轻量运行时，trm_lite.a，唯一运行时依赖）───┐
│  tl_tbl：字节层表容器（纯 unsafe/ptr，零表依赖）        │
│  tbl_new / tbl_len / tbl_ensure / tbl_set_len /        │
│  tbl_at / tbl_set                                      │
└──────────────────────────────────────────────────┘
         ↑ 可选封装（不参与 table 功能路径）
┌─ trm（完整运行时套件，lib/tbl.tie，可选）───────────┐
│  trm_tbl：包装 tl_tbl（后续可选，非依赖）             │
└──────────────────────────────────────────────────┘
```

- **trm 不是依赖**：table 功能只需 trm-lite（trm_lite.a）静态链接。
- **tiec 自动链接**：检测到表容器 extern 调用时置 g_used_trmlite 标记，
  toolchain 链 trm_lite.a（同 spawn/yield/collect 机制）。

# 3. 字节层接口（trm-lite：tl_tbl）

命名空间 `tl_tbl`，编译进 trm_lite.a，符号 `tl_tbl$<fn>`。全部以
**i64 承载指针**（ptrtoint/inttoptr，对齐 trm-lite spawn 模式）。
**内部零 table<T> 依赖**（纯 unsafe/ptr + 裸分配，保证自举无环）。

```tie
// 句柄：32 字节 {cap@0, len@8, data@16, esz@24}
tbl_new(esz: i64) -> i64          // 建空表：cap=0/len=0/data=null/esz
tbl_len(h: i64) -> i64            // 读 [h+8]
tbl_ensure(h: i64, need: i64) -> i64  // 若 need>cap 扩容（1.5x，cap=0→8）；
                                     //   返回 data ptr（i64），扩容后可能换址
tbl_set_len(h: i64, n: i64)       // 写 [h+8]
tbl_at(h: i64, i: i64, out: i64) -> i64  // 越界→写零 out；否则拷贝 esz 字节
                                         //   到 out；返回 ok(0/1)
tbl_set(h: i64, i: i64, src: i64) -> i64 // 越界静默；否则拷贝 esz 字节；返回 ok
```

扩容语义对齐现有 s21_table_grow：`newcap = cap==0 ? max(8,need) : max(cap+cap/2, need)`；
新缓冲 = alloc(newcap*esz)；memcpy 旧 len*esz 字节；free 旧 data。

# 4. tiec 类型层改动（compiler/）

## 4.1 elem_size：复合类型真实尺寸

`elem_size(t)` 扩展为按类型计算字节大小：
- bool=1，其余标量=8（现状）
- struct：字段尺寸和（对齐 C 布局，i64→8 已由 datalayout 保证）
- enum：tag(i64) + payload 槽尺寸和
- fn：16（`{ptr,ptr}` 闭包）
- 嵌套 table/map/string/port：8（句柄/指针）

## 4.2 槽类型选择：复合类型 id 直传

`tig_table_lit` / `tig_variadic_table` / 表下标读写的 `pty`/`ret_ty` 选择，
从"只认 i64/string/f64/bool"扩展为"任意类型 id 直传"（struct/enum/fn
类型 id 交给 llvmgen，其 alloca/store/load 映射已存在）。

## 4.3 表运行时调用：内联 IR → tl_tbl extern

新增 `tig_tbl_*` 包装生成 extern 调用（对齐 `tig_trmlite_call`）：

```text
建表： h   = tl_tbl$tbl_new(esz)
len：  l   = tl_tbl$tbl_len(h)
push： len = tbl_len(h); need = len+1;
       data = tbl_ensure(h, need)        // i64 → inttoptr
       addr = data + len*esz（字节 GEP）   // esz 编译期已知
       类型化 store 值 @ addr
       tbl_set_len(h, need)
读 t[i]： out = alloca elem_ty → ptrtoint
       tbl_at(h, i, out_ptr)
       类型化 load out
写 t[i]： src = alloca elem_ty; store 值 → ptrtoint
       tbl_set(h, i, src_ptr)
```

标量 + 复合统一走此路径（一步到位），删除编译器内联的
s21_table_new/push/at/set/grow。map 路径：句柄创建（s21_map_new 内部原调
s21_table_new(16)）改走 `tl_tbl$tbl_new(16)`；map 其余逻辑（二分/哈希、
memmove 插入、打印）保持内联，非本次范围。

## 4.4 可寻址字段访问（t[i].field 读写）

- `putil.is_addressable_base` / `sstate.is_addressable`：扩展识别
  Index→FieldAccess 链（`t[i].x`）。
- 写：pstmt 赋值目标识别 `t[i].field`；后端生成 GEP(data + i*esz) 直入槽
  + 字段偏移 store。
- 读：sinfer 字段访问 base 可寻址判定放开下标链；后端 load 槽后按字段
  偏移提取。

## 4.5 table<fn(...)->...> 类型实参解析修复

`pexpr_type.parse_type` 的 fn 特判在 `<...>` 实参上下文失效（报
"期望 ')'，实际是 LParen"）。修复 parse_type_args → parse_type 的 fn 分支
（含 `->` 返回箭头 + `>` 闭合），实现时定位根因。

# 5. 自举与构建顺序

tl_tbl **内部零 table<T>**（纯 unsafe/ptr 裸内存），故：

```
旧 tiec.exe → 编译 trm-lite/tl_tbl.tie → trm_lite.a（含 tl_tbl$* 符号）
旧 tiec.exe → 编译 tie-main 新源码（表代码gen改为 tl_tbl extern 调用）
             → 新 tiec.exe（内部表仍为旧内联 IR，正常运行）
新 tiec.exe → 编译用户程序（表 → tl_tbl extern）→ 自动链 trm_lite.a
```

无环。彻底自举（tiec 自身表也走 tl_tbl）作为后续自举重建步骤，非本阶段必须。

**自举约束（实测）**：trm_lite.a **必须用「表内联 codegen」的 tiec 构建**——
新 tiec（表→tl_tbl extern）编译 tl_runtime 时，sched/gc 的表用法生成
`tl_tbl$tbl_*` extern **声明**，与 tl_tbl 的**定义**同模块冲突（opt 报
invalid redefinition）。构建顺序：旧 tiec（含 memcpy 修复、表内联）→
trm_lite.a → 新 tiec。tl_tbl 自身零 table 依赖（纯 unsafe/ptr），故其
逻辑不受此约束。

# 6. 测试方案

1. **trm-lite 单测**：tl_tbl 容器（new/len/ensure/at/set、扩容边界、
   越界零值/静默）。
2. **tie-main 探针**（tests/language/ 正例，tests/_p2_probe/ 现有探针迁移）：
   - struct 元素表：声明/字面量/push/for/`t[i].x` 读写/`t[i].x = v`
   - enum 元素表：构造/下标/遍历
   - fn 元素表：`table<fn(i64) -> i64>` 声明/调用 `t[0](5)`
   - 二维 struct 表：`[Point(1,2); Point(3,4)]`
   - 既有标量/嵌套表回归（全量 tests 回归跑通）
3. **自举回归**：脚本 regress-driver-lite.ps1 等既有回归通道全绿。

# 8. P2b 异构元素表（2026-08-30，提交 6372e25/6b76954/353e5a2）——已实现

在 P2a 复合元素表基础上新增 `any` 动态类型，支持异构表 `[1, "a", true, 2.5]`：

| 能力 | 实现 |
|------|------|
| `any` 类型 | `TK_ANY=23`，LLVM 表示 `{i64, i64}`（tag + payload 16 字节值类型） |
| 装箱 | `tig_box_any`：tag 约定 0=i64/整数 1=f64 2=bool 3=string 4=char；bool/char/窄整数 zext 进 i64 槽，string 存 ptr，f64 存 double |
| 异构推断 | sinfer 元素类型不一致 → `table<any>`；表字面量元素类型优先取语义类型 |
| 拆箱 | `as_i64/as_f64/as_bool/as_string/as_char`：运行时 tag 检查，不匹配 → 运行时错误退出；`as_i64/as_f64` 与既有 S1.3 数值转换族重载（数字转换 / any 拆箱） |
| switch 类型匹配 | `switch (any) { case i64:/string:/bool:/f64:/char: ... }`：case 类型 → 装箱 tag 常量 icmp；body 内 `as_<T>(x)` 取用 |
| 存取 | `table<any>` 字面量 / 下标读写 / `table_push` 均自动装箱 |

**验收**：tests/language/table_any_elem.tie（7 项 PASS）+ tests/_p2b_probe/*.tie 探针；
tests/language 全量正例编译+运行无回归（extern_decl FFI 基线跳过、shift_neg_free 名为 _neg 实为正例除外）。

# 9. P2c 异构元素表深化（2026-08-30，提交 2dac1c9/1e447d2/d11cfa5）——已实现

在 P2b 基础上深化 `any` 一等值类型 + 复合装箱 + 运行时辅助：

| 能力 | 实现 |
|------|------|
| 复合装箱 | struct/enum/fn → any：tag = 类型 id（复合 id 远大于标量 0-4），堆分配 type_byte_size 字节按值拷贝聚合，payload = 堆指针 |
| 复合解构 | `switch (any) { case Point(p): }` 绑定提取（镜像枚举 `case Ok(v):`）；`case Point:` 裸类型匹配；scheck 校验 + irgen 提取 |
| any 一等值 | 函数参数/返回值自动装箱（return/实参/var 槽）；struct 字段（构造/赋值/嵌入式 table<any>）自动装箱 |
| map<any> | 异构值推断 map<any>；值槽存堆 any 盒指针（容器 16 字节条目布局不变）；读写自动装箱/还原 |
| 运行时辅助 | `any_tag(x)` 取 tag；`println(any)` 按 tag 运行时分派打印（标量值 / <struct>/<enum>/<fn>） |
| any 零值 | 全零聚合 {tag:0, payload:0}（t21_zero/tig_default_val；直接 `tig_int_lit_ty(0,any)` 生成非法 `add {i64,i64}`） |

**验收**：tests/language/table_any_deep.tie（8 项 PASS）+ tests/_p2b_probe/p2c_*.tie 探针；
tests/language 全量正例编译+运行 69/69 无回归；P2a/P2b 验收（struct/fn/enum/any 元素表）全过。

# 10. P2d 表/集合标准库（2026-08-30，提交 8f32a05/18cea7d/20e0235）——已实现

在 P1 数据流箭头 + P2b/P2c any 异构表基础上，为表补充集合标准库与嵌套能力：

| 能力 | 实现 |
|------|------|
| coll 高阶函数 | std/collection.tie 新增 map_i64/map_string、filter_i64/filter_string、reduce_i64/reduce_string、foreach_i64；**表作末参**（`t -> coll.map(f)` = `coll.map(f, t)` 配合 P1 管道）；fn 值参数走 S2.2 命名函数/闭包 |
| coll 表操作 | reverse_i64/reverse_string、to_string_i64/to_string_string（`[1, 2, 3]`，空表 `[]`）、join（分隔符连接，空表空串）、sum_i64（空 0）、product_i64（空 1）、max_i64/min_i64（空哨兵 0） |
| 嵌套 table\<any\> 装箱 | tig_box_any 表/映射分支：tag=精确表/映射类型 id，payload=ptrtoint(表 ptr)——表是引用类型（句柄在指针后），8 字节 payload 直接容纳，**无堆拷贝** |
| 嵌套 table\<any\> 拆箱 | tig_unbox_any inttoptr 还原表值；运行时 tag 检查（期望=请求表类型 id），不匹配 → 运行时错误退出 |
| as_table_\* 内置 | as_table_i64/string/bool/f64/char/any 六个（sbuiltin 返回类型 + sinfer_ret 实参必须 any + irgen 拆箱三处登记）；返回 table_of(元素)，精确匹配装箱 tag |

**验收**：tests/language/table_coll_p2d.tie（7 项 PASS：hof/hof_str/pipe/ops/join/nested/nested_deep）
+ 探针 p2d_hof/p2d_ops/p2d_nested/p2d_nested_mismatch（tag 错 → 运行时错误）；
tests/language 全量正例编译+运行 52/52 无回归；自举（tiec 编译自身 driver.tie）零错误。

# 11. P2d 深化：集合库（2026-08-31，提交 de2364d/ f5bc0bf/5740a53）——已实现

在 P2d 基础集合库之上深化统计、谓词查找与 map 高阶：

| 能力 | 实现 |
|------|------|
| sort_f64 | std/sort.tie 新增 f64 冒泡（与 sort_i64/sort_string 对称，ref 回写） |
| coll 统计 | mean/median/variance/stddev（i64 与 f64 变体）；中位数复用 sort 冒泡（局部副本）；总体方差 1/n；空表 → 0.0 |
| coll 谓词 | count_if/any/all（fn 谓词 HOF，表作末参配合 P1 管道；any 短路、all 空表 true）；find_index/contains（线性，无序可用；未找到 -1） |
| map_keys | 编译器内置：遍历 map 双模式（数组有序 data / 哈希槽跳过空槽）提取键 → table<string>；数组模式键升序 |
| map_values | 编译器内置：值类型 V 从实参 map\<string,V\> 解码（sinfer 动态返回类型 table\<V\>）；map\<any\> 值槽存堆 any 盒指针 → 解引用还原 |
| map_contains | 编译器内置：不 raise 的含键判断（数组二分 s21_arr_find / 哈希线性扫描 strcmp），布尔返回 |

**验收**：tests/language/table_coll_deep.tie（7 项 PASS：stats/stats_empty/pred/pred_pipe/
map_hof/map_str/map_any）+ 探针 p2d_stats/p2d_pred/p2d_map/p2d_map_any；
tests/language 全量正例 50/50 无回归；自举零错误。

# 12. P2e：集合库补全（2026-08-31，提交 74a4da0/80a1b96）——已实现

P2d 规划中的 table/set 标准库补全 set 部分，并深化表运算：

| 能力 | 实现 |
|------|------|
| set 集合（i64/string） | 载体 = 有序唯一 table；set_new/add（二分判重 + 有序插入）/contains（二分）/remove（二分定位 + ref 重建）/size/to_table + set_union/intersect/diff（双指针归并，O(n+m)） |
| set 实现要点 | 纯 std 复用 std/sort（contains_i64/index_of_i64/insert_sorted_*）；修改类用 ref 表参数 + 局部表重绑定（T0.3）；tie && 不短路 → 嵌套 if 防护越界 |
| concat | 拼接两表（新表，原表不变），i64/string |
| slice | 半开区间 t[start..end)：start 越界空表、end 越界截断，i64/string |
| copy / dedup | 深拷贝；去重保持首次出现顺序（线性 contains 判重），i64/string |

**验收**：tests/language/table_coll_set_p2e.tie（3 项 PASS：set_i64/set_ops/table_ops）
+ 探针 p2e_set/p2e_ops；tests/language 全量正例 52/52 无回归；自举零错误。




