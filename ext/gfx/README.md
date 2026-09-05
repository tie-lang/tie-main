# tie gfx · Skia 裁剪（p.6.8.4） / Trimmed Skia graphics layer

本目录承载 p.6.8.4「精简自建 Skia 子集」：把 Google Skia（chrome/m120）裁剪到
**软件光栅 + 文本 + 图像 + 离屏表面**，产物为静态库（Release x64 MSVC）。
全部构建逻辑用 tie 语言编写；仅 Skia 裁剪库本体为第三方 C++ 源码。

EN: This directory hosts the p.6.8.4 trimmed Skia subset: Google Skia (chrome/m120)
cut down to **software raster + text + image + offscreen surface**, shipped as a
static library (Release x64 MSVC). All build logic is written in tie; only the
trimmed Skia library itself is third-party C++ source.

---

## 固定版本 / Pinned version

| 项 | 值 | 说明 |
| --- | --- | --- |
| 分支 | `chrome/m120` | 2023 后期稳定里程碑，早于 base/abseil 硬化，第三方依赖最少。EN: late-2023 stable, pre base/abseil, fewest deps |
| Commit | `77fe8841d9ec287eeb3d3f70fc0a674162664064` | 固定提交（tarball 来源）。EN: pinned commit (tarball source) |
| gn | Chromium CIPD `gn/gn/windows-amd64` latest | `bin/fetch-gn` 等价，见 manifest `[gn]` |
| 编译器 | MSVC 14.51（VS2026/18 Community，vcvarsall x64） | 备用 clang-cl（D:\LLVM\bin\clang-cl.exe） |
| ninja | 1.12.0（C:/Strawberry/c/bin/ninja.exe） | 由 manifest `[ninja]` 指定 |

EN: Pinned to chrome/m120 @ the commit above; gn from Chromium CIPD; MSVC 14.51; ninja 1.12.

第三方依赖（externals）收窄到 **两项**，其余全部裁剪关闭（全量 DEPS 拉取达数 GB，此处
不取）：EN: Third-party externals narrowed to **two**, the rest disabled (a full DEPS
pull is multi-GB and avoided):

| 依赖 | 作用 | 固定提交 |
| --- | --- | --- |
| zlib（chromium 版） | PNG 压缩 / Skia 内部 | `c876c8f87101c5a75f6014b0f832499afeb65b73` |
| libpng（pnggroup） | SkPngCodec/编码 | `386707c6d19b974ca2e3db7f5c61873813c6fe44` |

（skcms 在 m120 内嵌于 `modules/skcms/`，非 external，无需单独拉取。）
EN: (In m120 skcms is vendored under `modules/skcms/`, not an external.)

---

## 裁剪模块清单（p.6.8.5 补全）/ Trimmed module list

**机器生成的详细清单：`ext/gfx/lib/modules.txt`**（34 源目录分组、552 编译单元，由
`ext/gfx/skia/modlist.tie` 扫描构建 out/obj 目录自动产出）。EN: Machine-generated
detail list is `ext/gfx/lib/modules.txt` (34 source-directory groups, 552 compile
units), produced by `ext/gfx/skia/modlist.tie` from the build obj dir.

保留的 API / 类：EN: Retained API / classes:
- 离屏表面：`SkSurface::MakeRaster` / `SkSurfaces::Raster`（N32 premul 8888 位图 Surface）
  EN: offscreen raster Surface.
- 绘制：`SkCanvas`(drawColor/drawRect/drawImage/drawTextBlob)、`SkPaint`
- 形状：`SkPath`、`SkRect`；文本：`SkFont` + `SkTextBlob`（DirectWrite 字体管理器）
- 图像：`SkImage` / `SkBitmap` / `SkPixmap`；编解码：`SkCodec`（PNG+BMP，走 libpng+zlib）
- 编码导出：`SkPngEncoder::Encode`

**模块分组概述（modules.txt 分组标题同名，行数见文件）** EN: Module groups at a glance:
- **src/core**（192）——软件光栅核心：Canvas/RasterPipeline/SkOpts(SIMD 变体)/Blitter/
  Scan/Path/TextBlob/Paint/Typeface/Text（SkText 文本内联在 core）。
- **src/base**（24）——分配器/基础容器/UTF/Math 基元；**src/image**（14）——Image &
  Surface（Raster/Null）；**src/effects**（15 + colorfilters 9 + imagefilters 17）；
  **src/shaders**（17）+ gradients（5）。
- **src/pathops**（32）——路径运算 Op/Simplify；**src/codec**（25）——SkCodec + 各
  位图编解码（PNG 走 libpng，BMP/WBMP/ICO 内置）；**src/encode**（3）——SkPngEncoder。
- **src/ports**（13）——win32（DWrite 字体/Debug/OSFile）端口 + GDI/内存端口；
  **src/utils/win**（7）——DWrite 桥；**src/utils**（28）+ utils/mac（2，无操作桩）；
  **src/fonts**（1）+ **src/sfnt**（2）——字体表。
- **src/sksl**（20 + analysis 15 + ir 45 + transform 12 + tracing 3 + codegen 2）——
  SkSL 着色器 DSL 骨架（软件光栅需要）；**src/opts**（1）、**src/lazy**（1）、
  **src/text**（3）、**src/pdf**（1，`SkDocument_PDF_None` 空桩）。
- **modules/skcms**（1）——色彩管理（内嵌）。**src/android**（2）+ client_utils/android（2）
  与 utils/mac 类似为跨平台编译单元（无实际 backend）。
- **third_party/externals/libpng**（15 + intel 2）、**zlib**（19 + contrib/optimizations 2）
  ——第三方两项依赖（下节）。

**是否含 src/gpu：否** EN: **src/gpu is NOT included**——`skia_enable_gpu=false`，
obj 目录无 `gpu/` 子目录，`modules.txt` 末尾 `GPU_src/gpu_present=no` 确认。

