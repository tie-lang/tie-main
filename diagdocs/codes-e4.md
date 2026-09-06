# tie 诊断标号 E4xxx — 运行时（Runtime） / tie diagnostic codes E4xxx — 运行时（Runtime）

> 每种标号的成因与常见解决方案说明由 tie-diag 文档维护；本页为自动生成的目录骨架。

### E40001  token_tag_at 下标越界
- 消息：`token_tag_at 下标越界：索引  <...>  超出长度 `；消息名：token_tag_at 下标越界
- 出处：`/compiler/interp/interp_call.tie`

### E40002  REPL 不支持调用 extern 函数 '?'（仅编译路径可用，请用 tie-llvm 编译运行）
- 消息：`REPL 不支持调用 extern 函数 ' <...> '（仅编译路径可用，请用 tie-llvm 编译运行）`；消息名：REPL 不支持调用 extern 函数 '?'（仅编译路径可用，请用 tie-llvm 编译运行）
- 出处：`/compiler/interp/interp.tie`

### E40003  trit 不支持除/取模运算（三值无除法）
- 消息：`trit 不支持除/取模运算（三值无除法）`；消息名：trit 不支持除/取模运算（三值无除法）
- 出处：`/compiler/interp/interp_bin.tie`

### E40004  '?' 不是宏（未以 macro 声明）
- 消息：`' <...> ' 不是宏（未以 macro 声明）`；消息名：'?' 不是宏（未以 macro 声明）
- 出处：`/compiler/interp/interp_macro.tie`

### E40005  i64 与 trit 不支持该运算:
- 消息：`i64 与 trit 不支持该运算: `；消息名：i64 与 trit 不支持该运算:
- 出处：`/compiler/interp/interp_bin.tie`

### E40006  code 值 .call() 不接受参数（第一版）
- 消息：`code 值 .call() 不接受参数（第一版）`；消息名：code 值 .call() 不接受参数（第一版）
- 出处：`/compiler/interp/interp.tie`

### E40007  eval_call: 函数 '?' 必须恰好接收 1 个字符串参数（实际形参 ? 个）
- 消息：`eval_call: 函数 ' <...> ' 必须恰好接收 1 个字符串参数（实际形参  <...>  个）`；消息名：eval_call: 函数 '?' 必须恰好接收 1 个字符串参数（实际形参 ? 个）
- 出处：`/compiler/interp/interp.tie`

### E40008  eval_call: 函数 '?' 缺少第 ? 个参数且无默认值
- 消息：`eval_call: 函数 ' <...> ' 缺少第  <...>  个参数且无默认值`；消息名：eval_call: 函数 '?' 缺少第 ? 个参数且无默认值
- 出处：`/compiler/interp/interp.tie`

### E40009  case 区间起点必须是整数或字符
- 消息：`case 区间起点必须是整数或字符`；消息名：case 区间起点必须是整数或字符
- 出处：`/compiler/interp/interp.tie`

### E40010  str_len 只支持字符串
- 消息：`str_len 只支持字符串`；消息名：str_len 只支持字符串
- 出处：`/compiler/interp/interp_call.tie`

### E40011  len 只支持字符串、表或键值表
- 消息：`len 只支持字符串、表或键值表`；消息名：len 只支持字符串、表或键值表
- 出处：`/compiler/interp/interp_call.tie`

### E40012  .call() 只能作用于 code 值（实际是 ?）
- 消息：`.call() 只能作用于 code 值（实际是  <...> ）`；消息名：.call() 只能作用于 code 值（实际是 ?）
- 出处：`/compiler/interp/interp.tie`

### E40013  .chars() 只能作用于字符串（实际是 ?）
- 消息：`.chars() 只能作用于字符串（实际是  <...> ）`；消息名：.chars() 只能作用于字符串（实际是 ?）
- 出处：`/compiler/interp/interp.tie`

### E40014  break?只能出现在循环体内
- 消息：`break <...> 只能出现在循环体内`；消息名：break?只能出现在循环体内
- 出处：`/compiler/interp/interp.tie`

### E40015  tokenize 失败: 词法错误 @?:?:
- 消息：`tokenize 失败: 词法错误 @ <...> : <...> : `；消息名：tokenize 失败: 词法错误 @?:?:
- 出处：`/compiler/interp/interp_call.tie`

