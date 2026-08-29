# -*- coding: utf-8 -*-
# tsha1f / tsha1r 参考生成器（纯 Python，与 std/tsha1.tie 对照，仅用于向量生成与复现）。
# 设计（docs/superpowers/specs/2026-08-29-plugin-kernel-design.md §6.6，内部摘要按
#   「三进制 + 双轨并行 + 最后综合」统一重设计，废弃 BLAKE-ARX/SPN 骨架）：
#   三档全部复用同一套三进制双轨并行压缩器（与 tsha1b 同构，仅轮数/常量/输出字数不同）：
#     - 轨道全用平衡三进制位平面运算（tadd2 平衡加 / tmul2 平衡乘 / quant3 majority /
#       rrp 旋转混洗）；双轨并行——轨 A(v[0..7]) 与轨 B(v[8..15]) 各 4 个三进制字独立
#       扩散，每轮消息平面交替注入两轨并做轨间耦合/轮常量；
#     - 整链压缩完后再跑 S=4 轮一体化收束轮（最后综合 fin）并投影。
#   tsha1f-256：快速档，R_F=12 轮（三档中最快），链 8 字 → 输出 64 hex（32 字节）。
#     常量：SEED_F = "TSHA1-2026-f-256-v1" → IV(8 字) + RCON(16 字)。
#   tsha1r-128：嵌入式/轻量档，R_R=8 轮（轮数最少），链 8 字 → 输出仅前 4 字
#     （16 字节 → 32 hex）。常量：SEED_R = "TSHA1-2026-r-128-v1" → IV(8 字) + RCON(16 字)。
# trit 表示（层内标准）：位平面——每个 u64 存 32 trit，高 32 位为幅值位平面、低 32 位为
#   符号位平面；运算全走 &/^/|/<<。(M=幅值, N=符号) 两个 32 位字。
# 常量定制（可复现）：标准种子 + PRNG 扩展（SHA-256(SEED || u64be(k)) 计数器流）。
import hashlib
M32 = 0xFFFFFFFF

def byte_stream(seed):
    k = 0
    while True:
        for b in hashlib.sha256(seed + k.to_bytes(8, 'big')).digest():
            yield b
        k += 1

def gen_words(stream, nwords):
    out = []
    for _ in range(nwords):
        v = 0
        for _ in range(4):
            v = ((v << 8) | next(stream)) & M32
        out.append(v)
    return out

def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & M32
def rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & M32
def rrp(x, r):
    return rotr(x, r & 31)

def byte_trit(b):
    bits3 = b & 7
    tf = (b >> 6) & 3
    t = tf - 1
    tv = -1 if t < 0 else (0 if t == 0 else 1)
    return bits3, tv

def planes(tvs, count):
    nm = (count + 31) // 32
    M = [0] * nm; N = [0] * nm
    for p in range(count):
        tv = tvs[p]
        if tv == 0:
            continue
        w = p // 32; bit = p % 32
        M[w] |= (1 << bit)
        if tv < 0:
            N[w] |= (1 << bit)
    return M, N

def carry32(a, b):
    return (a + b) >> 32

def tadd2(Ma, Na, Mb, Nb):
    aP = Ma & ~Na; aN = Ma & Na
    bP = Mb & ~Nb; bN = Mb & Nb
    o_pos = ((~Ma & Mb & ~Nb) | (Ma & ~Na & ~Mb) | (aN & bN)) & M32
    o_neg = ((~Ma & Mb & Nb) | (Ma & Na & ~Mb) | (aP & bP)) & M32
    return (o_pos | o_neg) & M32, o_neg & M32

def tmul2(Ma, Na, Mb, Nb):
    amp = (Ma & Mb) & M32
    no = ((Na ^ Nb) & amp) & M32
    return amp, no

def quant3(m0, n0, m1, n1, m2, n2):
    A = m0 & ~n0
    B = m1 & ~n1
    C = m2 & ~n2
    return ((A & B) | (B & C) | (C & A)) & M32

