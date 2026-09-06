# tie 诊断标号 E3xxx — 语义（Semantic） / tie diagnostic codes E3xxx — 语义（Semantic）

> 每种标号的成因与常见解决方案说明由 tie-diag 文档维护；本页为自动生成的目录骨架。

### E30001  table_at() 下标必须是整数，实际是
- 消息：`table_at() 下标必须是整数，实际是 `；消息名：table_at() 下标必须是整数，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30002  port '?' 不接受类型参数（第一版 port 不支持泛型）
- 消息：`port ' <...> ' 不接受类型参数（第一版 port 不支持泛型）`；消息名：port '?' 不接受类型参数（第一版 port 不支持泛型）
- 出处：`/compiler/frontend/sgen.tie`

### E30003  struct '?' 不接受类型参数（非泛型 struct）
- 消息：`struct ' <...> ' 不接受类型参数（非泛型 struct）`；消息名：struct '?' 不接受类型参数（非泛型 struct）
- 出处：`/compiler/frontend/sgen.tie`

### E30004  atomic<T> 不支持方法 '?'（支持: load/store/fetch_add/fetch_sub/fetch_and/fetch_or/fetch_xor/compare_exchange）
- 消息：`atomic<T> 不支持方法 ' <...> '（支持: load/store/fetch_add/fetch_sub/fetch_and/fetch_or/fetch_xor/compare_exchange）`；消息名：atomic<T> 不支持方法 '?'（支持: load/store/fetch_add/fetch_sub/fetch_and/fetch_or/fetch_xor/compare_exchange）
- 出处：`/compiler/frontend/sinfer.tie`

### E30005  guard<?> 不能委派为 guard<?>（delegate 第1批仅同域派生）
- 消息：`guard< <...> > 不能委派为 guard< <...> >（delegate 第1批仅同域派生）`；消息名：guard<?> 不能委派为 guard<?>（delegate 第1批仅同域派生）
- 出处：`/compiler/frontend/sinfer.tie`

### E30006  case 值 '?' 与 switch 对象枚举类型 ? 不匹配
- 消息：`case 值 ' <...> ' 与 switch 对象枚举类型  <...>  不匹配`；消息名：case 值 '?' 与 switch 对象枚举类型 ? 不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30007  case 值 '?' 与 switch 对象枚举类型 ? 不匹配（泛型 enum 实例）
- 消息：`case 值 ' <...> ' 与 switch 对象枚举类型  <...>  不匹配（泛型 enum 实例）`；消息名：case 值 '?' 与 switch 对象枚举类型 ? 不匹配（泛型 enum 实例）
- 出处：`/compiler/frontend/scheck.tie`

### E30008  case 值必须是字面量（整数/浮点/字符/布尔/字符串）
- 消息：`case 值必须是字面量（整数/浮点/字符/布尔/字符串）`；消息名：case 值必须是字面量（整数/浮点/字符/布尔/字符串）
- 出处：`/compiler/frontend/scheck.tie`

### E30009  case 值必须是枚举变体引用（如 ?.Variant / ?.Variant(v)）
- 消息：`case 值必须是枚举变体引用（如  <...> .Variant /  <...> .Variant(v)）`；消息名：case 值必须是枚举变体引用（如 ?.Variant / ?.Variant(v)）
- 出处：`/compiler/frontend/scheck.tie`

### E30010  case 值类型 ? 与 switch 对象类型 ? 不匹配
- 消息：`case 值类型  <...>  与 switch 对象类型  <...>  不匹配`；消息名：case 值类型 ? 与 switch 对象类型 ? 不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30011  atomic.store() 值类型不匹配
- 消息：`atomic.store() 值类型不匹配：期望  <...> ，实际 `；消息名：atomic.store() 值类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30012  table_push() 元素类型不匹配
- 消息：`table_push() 元素类型不匹配：表 ' <...> ' 的元素是  <...> ，推入的是 `；消息名：table_push() 元素类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30013  asm! 内联汇编必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）
- 消息：`asm! 内联汇编必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）`；消息名：asm! 内联汇编必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）
- 出处：`/compiler/frontend/sinfer.tie`

### E30014  extern 函数 '?' 与已有函数重复定义
- 消息：`extern 函数 ' <...> ' 与已有函数重复定义`；消息名：extern 函数 '?' 与已有函数重复定义
- 出处：`/compiler/frontend/scollect_port.tie`

### E30015  extern 函数 '?' 的参数 '?' 必须是标量/string/ptr/slice 类型，实际是
- 消息：`extern 函数 ' <...> ' 的参数 ' <...> ' 必须是标量/string/ptr/slice 类型，实际是 `；消息名：extern 函数 '?' 的参数 '?' 必须是标量/string/ptr/slice 类型，实际是
- 出处：`/compiler/frontend/scollect_port.tie`

### E30016  extern 函数 '?' 的参数 '?' 必须是标量/string/ptr/slice 类型，或 repr(C) struct（按引用传指针）；'?' 不是 repr(C)，需显式标注 repr(C)
- 消息：`extern 函数 ' <...> ' 的参数 ' <...> ' 必须是标量/string/ptr/slice 类型，或 repr(C) struct（按引用传指针）；' <...> ' 不是 repr(C)，需显式标注 repr(C)`；消息名：extern 函数 '?' 的参数 '?' 必须是标量/string/ptr/slice 类型，或 repr(C) struct（按引用传指针）；'?' 不是 repr(C)，需显式标注 repr(C)
- 出处：`/compiler/frontend/scollect_port.tie`

### E30017  extern 函数 '?' 的返回类型必须是标量/string/ptr/slice 或 void，实际是
- 消息：`extern 函数 ' <...> ' 的返回类型必须是标量/string/ptr/slice 或 void，实际是 `；消息名：extern 函数 '?' 的返回类型必须是标量/string/ptr/slice 或 void，实际是
- 出处：`/compiler/frontend/scollect_port.tie`

### E30018  case 区间两端必须是整数或字符字面量（浮点区间不支持）
- 消息：`case 区间两端必须是整数或字符字面量（浮点区间不支持）`；消息名：case 区间两端必须是整数或字符字面量（浮点区间不支持）
- 出处：`/compiler/frontend/scheck.tie`

### E30019  case 区间必须 start < end（左闭右开）
- 消息：`case 区间必须 start < end（左闭右开）`；消息名：case 区间必须 start < end（左闭右开）
- 出处：`/compiler/frontend/scheck.tie`

### E30020  case 区间类型与 switch 对象类型 ? 不匹配
- 消息：`case 区间类型与 switch 对象类型  <...>  不匹配`；消息名：case 区间类型与 switch 对象类型 ? 不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30021  any_tag() 参数必须是 any，实际是
- 消息：`any_tag() 参数必须是 any，实际是 `；消息名：any_tag() 参数必须是 any，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30022  slice_len() 参数必须是切片类型，实际是
- 消息：`slice_len() 参数必须是切片类型，实际是 `；消息名：slice_len() 参数必须是切片类型，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30023  eval() 参数必须是字符串，实际是
- 消息：`eval() 参数必须是字符串，实际是 `；消息名：eval() 参数必须是字符串，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30024  slice_of() 只支持字符串或动态表，实际是
- 消息：`slice_of() 只支持字符串或动态表，实际是 `；消息名：slice_of() 只支持字符串或动态表，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30025  unsafe use 只能在 unsafe 上下文使用（unsafe 块或 unsafe 函数内）
- 消息：`unsafe use 只能在 unsafe 上下文使用（unsafe 块或 unsafe 函数内）`；消息名：unsafe use 只能在 unsafe 上下文使用（unsafe 块或 unsafe 函数内）
- 出处：`/compiler/frontend/scheck.tie`

### E30026  port 名 '?' 与 struct 名冲突
- 消息：`port 名 ' <...> ' 与 struct 名冲突`；消息名：port 名 '?' 与 struct 名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30027  port 名 '?' 与函数名冲突
- 消息：`port 名 ' <...> ' 与函数名冲突`；消息名：port 名 '?' 与函数名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30028  port 名 '?' 与枚举名冲突
- 消息：`port 名 ' <...> ' 与枚举名冲突`；消息名：port 名 '?' 与枚举名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30029  port 名 '?' 与泛型模板名冲突
- 消息：`port 名 ' <...> ' 与泛型模板名冲突`；消息名：port 名 '?' 与泛型模板名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30030  goto 向前跳过局部变量初始化（goto 与标签之间不得经过 var/const 声明，R3）
- 消息：`goto 向前跳过局部变量初始化（goto 与标签之间不得经过 var/const 声明，R3）`；消息名：goto 向前跳过局部变量初始化（goto 与标签之间不得经过 var/const 声明，R3）
- 出处：`/compiler/frontend/scheck.tie`

