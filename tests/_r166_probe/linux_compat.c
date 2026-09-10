/* r.1.6.6 Linux 链接兼容层（CI linux-bootstrap 使用）
 * tie 编译器自身源码（semantic/llvmgen 计时、irgen_expr 浮点格式化）引用了
 * Windows CRT 专用符号；Linux glibc 无同名实现，以 POSIX 对等物补足语义：
 *   GetTickCount() -> 毫秒时钟（CLOCK_MONOTONIC，同 Windows 单调语义）；
 *   _gcvt(v,d,b)   -> 有效数字格式（glibc 仅 gcvt，下划线变体不存在）。
 */
#include <time.h>
#include <stdio.h>

long long GetTickCount(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
}

extern char *gcvt(double value, int ndigit, char *buf);

char *_gcvt(double value, int ndigit, char *buf) {
    return gcvt(value, ndigit, buf);
}