### E40016  REPL v1 暂不支持 import
- 消息：`REPL v1 暂不支持 import`；消息名：REPL v1 暂不支持 import
- 出处：`/compiler/interp/interp.tie`

### E40017  REPL v1 暂不支持 struct 定义
- 消息：`REPL v1 暂不支持 struct 定义`；消息名：REPL v1 暂不支持 struct 定义
- 出处：`/compiler/interp/interp.tie`

### E40018  REPL v1 暂不支持 struct 方法调用
- 消息：`REPL v1 暂不支持 struct 方法调用`；消息名：REPL v1 暂不支持 struct 方法调用
- 出处：`/compiler/interp/interp.tie`

### E40019  REPL v1 暂不支持 goto 跳转（请用编译路径）
- 消息：`REPL v1 暂不支持 goto 跳转（请用编译路径）`；消息名：REPL v1 暂不支持 goto 跳转（请用编译路径）
- 出处：`/compiler/interp/interp.tie`

### E40020  REPL v1 暂不支持元组
- 消息：`REPL v1 暂不支持元组`；消息名：REPL v1 暂不支持元组
- 出处：`/compiler/interp/interp.tie`

### E40021  REPL v1 暂不支持字段访问（类/元组）
- 消息：`REPL v1 暂不支持字段访问（类/元组）`；消息名：REPL v1 暂不支持字段访问（类/元组）
- 出处：`/compiler/interp/interp.tie`

### E40022  REPL v1 暂不支持字段赋值（类）
- 消息：`REPL v1 暂不支持字段赋值（类）`；消息名：REPL v1 暂不支持字段赋值（类）
- 出处：`/compiler/interp/interp.tie`

### E40023  eval_call: 未定义的函数 '?'
- 消息：`eval_call: 未定义的函数 ' <...> '`；消息名：eval_call: 未定义的函数 '?'
- 出处：`/compiler/interp/interp.tie`

### E40024  token 流为空
- 消息：`token 流为空`；消息名：token 流为空
- 出处：`/compiler/interp/interp_macro.tie`

### E40025  token 流格式错误（第 ? 行缺少空格分隔）
- 消息：`token 流格式错误（第  <...>  行缺少空格分隔）`；消息名：token 流格式错误（第 ? 行缺少空格分隔）
- 出处：`/compiler/interp/interp_macro.tie`

### E40026  eval_code 源码语法错误:
- 消息：`eval_code 源码语法错误: `；消息名：eval_code 源码语法错误:
- 出处：`/compiler/interp/interp_call.tie`

### E40027  table_push 的第 1 个参数必须是表
- 消息：`table_push 的第 1 个参数必须是表`；消息名：table_push 的第 1 个参数必须是表
- 出处：`/compiler/interp/interp.tie`

### E40028  table_push 的第 1 个参数必须是表变量
- 消息：`table_push 的第 1 个参数必须是表变量`；消息名：table_push 的第 1 个参数必须是表变量
- 出处：`/compiler/interp/interp.tie`

### E40029  for 的迭代对象必须是范围（0..10）、表或字符串迭代器
- 消息：`for 的迭代对象必须是范围（0..10）、表或字符串迭代器`；消息名：for 的迭代对象必须是范围（0..10）、表或字符串迭代器
- 出处：`/compiler/interp/interp.tie`

### E40030  eval_expr 表达式为空
- 消息：`eval_expr 表达式为空`；消息名：eval_expr 表达式为空
- 出处：`/compiler/interp/interp_macro.tie`

### E40031  break?逃出函数体（内部错误）
- 消息：`break <...> 逃出函数体（内部错误）`；消息名：break?逃出函数体（内部错误）
- 出处：`/compiler/interp/interp_call.tie`

### E40032  token_tag_at 需要 token 流与下标参数
- 消息：`token_tag_at 需要 token 流与下标参数`；消息名：token_tag_at 需要 token 流与下标参数
- 出处：`/compiler/interp/interp_call.tie`

### E40033  trit_val 需要一个 trit 参数
- 消息：`trit_val 需要一个 trit 参数`；消息名：trit_val 需要一个 trit 参数
- 出处：`/compiler/interp/interp_call.tie`

