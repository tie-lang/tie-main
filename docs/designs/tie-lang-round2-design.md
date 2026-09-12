# tie 语言功能与语法糖第二轮设计

*EN: tie Language Features & Sugar — Round 2 Design*

> 定位：p.8 档（语言第一轮：特性+糖集 21 项）已闭环后，第二轮语言层规划。
> 按四个梯队 + 候选池组织；全部能力纳入当前架构，仅区分落地顺序（ROAD p.9.10 逐子项立项）。
> 依据：三支柱（效率·性能·安全·通用）+ p.8 各子项实测遗留缺口（含批次 C 多行续行实测坑）。
>
> EN: Round 2 of language-layer planning after the p.8 tier (21 language sub-items) closed.
> Organized in four tiers plus a candidate pool; every capability is part of the current
> architecture — only the landing order differs (ROAD p.9.10, one sub-item per feature).

## 1. 分组总览 / Overview

| 梯队 | 方向 | 子项 |
|---|---|---|
| 一 | 半开能力补全（错误/模式） | match 表达式 · if-let · try 块 · defer |
| 二 | 表与值语义糖 | 映射/记录字面量 · 表不可变更新 · 切片/区间 · 剩余解构 |
| 三 | 安全与性能 | checked 运算 · inline 标注 · immut 只读形参 |
| 四 | 元编程与平台 | @注解 · #cfg 条件编译 · import 别名 · yield 生成器语法 |
| 补 | 生态缺口的第二轮补充 | 迭代器协议 · 函数类型一等公民 · 多行续行 · 数值字面量加强 · enum 关联方法 |
| 池 | 候选池（排后） | interface/trait 轻量化 · 表结构模式匹配 · 标签 break 'label |

