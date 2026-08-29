# -*- coding: utf-8 -*-
# poly1305 参考生成器（纯 Python，26-bit 肢算法，与 std/poly1305.tie 对照）。
# 先以 RFC 8439 §2.5.2 验证向量校验本参考实现，再生成 4 组探针向量。
import sys

MASK = 0x3ffffff

def clamp16(r):
    # r = 16 字节小端；掩码 0x0ffffffc0ffffffc0ffffffc0fffffff（字节级）
    r[3] &= 0x0f; r[7] &= 0x0f; r[11] &= 0x0f; r[15] &= 0x0f
    r[4] &= 0xfc; r[8] &= 0xfc; r[12] &= 0xfc
    return r

def load_r(key):
    r = clamp16(list(key[:16]))
    # 映射为 5 个 26-bit 肢
    limbs = []
    acc = 0
    for i in range(16):
        acc |= r[i] << (8 * i)
    return [(acc >> (26 * i)) & MASK for i in range(5)]

def load_s(key):
    s = list(key[16:32])
    acc = 0
    for i in range(16):
        acc |= s[i] << (8 * i)
    return [(acc >> (26 * i)) & MASK for i in range(5)]

def block_limbs(msg, off, cnt):
    # 本块 cnt 字节小端 + 高位 1（位置 2^(8*cnt)）：满块 cnt=16 → 2^128，偏块 2^(8*cnt)
    acc = 0
    for j in range(cnt):
        acc |= msg[off + j] << (8 * j)
    acc += (1 << (8 * cnt))
    return [(acc >> (26 * i)) & MASK for i in range(5)]

def addmul(h, r, t):
    h0, h1, h2, h3, h4 = h
    r0, r1, r2, r3, r4 = r
    t0, t1, t2, t3, t4 = t
    # h += t
    h0 += t0; h1 += t1; h2 += t2; h3 += t3; h4 += t4
    d0 = h0 * r0
    d1 = h0 * r1 + h1 * r0
    d2 = h0 * r2 + h1 * r1 + h2 * r0
    d3 = h0 * r3 + h1 * r2 + h2 * r1 + h3 * r0
    d4 = h0 * r4 + h1 * r3 + h2 * r2 + h3 * r1 + h4 * r0
    d5 = h1 * r4 + h2 * r3 + h3 * r2 + h4 * r1
    d6 = h2 * r4 + h3 * r3 + h4 * r2
    d7 = h3 * r4 + h4 * r3
    d8 = h4 * r4
    # fold 高肢 (2^130 ≡ 5 mod 2^130-5)：d[5..8] 全值 ×5 折入低肢
    d3 += 5 * d8
    d2 += 5 * d7
    d1 += 5 * d6
    d0 += 5 * d5
    # carry 低链
    c = d0 >> 26; d0 &= MASK; d1 += c
    c = d1 >> 26; d1 &= MASK; d2 += c
    c = d2 >> 26; d2 &= MASK; d3 += c
    c = d3 >> 26; d3 &= MASK; d4 += c
    c = d4 >> 26; d4 &= MASK; h0 = d0 & MASK; h1 = d1 & MASK; h2 = d2 & MASK; h3 = d3 & MASK; h4 = d4 & MASK
    h0 += c * 5
    # normalize
    c = h0 >> 26; h0 &= MASK; h1 += c
    c = h1 >> 26; h1 &= MASK; h2 += c
    c = h2 >> 26; h2 &= MASK; h3 += c
    c = h3 >> 26; h3 &= MASK; h4 += c
    c = h4 >> 26; h4 &= MASK; h0 += c * 5
    return [h0, h1, h2, h3, h4]

def sys_emit(tag_limbs):
    # 5 个 26-bit 肢 → 16 字节小端
    acc = 0
    for i in range(5):
        acc |= tag_limbs[i] << (26 * i)
    return (acc & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF).to_bytes(16, 'little')