### E30031  extern 声明必须标注 unsafe（`unsafe extern fn ?(...)`），安全代码禁止直接调用外部符号
- 消息：`extern 声明必须标注 unsafe（`unsafe extern fn  <...> (...)`），安全代码禁止直接调用外部符号`；消息名：extern 声明必须标注 unsafe（`unsafe extern fn ?(...)`），安全代码禁止直接调用外部符号
- 出处：`/compiler/frontend/scollect_port.tie`

### E30032  code 字面量不能作为语句
- 消息：`code 字面量不能作为语句`；消息名：code 字面量不能作为语句
- 出处：`/compiler/frontend/scheck.tie`

### E30033  when 守卫必须是布尔表达式，实际是
- 消息：`when 守卫必须是布尔表达式，实际是 `；消息名：when 守卫必须是布尔表达式，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30034  struct 实例 '?' 的字段访问需要可寻址对象（变量/字段链），
- 消息：`struct 实例 ' <...> ' 的字段访问需要可寻址对象（变量/字段链），`；消息名：struct 实例 '?' 的字段访问需要可寻址对象（变量/字段链），
- 出处：`/compiler/frontend/sinfer.tie`

### E30035  port '?' 对 struct '?' 的 impl 重复定义
- 消息：`port ' <...> ' 对 struct ' <...> ' 的 impl 重复定义`；消息名：port '?' 对 struct '?' 的 impl 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30036  switch 对象仅支持数字、布尔、字符、字符串、枚举或 any 类型，实际是
- 消息：`switch 对象仅支持数字、布尔、字符、字符串、枚举或 any 类型，实际是 `；消息名：switch 对象仅支持数字、布尔、字符、字符串、枚举或 any 类型，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30037  port 对象变量 '?' 必须初始化（如 unsafe { var ?: ? = 具体实例 }）
- 消息：`port 对象变量 ' <...> ' 必须初始化（如 unsafe { var  <...> :  <...>  = 具体实例 }）`；消息名：port 对象变量 '?' 必须初始化（如 unsafe { var ?: ? = 具体实例 }）
- 出处：`/compiler/frontend/scheck.tie`

### E30038  port 对象变量 '?' 的初始化必须是实现了该 port 的具体类型实例（提升）或同 port 对象，实际是
- 消息：`port 对象变量 ' <...> ' 的初始化必须是实现了该 port 的具体类型实例（提升）或同 port 对象，实际是 `；消息名：port 对象变量 '?' 的初始化必须是实现了该 port 的具体类型实例（提升）或同 port 对象，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30039  port 对象变量 '?' 类型不匹配
- 消息：`port 对象变量 ' <...> ' 类型不匹配：标注  <...> ，表达式推导为 `；消息名：port 对象变量 '?' 类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30040  impl 引用的 port '?' 未定义
- 消息：`impl 引用的 port ' <...> ' 未定义`；消息名：impl 引用的 port '?' 未定义
- 出处：`/compiler/frontend/scollect_port.tie`

### E30041  atomic.compare_exchange() 新值类型不匹配
- 消息：`atomic.compare_exchange() 新值类型不匹配：期望  <...> ，实际 `；消息名：atomic.compare_exchange() 新值类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30042  impl 方法 '?' 参数个数与 port 签名不匹配
- 消息：`impl 方法 ' <...> ' 参数个数与 port 签名不匹配：期望  <...> ，实际 `；消息名：impl 方法 '?' 参数个数与 port 签名不匹配
- 出处：`/compiler/frontend/scollect_port.tie`

### E30043  impl 方法 '?' 参数类型与 port 签名不匹配（port 方法参数必须类型一致）
- 消息：`impl 方法 ' <...> ' 参数类型与 port 签名不匹配（port 方法参数必须类型一致）`；消息名：impl 方法 '?' 参数类型与 port 签名不匹配（port 方法参数必须类型一致）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30044  port 方法 '?' 必须有 self 接收者（第一参数）
- 消息：`port 方法 ' <...> ' 必须有 self 接收者（第一参数）`；消息名：port 方法 '?' 必须有 self 接收者（第一参数）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30045  impl 方法 '?' 必须有函数体（impl 块 = 实现，不能只声明签名）
- 消息：`impl 方法 ' <...> ' 必须有函数体（impl 块 = 实现，不能只声明签名）`；消息名：impl 方法 '?' 必须有函数体（impl 块 = 实现，不能只声明签名）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30046  port 方法 '?' 必须标注 pub（`pub func ?`）
- 消息：`port 方法 ' <...> ' 必须标注 pub（`pub func  <...> `）`；消息名：port 方法 '?' 必须标注 pub（`pub func ?`）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30047  port 方法 '?' 的第一参数必须是 self
- 消息：`port 方法 ' <...> ' 的第一参数必须是 self`；消息名：port 方法 '?' 的第一参数必须是 self
- 出处：`/compiler/frontend/scollect_port.tie`

### E30048  impl 方法 '?' 返回类型与 port 签名不匹配
- 消息：`impl 方法 ' <...> ' 返回类型与 port 签名不匹配：期望  <...> ，实际 `；消息名：impl 方法 '?' 返回类型与 port 签名不匹配
- 出处：`/compiler/frontend/scollect_port.tie`

### E30049  load_library()
- 消息：`load_library() 期望 1 个参数（DLL 名），实际  <...>  个`；消息名：load_library()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30050  cstr_to_string()
- 消息：`cstr_to_string() 期望 1 个参数（C 字符串地址），实际  <...>  个`；消息名：cstr_to_string()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30051  ch_select()
- 消息：`ch_select() 期望 3 个参数（handles/actions/values 表），实际  <...>  个`；消息名：ch_select()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30052  any_tag()
- 消息：`any_tag() 期望 1 个参数（any），实际  <...>  个`；消息名：any_tag()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30053  atomic.store()
- 消息：`atomic.store() 期望 2 个参数（值, 内存序），实际  <...>  个`；消息名：atomic.store()
- 出处：`/compiler/frontend/sinfer.tie`

### E30054  catch_panic()
- 消息：`catch_panic() 期望 1 个参数（函数值），实际  <...>  个`；消息名：catch_panic()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30055  eval_call()
- 消息：`eval_call() 期望 2 个参数（函数名, 参数），实际  <...>  个`；消息名：eval_call()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30056  wg_add()
- 消息：`wg_add() 期望 2 个参数（句柄, n），实际  <...>  个`；消息名：wg_add()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30057  sb_build()
- 消息：`sb_build() 期望 1 个参数（句柄），实际  <...>  个`；消息名：sb_build()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30058  atomic.?()
- 消息：`atomic. <...> () 期望 2 个参数（增量, 内存序），实际  <...>  个`；消息名：atomic.?()
- 出处：`/compiler/frontend/sinfer.tie`

### E30059  str_sub_bytes()
- 消息：`str_sub_bytes() 期望 3 个参数（字符串, 起, 止），实际  <...>  个`；消息名：str_sub_bytes()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30060  alloc()
- 消息：`alloc() 期望 1 个参数（字节数），实际  <...>  个`；消息名：alloc()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30061  byte_concat()
- 消息：`byte_concat() 期望 2 个参数（字节表, 字节表），实际  <...>  个`；消息名：byte_concat()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30062  addr_of_field()
- 消息：`addr_of_field() 期望 2 个参数（对象, 字段名），实际  <...>  个`；消息名：addr_of_field()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30063  slice_of()
- 消息：`slice_of() 期望 3 个参数（对象, 起点, 长度），实际  <...>  个`；消息名：slice_of()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30064  deref_write()
- 消息：`deref_write() 期望 2 个参数（指针, 值），实际  <...>  个`；消息名：deref_write()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30065  free()
- 消息：`free() 期望 1 个参数（指针），实际  <...>  个`；消息名：free()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30066  atomic.compare_exchange()
- 消息：`atomic.compare_exchange() 期望 3 个参数（期望值, 新值, 内存序），实际  <...>  个`；消息名：atomic.compare_exchange()
- 出处：`/compiler/frontend/sinfer.tie`

