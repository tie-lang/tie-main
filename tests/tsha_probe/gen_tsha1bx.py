# -*- coding: utf-8 -*-
# tsha1b / tsha1x 参考生成器（纯 Python，与 std/tsha1.tie 对照，仅用于向量生成与复现）。
# 设计（docs/superpowers/specs/2026-08-29-plugin-kernel-design.md §6.6）：
#   tsha1b-256：A 骨架 = 双轨并行压缩（B 轨 = tsha1f 同构 ARX G 网络；T 轨 = trit 位平面
#     扩散），每轮互转（B→T 分段展开入 T 轨、T→B majority 量化回 B 轨），混入 S-盒/位切片
#     + SPN 强化（Ascon 型：nibble S 盒 + 旋-异或线性扩散 + 轮常量），B 轨轮数 RB=14 ≥ tsha1f。
#   tsha1x-256：加强档 = 对 f 与 b 的输出做多次排列组合再算（固定排列表 PATT，多轮
#     π_i 混合，每轮对上一状态再做 digest_f/digest_b）。
# trit 表示（层内标准，与 gen_vectors.py 同）：位平面——每个 u64 存 32 trit，高 32 位为
#   幅值位平面、低 32 位为符号位平面；运算全走 &/^/|/<<。(M=幅值, N=符号) 两个 32 位字。
# 常量定制（可复现）：标准种子 + PRNG 扩展（SHA-256(SEED || u64be(k)) 计数器流）。
import hashlib
from gen_vectors import tsha1f_consts, tsha1f
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

# ---- tsha1b 常量 ----
SEED_B = b"TSHA1-2026-b-256-v1"
def tsha1b_consts():
    st = byte_stream(SEED_B)
    iv = gen_words(st, 8)
    sig = []
    for _ in range(10):
        sig += gen_perm_16(st)
    sbox = gen_perm_16(st)
    rcon = [gen_words(st, 1)[0] for _ in range(16)]
    return iv, sig, sbox, rcon

# 平衡三进制（balanced mod 3）两位 trit 相加，位切片实现，无进位（作扩散混合）。
def tadd2(Ma, Na, Mb, Nb):
    aP = Ma & ~Na; aN = Ma & Na
    bP = Mb & ~Nb; bN = Mb & Nb
    o_pos = ((~Ma & Mb & ~Nb) | (Ma & ~Na & ~Mb) | (aN & bN)) & M32
    o_neg = ((~Ma & Mb & Nb) | (Ma & Na & ~Mb) | (aP & bP)) & M32
    return (o_pos | o_neg) & M32, o_neg & M32

# majority 量化：三组位平面逐 trit 取签，+1 计数 ≥2 则该位为 1，否则 0（含平局→0）。
def quant3(m0, n0, m1, n1, m2, n2):
    A = m0 & ~n0
    B = m1 & ~n1
    C = m2 & ~n2
    return ((A & B) | (B & C) | (C & A)) & M32

# SPN 强化层（Ascon 型：nibble S 盒 + 旋-异或线性扩散 + 轮常量），作用于 v[0..7]。
def spn_b(v, r, sbox, rcon):
    for w in range(8):
        x = v[w]; nx = 0
        for nb in range(8):
            nx |= (sbox[(x >> (4 * nb)) & 0xF] << (4 * nb))
        v[w] = nx & M32
    v[0] ^= rotr(v[0], 5) ^ rotr(v[1], 25)
    v[1] ^= rotr(v[1], 7) ^ rotr(v[2], 19)
    v[2] ^= rotr(v[2], 9) ^ rotr(v[3], 21)
    v[3] ^= rotr(v[3], 11) ^ rotr(v[0], 27)
    v[4] ^= rotr(v[4], 13) ^ rotr(v[5], 29)
    v[5] ^= rotr(v[5], 15) ^ rotr(v[6], 3)
    v[6] ^= rotr(v[6], 17) ^ rotr(v[7], 23)
    v[7] ^= rotr(v[7], 1) ^ rotr(v[4], 31)
    v[0] ^= v[4]; v[1] ^= v[5]; v[2] ^= v[6]; v[3] ^= v[7]
    v[4] ^= v[0]; v[5] ^= v[1]; v[6] ^= v[2]; v[7] ^= v[3]
    v[0] ^= (rcon[r & 15] + r) & M32
    v[2] ^= (rcon[(r + 1) & 15] + r + 1) & M32

