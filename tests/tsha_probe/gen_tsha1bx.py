# -*- coding: utf-8 -*-
# tsha1b / tsha1x 参考生成器（纯 Python，与 std/tsha1.tie 对照，仅用于向量生成与复现）。
# 设计（docs/superpowers/specs/2026-08-30-tsha1-tri-quad-track-design.md §2，b 增第三轨海绵）：
#   tsha1b-256：轨道用平衡三进制位平面运算（tadd2 平衡加 / tmul2 平衡乘 /
#     quant3 majority / 旋转混洗）；三轨并行——轨 A(v[0..7])、轨 B(v[8..15]) 各 4 个
#     三进制字，外加轨 C 海绵轨（v[16..23]，rate=v[16..19]、capacity=v[20..23]）独立
#     演化，每轮消息平面交替注入双轨并对海绵 rate 做吸收/置换，整链压缩完后再跑 S=4 轮
#     一体化收束轮（最后综合）并投影 8 字。
#   tsha1x-256：加强档 = 对 f 与 b 的输出做多次排列组合再算（固定排列表 PATT，多轮
#     π_i 混合，每轮对上一状态再做 digest_f/digest_b）。
# trit 表示（层内标准）：位平面——每个 u64 存 32 trit，高 32 位为幅值位平面、低 32 位为
#   符号位平面；运算全走 &/^/|/<<。(M=幅值, N=符号) 两个 32 位字。
# 常量定制（可复现）：标准种子 + PRNG 扩展（SHA-256(SEED || u64be(k)) 计数器流）。
import hashlib
from gen_tsha1fr import fr_consts, SEED_F, tsha1f   # f 档已统一为三进制双轨并行参考
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

