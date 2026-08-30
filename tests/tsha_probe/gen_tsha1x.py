# -*- coding: utf-8 -*-
# tsha1x 参考生成器（纯 Python，与 std/tsha1.tie 逐字节对照，仅用于向量生成与复现）。
# 设计（docs/superpowers/specs/2026-08-30-tsha1-tri-quad-track-design.md §3，四轨独立重构）：
#   tsha1x-256：加强档，四轨并行 + 最后综合，R_X=16 轮（四模型最高）。
#     轨 A（v[0..7]）与轨 B（v[8..15]）：三进制位平面双轨（复用 f/b 压缩器同构，
#       常量用独立 x 常量族 tsha_xiv/tsha_xrcon）；
#     轨 C（v[16..23]）海绵轨（rate=v[16..19]、capacity=v[20..23]，复用 §2 海绵语义，
#       常量复用 SEED_S 的 tsha_bscon）；
#     轨 D（v[24..27]，保留 v[28..31] 综合暂存）LFSR 反馈移位轨（第四种算法，非线性化
#       用 quant3 门控），常量用 SEED_XD 的 tsha_xdcon；
#   末段：四轨状态投影折叠 → fin_synth_x（终筛）→ 64 hex（内部摘要 32 字节）。
# trit 表示（层内标准）：位平面——每个 u64 存 32 trit，高 32 位为幅值位平面、低 32 位为
#   符号位平面；运算全走 &/^/|/<<。(M=幅值, N=符号) 两个 32 位字。
# 常量定制（可复现）：标准种子 + PRNG 扩展（SHA-256(SEED || u64be(k)) 计数器流）。
#   SEED_X  = "TSHA1-2026-x-256-v1"  → xiv(8) + xrcon(16)
#   SEED_XD = "TSHA1-2026-x-lfsr-v1" → xdcon(16)
#   轨 C 复用 SEED_S = "TSHA1-2026-b-sponge-v1" → bscon(16)（见 b）
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

# ---- tsha1x 常量（SEED_X / SEED_XD；轨 C 复用 SEED_S 的 bscon）----
SEED_X = b"TSHA1-2026-x-256-v1"
SEED_XD = b"TSHA1-2026-x-lfsr-v1"
SEED_S = b"TSHA1-2026-b-sponge-v1"

def tsha1x_consts():
    st = byte_stream(SEED_X)
    iv = gen_words(st, 8)
    rcon = [gen_words(st, 1)[0] for _ in range(16)]
    return iv, rcon

def tsha1x_dcon():
    st = byte_stream(SEED_XD)
    return [gen_words(st, 1)[0] for _ in range(16)]

def tsha1x_scon():
    st = byte_stream(SEED_S)
    return [gen_words(st, 1)[0] for _ in range(16)]

# ---- tsha1x-256 四轨并行压缩 + 最后综合（R_X = 16 轮）----
RX = 16

