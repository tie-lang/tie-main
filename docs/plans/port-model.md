# 规划：tie 接口模型（port：显式 impl + 双形态分发 + 隐式 vtable）
*EN: Plan: tie Interface Model (port: explicit impl + dual-form dispatch + implicit vtable)*

> 状态：**规划**（2026-08-15 设计讨论定稿，未实现）
> EN: Status: **Plan** (design discussion finalized 2026-08-15, not yet implemented)
> 本文档定义 tie 的接口模型。决策汇总：
> EN: This document defines tie's interface model. Decision summary:
> **语法 P1**（port 声明 + 显式 impl 块）+ **分发 D3**（静态：泛型约束单态化；
> EN: **Syntax P1** (port declaration + explicit impl block) + **Dispatch D3** (static: generic-constraint monomorphization;
> 动态：port 对象 + vtable）+ **实现 I1+I2 混合**（编译器隐式生成 vtable 为默认，
> EN: dynamic: port objects + vtable) + **Implementation I1+I2 hybrid** (compiler-implicit vtable as default,
> 用户手写方法表为 escape hatch，手写路径归 unsafe）。
> EN: user hand-written method tables as the escape hatch; the hand-written path belongs to unsafe).
> 关联：闭包模型（docs/plans/closure-model.md，C2 函数指针是 vtable 的地基）、
> EN: Related: closure model (docs/plans/closure-model.md; C2 function pointers are the foundation of the vtable),
> 内存模型（移动语义+arena）、UI 框架（docs/plans/ui-framework.md）。
> EN: memory model (move semantics + arena), UI framework (docs/plans/ui-framework.md).

## 1. 动机与目标
*EN: 1. Motivation and Goals*

tie 有 `type tie<port>` 文件角色（接口占位）但**零实现零用例**；泛型无约束
（单态化展开但无法表达"类型必须支持某组方法"）。接口模型需要解决：
EN: tie has the `type tie<port>` file role (an interface placeholder) but **zero implementations and zero use cases**; generics are unconstrained (they monomorphize but cannot express "a type must support a certain set of methods"). The interface model must address:

- **抽象**：UI 组件抽象（Button/Text 实现同一 Drawable 接口，三端复用）
  EN: **Abstraction**: UI-component abstraction (Button/Text implement the same Drawable interface, reused across the three backends).
- **解耦**：库发布携带接口，实现可替换（tieuicore 抽象面）
  EN: **Decoupling**: libraries ship interfaces and implementations are replaceable (the tieuicore abstraction surface).
- **约束**：泛型参数限制（`func render_all<T: Drawable>(...)`）
  EN: **Constraints**: bounding generic parameters (`func render_all<T: Drawable>(...)`).
- **多态**：异构容器（`table<Drawable>` 装 Button+Text 混排）
  EN: **Polymorphism**: heterogeneous containers (`table<Drawable>` holding a mix of Button+Text).

设计目标：**静态分发零开销**（复用单态化）+ **动态分发完整多态**（vtable），
安全优先（显式 impl 保证完整性），与闭包/内存/arena 模型咬合。
EN: Design goals: **zero-cost static dispatch** (reusing monomorphization) + **full-polymorphism dynamic dispatch** (vtable), safety-first (explicit impl guarantees completeness), interlocking with the closure/memory/arena models.

## 2. 语法（P1：port 声明 + 显式 impl）
*EN: 2. Syntax (P1: port Declaration + Explicit impl)*

### 2.1 port 声明：方法签名集合
*EN: 2.1 port Declaration: a Set of Method Signatures*

```tie
// port = 接口，声明方法签名集合（不包含实现）
// 方法接收者统一为 self（与 tie 的"struct 数据/逻辑分离"一致）
port Drawable {
    pub func draw(self, ctx: ptr) -> i64
    pub func bounds(self) -> Rect
}

// port 可含默认实现（可选）
port Greeter {
    pub func hello(self) -> string
    pub func greet(self) -> string {
        return "Hello, " + self.hello()   // 默认实现，impl 可覆盖
    }
}
```

- port 声明位置：`type tie<port>` 文件（接口库）或普通逻辑文件内
  EN: port declaration location: a `type tie<port>` file (interface library) or inside a normal logic file.
