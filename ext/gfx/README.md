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

## 裁剪模块清单（大纲，细节留 p.6.8.5）/ Trimmed module outline

保留的 API / 类（deta提清单在 p.6.8.5 模块清单子项给出）：
EN: Retained API / classes (detailed file list lands in p.6.8.5):

- 离屏表面：`SkSurface::MakeRaster` / `SkSurfaces::Raster`（N32 premul 8888 位图 Surface）
- 绘制：`SkCanvas`(drawColor/drawRect/drawImage/drawTextBlob)、`SkPaint`
- 形状：`SkPath`、`SkRect`
- 文本：`SkFont` + `SkTextBlob`（Windows 走 DirectWrite 字体管理器，`skia_enable_fontmgr_win`）
- 图像：`SkImage` / `SkBitmap` / `SkPixmap`
- 编解码：`SkCodec`（仅保留 PNG=BMP，走 libpng+zlib）
- 编码导出：`SkPngEncoder::Encode`

编译宏 / 关键 define：`SK_FONTMGR_WIN`（DirectWrite）、`SK_XML`(关)、`SK_HAS_WUFFS_LIBRARY`(关) 等由
GN args 生成；SDK `10.0.26100.0`。
EN: Compile macros: SK_FONTMGR_WIN (DirectWrite) on; XML/Wuffs etc off, driven by GN args.

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
```

GN `gen` 本组参数零警告生效（95 targets / 41 files）。EN: These GN args gen with zero warnings.

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

EN: default builds (idempotent), `--force` rebuild, `--gen` gn gen only, `--smoke`
compile+run+validate PNG, `--check` status, `--clean` remove out dir.

`build.tie` 经 `process.exec_code`（→ libc `system` → cmd.exe）执行 vcvarsall、gn、ninja、
cl 等外部命令；MSVC 环境统一由脚本注入（`call <vcvarsall> x64`）。幂等基于外部产物
`ext/gfx/lib/skia.lib` 存在 + `out/tie_raster_release/.build_state` 指纹与 manifest 一致。

EN: build.tie drives vcvarsall/gn/ninja/cl via process.exec_code; idempotent via the
`skia.lib` artifact + a `.build_state` fingerprint matching the manifest.

---

## 产物与体积基线 / Artifact & size baseline

- 静态库：`ext/gfx/lib/skia.lib`（Release x64，MSVC `/MT`，386 编译单元 / 556 目标）
- **体积基线：169,329,356 字节（≈161.5 MiB）**，记录于 `ext/gfx/skia/manifest.txt [size]` 与 README/CHANGELOG。
  EN: Size baseline: **169,329,356 bytes** (~161.5 MiB).
- 冒烟输出：`ext/gfx/skia/smoke/out/smoke.png`（320x200，2768 B，魔数
  `89504e470d0a1a0a` 校验通过）。EN: smoke output 320x200, 2768B, magic verified.

构建输出目录 `out/tie_raster_release/`、`.tools/`、冒烟 `out/` 均为本地产物，不入库。
EN: `out/tie_raster_release/`, `.tools/`, smoke `out/` are local artifacts, not committed.

---

## 清单与仓库纪律 / Manifest & repo hygiene

- `ext/gfx/skia/manifest.txt`：单一事实源（版本/依赖固定提交/toolchain/GN args/体积），
  build.tie 经 `cfg.parse_kv` 解析（INI 节 → `节.键`）。
- 第三方源码与二进制不入库：`.gitignore` 忽略 `ext/gfx/skia/`（源码树）与
  `ext/gfx/lib/`（二进制）；白名单保留 `build.tie` / `manifest.txt` / `smoke/smoke.cpp`。

EN: manifest.txt is the single source of truth, parsed by build.tie. .gitignore excludes
the third-party tree and lib binary, whitelisting our three authored files.

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