EN: Tier 1 = half-open capability completion (match-as-expression, if-let, try block, defer);
Tier 2 = table/value-semantics sugar (record literal, immutable update, slicing, rest destructure);
Tier 3 = safety & performance (checked arithmetic, inline, immut params);
Tier 4 = metaprogramming & platforms (@annotations, #cfg, import aliases, yield generator syntax);
Extras = second-round gaps (iterator protocol, first-class function types, line continuation,
numeric literal upgrades, enum associated methods); Pool = deferred (lightweight traits,
table-pattern matching, labeled break).

## 2. 梯队一：半开能力补全 / Tier 1

- **match/switch 表达式**：模式匹配从语句位扩展到表达式位，`let v = when x { 1 => "a" _ => "b" }`；复用既穷尽检查（p.8.1.4），分支为表达式。缺臂/类型不一致沿用既有诊断。
- **if-let 解构条件**：`if let Some(x) = opt { }`（补 `else`），Option/Result 解包惯用法；与 `?.`/`?:` 互补。嵌套解构复用既有解构器。
- **try 错误聚合块**：`try { a? b? }` 块内首个 `Err` 早退返回函数（传播到调用方），块尾可取 result；与 `?` 同语义、纯糖，不引入异常。负例：块外捕获/跨函数传播禁止（保持无异常）。
- **defer 资源释放**：`defer { f.close() }` 作用域退出时逆序执行；tie 无 RAII/析构，此为句柄/文件/锁的安全关闭钥匙；限制：defer 块内只允许表达式语句与 return 之外的流控（编译期检查）。

EN: match becomes an expression reusing the exhaustive checker; if-let unwraps Option/Result
with else; try { } aggregates `?` early-returns without exceptions; defer runs LIFO cleanup
on scope exit (tie has no RAII/destructors — the resource-safety key).

## 3. 梯队二：表与值语义糖 / Tier 2

- **映射/记录字面量**：`{name: "x", age: 3}` 记录/映射字面量（真实缺口：p.8.2.5 推导式因此只做数组版）；关键设计点=花括号消歧（块/尾随闭包 vs 记录）——裁决：记录首元素必须为 `标识符:` 或 `string:` 或`字符串:` 前缀即记录，否则块；未定案的歧义在实现期补丁化处理。
- **表不可变更新**：`t2 = t1 with {k: v}` 值语义下新生表、共享未变部分（零拷贝共享）；多键 `with {a: 1, b: 2}`。
- **切片/区间糖**：`t[1..3]`/`t[..n]`/`t[n..]`/`t[..]`；区间端点开闭（含/不含）明确；字符串切片同语法；表返回拷贝还是视图待实现期按性能裁决（拷贝默认）。
- **剩余解构**：`var (a, ...rest) = t` rest 收集剩余元素为表；与元组解构、变长泛型（p.8.1.3）表述一致；也可用于实参 `f(xs...)` 反向（p.8.2.10 已覆盖调用侧）。

EN: record literal `{k: v}` (brace disambiguation: leading ident/string+colon = record);
immutable update `t with {k:v}` shares unchanged parts; slicing `t[1..3]` etc.; rest
destructuring `var (a, ...rest) = t`.

## 4. 梯队三：安全与性能 / Tier 3

- **checked 运算**：`a +? b` 溢出即错误（诊断路径），普通 `+` 语义不变；策略可配置（全局档位配上已有告警体系 W00001/W00002）。
- **inline 标注**：`inline fn hot()` 内联提示（配合优化档位，p.9.1.2 资源可调联动）；跨模块 inline 走既有链接期规则。
- **immut 只读形参**：`fn f(immut t)` 形参只读约束，表值语义下降拷贝/防误写；与 const fn 语境区分（运行期只读 vs 编译期常量）。

EN: `a +? b` checked arithmetic (overflow = diagnostic, no behavior change to `+`);
`inline fn` hint for hot paths; `immut` read-only parameters.

## 5. 梯队四：元编程与平台 / Tier 4

- **@注解/属性**：`@component class X` 声明式注解；与 Keel 注册表（p.7.1.1）、tieapi、tdiag 诊断元数据咬合；注解体 = 表达式/表字面量，编译期求值。
- **#cfg 条件编译**：`#cfg(os=linux)` / `#cfg(debug)` / `#else`；基于头部/命令行目标求值（p.9.6 平台移植钥匙）；仅影响编译单元内文本/AST 裁剪，不产生运行期分支。
- **import 别名/重导出**：`import x as y`、`export` 重导出；库树收敛（p.7.1.6）后的模块体验补齐，纯解析层糖。
- **yield 生成器语法**：`func gen() { yield v }` 生成器式协程（产出+惰性流）；语言侧语法落地 tiec，运行时/调度落 trm-lite p.9.4.1（联动，互不阻塞）。

EN: `@ann` declarative annotations (tie into Keel registry / tieapi / tdiag); `#cfg`
compile-time text pruning for platform ports; `import x as y` + re-export (parse-level);
`yield v` generator syntax (language side in tiec, runtime/scheduling in trm-lite p.9.4.1).

## 6. 第二轮补充 / Extras

- **迭代器协议 + 惰性序列**：定义 `iterable` 协议（has_next/next 或列式切片视图）；`for x in iterable` 与推导式消费任意可迭代值；惰性链（map/filter 不物化）与 trm-lite 生成器（p.9.4）同源；性能导向（避免中间表）。
- **函数类型一等公民**：`fn(i64)->bool` 类型写法（参数/返回/变量/字段），与闭包 `func(){}`、尾随闭包配套；函数值引用语法统一（现有函数指针能力查证后衔接）。
- **多行表达式续行**：行尾 `\` 与流水线 `|` 续行（批次 C 实测「运算符开头续行」当前非法——补齐体验缺口）；lexer 规则与既有注释/字符串边界不冲突。
- **数值字面量加强**：`1_000_000` 分隔、`0b` 二进制（0x/0o 现状查证后补齐缺失格）；raw 字符串 `r"..."` 免转义（插值 p.8.2.3 之上）。
- **enum 关联方法**：enum 类型可定义方法（p.8.1.4 解构已就绪，方法位补全；与 struct 方法约定一致）。

EN: iterator protocol + lazy chains (consumer-agnostic for-in/comprehension, shared with
trm-lite generators); first-class function types `fn(i64)->bool`; line continuation `\`/`|`;
numeric separators `1_000_000` + `0b` + raw strings; enum associated methods.

## 7. 候选池（排后）/ Candidate Pool

- **interface/trait 轻量化**：`type Drawable { fn draw(); }` 静态接口 + 实现检查；鸭子多态的类型安全升级（tiu/t3d/tge 受益）；工程量大，独立档位。
- **表结构模式匹配**：`when t { [a, b] => }` 序列/记录形态匹配（数据导向）。
- **标签 break 'label**：深循环命名跳出（标签已有，break 命名化补全）。

EN: Pool (deferred): lightweight interfaces/traits, table-pattern matching, labeled break.

## 8. ROAD 映射 / ROAD Mapping

| ROAD | 项目 |
|---|---|
| p.9.10.1–4 | match 表达式 / if-let / try 块 / defer |
| p.9.10.5–8 | 记录字面量 / 表更新 / 切片 / 剩余解构 |
| p.9.10.9–11 | checked 运算 / inline / immut |
| p.9.10.12–15 | @注解 / #cfg / import 别名 / yield |
| p.9.10.16–20 | 迭代器协议 / 函数类型 / 续行 / 数值字面量 / enum 方法 |
| p.9.10.21 | interface/trait 轻量化（候选池排后） |

EN: every feature maps to one ROAD p.9.10.x sub-item; pool items still get numbered
sub-items but land later.