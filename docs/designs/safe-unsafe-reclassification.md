# tie 安全 unsafe 重分类设计（2026-09-17 定稿）

*EN: tie Safe-Unsafe Reclassification Design (finalized 2026-09-17)*

> **定位**（用户指令）：将「安全的 unsafe」踢出 unsafe。判定准则唯一：
> **构造安全 ⟺ 不可能引发 UB**（悬垂解引 / 越界访问 / 数据竞争）——误用只导致
> 可捕获 panic 或逻辑错误的不算 unsafe。逐项裁决如下，落地时同步修订
> language.md §14/§16 类型表标注。
>
> EN: Per user directive: move "safe-in-practice unsafe" out of unsafe. Single
> criterion: **a construct is safe ⟺ it cannot cause UB** (dangling dereference /
> out-of-bounds access / data race) — misuse that only yields a catchable panic or
> a logic error does not count as unsafe. Item-by-item rulings below; language.md
> §14/§16 type-table annotations get revised at landing.

## 1. 逐项裁决

*EN: 1. Item-by-Item Rulings*

| 构造 | 现状 | 裁决 | 依据 |
| --- | --- | --- | --- |
| `atomic<T>` 全家（load/store/atomicrmw/cmpxchg） | unsafe | **→ 安全** | 原子操作无数据竞争 UB；内存序误用是正确性 bug 不是内存不安全（Rust 同判） |
| `slice<T>` + `s[i]` 下标 + `slice_of(表)` | unsafe | **→ 安全** | §14 已实现边界防护 + 可捕获 panic——越界是 panic 不是 UB；`slice_of` 只是表的连续视图，不产生新所有权 |
| `ptr<T>` 声明 / 比较 / 传参 | unsafe | **→ 安全** | 指针值本身无危害（Rust 同判：裸指针可创建可拷贝，解引才 unsafe） |
| `*p` 解引 / 指针算术 / 偏移 | unsafe | **维持 unsafe** | 悬垂/越界解引 = 真 UB，唯一 guarded 面 |
| `alloc(n)` 原始缓冲 | unsafe | **维持 unsafe** | 未初始化读是垃圾值（alloc 误扫 RCA 实证过 0xC0000005 级事故）；安全路径 = p.9.1.4 std 封装 |
| `#[repr(C)]` 声明 | unsafe | **→ 安全** | 布局属性本身无副作用；危害只发生在指针逃逸时 |
| `addr_of` | unsafe | **维持 unsafe** | 取地址 + 逃逸 = 悬垂可能 |
| `extern fn` 调用 | unsafe | **维持 unsafe** | C 侧内存安全无法由 tiec 验证（Rust 同判） |
| volatile/MMIO、`asm!`、`unsafe goto`、凭据门禁 | unsafe | **维持 unsafe** | 裸硬件/状态机/越界逃生，本质危险面 |

*EN: atomics, bounds-checked slices, and pointer-value manipulations become safe; raw dereference/arithmetic, alloc, addr_of, extern calls, and hardware/state-machine constructs stay unsafe.*

## 2. 机制细节

*EN: 2. Mechanics*

- **slice 安全化 = 把已有实现转正**：§14 边界防护 + 可捕获 panic 已落地，本设计不改
  运行期行为，只改门禁分类——`s[i]`/`len`/`slice_of` 免 unsafe 上下文；`*p` 解引与
  算术仍要求 `unsafe fn` / `unsafe { }`（同一类型两种访问面、两种门禁，与 Rust
  「安全切片 vs 裸指针」双层同构）；
