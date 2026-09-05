// thunk.cpp —— Skia 类方法 → C 入口的最小 extern "C" thunk（p.6.8.6）
// EN: minimal extern "C" thunk exposing Skia class methods as C entry points.
//
// 覆盖离屏画线闭环所需最小集：
//   Surface(创建/取 statusCanvas/snapshot/peek) + PNG 编码/落盘 +
//   Canvas(clear/drawLine/drawRect) + 统一释放。
// Paint 不暴露句柄：每次绘制把扁平 TSkPaint 转成内部 SkPaint（无状态，零泄漏）。
//
// 标题 exit 行为由 tie 侧 ExitProcess 承接（规避 DirectWrite 字体管理器
// 退出期访问违例，p.6.8.4 冒烟已知风险）。构建：见 build_thunk.tie / smoke 先例。

#include "thunk.h"

#include "include/core/SkSurface.h"
#include "include/core/SkCanvas.h"
#include "include/core/SkPaint.h"
#include "include/core/SkRect.h"
#include "include/core/SkPath.h"
#include "include/core/SkColor.h"
#include "include/core/SkImage.h"
#include "include/core/SkData.h"
#include "include/core/SkPixmap.h"
#include "include/core/SkGraphics.h"
#include "include/core/SkFont.h"
#include "include/core/SkFontMetrics.h"
#include "include/core/SkTextBlob.h"
#include "include/core/SkTypeface.h"
#include "include/encode/SkPngEncoder.h"

#include <cstdio>
#include <cstring>

namespace {

// 扁平 TSkPaint → 内部 SkPaint（style/aa/宽度/颜色落地）。
SkPaint make_paint(const TSkPaint* d) {
    SkPaint p;
    p.setColor((SkColor)d->color);
    p.setAntiAlias(d->antialias != 0);
    switch (d->style) {
        case 1: p.setStyle(SkPaint::kStroke_Style); break;
        case 2: p.setStyle(SkPaint::kStrokeAndFill_Style); break;
        default: p.setStyle(SkPaint::kFill_Style); break;
    }
    p.setStrokeWidth((SkScalar)d->stroke_width);
    return p;
}

}  // namespace

extern "C" {

void* sk_surface_create(int w, int h) {
    // 一次性初始化 Skia 图形运行时（字体缓存/DirectWrite 管理器等；幂等）。
    static bool inited = false;
    if (!inited) {
        SkGraphics::Init();
        inited = true;
    }
    auto s = SkSurfaces::Raster(SkImageInfo::MakeN32Premul(w, h));
    return s ? s.release() : nullptr;
}

void* sk_surface_canvas(void* surface) {
    SkSurface* s = static_cast<SkSurface*>(surface);
    return s ? s->getCanvas() : nullptr;
}

void* sk_surface_snapshot(void* surface) {
    SkSurface* s = static_cast<SkSurface*>(surface);
    if (!s) return nullptr;
    auto img = s->makeImageSnapshot();
    return img ? img.release() : nullptr;
}

void sk_surface_peek_pixels(void* surface, TSkImageInfo* out) {
    SkSurface* s = static_cast<SkSurface*>(surface);
    if (out == nullptr) return;
    std::memset(out, 0, sizeof(*out));
    if (!s) return;
    SkPixmap pm;
    if (!s->peekPixels(&pm)) return;
    const SkImageInfo& ii = pm.info();
    out->width      = ii.width();
    out->height     = ii.height();
    out->color_type = static_cast<int>(ii.colorType());
    out->alpha_type = static_cast<int>(ii.alphaType());
    out->row_bytes  = static_cast<int>(pm.rowBytes());
    out->pixels     = const_cast<void*>(pm.addr());
}

void* sk_image_encode_png(void* image, long long* out_len) {
    SkImage* img = static_cast<SkImage*>(image);
    if (!img) { if (out_len) *out_len = 0; return nullptr; }
    auto data = SkPngEncoder::Encode(/*GrDirectContext*/nullptr, img, SkPngEncoder::Options());
    if (!data || data->size() == 0) { if (out_len) *out_len = 0; return nullptr; }
    if (out_len) *out_len = static_cast<long long>(data->size());
    return data.release();
}

int sk_data_write_file(void* data, const char* path) {
    SkData* d = static_cast<SkData*>(data);
    if (!d || !path) return 0;
    FILE* f = std::fopen(path, "wb");
    if (!f) return 0;
    size_t n = std::fwrite(d->data(), 1, d->size(), f);
    std::fflush(f);
    bool ok = (std::fclose(f) == 0) && (n == d->size());
    return ok ? 1 : 0;
}

void* sk_data_bytes(void* data) {
    SkData* d = static_cast<SkData*>(data);
    return (d && d->size() > 0) ? const_cast<void*>(d->data()) : nullptr;
}

void sk_canvas_clear(void* canvas, unsigned int color) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    if (c) c->clear((SkColor)color);
}

void sk_canvas_draw_line(void* canvas, double x0, double y0, double x1, double y1,
                         const TSkPaint* paint) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    if (!c || !paint) return;
    SkPaint p = make_paint(paint);
    c->drawLine((SkScalar)x0, (SkScalar)y0, (SkScalar)x1, (SkScalar)y1, p);
}

