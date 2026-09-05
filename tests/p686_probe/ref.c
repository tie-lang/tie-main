#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

// p.6.8.6 layout probe reference: compute C offsetof for the flat repr(C)
// structs mirrored in ext/gfx/thunk_binding.tie (TSkPaint / TSkImageInfo).
// MSVC x64 natural alignment must agree with tie repr(C) (p.6.8.2).

typedef struct TSkPaint {
    unsigned int color;   // 0
    int          style;   // 4
    int          antialias; // 8
    double       stroke_width; // 16
} TSkPaint;

typedef struct TSkImageInfo {
    int   width;       // 0
    int   height;      // 4
    int   color_type;  // 8
    int   alpha_type;  // 12
    int   row_bytes;   // 16
    void* pixels;      // 24
} TSkImageInfo;

int main(void) {
    printf("TSkPaint size=%zu align=%zu color=%zu style=%zu antialias=%zu stroke_width=%zu\n",
        sizeof(TSkPaint), _Alignof(TSkPaint),
        offsetof(TSkPaint, color), offsetof(TSkPaint, style),
        offsetof(TSkPaint, antialias), offsetof(TSkPaint, stroke_width));
    printf("TSkImageInfo size=%zu align=%zu width=%zu height=%zu color_type=%zu alpha_type=%zu row_bytes=%zu pixels=%zu\n",
        sizeof(TSkImageInfo), _Alignof(TSkImageInfo),
        offsetof(TSkImageInfo, width), offsetof(TSkImageInfo, height),
        offsetof(TSkImageInfo, color_type), offsetof(TSkImageInfo, alpha_type),
        offsetof(TSkImageInfo, row_bytes), offsetof(TSkImageInfo, pixels));
    return 0;
}