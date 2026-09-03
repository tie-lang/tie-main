# tie p.6.8 Skia 全栈图形（精简自建子集 + unsafe 直绑）

* 日期 / Date：2026-09-03

* 状态 / Status：规划已对齐，待执行（Aligned with user, pending execution）

* 基线 / Baseline：p.6.7 验收后（trm-lite preview\.3 并发安全 + 双形态真并行收官）

* 依据 / Basis：`docs/plans/ui-framework.md`（UI 框架与 unsafe 模型决策）、
  `docs/plans/tucore-arch.md`（trm.ui 域：D2 命令列表 / H2 句柄 / E3 事件+信号）、
  `docs/plans/roadmap.md`（S4.2 trm.ui / S4.3 tieui）。

* 实现约束 / Implementation constraint：本模块全部工作**用 tie 语言完成**
  （编译器扩展、构建脚本、绑定层、探针、验收）；仅 Skia 裁剪库本身为
  C++ 源码（第三方依赖），其构建脚本亦用 tie 编写（延续「打包器不用
  PowerShell」约束）。EN: All work in this module is done **in tie** (compiler
  extensions, build scripts, binding layer, probes, acceptance); only the trimmed
  Skia library itself is C++ source (third-party), and its build script is also
  written in tie (following the "no PowerShell for packagers" constraint).

***

## 1. 定位 / Positioning

p.6.8 为 tie 引入 **Skia 全栈图形**：以 Google Skia 为统一 2D 渲染核心，承载
窗口绘制、文本、路径、图像的完整图形栈。用户决策（2026-09-03）：

EN: p.6.8 brings **Skia full-stack graphics** to tie: Google Skia as the unified 2D
rendering core carrying the complete graphics stack of window drawing, text, paths,
and images. User decisions (2026-09-03):

* 范围 / Scope：**全栈图形**——渲染 + 窗口 + 事件由 Skia 图形栈整体承担（Flutter 式）。

* 绑定 / Binding：**先扩 unsafe 再直绑**——先实现 ptr / repr(C) 结构体语言能力，
  再用 typed ptr / repr(C) 直接表示 Skia 对象，非黑盒 i64 句柄。

* 来源 / Source：**精简自建子集**——裁剪 Skia 源码只编必需模块（软件光栅 + 文本

  * 图像 + 离屏表面），GPU 后端后置。

**决策变更（对既有规划）**：[ui-framework.md §2.2](ui-framework.md)「无软件光栅化」
原决策是绘制指令委托系统 API（桌面 GDI/Direct2D、嵌入式帧缓冲、浏览器 Canvas）。
p.6.8 改为：**桌面绘制统一走自建 Skia 子集**（软件光栅 + 后续 GPU），嵌入式帧缓冲
直绘与 webui Canvas 桥保持可选项不变。理由：一套引擎跨平台一致渲染（Win32/X11/
Wayland 输出同一结果）、高质量抗锯齿/子像素文本、离屏渲染天然可测（CI 友好）。

EN: **Decision change (vs. prior plans)**: ui-framework.md §2.2 "no software
rasterization" delegated drawing to system APIs (GDI/Direct2D on desktop, framebuffer
on embedded, Canvas on browser). p.6.8 changes this to: **desktop drawing goes through
the self-built Skia subset** (software raster, GPU later); embedded framebuffer and
webui Canvas bridge stay as optional. Rationale: one engine renders identically across
platforms (Win32/X11/Wayland), high-quality AA/subpixel text, and offscreen rendering
is naturally testable (CI-friendly).

***

## 2. 策略校准 / Strategy Calibration

对 Skia 能力边界、tie extern 现状、Skia 构建体系深挖得到三个事实，修正了
「拿 Skia 即拿全栈」的直觉设想：

EN: A deep dive into Skia's capability boundary, tie's extern current state, and
Skia's build system yields three facts that correct the intuition "take Skia, get the
full stack":