### E30067  get_proc()
- 消息：`get_proc() 期望 2 个参数（模块句柄, 函数名），实际  <...>  个`；消息名：get_proc()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30068  table_at()
- 消息：`table_at() 期望 2 个参数（表, 下标），实际  <...>  个`；消息名：table_at()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30069  table_push()
- 消息：`table_push() 期望 2 个参数（表, 元素），实际  <...>  个`；消息名：table_push()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30070  ch_send()
- 消息：`ch_send() 期望 2 个参数（通道, 值），实际  <...>  个`；消息名：ch_send()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30071  ch_recv()
- 消息：`ch_recv() 期望 1 个参数（通道），实际  <...>  个`；消息名：ch_recv()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30072  msg_t_lang()
- 消息：`msg_t_lang() 期望 2 个参数（键, 语言），实际  <...>  个`；消息名：msg_t_lang()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30073  ptr_to_int()
- 消息：`ptr_to_int() 期望 1 个参数，实际  <...>  个`；消息名：ptr_to_int()
- 出处：`/compiler/frontend/sbuiltin.tie`

### E30074  guard<cap>.delegate
- 消息：`guard<cap>.delegate 期望 1 个能力名参数（share/mem/ext），实际  <...>  个`；消息名：guard<cap>.delegate
- 出处：`/compiler/frontend/sinfer.tie`

### E30075  atomic.load()
- 消息：`atomic.load() 期望 0 或 1 个参数（内存序），实际  <...>  个`；消息名：atomic.load()
- 出处：`/compiler/frontend/sinfer.tie`

### E30076  atomic.compare_exchange() 期望值类型不匹配
- 消息：`atomic.compare_exchange() 期望值类型不匹配：期望  <...> ，实际 `；消息名：atomic.compare_exchange() 期望值类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30077  if 条件必须是 bool
- 消息：`if 条件必须是 bool`；消息名：if 条件必须是 bool
- 出处：`/compiler/frontend/scheck.tie`

### E30078  goto 标签 '#?' 重复定义（同函数内标签名必须唯一）
- 消息：`goto 标签 '# <...> ' 重复定义（同函数内标签名必须唯一）`；消息名：goto 标签 '#?' 重复定义（同函数内标签名必须唯一）
- 出处：`/compiler/frontend/scheck.tie`

### E30079  port '?' 没有方法 '?'
- 消息：`port ' <...> ' 没有方法 ' <...> '`；消息名：port '?' 没有方法 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30080  actor '?' 没有消息方法 '?'
- 消息：`actor ' <...> ' 没有消息方法 ' <...> '`；消息名：actor '?' 没有消息方法 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30081  panic 消息必须是 string，实际是
- 消息：`panic 消息必须是 string，实际是 `；消息名：panic 消息必须是 string，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30082  actor 消息方法 '?' 必须声明为 pub
- 消息：`actor 消息方法 ' <...> ' 必须声明为 pub`；消息名：actor 消息方法 '?' 必须声明为 pub
- 出处：`/compiler/frontend/scollect_port.tie`

### E30083  async 消息方法 '?' 必须返回 void（异步投递无返回值）
- 消息：`async 消息方法 ' <...> ' 必须返回 void（异步投递无返回值）`；消息名：async 消息方法 '?' 必须返回 void（异步投递无返回值）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30084  run 的 '?' 不是已声明的 actor 类型
- 消息：`run 的 ' <...> ' 不是已声明的 actor 类型`；消息名：run 的 '?' 不是已声明的 actor 类型
- 出处：`/compiler/frontend/sinfer.tie`

### E30085  unsafe use 的 '?' 必须是 guard<cap> 凭据变量（来自 unsafe.get(share) 等）
- 消息：`unsafe use 的 ' <...> ' 必须是 guard<cap> 凭据变量（来自 unsafe.get(share) 等）`；消息名：unsafe use 的 '?' 必须是 guard<cap> 凭据变量（来自 unsafe.get(share) 等）
- 出处：`/compiler/frontend/scheck.tie`

### E30086  actor '?' 的字段 '?' 重复定义
- 消息：`actor ' <...> ' 的字段 ' <...> ' 重复定义`；消息名：actor '?' 的字段 '?' 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30087  impl '? for ?' 的方法 '?' 重复定义
- 消息：`impl ' <...>  for  <...> ' 的方法 ' <...> ' 重复定义`；消息名：impl '? for ?' 的方法 '?' 重复定义
- 出处：`/compiler/frontend/scollect_port.tie`

### E30088  goto 的目标标签 '#?' 未定义（R1 同函数
- 消息：`goto 的目标标签 '# <...> ' 未定义（R1 同函数：同函数内必须有 #[tag. <...> ] 标签）`；消息名：goto 的目标标签 '#?' 未定义（R1 同函数
- 出处：`/compiler/frontend/scheck.tie`

### E30089  unsafe with 的能力域必须是 share/mem/ext，实际是 '?'
- 消息：`unsafe with 的能力域必须是 share/mem/ext，实际是 ' <...> '`；消息名：unsafe with 的能力域必须是 share/mem/ext，实际是 '?'
- 出处：`/compiler/frontend/scheck.tie`

### E30090  goto 目标 '#?' 不在同块或外层块（禁止跳入更内层块/跨块跳转，R2）
- 消息：`goto 目标 '# <...> ' 不在同块或外层块（禁止跳入更内层块/跨块跳转，R2）`；消息名：goto 目标 '#?' 不在同块或外层块（禁止跳入更内层块/跨块跳转，R2）
- 出处：`/compiler/frontend/scheck.tie`

### E30091  goto 目标 '#?' 在外层块但位于 goto 之后（只能向后跳到已执行的外层块头，R2）
- 消息：`goto 目标 '# <...> ' 在外层块但位于 goto 之后（只能向后跳到已执行的外层块头，R2）`；消息名：goto 目标 '#?' 在外层块但位于 goto 之后（只能向后跳到已执行的外层块头，R2）
- 出处：`/compiler/frontend/scheck.tie`

### E30092  map_contains() 第 1 个参数必须是 map，实际是
- 消息：`map_contains() 第 1 个参数必须是 map，实际是 `；消息名：map_contains() 第 1 个参数必须是 map，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30093  slice_index() 第 1 个参数必须是切片类型，实际是
- 消息：`slice_index() 第 1 个参数必须是切片类型，实际是 `；消息名：slice_index() 第 1 个参数必须是切片类型，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30094  volatile_load() 第 1 个参数必须是指针类型，实际是
- 消息：`volatile_load() 第 1 个参数必须是指针类型，实际是 `；消息名：volatile_load() 第 1 个参数必须是指针类型，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30095  table_push() 第 1 个参数必须是表变量（不能是字面量/下标）
- 消息：`table_push() 第 1 个参数必须是表变量（不能是字面量/下标）`；消息名：table_push() 第 1 个参数必须是表变量（不能是字面量/下标）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30096  return 类型不匹配
- 消息：`return 类型不匹配：函数返回  <...> ，实际返回 `；消息名：return 类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30097  code 类型值只能在宏函数体内使用（宏 = 编译期 AST→AST 函数；准引用/插值/宏参数都是编译期构造）
- 消息：`code 类型值只能在宏函数体内使用（宏 = 编译期 AST→AST 函数；准引用/插值/宏参数都是编译期构造）`；消息名：code 类型值只能在宏函数体内使用（宏 = 编译期 AST→AST 函数；准引用/插值/宏参数都是编译期构造）
- 出处：`/compiler/frontend/scheck.tie`

### E30098  case 类型匹配（?）不是可装箱类型（整数/浮点/bool/string/char）
- 消息：`case 类型匹配（ <...> ）不是可装箱类型（整数/浮点/bool/string/char）`；消息名：case 类型匹配（?）不是可装箱类型（整数/浮点/bool/string/char）
- 出处：`/compiler/frontend/scheck.tie`

### E30099  case 类型匹配（?）仅支持 any 动态类型，当前 switch 对象是
- 消息：`case 类型匹配（ <...> ）仅支持 any 动态类型，当前 switch 对象是 `；消息名：case 类型匹配（?）仅支持 any 动态类型，当前 switch 对象是
- 出处：`/compiler/frontend/scheck.tie`

### E30100  struct 继承形成环（含 '?'）
- 消息：`struct 继承形成环（含 ' <...> '）`；消息名：struct 继承形成环（含 '?'）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30101  impl '? for ?' 缺少方法 '?'（port 方法必须全部实现）
- 消息：`impl ' <...>  for  <...> ' 缺少方法 ' <...> '（port 方法必须全部实现）`；消息名：impl '? for ?' 缺少方法 '?'（port 方法必须全部实现）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30102  guard<cap> 能力域必须是 share/mem/ext，实际是 '?'
- 消息：`guard<cap> 能力域必须是 share/mem/ext，实际是 ' <...> '`；消息名：guard<cap> 能力域必须是 share/mem/ext，实际是 '?'
- 出处：`/compiler/frontend/sgen.tie`

