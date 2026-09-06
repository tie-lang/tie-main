# tie 诊断标号 E6xxx — 后端与 IR（Backend & IR） / tie diagnostic codes E6xxx — 后端与 IR（Backend & IR）

> 每种标号的成因与常见解决方案说明由 tie-diag 文档维护；本页为自动生成的目录骨架。

### E60001  irgen 不支持 code 字面量作语句（tag=136，函数 ?）
- 消息：`irgen 不支持 code 字面量作语句（tag=136，函数  <...> ）`；消息名：irgen 不支持 code 字面量作语句（tag=136，函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60002  guard<cap> 不支持方法 '?'（函数 ?）
- 消息：`guard<cap> 不支持方法 ' <...> '（函数  <...> ）`；消息名：guard<cap> 不支持方法 '?'（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60003  actor 与 import trm-lite 冲突
- 消息：`actor 与 import trm-lite 冲突：actor 默认由 trm-lite 简单执行体承载，与 import 是替代运行时路径，不能混用（函数  <...> ）`；消息名：actor 与 import trm-lite 冲突
- 出处：`/compiler/backend/irgen_rt.tie`

### E60004  case 值 '?' 不是 struct（函数 ?）
- 消息：`case 值 ' <...> ' 不是 struct（函数  <...> ）`；消息名：case 值 '?' 不是 struct（函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60005  case 值不是枚举 '?' 的变体引用（函数 ?）
- 消息：`case 值不是枚举 ' <...> ' 的变体引用（函数  <...> ）`；消息名：case 值不是枚举 '?' 的变体引用（函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60006  const 全局表暂不支持
- 消息：`const 全局表暂不支持：' <...> '需要 main 入口运行时创建，无法静态初始化`；消息名：const 全局表暂不支持
- 出处：`/compiler/proto/semantic.tie`

### E60007  spawn 内置与 import trm-lite 冲突
- 消息：`spawn 内置与 import trm-lite 冲突：内置与 import 是替代运行时路径，不能混用（函数  <...> ）`；消息名：spawn 内置与 import trm-lite 冲突
- 出处：`/compiler/backend/irgen_expr.tie`

### E60008  cb_ptr 参数 '?' 不是命名函数（函数 ?）
- 消息：`cb_ptr 参数 ' <...> ' 不是命名函数（函数  <...> ）`；消息名：cb_ptr 参数 '?' 不是命名函数（函数 ?）
- 出处：`/compiler/backend/irgen_rt.tie`

### E60009  spawn 参数必须是函数值（fn() -> i64 / fn() -> void），函数
- 消息：`spawn 参数必须是函数值（fn() -> i64 / fn() -> void），函数 `；消息名：spawn 参数必须是函数值（fn() -> i64 / fn() -> void），函数
- 出处：`/compiler/backend/irgen_expr.tie`

### E60010  cb_ptr 参数必须是无捕获闭包字面量或命名函数（函数 ?）
- 消息：`cb_ptr 参数必须是无捕获闭包字面量或命名函数（函数  <...> ）`；消息名：cb_ptr 参数必须是无捕获闭包字面量或命名函数（函数 ?）
- 出处：`/compiler/backend/irgen_rt.tie`

### E60011  cb_ptr 参数闭包含捕获变量（C 回调函数指针不携带环境），函数
- 消息：`cb_ptr 参数闭包含捕获变量（C 回调函数指针不携带环境），函数 `；消息名：cb_ptr 参数闭包含捕获变量（C 回调函数指针不携带环境），函数
- 出处：`/compiler/backend/irgen_rt.tie`

