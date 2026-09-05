#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

// p.6.8.2 layout probe reference: compute C offsetof for the repr(C) structs
// used in tests/p682_probe/p682_probe.tie. Both clang and gcc must agree.
struct PodA { uint8_t a; int16_t b; int32_t c; int64_t d; };
struct PodB { uint32_t a; uint8_t b; uint8_t c; };
struct PodC { uint8_t a; uint32_t b; int16_t c; uint8_t d; int64_t e; };
struct PodD { float x; double y; };
struct PodE { int32_t a; uint16_t b; uint32_t c; int16_t d; int64_t e; uint8_t f; };

int main(void) {
    printf("PodA size=%zu align=%zu a=%zu b=%zu c=%zu d=%zu\n",
        sizeof(struct PodA), _Alignof(struct PodA),
        offsetof(struct PodA, a), offsetof(struct PodA, b),
        offsetof(struct PodA, c), offsetof(struct PodA, d));
    printf("PodB size=%zu align=%zu a=%zu b=%zu c=%zu\n",
        sizeof(struct PodB), _Alignof(struct PodB),
        offsetof(struct PodB, a), offsetof(struct PodB, b), offsetof(struct PodB, c));
    printf("PodC size=%zu align=%zu a=%zu b=%zu c=%zu d=%zu e=%zu\n",
        sizeof(struct PodC), _Alignof(struct PodC),
        offsetof(struct PodC, a), offsetof(struct PodC, b), offsetof(struct PodC, c),
        offsetof(struct PodC, d), offsetof(struct PodC, e));
    printf("PodD size=%zu align=%zu x=%zu y=%zu\n",
        sizeof(struct PodD), _Alignof(struct PodD),
        offsetof(struct PodD, x), offsetof(struct PodD, y));
    printf("PodE size=%zu align=%zu a=%zu b=%zu c=%zu d=%zu e=%zu f=%zu\n",
        sizeof(struct PodE), _Alignof(struct PodE),
        offsetof(struct PodE, a), offsetof(struct PodE, b), offsetof(struct PodE, c),
        offsetof(struct PodE, d), offsetof(struct PodE, e), offsetof(struct PodE, f));
    return 0;
}