**工程级编译宏要点**（GN args 已全列于 manifest；此处说明关键 define 生效状态）：
EN: Engine-level compile macros: 
- `SK_SUPPORT_GPU` / `SK_GANESH` / `SK_GPU_VENDOR_*` **未定义**（无 GPU 后端）。
- `SK_FONTMGR_WIN`（DirectWrite 字体管理器）**定义**（=1）；`skia_enable_fontmgr_win` 经
  GN true。载入 `src/ports/fontmgr_win*`。
- `SK_HAS_LIBPNG_LIBRARY` + `SK_CODEC_DECODES_PNG`/`SK_CODEC_ENCODES_PNG` 定义
  （libpng encode+decode 均开）；`SK_HAS_ZLIB` 定义。
- `SK_HAS_JPEG/WEBP/WUFFS` 未定义（对应 GN=false，编解码关闭，无 libjpeg/libwebp）。
- `SK_DISABLE_LEGACY_TYPOGRAPHY`、`SK_DISABLE_LEGACY_MATH` 等由 GN 默认；`SK_ENABLE_DISCRETE_GPU`
  等 GPU 相关宏不定义。细节以 manifest `[args]` / `args.gn` 为准。

### 最终生效 GN args（归档自 manifest.txt `[args]`） / Effective GN args

```
target_cpu="x64"
is_debug=false
is_official_build=false
is_component_build=false
skia_enable_gpu=false
skia_use_gl=false
skia_use_dawn=false
skia_use_vulkan=false
skia_use_metal=false
skia_use_angle=false
skia_use_icu=false
skia_use_harfbuzz=false
skia_use_expat=false
skia_use_jpeg_gainmaps=false
skia_use_libjpeg_turbo_decode=false
skia_use_libjpeg_turbo_encode=false
skia_use_libwebp_decode=false
skia_use_libwebp_encode=false
skia_use_wuffs=false
skia_use_libpng_decode=true
skia_use_libpng_encode=true
skia_use_zlib=true
skia_use_system_libpng=false
skia_use_system_zlib=false
skia_use_freetype=false
skia_use_xps=false
skia_enable_skottie=false
skia_enable_svg=false
skia_enable_pdf=false
skia_enable_skparagraph=false
skia_enable_skshaper=false
skia_enable_tools=false
skia_enable_spirv_validation=false
extra_cflags=["/Brepro"]
extra_ldflags=["/Brepro"]
```

GN `gen` 本组参数零警告生效（95 targets / 41 files）。`[args]` 现含确定性构建开关
`extra_cflags/extra_ldflags=["/Brepro"]`（p.6.8.5，见下节）。EN: These GN args gen with
zero warnings; `extra_cflags/extra_ldflags=["/Brepro"]` added for determinism (p.6.8.5).

---

## 构建命令（全部经 build.tie） / Build commands (all via build.tie)

先按 tie 编译 `build.tie`：EN: First compile the tie driver:
```
compiler\tiec.exe ext\gfx\skia\build.tie -o ext\gfx\skia\build.exe
```
然后（仓库根运行）：EN: then (run from repo root):

| 命令 | 作用 |
| --- | --- |
| `ext\gfx\skia\build.exe` | 默认构建：ensure(gn/skia/externals) → gn gen → ninja → 拷贝 `ext/gfx/lib/skia.lib` → 写状态；已是最新则跳过 |
| `ext\gfx\skia\build.exe --force` | 强制重建（覆盖幂等跳过） |
| `ext\gfx\skia\build.exe --gen` | 仅 gn gen（写 out/tie_raster_release/args.gn） |
| `ext\gfx\skia\build.exe --smoke` | 编译链接+运行冒烟，校验 PNG（魔数/尺寸/字节数） |
| `ext\gfx\skia\build.exe --check` | 打印版本/产物体积/状态 |
| `ext\gfx\skia\build.exe --clean` | 删除 out 构建目录与状态 |
| `ext\gfx\skia\modlist.exe` | 扫描 out/obj → 重生成 `ext/gfx/lib/modules.txt`（模块清单） |

EN: default builds (idempotent), `--force` rebuild, `--gen` gn gen only, `--smoke`
compile+run+validate PNG, `--check` status, `--clean` remove out dir.

`build.tie` 经 `process.exec_code`（→ libc `system` → cmd.exe）执行 vcvarsall、gn、ninja、
cl 等外部命令；MSVC 环境统一由脚本注入（`call <vcvarsall> x64`）。幂等基于外部产物
`ext/gfx/lib/skia.lib` 存在 + `out/tie_raster_release/.build_state` 指纹与 manifest 一致。

EN: build.tie drives vcvarsall/gn/ninja/cl via process.exec_code; idempotent via the
`skia.lib` artifact + a `.build_state` fingerprint matching the manifest.

---

## 产物与体积基线 / Artifact & size baseline

- 静态库：`ext/gfx/lib/skia.lib`（Release x64，MSVC `/MT`，552 编译单元 / 556 目标）。
- **体积基线：168,338,664 字节（≈160.5 MiB）**——为启用 `/Brepro` 确定性后实测值
  （p.6.8.5），由 169,329,356 减少 ≈991 KB（去除 codeview 时间戳/绝对路径注入）；
  记录于 `ext/gfx/skia/manifest.txt [size]` 与 README/CHANGELOG。
  EN: Size baseline: **168,338,664 bytes** (~160.5 MiB) after /Brepro ~991 KB smaller.
- 冒烟可执行：`ext/gfx/skia/smoke/skia_smoke.exe` = 2,761,728 B。
- 冒烟输出：`ext/gfx/skia/smoke/out/smoke.png`（320x200，2768 B，魔数
  `89504e470d0a1a0a` 校验通过）。EN: smoke exe 2,761,728 B; PNG 320x200 2768B, magic verified.