def gen_perm_16(stream):
    perm = list(range(16))
    for i in range(15, 0, -1):
        j = next(stream) % (i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    return perm

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

def le_word(blk, k):
    v = 0
    for j in range(4):
        b = blk[k * 4 + j] if k * 4 + j < len(blk) else 0
        v |= b << (8 * j)
    return v & M32

def g_f(v, a, b, c, d, x, y):
    v[a] = (v[a] + v[b] + x) & M32
    v[d] = rotr(v[d] ^ v[a], 16)
    v[c] = (v[c] + v[d]) & M32
    v[b] = rotr(v[b] ^ v[c], 12)
    v[a] = (v[a] + v[b] + y) & M32
    v[d] = rotr(v[d] ^ v[a], 8)
    v[c] = (v[c] + v[d]) & M32
    v[b] = rotr(v[b] ^ v[c], 7)

# ---- tsha1b 常量（IV / 轮常量；海绵轨轮常量 bscon 独立种子，见 §2.2）----
SEED_B = b"TSHA1-2026-b-256-v1"
SEED_S = b"TSHA1-2026-b-sponge-v1"
def tsha1b_consts():
    st = byte_stream(SEED_B)
    iv = gen_words(st, 8)
    sig = []
    for _ in range(10):
        sig += gen_perm_16(st)
    sbox = gen_perm_16(st)
    rcon = [gen_words(st, 1)[0] for _ in range(16)]
    return iv, sig, sbox, rcon

def tsha1b_scon():
    st = byte_stream(SEED_S)
    return [gen_words(st, 1)[0] for _ in range(16)]

# 平衡三进制（balanced mod 3）两位 trit 相加，位切片实现，无进位（作扩散混合）。
def tadd2(Ma, Na, Mb, Nb):
    aP = Ma & ~Na; aN = Ma & Na
    bP = Mb & ~Nb; bN = Mb & Nb
    o_pos = ((~Ma & Mb & ~Nb) | (Ma & ~Na & ~Mb) | (aN & bN)) & M32
    o_neg = ((~Ma & Mb & Nb) | (Ma & Na & ~Mb) | (aP & bP)) & M32
    return (o_pos | o_neg) & M32, o_neg & M32

# 平衡三进制（balanced mod 3）两位 trit 相乘（±1·±1 = ±1，0 吸收为 0），位切片实现。
def tmul2(Ma, Na, Mb, Nb):
    amp = (Ma & Mb) & M32
    no = ((Na ^ Nb) & amp) & M32
    return amp, no

# majority 量化：三组位平面逐 trit 取签，+1 计数 ≥2 则该位为 1，否则 0（含平局→0）。
def quant3(m0, n0, m1, n1, m2, n2):
    A = m0 & ~n0
    B = m1 & ~n1
    C = m2 & ~n2
    return ((A & B) | (B & C) | (C & A)) & M32

# ---- tsha1b-256 三进制三轨并行压缩 + 最后综合（第三轨 = 海绵轨，见 §2.1-2.5）----
RB = 14
S = 4

# 单 64 字节块压缩（三进制三轨并行；轨 A = v[0..7]、轨 B = v[8..15]、
#   轨 C 海绵 = v[16..23]（rate=v[16..19]、capacity=v[20..23]））。
# 末块（last=True）时把海绵 capacity v[20..23] 填回 sp（4 字），供 digest 终筛前折回链值。
def tsha1b_compress(h, blk, t_lo, t_hi, last, iv, rcon, scon, sp):
    tvs = [byte_trit(blk[j])[1] for j in range(64)]
    M, N = planes(tvs, 64)
    M0, M1 = M[0], M[1]; N0, N1 = N[0], N[1]
    skey = 0
    for j in range(64):
        bits3, tv = byte_trit(blk[j])
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    v = [0] * 24
    # 初始化双轨（链值 h / IV / 计数器 / 末块）
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
    # 初始化海绵轨（§2.1；rate/capacity 由链值 h 与 IV 派生）
    v[16] = h[0]; v[17] = rotr(h[4], 7)
    v[18] = h[1]; v[19] = rotr(h[5], 13)
    v[20] = iv[0]; v[21] = rotr(iv[4], 7)
    v[22] = iv[1]; v[23] = rotr(iv[5], 13)
    if last:
        v[19] ^= M32                        # 末块标记：海绵 padding 边界
    v = [x & M32 for x in v]
    # 三进制三轨并行轮
    for r in range(RB):
        rA = (r * 3 + (skey & 7)) & 31
        rB = (r * 7 + ((skey >> 3) & 7)) & 31
        mA = (r * 5 + ((skey >> 6) & 7)) & 31
        mB = (r * 11 + ((skey >> 9) & 7)) & 31
        # 轨 A 并行扩散（平衡加 + 平衡乘 + majority）
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
        # ==== 海绵轨处理（§2.3：吸收 → 海绵置换 → 海绵常量注入 → 双轨耦合）====
        sA = (r * 3 + ((skey >> 12) & 7)) & 31
        sB = (r * 7 + ((skey >> 15) & 7)) & 31
        # 1. 吸收：消息平面注入海绵 rate
        a0 = tadd2(v[16], v[17], rrp(M0, sA), rrp(N0, sA))
        v[16], v[17] = a0
        a1 = tadd2(v[18], v[19], rrp(M1, sB), rrp(N1, sB))
        v[18], v[19] = a1
        # 2. 海绵置换（8 字环式，1 轮）
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
        # 3. 轮常量注入（海绵轨独立常量）
        v[16] ^= scon[r & 15]
        v[19] ^= rrp(scon[(r + 3) & 15], r * 3)
        # 4. 与轨 A/B 双向耦合（海绵 rate 出 → 轨 A/B；轨 A/B 回填 capacity）
        c0 = tadd2(v[0], v[1], rrp(v[16], r * 5), rrp(v[17], r * 5))
        v[0], v[1] = c0
        c1 = tadd2(v[8], v[9], rrp(v[18], r * 7), rrp(v[19], r * 7))
        v[8], v[9] = c1
        c2 = tadd2(v[20], v[21], rrp(v[4], r * 11), rrp(v[5], r * 11))
        v[20], v[21] = c2
        c3 = tadd2(v[22], v[23], rrp(v[12], r * 13), rrp(v[13], r * 13))
        v[22], v[23] = c3
        # 5. 轮常量注入（轨 A/B，既有不变）
        v[0] ^= rcon[r & 15]
        v[9] ^= rrp(rcon[(r + 1) & 15], r * 5)
        v = [x & M32 for x in v]
    # 折回链值（双轨 + 海绵 rate，见 §2.4）
    for i in range(8):
        h[i] = (h[i] ^ v[2 * i] ^ rrp(v[2 * i + 1], i * 3)
                ^ rrp(v[16 + (i & 3) * 2], i * 7)
                ^ rrp(v[17 + (i & 3) * 2], i * 7)) & M32
    if last:
        sp[0] = v[20]; sp[1] = v[21]; sp[2] = v[22]; sp[3] = v[23]

# 最后综合（终筛）：链 h 重新载入双轨，S 轮一体化收束后投影 8 字
def tsha1b_fin(h):
    v = [0] * 16
    v[0] = h[0]; v[1] = rotr(h[4], 7)
    v[2] = h[1]; v[3] = rotr(h[5], 7)
    v[4] = h[2]; v[5] = rotr(h[6], 7)
    v[6] = h[3]; v[7] = rotr(h[7], 7)
    v[8] = rotr(h[0], 13); v[9] = rotr(h[4], 13)
    v[10] = rotr(h[1], 13); v[11] = rotr(h[5], 13)
    v[12] = rotr(h[2], 13); v[13] = rotr(h[6], 13)
    v[14] = rotr(h[3], 13); v[15] = rotr(h[7], 13)
    for sf in range(S):
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

def tsha1b(msg, iv, rcon, scon):
    h = iv[:]
    h[0] ^= 0x01010000 ^ 32
    n = len(msg)
    sp = [0, 0, 0, 0]
    t_lo = t_hi = 0
    pos = 0
    while pos + 64 < n:
        t_hi = (t_hi + carry32(t_lo, 64)) & M32
        t_lo = (t_lo + 64) & M32
        tsha1b_compress(h, list(msg[pos:pos + 64]), t_lo, t_hi, False, iv, rcon, scon, sp)
        pos += 64
    rem = n - pos
    t_hi = (t_hi + carry32(t_lo, rem)) & M32
    t_lo = (t_lo + rem) & M32
    pad = list(msg[pos:]) + [0] * (64 - rem)
    tsha1b_compress(h, pad[:64], t_lo, t_hi, True, iv, rcon, scon, sp)
    # 末块海绵 capacity 折回链值（终筛前，见 §2.5）
    h[0] ^= sp[0]; h[1] ^= rotr(sp[1], 7)
    h[2] ^= sp[2]; h[3] ^= rotr(sp[3], 7)
    h = [x & M32 for x in h]
    tsha1b_fin(h)     # 最后综合（终筛）
    return ''.join('%08x' % w for w in h)

# ---- tsha1x-256（f+b 排列组合再算）----
# 固定排列表 PATT：每轮从 u=digest_f(state)、w=digest_b(state) 各取 16-hex 四分
#   （u0..u3 / w0..w3），按排列拼接回 64-hex 状态。顺序固定、可复现。
NX = 6
PATT = [
    ["u0", "w0", "u1", "w1"],
    ["w2", "u2", "w3", "u3"],
    ["u3", "u0", "w2", "w1"],
    ["w0", "u1", "w3", "u2"],
    ["u2", "w1", "u0", "w3"],
    ["w0", "u3", "w2", "u1"],
]

def digest_b(msg, ivb, rcon, scon):
    return tsha1b(msg, ivb, rcon, scon)

def tsha1x_ref(msg, ivf, rconf, ivb, rcon, scon):
    # 首状态 = f 与 b 各自 64-hex 输出直接拼接（128-hex），再进入 NX 轮排列组合
    state = tsha1f(msg, ivf, rconf) + digest_b(msg, ivb, rcon, scon)
    for i in range(NX):
        # 与 tie 一致：把 hex 状态按 ASCII 字节喂回（str 为字节语义）
        inp = state.encode('ascii')
        u = tsha1f(inp, ivf, rconf)
        w = digest_b(inp, ivb, rcon, scon)
        out = ""
        for spec in PATT[i]:
            s = int(spec[1]) * 16
            out += (u if spec[0] == "u" else w)[s:s + 16]
        state = out
    return state   # 64-hex = 256 位

def reps(c, n):
    return bytes([c]) * n

def main():
    iv_f, rcon_f = fr_consts(SEED_F)
    ivb, sigb, sbox, rcon = tsha1b_consts()
    scon = tsha1b_scon()
    print("IV_B   = " + "".join("%08x" % w for w in ivb))
    print("RCON_B = " + "".join("%08x" % w for w in rcon))
    print("SCON_B = " + "".join("%08x" % w for w in scon))
    for name, ln in [("empty", 0), ("abc", 3), ("a1000", 1000), ("b55", 55),
                     ("b56", 56), ("b63", 63), ("b64", 64), ("b65", 65),
                     ("b127", 127), ("b128", 128), ("b129", 129), ("b256", 256)]:
        msg = b"" if ln == 0 else (b"abc" if ln == 3 else reps(ord("a"), ln))
        print("B  %-5s %s" % (name, tsha1b(msg, ivb, rcon, scon)))
        print("X  %-5s %s" % (name, tsha1x_ref(msg, iv_f, rcon_f, ivb, rcon, scon)))

if __name__ == "__main__":
    main()