* **事实一：Skia 是纯渲染库，不提供窗口/事件/显示管理**。Skia 只渲染到 Surface
  （离屏位图或 GPU 纹理）。「全栈图形」= **Skia 渲染核心 + 平台嵌入层**（Flutter
  嵌入模型）：窗口创建、消息泵、事件收集、Surface 呈现由嵌入层（Win32 起步）承担，
  Skia 只负责把命令列表画到后备缓冲。这不会改变「渲染统一」，只是窗口/事件仍需
  平台代码。
  EN: **Fact 1: Skia is a pure rendering library — no window/event/display management.**
  Skia only renders to a Surface (offscreen bitmap or GPU texture). "Full-stack
  graphics" = **Skia rendering core + platform embedding layer** (the Flutter
  embedding model): window creation, message pump, event collection, and surface
  presentation live in the embedding layer (Win32 first); Skia only draws the command
  list into the back buffer. Rendering stays unified; windowing/events still need
  platform code.

* **事实二：Skia 公共 API 是 C++ 类，tie extern 是 C ABI**。类方法无法经 C ABI 直调
  （thiscall/符号修饰），**无论如何都需最小 extern "C" thunk** 把类方法暴露为 C
  入口。「直绑」的落地含义 = tie 侧用 repr(C)/ptr **直接表示 Skia 对象与 C 结构**
  （SkPaint、SkImageInfo、SkRRect 等映射为 repr(C) struct，对象为不透明 ptr），
  而非黑盒 i64 句柄；方法经 thunk 以 C 函数形式 extern 调用。
  EN: **Fact 2: Skia's public API is C++ classes; tie extern is C ABI.** Class methods
  cannot be called through the C ABI directly (thiscall/name mangling), so **a minimal
  extern "C" thunk is unavoidable** to expose class methods as C entry points. "Direct
  binding" lands as: tie represents Skia objects and C structs **directly with
  repr(C)/ptr** (SkPaint, SkImageInfo, SkRRect, ... mapped to repr(C) structs; objects
  as opaque ptrs) — not opaque i64 handles; methods are extern-called as C functions
  through the thunk.

* **事实三：Skia 源码构建体系重（GN/ninja + 第三方库）**。全量 Skia 依赖
  zlib/png/jpeg/webp/icu/harfbuzz 等。精简自建子集必须收窄到**软件光栅 + 文本 +
  图像 + 离屏表面**，编解码器可裁剪（初期只用 PNG/BMP，走 SkCodec 或自解码），
  文本走 SkFont/SkTextBlob（字距/度量），排版（SkParagraph）后置。
  EN: **Fact 3: Skia's build system is heavy (GN/ninja + third-party libs).** Full Skia
  depends on zlib/png/jpeg/webp/icu/harfbuzz, etc. The trimmed subset must narrow to
  **software raster + text + image + offscreen surface**: codecs are cut (PNG/BMP
  only initially, via SkCodec or self-decoding), text uses SkFont/SkTextBlob (kerning/
  metrics), and SkParagraph layout is deferred.

用户决策 / User decisions：全栈图形 + 先扩 unsafe 再直绑 + 精简自建子集（如上）。

***

## 3. 目标与范围 / Goals and Scope

1. **unsafe 语言扩展（Skia 绑定最小集）**：`ptr` 类型化指针 + `repr(C)` 结构体 +
   extern 扩展（ptr 参数/返回值、结构体按引用）。完整 unsafe 模型（切片/asm!/
   alloc-free/ref 通用化）后置。
   EN: **unsafe language extension (Skia-binding minimum)**: typed `ptr` + `repr(C)`
   structs + extern extension (ptr args/returns, struct-by-reference). The full unsafe
   model (slices/asm!/alloc-free/ref generalization) is deferred.