构建输出目录 `out/tie_raster_release/`、`.tools/`、冒烟 `out/` 均为本地产物，不入库。
EN: `out/tie_raster_release/`, `.tools/`, smoke `out/` are local artifacts, not committed.

---

## 第三依赖收窄结论 / Third-party narrowing

p.6.8.5 核实：**zlib 为 libpng 的硬依赖**（libpng 压缩/解压底层调 zlib inflate/deflate），
故 `skia_use_zlib=true` 无法在保留 PNG 编解码的前提下移除——**zlib + libpng 两项已是
本裁剪集的最小闭包**，不再压缩（不强行去除引入编译/运行风险）。

EN: zlib is a hard dependency of libpng (libpng calls zlib inflate/deflate), so zlib
cannot be dropped while keeping the PNG codec. **zlib + libpng is already the minimal
closure** for this trimmed set; no further narrowing (dropping would add risk).

- 仅保留 PNG/BMP 编解码（`skia_use_libpng_decode/encode=true`、`skia_use_zlib=true`）；
  JPEG/WebP/Wuffs/HEIF 等 `=false`，故不引入 libjpeg/libwebp/libgav1。
- PNG encode（`SkPngEncoder`）为本模块冒烟导出路径所需，与 decode 均保留。
- 其余 HEIF/AVIF 相关目标为空（`heif`/`avif` phony 无依赖，`SkHeifCodec` 为空桩）。

EN: Only PNG/BMP codecs kept (JPEG/WebP/Wuffs off → no libjpeg/libwebp); PNG encode kept
for SkPngEncoder; HEIF is an empty stub.

---

## 模块清单（modules.txt）/ Module manifest

- `ext/gfx/lib/modules.txt`：34 源目录分组、552 编译单元、`TOTAL_OBJ`/`TOTAL_MODULE_GROUPS`/
  `GPU_src/gpu_present=no` 汇总，由 `ext/gfx/skia/modlist.tie`（tie 写，`dir /s /b` 枚举 +
  `str.split`）扫描构建 out 生成。
- 分组：`src/core`192、`src/base`24、`src/codec`25、`src/effects`(+colorfilters+imagefilters)、
  `src/image`14、`src/pathops`32、`src/ports`13、`src/shaders`(+gradients)、`src/sksl`
  (+analysis/ir/transform/tracing/codegen)、`src/encode`3、`src/utils`(+win/mac)、
  `src/fonts`+`src/sfnt`、`src/opts`、`src/lazy`、`src/text`、`src/pdf`(空桩)、
  `src/android`/`client_utils/android`、modules/skcms、third_party/externals/{libpng,zlib}。

---

## 构建可复现 / Reproducible build

同一 manifest（同一 commit + 同一 GN args）应产出同一产物。p.6.8.5 落地与实测：

- **确定性开关**：`[args] extra_cflags=["/Brepro"]` + `extra_ldflags=["/Brepro"]`（MSVC
  确定性编译/链接）。verify：.obj 与 PE 产物中的 codeview 时间戳、绝对路径注入、
  生成的 GUID 被消除，obj 产物字节不随重建墙钟漂移；lib 体积 169329356→168338664。
- **可复现探针**：`tests/p685_probe/p685_probe.tie`——读 manifest（断言已开 /Brepro），
  记录 skia.lib SHA256 → `build.exe --clean` + `--force` 干净重建 → 再算 SHA256 → 校验；
  再跑默认构建验幂等。hash 经系统 `certutil -hashfile <f> SHA256` 计算（tie 直接读大
  lib 有 byte_read 缺陷，见已知限制）。干净重建约 60s。
- **已知取舍（Level-2 幂等下界）**：整库字节级一致**不可达**——MSVC `lib.exe`（GN alink
  规则）把每个 .obj 的修改时间写进 COFF 归档成员头的 Date 字段，`/Brepro` 无法改写
  lib.exe 的归档时间戳；两个不同时刻的干净重建仅成员头时间戳字节不同、.obj 代码一致。
  故验收取「相同输入的 ninja 增量重建不产出新字节」为幂等下界（再跑 build = no-op，
  lib SHA256 不变）——探针断言该下界通过（asserts=9，PASS，exit 0）。若工具链升级为可
  输出无时间戳归档，Level-1 字节一致分支会自动接过。

EN: /Brepro determinism enabled; reproducibility probe sits at tests/p685_probe; whole-lib
byte-identity across clean rebuilds is **not** achievable because MSVC lib.exe writes each
member's obj mtime into the archive header (no lib.exe /Brepro). Accepted lower bound:
an incremental rebuild of identical input produces no new bytes (re-`build` is a no-op,
lib SHA256 stable). Probe: 9 asserts PASS / exit 0.

---

## 清单与仓库纪律 / Manifest & repo hygiene

- `ext/gfx/skia/manifest.txt`：单一事实源（版本/依赖固定提交/toolchain/GN args/体积），
  build.tie 经 `cfg.parse_kv` 解析（INI 节 → `节.键`）。
- 第三方源码与二进制不入库：`.gitignore` 忽略 `ext/gfx/skia/`（源码树）与
  `ext/gfx/lib/`（二进制）；白名单保留 `build.tie` / `manifest.txt` / `smoke/smoke.cpp` /
  `modlist.tie` / `lib/modules.txt`。

EN: manifest.txt is the single source of truth, parsed by build.tie. .gitignore excludes
the third-party tree and lib binary, whitelisting our authored files: build.tie,
manifest.txt, smoke/smoke.cpp, modlist.tie, lib/modules.txt.

---

## 已知边界 / Known limits

