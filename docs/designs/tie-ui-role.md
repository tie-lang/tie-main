# tie UI 角色设计（设计 v1.0 / ROAD p.9.4）
*EN: tie UI role design (design v1.0 / ROAD p.9.4)*

**日期** / Date: 2026-09-26 · **状态** / Status: 设计定案（决策已对齐）
**依据** / Basis: `docs/language.md` §2.2（头类型已含 `ui` 角色）· §8（数据结构与逻辑分离）· §9（一等函数）· §12（宏）
**关联** / Related: `docs/designs/tie-primitive-op-design.md`（图语法，本设计**并入**其流向子集）· `docs/designs/tiu-ui-widgets.md`（本设计的**一个**消费方）· `docs/designs/tiu-drawing-api.md`

> EXEC BRIEF: Defines tie's **UI role** (`type tie<ui>`) as a renderer-neutral
> declaration layer, separated into three concerns mirroring HTML/CSS/JS —
> structure (`ui`) / style (style units) / logic (`logic`) — with three file
> roles splitting by change-rate: `ui` declares, `class` assembles, `logic`
> displays. Elements are marked with `@`, using tie's own `{ }` blocks so that
> `if` / `for` stay **native statements** (no second bracket system). Data flow
> reuses the planned graph operators (`{ }` node modules, `-` fork, `->` flow,
> `~` back edge). Styles are separate units with an explicit layer order —
> no specificity weights, no `!important`, no pseudo-elements. Layout belongs
> to structure; styles reference semantic tokens only. Every language-capability
> claim in §9 is **measured** on the shipping compiler, not assumed.

---

## 1. 三角色 × 三关注点 / Three roles × three concerns

界面开发按**关注点**切成三份（学 HTML / CSS / JS 的骨架·样式·逻辑分离），
再由**文件角色**承载。

| 关注点 | 对应 | 内容 | 文件角色 |
|---|---|---|---|
| **骨架** | HTML | 元素树、语义属性、插槽、动作契约 | `ui` |
| **样式** | CSS | 选择器规则、分层、状态、主题 token | 样式单元（块 + 文件） |
| **逻辑** | JS | 状态、事件处理、适配器绑定 | `logic` |

三角色**按变更频率**分工，各不越权：

| 角色 | 职责 | 不负责 |
|---|---|---|
| `ui` | 界面**是什么**：view / component / 样式引用 / 动作契约 | 状态 · 渲染调用 · 具体渲染器 · 平台 |
| `class` | **怎么拼**：组件库与设计系统；把界面组装成应用（路由 / 布局壳 / 共享状态桥） | 不定义页面结构 · 不渲染 |
| `logic` | **怎么显示**：状态、事件处理、适配器绑定、事件循环 | 不定义界面结构 · 不写渲染参数 |

```
   ui（骨架）            class（组装）           logic（逻辑）
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │ view/component│    │ 组件库/设计系统│    │ 状态/事件处理 │
 │ 样式引用      │───▶│ 应用组装      │───▶│ 适配器绑定    │
 └──────────────┘    └──────────────┘    └──────────────┘
        │                                        │
        └──────▶ UI IR（结构 + 未解析外观）◀───────┘
                          ▼
        tiu / Skia / 终端 / 测试快照（适配器）
```

`class` 双职责（组件库 + 应用组装）是本设计的选择：组件与页面同居一类文件边界内，
减少跨角色跳转；真正需要分开时，组件库可拆成独立 `class` 文件。

> EN: Three concerns (structure/style/logic, mirroring HTML/CSS/JS) carried by
> three file roles split by change-rate. `ui` declares, `class` assembles
> (component library + app assembly), `logic` displays.

---

## 2. 渲染器中立 / Renderer neutrality

`ui` 角色的编译产物是 **UI IR（界面描述数据）**，不是渲染调用。

* **铁律**：`ui` / 样式文件内**不得出现任何渲染器标识符**（无 Canvas、无骨架、无绘制记录、无窗口、无 GPU 概念）。编译期强制校验。
* **收益**：同一份界面描述可跑多后端（tiu 软件内核 / Skia / 终端）；界面可**无渲染器测试**（测试快照适配器直接断言 UI IR）；ui 不承担后端演进风险。
* 与 tiu 自身的「层间只走数据」是**同一条原则**，只是提升到文件角色层。
* **tiu 是适配器之一，不是 ui 角色的基础**。ui 文件不 import 任何 tiu 模块。

