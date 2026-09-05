// thunk.h —— Skia 类方法 → C 入口的最小 extern "C" 面（p.6.8.6）
// EN: minimal extern "C" surface exposing Skia class methods as C entry points.
//
// 设计要点 / Design:
//   * 所有 Skia 对象一律不透明指针（void*，tie 侧 ptr<u8>）；stub 持有所有权，
//     tie 经 sk_obj_release(obj, kind) 显式释放。canvas 由 surface 拥有，不单独释放。
//   * SkPaint 不直接镜像 C++ 布局（位域脆弱），改为扁平 repr(C) 描述结构
//     TSkPaint，由 thunk 转成 SkPaint。TSkImageInfo 同理承载像素回读信息。
//   * 布局 = MSVC x64 自然对齐（tie repr(C) 由 p.6.8.2 保证一致），由
//     tests/p686_probe/ref.c 对照 offsetof 核验后写死期望。

#ifndef TIE_SKIA_THUNK_H
#define TIE_SKIA_THUNK_H

#ifdef __cplusplus
extern "C" {
#endif

// 扁平 repr(C) paint 描述。Offsets (MSVC x64)：color@0, style@4, antialias@8,
// stroke_width@16（double align 8）；size=24 align=8。
// value 约束/style 编码：style 0=fill 1=stroke 2=fillAndStroke；antialias 0/1。
typedef struct TSkPaint {
    unsigned int color;       // ARGB premul（SkColor）
    int          style;       // 0 fill / 1 stroke / 2 fillAndStroke
    int          antialias;   // 0 关 / 1 开
    double       stroke_width;
} TSkPaint;

// 扁平 repr(C) image info，由 sk_surface_peek_pixels 填充。
// Offsets (MSVC x64)：width@0, height@4, color_type@8, alpha_type@12,
// row_bytes@16, pixels@24；size=32 align=8。
typedef struct TSkImageInfo {
    int   width;
    int   height;
    int   color_type;   // SkColorType 数值（N32 premul 8888）
    int   alpha_type;   // SkAlphaType 数值（kPremul=1）
    int   row_bytes;    // 每行字节数
    void* pixels;       // 首行首像素地址（surface 拥有，勿释放）
} TSkImageInfo;

// sk_obj_release 的对象种类
enum {
    SK_OBJ_SURFACE = 0,   // SkSurface*（canvas 由其拥有，一并回收）
    SK_OBJ_IMAGE   = 2,   // SkImage*（snapshot）
    SK_OBJ_DATA    = 3,   // SkData*（PNG 编码缓冲）
    SK_OBJ_PAINT   = 4    // 保留（本最小面 paint 由 thunk 内部构造，无需句柄）
};

// SkPath 最小面（p.6.8.7）：对象持有所有权，经 sk_path_free 显式释放。
// SkPath 走独立 sk_path_free 而非 sk_obj_release，路径生命周期与 surface/image/data
// 分开管理，避免与 SK_OBJ_* kind 枚举耦合。

// —— 离屏 Surface ——
void*  sk_surface_create(int w, int h);                          // SkSurface* (N32 premul 8888 raster)
void*  sk_surface_canvas(void* surface);                         // SkCanvas*（surface 拥有）
void*  sk_surface_snapshot(void* surface);                       // SkImage*（.release() 交付）
void   sk_surface_peek_pixels(void* surface, TSkImageInfo* out); // 回读底层像素/信息

// —— 图像编码 ——
void*  sk_image_encode_png(void* image, long long* out_len);     // SkData*（PNG 字节；out_len 记账）
void*  sk_data_bytes(void* data);                                // SkData* → 原始字节缓冲指针
int    sk_data_write_file(void* data, const char* path);         // 写文件（wb + fflush 同步）

// —— Canvas 绘制 ——
void   sk_canvas_clear(void* canvas, unsigned int color);
void   sk_canvas_draw_line(void* canvas, double x0, double y0, double x1, double y1, const TSkPaint* paint);
void   sk_canvas_draw_rect(void* canvas, double l, double t, double r, double b, const TSkPaint* paint);
void   sk_canvas_draw_path(void* canvas, void* path, const TSkPaint* paint);   // SkCanvas::drawPath

// —— SkPath 构造 / 逐点构建（p.6.8.7）——
void*  sk_path_new(void);                        // new SkPath（所有权交付；sk_path_free 释放）
void   sk_path_free(void* path);                 // SkPath 值类型：delete 配对，非 unref
void   sk_path_move_to(void* path, double x, double y);  // moveTo
void   sk_path_line_to(void* path, double x, double y);  // lineTo
void   sk_path_close(void* path);                       // close（闭合）

// —— 生命周期 ——
void   sk_obj_release(void* obj, int kind);

// —— 输出同步 ——
void   sk_flush_std(void);   // fflush(stdout/stderr)：ExitProcess 前落盘，保住探针报告

#ifdef __cplusplus
}
#endif

#endif // TIE_SKIA_THUNK_H