- 仅 PNG/BMP 编解码（JPEG/WebP/GIF/RAW 等关闭）。EN: PNG/BMP codecs only.
- 文本走 DirectWrite（`skia_enable_fontmgr_win`）；静态 exe 退出期有 DWrite 字体管理器
  静态析构访问违例怪癖，冒烟以 `ExitProcess` + `start /b` 分离运行绕开（输出完整）。
  报告见最终交付（供 p.6.8.6+ 嵌入层参考）。EN: DirectWrite text; static-exe exit-time
  DWrite teardown quirk worked around in smoke (ExitProcess + detached `start /b`).
- `tie` 的 `byte_read` 对本 PNG 中段字节内容触发访问违例（tie stdlib 二进制读取缺陷，
  非本模块）；冒烟改以文本标记校验绕开，已上报主代理。EN: tie `byte_read` crashes on
  this PNG's middle bytes (tie stdlib bug, out of scope); smoke validates via a text marker.
- `tie` 对 `fs.walk`/`fs.read_dir` 返回的 `table<string>` 做 `[]` 元素读取会触发启动期
  访问违例/非法句柄崩溃（p.6.8.5 RCA）；`fs` 与 `sort` 同程序 co-import 在较大负载下
  亦崩溃。modlist.tie 改以 `process.exec_output` 枚举 + `str.split` 自建表避开；探针内联
  排序。EN: tie crashes on `[i]` element reads of `fs.walk`/`fs.read_dir` result tables,
  and on fs+sort co-import at higher load (p.6.8.5 RCA); modlist avoids it via
  `exec_output` + `str.split`; probe inlines its own sort (no sort import).
- MSVC 整库字节级可复现受限（见「构建可复现」节）：`lib.exe` 在 COFF 归档成员头写入
  obj mtime，`/Brepro` 不能改写 → 整库跨时刻 clean-rebuild 字节不一致；以幂等下界验收。
  EN: whole-lib byte-identity across clean rebuilds not achievable (lib.exe archive mtime);
  reproducible-build acceptance uses the idempotency lower bound.

---

## p.6.8.6 extern "C" thunk 绑定 / extern "C" thunk binding layer

本子项把 Skia 类方法经最小手写 extern "C" 面暴露为 C 入口，使 tie 程序可 **经
`unsafe extern fn` 直绑 Skia** 离屏画线（p.6.8.1-6.8.3 语言能力 + p.6.8.4 库的汇聚点）。
全部 thunk/构建/生成器逻辑用 tie 编写。EN: This sub-item exposes Skia class methods
as C entry points via a minimal handwritten extern "C" thunk so a tie program can
**direct-bind Skia through `unsafe extern fn`** for offscreen drawing — the convergence
of the p.6.8.1-6.8.3 language abilities with the p.6.8.4 library.

### thunk 面（C 入口清单）/ C entry-point surface

源码：`ext/gfx/skia/thunk/thunk.h` + `thunk.cpp`。对象一律不透明 `ptr<u8>`；canvas
由 surface 拥有、不单独释放；`sk_obj_release(obj, kind)` 统一回收。

| C 入口 | 作用 / Purpose |
| --- | --- |
| `sk_surface_create(w,h)` | `SkSurfaces::Raster` N32 premul 8888 → Surface |
| `sk_surface_canvas(s)` | Surface → Canvas（借出） |
| `sk_surface_snapshot(s)` | Surface → Snapshot Image |
| `sk_surface_peek_pixels(s, info*)` | 回读底层像素/信息（TSkImageInfo） |
| `sk_image_encode_png(img, len*)` | `SkPngEncoder::Encode` → SkData |
| `sk_data_bytes(data)` | SkData → 原始字节缓冲指针 |
| `sk_data_write_file(data, path)` | 写 PNG（wb + fflush 同步） |
| `sk_canvas_clear(c, color)` | 清屏 |
| `sk_canvas_draw_line/rect(...)` | 取扁平 TSkPaint → SkPaint 绘制 |
| `sk_obj_release(obj, kind)` | 释放 Surface/Image/Data |
| `sk_flush_std()` | `fflush(stdout/stderr)`：`ExitProcess` 前落盘，保住探针报告 |

EN: All objects are opaque `ptr<u8>`; canvas is owned by the surface; `sk_obj_release`
frees Surface/Image/Data; `sk_flush_std` flushes stdio before `ExitProcess`.

### 扁平 repr(C) 结构 / flat repr(C) structs

`TSkPaint`（color u32 / style i32 / antialias i32 / stroke_width f64，
offset 0/4/8/16，size 24，align 8）——**不镜像 SkPaint C++ 位域布局**，改传扁平描述，
thunk 内部转 SkPaint，规避 C++ 布局脆弱面。`TSkImageInfo`（width/height/color_type/
alpha_type/row_bytes int + pixels i64 地址，offset 0..24/32）。布局经
`tests/p686_probe/ref.c` 对照 clang/MSVC `offsetof` 核验（探针写死期望）。
EN: `TSkPaint` and `TSkImageInfo` are flat repr(C) structs mirrored in tie, verified
against C `offsetof` by `tests/p686_probe/ref.c`.

### 生成器机制 / generator（签名集中登记）

`ext/gfx/skia/thunk/gen_thunk.tie` 持有**静态签名登记表**（C 名 → 参数/返回类型表），
运行后生成 tie 侧绑定模块 `ext/gfx/thunk_binding.tie`（repr(C) 结构 + `unsafe extern fn`
声明）；探针 `import "../../ext/gfx/thunk_binding.tie" as tb` + `using tb;` 使用。
`--emit-c` 额外打印 C 头片段供人工对照 `thunk.h`；机器级一致性由探针 thunk 调用 +
布局 ref.c 兜底。**改 thunk.h 必同步登记表/生成器，再生成绑定**。
EN: `gen_thunk.tie` holds the central signature registry and generates
`ext/gfx/thunk_binding.tie` (structs + extern declarations) for probes to `using`.
`--emit-c` prints a C-header fragment for manual cross-check against `thunk.h`.