### E40034  deparse 需要一个 token 流参数
- 消息：`deparse 需要一个 token 流参数`；消息名：deparse 需要一个 token 流参数
- 出处：`/compiler/interp/interp_call.tie`

### E40035  len 需要一个参数
- 消息：`len 需要一个参数`；消息名：len 需要一个参数
- 出处：`/compiler/interp/interp_call.tie`

### E40036  gensym 需要一个字符串前缀参数
- 消息：`gensym 需要一个字符串前缀参数`；消息名：gensym 需要一个字符串前缀参数
- 出处：`/compiler/interp/interp_call.tie`

### E40037  eval_expr 需要一个字符串参数
- 消息：`eval_expr 需要一个字符串参数`；消息名：eval_expr 需要一个字符串参数
- 出处：`/compiler/interp/interp_call.tie`

### E40038  eval_code 需要一个字符串源码参数
- 消息：`eval_code 需要一个字符串源码参数`；消息名：eval_code 需要一个字符串源码参数
- 出处：`/compiler/interp/interp_call.tie`

### E40039  to_string 需要一个数字参数
- 消息：`to_string 需要一个数字参数`；消息名：to_string 需要一个数字参数
- 出处：`/compiler/interp/interp_call.tie`

### E40040  to_trit 需要一个整数参数
- 消息：`to_trit 需要一个整数参数`；消息名：to_trit 需要一个整数参数
- 出处：`/compiler/interp/interp_call.tie`

### E40041  eval_call 需要两个字符串参数（函数名, 参数）
- 消息：`eval_call 需要两个字符串参数（函数名, 参数）`；消息名：eval_call 需要两个字符串参数（函数名, 参数）
- 出处：`/compiler/interp/interp_call.tie`

### E40042  str_char 需要字符串与整数参数
- 消息：`str_char 需要字符串与整数参数`；消息名：str_char 需要字符串与整数参数
- 出处：`/compiler/interp/interp_call.tie`

### E40043  table_push 需要表与元素参数
- 消息：`table_push 需要表与元素参数`；消息名：table_push 需要表与元素参数
- 出处：`/compiler/interp/interp.tie`

### E40044  table_at 需要表与整数下标参数
- 消息：`table_at 需要表与整数下标参数`；消息名：table_at 需要表与整数下标参数
- 出处：`/compiler/interp/interp_call.tie`

### E40045  一元负号只能作用于数字
- 消息：`一元负号只能作用于数字`；消息名：一元负号只能作用于数字
- 出处：`/compiler/interp/interp.tie`

### E40046  下标必须是整数
- 消息：`下标必须是整数`；消息名：下标必须是整数
- 出处：`/compiler/interp/interp.tie`

### E40047  下标访问仅支持表
- 消息：`下标访问仅支持表`；消息名：下标访问仅支持表
- 出处：`/compiler/interp/interp.tie`

### E40048  下标访问仅支持表或键值表
- 消息：`下标访问仅支持表或键值表`；消息名：下标访问仅支持表或键值表
- 出处：`/compiler/interp/interp.tie`

### E40049  下标赋值暂只支持单层表变量（t[i]）；二维表元素暂不支持写
- 消息：`下标赋值暂只支持单层表变量（t[i]）；二维表元素暂不支持写`；消息名：下标赋值暂只支持单层表变量（t[i]）；二维表元素暂不支持写
- 出处：`/compiler/interp/interp.tie`

### E40050  位运算/移位只支持整数
- 消息：`位运算/移位只支持整数`；消息名：位运算/移位只支持整数
- 出处：`/compiler/interp/interp_bin.tie`

### E40051  函数 '?' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）
- 消息：`函数 ' <...> ' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）`；消息名：函数 '?' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）
- 出处：`/compiler/interp/interp_call.tie`

### E40052  函数 '?' 缺少第 ? 个参数且无默认值
- 消息：`函数 ' <...> ' 缺少第  <...>  个参数且无默认值`；消息名：函数 '?' 缺少第 ? 个参数且无默认值
- 出处：`/compiler/interp/interp_call.tie`

### E40053  变量 '?' 未声明
- 消息：`变量 ' <...> ' 未声明`；消息名：变量 '?' 未声明
- 出处：`/compiler/interp/interp.tie`