### E60012  addr_of_field() 字段 '?' 不存在（函数 ?）
- 消息：`addr_of_field() 字段 ' <...> ' 不存在（函数  <...> ）`；消息名：addr_of_field() 字段 '?' 不存在（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60013  addr_of_field() 字段名必须是字符串字面量（函数 ?）
- 消息：`addr_of_field() 字段名必须是字符串字面量（函数  <...> ）`；消息名：addr_of_field() 字段名必须是字符串字面量（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60014  slice_index() 实参必须是切片类型（函数 ?）
- 消息：`slice_index() 实参必须是切片类型（函数  <...> ）`；消息名：slice_index() 实参必须是切片类型（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60015  deref() 实参必须是指针类型（函数 ?）
- 消息：`deref() 实参必须是指针类型（函数  <...> ）`；消息名：deref() 实参必须是指针类型（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60016  addr_of() 实参类型未知（函数 ?）
- 消息：`addr_of() 实参类型未知（函数  <...> ）`；消息名：addr_of() 实参类型未知（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60017  switch 对象仅支持数字、布尔、字符或字符串类型，实际是
- 消息：`switch 对象仅支持数字、布尔、字符或字符串类型，实际是 `；消息名：switch 对象仅支持数字、布尔、字符或字符串类型，实际是
- 出处：`/compiler/proto/semantic.tie`

### E60018  addr_of_field() 对象类型未知（函数 ?）
- 消息：`addr_of_field() 对象类型未知（函数  <...> ）`；消息名：addr_of_field() 对象类型未知（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60019  asm! 平台 target(?) 与当前编译目标 ? 不匹配（无目标平台分支可编译）
- 消息：`asm! 平台 target( <...> ) 与当前编译目标  <...>  不匹配（无目标平台分支可编译）`；消息名：asm! 平台 target(?) 与当前编译目标 ? 不匹配（无目标平台分支可编译）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60020  actor 方法 '?' 未找到（函数 ?）
- 消息：`actor 方法 ' <...> ' 未找到（函数  <...> ）`；消息名：actor 方法 '?' 未找到（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60021  atomic 方法 '?' 生成失败（函数 ?）
- 消息：`atomic 方法 ' <...> ' 生成失败（函数  <...> ）`；消息名：atomic 方法 '?' 生成失败（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60022  actor 方法 ? 节点未找到
- 消息：`actor 方法  <...>  节点未找到`；消息名：actor 方法 ? 节点未找到
- 出处：`/compiler/backend/irgen_rt.tie`

### E60023  spawn 暂只支持返回 i64/void 的闭包（当前 ?），函数
- 消息：`spawn 暂只支持返回 i64/void 的闭包（当前  <...> ），函数 `；消息名：spawn 暂只支持返回 i64/void 的闭包（当前 ?），函数
- 出处：`/compiler/backend/irgen_expr.tie`

### E60024  struct '?' 未定义（函数 ?）
- 消息：`struct ' <...> ' 未定义（函数  <...> ）`；消息名：struct '?' 未定义（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60025  irgen 未支持的表达式（tag=?，函数 ?）
- 消息：`irgen 未支持的表达式（tag= <...> ，函数  <...> ）`；消息名：irgen 未支持的表达式（tag=?，函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60026  irgen 未支持的语句（tag=?，函数 ?）
- 消息：`irgen 未支持的语句（tag= <...> ，函数  <...> ）`；消息名：irgen 未支持的语句（tag=?，函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60027  port '?' 没有方法 '?'（函数 ?）
- 消息：`port ' <...> ' 没有方法 ' <...> '（函数  <...> ）`；消息名：port '?' 没有方法 '?'（函数 ?）
- 出处：`/compiler/backend/irgen_vtable.tie`

### E60028  run 的 '?' 不是已声明的 actor 类型（函数 ?）
- 消息：`run 的 ' <...> ' 不是已声明的 actor 类型（函数  <...> ）`；消息名：run 的 '?' 不是已声明的 actor 类型（函数 ?）
- 出处：`/compiler/backend/irgen_rt.tie`

