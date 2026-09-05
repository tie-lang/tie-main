// bench.cpp —— 软件光栅性能基线 thunk（p.6.8.13）
// EN: software-raster performance-baseline thunk (p.6.8.13).
//
// 提供两个基准 C 入口：bench_skia_rects（Skia 软光栅填充矩形到离屏 Surface）与
// bench_gdi_rects（GDI FillRect/HBRUSH 填充矩形到内存 DC）。二者均离线屏、均软件光栅、
// 同尺寸同像素格式（BGRA 32bpp），用 GetTickCount64 计时，返回毫秒——供 tie 侧基准
// 探针 tests/p6813_probe 打印 INFO 基线并做温和断言。
//
// 构建：与 thunk 一致用 clang-cl /MT（对 skia.lib）；系统库 gdi32（GetTickCount64
// 在 kernel32，默认链入）。独立文件，不改动 ext/gfx/skia/thunk/ 与 win/ 既有面。
//
// 计时说明：GetTickCount64 分辨率约 1–15.6ms，返回的是量化基线（参考值）；本仓库纪律
// 禁做精确时序断言，调用方只做温和合理性检查（ms>0 / gdi>=0）。

#include "bench.h"

// 需在 windows.h 之前定义：Skia 头里用 std::min/max 与 args 名为 min/max 的原语，
// 与 Windows min/max 宏冲突（20 错误），NOMINMAX 关闭宏即可同 TU 混用。
#define NOMINMAX
#include <windows.h>

#include "include/core/SkSurface.h"
#include "include/core/SkCanvas.h"
#include "include/core/SkPaint.h"
#include "include/core/SkRect.h"
#include "include/core/SkColor.h"
#include "include/core/SkImageInfo.h"
#include "include/core/SkGraphics.h"

namespace {

// Skia 一次性图形运行时初始化（幂等；字体缓存/DirectWrite 管理器等）。
void ensure_skia_init() {
    static bool inited = false;
    if (!inited) {
        SkGraphics::Init();
        inited = true;
    }
}

// 矩形：近似全表面（左右上下各内缩 2px），把填充字节最长化。
inline SkRect make_rect(float w, float h) {
    float r = w - 2.0f > 2.0f ? w - 2.0f : 3.0f;
    float b = h - 2.0f > 2.0f ? h - 2.0f : 3.0f;
    return SkRect::MakeLTRB(2.0f, 2.0f, r, b);
}

}  // namespace

extern "C" {

long long bench_skia_rects(int n, int w, int h) {
    if (n <= 0 || w <= 0 || h <= 0) {
        return -1;
    }
    ensure_skia_init();
    auto s = SkSurfaces::Raster(SkImageInfo::MakeN32Premul(w, h));
    if (!s) {
        return -1;
    }
    SkCanvas* c = s->getCanvas();
    if (!c) {
        return -1;
    }
    SkRect rc = make_rect((float)w, (float)h);
    SkPaint p;
    p.setColor(SK_ColorBLUE);
    p.setAntiAlias(false);
    p.setStyle(SkPaint::kFill_Style);

    // 暖机一次，规避首次 caches/page-fault 拖慢计时。
    for (int i = 0; i < n; i++) {
        c->drawRect(rc, p);
    }

    // GetTickCount64 分辨率约 1–15.6ms：跑 passes 轮（每轮 n 个矩形），取总耗时/passes，
    // 直到单轮耗时可辨（>=8ms），保证低 n 档也有正的基线读数（量化参考值，非精确时序）。
    int passes = 1;
    long long ms = 0;
    for (int attempt = 0; attempt < 6; attempt++) {
        ULONGLONG t0 = GetTickCount64();
        for (int k = 0; k < passes; k++) {
            for (int i = 0; i < n; i++) {
                c->drawRect(rc, p);
            }
        }
        ULONGLONG t1 = GetTickCount64();
        ms = (long long)(t1 - t0);
        if (ms >= 8) {
            break;
        }
        passes *= 4;
    }
    return ms / (long long)passes;
}

long long bench_gdi_rects(int n, int w, int h) {
    if (n <= 0 || w <= 0 || h <= 0) {
        return -1;
    }
    HDC mem = CreateCompatibleDC(NULL);
    if (!mem) {
        return -1;
    }
    // 32bpp 顶-下 DIB section：与 Skia N32 premul 同像素格式（BGRA little-endian）。
    BITMAPINFO bmi;
    memset(&bmi, 0, sizeof(bmi));
    bmi.bmiHeader.biSize        = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth       = w;
    bmi.bmiHeader.biHeight      = -h;   // top-down
    bmi.bmiHeader.biPlanes      = 1;
    bmi.bmiHeader.biBitCount    = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    void* bits = NULL;
    HBITMAP hbmp = CreateDIBSection(mem, &bmi, DIB_RGB_COLORS, &bits, NULL, 0);
    if (!hbmp) {
        DeleteDC(mem);
        return -1;
    }
    HGDIOBJ old = SelectObject(mem, hbmp);
    HBRUSH br = CreateSolidBrush(RGB(0, 0, 255));
    RECT rc;
    rc.left   = 2;
    rc.top    = 2;
    rc.right  = w - 2 > 2 ? w - 2 : 3;
    rc.bottom = h - 2 > 2 ? h - 2 : 3;

    // 暖机一次。
    for (int i = 0; i < n; i++) {
        FillRect(mem, &rc, br);
    }

    // 同 Skia 端：passes 轮直到可辨（>=8ms），返回 总耗时/passes。
    int passes = 1;
    long long ms = 0;
    for (int attempt = 0; attempt < 6; attempt++) {
        ULONGLONG t0 = GetTickCount64();
        for (int k = 0; k < passes; k++) {
            for (int i = 0; i < n; i++) {
                FillRect(mem, &rc, br);
            }
        }
        ULONGLONG t1 = GetTickCount64();
        ms = (long long)(t1 - t0);
        if (ms >= 8) {
            break;
        }
        passes *= 4;
    }

    DeleteObject(br);
    SelectObject(mem, old);
    DeleteObject(hbmp);
    DeleteDC(mem);
    return ms / (long long)passes;
}

}  // extern "C"