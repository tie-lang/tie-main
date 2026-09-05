// win.cpp —— p.6.8.9 Win32 窗口嵌入层 thunk（纯 C 风格，extern "C" 导出）
// EN: Win32 window-embedding thunk — pure C style, extern "C" exports.
//
// 设计要点 / Design:
//   * 窗口类 "TieWinClass" 首次 win_open 时惰性注册，WndProc = 模块静态 win_proc。
//   * 窗口状态收敛在固定容量 slot 表（WIN_SLOT_MAX = 8），以 HWND 查表；每个 slot
//     持有 closed / paint_pending 标志 + 宾客后备缓冲留存副本（BGRA，w*h*4）+ BITMAPINFO。
//   * win_present 把调用方（Skia 离屏 Surface peek 出的像素）按行拷入 slot->buf，
//     构建 top-down BITMAPINFO 并 InvalidateRect；WM_PAINT 内 StretchDIBits 上屏
//     （Stretch 处理客户区与窗口外框尺寸差，稳妥不上溢）。
//   * win_pump 每次调用先把 paint_pending 清零，再用 PeekMessage + DispatchMessage
//     非阻塞排空线程队列 —— 探针无需 GetMessage 阻塞等待（禁无限等，5-8s 上限）。
//   * 标题经 tie 侧宽字符桥转 UTF-16LE 字节缓冲传给 win_open，本端拷贝为 wchar_t*。
//
// 系统库（在链接清单中）：user32（CreateWindow/PeekMessage）、gdi32（StretchDIBits）
//     ——均已在 p.6.8.6-6.8.8 探针链接清单内，无新增依赖。

#include <windows.h>
#include <string.h>
#include <stdint.h>
#include "win.h"

#define WIN_SLOT_MAX 8

typedef struct {
    HWND              hwnd;
    int               closed;         // 1=已关闭（WM_CLOSE/WM_DESTROY 置位）
    int               paint_pending;  // pump 清零；WM_PAINT/WM_SIZE 置位
    int               w;              // 后备缓冲宽（像素）
    int               h;              // 后备缓冲高（像素）
    int               rowbytes;       // 调用方行字节数
    unsigned char*    buf;            // BGRA 宾客像素留存副本（malloc，cap 记账）
    long              cap;            // buf 已分配字节数
    BITMAPINFOHEADER  bmi;            // 有效后备缓冲的 DIB 头（top-down BGRA）
    int               bmi_valid;      // 1=已 present 过、可 blit
} WinSlot;

static WinSlot      g_slots[WIN_SLOT_MAX];
static int          g_registered = 0;   // 窗口类注册一次
static const wchar_t* kWinClass = L"TieWinClass";
static long         g_message_count = 0;

static WinSlot* slot_find(HWND hwnd) {
    for (int i = 0; i < WIN_SLOT_MAX; i++) {
        if (g_slots[i].hwnd == hwnd && g_slots[i].hwnd != 0) {
            return &g_slots[i];
        }
    }
    return (WinSlot*)0;
}

static WinSlot* slot_alloc(void) {
    for (int i = 0; i < WIN_SLOT_MAX; i++) {
        if (g_slots[i].hwnd == 0) {
            memset(&g_slots[i], 0, sizeof(g_slots[i]));
            return &g_slots[i];
        }
    }
    return (WinSlot*)0;
}

// 把已留存的后备缓冲经 StretchDIBits 缩放到客户区上屏（BGRA 32bpp top-down）。
static void slot_blit(WinSlot* s, HDC hdc) {
    if (!s || !s->bmi_valid || !s->buf || s->w <= 0 || s->h <= 0) {
        return;
    }
    RECT rc;
    GetClientRect(s->hwnd, &rc);
    int cw = rc.right - rc.left;
    int ch = rc.bottom - rc.top;
    if (cw <= 0 || ch <= 0) {
        return;
    }
    StretchDIBits(hdc,
                  0, 0, cw, ch,                              // 目标客户区
                  0, 0, s->w, s->h,                          // 源后备缓冲
                  s->buf, (const BITMAPINFO*)&s->bmi,
                  DIB_RGB_COLORS, SRCCOPY);
}

static LRESULT CALLBACK win_proc(HWND h, UINT msg, WPARAM wp, LPARAM lp) {
    WinSlot* s = slot_find(h);
    switch (msg) {
        case WM_PAINT: {
            PAINTSTRUCT ps;
            BeginPaint(h, &ps);
            if (s && s->bmi_valid) {
                // 记录：pump 期间处理过 WM_PAINT
                s->paint_pending = 1;
                slot_blit(s, ps.hdc);
            } else {
                // 尚无后备缓冲（present 前）：用窗口底色填充，避免残留。
                RECT rc;
                GetClientRect(h, &rc);
                FillRect(ps.hdc, &rc, (HBRUSH)(COLOR_WINDOW + 1));
            }
            EndPaint(h, &ps);
            return 0;
        }
        case WM_SIZE:
            if (s) {
                s->paint_pending = 1;   // 客户区变化标记置位
            }
            break;                      // 落 DefWindowProc
        case WM_ERASEBKGND:
            return 1;                   // 禁背景擦除（防闪烁，present 全量覆盖）
        case WM_CLOSE:
            if (s) {
                s->closed = 1;          // 关闭请求置位
            }
            break;                      // DefWindowProc → DestroyWindow
        case WM_DESTROY:
            if (s) {
                s->closed = 1;
            }
            break;
        default:
            break;
    }
    return DefWindowProcW(h, msg, wp, lp);
}