- port 方法**必须**带 `self` 接收者（接口是对象行为的抽象）
  EN: port methods **must** take a `self` receiver (an interface abstracts object behavior).
- 方法签名完整：参数类型 + 返回类型
  EN: Method signatures are complete: parameter types + return type.

### 2.2 显式 impl：绑定 struct
*EN: 2.2 Explicit impl: Binding a struct*

```tie
// impl 块 = 把命名空间函数注册为 port 方法
// tie 的 struct 是纯数据，方法实现是命名空间函数（obj.method() 转发）
// impl 块即声明"该 struct 的这些命名空间函数满足 port 签名"
impl Drawable for Button {
    pub func draw(self, ctx: ptr) -> i64 { ... }
    pub func bounds(self) -> Rect { ... }
}
```

- **显式 impl 是强制要求**：struct 不声明 impl 就不满足 port（拒绝鸭子类型）
  EN: **Explicit impl is mandatory**: a struct that does not declare an impl does not satisfy the port (duck typing rejected).
- **完整性检查**：impl 必须实现 port 全部方法（漏方法 = 编译错误）；
  实现了额外方法 = 允许（不报错，只是不参与该 port）
  EN: **Completeness check**: an impl must implement all port methods (missing a method = a compile error); implementing extra methods is allowed (no error, they just do not participate in that port).
- impl 的位置：与 struct 同文件，或分离文件（`impl` 可出现在任何
  import 了 struct 与 port 的文件中）——支持"为外部类型实现接口"
  EN: impl placement: same file as the struct, or a separate file (`impl` can appear in any file that imports both the struct and the port) — supporting "implementing an interface for external types".

### 2.3 泛型约束（静态分发形态）
*EN: 2.3 Generic Constraints (the Static-Dispatch Form)*

```tie
// port 作泛型约束：T 必须 impl Drawable
func render_all<T: Drawable>(items: table<T>, ctx: ptr) {
    var i: i64 = 0
    while i < len(items) {
        items[i].draw(ctx)   // 编译期绑定具体实现（单态化）
        i = i + 1
    }
}
```

- 约束语法：`<T: Port1, U: Port2>`，多约束逗号分隔
  EN: Constraint syntax: `<T: Port1, U: Port2>`, multiple constraints comma-separated.
- 违反约束 = 编译错误（"类型 T 未实现 port Drawable"）
  EN: Violating a constraint = a compile error ("type T does not implement port Drawable").
- 与现有泛型单态化同路径：实参化时校验 + 直接调用具体函数
  EN: On the same path as existing generic monomorphization: validate at instantiation + call the concrete function directly.

## 3. 分发机制（D3：双形态）
*EN: 3. Dispatch Mechanism (D3: Dual Forms)*

### 3.1 静态分发（编译期）
*EN: 3.1 Static Dispatch (Compile Time)*

- 机制：泛型约束 + 单态化展开，调用点编译期绑定
  EN: Mechanism: generic constraints + monomorphization expansion, bound at the call site at compile time.
- 开销：零（无间接调用、无 vtable）
  EN: Cost: zero (no indirect calls, no vtable).
- 适用：泛型算法、编译期已知类型的场景
  EN: Applies to: generic algorithms, scenarios where types are known at compile time.

### 3.2 动态分发（运行时，port 对象）
*EN: 3.2 Dynamic Dispatch (Runtime, port Objects)*

```tie
// port 对象：具体类型提升为接口类型（数据指针 + vtable）
var d: Drawable = button          // Button → Drawable（自动提升）
var d2: Drawable = text           // Text → Drawable
var list: table<Drawable> = [d, d2]   // 异构混排

list[0].draw(ctx)                 // 间接调用（vtable 查表）
```

- **提升**：具体类型 → port 对象是隐式自动转换（I1 编译器生成 vtable 与打包代码）
  EN: **Promotion**: concrete type → port object is an implicit, automatic conversion (I1 generates the vtable and the packing code).
- **调用**：`d.draw(ctx)` 编译为 vtable 间接调用
  EN: **Calling**: `d.draw(ctx)` compiles to a vtable indirect call.
- **适用**：UI 组件树（异构容器）、插件注册、tieuicore 抽象面
  EN: **Applies to**: UI component trees (heterogeneous containers), plugin registration, the tieuicore abstraction surface.