> EN: The `ui` role compiles to data (UI IR), never to render calls. No renderer
> identifier may appear in a `ui` file — enforced at compile time.

---

## 3. 语法 / Syntax

### 3.1 元素标记 `@` / Element marker

元素用 `@` 前缀标记：

```
@Column {
    @Text "tiu demo"
    @Row {
        @Button "-1" -> Dec
        @Button "+1" -> Inc
    }
}
```

**为什么是 `@`**（三者对比，见 §9 实测）：

| 方案 | 有符号标记元素 | 融合于 tie | 控制流原生 | 解析代价 |
|---|---|---|---|---|
| 无符号 `Column { }` | ✗ | ✓ | ✓ | 零 |
| **`@` 前缀** | ✓ | ✓ | ✓ | 加一个 token |
| 尖括号 `<Column>` | ✓ | ✗ 词法飞地 | ✗ 需 `if={}` 指令 | 词法模式 + LSP 双模 |

`@` 是唯一三项全中的。它在 tie 符号表中**完全空闲**（`<` `>` 是比较运算符，`!` 是逻辑非，`#` 被 `#[...]` 占用，`$` 是宏插值）。它同时给编译期校验以抓手：`ui` 文件里的 `@X` 必须是组件集成员。

### 3.2 块即元素体（控制流原生）/ Blocks are element bodies

元素用 tie **自身的 `{ }` 块**，元素是块内的**元素语句**。因此：

* `if` / `for` 是**原生 tie 语句**，不需要 `if={}` / `for={}` 指令（尖括号方案的第二大代价由此消除）；
* 一个 `if` 块可容纳**任意多个元素**——不需要额外片段容器；
* 兄弟元素按声明顺序排列；`-` 可显式强调并排（见 §3.4）。

```
@Column {
    @Text "tiu demo" .title
    @Text "count: {count}"

    if count > 2 {
        @Badge "large"
    }
    for h in history {
        @Text "- {h}" .muted
    }
}
```

### 3.3 内容形式 / Content forms

* **字符串字面量省括号**：`@Text "tiu demo"`（最常写）；
* **表达式保留括号**：`@Text(h)`（`@Text h` 有解析歧义风险，不采用）。

### 3.4 图算子并入 / Graph operators folded in

界面的数据流用 tie 规划的图语法表达（见 `tie-primitive-op-design.md` §5）：

| 图算子 | 界面语义 |
|---|---|
| `{ }` 节点模块 | 容器体（块内为子元素） |
| 模块内并列 / `-` 分叉 | 兄弟元素；`-` 显式强调并排（`@Row` 的语义即并行分支） |
| `a -> b` | 事件流向动作：`@Button "+1" -> Inc` |
| `a -> ~ b` | 回边 = 状态回流，触发视图重求值 |

**响应式循环就是一条回边**：

```
state -> Counter -> handle -> ~ state
```

这与 tiu 文档「状态经快照单向流动」一致，但**在语法上把重求值那条边写了出来**。

### 3.5 `view` 是带端口的图节点 / `view` as a ported node

```
view Counter(count, history) -> (Dec, Inc, Reset) {
    @Column { … }
}
```

* **入端口** = props（`count` / `history`）；**出端口** = 动作契约（`Dec` / `Inc` / `Reset`）。
* 于是 `class` 侧可用 `->` 串联、用 `~` 闭环——**组装与接线都是图运算**，与「用 class 拼接到一起」对齐。
* 声明本身用 tie 语法；只有**体内**进入 `@` 元素块语境。边界是一对花括号，最易实现也最易降级。

### 3.6 声明单元 / Declaration units

| 单元 | 作用 | 承载 |
|---|---|---|
| `view` | 页面级界面单元（有 props 与动作端口） | `@` 元素块 + 原生控制流 + 修饰链 |
| `component` | 可复用界面单元（含 `Slot`） | 同上 |
| 样式单元 | 选择器规则 + 分层 | 见 §4 |
| `theme` | token 取值表 | `token = 值` |
| `action` | 交互契约（只声明变体，不写实现） | 变体名 |

