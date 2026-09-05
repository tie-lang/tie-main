// bench.h —— 软件光栅性能基线 thunk（p.6.8.13，独立文件，未动 skia/thunk 既有面）
// EN: software-raster performance-baseline thunk (p.6.8.13, standalone file; does not
// touch the existing skia/thunk surface).
//
// 目的 / Purpose：用一个轻量基准量化「离屏软光栅填充矩形」的吞吐，并对照同等离屏
// 内存 DC 的 GDI FillRect，得到 skia/gdi 耗时比（基准参考值，随宿主/机器浮动）。
//
// 设计要点 / Design：
//   * bench_skia_rects：Skia 软件光栅（N32 premul 8888 Surface）逐次 drawRect 填充一个
//     略内缩的矩形（近似全覆盖，逼近有效载荷边界），GetTickCount64 计时 → 毫秒。
//   * bench_gdi_rects：GDI 内存 DC + 32bpp 顶-下 DIB section，逐次 FillRect(HBRUSH) 填充
//     同样的矩形，GetTickCount64 计时 → 毫秒。
//   * 两者画到等尺寸、同像素格式（BGRA 32bpp）的离屏缓冲，均软件光栅，可公平对照。
//   * GetTickCount64 分辨率约 1–15.6ms，故数字为量化基线（参考值，不接受精确时序断言）。
//   * 断言纪律：调用方只要求 skia_ms>0、gdi_ms>=0（温和），禁精确时序断言（仓库忌时钟教训）。

#ifndef TIE_GFX_BENCH_H
#define TIE_GFX_BENCH_H

#ifdef __cplusplus
extern "C" {
#endif

// 离屏 Skia 软光栅画 n 个填充矩形（近似全表面）到 w x h 离屏 Surface 的毫秒（GetTickCount64）。
// 失败（surface 创建失败）返回 -1；正常返回 >=0 的毫秒数。
long long bench_skia_rects(int n, int w, int h);

// GDI FillRect/HBRUSH 画 n 个填充矩形到 w x h 内存 DC（32bpp DIB）的毫秒（GetTickCount64）。
// 失败返回 -1；正常返回 >=0 的毫秒数。
long long bench_gdi_rects(int n, int w, int h);

#ifdef __cplusplus
}
#endif

#endif // TIE_GFX_BENCH_H