extern "C" {

long long win_open(const void* title16, int title_bytes, int win_w, int win_h) {
    if (win_w <= 0 || win_h <= 0) {
        return 0;
    }
    HINSTANCE inst = GetModuleHandleW(NULL);
    if (!g_registered) {
        WNDCLASSW wc;
        memset(&wc, 0, sizeof(wc));
        wc.lpfnWndProc   = win_proc;
        wc.hInstance     = inst;
        wc.hCursor       = LoadCursorW(NULL, (LPCWSTR)IDC_ARROW);
        wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
        wc.lpszClassName = kWinClass;
        RegisterClassW(&wc);
        g_registered = 1;
    }

    // 拷贝标题：UTF-16LE 字节缓冲 → wchar_t[]（补尾 0）。
    const unsigned char* tb = (const unsigned char*)title16;
    int words = (tb && title_bytes > 0) ? (title_bytes / 2) : 0;
    wchar_t* ts = (wchar_t*)malloc(sizeof(wchar_t) * (words + 1));
    if (!ts) {
        return 0;
    }
    for (int i = 0; i < words; i++) {
        ts[i] = (wchar_t)(tb[2 * i] | (((wchar_t)tb[2 * i + 1]) << 8));
    }
    ts[words] = 0;

    HWND h = CreateWindowExW(0, kWinClass, ts, WS_OVERLAPPEDWINDOW,
                             CW_USEDEFAULT, CW_USEDEFAULT,
                             (int)win_w, (int)win_h,
                             NULL, NULL, inst, NULL);
    free(ts);
    if (!h) {
        return 0;
    }
    WinSlot* s = slot_alloc();
    if (!s) {
        DestroyWindow(h);
        return 0;
    }
    s->hwnd = h;
    s->closed = 0;
    s->paint_pending = 0;
    s->w = (int)win_w;
    s->h = (int)win_h;
    s->buf = (unsigned char*)0;
    s->cap = 0;
    s->bmi_valid = 0;
    return (long long)(intptr_t)h;
}

void win_show(long long hwnd) {
    HWND h = (HWND)(intptr_t)hwnd;
    if (h) {
        ShowWindow(h, SW_SHOW);
    }
}

void win_update(long long hwnd) {
    HWND h = (HWND)(intptr_t)hwnd;
    if (h) {
        UpdateWindow(h);   // 同步刷一遍待定 WM_PAINT
    }
}

int win_pump(long long hwnd) {
    WinSlot* s = slot_find((HWND)(intptr_t)hwnd);
    if (!s) {
        return 0;   // slot 已清理：安全返回 0，不触发崩溃
    }
    s->paint_pending = 0;   // 每轮 pump 复位，结果反映本轮是否出现 paint/size
    int processed = 0;
    MSG msg;
    // 非阻塞排空本线程消息队列；cap 防止极端情况死循环。
    int guard;
    for (guard = 0; guard < 64; guard++) {
        if (PeekMessageW(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                if (s) {
                    s->closed = 1;
                }
            }
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
            g_message_count++;
            processed++;
        } else {
            break;
        }
    }
    return processed;
}

int win_closed(long long hwnd) {
    WinSlot* s = slot_find((HWND)(intptr_t)hwnd);
    return (s && s->closed) ? 1 : 0;
}

int win_paint_pending(long long hwnd) {
    WinSlot* s = slot_find((HWND)(intptr_t)hwnd);
    return (s && s->paint_pending) ? 1 : 0;
}

int win_present(long long hwnd, const void* pixels, int rowbytes, int w, int h) {
    WinSlot* s = slot_find((HWND)(intptr_t)hwnd);
    if (!s || !pixels || w <= 0 || h <= 0) {
        return 1;
    }
    long need = (long)w * (long)h * 4;
    if (s->cap < need) {
        unsigned char* nb = (unsigned char*)realloc(s->buf, (size_t)need);
        if (!nb) {
            return 1;
        }
        s->buf = nb;
        s->cap = need;
    }
    // 按行拷贝 BGRA（处理 rowbytes 与 w*4 不一致的通用情形）。
    const unsigned char* src = (const unsigned char*)pixels;
    const long line = (long)w * 4;
    int y;
    for (y = 0; y < (int)h; y++) {
        if (rowbytes > 0 && rowbytes <= (int)line) {
            memcpy(s->buf + (size_t)y * line, src + (size_t)y * rowbytes, (size_t)line);
        } else {
            memcpy(s->buf + (size_t)y * line, src + (size_t)y * line, (size_t)line);
        }
    }
    s->w = w;
    s->h = h;
    s->rowbytes = rowbytes;
    // 建 top-down BGRA DIB 头（buf[0] = 左上角）。
    memset(&s->bmi, 0, sizeof(s->bmi));
    s->bmi.biSize        = sizeof(s->bmi);
    s->bmi.biWidth       = w;
    s->bmi.biHeight      = -h;     // top-down
    s->bmi.biPlanes      = 1;
    s->bmi.biBitCount    = 32;
    s->bmi.biCompression = BI_RGB;
    s->bmi_valid         = 1;
    InvalidateRect((HWND)(intptr_t)hwnd, NULL, FALSE);   // 调度 WM_PAINT 上屏
    return 0;
}

void win_destroy(long long hwnd) {
    HWND h = (HWND)(intptr_t)hwnd;
    WinSlot* s = slot_find(h);
    if (!s) {
        return;
    }
    if (s->hwnd && IsWindow(s->hwnd)) {
        DestroyWindow(s->hwnd);   // 同线程：同步发 WM_DESTROY（closed 置位）
    }
    if (s->buf) {
        free(s->buf);
        s->buf = (unsigned char*)0;
        s->cap = 0;
    }
    memset(s, 0, sizeof(*s));     // 移除 slot / 清理映射
}

long win_message_count(void) {
    return g_message_count;
}

}  // extern "C"