### E60029  deref_write() 第 1 实参必须是指针类型（函数 ?）
- 消息：`deref_write() 第 1 实参必须是指针类型（函数  <...> ）`；消息名：deref_write() 第 1 实参必须是指针类型（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60030  slice_of() 第一版只支持字符串或动态表（函数 ?）
- 消息：`slice_of() 第一版只支持字符串或动态表（函数  <...> ）`；消息名：slice_of() 第一版只支持字符串或动态表（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60031  case 类型匹配（?）不是可装箱类型（函数 ?）
- 消息：`case 类型匹配（ <...> ）不是可装箱类型（函数  <...> ）`；消息名：case 类型匹配（?）不是可装箱类型（函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60032  any 装箱暂不支持类型 ?（函数 ?）
- 消息：`any 装箱暂不支持类型  <...> （函数  <...> ）`；消息名：any 装箱暂不支持类型 ?（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60033  tieir 读取失败
- 消息：`tieir 读取失败`；消息名：tieir 读取失败
- 出处：`(manual)`

### E60034  下标复合赋值运算失败（函数 ?）
- 消息：`下标复合赋值运算失败（函数  <...> ）`；消息名：下标复合赋值运算失败（函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60035  元组仅支持 ==/!= 比较（函数 ?）
- 消息：`元组仅支持 ==/!= 比较（函数  <...> ）`；消息名：元组仅支持 ==/!= 比较（函数 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60036  元组字段为表类型，不支持 ==/!= 比较（字段类型 ?）
- 消息：`元组字段为表类型，不支持 ==/!= 比较（字段类型  <...> ）`；消息名：元组字段为表类型，不支持 ==/!= 比较（字段类型 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60037  元组字面量缺少语义类型（函数 ?）
- 消息：`元组字面量缺少语义类型（函数  <...> ）`；消息名：元组字面量缺少语义类型（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60038  元组比较目标不是元组（函数 ?）
- 消息：`元组比较目标不是元组（函数  <...> ）`；消息名：元组比较目标不是元组（函数 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60039  内置调用 '?' 生成失败（函数 ?）
- 消息：`内置调用 ' <...> ' 生成失败（函数  <...> ）`；消息名：内置调用 '?' 生成失败（函数 ?）
- 出处：`/compiler/backend/irgen_expr.tie`

### E60040  函数 ? 参数类型解析失败
- 消息：`函数  <...>  参数类型解析失败`；消息名：函数 ? 参数类型解析失败
- 出处：`/compiler/backend/irgen.tie`

### E60041  函数 '?' 无定义节点，无法补齐默认值参数（函数 ?）
- 消息：`函数 ' <...> ' 无定义节点，无法补齐默认值参数（函数  <...> ）`；消息名：函数 '?' 无定义节点，无法补齐默认值参数（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60042  函数 '?' 无签名（函数 ?）
- 消息：`函数 ' <...> ' 无签名（函数  <...> ）`；消息名：函数 '?' 无签名（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60043  函数 '?'
- 消息：`函数 ' <...> ' 期望  <...>  到  <...>  个参数，实际  <...>  个`；消息名：函数 '?'
- 出处：`/compiler/proto/semantic.tie`

### E60044  函数 '?' 缺少第 ? 个参数且无默认值（函数 ?）
- 消息：`函数 ' <...> ' 缺少第  <...>  个参数且无默认值（函数  <...> ）`；消息名：函数 '?' 缺少第 ? 个参数且无默认值（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60045  函数 ? 返回类型解析失败
- 消息：`函数  <...>  返回类型解析失败`；消息名：函数 ? 返回类型解析失败
- 出处：`/compiler/backend/irgen.tie`

### E60046  函数值调用
- 消息：`函数值调用：变量 ' <...> ' 在实参求值后不可见（函数  <...> ）`；消息名：函数值调用
- 出处：`/compiler/backend/irgen_closure.tie`

### E60047  函数值调用
- 消息：`函数值调用：变量 ' <...> ' 类型缺失（函数  <...> ）`；消息名：函数值调用
- 出处：`/compiler/backend/irgen_closure.tie`

### E60048  动态库边界错误: 导出函数 ? 参数
- 消息：`动态库边界错误: 导出函数  <...>  参数`；消息名：动态库边界错误: 导出函数 ? 参数
- 出处：`/compiler/backend/irgen.tie`