### E30103  '?' 解包只能用于返回 Result/Option 的函数内（当前函数无返回类型）
- 消息：`'?' 解包只能用于返回 Result/Option 的函数内（当前函数无返回类型）`；消息名：'?' 解包只能用于返回 Result/Option 的函数内（当前函数无返回类型）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30104  '?' 解包只能用于返回 Result/Option 的函数内，当前函数返回
- 消息：`'?' 解包只能用于返回 Result/Option 的函数内，当前函数返回 `；消息名：'?' 解包只能用于返回 Result/Option 的函数内，当前函数返回
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30105  '?' 解包的操作数必须是 Result/Option 枚举，实际是
- 消息：`'?' 解包的操作数必须是 Result/Option 枚举，实际是 `；消息名：'?' 解包的操作数必须是 Result/Option 枚举，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30106  '?' 解包要求枚举 '?' 具有 Ok/Some 与 Err/None 变体（Result/Option 形态）
- 消息：`'?' 解包要求枚举 ' <...> ' 具有 Ok/Some 与 Err/None 变体（Result/Option 形态）`；消息名：'?' 解包要求枚举 '?' 具有 Ok/Some 与 Err/None 变体（Result/Option 形态）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30107  '?' 解包错误类型不匹配
- 消息：`'?' 解包错误类型不匹配：函数返回  <...> ，操作数是 `；消息名：'?' 解包错误类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30108  case 解构要求变体 '?' 恰有 1 个 payload 字段，实际 ? 个
- 消息：`case 解构要求变体 ' <...> ' 恰有 1 个 payload 字段，实际  <...>  个`；消息名：case 解构要求变体 '?' 恰有 1 个 payload 字段，实际 ? 个
- 出处：`/compiler/frontend/scheck.tie`

### E30109  for 迭代对象仅支持范围（0..10）或表变量，实际是
- 消息：`for 迭代对象仅支持范围（0..10）或表变量，实际是 `；消息名：for 迭代对象仅支持范围（0..10）或表变量，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30110  struct '?' 重复定义
- 消息：`struct ' <...> ' 重复定义`；消息名：struct '?' 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30111  port 默认实现暂不支持（第一版
- 消息：`port 默认实现暂不支持（第一版：port 方法只声明签名，请用 impl 块提供实现）`；消息名：port 默认实现暂不支持（第一版
- 出处：`/compiler/frontend/scollect_port.tie`

### E30112  struct '?'（含继承链）没有方法 '?'
- 消息：`struct ' <...> '（含继承链）没有方法 ' <...> '`；消息名：struct '?'（含继承链）没有方法 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30113  三目两分支类型不一致
- 消息：`三目两分支类型不一致： <...>  与 `；消息名：三目两分支类型不一致
- 出处：`/compiler/frontend/sinfer.tie`

### E30114  三目条件必须是 bool
- 消息：`三目条件必须是 bool`；消息名：三目条件必须是 bool
- 出处：`/compiler/frontend/sinfer.tie`

### E30115  下标必须是整数，实际是
- 消息：`下标必须是整数，实际是 `；消息名：下标必须是整数，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30116  下标访问的对象必须是表或字符串，实际是
- 消息：`下标访问的对象必须是表或字符串，实际是 `；消息名：下标访问的对象必须是表或字符串，实际是
- 出处：`/compiler/frontend/sinfer.tie`

### E30117  下标赋值的对象必须是表，实际是
- 消息：`下标赋值的对象必须是表，实际是 `；消息名：下标赋值的对象必须是表，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30118  下标赋值的目标必须是表元素访问（t[i]）
- 消息：`下标赋值的目标必须是表元素访问（t[i]）`；消息名：下标赋值的目标必须是表元素访问（t[i]）
- 出处：`/compiler/frontend/scheck.tie`

### E30119  不能对 const 变量 '?' 自增/自减
- 消息：`不能对 const 变量 ' <...> ' 自增/自减`；消息名：不能对 const 变量 '?' 自增/自减
- 出处：`/compiler/frontend/sinfer.tie`

### E30120  不能给 const 变量 '?' 赋值
- 消息：`不能给 const 变量 ' <...> ' 赋值`；消息名：不能给 const 变量 '?' 赋值
- 出处：`/compiler/frontend/scheck.tie`

### E30121  二元运算两侧类型不一致
- 消息：`二元运算两侧类型不一致： <...>  与 `；消息名：二元运算两侧类型不一致
- 出处：`/compiler/frontend/sinfer.tie`

### E30122  位运算只支持整数，不能用于
- 消息：`位运算只支持整数，不能用于 `；消息名：位运算只支持整数，不能用于
- 出处：`/compiler/frontend/sinfer.tie`

### E30123  元组字段名 '?' 重复
- 消息：`元组字段名 ' <...> ' 重复`；消息名：元组字段名 '?' 重复
- 出处：`/compiler/frontend/sinfer.tie`

### E30124  元组没有字段 '?'
- 消息：`元组没有字段 ' <...> '`；消息名：元组没有字段 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30125  全局 port 对象变量暂不支持（第一版请用局部变量提升
- 消息：`全局 port 对象变量暂不支持（第一版请用局部变量提升：unsafe { var d:  <...>  = 具体实例 }）`；消息名：全局 port 对象变量暂不支持（第一版请用局部变量提升
- 出处：`/compiler/frontend/scollect_port.tie`

### E30126  全局变量 '?' 与函数名冲突
- 消息：`全局变量 ' <...> ' 与函数名冲突`；消息名：全局变量 '?' 与函数名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30127  全局变量 '?' 初始化类型不匹配
- 消息：`全局变量 ' <...> ' 初始化类型不匹配：期望  <...> ，实际 `；消息名：全局变量 '?' 初始化类型不匹配
- 出处：`/compiler/frontend/scollect_port.tie`

### E30128  全局变量 '?' 必须显式标注类型（如 var x: i64）
- 消息：`全局变量 ' <...> ' 必须显式标注类型（如 var x: i64）`；消息名：全局变量 '?' 必须显式标注类型（如 var x: i64）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30129  全局变量 '?' 重复定义
- 消息：`全局变量 ' <...> ' 重复定义`；消息名：全局变量 '?' 重复定义
- 出处：`/compiler/frontend/scollect_port.tie`

### E30130  全局表 '?' 的初始化必须是空表 []（元素类型由标注决定）
- 消息：`全局表 ' <...> ' 的初始化必须是空表 []（元素类型由标注决定）`；消息名：全局表 '?' 的初始化必须是空表 []（元素类型由标注决定）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30131  内存序必须是 Relaxed / Acquire / Release / AcqRel / SeqCst（标识符常量）
- 消息：`内存序必须是 Relaxed / Acquire / Release / AcqRel / SeqCst（标识符常量）`；消息名：内存序必须是 Relaxed / Acquire / Release / AcqRel / SeqCst（标识符常量）
- 出处：`/compiler/frontend/sinfer.tie`

### E30132  函数 '?' 在命名空间 '?' 中重复定义
- 消息：`函数 ' <...> ' 在命名空间 ' <...> ' 中重复定义`；消息名：函数 '?' 在命名空间 '?' 中重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30133  函数 '?' 实参过多（泛型推断）
- 消息：`函数 ' <...> ' 实参过多（泛型推断）`；消息名：函数 '?' 实参过多（泛型推断）
- 出处：`/compiler/frontend/sgen.tie`

### E30134  函数 '?' 是命名空间 '?' 的私有函数（默认私有，`pub func` 显式导出），不可在命名空间之外调用
- 消息：`函数 ' <...> ' 是命名空间 ' <...> ' 的私有函数（默认私有，`pub func` 显式导出），不可在命名空间之外调用`；消息名：函数 '?' 是命名空间 '?' 的私有函数（默认私有，`pub func` 显式导出），不可在命名空间之外调用
- 出处：`/compiler/frontend/sstate.tie`