`style` / `theme` / `action` 是 `ui` 角色**新增的关键词**；`view` / `component` 亦进语言。

### 3.7 修饰链 / Modifier chains

修饰链是**样式钩子**，含义由样式表定义（等价 HTML 的 `class="primary"`）：

```
@Text "tiu demo" .title
@Button "-1" .lg -> Dec
```

* 修饰链允许**两类标记**共存：外观钩子（`.primary` / `.muted`，含义在样式表）与语义档位（`.lg` / `.compact`，含义在组件库）。
* 元素上只有两类东西：**语义属性**（命名参数：`on:` / `key:` / 内容 / `disabled`）与**样式钩子**（修饰链）。结构文件里**绝不出现颜色**。

### 3.8 事件箭头 / Event arrows

`->` 与 `→` **等价双支持**（`→` 为糖，`->` 为规范形）。事件用图箭头而非属性：

```
@Button "+1" -> Inc          // 规范形
@Button "+1" → Inc           // 糖
```

---

## 4. 样式体系 / Style system

### 4.1 单元与作用域 / Units and scope

* **独立样式单元**：可写在 `ui` 文件内的 `style` 块（文件局部），也可抽成独立**样式角色文件**（设计系统与跨文件复用）。两者并存。
* **作用域显式控制**：作用域写在**选择器侧**，不用命名约定兜底。

```
@layer base, components, overrides            // 分层序（胜负规则）
@scope Card { .title { fg: on_surface } }     // 作用域显式声明
```

### 4.2 选择器 / Selectors

支持：类型名 · 样式钩子 · 四态伪类（`:hover` `:focus` `:pressed` `:disabled`）· 后代 / 子 / 相邻 · 结构化伪类（`:first-child` 等）· 属性选择器。

**不做**：
* **特异性权重计算**——改
* **`!important`**——否
* **伪元素 `::before` / `::after`**——否。骨架是唯一结构真相（命中测试、差分、可访问性都依赖它），渲染层不得凭空造元素。装饰用真实元素或样式属性（`border` / `shadow`）表达。

### 4.3 层叠规则 / Cascade

**层序由声明顺序决定**（后声明层覆盖前层），**层内按书写顺序后者胜**，不做选择器权重计算。可预测、易调试，避开特异性战争。

### 4.4 布局归属 / Layout ownership

**结构决定「怎么排」，样式决定「多大、间距多少、怎么对齐」**（同 CSS 的 `div` + `display:flex` 分工）。

* 排布语义（`@Row` / `@Column` / `@Grid`）在结构里；
* 尺寸与间距在样式里，但**只引用布局 token**（`Space.md` / `Size.md`），不写裸数值。

故换肤、换 DPI、换渲染器**都不动结构文件**。

### 4.5 token / Tokens

样式属性**只认 token，不认裸值**：写 `accent` / `space.md`，不写 `0xFF4A9EFF` / `16`。token 解析发生在**适配器侧**——这使「换肤」与「换渲染器」在实现上是同一件事。

```
@theme dark { surface = shade.900  accent = hue.blue.400 }
```

---

## 5. UI IR / UI IR

`ui` 角色的编译产物，**唯一的跨角色契约**（与 tiu 绘制表 IR 同等地位）。

| 字段 | 内容 |
|---|---|
| `kind` | 元素种类（适配器提供的组件集） |
| `props` | 属性（含修饰链合并结果），静态值 |
| `children` | 子元素序列（顺序 = 声明顺序） |
| `slot` | 是否插槽占位 |
| `action` | 动作引用（事件种类 + 动作标识） |
| `key` | 稳定身份键（列表对账与差分复用） |
| `style_ref` / `theme_ref` | 样式与主题 token 引用（**不解析**） |

**中立性要求**：UI IR 中不得出现像素、颜色、字体句柄、渲染目标、GPU 概念。

**冻结纪律**：UI IR 布局一经冻结，修订只走版本表回写。

---

## 6. 组件模型 / Component model

