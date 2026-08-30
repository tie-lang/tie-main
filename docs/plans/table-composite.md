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