### E30135  函数 '?'
- 消息：`函数 ' <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：函数 '?'
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30136  函数 '?' 重复定义
- 消息：`函数 ' <...> ' 重复定义`；消息名：函数 '?' 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30137  函数值调用 '?' 参数类型不匹配
- 消息：`函数值调用 ' <...> ' 参数类型不匹配：期望  <...> ，实际 `；消息名：函数值调用 '?' 参数类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30138  函数值调用 '?'
- 消息：`函数值调用 ' <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：函数值调用 '?'
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30139  函数值调用 '?' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）
- 消息：`函数值调用 ' <...> ' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）`；消息名：函数值调用 '?' 的 ref 参数需要可寻址的表变量实参（字面量/下标/调用结果不可取地址）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30140  函数值调用 '?' 的 ref 参数需要表变量实参（实际 ?）
- 消息：`函数值调用 ' <...> ' 的 ref 参数需要表变量实参（实际  <...> ）`；消息名：函数值调用 '?' 的 ref 参数需要表变量实参（实际 ?）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30141  原子操作 '?()' 必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）
- 消息：`原子操作 ' <...> ()' 必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）`；消息名：原子操作 '?()' 必须在 unsafe 块或 unsafe 函数中使用（安全代码禁止触底）
- 出处：`/compiler/frontend/sinfer.tie`

### E30142  参数 '?' 的 ref 修饰仅支持表参数（table/table<T>），实际是
- 消息：`参数 ' <...> ' 的 ref 修饰仅支持表参数（table/table<T>），实际是 `；消息名：参数 '?' 的 ref 修饰仅支持表参数（table/table<T>），实际是
- 出处：`/compiler/frontend/scollect.tie`

### E30143  参数 '?' 的 ref 参数不能有默认值（必须在调用点传实参）
- 消息：`参数 ' <...> ' 的 ref 参数不能有默认值（必须在调用点传实参）`；消息名：参数 '?' 的 ref 参数不能有默认值（必须在调用点传实参）
- 出处：`/compiler/frontend/scollect.tie`

### E30144  参数 '?' 的指针/切片/原子类型 '?' 只能在 unsafe 函数中使用
- 消息：`参数 ' <...> ' 的指针/切片/原子类型 ' <...> ' 只能在 unsafe 函数中使用`；消息名：参数 '?' 的指针/切片/原子类型 '?' 只能在 unsafe 函数中使用
- 出处：`/compiler/frontend/scollect.tie`

### E30145  参数 '?' 的默认值必须是字面量（数/布尔/字符/字符串或空表 []）
- 消息：`参数 ' <...> ' 的默认值必须是字面量（数/布尔/字符/字符串或空表 []）`；消息名：参数 '?' 的默认值必须是字面量（数/布尔/字符/字符串或空表 []）
- 出处：`/compiler/frontend/scollect.tie`

### E30146  参数 '?' 缺少默认值
- 消息：`参数 ' <...> ' 缺少默认值：可选参数（带默认值）必须连续排在必选参数之后`；消息名：参数 '?' 缺少默认值
- 出处：`/compiler/frontend/scollect.tie`

### E30147  参数 '?' 默认值类型不匹配
- 消息：`参数 ' <...> ' 默认值类型不匹配：期望  <...> ，实际 `；消息名：参数 '?' 默认值类型不匹配
- 出处：`/compiler/frontend/scollect.tie`

### E30148  取模运算只支持整数
- 消息：`取模运算只支持整数`；消息名：取模运算只支持整数
- 出处：`/compiler/frontend/sinfer.tie`

### E30149  取负运算的操作数必须是数字
- 消息：`取负运算的操作数必须是数字`；消息名：取负运算的操作数必须是数字
- 出处：`/compiler/frontend/sinfer.tie`

### E30150  变体 '?' 的 payload 暂不支持类型 '?'
- 消息：`变体 ' <...> ' 的 payload 暂不支持类型 ' <...> '`；消息名：变体 '?' 的 payload 暂不支持类型 '?'
- 出处：`/compiler/frontend/scollect_port.tie`

### E30151  变体 '?' 重复定义
- 消息：`变体 ' <...> ' 重复定义`；消息名：变体 '?' 重复定义
- 出处：`/compiler/frontend/scollect_port.tie`

### E30152  变体 '?.?' 需要 payload 参数（不能裸引用，请用 ?.?(...) 构造）
- 消息：`变体 ' <...> . <...> ' 需要 payload 参数（不能裸引用，请用  <...> . <...> (...) 构造）`；消息名：变体 '?.?' 需要 payload 参数（不能裸引用，请用 ?.?(...) 构造）
- 出处：`/compiler/frontend/sinfer.tie`

### E30153  变参参数 '?' 不能同时使用 ref 修饰
- 消息：`变参参数 ' <...> ' 不能同时使用 ref 修饰`；消息名：变参参数 '?' 不能同时使用 ref 修饰
- 出处：`/compiler/frontend/scollect.tie`

### E30154  变参参数 '?' 不能有默认值
- 消息：`变参参数 ' <...> ' 不能有默认值`；消息名：变参参数 '?' 不能有默认值
- 出处：`/compiler/frontend/scollect.tie`

### E30155  变参参数 '?' 元素类型必须是标量（i8..u64/f32/f64/bool/char/string），实际是
- 消息：`变参参数 ' <...> ' 元素类型必须是标量（i8..u64/f32/f64/bool/char/string），实际是 `；消息名：变参参数 '?' 元素类型必须是标量（i8..u64/f32/f64/bool/char/string），实际是
- 出处：`/compiler/frontend/scollect.tie`

### E30156  变参参数 '?' 必须是最后一个参数
- 消息：`变参参数 ' <...> ' 必须是最后一个参数`；消息名：变参参数 '?' 必须是最后一个参数
- 出处：`/compiler/frontend/scollect.tie`

### E30157  变量 '?' 必须标注类型或初始化
- 消息：`变量 ' <...> ' 必须标注类型或初始化`；消息名：变量 '?' 必须标注类型或初始化
- 出处：`/compiler/frontend/scheck.tie`

### E30158  变量 '?' 的指针/切片/原子类型 '?' 只能在 unsafe 代码中使用
- 消息：`变量 ' <...> ' 的指针/切片/原子类型 ' <...> ' 只能在 unsafe 代码中使用`；消息名：变量 '?' 的指针/切片/原子类型 '?' 只能在 unsafe 代码中使用
- 出处：`/compiler/frontend/scheck.tie`

### E30159  变量 '?' 类型不匹配
- 消息：`变量 ' <...> ' 类型不匹配：标注  <...> ，表达式推导为 `；消息名：变量 '?' 类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30160  变量节点缺少名字
- 消息：`变量节点缺少名字`；消息名：变量节点缺少名字
- 出处：`/compiler/frontend/mexpand.tie`