### 3.3 双形态的取舍
*EN: 3.3 Trade-offs of the Dual Forms*

| | 静态分发 | 动态分发 |
| --- | --- | --- |
| 绑定时机 | 编译期 | 运行期 |
| 开销 | 零 | 一次间接调用 |
| 异构容器 | ❌ | ✅ |
| 动态注册 | ❌ | ✅ |
| 适用 | 泛型算法 | 组件树/插件 |

EN: Static dispatch binds at compile time at zero cost but cannot do heterogeneous containers or dynamic registration; dynamic dispatch (port objects) enables both at the cost of one indirect call. Static is best for generic algorithms; dynamic for component trees / plugins.

两者互补：**算法默认静态，对象集合默认动态**。同一 port 双形态并存，
`T: Drawable` 是约束，`Drawable`（无类型参数）是对象类型。
EN: The two complement each other: **algorithms default to static, object collections default to dynamic**. The same port coexists in both forms — `T: Drawable` is a constraint, while `Drawable` (no type parameter) is an object type.

## 4. 实现（I1+I2 混合：编译器隐式 vtable + 用户手写逃生舱）
*EN: 4. Implementation (I1+I2 Hybrid: Compiler-Implicit vtable + User Hand-Written Escape Hatch)*

### 4.1 vtable 布局
*EN: 4.1 vtable Layout*

```
port Drawable 的 vtable（每个 impl 生成一份，全局静态）：
  struct Drawable_vtable {
      draw:  fn(ptr /* self */, ptr /* ctx */) -> i64,   // 函数指针
      bounds: fn(ptr /* self */) -> Rect,
  }

port 对象（Drawable 类型的值）：
  struct Drawable {
      data: ptr,                    // 指向具体对象（Button 实例）
      vtable: ptr,                  // 指向 Drawable_vtable（静态）
  }
```

### 4.2 I1：编译器隐式生成（默认路径）
*EN: 4.2 I1: Compiler-Implicit Generation (Default Path)*

- `impl Drawable for Button` 处：编译器自动生成
  - `Button_drawable_vtable` 全局常量（方法指针表）
  - 提升代码：`Button → Drawable`（打包 data + vtable）
  EN: At `impl Drawable for Button`, the compiler auto-generates the `Button_drawable_vtable` global constant (method-pointer table) and the promotion code `Button → Drawable` (packing data + vtable).
- vtable 是**全局静态数据**：无生命周期问题、无分配开销
  EN: The vtable is **global static data**: no lifetime issues, no allocation cost.
- 零样板、安全：impl 完整性检查（漏方法报错）保证 vtable 永远完整
  EN: Zero boilerplate and safe: the impl completeness check (missing a method errors) guarantees the vtable is always complete.

### 4.3 I2：用户手写方法表（escape hatch，归 unsafe）
*EN: 4.3 I2: User Hand-Written Method Table (escape hatch, under unsafe)*

```tie
// 手写路径：unsafe 内手动构造 vtable 结构（I1 之外的灵活性）
unsafe {
    var vt: Drawable_vtable = Drawable_vtable(
        draw = my_draw_fn,          // 函数指针直接赋值
        bounds = my_bounds_fn,
    )
    var d: Drawable = Drawable(
        data = addr_of(obj),        // 手动取地址
        vtable = addr_of(vt),
    )
}
```

适用场景（I1 表达不了的）：
- **外部类型适配**：为无法写 impl 的类型（C 库结构、extern 类型）构造方法表
  EN: **External-type adaptation**: constructing method tables for types that cannot have an impl written (C library structs, extern types).
- **动态方法集**：运行时按条件选择不同方法实现
  EN: **Dynamic method sets**: choosing different method implementations by condition at runtime.
- **绕过完整性检查**：故意不实现全部方法（剩余方法运行时才调用）——危险，unsafe 自证
  EN: **Bypassing the completeness check**: deliberately not implementing all methods (the rest are called at runtime) — dangerous, self-justified under unsafe.

- I2 归 unsafe 的原因：手动构造涉及函数指针 + 取地址（指针操作总原则）
  EN: Why I2 belongs to unsafe: manual construction involves function pointers + taking addresses (the general pointer-operations principle).