2. **精简 Skia 子集**：源码裁剪只编软件光栅 + 文本 + 图像 + 离屏表面；静态库产物；
   构建脚本 tie 写；GPU 后端（Vulkan/D3D/Metal）后置。
   EN: **trimmed Skia subset**: only software raster + text + image + offscreen
   surface; static-library artifact; tie-written build script; GPU backends
   (Vulkan/D3D/Metal) deferred.

3. **绑定层**：extern "C" thunk（类方法 → C 入口）+ repr(C)/ptr 直表示 +
   命令列表翻译器（D2 → Skia 调用）。
   EN: **binding layer**: extern "C" thunk (class methods → C entries) + repr(C)/ptr
   direct representation + command-list translator (D2 → Skia calls).

4. **全栈图形闭环**：Win32 窗口嵌入层 + 事件系统（E3）+ 主循环 + 脏矩形 + 呈现；
   trm.ui port 抽象面接线。
   EN: **full-stack graphics loop**: Win32 window embedding + event system (E3) +
   main loop + dirty rect + presentation; trm.ui port surface wired.

**非目标 / Non-goals**：GPU 后端（后置）、X11/Wayland 窗口嵌入（后置）、
SkParagraph 复杂文本排版（后置）、Skia 全量编解码器（只用 PNG/BMP）、
webui Canvas 桥改造（保持既有）、tieui 完整组件框架（属 S4.3，p.6.8 只出
组合式布局雏形）。

***

## 4. p.6.8 子项盘子 / Sub-item Plan

| 子项 / Item | 内容 / Content                                                                                                                                                                                                                            | 验收 / Acceptance                                                                                     |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| p.6.8.1   | `ptr` 指针类型：T2 类型化指针 + addr\_of/deref/指针算术 + U3 语法（unsafe 块/函数，文件级逃生舱）；安全代码触碰指针 = 编译错误 / Typed ptr: addr\_of/deref/pointer arithmetic; U3 syntax (unsafe block/function, file-level escape); safe code touching pointers = compile error | 指针探针（取址/解引用/算术/比较）PASS；unsafe 边界外使用 ptr 编译拒绝 / Pointer probes PASS; ptr use outside unsafe rejected |
| p.6.8.2   | `repr(C)` 结构体：R1 显式 ABI 布局（字段偏移精确对齐，对照 C 编译输出）；可整体按引用传 extern；与窄整数模型咬合 / repr(C) structs: explicit ABI layout (field offsets vs C compiler output); passable by reference to extern; interlocks with the narrow-int model               | repr(C) 布局探针对照 C 的 offsetof 全等；按引用传结构体 PASS / Layout probe matches C offsetof; struct-by-ref PASS   |
| p.6.8.3   | extern 扩展：E3 extern 强制 unsafe + ptr 参数/返回值 + 结构体按引用 + string↔char\* / extern extension: extern-forced-unsafe + ptr args/returns + struct-by-ref + string↔char\*                                                                         | 双向 ptr 探针；extern\_move\_check 零回归 / Bidirectional-ptr probe; extern\_move\_check zero regression    |

| 子项 / Item | 内容 / Content                                                                                                                                                                                                                                                                                                                                                                                                         | 验收 / Acceptance                                                                                                          |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| p.6.8.4   | 源码裁剪与构建：收窄到 SkSurface/SkCanvas/SkPaint/SkPath/SkTextBlob/SkFont/SkImage/SkCodec(PNG/BMP) + Raster 软件光栅 + 离屏位图 Surface；构建脚本 tie 写（GN/ninja 或最小 CMake 裁剪，脚本逻辑全 tie）；产物静态库（.a/.lib）/ Source trim + build: narrowed to SkSurface/SkCanvas/SkPaint/SkPath/SkTextBlob/SkFont/SkImage/SkCodec(PNG/BMP) + Raster software rasterizer + offscreen bitmap Surface; tie-written build script; static library (.a/.lib) artifact | 最小 C++ 冒烟：画矩形/文本/图像到离屏位图 → 导出 PNG 成功 / Minimal C++ smoke: draw rect/text/image to offscreen bitmap → PNG export succeeds |
| p.6.8.5   | 模块清单与依赖收窄：源文件/编译宏/第三方依赖清单（zlib 等收窄或系统库）；裁剪后体积基线记录 / Module list + dependency narrowing: source/compile-macro/third-party list (zlib narrowed or system lib); trimmed-size baseline recorded                                                                                                                                                                                                                          | 清单文档化；构建可复现（同一 commit 同一产物字节） / List documented; reproducible build (same commit → byte-identical artifact)              |