- EN: **Slice safification formalizes the existing implementation**: §14 bounds protection + catchable panic already landed — runtime behavior unchanged, only the gate classification moves; `s[i]`/`len`/`slice_of` need no unsafe context, while `*p` dereference and arithmetic still require `unsafe fn` / `unsafe { }` (one type, two access faces, two gates — isomorphic to Rust's safe-slices-vs-raw-pointers split);

- **atomic 无新增机制**：类型与五个操作整体搬出 unsafe；内存序参数仍显式（顺序错误
  的后果由文档约定，编译器不猜）；
- EN: **Atomics add no machinery**: the type and its five operations move out of unsafe wholesale; memory-ordering parameters stay explicit (consequences of wrong ordering are documented conventions, not compiler guesses);

- **repr(C)/addr_of/extern 拆分**：声明、布局、结构体使用安全；指针逃逸到 C 边界
  unsafe——这条线让「定义 Win32 结构体」（纯数据工作）不再被迫进 unsafe，只有
  调用 OS API 那一行进；
- EN: **repr(C)/addr_of/extern split**: declaration, layout, and struct usage are safe; pointer escape to the C boundary is unsafe — the line lets "defining Win32 structs" (pure data work) stay out of unsafe, with only the OS-API call lines inside;

- **与 p.9.1.4 的关系**：round3 设计已定「封装后的安全路径不要求 unsafe 上下文」——
  本设计使其在语言层成立（slice 视图族、CStr 桥底层若用 slice/ptr，安全面自动脱离
  门禁）；alloc 底层封装实现者仍需 unsafe，用户面不需要；
- EN: **Relation to p.9.1.4**: round3 already decided "wrapped safe paths need no unsafe context" — this design makes that true at the language layer (slice-view family and the CStr bridge automatically leave the gate on their safe faces); wrapper implementers still need unsafe over raw alloc, users do not;

- **与凭据门禁的关系**：`guard<share>`/`mem`/`ext`/`trm` 面不动——凭据管的是
  「跨 actor 共享 / 越界逃生」，与本次内存安全重分类正交。
- EN: **Relation to credential gates**: `guard<share>`/`mem`/`ext`/`trm` surfaces are untouched — credentials govern cross-actor sharing / escape hatches, orthogonal to this memory-safety reclassification.

## 3. 明确不做

*EN: 3. Explicit Non-Goals*

- **alloc(n) 安全化**：未初始化语义是它的存在理由（性能），加零初始化检查就变成了
  另一个类型；安全替代走 std（p.9.1.4）；
- EN: **No alloc safification**: uninitialized semantics is its reason to exist (performance); zero-init checks would make it a different type; the safe alternative lives in std (p.9.1.4);

- **volatile/MMIO 包装**：裸硬件定位，包一层只会模糊危险边界；
- EN: **No volatile/MMIO wrapping**: bare-hardware positioning; wrapping would only blur the danger boundary;

- **extern 调用白名单**：不为「可信 C 库」开白名单——C 侧可变性不可静态断言，门禁
  保持二值。
- EN: **No extern-call whitelist**: no "trusted C library" allowlist — C-side mutability is not statically assertable; the gate stays binary.

## 4. 验收

*EN: 4. Acceptance*

- 正例探针：`atomic` 五操作 / `slice_of` + `s[i]` + `len` / `ptr` 声明比较传参 /
  `#[repr(C)]` struct 声明与字段访问——全部**免** unsafe 上下文编译运行；
- EN: Positive probes: the five atomic ops / `slice_of` + `s[i]` + `len` / ptr declare-compare-pass / `#[repr(C)]` struct declaration and field access — all compile and run **without** unsafe context;

- 负例探针：`*p` 解引 / 指针算术 / `alloc` / `addr_of` / `extern` 调用在安全路径
  仍报「需 unsafe 上下文」；
- EN: Negative probes: `*p` dereference / pointer arithmetic / `alloc` / `addr_of` / `extern` calls still report "unsafe context required" on the safe path;

- 越界 slice 访问 panic 可捕获行为与重分类前逐字节一致（纯门禁移动，零运行期变化）；
  自举不动点 + 回归基线不劣化。
- EN: Out-of-bounds slice-panic catchability byte-identical to before (pure gate move, zero runtime change); bootstrap fixpoint + no regression-baseline degradation.