### 构建与运行（tie 驱动）/ build & run (tie-driven)

```
compiler\tiec.exe ext\gfx\skia\thunk\build_thunk.tie -o ext\gfx\skia\thunk\build_thunk.exe
ext\gfx\skia\thunk\build_thunk.exe     # 仓库根运行：生成绑定→thunk.obj→探针obj→链接→运行
```
build_thunk.tie 链路：生成绑定 → `clang-cl /MT` 编译 thunk.cpp → tiec `--emit-ir` +
`clang -c` 编探针 → `clang -fuse-ld=link` 链接（探针.obj + thunk.obj + skia.lib）→ 运行。
EN: build_thunk.tie: gen binding → clang-cl /MT thunk.obj → probe.obj → clang link with
skia.lib → run probe.

**链接所需系统库 / required system libs**（随 linker 报错补齐后固化，见 build_thunk.tie）：
`user32 gdi32 shell32 dwrite ole32 oleaut32 advapi32 windowscodecs`
`+ compiler-rt`（i128 除法辅助）；CRT 用静态 `/MT` 与 skia.lib 一致，避免混链。
EN: `user32 gdi32 shell32 dwrite ole32 oleaut32 advapi32 windowscodecs` + compiler-rt;
static /MT CRT matches skia.lib.

### 验收探针 / acceptance probe

`tests/p686_probe/p686_probe.tie`：96x48 离屏 Surface → clear 白 → 红矩形 fill →
蓝竖粗线 + 绿对角（drawLine）→ peek 逐像素断言（背景/矩形中心/线中心纯色、对角区域
计数）→ snapshot → PNG 编码（魔数 `89504e470d0a1a0a` + IHDR 尺寸 96x48 逐字节回读）→
落盘 `tests/p686_probe/out.png` → 全释放 → `ExitProcess` 确定性退出。**asserts=27，PASS /
exit 0**，探针 exe≈2.77 MB、运行≈50 ms。像素读回与 PNG 字节校验走 **ptr 解引用**
（不经 std `byte_read`）。
EN: tests/p686_probe renders offscreen, validates pixels/PNG byte-level, exit 0 on full
PASS (27 asserts); pixel + PNG validation use direct ptr deref, not std byte_read.

### 已知链路风险与规避 / known pipeline risks & mitigations

- **DirectWrite teardown 访问违例**：静态 exe 退出期静态析构崩溃（p.6.8.4 冒烟发现）——
  探针打印后用 `sk_flush_std()` + `ExitProcess(code)` 确定性退出；PNG 先 `fflush` 落盘。
  EN: probe exits via ExitProcess after sk_flush_std to avoid the DWrite teardown crash.
- **tie `byte_read` + 表元素 `t[i]` 访问违例**：复现确认——本探针 281 字节 PNG 上
  `byte_read` 成功返回但 `b[0]` 元素读取触发 0xC0000005（table `<i64>` 运行时桥边界，
  与 p.6.8.4 记录一致；同族于 p.6.8.5 记录的 fs 表元素读取崩溃）。**已上报，待独立修复**
  （建议新增 bug 子项：编译器 `tig_byte_read` 手工组表头式与新表运行时布局不对齐，需
  编译器改动 + 自举核验）。探针 **故意不经 byte_read**，改对返回的 SkData 缓冲 ptr 直接
  解引用逐字节校验（校验的是编码器实际产出字节，更鲁棒）。EN: reproduced byte_read
  element-read access violation; probe deliberately validates the SkData buffer via ptr
  deref instead and reports the defect upstream.

---

## p.6.8.7 trm.ui.gfx 句柄层 / trm.ui.gfx handle layer

本子项在 p.6.8.6 thunk 之上加**句柄层**（`ext/gfx/gfx.tie`，`type tie<class>` 模块）：对象以
repr(C) 句柄 struct 表示，方法转发 + 显式 release / arena 生命周期。EN: builds the handle layer
on the p.6.8.6 thunk — objects are repr(C) handle structs, with forwarding + explicit release / arena.

### repr(C) 句柄 / repr(C) handle structs

Surface / Canvas / Path / Image = `repr(C) struct { var h: i64 }` 包裹不透明 C 指针地址
（repr(C) 字段不支持 `ptr<T>`，用 i64 存地址，跨 FFI `int_to_ptr` 还原）；Paint 为扁平 repr(C)
描述（对齐 thunk 的 `TSkPaint`，非 Skia 堆句柄）；Pixels / Encoded 为扁平回读结构。
EN: handles wrap i64 addresses (repr(C) forbids ptr<T>); Paint is the flat TSkPaint-style desc.

### 方法转发形态 / method-binding form（obj.method() 与函数转发）

tie 支持 struct 实例方法（`infer_struct_method` + M2.1.8 首参自动按引用），但**方法符号只在
定义模块内注册；跨模块 import 时子命名空间（如 `namespace Canvas`）方法不导出**，探针中
`canvas.clear(...)` 报「Canvas::clear 未定义」；且命名空间函数仅在 namespace == 模块文件名时以
`alias.fn()` 跨模块可达。**实测**（p.6.8.7）故本子项落到设计文档允许的**「句柄作第一参数的
函数」转发形态**：`namespace gfx` 内 `gfx.canvas_clear(c, ...)` 即 `Canvas::clear(&c, ...)` 的
跨模块等价。`obj.method()` 是 H2 长期形态，待编译器补齐跨模块方法符号注册后无缝切换（不为此
扩语言）。另：句柄 struct 传值触发复制而非移动（repr 按值拷贝，非 string/table 移动语义），
故同一句柄可安全复用。EN: tie's struct-instance methods only register in the defining module and
do not cross module import boundaries; so the handle layer ships the handle-first-arg function form
(`gfx.canvas_clear(c,...)`), the documented fallback; handle structs copy by value (no move), reusable.