### E40054  变量 '?' 重复声明
- 消息：`变量 ' <...> ' 重复声明`；消息名：变量 '?' 重复声明
- 出处：`/compiler/interp/interp.tie`

### E40055  右移量必须在 0..64 范围内
- 消息：`右移量必须在 0..64 范围内`；消息名：右移量必须在 0..64 范围内
- 出处：`/compiler/interp/interp_bin.tie`

### E40056  命名空间路径 '?' 不能作为值使用（只能用于调用）
- 消息：`命名空间路径 ' <...> ' 不能作为值使用（只能用于调用）`；消息名：命名空间路径 '?' 不能作为值使用（只能用于调用）
- 出处：`/compiler/interp/interp.tie`

### E40057  字符串迭代器 s.chars() 不接受实参
- 消息：`字符串迭代器 s.chars() 不接受实参`；消息名：字符串迭代器 s.chars() 不接受实参
- 出处：`/compiler/interp/interp.tie`

### E40058  宏 '?' 必须返回 code 值（return 了一个 ?）
- 消息：`宏 ' <...> ' 必须返回 code 值（return 了一个  <...> ）`；消息名：宏 '?' 必须返回 code 值（return 了一个 ?）
- 出处：`/compiler/interp/interp_macro.tie`

### E40059  宏 '?'
- 消息：`宏 ' <...> ' 期望  <...>  个 code 参数，实际  <...>  个`；消息名：宏 '?'
- 出处：`/compiler/interp/interp_macro.tie`

### E40060  宏 '?' 未定义
- 消息：`宏 ' <...> ' 未定义`；消息名：宏 '?' 未定义
- 出处：`/compiler/interp/interp_macro.tie`

### E40061  宏 '?' 未返回 code 值（函数体缺少 return code 语句）
- 消息：`宏 ' <...> ' 未返回 code 值（函数体缺少 return code 语句）`；消息名：宏 '?' 未返回 code 值（函数体缺少 return code 语句）
- 出处：`/compiler/interp/interp_macro.tie`

### E40062  宏 '?' 的实参必须是 code 值（准引用或插值），实际是
- 消息：`宏 ' <...> ' 的实参必须是 code 值（准引用或插值），实际是 `；消息名：宏 '?' 的实参必须是 code 值（准引用或插值），实际是
- 出处：`/compiler/interp/interp.tie`

### E40063  宏定义注册失败: 协议根既不是声明节点也不是语句列表
- 消息：`宏定义注册失败: 协议根既不是声明节点也不是语句列表`；消息名：宏定义注册失败: 协议根既不是声明节点也不是语句列表
- 出处：`/compiler/interp/interp_macro.tie`

### E40064  宏展开嵌套过深（超过 64 层，疑似无限递归）
- 消息：`宏展开嵌套过深（超过 64 层，疑似无限递归）：`；消息名：宏展开嵌套过深（超过 64 层，疑似无限递归）
- 出处：`/compiler/interp/interp_macro.tie`

### E40065  左移量必须在 0..64 范围内
- 消息：`左移量必须在 0..64 范围内`；消息名：左移量必须在 0..64 范围内
- 出处：`/compiler/interp/interp_bin.tie`

### E40066  布尔只能做逻辑运算与相等比较
- 消息：`布尔只能做逻辑运算与相等比较`；消息名：布尔只能做逻辑运算与相等比较
- 出处：`/compiler/interp/interp_bin.tie`

### E40067  插值 code 值缺少节点
- 消息：`插值 code 值缺少节点`；消息名：插值 code 值缺少节点
- 出处：`/compiler/interp/interp_code.tie`

### E40068  插值 $(表达式) 必须是 code 或字符串，实际是
- 消息：`插值 $(表达式) 必须是 code 或字符串，实际是 `；消息名：插值 $(表达式) 必须是 code 或字符串，实际是
- 出处：`/compiler/interp/interp_code.tie`

### E40069  插值变量 '?' 必须是 code 或字符串，实际是
- 消息：`插值变量 ' <...> ' 必须是 code 或字符串，实际是 `；消息名：插值变量 '?' 必须是 code 或字符串，实际是
- 出处：`/compiler/interp/interp_code.tie`

### E40070  插值变量 '?' 未声明
- 消息：`插值变量 ' <...> ' 未声明`；消息名：插值变量 '?' 未声明
- 出处：`/compiler/interp/interp_code.tie`

