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