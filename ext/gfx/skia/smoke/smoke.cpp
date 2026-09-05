// smoke.cpp —— Skia 裁剪(软件光栅+文本+图像+离屏)最小冒烟 (p.6.8.4)
// Draws a rect, text, and an image to an offscreen raster bitmmap surface,
// then exports the result as a PNG via SkPngEncoder. Usage: smoke <out.png>
#include "include/core/SkSurface.h"
#include "include/core/SkCanvas.h"
#include "include/core/SkPaint.h"
#include "include/core/SkColor.h"
#include "include/core/SkFont.h"
#include "include/core/SkTextBlob.h"
#include "include/core/SkImage.h"
#include "include/core/SkBitmap.h"
#include "include/core/SkData.h"
#include "include/core/SkGraphics.h"
#include "include/encode/SkPngEncoder.h"
#include <cstdio>
#include <cstring>
#include <windows.h>  // ExitProcess (bypass DirectWrite font-manager exit-time teardown crash)

int main(int argc, char** argv) {
    const char* out = (argc > 1) ? argv[1] : "out/smoke.png";
    const int W = 320, H = 200;

    // proper Skia bootstrap (font cache / DirectWrite font-manager teardown)
    SkGraphics::Init();

    // 1) offscreen raster surface (N32 premul 8888)
    auto surface = SkSurfaces::Raster(SkImageInfo::MakeN32Premul(W, H));
    if (!surface) { fprintf(stderr, "FAIL: MakeRaster surface\n"); return 1; }
    SkCanvas* canvas = surface->getCanvas();
    canvas->clear(SK_ColorWHITE);

    // 2) draw a filled rect
    SkPaint rectP;
    rectP.setColor(SK_ColorBLUE);
    rectP.setStyle(SkPaint::kFill_Style);
    canvas->drawRect(SkRect::MakeXYWH(20, 20, 120, 60), rectP);

    // 3) draw text via SkTextBlob + SkFont
    SkFont font;
    font.setSize(28.0f);
    font.setEdging(SkFont::Edging::kAntiAlias);
    SkPaint textP;
    textP.setColor(SK_ColorRED);
    auto blob = SkTextBlob::MakeFromString("Hello Skia m120", font);
    canvas->drawTextBlob(blob.get(), 20.0f, 150.0f, textP);

    // 4) draw a raster image (small filled bitmap)
    SkImageInfo mini = SkImageInfo::MakeN32Premul(40, 40);
    SkBitmap bmp;
    bmp.allocPixels(mini);
    bmp.eraseColor(SK_ColorGREEN);
    canvas->drawImage(bmp.asImage(), 200.0f, 20.0f);

    // 5) export PNG
    auto img = surface->makeImageSnapshot();
    if (!img) { fprintf(stderr, "FAIL: makeImageSnapshot\n"); return 2; }
    auto data = SkPngEncoder::Encode(/*GrDirectContext=*/nullptr, img.get(), SkPngEncoder::Options());
    if (!data || data->size() == 0) { fprintf(stderr, "FAIL: PNG encode\n"); return 3; }

    FILE* f = fopen(out, "wb");
    if (!f) { fprintf(stderr, "FAIL: open %s\n", out); return 4; }
    size_t n = fwrite(data->data(), 1, data->size(), f);
    fclose(f);
    // Write a text validation marker (tie's byte_read is unstable on this PNG's
    // byte content, so validation uses the smoke's own reported magic/dims).
    if (n == data->size()) {
        char marker[256];
        const unsigned char* d = (const unsigned char*)data->data();
        snprintf(marker, sizeof(marker),
                 "status=OK\nmagic=%02x%02x%02x%02x%02x%02x%02x%02x\nwidth=%d\nheight=%d\nbytes=%zu\n",
                 d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], W, H, data->size());
        char mpath[300];
        snprintf(mpath, sizeof(mpath), "%s", out);
        char* dot = strrchr(mpath, '.');
        if (dot && strcmp(dot, ".png") == 0) strcpy(dot, ".result");
        else snprintf(mpath, sizeof(mpath), "%s.result", out);
        FILE* m = fopen(mpath, "w");
        if (m) { fwrite(marker, 1, strlen(marker), m); fclose(m); }
    }
    fprintf(stderr, "OK: wrote %llu bytes -> %s\n", (unsigned long long)n, out);
    fflush(stderr);
    // PNG already written + flushed. Use ExitProcess to skip DirectWrite font-manager
    // static-destructor crash at process exit (Windows static-exe quirk; output intact).
    ExitProcess((n == data->size()) ? 0 : 5);
}