### E40071  插值名变量 '?' 必须是字符串或 code（实际 ?）
- 消息：`插值名变量 ' <...> ' 必须是字符串或 code（实际  <...> ）`；消息名：插值名变量 '?' 必须是字符串或 code（实际 ?）
- 出处：`/compiler/interp/interp_code.tie`

### E40072  插值名变量 '?' 未声明
- 消息：`插值名变量 ' <...> ' 未声明`；消息名：插值名变量 '?' 未声明
- 出处：`/compiler/interp/interp_code.tie`

### E40073  插值赋值目标必须是变量（code 值根不是变量节点）
- 消息：`插值赋值目标必须是变量（code 值根不是变量节点）`；消息名：插值赋值目标必须是变量（code 值根不是变量节点）
- 出处：`/compiler/interp/interp_code.tie`

### E40074  整数不能做逻辑运算（需布尔）
- 消息：`整数不能做逻辑运算（需布尔）`；消息名：整数不能做逻辑运算（需布尔）
- 出处：`/compiler/interp/interp_bin.tie`

### E40075  条件必须是布尔，实际是
- 消息：`条件必须是布尔，实际是 `；消息名：条件必须是布尔，实际是
- 出处：`/compiler/interp/value.tie`

### E40076  浮点数不能做逻辑运算（需布尔）
- 消息：`浮点数不能做逻辑运算（需布尔）`；消息名：浮点数不能做逻辑运算（需布尔）
- 出处：`/compiler/interp/interp_bin.tie`

### E40077  类型不匹配: ? ?
- 消息：`类型不匹配:  <...>   <...>  `；消息名：类型不匹配: ? ?
- 出处：`/compiler/interp/interp_bin.tie`

### E40078  编译错误:
- 消息：`编译错误: `；消息名：编译错误:
- 出处：`/compiler/interp/interp_call.tie`

### E40079  自增/自减只支持变量
- 消息：`自增/自减只支持变量`；消息名：自增/自减只支持变量
- 出处：`/compiler/interp/interp.tie`

### E40080  自增/自减只能作用于数字
- 消息：`自增/自减只能作用于数字`；消息名：自增/自减只能作用于数字
- 出处：`/compiler/interp/interp.tie`

### E40081  范围起点必须是整数
- 消息：`范围起点必须是整数`；消息名：范围起点必须是整数
- 出处：`/compiler/interp/interp.tie`

### E40082  词法错误 @?:?:
- 消息：`词法错误 @ <...> : <...> : `；消息名：词法错误 @?:?:
- 出处：`/compiler/interp/interp.tie`

### E40083  过程宏 '?' 必须返回 code 值（return 了一个 ?）
- 消息：`过程宏 ' <...> ' 必须返回 code 值（return 了一个  <...> ）`；消息名：过程宏 '?' 必须返回 code 值（return 了一个 ?）
- 出处：`/compiler/interp/interp_macro.tie`

