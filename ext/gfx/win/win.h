// win.h —— p.6.8.9 Win32 窗口嵌入层 thunk（C 入口面）
// EN: Win32 window-embedding thunk — C entry-point surface.
//
// p.6.8.9 采用 Flutter 嵌入模型：窗口创建/消息泵/呈现由本 thunk（纯 Win32 C API，
// 无 C++ 特性）承担，Skia 只负责把命令列表渲染到离屏后备缓冲 Surface，经
// win_present 把 BGRA 像素 blit 上屏。tie 无法传 WndProc 回调，故窗口状态机
// （closed / paint_pending 标志、后备缓冲留存副本）全部收敛在 C 端。
//
// EN: p.6.8.9 follows the Flutter embedding model: windowing/message-pump/
// presentation lives in this thunk (pure Win32 C API, no C++ features); Skia only
// renders the command list into an offscreen back-buffer Surface, which is then
// blitted on-screen via win_present. tie cannot pass a WndProc callback, so the
// window state machine (closed / paint_pending flags + a retained back-buffer copy)
// lives entirely on the C side.

#ifndef TIE_GFX_WIN_H
#define TIE_GFX_WIN_H

#ifdef __cplusplus
extern "C" {
#endif

// title16：探针端以宽字符桥（wide_from 同款 UTF-16LE 编码）产出的字节缓冲，
// title_bytes 为其字节长度（不含尾 0）。w/h 为窗口尺寸。
// EN: title16 is a UTF-16LE byte buffer (NUL-terminated) as produced by the
// tie-side wide bridge; title_bytes is its length excluding the trailing NUL.

// 创建并注册窗口（类名 TieWinClass）；返回 HWND（i64），失败 0。
long long win_open(const void* title16, int title_bytes, int w, int h);

// 显示窗口 / 立即处理待定 WM_PAINT（UpdateWindow 同步刷一次）。
void   win_show(long long hwnd);
void   win_update(long long hwnd);

// 消息泵单步（PeekMessage+DispatchMessage 排空当前线程队列）；返回本轮处理消息数。
int    win_pump(long long hwnd);

// 状态机查询：1=窗口已关闭（WM_CLOSE/WM_DESTROY 置位）；
// paint_pending：最近一次 win_pump 是否处理过 WM_PAINT/WM_SIZE（每次 pump 开始清零）。
int    win_closed(long long hwnd);
int    win_paint_pending(long long hwnd);

// 把 BGRA 后备缓冲像素留存副本上屏并 InvalidateRect（WM_PAINT 时 StretchDIBits）。
// 返回 0 成功（slot 找到、尺寸合理、拷贝完成）。
int    win_present(long long hwnd, const void* pixels, int rowbytes, int w, int h);

// DestroyWindow + 释放后备缓冲 + 移除 slot（清理映射）。
void   win_destroy(long long hwnd);

// 累计 pump 处理消息数（诊断用）。
long   win_message_count(void);

// ---------------------------------------------------------------------------
// p.6.8.10 事件系统 E3：鼠标/键盘/定时器事件队列 + 信号标志
// E3 event queue (mouse/keyboard/timer) + signal flags.
//
// 事件结构体（C 端 WinSlot 内环形队列，容量 EVENT_CAP=256，满则丢最旧并置 overflow）：
//   { type:i32, x:i32, y:i32, key:i32, t_ms:i32 }
//   type：1 MOUSE_MOVE  2 LBUTTON_DOWN  3 LBUTTON_UP  4 RBUTTON_DOWN
//         5 RBUTTON_UP  6 KEY_DOWN  7 KEY_UP  8 TIMER
//   鼠标事件 x/y = lParam 客户区坐标（LOWORD/HIWORD）；key = 0。
//   键盘事件 x=y=0，key = WM_KEYDOWN/UP 的 vk 键码（WM_CHAR 亦入 KEY 类、key=字符码）。
//   TIMER 事件 x=y=0，key = 定时器 id（wParam）。
//   t_ms = GetMessageTime()（进程内单调，不用精确值断言，只断言单调不减）。
//
// 跨模块 struct 不能写（仓库惯例：跨模块类型用标量参数/i64 槽），故 `win_event_pop`
// 经 out 写 5 个 i64 槽 [type, x, y, key, t_ms]（t_ms 用 i64 槽承载，避免 32 位截断/
// 符号扩展），out 需持 5*i64 字节，返回是否弹出一条（0=空 1=弹出）。
// EN: pop writes 5 i64 slots [type, x, y, key, t_ms] (t_ms carried in an i64 slot to
// avoid 32-bit truncation/sign-extension); returns 1 popped / 0 empty.

// 队列剩余事件条数（O(1)）。
int    win_events_avail(long long hwnd);
// 弹出一条事件到 out[0..4] = {type,x,y,key,t_ms}；返回 1=弹出 / 0=空。
int    win_event_pop(long long hwnd, long long* out);
// 溢出标志：容量已满时丢弃最旧事件会置位（仅向上置位，不自动复位）。
int    win_event_overflow(long long hwnd);
// SetTimer：为窗口配对定时器 id=1，ms 毫秒后周期性投递 WM_TIMER。
void   win_set_timer(long long hwnd, int ms);
// WM_TIMER 信号标志：返回最近是否发生过 WM_TIMER，读取即复位（一次性信号语义）。
int    win_timer_flag(long long hwnd);

#ifdef __cplusplus
}
#endif

#endif // TIE_GFX_WIN_H