# ---- 通用三进制双轨并行压缩器 + 最后综合（与 tsha1b 完全同构，仅轮数 R 可调）----
# 复用 gen_tsha1bx.py 中的 tsha1b_compress / tsha1b_fin 结构。
def tri_compress(h, blk, t_lo, t_hi, last, iv, rcon, R):
    tvs = [byte_trit(blk[j])[1] for j in range(64)]
    M, N = planes(tvs, 64)
    M0, M1 = M[0], M[1]; N0, N1 = N[0], N[1]
    skey = 0
    for j in range(64):
        bits3, tv = byte_trit(blk[j])
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    v = [0] * 16
    v[0] = h[0]; v[1] = rotr(h[4], 7)
    v[2] = h[1]; v[3] = rotr(h[5], 7)
    v[4] = h[2]; v[5] = rotr(h[6], 7)
    v[6] = h[3]; v[7] = rotr(h[7], 7)
    v[8] = rotr(h[0], 13); v[9] = iv[0]
    v[10] = rotr(h[1], 13); v[11] = iv[1]
    v[12] = rotr(h[2], 13); v[13] = iv[2]
    v[14] = rotr(h[3], 13); v[15] = iv[3]
    v[0] ^= iv[4]; v[2] ^= iv[5]; v[4] ^= iv[6]; v[6] ^= iv[7]
    v[1] ^= t_lo; v[9] ^= t_hi
    if last:
        v[3] ^= M32
    v = [x & M32 for x in v]
    for r in range(R):
        rA = (r * 3 + (skey & 7)) & 31
        rB = (r * 7 + ((skey >> 3) & 7)) & 31
        mA = (r * 5 + ((skey >> 6) & 7)) & 31
        mB = (r * 11 + ((skey >> 9) & 7)) & 31
        s0 = tadd2(v[0], v[1], rrp(v[2], rA), rrp(v[3], rA))
        s1 = tadd2(v[2], v[3], rrp(v[4], rA + 5), rrp(v[5], rA + 5))
        s2 = tadd2(v[4], v[5], rrp(v[6], rA + 9), rrp(v[7], rA + 9))
        s3 = tadd2(v[6], v[7], rrp(v[0], rA + 13), rrp(v[1], rA + 13))
        p1 = tmul2(s0[0], s0[1], s2[0], s2[1])
        p2 = tmul2(s1[0], s1[1], s3[0], s3[1])
        mjA = quant3(s0[0], s0[1], s1[0], s1[1], s2[0], s2[1])
        v[0] = s0[0]; v[1] = s0[1]
        v[2] = s1[0] ^ p1[0]; v[3] = s1[1] ^ p1[1]
        v[4] = s2[0] ^ p2[0]; v[5] = s2[1] ^ p2[1]
        v[6] = s3[0] ^ mjA; v[7] = s3[1] ^ rrp(mjA, rA + 7)
        u0 = tadd2(v[8], v[9], rrp(v[10], rB), rrp(v[11], rB))
        u1 = tadd2(v[10], v[11], rrp(v[12], rB + 4), rrp(v[13], rB + 4))
        u2 = tadd2(v[12], v[13], rrp(v[14], rB + 8), rrp(v[15], rB + 8))
        u3 = tadd2(v[14], v[15], rrp(v[8], rB + 12), rrp(v[9], rB + 12))
        q1 = tmul2(u0[0], u0[1], u2[0], u2[1])
        q2 = tmul2(u1[0], u1[1], u3[0], u3[1])
        mjB = quant3(u0[0], u0[1], u1[0], u1[1], u2[0], u2[1])
        v[8] = u0[0]; v[9] = u0[1]
        v[10] = u1[0] ^ q1[0]; v[11] = u1[1] ^ q1[1]
        v[12] = u2[0] ^ q2[0]; v[13] = u2[1] ^ q2[1]
        v[14] = u3[0] ^ mjB; v[15] = u3[1] ^ rrp(mjB, rB + 6)
        im = tadd2(v[0], v[1], rrp(M0, mA), rrp(N0, mA))
        v[0], v[1] = im
        jm = tadd2(v[8], v[9], rrp(M1, mB), rrp(N1, mB))
        v[8], v[9] = jm
        cm = tadd2(v[4], v[5], v[10], v[11])
        v[4], v[5] = cm
        dm = tmul2(v[12], v[13], v[0], v[1])
        v[12], v[13] = dm
        em = tadd2(v[14], v[15], rrp(v[6], r * 3), rrp(v[7], r * 3))
        v[14], v[15] = em
        v[0] ^= rcon[r & 15]
        v[9] ^= rrp(rcon[(r + 1) & 15], r * 5)
        v = [x & M32 for x in v]
    for i in range(8):
        h[i] = (h[i] ^ v[2 * i] ^ rrp(v[2 * i + 1], i * 3)) & M32

