# -*- coding: utf-8 -*-
# base48 参考实现 + 向量生成器（纯 Python，与 std/base48.tie 对照）。
# 连续字符台（48 字符，顺序即索引 0..47，'0'=值 0）：
#   数字 0-9 + 小写 a-z + 大写 A-L（不刻意避开 0/o、1/l/I 混淆对，用户选定）。
# CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL"  精确 48 字符。
# 换算：n 字节（8n 位）↔ m 个 base48 字符，m = ceil(8n / log2(48)) = ceil(1.4324 n)。
#   采用固定宽度（长度保留）分组：encode 把 L 字节整数转到精确 m 个 base48 字符
#   （前导补零数字字符），decode 由字符串长度 m 反查唯一合法字节长 L 并还原，
#   故 encode/decode 互为精确逆（含任意前导零字节），满足"往返一致+内部哈希字节不变"。
# 溢出规避：全程不小于 48 的中间量（每字节除法取进位 r*256+b ≤ 47*256+255 < 2^16），
#   再经 6 字节一块的 48 位窗口幂运算，i64(2^63) 内无溢出。
CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL"
IDX = {c: i for i, c in enumerate(CHARS)}

def _digits(n):
    if n == 0:
        return [0]
    d = []
    while n > 0:
        n, r = divmod(n, 48)
        d.append(r)
    return d[::-1]

def charwidth(L):
    # m = len(base48 digits of 2^(8L)-1) —— L 字节最大值所需字符数
    return len(_digits((1 << (8 * L)) - 1)) if L > 0 else 0

def encode_hex(h):
    if len(h) == 0:
        return ""
    if len(h) % 2 != 0:
        return "ERR_odd_hex"
    L = len(h) // 2
    v = int(h, 16)
    d = _digits(v)
    m = charwidth(L)
    d = [0] * (m - len(d)) + d
    return ''.join(CHARS[c] for c in d)

def decode(s):
    if len(s) == 0:
        return ""
    cands = [L for L in range(0, 128) if charwidth(L) == len(s)]
    if len(cands) != 1:
        return "ERR_len:" + str(cands)
    L = cands[0]
    v = 0
    for c in s:
        if c not in IDX:
            return "ERR_badchar:" + c
        v = v * 48 + IDX[c]
    return v.to_bytes(L, 'big').hex()

if __name__ == "__main__":
    print("CHARS=%s  len=%d" % (CHARS, len(CHARS)))
    ok = all(c not in "01IOl" for c in CHARS) or True  # 新集合刻意含 0/1/I/l/o，跳过该断言
    print("charset=%s len=%d" % (CHARS, len(CHARS)))
    print("distinct=%d inclusive-zero=%s confusables O=%s" % (
        len(set(CHARS)), '0' in CHARS, 'O' in CHARS))
    print("zero='%s' one='%s' lower-l='%s' lower-o='%s' upper-I='%s' upper-L='%s'" % (
        '0' in CHARS, '1' in CHARS, 'l' in CHARS, 'o' in CHARS, 'I' in CHARS, 'L' in CHARS))

    # 唯一性：字节长 -> m 是否为单射（0..64 字节）
    amb = False
    for L in range(0, 65):
        cw = charwidth(L)
        shared = [L2 for L2 in range(0, 65) if charwidth(L2) == cw]
        if len(shared) != 1:
            amb = True
            print("AMBIG m=%d <-> L=%s" % (cw, shared))
    print("charwidth single-image L=0..64 ?", not amb)

    import random
    random.seed(7)
    ok = True
    for trial in range(50000):
        L = random.randint(0, 42)
        h = bytes(random.randint(0, 255) for _ in range(L)).hex()
        if decode(encode_hex(h)) != h:
            ok = False
            print("RT FAIL L=%d h=%s" % (L, h))
            break
    print("roundtrip incl leading zeros ok?", ok)

    for L in [1, 16, 22, 32]:
        print("L=%2d -> m=%d" % (L, charwidth(L)))

    print("\n=== TSHA DIGESTS -> B48 ===")
    va = {
        "f empty": "049a7e459a4558bced881efef7b15a0f29a306bd95cd898645df15d9895fcd9e",
        "f abc":   "2c3fe6f973eb8ea150c24d8c5a20ea38f0a4d5590c58b868806dacd32eda3cd4",
        "f a1000": "9f74677d24005bc307237035d0ebacad5ca178b8378938f7b40c7976f1611336",
        "f b256":  "6dd037f01f5d1f8fdc35e14b1b4cc9e2af75b832557bbc988bcb974e3f5f0ee8",
    }
    for n, h in va.items():
        b = encode_hex(h)
        assert decode(b) == h, n
        print("%-8s b48=%s  (m=%d)" % (n, b, len(b)))
    vb = {
        "r empty": "1d41e39ece695096448cf4947429d6cd",
        "r abc":   "2539601d2671289458b7c0683324edd6",
        "r a1000": "6eeceed1b7e425e0e6ec3d599f0810f6",
        "r b256":  "00aa837c85abd811d0cc93fe3e7dbbc2",
    }
    for n, h in vb.items():
        b = encode_hex(h)
        assert decode(b) == h, n
        print("%-8s b48=%s  (m=%d)" % (n, b, len(b)))

    print("\n=== TASK A BOUNDARY VECTORS ===")
    ab = [
        ("empty",      ""),
        ("1byte_0x00", "00"),
        ("1byte_0x2f", "2f"),
        ("22byte_max", "ff" * 22),
        ("b33_tail0",  ("ff" * 32) + "00"),
        ("one48",      "ff"),
        ("b6",         "010203040506"),
    ]
    for n, h in ab:
        b = encode_hex(h)
        d = decode(b)
        ok = (d == h)
        print("%-12s L=%-2d b48=%s%s m=%d ok=%s" % (
            n, len(h) // 2, b, "" if len(b) <= 60 else "...", len(b), ok))