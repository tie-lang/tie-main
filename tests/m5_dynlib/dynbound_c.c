/* tests/m5_dynlib/dynbound_c.c —— M5 动态库边界正例 C 冒烟（S10 扩展链面）
 * 加载 tie 编译的 dynbound_pos.dll，调用 slice<T> 与 repr(C) pod struct 导出面。
 * x64 调用约定：`%struct.Pod {i64,i64}` 与 `{ptr,i64}` 按值各占 2 个整数寄存器，
 * 故用「两个标量形参」声明即与 struct 按值寄存器传递 ABI 一致。
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

typedef long long i64;
typedef i64 (*FnSlice)(void*, i64);   /* slice<i64> → {ptr,len} → RCX=data,RDX=len */
typedef struct { i64 a; i64 b; } Pod;
typedef i64 (*FnPod)(i64, i64);       /* Pod {i64,i64} 按值 → RCX=a,RDX=b */

static int failures = 0;
static void expect_i64(const char *what, i64 got, i64 want) {
    if (got != want) { printf("FAIL %s: got %lld want %lld\n", what, got, want); failures++; }
    else printf("PASS %s = %lld\n", what, got);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "用法: dynbound_c.exe <dynbound_pos.dll>\n"); return 2; }
    HMODULE h = LoadLibraryA(argv[1]);
    if (!h) { fprintf(stderr, "LoadLibrary 失败: %lu\n", (unsigned long)GetLastError()); return 1; }
    printf("LoadLibrary OK: %s\n", argv[1]);

    FnPod pod_add = (FnPod)GetProcAddress(h, "dynbound_pos$pod_add");
    FnSlice sum_slice = (FnSlice)GetProcAddress(h, "dynbound_pos$sum_slice");
    if (!pod_add || !sum_slice) { fprintf(stderr, "GetProcAddress 失败\n"); FreeLibrary(h); return 1; }

    /* pod struct: pod_add(Pod{2,3}) → 5 ; Pod{10,4} → 14 */
    Pod p = { 2, 3 };
    expect_i64("pod_add(2,3)", pod_add(p.a, p.b), 5);
    expect_i64("pod_add(10,4)", pod_add(10, 4), 14);

    /* slice: sum_slice(buf{1,2,3}, 3) → 6 ; buf{-1,5} → 4 */
    static i64 buf1[3] = { 1, 2, 3 };
    expect_i64("sum_slice(1,2,3)", sum_slice((void*)buf1, 3), 6);
    static i64 buf2[2] = { -1, 5 };
    expect_i64("sum_slice(-1,5)", sum_slice((void*)buf2, 2), 4);

    FreeLibrary(h);
    if (failures == 0) { printf("=== 动态库边界正例（slice/pod struct）C 冒烟全部通过 ===\n"); return 0; }
    printf("=== %d 项失败 ===\n", failures);
    return 1;
}