### E40084  过程宏 '?'
- 消息：`过程宏 ' <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：过程宏 '?'
- 出处：`/compiler/interp/interp_macro.tie`

### E40085  过程宏 '?' 未定义
- 消息：`过程宏 ' <...> ' 未定义`；消息名：过程宏 '?' 未定义
- 出处：`/compiler/interp/interp_macro.tie`

### E40086  过程宏 '?' 未返回 code 值（函数体缺少 return code 语句）
- 消息：`过程宏 ' <...> ' 未返回 code 值（函数体缺少 return code 语句）`；消息名：过程宏 '?' 未返回 code 值（函数体缺少 return code 语句）
- 出处：`/compiler/interp/interp_macro.tie`

### E40087  运行时错误: table_at 下标越界
- 消息：`运行时错误: table_at 下标越界：索引  <...>  超出长度 `；消息名：运行时错误: table_at 下标越界
- 出处：`/compiler/interp/env.tie`

### E40088  运行时错误: parse_int 参数 '?' 不是合法的整数
- 消息：`运行时错误: parse_int 参数 ' <...> ' 不是合法的整数`；消息名：运行时错误: parse_int 参数 '?' 不是合法的整数
- 出处：`/compiler/interp/interp_call.tie`

### E40089  运行时错误: parse_float 参数 '?' 不是合法的浮点数
- 消息：`运行时错误: parse_float 参数 ' <...> ' 不是合法的浮点数`；消息名：运行时错误: parse_float 参数 '?' 不是合法的浮点数
- 出处：`/compiler/interp/interp_call.tie`

### E40090  运行时错误: 未实现的 stdio 桥函数 '?'
- 消息：`运行时错误: 未实现的 stdio 桥函数 ' <...> '`；消息名：运行时错误: 未实现的 stdio 桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40091  运行时错误: 未实现的字节桥函数 '?'
- 消息：`运行时错误: 未实现的字节桥函数 ' <...> '`；消息名：运行时错误: 未实现的字节桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40092  运行时错误: 未实现的数学桥函数 '?'
- 消息：`运行时错误: 未实现的数学桥函数 ' <...> '`；消息名：运行时错误: 未实现的数学桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40093  运行时错误: 未实现的文件桥函数 '?'
- 消息：`运行时错误: 未实现的文件桥函数 ' <...> '`；消息名：运行时错误: 未实现的文件桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40094  运行时错误: 未实现的标量桥函数 '?'
- 消息：`运行时错误: 未实现的标量桥函数 ' <...> '`；消息名：运行时错误: 未实现的标量桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40095  运行时错误: 未实现的路径/目录桥函数 '?'
- 消息：`运行时错误: 未实现的路径/目录桥函数 ' <...> '`；消息名：运行时错误: 未实现的路径/目录桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40096  运行时错误: 未实现的进程桥函数 '?'
- 消息：`运行时错误: 未实现的进程桥函数 ' <...> '`；消息名：运行时错误: 未实现的进程桥函数 '?'
- 出处：`/compiler/interp/env.tie`

### E40097  运行时错误: 环境桥函数 'exit' 在解释器内受限（REPL 退出经 read_line EOF）
- 消息：`运行时错误: 环境桥函数 'exit' 在解释器内受限（REPL 退出经 read_line EOF）`；消息名：运行时错误: 环境桥函数 'exit' 在解释器内受限（REPL 退出经 read_line EOF）
- 出处：`/compiler/interp/env.tie`

### E40098  运行时错误: 环境桥函数 'byte_write' 尚未 tie 化（限制清单见 env.tie 头注释）
- 消息：`运行时错误: 环境桥函数 'byte_write' 尚未 tie 化（限制清单见 env.tie 头注释）`；消息名：运行时错误: 环境桥函数 'byte_write' 尚未 tie 化（限制清单见 env.tie 头注释）
- 出处：`/compiler/interp/env.tie`

### E40099  运行时错误: map_get 键不存在
- 消息：`运行时错误: map_get 键不存在：' <...> '`；消息名：运行时错误: map_get 键不存在
- 出处：`/compiler/interp/value.tie`

### E40100  逻辑非只能作用于布尔
- 消息：`逻辑非只能作用于布尔`；消息名：逻辑非只能作用于布尔
- 出处：`/compiler/interp/interp.tie`

### E40101  键值表下标必须是字符串键
- 消息：`键值表下标必须是字符串键`；消息名：键值表下标必须是字符串键
- 出处：`/compiler/interp/interp.tie`

### E40102  键值表元素必须全部带字符串键
- 消息：`键值表元素必须全部带字符串键`；消息名：键值表元素必须全部带字符串键
- 出处：`/compiler/interp/interp.tie`

### E40103  除零错误
- 消息：`除零错误`；消息名：除零错误
- 出处：`/compiler/interp/interp_bin.tie`

### E40104  除零错误（取模）
- 消息：`除零错误（取模）`；消息名：除零错误（取模）
- 出处：`/compiler/interp/interp_bin.tie`

### E40105  顶层全局变量必须有初始化
- 消息：`顶层全局变量必须有初始化`；消息名：顶层全局变量必须有初始化
- 出处：`/compiler/interp/interp.tie`

### E40106  顶层只允许函数/类/import/using/命名空间/全局变量/extern 声明定义
- 消息：`顶层只允许函数/类/import/using/命名空间/全局变量/extern 声明定义`；消息名：顶层只允许函数/类/import/using/命名空间/全局变量/extern 声明定义
- 出处：`/compiler/interp/interp.tie`