### E30161  命名空间函数 '?'
- 消息：`命名空间函数 ' <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：命名空间函数 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30162  命名空间函数 '?' 未定义
- 消息：`命名空间函数 ' <...> ' 未定义`；消息名：命名空间函数 '?' 未定义
- 出处：`/compiler/frontend/sinfer.tie`

### E30163  命名空间路径 '?' 不能作为值使用（只能用于调用，如 'x::f()'）
- 消息：`命名空间路径 ' <...> ' 不能作为值使用（只能用于调用，如 'x::f()'）`；消息名：命名空间路径 '?' 不能作为值使用（只能用于调用，如 'x::f()'）
- 出处：`/compiler/frontend/sinfer.tie`

### E30164  复合赋值位运算只支持整数，目标类型是
- 消息：`复合赋值位运算只支持整数，目标类型是 `；消息名：复合赋值位运算只支持整数，目标类型是
- 出处：`/compiler/frontend/scheck.tie`

### E30165  复合赋值取模只支持整数，目标类型是
- 消息：`复合赋值取模只支持整数，目标类型是 `；消息名：复合赋值取模只支持整数，目标类型是
- 出处：`/compiler/frontend/scheck.tie`

### E30166  复合赋值类型不匹配
- 消息：`复合赋值类型不匹配：目标类型  <...>  与表达式 `；消息名：复合赋值类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30167  复合赋值运算符不能用于
- 消息：`复合赋值运算符不能用于 `；消息名：复合赋值运算符不能用于
- 出处：`/compiler/frontend/scheck.tie`

### E30168  字段 '?.?' 与继承链中的字段重名（字段名必须跨继承链唯一）
- 消息：`字段 ' <...> . <...> ' 与继承链中的字段重名（字段名必须跨继承链唯一）`；消息名：字段 '?.?' 与继承链中的字段重名（字段名必须跨继承链唯一）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30169  字段访问 '.' 的对象必须是元组或类实例，实际是
- 消息：`字段访问 '.' 的对象必须是元组或类实例，实际是 `；消息名：字段访问 '.' 的对象必须是元组或类实例，实际是
- 出处：`/compiler/frontend/sinfer.tie`

### E30170  字段赋值的对象必须是 struct 实例，实际是
- 消息：`字段赋值的对象必须是 struct 实例，实际是 `；消息名：字段赋值的对象必须是 struct 实例，实际是
- 出处：`/compiler/frontend/scheck.tie`

### E30171  字段赋值类型不匹配
- 消息：`字段赋值类型不匹配：期望  <...> ，实际 `；消息名：字段赋值类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30172  字符串字面量缺少文本
- 消息：`字符串字面量缺少文本`；消息名：字符串字面量缺少文本
- 出处：`/compiler/frontend/mexpand.tie`

### E30173  字符串迭代器 s.chars() 不接受实参（实际 ? 个）
- 消息：`字符串迭代器 s.chars() 不接受实参（实际  <...>  个）`；消息名：字符串迭代器 s.chars() 不接受实参（实际 ? 个）
- 出处：`/compiler/frontend/sinfer.tie`

### E30174  字符字面量缺少文本
- 消息：`字符字面量缺少文本`；消息名：字符字面量缺少文本
- 出处：`/compiler/frontend/mexpand.tie`

### E30175  宏 '?' 展开失败:
- 消息：`宏 ' <...> ' 展开失败: `；消息名：宏 '?' 展开失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30176  宏 '?' 是私有宏，只能在定义文件内使用（pub macro 导出跨文件可见）
- 消息：`宏 ' <...> ' 是私有宏，只能在定义文件内使用（pub macro 导出跨文件可见）`；消息名：宏 '?' 是私有宏，只能在定义文件内使用（pub macro 导出跨文件可见）
- 出处：`/compiler/frontend/mexpand.tie`

### E30177  宏 '?' 注册失败:
- 消息：`宏 ' <...> ' 注册失败: `；消息名：宏 '?' 注册失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30178  宏 '?' 的实参缺失
- 消息：`宏 ' <...> ' 的实参缺失`；消息名：宏 '?' 的实参缺失
- 出处：`/compiler/frontend/mexpand.tie`

### E30179  宏定义 '?' 只能出现在主文件中（跨文件宏暂不支持，S3.3 第一版限制）
- 消息：`宏定义 ' <...> ' 只能出现在主文件中（跨文件宏暂不支持，S3.3 第一版限制）`；消息名：宏定义 '?' 只能出现在主文件中（跨文件宏暂不支持，S3.3 第一版限制）
- 出处：`/compiler/frontend/scollect_port.tie`

### E30180  宏定义序列化失败:
- 消息：`宏定义序列化失败: `；消息名：宏定义序列化失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30181  宏定义缺少名字
- 消息：`宏定义缺少名字`；消息名：宏定义缺少名字
- 出处：`/compiler/frontend/mexpand.tie`

### E30182  宏实参序列化失败:
- 消息：`宏实参序列化失败: `；消息名：宏实参序列化失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30183  宏展开结果加载失败（AST 协议解析错误）
- 消息：`宏展开结果加载失败（AST 协议解析错误）`；消息名：宏展开结果加载失败（AST 协议解析错误）
- 出处：`/compiler/frontend/mexpand.tie`

### E30184  宏展开轮次超过 64 次上限（疑似展开结果无限产生宏调用）
- 消息：`宏展开轮次超过 64 次上限（疑似展开结果无限产生宏调用）`；消息名：宏展开轮次超过 64 次上限（疑似展开结果无限产生宏调用）
- 出处：`/compiler/frontend/mexpand.tie`

### E30185  宏展开返回语句块，但调用点在表达式位置（宏须返回表达式）
- 消息：`宏展开返回语句块，但调用点在表达式位置（宏须返回表达式）`；消息名：宏展开返回语句块，但调用点在表达式位置（宏须返回表达式）
- 出处：`/compiler/frontend/mexpand.tie`

### E30186  实例化 '?' 参数 '?' 的 ref 修饰仅支持表参数，实际是
- 消息：`实例化 ' <...> ' 参数 ' <...> ' 的 ref 修饰仅支持表参数，实际是 `；消息名：实例化 '?' 参数 '?' 的 ref 修饰仅支持表参数，实际是
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30187  实例化 '?' 参数 '?' 类型解析失败
- 消息：`实例化 ' <...> ' 参数 ' <...> ' 类型解析失败`；消息名：实例化 '?' 参数 '?' 类型解析失败
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30188  实例化 '?' 参数 '?' 缺少默认值
- 消息：`实例化 ' <...> ' 参数 ' <...> ' 缺少默认值：可选参数（带默认值）必须连续排在必选参数之后`；消息名：实例化 '?' 参数 '?' 缺少默认值
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30189  实例化 '?' 字段 '?' 类型解析失败
- 消息：`实例化 ' <...> ' 字段 ' <...> ' 类型解析失败`；消息名：实例化 '?' 字段 '?' 类型解析失败
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30190  实例化 '?' 返回类型解析失败
- 消息：`实例化 ' <...> ' 返回类型解析失败`；消息名：实例化 '?' 返回类型解析失败
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30191  导入文件 '?' 解析失败:
- 消息：`导入文件 ' <...> ' 解析失败: `；消息名：导入文件 '?' 解析失败:
- 出处：`/compiler/frontend/semantic.tie`

### E30192  提升 '?' 到 port '?' 必须在 unsafe 块或 unsafe 函数中（接口对象借用具体对象，指针操作归 unsafe）
- 消息：`提升 ' <...> ' 到 port ' <...> ' 必须在 unsafe 块或 unsafe 函数中（接口对象借用具体对象，指针操作归 unsafe）`；消息名：提升 '?' 到 port '?' 必须在 unsafe 块或 unsafe 函数中（接口对象借用具体对象，指针操作归 unsafe）
- 出处：`/compiler/frontend/scheck.tie`

### E30193  方法 '?' 参数类型不匹配
- 消息：`方法 ' <...> ' 参数类型不匹配：期望  <...> ，实际 `；消息名：方法 '?' 参数类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30194  方法 '?'
- 消息：`方法 ' <...> ' 期望  <...>  个参数（含接收者对象），实际  <...>  个`；消息名：方法 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30195  方法 '?'
- 消息：`方法 ' <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：方法 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30196  方法 '?' 首参类型不匹配
- 消息：`方法 ' <...> ' 首参类型不匹配：期望  <...> ，实际 `；消息名：方法 '?' 首参类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30197  方法调用的对象必须是 struct 实例或 struct 名，实际是
- 消息：`方法调用的对象必须是 struct 实例或 struct 名，实际是 `；消息名：方法调用的对象必须是 struct 实例或 struct 名，实际是
- 出处：`/compiler/frontend/sinfer.tie`

### E30198  无 payload 变体 '?.?' 不接受参数，实际 ? 个
- 消息：`无 payload 变体 ' <...> . <...> ' 不接受参数，实际  <...>  个`；消息名：无 payload 变体 '?.?' 不接受参数，实际 ? 个
- 出处：`/compiler/frontend/sinfer.tie`

### E30199  无法推断类型参数 ?（调用点无足够信息，请显式指定类型实参，如 max<i64>(...)）
- 消息：`无法推断类型参数  <...> （调用点无足够信息，请显式指定类型实参，如 max<i64>(...)）`；消息名：无法推断类型参数 ?（调用点无足够信息，请显式指定类型实参，如 max<i64>(...)）
- 出处：`/compiler/frontend/sgen.tie`

### E30200  无法推断表达式（节点 ?）
- 消息：`无法推断表达式（节点  <...> ）`；消息名：无法推断表达式（节点 ?）
- 出处：`/compiler/frontend/sinfer.tie`

### E30201  无法读取导入文件 '?'
- 消息：`无法读取导入文件 ' <...> '`；消息名：无法读取导入文件 '?'
- 出处：`/compiler/frontend/semantic.tie`

### E30202  无法读取导入文件 '?'（文件不存在）
- 消息：`无法读取导入文件 ' <...> '（文件不存在）`；消息名：无法读取导入文件 '?'（文件不存在）
- 出处：`/compiler/frontend/semantic.tie`

### E30203  期望类型，实际是未知节点
- 消息：`期望类型，实际是未知节点`；消息名：期望类型，实际是未知节点
- 出处：`/compiler/frontend/stype.tie`