def poly1305(key, msg):
    r = load_r(key)
    s = load_s(key)
    h = [0, 0, 0, 0, 0]
    n = len(msg)
    pos = 0
    nblocks = (n + 15) // 16   # 每 16 字节一块，末块可短
    b = 0
    while b < nblocks:
        remb = n - pos
        cnt = remb if remb < 16 else 16
        h = addmul(h, r, block_limbs(msg, pos, cnt))
        pos += cnt
        b += 1
    # finish: reduce h < p (=2^130-5)，再 h+s mod 2^130 → 低 128 位
    h0, h1, h2, h3, h4 = h
    # fully carry
    c = h4 >> 26; h4 &= MASK; h0 += c * 5
    c = h0 >> 26; h0 &= MASK; h1 += c
    c = h1 >> 26; h1 &= MASK; h2 += c
    c = h2 >> 26; h2 &= MASK; h3 += c
    c = h3 >> 26; h3 &= MASK; h4 += c
    # h - p (p limbs [0x3fffffb,0x3ffffff,0x3ffffff,0x3ffffff,0x3ffffff])
    g0 = h0 + 5; c = g0 >> 26; g0 &= MASK
    g1 = h1 + c; c = g1 >> 26; g1 &= MASK
    g2 = h2 + c; c = g2 >> 26; g2 &= MASK
    g3 = h3 + c; c = g3 >> 26; g3 &= MASK
    g4 = h4 + c - 0x4000000
    mask = -1 if g4 >= 0 else 0   # h ≥ p（g4≥0）→ 选 g
    g0 &= mask; g1 &= mask; g2 &= mask; g3 &= mask; g4 &= mask
    mask = ~mask
    h0 = (h0 & mask) | g0
    h1 = (h1 & mask) | g1
    h2 = (h2 & mask) | g2
    h3 = (h3 & mask) | g3
    h4 = (h4 & mask) | g4
    # h + s
    s0, s1, s2, s3, s4 = s
    c = h4
    h4 = s4
    h0 += s0; c1 = h0 >> 26; h0 &= MASK; h1 += s1 + c1; c1 = h1 >> 26; h1 &= MASK
    h2 += s2 + c1; c1 = h2 >> 26; h2 &= MASK
    h3 += s3 + c1; c1 = h3 >> 26; h3 &= MASK
    h4 += c + c1
    # carry h4 low bits to fold (mod 2^130)
    c1 = h4 >> 26; h4 &= MASK; h0 += c1 * 5
    c1 = h0 >> 26; h0 &= MASK; h1 += c1
    c1 = h1 >> 26; h1 &= MASK; h2 += c1
    c1 = h2 >> 26; h2 &= MASK; h3 += c1
    c1 = h3 >> 26; h3 &= MASK; h4 += c1
    return sys_emit([h0, h1, h2, h3, h4]).hex()

def txt_to_bytes(s):
    return s.encode('ascii')

def reps(c, n):
    return bytes([c]) * n

def main():
    # RFC 8439 §2.5.2 验证向量
    key_rfc = bytes.fromhex('85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b')
    msg_rfc = b'Cryptographic Forum Research Group'
    tag = poly1305(key_rfc, msg_rfc)
    rfc_tag = 'a8061dc1305136c6c22b8baf0c0127a9'
    print("RFC self-check:", "OK" if tag == rfc_tag else "FAIL got " + tag)
    if tag != rfc_tag:
        sys.exit(1)
    # 4 组探针向量
    vecs = [
        ("vec1_rfc", "85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b", b"Cryptographic Forum Research Group"),
        ("vec2_allzero_key", "00" * 32, b"Cryptographic Forum Research Group"),
        ("vec3_empty_msg", "0f0e0d0c0b0a09080706050403020100d8d9dadbdcdddedfe0e1e2e3e4e5e6e7", b""),
        ("vec4_multiblock", "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f", b"a" * 48),
    ]
    for name, khx, msg in vecs:
        t = poly1305(bytes.fromhex(khx), msg)
        if name == "vec3_empty_msg":
            print("%s key=%s" % (name, khx))
            print("   msg=<empty>")
        elif name == "vec4_multiblock":
            print("%s key=%s" % (name, khx))
            print("   msg=48*'a'")
        else:
            print("%s key=%s" % (name, khx))
            print("   msg=%s" % msg.decode())
        print("   tag=%s" % t)

if __name__ == "__main__":
    main()