def tri_fin(h):
    v = [0] * 16
    v[0] = h[0]; v[1] = rotr(h[4], 7)
    v[2] = h[1]; v[3] = rotr(h[5], 7)
    v[4] = h[2]; v[5] = rotr(h[6], 7)
    v[6] = h[3]; v[7] = rotr(h[7], 7)
    v[8] = rotr(h[0], 13); v[9] = rotr(h[4], 13)
    v[10] = rotr(h[1], 13); v[11] = rotr(h[5], 13)
    v[12] = rotr(h[2], 13); v[13] = rotr(h[6], 13)
    v[14] = rotr(h[3], 13); v[15] = rotr(h[7], 13)
    for sf in range(4):
        tmp = [0] * 16
        for t in range(8):
            t1 = (t + 1) & 7; t2 = (t + 2) & 7; t3 = (t + 3) & 7; t4 = (t + 4) & 7
            rot = (sf * 3 + t * 5) & 31
            am = tadd2(v[2 * t], v[2 * t + 1], rrp(v[2 * t1], rot), rrp(v[2 * t1 + 1], rot))
            pm = tmul2(v[2 * t3], v[2 * t3 + 1], rrp(v[2 * t4], rot + 1), rrp(v[2 * t4 + 1], rot + 1))
            mj = quant3(v[2 * t], v[2 * t + 1], v[2 * t2], v[2 * t2 + 1], am[0], am[1])
            tmp[2 * t] = (am[0] ^ pm[0] ^ mj) & M32
            tmp[2 * t + 1] = (am[1] ^ pm[1] ^ rrp(mj, rot + 3)) & M32
        v = tmp
    for i in range(8):
        h[i] = (h[i] ^ v[2 * i] ^ rotl(v[2 * i + 1], (i * 7) & 31)) & M32

# 通用壳：nwords=输出字数（f=8 全出；r=4 只取前 4 字）。
def dig_hex(msg, iv, rcon, R, sep, nwords):
    h = iv[:]
    h[0] ^= 0x01010000 ^ sep
    n = len(msg)
    t_lo = t_hi = 0
    pos = 0
    while pos + 64 < n:
        t_hi = (t_hi + carry32(t_lo, 64)) & M32
        t_lo = (t_lo + 64) & M32
        tri_compress(h, list(msg[pos:pos + 64]), t_lo, t_hi, False, iv, rcon, R)
        pos += 64
    rem = n - pos
    t_hi = (t_hi + carry32(t_lo, rem)) & M32
    t_lo = (t_lo + rem) & M32
    pad = list(msg[pos:]) + [0] * (64 - rem)
    tri_compress(h, pad[:64], t_lo, t_hi, True, iv, rcon, R)
    tri_fin(h)
    return ''.join('%08x' % w for w in h[:nwords])

# ---- 常量（SEED_F / SEED_R → IV(8) + RCON(16)，废弃 σ/S 盒）----
SEED_F = b"TSHA1-2026-f-256-v1"
SEED_R = b"TSHA1-2026-r-128-v1"
def fr_consts(seed):
    st = byte_stream(seed)
    iv = gen_words(st, 8)
    rcon = [gen_words(st, 1)[0] for _ in range(16)]
    return iv, rcon

def tsha1f(msg, iv, rcon):
    return dig_hex(msg, iv, rcon, R=12, sep=32, nwords=8)

def tsha1r(msg, iv, rcon):
    return dig_hex(msg, iv, rcon, R=8, sep=16, nwords=4)

def reps(c, n):
    return bytes([c]) * n

def main():
    iv_f, rcon_f = fr_consts(SEED_F)
    iv_r, rcon_r = fr_consts(SEED_R)
    print("IV_F   = " + "".join("%08x" % w for w in iv_f))
    print("RCON_F = " + "".join("%08x" % w for w in rcon_f))
    print("IV_R   = " + "".join("%08x" % w for w in iv_r))
    print("RCON_R = " + "".join("%08x" % w for w in rcon_r))
    for name, ln in [("empty", 0), ("abc", 3), ("a1000", 1000), ("b55", 55),
                     ("b56", 56), ("b63", 63), ("b64", 64), ("b65", 65),
                     ("b127", 127), ("b128", 128), ("b129", 129), ("b256", 256)]:
        msg = b"" if ln == 0 else (b"abc" if ln == 3 else reps(ord("a"), ln))
        print("F  %-5s %s" % (name, tsha1f(msg, iv_f, rcon_f)))
    for name, ln in [("empty", 0), ("abc", 3), ("a1000", 1000), ("b15", 15),
                     ("b16", 16), ("b17", 17), ("b31", 31), ("b32", 32),
                     ("b33", 33), ("b128", 128), ("b256", 256)]:
        msg = b"" if ln == 0 else (b"abc" if ln == 3 else reps(ord("a"), ln))
        print("R  %-5s %s" % (name, tsha1r(msg, iv_r, rcon_r)))

if __name__ == "__main__":
    main()