* **组件 = 声明单元 + props 契约**；props 具名、有类型、编译期静态检查。
* **组合优于继承**：不引入组件继承；复用靠嵌套与插槽 `Slot`。
* **组件集可替换**：`Column` / `Row` / `Text` / `Button` 等**由适配器提供**，语言层只规定**最小语义集**（容器 / 文本 / 交互 / 图像 / 列表），不规定具体控件名。这是渲染器中立的必要条件。
* **组件无状态**：一切随 props 进入。
* **组件库归 `class` 角色**；`ui` 聚焦页面编排。

---

## 7. 状态 · 事件 / State and events

* **状态归 `logic`**：ui 文件无状态、无副作用、无全局。状态经 props 流入视图。
* **动作契约解耦**：ui 声明 `action` 变体（语义名），logic 实现处理器。换状态管理方案（局部状态 / 全局 store / actor）**不动 ui 文件**。
* **单向数据流**：事件 → 动作 → logic 更新状态 → 新 props → 视图重新求值 → 新 UI IR → 适配器重绘。
* **主题由 logic 选择**：ui 文件不含「当前主题」概念。

---

## 8. 适配器模型 / Adapter model

适配器把 UI IR 变成像素：`适配器.run(view_ref, state, action_handler)`。

| 适配器 | 产出 | 状态 |
|---|---|---|
| tiu 适配器 | tiu 骨架 + 绘制表 → 软件内核/GPU → 窗口 | 已有基础（tiu 仓 `ui/src/view.tie` 库函数形态 + `probe_app` 交互闭环） |
| 测试快照适配器 | UI IR 结构断言 | 未做（**价值高**：界面可无渲染器测试） |
| Skia 适配器 | Skia Canvas 调用 | 未做（`ext/gfx` 已有 Skia 裁剪库与 thunk 可复用） |
| 终端适配器 | ANSI / 文本布局 | 未做 |

职责边界：适配器**负责**组件集实现、token 解析、布局、绘制、事件采集；**不负责**界面结构（ui）与状态语义（logic）。

---

## 9. 实测依据 / Measured basis

2026-09-26 以现役自举 tiec 实测（逐条附错误码）；**文档常滞后于编译器，能力以实测为准**。

### 9.1 已可用 / Available

| 能力 | 结论 |
|---|---|
| 尾随闭包段落 `F { … }` | ✓ 解析为「传语句块闭包」（当前元素块的**过渡形态**） |
| 元素语句自登记（裸调用作语句） | ✓ |
| 语句位置 `if` / `while` | ✓（普通函数与闭包内均可） |
| 泛型函数 + `fn` 形参 | ✓（组件与列表映射的基石） |
| 闭包作实参（字面量 / 变量 / 尾随） | ✓ 三种传法均可 |
| 闭包嵌套 / 闭包捕获 | ✓ |
| `enum` 递归 payload `Box(table<Node>)` | ✓ |
| 管道 `t -> [i]` / `p -> .field`（读取） | ✓ **2026-09-26 落地**（tiec `22b1519`） |
| `enum` payload = string / f64 / `table<T>` / 多字段 + 绑定解构 | ✓ |

### 9.2 不可用 / Not available

| 能力 | 现象 / 错误码 |
|---|---|
| `if` / `for` / `switch` 作表达式 | `无法以 If/For 开始表达式` |
| **闭包形参省略类型** | `E00484 期望 ':'` ⇒ **`{ v -> expr }` 无法脱糖为闭包**，块管道必须走内联绑定 |
| `{ }` 作表达式块 | 被当 map 字面量（`记录字面量元素必须是 '键: 值'`） |
| **闭包体内含 `for`** | **IR 缺陷** `undefined value '%-1'`（`while` 正常） |
| 闭包内改捕获局部变量 | 外层不可见（env 副本语义） |
| `table<R>` 作函数形参 | `E00000 行池 table<R> 不能作函数形参` |
| `enum` payload = struct / fn | `E00365` |
| `pub` 修饰 enum | `E00484` |
| `fn` 作 extern 形参（C 回调） | `E00041` ⇒ WndProc 类回调必须落 C 端 |
| 表字面量尾随逗号 | `无法以 RBracket 开始表达式` |
| 全局 `bool` 初值 | 不可靠（`var g: bool = false` 实测失效）⇒ 用 `i64` 标志位 |
| 保留名撞车 | `text`（类型名）· `when`（switch 守卫） |