- I2 是逃生舱不是主路：正常开发用 I1，I2 只留给适配层（tieuicore 对接系统 API）
  EN: I2 is an escape hatch, not the main path: normal development uses I1; I2 is reserved for the adapter layer (tieuicore bridging to system APIs).

### 4.4 与闭包模型（C2）的关系
*EN: 4.4 Relationship with the Closure Model (C2)*

- vtable 字段是**函数指针**（fn 类型）——依赖闭包模型的 C2（函数指针+环境）
  EN: vtable fields are **function pointers** (fn types) — depending on closure-model C2 (function pointer + environment).
- 方法实现本质 = "self 环境 + 函数指针"的闭包形态
  EN: A method implementation is essentially a closure of "self environment + function pointer".
- 无捕获方法 = 普通函数指针；self 作为隐藏第一参数传递
  EN: Non-capturing methods = plain function pointers; self is passed as a hidden first parameter.
- **依赖序：闭包 C2（函数指针）先行 → port 动态分发后行**
  EN: **Dependency order: closure C2 (function pointers) first → port dynamic dispatch later**.

### 4.5 借用语义（归 unsafe）
*EN: 4.5 Borrow Semantics (under unsafe)*

- 接口对象持有 `data: ptr`（借用具体对象）——**指针操作归 unsafe**
  EN: An interface object holds `data: ptr` (borrowing the concrete object) — **pointer operations belong to unsafe**.
- **提升操作必须在 unsafe 上下文内**：
  EN: **Promotion must happen inside an unsafe context**:

```tie
unsafe {
    var d: Drawable = button          // 提升 = 取 data 地址 + 打包 vtable
}
```

- 生命周期责任在程序员：保证被提升对象存活时间 ≥ 接口对象使用时间
  （编译器不做检查——不引入生命周期分析，与"指针归 unsafe"总原则一致）
  EN: Lifetime responsibility rests with the programmer: ensure the promoted object outlives the interface object's usage (the compiler does not check — no lifetime analysis is introduced, consistent with the "pointers are unsafe" principle).
- 推荐实践（文档约定）：接口对象引用 arena 内对象（同区域同生命周期），
  区域释放时接口对象同时失效——arena 是安全的默认使用模式，
  unsafe 是逃生舱（引用堆对象/跨区域对象时由程序员自证安全）
  EN: Recommended practice (documented convention): interface objects reference arena objects (same region, same lifetime) so they become invalid with region release — arena is the safe default usage; unsafe is the escape hatch (the programmer self-justifies safety when referencing heap / cross-region objects).

## 5. 与库模型的关系
*EN: 5. Relationship with the Library Model*

- `type tie<port>` 文件 = 接口库（纯 port 声明 + 默认实现，无 struct）
  EN: A `type tie<port>` file = an interface library (pure port declarations + default implementations; no structs).
- 库发布携带 port（接口面），实现可替换：
  EN: Libraries ship ports (the interface surface); implementations are replaceable:
  - tieuicore 暴露 port（如 `port Window`），tieui 消费 port，
    具体后端（Win32/X11/wasm）是 impl
    EN: tieuicore exposes ports (e.g. `port Window`), tieui consumes them, and concrete backends (Win32/X11/wasm) are the impls.
- 包依赖可声明为"接口依赖"（依赖 port 而非具体实现）
  EN: Package dependencies can be declared as "interface dependencies" (depending on a port rather than a concrete implementation).

## 6. 编译器实现拆解（tiec 自举）
*EN: 6. Compiler Implementation Breakdown (tiec bootstrap)*

| 模块 | 改动 |
| --- | --- |
| lexer/parser | `port` 声明语法、`impl ... for ...` 语法、泛型约束 `<T: Port>` 语法 |
| semantic | port 方法集收集、impl 完整性检查（漏方法报错）、泛型约束校验、提升合法性（arena 检查） |
| 类型系统 | port 类型、port 对象类型（data+vtable）、泛型约束注册 |
| irgen | vtable 常量生成、提升代码生成（打包）、间接调用指令 |
| llvmgen | vtable 全局常量发射、间接调用、函数指针类型 |
| 泛型单态化 | 约束校验接入现有单态化展开（T 实参化时检查 impl） |