| 子项 / Item | 内容 / Content                                                                                                                                                                                                                                                          | 验收 / Acceptance                                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| p.6.8.6   | extern "C" thunk：Skia 类方法 → C 入口（最小手写 + tie 写生成器脚本）；对象 = 不透明 ptr；SkPaint/SkImageInfo 等映射 repr(C) 结构 / extern "C" thunk: class methods → C entries (minimal handwritten + tie-written generator); objects = opaque ptrs; SkPaint/SkImageInfo mapped as repr(C) structs | thunk 冒烟：tie 程序经 extern 画线到离屏表面并导出校验 / Thunk smoke: tie program draws a line offscreen via extern and exports for validation |
| p.6.8.7   | trm.ui.gfx 句柄层：repr(C) 句柄 struct（SkCanvas/SkPaint/SkPath/...）+ 方法绑定（obj.method() 转发）+ 生命周期（显式 release / arena）/ trm.ui.gfx handle layer: repr(C) handle structs + method binding (obj.method() forwarding) + lifecycle (explicit release / arena)                     | 句柄探针（创建/使用/释放）；move 语义零回归 / Handle probe (create/use/release); move semantics zero regression                                |
| p.6.8.8   | 命令列表翻译器：D2 Paint Commands → Skia 调用（rect/text/path/image）+ font\_measure 文本度量桥 / Command-list translator: D2 Paint Commands → Skia calls (rect/text/path/image) + font\_measure text-metrics bridge                                                                   | 命令列表离屏渲染逐像素/哈希校验一致 / Offscreen command-list render hash-exact                                                                |

| 子项 / Item | 内容 / Content                                                                                                                                                                                                                                | 验收 / Acceptance                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| p.6.8.9   | 窗口嵌入层（Win32 起步）：CreateWindow + 消息泵 + 后备缓冲 Surface（离屏位图）+ 呈现（blit 上屏）/ Window embedding (Win32 first): CreateWindow + message pump + back-buffer Surface (offscreen bitmap) + presentation (blit)                                            | 窗口显示 + 后备缓冲绘制正确 / Window shows; back-buffer drawing correct                                          |
| p.6.8.10  | 事件系统 E3：事件队列（鼠标/键盘，含位置/键码/时间戳）+ 信号标志（WM\_PAINT→重绘、WM\_TIMER→定时）/ Event system E3: event queue (mouse/keyboard with pos/keycode/timestamp) + signal flags (WM\_PAINT→redraw, WM\_TIMER→timer)                                                | 事件驱动探针（移动/点击/按键 → 队列） / Event-driven probe (move/click/key → queue)                                  |
| p.6.8.11  | 主循环与呈现：主循环整合 + 脏矩形重绘 + 帧节流/vsync；trm.ui port 抽象面接线（api 面 = Window/Painter/EventSource） / Main loop + presentation: main-loop integration + dirty-rect redraw + frame throttle/vsync; trm.ui port surface wired (Window/Painter/EventSource) | 帧率/脏矩形正确；port 双实现（Skia/离屏）可切换 / Frame/dirty-rect correct; port dual impl (Skia/offscreen) switchable |
| p.6.8.12  | 全栈演示：窗口 + 命令列表绘制（矩形/文本/路径/图像）+ 事件响应 + 组合式布局雏形（row/column 嵌套）/ Full-stack demo: window + command-list drawing (rect/text/path/image) + event response + composable-layout seed (row/column nesting)                                          | 演示程序运行交互正常 / Demo runs and interacts correctly                                                       |