### 9.3 缺陷与语言档依赖 / Defects and dependencies

**缺陷登记**：
* **D1（阻断级）** 闭包体内含 `for` → IR 缺陷。元素块若沿用闭包语义则不可用；**改声明式元素块自然绕开**。
* **D2** 闭包捕获 move 语义：闭包内写捕获变量外层不可见 ⇒ ui 构建器不得依赖捕获回写。
* **D3 / D4** `table_push` 不能推入下标 / 不能直接推字面量。

**语言档依赖**：
* **主依赖**：ui 角色元素块语义（解析器按文件角色分派；`@` token）。
* 新关键词：`view` / `component` / `style` / `theme` / `action` / `Slot` / `@`。
* 图语法声明与流向子集（`{ }` / 并列 / `-` / `->` / `~`）——**只取声明与流向，不取波次执行与图论套件**，故是可裁剪依赖。
* `p.8.1.8`（struct payload）与 `p.9.11.22`（fn 捕获）**非必需**：本设计用扁平 props 与声明式元素块绕开。

---

## 10. 落地路线 / Roadmap

| 阶段 | 内容 | 门禁 |
|---|---|---|
| 前置 | **图轨道** p.9.13.5（`{ }` 节点模块 / `-` / `->` / `~`）——ui 的流向算子与其同形 | 图内核探针 |
| 一 | 语言档：`@` 元素块 + `view` / `component` + 元素块内原生控制流 | 解析与语义探针；现有代码零回归 |
| 二 | UI IR 定稿（§5）并冻结 | gold UI IR 断言 |
| 三 | `action` 契约 + `Slot` 插槽 | 动作引用与插槽注入探针 |
| 四 | tiu 适配器正式化（现有 `view.tie` 库函数形态升级） | 与 `probe_app` 交互闭环同比全绿 |
| 五 | 测试快照适配器 | 结构断言可脱离渲染器 |
| 六 | Skia 适配器（复用 `ext/gfx` 裁剪库） | 同一 ui 文件零改动跑通 |
| 增强 | 修饰链无括号形式 / 插值 / 尾随逗号 / 命名参数 | 逐项独立，不阻塞主线 |

---

## 11. 验收基准 / Acceptance

| 项 | 基准 |
|---|---|
| 渲染器中立 | `ui` 文件内**零渲染器标识符**（静态检查探针） |
| 多后端 | **同一 ui 文件零改动**在 tiu 与 Skia 两适配器产出等价结构 |
| 无渲染器可测 | 测试快照适配器可在无窗口 / 无 GPU 环境断言结构 |
| 组件复用 | 同一 component 多处实例化，结构正确且属性独立 |
| 事件解耦 | 更换动作实现不改 ui 文件 |
| 主题解耦 | 切换主题不改 ui 文件；token 解析全在适配器侧 |
| 构建期校验 | ui 文件内的渲染调用 / 状态写入 → 编译期报错 |
| 控制流 | 元素块内 `if` / `for` 编译通过并语义正确（需 D1 修复或声明式元素块） |

---

## 12. 附录 / Appendix

**术语**：UI IR（界面描述数据）· 适配器（UI IR → 具体渲染）· 元素块（element block）· 动作契约（action contract）· 插槽（Slot）· 语义 token（semantic design token）

**本轮锁定决策**（用户对齐，2026-09-26）：
1. `class` 双职责：组件库 + 应用组装
2. 现在就加新语法（非渐进）
3. 核心声明单元进语言，次级糖用宏
4. 元素标记用 `@`；`<>` 不采用（词法飞地）
5. 修饰链两类标记共用（外观钩子 + 语义档位）
6. 不做伪元素
7. 样式单元：块与独立文件并存
8. 选择器接近完整 CSS
9. 层叠 = 显式分层序 + 层内源序，不做权重
10. 布局归结构
11. 字符串字面量省括号，表达式保留括号
12. 事件箭头 `->` 与 `→` 双支持
13. 保留可选容器（`@Group` 类）作不渲染容器
14. `view` = 带端口的图节点
15. 先做图后做 ui

**演进**：本设计随语言实现修正；阶段一落地结论（元素块语义最终形态）反向修订 §3.2 与 §5。