# 单 64 字节块压缩（四轨：轨 A/B 三进制双轨、轨 C 海绵、轨 D LFSR）。
# 末块（last=True）时把海绵 capacity v[20..23] 填回 sp（4 字），供 digest 终筛前折回链值。
def tsha1x_compress(h, blk, t_lo, t_hi, last, iv, rcon, scon, xdcon, sp):
    tvs = [byte_trit(blk[j])[1] for j in range(64)]
    M, N = planes(tvs, 64)
    M0, M1 = M[0], M[1]; N0, N1 = N[0], N[1]
    skey = 0
    for j in range(64):
        bits3, tv = byte_trit(blk[j])
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    v = [0] * 32
    # 初始化轨 A/B（双轨；链值 h / IV / 计数器 / 末块）
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
    # 初始化轨 C 海绵（rate/capacity 由链值 h 与 IV 派生，同 §2.1）
    v[16] = h[0]; v[17] = rotr(h[4], 7)
    v[18] = h[1]; v[19] = rotr(h[5], 13)
    v[20] = iv[0]; v[21] = rotr(iv[4], 7)
    v[22] = iv[1]; v[23] = rotr(iv[5], 13)
    if last:
        v[19] ^= M32                        # 末块标记：海绵 padding 边界
    # 初始化轨 D（LFSR，v[24..27]；d0..d3 = h 与 IV 的线性混合，固定且可复现）
    v[24] = (h[2] ^ iv[0]) & M32
    v[25] = (h[3] ^ rotr(iv[4], 11)) & M32
    v[26] = (h[6] ^ iv[2]) & M32
    v[27] = (h[7] ^ rotr(iv[6], 19)) & M32
    v = [x & M32 for x in v]
    # 四轨并行轮
    for r in range(RX):
        rA = (r * 3 + (skey & 7)) & 31
        rB = (r * 7 + ((skey >> 3) & 7)) & 31
        mA = (r * 5 + ((skey >> 6) & 7)) & 31
        mB = (r * 11 + ((skey >> 9) & 7)) & 31
        # 轨 A 并行扩散
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
        # 轨 B 并行扩散
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
        # 消息平面注入（轨 A ← M0,N0；轨 B ← M1,N1，旋转后平衡加）
        im = tadd2(v[0], v[1], rrp(M0, mA), rrp(N0, mA))
        v[0], v[1] = im
        jm = tadd2(v[8], v[9], rrp(M1, mB), rrp(N1, mB))
        v[8], v[9] = jm
        # 轨间耦合（隔轨平衡加 / 乘积 / 旋转传播）
        cm = tadd2(v[4], v[5], v[10], v[11])
        v[4], v[5] = cm
        dm = tmul2(v[12], v[13], v[0], v[1])
        v[12], v[13] = dm
        em = tadd2(v[14], v[15], rrp(v[6], r * 3), rrp(v[7], r * 3))
        v[14], v[15] = em
        # ==== 轨 C 海绵处理（§2.3：吸收 → 海绵置换 → 海绵常量 → 双轨耦合）====
        sA = (r * 3 + ((skey >> 12) & 7)) & 31
        sB = (r * 7 + ((skey >> 15) & 7)) & 31
        a0 = tadd2(v[16], v[17], rrp(M0, sA), rrp(N0, sA))
        v[16], v[17] = a0
        a1 = tadd2(v[18], v[19], rrp(M1, sB), rrp(N1, sB))
        v[18], v[19] = a1
        p0 = tadd2(v[16], v[17], rrp(v[18], sA + 1), rrp(v[19], sA + 1))
        p1 = tadd2(v[18], v[19], rrp(v[20], sA + 5), rrp(v[21], sA + 5))
        p2 = tadd2(v[20], v[21], rrp(v[22], sB + 2), rrp(v[23], sB + 2))
        p3 = tadd2(v[22], v[23], rrp(v[16], sB + 6), rrp(v[17], sB + 6))
        pp1 = tmul2(p0[0], p0[1], p2[0], p2[1])
        pp2 = tmul2(p1[0], p1[1], p3[0], p3[1])
        mj = quant3(p0[0], p0[1], p1[0], p1[1], p2[0], p2[1])
        v[16] = p0[0]; v[17] = p0[1]
        v[18] = p1[0] ^ pp1[0]; v[19] = p1[1] ^ pp1[1]
        v[20] = p2[0] ^ pp2[0]; v[21] = p2[1] ^ pp2[1]
        v[22] = p3[0] ^ mj; v[23] = p3[1] ^ rrp(mj, sA + 7)
        v[16] ^= scon[r & 15]
        v[19] ^= rrp(scon[(r + 3) & 15], r * 3)
        c0 = tadd2(v[0], v[1], rrp(v[16], r * 5), rrp(v[17], r * 5))
        v[0], v[1] = c0
        c1 = tadd2(v[8], v[9], rrp(v[18], r * 7), rrp(v[19], r * 7))
        v[8], v[9] = c1
        c2 = tadd2(v[20], v[21], rrp(v[4], r * 11), rrp(v[5], r * 11))
        v[20], v[21] = c2
        c3 = tadd2(v[22], v[23], rrp(v[12], r * 13), rrp(v[13], r * 13))
        v[22], v[23] = c3
        # ==== 轨 D（LFSR）处理（§3.3：反馈 → 吸收 → 移位(经 quant3 门控) → 与轨 A/B 耦合）====
        sX = (r * 11 + ((skey >> 18) & 7)) & 31
        fb = ((v[27] >> 16) ^ v[25]) & M32        # 反馈：抽高位混合
        v[24] = (v[24] ^ rrp(M0, sX)) & M32         # 吸收：消息平面注入 d0
        v[25] = (v[25] ^ rrp(N0, sX)) & M32         # 吸收：消息平面注入 d1
        qx = quant3(v[0], v[1], v[8], v[9], v[16], v[17])  # 非线性门控（轨 A/B/C 字对）
        nd0 = v[25]; nd1 = v[26]; nd2 = v[27]
        nd3 = (fb ^ qx) & M32
        v[24] = nd0 & M32; v[25] = nd1 & M32; v[26] = nd2 & M32; v[27] = nd3 & M32
        # 与轨 A/B 双向耦合（四向平衡加混写，回归写回两侧）
        x0 = tadd2(v[24], v[2], rrp(v[16], sX), rrp(v[8], sX))
        v[24] = x0[0] & M32; v[2] = x0[1] & M32
        x1 = tadd2(v[25], v[6], rrp(v[17], sX + 1), rrp(v[9], sX + 1))
        v[25] = x1[0] & M32; v[6] = x1[1] & M32
        x2 = tadd2(v[26], v[10], rrp(v[18], sX + 2), rrp(v[11], sX + 2))
        v[26] = x2[0] & M32; v[10] = x2[1] & M32
        x3 = tadd2(v[27], v[14], rrp(v[19], sX + 3), rrp(v[15], sX + 3))
        v[27] = x3[0] & M32; v[14] = x3[1] & M32
        # 轮常量注入（轨 D 用 xdcon；轨 A/B 用 xrcon）
        v[24] ^= xdcon[r & 15]
        v[27] ^= rrp(xdcon[(r + 4) & 15], r * 5)
        v[0] ^= rcon[r & 15]
        v[9] ^= rrp(rcon[(r + 1) & 15], r * 5)
        v = [x & M32 for x in v]
    # 四轨状态投影折回链值 h（轨 A/B 双轨 + 轨 C 海绵 rate + 轨 D 投影，见 §3.2）
    for i in range(8):
        h[i] = (h[i] ^ v[2 * i] ^ rrp(v[2 * i + 1], i * 3)
                ^ rrp(v[16 + (i & 3) * 2], i * 7)
                ^ rrp(v[17 + (i & 3) * 2], i * 7)
                ^ rrp(v[24 + (i & 1) * 2], i * 13)
                ^ rrp(v[25 + (i & 1) * 2], i * 13)) & M32
    if last:
        sp[0] = v[20]; sp[1] = v[21]; sp[2] = v[22]; sp[3] = v[23]