### 生命周期 / lifecycle

- **显式 release**：`gfx.release_surface/path/image/data` 逐个释放（SkPath 走 `sk_path_free`，
  surface/image/data 走 `sk_obj_release`）。
- **arena 批量回收**：构造函数自动登记（`gfx.arena_count` 返回当前活跃数），
  `gfx.arena_release()` 一次释放全部未单独释放者并返回本批释放数；单独 release 会自动去记账
  （标记 -1，防双重释放）。探针断言 create/explicit/arena 全程计数一致（无泄漏）。
  EN: per-handle explicit release + arena bulk reclaim (auto-tracked; arena_release frees all
  and returns the batch count; explicit release untracks to avoid double free).

### thunk 追加面 / appended thunk entries

SkPath 最小面（append-only，未动 p.6.8.6 条目）+ gen_thunk 签名登记 + 绑定重生成：
`sk_path_new/free/move_to/line_to/close` + `sk_canvas_draw_path`。EN: minimal SkPath surface
appended to the thunk and the signature registry.

### 构建与运行 / build & run

```
compiler\tiec.exe ext\gfx\skia\thunk\build_p687.tie -o ext\gfx\skia\thunk\build_p687.exe
ext\gfx\skia\thunk\build_p687.exe     # 仓库根运行：生成绑定→thunk.obj→探针obj→链接→运行
```
与 build_thunk 相同链路，**额外链 `..\trm-lite\trm_lite.a`**（gfx arena 用 table<T> 容器，
`tl_tbl$*` 表运行时符号须由 trm_lite.a 提供）。EN: same pipeline as build_thunk, plus
`trm_lite.a` (table runtime for the arena's table<T> bookkeeping).

### 验收探针 / acceptance probe

`tests/p687_probe/p687_probe.tie`：Surface/Canvas/Paint/两条 Path（move/line/close）→
绘制（clear 白 / 红矩形 fill / 蓝竖线 stroke / 绿 path 折线 / 黄 path 闭合填充）→ peek 逐像素
断言（BGRA 内存序）→ snapshot→PNG 编码（魔数 + IHDR 96x48）→ 落盘 → 显式 release + arena
批量回收计数一致 → `ExitProcess` 确定性退出。**asserts=23，PASS / exit 0**。
EN: acceptance probe renders via the handle layer and validates pixels/PNG + lifecycle counts;
23 asserts PASS / exit 0.

### 本子项踩坑与根治记录 / gotchas & decisions

- 跨模块方法符号不注册 → 落函数转发形态（见上，记录在档）。
- class 角色 `ptr<u8>` 局部量须在 `unsafe {}` 内声明并初始化。
- 全局 `table<T>` 声明须 `var t: table<i64>;`（不带初始化器）。
- struct 字段须多行声明（单行 `{ var x:i64 }` 解析失败）。
- `ref` 修饰仅支持表参数（结构体不能 `ref` 借引用）。
- SkPath 是值类型（内部 ref-counted SkPathRef），`new SkPath`/`delete` 配对，非 `unref`。
EN: key findings during the sub-item — cross-module method symbols don't register (→ function
form); class-role ptr<u8> locals need unsafe; global tables take no initializer; struct fields
multi-line; `ref` is tables-only; SkPath is a value type (new/delete, not unref).

---

## p.6.8.8 D2 命令列表翻译器 + font_measure 文本度量桥

*EN: D2 command-list translator (Paint Commands → Skia) + SkFont text-measure bridge.*

### 命令列表格式 / command-list format

命令列表 = **平面 `table<i64>` 字节码**（`ext/gfx/commands.tie` 的 `commands.*` 构造器生成，
`gfx.run_commands(canvas, cmds)` 消费）。每条命令**自定长**，解码器以单遍下标游标推进到表尾
（O(总槽数)，不逐条重建全表、无嵌套表）。凡 f64 数值槽一律以 `bitcast_f64_i64` 位模式存储，
解码端 `bitcast_i64_f64` 回读。TEXT/IMAGE 的字节负载内联为 i64 字节值，解码处 `alloc` 临时缓冲
→ 绘制 → `free`。kind 编码（长度=槽数）：

| kind | 名称 | 槽布局 | len |
|---|---|---|---|
| 0 | CLEAR | `[0, color]` | 2 |
| 1 | FILL_RECT | `[1, l,t,r,b_{bits}, color, aa]` | 7 |
| 2 | STROKE_RECT | `[2, l,t,r,b_{bits}, color, w_{bits}]` | 7 |
| 3 | TEXT | `[3, size_{bits}, x_{bits}, y_{bits}, color, nchars, c0..cN]` | 6+N |
| 4 | PATH | `[4, color, style, aa, width_{bits}, closed, npts, x0,y0,x1,y1,..]`（moveTo p0 / lineTo 其余；closed=1 close） | 7+2·npts |
| 5 | IMAGE | `[5, x_{bits}, y_{bits}, nbytes, b0..bM]`（PNG 字节值） | 4+M |

`color` 为 u32 ARGB premul（SkColor），以 i64 直存；`style` 0fill/1stroke；`aa` 0/1。
映射：FILL_RECT/STROKE_RECT→`drawRect`、TEXT→`measure+drawTextBlob`、PATH→`path_new/
move_to/line_to/close+drawPath`、IMAGE→`make_from_encoded+drawImage`（绘制后立 unref）。
EN: a flat single-pass command-list bytecode as `table<i64>` (self-delimited commands,
single-index decode, no nested tables, no full-table rebuild).

### font_measure 文本度量桥 / text-measure bridge