void sk_canvas_draw_rect(void* canvas, double l, double t, double r, double b,
                         const TSkPaint* paint) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    if (!c || !paint) return;
    SkPaint p = make_paint(paint);
    c->drawRect(SkRect::MakeLTRB((SkScalar)l, (SkScalar)t, (SkScalar)r, (SkScalar)b), p);
}

void sk_obj_release(void* obj, int kind) {
    if (!obj) return;
    switch (kind) {
        case SK_OBJ_SURFACE: static_cast<SkSurface*>(obj)->unref(); break;
        case SK_OBJ_IMAGE:   static_cast<SkImage*>(obj)->unref();   break;
        case SK_OBJ_DATA:    static_cast<SkData*>(obj)->unref();    break;
        default: break;  // 未知 kind 忽略（最小面 paint 无句柄）
    }
}

// ==================== p.6.8.7 SkPath 追加面（append，未动既有条目） ====================

void sk_canvas_draw_path(void* canvas, void* path, const TSkPaint* paint) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    SkPath*   p = static_cast<SkPath*>(path);
    if (!c || !p || !paint) return;
    SkPaint sp = make_paint(paint);
    c->drawPath(*p, sp);
}

void* sk_path_new(void) {
    return (new SkPath());
}

void sk_path_free(void* path) {
    SkPath* p = static_cast<SkPath*>(path);
    if (!p) return;
    delete p;   // SkPath 是值类型（内部 ref-counted SkPathRef），new/delete 配对
}

void sk_path_move_to(void* path, double x, double y) {
    SkPath* p = static_cast<SkPath*>(path);
    if (!p) return;
    p->moveTo((SkScalar)x, (SkScalar)y);
}

void sk_path_line_to(void* path, double x, double y) {
    SkPath* p = static_cast<SkPath*>(path);
    if (!p) return;
    p->lineTo((SkScalar)x, (SkScalar)y);
}

void sk_path_close(void* path) {
    SkPath* p = static_cast<SkPath*>(path);
    if (!p) return;
    p->close();
}

// ==================== p.6.8.8 SkFont / 文本 / 图像 追加面（append，未动既有条目） ====================
// 字体度量(measureText) 与 文本绘制(textBlob) 均以默认 typeface（SkGraphics::Init 已启动
// DirectWrite 字体管理器）。文本一律裸指针 + 字节数（UTF-8），语义与 SkTextEncoding::kUTF8 对齐。

void* sk_font_create(double size) {
    // SkFont 值类型，new/delete 配对；setSize 后默认 typeface 惰性解析到系统字体。
    SkFont* f = new SkFont();
    f->setSize((SkScalar)size);
    return f;
}

void sk_font_free(void* font) {
    SkFont* f = static_cast<SkFont*>(font);
    if (!f) return;
    delete f;   // SkFont 值类型（内部引用计数 typeface），new/delete 配对
}

double sk_font_measure(void* font, const char* text, long long len) {
    SkFont* f = static_cast<SkFont*>(font);
    if (!f || !text || len < 0) return 0.0;
    SkRect bounds;
    // 返回 sum of default advance widths；bounds 一并回填（无需，传 nullptr 亦可）。
    return (double)f->measureText(text, (size_t)len, SkTextEncoding::kUTF8, nullptr);
}

void sk_font_metrics(void* font, long long* ascent, long long* descent, long long* leading) {
    SkFont* f = static_cast<SkFont*>(font);
    SkFontMetrics m;
    if (f) {
        f->getMetrics(&m);
    } else {
        std::memset(&m, 0, sizeof(m));
    }
    // 每个度量以它自身的 f64 位模式写进 i64 槽，tie 侧 bitcast_i64_f64 读回。
    double a = m.fAscent, d = m.fDescent, l = m.fLeading;
    if (ascent)  std::memcpy(ascent,  &a, sizeof(a));
    if (descent) std::memcpy(descent, &d, sizeof(d));
    if (leading) std::memcpy(leading, &l, sizeof(l));
}

void sk_canvas_draw_text_blob(void* canvas, void* font, double x, double y,
                              const char* text, long long len, const TSkPaint* paint) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    SkFont*   f = static_cast<SkFont*>(font);
    if (!c || !f || !text || len < 0 || !paint) return;
    auto blob = SkTextBlob::MakeFromText(text, (size_t)len, *f, SkTextEncoding::kUTF8);
    if (!blob) return;
    SkPaint p = make_paint(paint);
    c->drawTextBlob(blob.get(), (SkScalar)x, (SkScalar)y, p);
}

void* sk_image_make_from_encoded(void* data, long long len) {
    if (!data || len <= 0) return nullptr;
    auto img = SkImages::DeferredFromEncodedData(SkData::MakeWithCopy(data, (size_t)len));
    return img ? img.release() : nullptr;   // 对象交付；探针经 sk_obj_release(img, IMAGE) unref
}

void sk_canvas_draw_image(void* canvas, void* image, double x, double y) {
    SkCanvas* c = static_cast<SkCanvas*>(canvas);
    SkImage*  im = static_cast<SkImage*>(image);
    if (!c || !im) return;
    c->drawImage(im, (SkScalar)x, (SkScalar)y);
}

void sk_flush_std(void) {
    // ExitProcess 会跳过 CRT 终止，未刷新的 stdout/stderr 将丢失——flush 落盘。
    std::fflush(stdout);
    std::fflush(stderr);
}

}  // extern "C"