| 子项 / Item | 内容 / Content                                                                                                                                                                                                                  | 验收 / Acceptance                                          |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| p.6.8.13  | 验收矩阵：无窗口离屏渲染探针（CI 可跑，逐像素/哈希）+ 窗口演示 + 自举/回归 + 软件光栅性能基线（vs GDI） / Acceptance matrix: windowless offscreen-render probes (CI-runnable, hash-exact) + window demo + bootstrap/regression + software-raster perf baseline (vs GDI) | 全 PASS、exit 0、基线记录 / All PASS, exit 0, baseline recorded |
| p.6.8.14  | 收尾：preview\.4、README/CHANGELOG、已知限制清单（GPU/X11/SkParagraph 后置）、双语文档 / Wrap-up: preview\.4, README/CHANGELOG, known-limits list (GPU/X11/SkParagraph deferred), bilingual docs                                                  | 自举核验 + 零回归 / Bootstrap verify + zero regression          |

***

## 5. 依赖主线 / Dependency Line

p.6.8.1-6.8.3（unsafe）→ p.6.8.4-6.8.5（Skia 库）→ p.6.8.6-6.8.8（绑定）→
p.6.8.9-6.8.12（全栈）→ p.6.8.13-6.8.14（验收发布）。p.6.8.1-6.8.3 与 p.6.8.4-6.8.5
**可并行**（语言扩展与 Skia 构建互不依赖）；p.6.8.6-6.8.8 依赖前两者；
p.6.8.9-6.8.12 依赖 p.6.8.6-6.8.8；p.6.8.7/8 依赖 p.6.8.6。

EN: p.6.8.1-6.8.3 (unsafe) → p.6.8.4-6.8.5 (Skia lib) → p.6.8.6-6.8.8 (binding) →
p.6.8.9-6.8.12 (full stack) → p.6.8.13-6.8.14 (acceptance/release). p.6.8.1-6.8.3 and
p.6.8.4-6.8.5 proceed **in parallel** (language extension vs Skia build are independent);
p.6.8.6-6.8.8 depends on the former two; p.6.8.9-6.8.12 depends on p.6.8.6-6.8.8;
p.6.8.7/8 depend on p.6.8.6.

***

## 6. 风险与对策 / Risks & Mitigations

* **unsafe 扩展是编译器大手术（M0 面）**：ptr/repr(C)/extern 触及 semantic/irgen/
  llvmgen 全链路 → **只做 Skia 绑定最小集**，完整 unsafe 模型后置；先正确后性能；
  探针先行、自举字节不动点把关。
  EN: the unsafe extension is major compiler surgery (M0 surface) → do only the
  Skia-binding minimum, defer the full unsafe model; correctness first; probes first,
  bootstrap byte-fixpoint gate.

* **repr(C) 布局偏差（ABI 不一致）**：字段对齐/偏移与 C 编译器不符 → 布局探针
  对照 C 的 offsetof 输出逐字段全等，纳入 CI。
  EN: repr(C) layout drift (ABI mismatch) → layout probe compares each field against
  C's offsetof output, in CI.

* **Skia 源码构建环境重**：GN/ninja + 第三方库下载/版本 → 精简裁剪 + 依赖收窄
  （初期 PNG/BMP、zlib 复用系统或裁剪）；构建脚本 tie 写；构建复现探针（同 commit
  同字节）。
  EN: heavy Skia source build → trimmed subset + narrowed deps (PNG/BMP first, zlib
  reused system or trimmed); tie-written build script; reproducibility probe.

* **thunk 手写量大易错**：类方法多、签名杂 → 最小必要面（先 Canvas/Paint/Path/
  Font/Image 的核心绘制子集）+ tie 写 thunk 生成器，签名集中登记。
  EN: large hand-written thunk surface → minimal necessary set (core drawing subset of
  Canvas/Paint/Path/Font/Image) + tie-written thunk generator with centralized
  signature registry.