EN: The table breaks the tiec changes down by module: lexer/parser add the `port`/`impl ... for ...` and `<T: Port>` syntax; semantic collects port method sets, checks impl completeness, validates generic constraints, and checks promotion legality (arena); the type system adds port and port-object types; irgen and llvmgen emit vtable constants and indirect calls; monomorphization integrates constraint checks.

## 7. wasm 兼容
*EN: 7. wasm Compatibility*

- vtable = 静态表：wasm 直接支持（函数指针表 + call_indirect）
  EN: vtable = a static table: directly supported in wasm (function-pointer table + call_indirect).
- 动态分发在 wasm 无障碍（与闭包 C2 同一机制）
  EN: Dynamic dispatch is friction-free in wasm (same mechanism as closure C2).
- 嵌入式（tie:embedded）：vtable 是静态数据，无动态分配，适用；
  但动态分发若追求零开销可禁（编译期报错，改用静态分发）
  EN: Embedded (tie:embedded): vtable is static data with no dynamic allocation, so it applies; but dynamic dispatch can be disabled if zero-overhead is required (compile-time error, switching to static dispatch).

## 8. 决策记录（讨论产物）
*EN: 8. Decision Record (Discussion Output)*

| 决策点 | 结论 | 备选（未选） |
| --- | --- | --- |
| 语法 | P1：port 声明 + 显式 impl 块 | P2 鸭子类型（结构匹配）、P3 继承式 |
| 分发 | D3：静态（泛型约束）+ 动态（port 对象）双形态 | D1 纯静态、D2 纯动态 |
| vtable 生成 | **I1+I2 混合**：编译器隐式生成（默认）+ 用户手写方法表（escape hatch，归 unsafe） | 纯 I1 隐式、纯 I2 手写 |
| 借用语义 | 归 unsafe：提升操作必须在 unsafe 上下文内，生命周期责任在程序员 | 编译器检查（arena 边界）、完整借用检查 |
| 完整性 | 显式 impl + 漏方法编译错误 | 鸭子类型运行时暴露 |

EN: Decisions: syntax P1 (explicit impl), dispatch D3 (static + dynamic), vtable generation I1+I2 hybrid, borrow semantics under unsafe, completeness via explicit impl + compile error on missing methods.

## 9. 依赖与顺序
*EN: 9. Dependencies and Order*

1. **闭包模型 C2（函数指针）先落地** → vtable 才有地基
   EN: **Closure model C2 (function pointers) lands first** → only then the vtable has a foundation.
2. 静态分发（泛型约束）可先行（只依赖泛型单态化，已存在）
   EN: Static dispatch (generic constraints) can go first (depends only on generic monomorphization, which already exists).
3. 动态分发（port 对象）随 C2 落地后加
   EN: Dynamic dispatch (port objects) is added after C2 lands.

## 10. 未决问题
*EN: 10. Open Questions*

1. **默认实现的覆盖规则**：impl 未覆盖默认方法时用 port 默认实现；
   覆盖时签名必须一致——检查规则细化
   EN: **Default-implementation override rules**: use the port default when an impl does not override a default method; overriding must keep the signature consistent — refine the checking rules.
2. **多 port 提升**：struct 实现多个 port，提升到不同 port 对象——
   vtable 各自生成，无冲突（确认）
   EN: **Multi-port promotion**: a struct implementing several ports promotes to different port objects — each vtable is generated separately without conflict (confirm).
3. **port 继承/组合**：port 能否继承 port（`port A : B`）？第一版建议
   **禁止**（组合代替继承：`port C { func a(); func b() }`），后置
   EN: **port inheritance/composition**: can a port inherit a port (`port A : B`)? v1 recommends **forbidding** it (composition over inheritance: `port C { func a(); func b() }`), deferred.
4. **接口对象的方法扩展**：port 对象上能否调用非 port 方法（强转回具体
   类型）？第一版**禁止**（数据抽象），需要 downcast 时走 unsafe
   EN: **Method extension on interface objects**: can non-port methods be called on a port object (casting back to the concrete type)? v1 **forbids** it (data abstraction); downcasts go through unsafe.
5. **泛型 port 对象**：`port Box<T>` 的泛型 port 是否支持——与泛型单态化
   同路径，理论上可，后置
   EN: **Generic port objects**: whether generic ports like `port Box<T>` are supported — same path as generic monomorphization, theoretically possible, deferred.