# 最后综合（终筛）：与 f/b/r 同构的 S=4 一体化收束轮，链 h 投影回 8 字。
def fin_synth_x(h):
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

def digest_x(msg, iv, rcon, scon, xdcon):
    h = iv[:]
    h[0] ^= 0x01010000 ^ 32
    n = len(msg)
    sp = [0, 0, 0, 0]
    t_lo = t_hi = 0
    pos = 0
    while pos + 64 < n:
        t_hi = (t_hi + carry32(t_lo, 64)) & M32
        t_lo = (t_lo + 64) & M32
        tsha1x_compress(h, list(msg[pos:pos + 64]), t_lo, t_hi, False, iv, rcon, scon, xdcon, sp)
        pos += 64
    rem = n - pos
    t_hi = (t_hi + carry32(t_lo, rem)) & M32
    t_lo = (t_lo + rem) & M32
    pad = list(msg[pos:]) + [0] * (64 - rem)
    tsha1x_compress(h, pad[:64], t_lo, t_hi, True, iv, rcon, scon, xdcon, sp)
    # 末块海绵 capacity 折回链值（终筛前）
    h[0] ^= sp[0]; h[1] ^= rotr(sp[1], 7)
    h[2] ^= sp[2]; h[3] ^= rotr(sp[3], 7)
    h = [x & M32 for x in h]
    fin_synth_x(h)     # 最后综合（终筛）
    return ''.join('%08x' % w for w in h)

def reps(c, n):
    return bytes([c]) * n

def main():
    iv, rcon = tsha1x_consts()
    xdcon = tsha1x_dcon()
    scon = tsha1x_scon()
    print("IV_X   = " + "".join("%08x" % w for w in iv))
    print("RCON_X = " + "".join("%08x" % w for w in rcon))
    print("DCON_X = " + "".join("%08x" % w for w in xdcon))
    print("SCON_S = " + "".join("%08x" % w for w in scon))
    for name, ln in [("empty", 0), ("abc", 3), ("a1000", 1000), ("b55", 55),
                     ("b56", 56), ("b63", 63), ("b64", 64), ("b65", 65),
                     ("b127", 127), ("b128", 128), ("b129", 129), ("b256", 256)]:
        msg = b"" if ln == 0 else (b"abc" if ln == 3 else reps(ord("a"), ln))
        print("X  %-5s %s" % (name, digest_x(msg, iv, rcon, scon, xdcon)))

if __name__ == "__main__":
    main()