* **窗口开发与 CI 解耦**：Win32 窗口不可在无头 CI 跑 → 离屏渲染探针先行（p.6.8.6-6.8.8
  起即可全 CI），窗口演示（p.6.8.9-6.8.12）作为人工/本地验收。
  EN: window dev decoupled from CI → offscreen probes from p.6.8.6-6.8.8 are fully
  CI-runnable; the window demo (p.6.8.9-6.8.12) is manual/local acceptance.

* **全栈图形范围大**：渲染 + 窗口 + 事件一次闭环易失焦 → 分四组子项严格验收，
  每组独立可交付（语言扩展 p.6.8.1-6.8.3 / 库 p.6.8.4-6.8.5 / 绑定 p.6.8.6-6.8.8 /
  闭环 p.6.8.9-6.8.14 各自有探针与演示）。
  EN: broad full-stack scope → four strictly-gated sub-item groups, each independently
  deliverable (language ext p.6.8.1-6.8.3 / lib p.6.8.4-6.8.5 / binding p.6.8.6-6.8.8 /
  loop p.6.8.9-6.8.14 each with probes and a demo).

***

## 7. 相关文档 / Related Documents

* `docs/plans/ui-framework.md`（UI 框架 + unsafe 模型决策；M0/M1/M2 里程碑；§2.2
  被本模块修订 / UI framework + unsafe decisions; M0/M1/M2 milestones; §2.2 revised
  here)

* `docs/plans/tucore-arch.md`（trm.ui 域：D2 命令列表 / H2 句柄 / E3 事件+信号 /
  L1 生命周期 / F3 字体——本模块落地其绘制面 / trm.ui domain: D2 command list / H2
  handles / E3 events+signals / L1 lifecycle / F3 fonts — this module lands its
  drawing surface)

* `docs/plans/roadmap.md`（S4.2 trm.ui / S4.3 tieui / S4.5 嵌入式）

* 落地仓库 / Landing repo：`tie-main/`（compiler/ 的 unsafe 扩展 + ext/gfx/ 的
  Skia 绑定与全栈图形，后续并入 trm.ui）

***

## 8. 决策记录 / Decision Log

| 决策点 / Point         | 结论 / Conclusion                                                            | 备选（未选）/ Alternatives   |
| ------------------- | -------------------------------------------------------------------------- | ---------------------- |
| Skia 范围             | **全栈图形**：渲染+窗口+事件（Flutter 嵌入模型：Skia 渲染核心 + 平台嵌入层）                          | 仅绘制后端、离屏渲染+合成          |
| 绑定方式                | **先扩 unsafe 再直绑**：ptr/repr(C) 直表示 Skia 对象 + 最小 extern "C" thunk（类方法须 C 入口） | 官方 C API（面窄）、黑盒 i64 句柄 |
| Skia 来源             | **精简自建子集**：软件光栅+文本+图像+离屏表面；GPU 后置                                          | 预编译二进制、源码全量            |
| 对 ui-framework §2.2 | **修订**：桌面绘制统一走自建 Skia 子集；嵌入式帧缓冲/webui Canvas 保持可选                          | 维持 GDI/Direct2D 委托     |
| unsafe 扩展范围         | 仅 Skia 绑定最小集（ptr/repr(C)/extern）；切片/asm!/alloc-free 后置                     | 完整 unsafe 模型一次做        |
| 文本排版                | SkFont/SkTextBlob（度量+绘制）；SkParagraph 后置                                    | 直接上 SkParagraph        |
| 图像编解码               | 初期 PNG/BMP（SkCodec 或自解码）；全量编解码器后置                                          | 全量 codecs              |
| 落地位置                | tie-main：compiler/（unsafe）+ ext/gfx/（Skia），后续并入 trm.ui                     | 独立 gfx 仓库              |