### E60049  动态库边界错误: 导出函数 ? 返回
- 消息：`动态库边界错误: 导出函数  <...>  返回`；消息名：动态库边界错误: 导出函数 ? 返回
- 出处：`/compiler/backend/irgen.tie`

### E60050  原子变量 '?' 未入作用域（函数 ?）
- 消息：`原子变量 ' <...> ' 未入作用域（函数  <...> ）`；消息名：原子变量 '?' 未入作用域（函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60051  变量 '?' 未入作用域（函数 ?）
- 消息：`变量 ' <...> ' 未入作用域（函数  <...> ）`；消息名：变量 '?' 未入作用域（函数 ?）
- 出处：`/compiler/backend/irgen.tie`

### E60052  命名函数提升
- 消息：`命名函数提升：函数 ' <...> ' 无签名（函数  <...> ）`；消息名：命名函数提升
- 出处：`/compiler/backend/irgen_closure.tie`

### E60053  命名空间 ? 的函数 ? 生成失败
- 消息：`命名空间  <...>  的函数  <...>  生成失败`；消息名：命名空间 ? 的函数 ? 生成失败
- 出处：`/compiler/backend/irgen.tie`

### E60054  命名空间函数 '?'
- 消息：`命名空间函数 ' <...> ' 期望  <...>  到  <...>  个参数，实际  <...>  个`；消息名：命名空间函数 '?'
- 出处：`/compiler/proto/semantic.tie`

### E60055  复合字段赋值运算失败（字段 ?，函数 ?）
- 消息：`复合字段赋值运算失败（字段  <...> ，函数  <...> ）`；消息名：复合字段赋值运算失败（字段 ?，函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60056  复合赋值运算失败（变量 ?，函数 ?）
- 消息：`复合赋值运算失败（变量  <...> ，函数  <...> ）`；消息名：复合赋值运算失败（变量 ?，函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60057  字段 '?' 解析失败（函数 ?）
- 消息：`字段 ' <...> ' 解析失败（函数  <...> ）`；消息名：字段 '?' 解析失败（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60058  字段访问 '.' 的对象不是元组/struct（类型 ?，函数 ?）
- 消息：`字段访问 '.' 的对象不是元组/struct（类型  <...> ，函数  <...> ）`；消息名：字段访问 '.' 的对象不是元组/struct（类型 ?，函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60059  字段赋值的目标不是元组/struct（类型 ?，函数 ?）
- 消息：`字段赋值的目标不是元组/struct（类型  <...> ，函数  <...> ）`；消息名：字段赋值的目标不是元组/struct（类型 ?，函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60060  提升操作数类型缺失（函数 ?）
- 消息：`提升操作数类型缺失（函数  <...> ）`；消息名：提升操作数类型缺失（函数 ?）
- 出处：`/compiler/backend/irgen_vtable.tie`

### E60061  方法 '?'
- 消息：`方法 ' <...> ' 期望  <...>  个参数（不含接收者），实际  <...>  个`；消息名：方法 '?'
- 出处：`/compiler/proto/semantic.tie`

### E60062  方法调用接收者不可解析（方法 ?，函数 ?）
- 消息：`方法调用接收者不可解析（方法  <...> ，函数  <...> ）`；消息名：方法调用接收者不可解析（方法 ?，函数 ?）
- 出处：`/compiler/backend/irgen_call.tie`

### E60063  未找到 opt，请确认 LLVM 已安装并在 PATH 中
- 消息：`未找到 opt，请确认 LLVM 已安装并在 PATH 中`；消息名：未找到 opt，请确认 LLVM 已安装并在 PATH 中
- 出处：`/compiler/backend/toolchain.tie`

### E60064  未知 checked_* 函数 '?'（函数 ?）
- 消息：`未知 checked_* 函数 ' <...> '（函数  <...> ）`；消息名：未知 checked_* 函数 '?'（函数 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60065  枚举 '?' 没有变体 '?'（函数 ?）
- 消息：`枚举 ' <...> ' 没有变体 ' <...> '（函数  <...> ）`；消息名：枚举 '?' 没有变体 '?'（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60066  父 struct '?' 未定义
- 消息：`父 struct ' <...> ' 未定义`；消息名：父 struct '?' 未定义
- 出处：`/compiler/proto/semantic.tie`