- `gfx.font_measure(size, text: string) → f64`：一键建 font→`measureText`→free，返回宽度
  （SkScalar advance 总和）。
- `gfx.font_new(size) → Font` / `gfx.font_free(font)`：SkFont 句柄（独立 `sk_font_free`，不并入
  arena）。
- `gfx.font_measure_bytes(font, bytes: table<i64>) → f64`：字节表文本宽度（UTF-8 逐字节）。
- `gfx.font_metrics(font) → FontMetrics{ascent,descent,leading: f64}`：ascent/descent/leading
  以 i64 槽承载 f64 位模式（`sk_font_metrics` 写、tie 端 `bitcast_i64_f64` 读回），与 std/tsha1
  位重解释同风格。
EN: convenience/one-shot/clamped measure + metrics bridges over SkFont::measureText / getMetrics.

### thunk 追加面 / appended thunk entries

text/font/image 面（append-only，未动 p.6.8.6/6.8.7 条目）：
`sk_font_create(size)→ptr` / `sk_font_free` / `sk_font_measure(font,text,len)→f64` /
`sk_font_metrics(font, &ascent,&descent,&leading)` / `sk_canvas_draw_text_blob(c,font,x,y,
text,len,paint)` / `sk_image_make_from_encoded(data,len)→ptr` / `sk_canvas_draw_image(c,img,x,y)`。
文本一律裸指针 + 字节数（UTF-8 → `SkTextEncoding::kUTF8`），规避 string 编解码歧义；SkFont 走
独立 `sk_font_free`（与 sk_path 同例）；image 复用 `sk_obj_release(obj, IMAGE)` unref。
EN: appended SkFont/text/image surface + gen_thunk registry entries + regenerated binding.

### 构建与运行 / build & run

```
compiler\tiec_7A6100.exe tests\p688_probe\build_p688.tie -o tests\p688_probe\build_p688.exe
tests\p688_probe\build_p688.exe      # 仓库根运行：重生成绑定→thunk.obj→探针obj→链接→运行
```
与 p.6.8.7 相同链路，额外链 `..\trm-lite\trm_lite.a`。**p.6.8.8 期间 compiler/ 由另一子代理
（std/fs 缺陷 RCA）并发修改、tiec.exe 处于中间态**，故本驱动固定用稳定现役 `tiec_7A6100.exe`
（SHA256 7A6100FC…BC44），不与 RCA 子代理并发改 compiler/。EN: same pipeline as p.6.8.7,
pinned to the known-good tiec_7A6100.exe while the std/fs RCA sub-agent owns compiler/.

### 验收探针 / acceptance probe

`tests/p688_probe/p688_probe.tie`：font_measure 数值桥 → 命令列表（clear→fill→stroke→text
「Hello」→path 折线→image(内置 8x8 合法 PNG)）→ render1 逐像素判定点断言（背景/填充/描边/
Glyph 计数/路径/图像）→ PNG 魔数/IHDR/落盘 → **render2 相同命令列表重画 → render2 判定点 +
区域逐像素一致 + render1/render2 PNG 字节全等（完整帧无损逐像素「哈希校验一致」）** → 生命周期
归零。**asserts=32，PASS / exit 0**（无窗口，CI 可跑）。
EN: acceptance probe loads a 4-kind command list, renders offscreen, asserts decision pixels +
font_measure values, and proves two identical command lists render identically (render1/render2
PNG byte-identical); 32 asserts PASS / exit 0.

### 本子项踩坑与根治记录 / gotchas & decisions

- **编译器缺陷（记录，未在本次修）**：tie 编译器把循环体内局部变量以 `alloca` 落下且**不提升到
  入口块** → 大循环（如 16 万次逐像素比对）线性涨栈 → `EXCEPTION_STACK_OVERFLOW(0xC00000FD)`。
  本探针以 **render1/render2 PNG 字节全等**证明完整帧逐像素等价，避免超大 tie 循环（PNG 编码在
  C++ 内完成，tie 侧仅 ~1600 字节比较）；compiler/ 根因修复不在本子项范围（由 RCA 子代理处理
  std/fs，编译器缺陷另立项），已记入 CHANGELOG。EN: a compiler codegen gap — loop-body locals
  lowered as non-hoisted `alloca` — linearly grows the stack in big loops; the probe proves
  full-frame pixel equality via PNG byte identity instead (RCA elsewhere).
- `text` 是 tie 保留类型名，函数参数不能叫 `text`（换 `s`）；`bytes` 可用。
- SkImage 解码用 `SkImages::DeferredFromEncodedData`（namespace SkImages，非 SkImage::）。
- SkFont 默认构造 + `setSize`，由 `SkGraphics::Init()`（surface_create 内幂等启动）托管
  DirectWrite 字体管理器；文本度量在 surface 创建前调用亦可（驱动 build 先建 surface）。
EN: key findings — `text` is a reserved type name (use `s`); image decode is
`SkImages::DeferredFromEncodedData`; SkFont uses the default typeface via SkGraphics::Init.

---

## p.6.8.9 Win32 窗口嵌入层 / Win32 window-embedding layer

p.6.8.9 落地设计文档 §2 事实一的 **Flutter 嵌入模型**：Skia 只是渲染核心，窗口创建/消息泵/
呈现由平台嵌入层承担。本子项以 **Win32 起步**——窗口由 thunk（纯 Win32 C API）承担，
Skia 把命令列表渲染到**离屏后备缓冲 Surface**，经 `win_present` 把 BGRA 像素 blit 上屏。
EN: p.6.8.9 lands Fact-1's Flutter embedding model (design doc §2): Skia is only the
rendering core; windowing/message-pump/presentation are handled by the platform embedding
layer. Here Win32 first — the thunk (pure Win32 C API) owns the window; Skia renders the
command list into an **offscreen back-buffer Surface**, blitted on-screen by `win_present`.