### E30204  未声明的变量 '?'
- 消息：`未声明的变量 ' <...> '`；消息名：未声明的变量 '?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30205  未定义的函数 '?'
- 消息：`未定义的函数 ' <...> '`；消息名：未定义的函数 '?'
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30206  未知内存序 '?'（合法: Relaxed/Acquire/Release/AcqRel/SeqCst）
- 消息：`未知内存序 ' <...> '（合法: Relaxed/Acquire/Release/AcqRel/SeqCst）`；消息名：未知内存序 '?'（合法: Relaxed/Acquire/Release/AcqRel/SeqCst）
- 出处：`/compiler/frontend/sinfer.tie`

### E30207  构造 '?' 参数类型不匹配：字段 '?'
- 消息：`构造 ' <...> ' 参数类型不匹配：字段 ' <...> ' 期望  <...> ，实际 `；消息名：构造 '?' 参数类型不匹配：字段 '?'
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30208  构造 '?.?' 参数类型不匹配
- 消息：`构造 ' <...> . <...> ' 参数类型不匹配：期望  <...> ，实际 `；消息名：构造 '?.?' 参数类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30209  构造 '?.?' 参数过多（payload 字段数 ?）
- 消息：`构造 ' <...> . <...> ' 参数过多（payload 字段数  <...> ）`；消息名：构造 '?.?' 参数过多（payload 字段数 ?）
- 出处：`/compiler/frontend/sgen.tie`

### E30210  构造 '?' 最多 ? 个参数（字段数），实际 ? 个
- 消息：`构造 ' <...> ' 最多  <...>  个参数（字段数），实际  <...>  个`；消息名：构造 '?' 最多 ? 个参数（字段数），实际 ? 个
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30211  构造 '?.?'
- 消息：`构造 ' <...> . <...> ' 期望  <...>  个参数，实际  <...>  个`；消息名：构造 '?.?'
- 出处：`/compiler/frontend/sinfer.tie`

### E30212  枚举 '?' 不接受类型参数（非泛型 enum）
- 消息：`枚举 ' <...> ' 不接受类型参数（非泛型 enum）`；消息名：枚举 '?' 不接受类型参数（非泛型 enum）
- 出处：`/compiler/frontend/sgen.tie`

### E30213  枚举 '?' 没有变体 '?'
- 消息：`枚举 ' <...> ' 没有变体 ' <...> '`；消息名：枚举 '?' 没有变体 '?'
- 出处：`/compiler/frontend/scheck.tie`

### E30214  枚举 '?' 重复定义
- 消息：`枚举 ' <...> ' 重复定义`；消息名：枚举 '?' 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30215  枚举名 '?' 与 struct 名冲突
- 消息：`枚举名 ' <...> ' 与 struct 名冲突`；消息名：枚举名 '?' 与 struct 名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30216  枚举名 '?' 与函数名冲突
- 消息：`枚举名 ' <...> ' 与函数名冲突`；消息名：枚举名 '?' 与函数名冲突
- 出处：`/compiler/frontend/scollect_port.tie`

### E30217  枚举暂不支持 == 比较
- 消息：`枚举暂不支持 == 比较`；消息名：枚举暂不支持 == 比较
- 出处：`/compiler/frontend/sinfer.tie`

### E30218  比较运算符不能用于
- 消息：`比较运算符不能用于 `；消息名：比较运算符不能用于
- 出处：`/compiler/frontend/sinfer.tie`

### E30219  泛型 struct '?' 必须显式指定类型参数（如 ?<i64>）
- 消息：`泛型 struct ' <...> ' 必须显式指定类型参数（如  <...> <i64>）`；消息名：泛型 struct '?' 必须显式指定类型参数（如 ?<i64>）
- 出处：`/compiler/frontend/sgen.tie`

### E30220  泛型 struct '?' 需要 ? 个类型参数，实际 ? 个
- 消息：`泛型 struct ' <...> ' 需要  <...>  个类型参数，实际  <...>  个`；消息名：泛型 struct '?' 需要 ? 个类型参数，实际 ? 个
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30221  泛型实例化深度超限（超过 64 层），疑似无限递归实例化
- 消息：`泛型实例化深度超限（超过 64 层），疑似无限递归实例化：' <...> '`；消息名：泛型实例化深度超限（超过 64 层），疑似无限递归实例化
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30222  泛型实例化规模超限（超过 2000 个实例化函数），疑似无限递归实例化
- 消息：`泛型实例化规模超限（超过 2000 个实例化函数），疑似无限递归实例化`；消息名：泛型实例化规模超限（超过 2000 个实例化函数），疑似无限递归实例化
- 出处：`/compiler/frontend/semantic_gen.tie`

### E30223  泛型枚举 '?' 的无 payload 变体 '?' 无法推断类型参数（一期请用带 payload 变体构造或显式类型标注，如 '?<i64>.?' 后续支持）
- 消息：`泛型枚举 ' <...> ' 的无 payload 变体 ' <...> ' 无法推断类型参数（一期请用带 payload 变体构造或显式类型标注，如 ' <...> <i64>. <...> ' 后续支持）`；消息名：泛型枚举 '?' 的无 payload 变体 '?' 无法推断类型参数（一期请用带 payload 变体构造或显式类型标注，如 '?<i64>.?' 后续支持）
- 出处：`/compiler/frontend/sinfer.tie`

### E30224  泛型枚举变体 '?.?' 无法推断类型参数（裸引用无实参，请用带 payload 的构造调用，如 ?.Some(...)）
- 消息：`泛型枚举变体 ' <...> . <...> ' 无法推断类型参数（裸引用无实参，请用带 payload 的构造调用，如  <...> .Some(...)）`；消息名：泛型枚举变体 '?.?' 无法推断类型参数（裸引用无实参，请用带 payload 的构造调用，如 ?.Some(...)）
- 出处：`/compiler/frontend/sinfer.tie`

### E30225  泛型模板 '?' 重复定义
- 消息：`泛型模板 ' <...> ' 重复定义`；消息名：泛型模板 '?' 重复定义
- 出处：`/compiler/frontend/sstate.tie`

### E30226  泛型模板类型参数 '?' 缺少实参
- 消息：`泛型模板类型参数 ' <...> ' 缺少实参`；消息名：泛型模板类型参数 '?' 缺少实参
- 出处：`/compiler/frontend/sgen.tie`

### E30227  泛型约束引用的 port '?' 未定义
- 消息：`泛型约束引用的 port ' <...> ' 未定义`；消息名：泛型约束引用的 port '?' 未定义
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30228  泛型约束必须是 port 类型（如 <T: Drawable>），实际是其他类型表达式
- 消息：`泛型约束必须是 port 类型（如 <T: Drawable>），实际是其他类型表达式`；消息名：泛型约束必须是 port 类型（如 <T: Drawable>），实际是其他类型表达式
- 出处：`/compiler/frontend/sstate.tie`

### E30229  浮点字面量缺少文本
- 消息：`浮点字面量缺少文本`；消息名：浮点字面量缺少文本
- 出处：`/compiler/frontend/mexpand.tie`

### E30230  空元组 () 不支持
- 消息：`空元组 () 不支持`；消息名：空元组 () 不支持
- 出处：`/compiler/frontend/sinfer.tie`

### E30231  算术运算符不能用于
- 消息：`算术运算符不能用于 `；消息名：算术运算符不能用于
- 出处：`/compiler/frontend/sinfer.tie`

### E30232  箭头传参实参类型不匹配
- 消息：`箭头传参实参类型不匹配：期望  <...> ，实际 `；消息名：箭头传参实参类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30233  箭头传参要求目标函数恰 1 个参数，实际 ? 个（?）
- 消息：`箭头传参要求目标函数恰 1 个参数，实际  <...>  个（ <...> ）`；消息名：箭头传参要求目标函数恰 1 个参数，实际 ? 个（?）
- 出处：`/compiler/frontend/sinfer.tie`

### E30234  箭头目标必须是函数、调用或可赋值变量（函数 ?）
- 消息：`箭头目标必须是函数、调用或可赋值变量（函数  <...> ）`；消息名：箭头目标必须是函数、调用或可赋值变量（函数 ?）
- 出处：`/compiler/frontend/sinfer.tie`

### E30235  箭头赋值类型不匹配
- 消息：`箭头赋值类型不匹配： <...>  与 `；消息名：箭头赋值类型不匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30236  类 '?' 没有字段 '?'
- 消息：`类 ' <...> ' 没有字段 ' <...> '`；消息名：类 '?' 没有字段 '?'
- 出处：`/compiler/frontend/scheck.tie`

### E30237  类型 '?' 必须显式指定元素类型（如 ?<i64>）
- 消息：`类型 ' <...> ' 必须显式指定元素类型（如  <...> <i64>）`；消息名：类型 '?' 必须显式指定元素类型（如 ?<i64>）
- 出处：`/compiler/frontend/sgen.tie`