### E60067  程序使用了 tie-interp 桥内置，但未找到 tie-interp 静态库。? ? -lws2_32 -luserenv -lntdll -lbcrypt -ladvapi32 -lole32 -lshell32
- 消息：`程序使用了 tie-interp 桥内置，但未找到 tie-interp 静态库。 <...>   <...>  -lws2_32 -luserenv -lntdll -lbcrypt -ladvapi32 -lole32 -lshell32`；消息名：程序使用了 tie-interp 桥内置，但未找到 tie-interp 静态库。? ? -lws2_32 -luserenv -lntdll -lbcrypt -ladvapi32 -lole32 -lshell32
- 出处：`/compiler/backend/toolchain.tie`

### E60068  程序使用了 trm-lite 运行时（spawn/yield/collect 或表容器 table<T>），但未找到 trm-lite 静态库。? ? -rtlib=compiler-rt
- 消息：`程序使用了 trm-lite 运行时（spawn/yield/collect 或表容器 table<T>），但未找到 trm-lite 静态库。 <...>   <...>  -rtlib=compiler-rt`；消息名：程序使用了 trm-lite 运行时（spawn/yield/collect 或表容器 table<T>），但未找到 trm-lite 静态库。? ? -rtlib=compiler-rt
- 出处：`/compiler/backend/toolchain.tie`

### E60069  箭头赋值目标 '?' 未入作用域（函数 ?）
- 消息：`箭头赋值目标 ' <...> ' 未入作用域（函数  <...> ）`；消息名：箭头赋值目标 '?' 未入作用域（函数 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60070  类 '?' 未定义
- 消息：`类 ' <...> ' 未定义`；消息名：类 '?' 未定义
- 出处：`/compiler/proto/semantic.tie`

### E60071  自增自减目标 '?' 未入作用域（函数 ?）
- 消息：`自增自减目标 ' <...> ' 未入作用域（函数  <...> ）`；消息名：自增自减目标 '?' 未入作用域（函数 ?）
- 出处：`/compiler/backend/irgen_arith.tie`

### E60072  表元素类型不一致
- 消息：`表元素类型不一致： <...>  与 `；消息名：表元素类型不一致
- 出处：`/compiler/proto/semantic.tie`

### E60073  调用表达式要求被调者为函数类型（函数 ?）
- 消息：`调用表达式要求被调者为函数类型（函数  <...> ）`；消息名：调用表达式要求被调者为函数类型（函数 ?）
- 出处：`/compiler/backend/irgen_closure.tie`

### E60074  赋值目标 '?' 未入作用域（函数 ?）
- 消息：`赋值目标 ' <...> ' 未入作用域（函数  <...> ）`；消息名：赋值目标 '?' 未入作用域（函数 ?）
- 出处：`/compiler/backend/irgen_stmt.tie`

### E60075  键值表值类型不匹配
- 消息：`键值表值类型不匹配：map 值为  <...>  与 `；消息名：键值表值类型不匹配
- 出处：`/compiler/proto/semantic.tie`

### E60076  键值表字面量元素缺少字符串键（函数 ?）
- 消息：`键值表字面量元素缺少字符串键（函数  <...> ）`；消息名：键值表字面量元素缺少字符串键（函数 ?）
- 出处：`/compiler/backend/irgen_agg.tie`

### E60077  闭包返回类型解析失败
- 消息：`闭包返回类型解析失败`；消息名：闭包返回类型解析失败
- 出处：`/compiler/backend/irgen_closure.tie`

### E60078  顶层函数 ? 生成失败
- 消息：`顶层函数  <...>  生成失败`；消息名：顶层函数 ? 生成失败
- 出处：`/compiler/backend/irgen.tie`

### E60079  顶层命名空间生成失败
- 消息：`顶层命名空间生成失败`；消息名：顶层命名空间生成失败
- 出处：`/compiler/backend/irgen.tie`