RB = 14
def tsha1b_compress(h, blk, t_lo, t_hi, last, iv, sig, sbox, rcon):
    m = [le_word(blk, k) for k in range(16)]
    tvs = [byte_trit(blk[j])[1] for j in range(64)]
    M, N = planes(tvs, 64)
    M0, M1 = M[0], M[1]; N0, N1 = N[0], N[1]
    skey = 0
    for j in range(64):
        bits3, tv = byte_trit(blk[j])
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    PM, PN = M0, N0                       # T 轨位平面累加器（32 trit）
    v = h[:] + iv[:]
    v[12] ^= t_lo; v[13] ^= t_hi
    if last:
        v[14] ^= M32
    for r in range(RB):
        sr = r if r < 10 else r - 10
        base = sr * 16
        rd = (skey + r * 7) & 15
        sx = [(sig[base + j] + rd) & 15 for j in range(16)]
        g_f(v, 0, 4, 8, 12, m[sx[0]], m[sx[1]])
        g_f(v, 1, 5, 9, 13, m[sx[2]], m[sx[3]])
        g_f(v, 2, 6, 10, 14, m[sx[4]], m[sx[5]])
        g_f(v, 3, 7, 11, 15, m[sx[6]], m[sx[7]])
        g_f(v, 0, 5, 10, 15, m[sx[8]], m[sx[9]])
        g_f(v, 1, 6, 11, 12, m[sx[10]], m[sx[11]])
        g_f(v, 2, 7, 8, 13, m[sx[12]], m[sx[13]])
        g_f(v, 3, 4, 9, 14, m[sx[14]], m[sx[15]])
        # B→T 互转：B 轨输出 v0,v1 分段展开入 T 轨
        PM, PN = tadd2(PM, PN, rotl(v[0] & M32, (r * 3) & 31), rotl(v[1] & M32, (r * 5) & 31))
        # T 轨 trit 位平面扩散（全位运算：balanced add + 旋转 + 混洗）
        PM, PN = tadd2(PM, PN, rotr((M1 + r) & M32, (r * 2) & 31), rotr(rotl(N1, (r * 3) & 31), (r * 7) & 31))
        PM = (PM ^ rotl(PN, (r * 5) & 31)) & M32
        PN = (PN ^ rotl(PM, (r * 2) & 31)) & M32
        PM = (rotl(PM, 16) ^ PM) & M32     # 16 位半字混洗（交换两半后异或回）
        # T→B 互转：majority 量化回 B 轨
        W0 = quant3(M0, N0, PM, PN, rotl(M1, (r * 9) & 31), rotl(N1, (r * 11) & 31))
        W1 = quant3(rotl(M1, 13), rotl(N1, 7), PM, PN, rotl(M0, (r * 3) & 31), rotl(N0, (r * 5) & 31))
        v[2] ^= rotl(W0, (r * 7) & 31)
        v[6] ^= rotl(W1, (r * 11) & 31)
        v[10] ^= rotr(PM, (r * 3) & 31)
        v[14] ^= rotl(PN, (r * 5) & 31)
        if r % 3 == 2:
            spn_b(v, r, sbox, rcon)        # 每 3 轮插一层 SPN
    for i in range(8):
        h[i] ^= v[i] ^ v[i + 8]

def tsha1b(msg, iv, sig, sbox, rcon):
    h = iv[:]
    h[0] ^= 0x01010000 ^ 32
    n = len(msg)
    t_lo = t_hi = 0
    pos = 0
    while pos + 64 < n:
        t_hi = (t_hi + carry32(t_lo, 64)) & M32
        t_lo = (t_lo + 64) & M32
        tsha1b_compress(h, list(msg[pos:pos + 64]), t_lo, t_hi, False, iv, sig, sbox, rcon)
        pos += 64
    rem = n - pos
    t_hi = (t_hi + carry32(t_lo, rem)) & M32
    t_lo = (t_lo + rem) & M32
    pad = list(msg[pos:]) + [0] * (64 - rem)
    tsha1b_compress(h, pad[:64], t_lo, t_hi, True, iv, sig, sbox, rcon)
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

def digest_b(msg, ivb, sigb, sbox, rcon):
    return tsha1b(msg, ivb, sigb, sbox, rcon)

def tsha1x_ref(msg, ivf, sigf, ivb, sigb, sbox, rcon):
    # 首状态 = f 与 b 各自 64-hex 输出直接拼接（128-hex），再进入 NX 轮排列组合
    state = tsha1f(msg, ivf, sigf) + digest_b(msg, ivb, sigb, sbox, rcon)
    for i in range(NX):
        # 与 tie 一致：把 hex 状态按 ASCII 字节喂回（str 为字节语义）
        inp = state.encode('ascii')
        u = tsha1f(inp, ivf, sigf)
        w = digest_b(inp, ivb, sigb, sbox, rcon)
        out = ""
        for spec in PATT[i]:
            s = int(spec[1]) * 16
            out += (u if spec[0] == "u" else w)[s:s + 16]
        state = out
    return state   # 64-hex = 256 位

def reps(c, n):
    return bytes([c]) * n

def main():
    iv_f, sig_f = tsha1f_consts()
    ivb, sigb, sbox, rcon = tsha1b_consts()
    print("IV_B   = " + "".join("%08x" % w for w in ivb))
    print("SIG_B  = " + "".join("%x" % s for s in sigb))
    print("SBOX_B = " + "".join("%x" % s for s in sbox))
    print("RCON_B = " + "".join("%08x" % w for w in rcon))
    for name, ln in [("empty", 0), ("abc", 3), ("a1000", 1000), ("b55", 55),
                     ("b56", 56), ("b63", 63), ("b64", 64), ("b65", 65),
                     ("b127", 127), ("b128", 128), ("b129", 129), ("b256", 256)]:
        msg = b"" if ln == 0 else (b"abc" if ln == 3 else reps(ord("a"), ln))
        print("B  %-5s %s" % (name, tsha1b(msg, ivb, sigb, sbox, rcon)))
        print("X  %-5s %s" % (name, tsha1x_ref(msg, iv_f, sig_f, ivb, sigb, sbox, rcon)))

if __name__ == "__main__":
    main()