### 代码布局 / layout

- `ext/gfx/win/win.h` + `win.cpp` —— Win32 窗口嵌入层 thunk（纯 C 风格、`extern "C"` 导出；
  tie 无法传 WndProc 回调，故窗口状态机收敛在 C 端）。
- `ext/gfx/window.tie` —— tie 侧封装（namespace `win`）：直透 C 面 + 标题 UTF-16LE 编码 +
  像素地址收发 + `Sleep`/`FindWindowW` 兜底。
- `tests/p689_probe/` —— 探针（离屏部分探针化）+ 构建驱动。
EN: thunk (C side owns the WndProc + state machine) + tie wrapper + probe.

### thunk 窗口面（C 入口清单）/ window C entry-point surface

| C 入口 | 作用 / Purpose |
| --- | --- |
| `win_open(title16, bytes, w, h)` | 惰性注册类名 `TieWinClass` + `CreateWindowExW(WS_OVERLAPPEDWINDOW)`，返回 HWND(i64) |
| `win_show(hwnd)` / `win_update(hwnd)` | `ShowWindow(SW_SHOW)` / `UpdateWindow`（同步一次 WM_PAINT） |
| `win_pump(hwnd)` | 消息泵：每轮先清零 paint_pending，再 `PeekMessage+DispatchMessage` **非阻塞排空**队列，返回处理消息数 |
| `win_closed(hwnd)` | 状态机：`WM_CLOSE`/`WM_DESTROY` 置位的关闭标志 |
| `win_paint_pending(hwnd)` | 最近一轮 pump 是否处理过 `WM_PAINT`/`WM_SIZE` |
| `win_present(hwnd, pixels, rowbytes, w, h)` | 按行拷 BGRA 像素字节到留存副本 + 建 top-down DIB + `InvalidateRect`，返回 0 成功 |
| `win_destroy(hwnd)` | `DestroyWindow` + 释放副本 + 移除 slot（清理映射） |
| `win_message_count()` | 累计 pump 处理消息数（诊断） |

WndProc 设计：`WM_PAINT` 内 `StretchDIBits` 把留存副本缩放到客户区上屏（Stretch 处理外框
与客户区尺寸差，避免上溢）；`WM_ERASEBKGND` 返回 1 防闪烁；`WM_CLOSE`/`WM_DESTROY` 置
closed。EN: WndProc does StretchDIBits blit on WM_PAINT, suppresses erasing, and latches
closed on WM_CLOSE/WM_DESTROY.

### tie 封装 / tie wrapper（namespace `win`）

`open(title,w,h)→hwnd` / `show` / `update` / `pump(hwnd)→n` / `closed` / `paint_pending` /
`present(hwnd, addr, rowbytes, w, h)→rc`（addr = `gfx.surface_peek(s).pixels` 地址，
后备缓冲 = p.6.8.8 离屏 Surface） / `destroy` / `sleep(ms)`（kernel32 `Sleep` 兜底） /
`find(cls,title)`（`FindWindowW` 供存活校验）。标题 UTF-16LE 在 tie 侧编码（复用
`sys/win32.wide_from` 同款码点→代理对拆分），alloc 缓冲传 C、调用后 free。
EN: thin tie wrapper on the C surface; back buffer is the p.6.8.8 offscreen Surface and
present sends its peeked pixel address.

### 构建与运行 / build & run

```
compiler\tiec_7A6100.exe tests\p689_probe\build_p689.tie -o tests\p689_probe\build_p689.exe
tests\p689_probe\build_p689.exe      # 仓库根运行：thunk.obj + win.obj → 探针obj → 链接 → 运行
```
链路：`clang-cl /MT` 编 `thunk.cpp` **与** `win.cpp`（win.obj 经本驱动独立登记，未改既有 thunk
构建）→ tiec `--emit-ir` + `clang -c` 编探针 → `clang -fuse-ld=link` 链接（探针.obj + thunk.obj
+ win.obj + skia.lib + trm_lite.a）→ 运行。系统库清单沿用 p.6.8.6-6.8.8（user32/gdi32/… +
compiler-rt），无新增。EN: build pipeline extended with win.obj; same system-lib list, no additions.

### 验收探针 / acceptance probe

`tests/p689_probe/p689_probe.tie`：open → show/update → 离屏 320x200 命令列表（CLEAR 白 →
FILL_RECT 红 → TEXT「p689」）→ peek 逐像素断言（背景/矩形/文本 Glyph 计数）→ **present blit
（断言返回 0）** → pump 若干轮（每轮 sleep 兜底，WM_PAINT 置 paint_pending）→ 断言 closed==0 +
`FindWindowW` 定位窗口存活 → destroy → 断言窗口消失 + 失效句柄 pump 安全返回 0。**asserts=14，
PASS / exit 0**；无无限等待（pump 非阻塞 + p0ms 兜底），全程数秒。窗口可见性/ blit 肉眼正确性
留待 p.6.8.12 全栈演示。EN: offscreen part is fully deterministic/CI-runnable; window part
(blit/pump/closed) verified locally; window visibility deferred to the p.6.8.12 full-stack demo.

### 本子项记录 / notes

- tie WndProc 回调无法跨 FFI 传 → 状态机留在 C 端（slot 表：closed/paint_pending/副本）。
- UTF-16 转换在 tie 侧（wide_from 同款），C 只收字节缓冲。
- `win::present` 收 peek 像素**地址**而非逐像素读整屏 → 像素搬运经 C 单遍 `memcpy` 行拷贝
  （无 O(n²)、无 tie 逐像素 C 面往返），与 p.6.8.8 性能约束一致。
EN: WndProc stays in C; UTF-16 done on the tie side; pixel transfer is a single C-side row
memcpy (no O(n²) tie-side per-pixel reads).