### E30238  类型 '?' 未定义
- 消息：`类型 ' <...> ' 未定义`；消息名：类型 '?' 未定义
- 出处：`/compiler/frontend/sgen.tie`

### E30239  类型 '?' 未实现 port '?'（泛型约束不满足）
- 消息：`类型 ' <...> ' 未实现 port ' <...> '（泛型约束不满足）`；消息名：类型 '?' 未实现 port '?'（泛型约束不满足）
- 出处：`/compiler/frontend/sgen_inst.tie`

### E30240  类型 '?' 未实现 port '?'，不能提升（请先写 impl ? for ?）
- 消息：`类型 ' <...> ' 未实现 port ' <...> '，不能提升（请先写 impl  <...>  for  <...> ）`；消息名：类型 '?' 未实现 port '?'，不能提升（请先写 impl ? for ?）
- 出处：`/compiler/frontend/scheck.tie`

### E30241  类型 '?' 缺少元素类型实参
- 消息：`类型 ' <...> ' 缺少元素类型实参`；消息名：类型 '?' 缺少元素类型实参
- 出处：`/compiler/frontend/sgen.tie`

### E30242  类型参数 ? 推断冲突: ? vs
- 消息：`类型参数  <...>  推断冲突:  <...>  vs `；消息名：类型参数 ? 推断冲突: ? vs
- 出处：`/compiler/frontend/sgen.tie`

### E30243  类型字面量只能用作 switch 的 case 类型匹配
- 消息：`类型字面量只能用作 switch 的 case 类型匹配`；消息名：类型字面量只能用作 switch 的 case 类型匹配
- 出处：`/compiler/frontend/sinfer.tie`

### E30244  类型实参不能是元组类型（泛型系统首轮不支持 tuple 实参）
- 消息：`类型实参不能是元组类型（泛型系统首轮不支持 tuple 实参）`；消息名：类型实参不能是元组类型（泛型系统首轮不支持 tuple 实参）
- 出处：`/compiler/frontend/sgen.tie`

### E30245  类型实参过多
- 消息：`类型实参过多：enum 模板需要  <...>  个类型参数，实际  <...>  个`；消息名：类型实参过多
- 出处：`/compiler/frontend/sgen.tie`

### E30246  类型实参过多
- 消息：`类型实参过多：模板需要  <...>  个类型参数，实际  <...>  个`；消息名：类型实参过多
- 出处：`/compiler/frontend/sgen.tie`

### E30247  自增/自减的操作数必须是可写数字变量
- 消息：`自增/自减的操作数必须是可写数字变量`；消息名：自增/自减的操作数必须是可写数字变量
- 出处：`/compiler/frontend/sinfer.tie`

### E30248  范围两端必须是整数
- 消息：`范围两端必须是整数`；消息名：范围两端必须是整数
- 出处：`/compiler/frontend/sinfer.tie`

### E30249  语句只能出现在文件顶层
- 消息：`语句只能出现在文件顶层`；消息名：语句只能出现在文件顶层
- 出处：`/compiler/frontend/scheck.tie`

### E30250  调用 unsafe 内置 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 消息：`调用 unsafe 内置 ' <...> ' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）`；消息名：调用 unsafe 内置 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30251  调用 unsafe 函数 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 消息：`调用 unsafe 函数 ' <...> ' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）`；消息名：调用 unsafe 函数 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30252  调用 '?' 参数类型不匹配
- 消息：`调用 ' <...> ' 参数类型不匹配：期望  <...> ，实际 `；消息名：调用 '?' 参数类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30253  调用 unsafe 方法 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 消息：`调用 unsafe 方法 ' <...> ' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）`；消息名：调用 unsafe 方法 '?' 必须在 unsafe 块或 unsafe 函数中（安全代码禁止触底）
- 出处：`/compiler/frontend/sinfer.tie`

### E30254  调用 '?' 的 ref 参数实参 '?' 必须是动态表（table_new_* 创建），'?' 是定长表
- 消息：`调用 ' <...> ' 的 ref 参数实参 ' <...> ' 必须是动态表（table_new_* 创建），' <...> ' 是定长表`；消息名：调用 '?' 的 ref 参数实参 '?' 必须是动态表（table_new_* 创建），'?' 是定长表
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30255  调用 '?' 的 ref 参数需要可寻址的变量实参（不能是字面量/下标/调用结果等不可取地址）
- 消息：`调用 ' <...> ' 的 ref 参数需要可寻址的变量实参（不能是字面量/下标/调用结果等不可取地址）`；消息名：调用 '?' 的 ref 参数需要可寻址的变量实参（不能是字面量/下标/调用结果等不可取地址）
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30256  调用 '?' 表参数元素类型不匹配
- 消息：`调用 ' <...> ' 表参数元素类型不匹配：期望 table< <...> >，实际 table< <...> >`；消息名：调用 '?' 表参数元素类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30257  调用表达式
- 消息：`调用表达式期望  <...>  个参数，实际 `；消息名：调用表达式
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30258  调用表达式第 ? 个实参类型不匹配
- 消息：`调用表达式第  <...>  个实参类型不匹配：期望  <...> ，实际 `；消息名：调用表达式第 ? 个实参类型不匹配
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30259  调用表达式要求被调者为函数类型，实际是
- 消息：`调用表达式要求被调者为函数类型，实际是 `；消息名：调用表达式要求被调者为函数类型，实际是
- 出处：`/compiler/frontend/sinfer_ret.tie`

### E30260  赋值目标 '?' 未声明
- 消息：`赋值目标 ' <...> ' 未声明`；消息名：赋值目标 '?' 未声明
- 出处：`/compiler/frontend/scheck.tie`

### E30261  赋值类型不匹配
- 消息：`赋值类型不匹配：变量 ' <...> ' 类型为  <...> ，表达式为 `；消息名：赋值类型不匹配
- 出处：`/compiler/frontend/scheck.tie`

### E30262  过程宏 '?' 展开失败:
- 消息：`过程宏 ' <...> ' 展开失败: `；消息名：过程宏 '?' 展开失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30263  过程宏 '?' 的实参缺失
- 消息：`过程宏 ' <...> ' 的实参缺失`；消息名：过程宏 '?' 的实参缺失
- 出处：`/compiler/frontend/mexpand.tie`

### E30264  过程宏实参解引用不支持节点类型 tag
- 消息：`过程宏实参解引用不支持节点类型 tag `；消息名：过程宏实参解引用不支持节点类型 tag
- 出处：`/compiler/frontend/mexpand.tie`

### E30265  过程宏实参解引用失败:
- 消息：`过程宏实参解引用失败: `；消息名：过程宏实参解引用失败:
- 出处：`/compiler/frontend/mexpand.tie`

### E30266  返回指针/切片/原子类型 '?' 的函数必须标注 unsafe（`unsafe fn`）
- 消息：`返回指针/切片/原子类型 ' <...> ' 的函数必须标注 unsafe（`unsafe fn`）`；消息名：返回指针/切片/原子类型 '?' 的函数必须标注 unsafe（`unsafe fn`）
- 出处：`/compiler/frontend/scollect.tie`

### E30267  逻辑运算符两侧必须是 bool（或两侧同为 trit）
- 消息：`逻辑运算符两侧必须是 bool（或两侧同为 trit）`；消息名：逻辑运算符两侧必须是 bool（或两侧同为 trit）
- 出处：`/compiler/frontend/sinfer.tie`

### E30268  逻辑非的操作数必须是 bool
- 消息：`逻辑非的操作数必须是 bool`；消息名：逻辑非的操作数必须是 bool
- 出处：`/compiler/frontend/sinfer.tie`

### E30269  重复的 case 值
- 消息：`重复的 case 值 `；消息名：重复的 case 值
- 出处：`/compiler/frontend/scheck.tie`

### E30270  闭包参数 '?' 的 ref 修饰仅支持表参数（table/table<T>），实际是
- 消息：`闭包参数 ' <...> ' 的 ref 修饰仅支持表参数（table/table<T>），实际是 `；消息名：闭包参数 '?' 的 ref 修饰仅支持表参数（table/table<T>），实际是
- 出处：`/compiler/frontend/sinfer.tie`

### E30271  闭包变参参数必须是最后一个参数
- 消息：`闭包变参参数必须是最后一个参数`；消息名：闭包变参参数必须是最后一个参数
- 出处：`/compiler/frontend/sinfer.tie`
