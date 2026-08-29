# -*- coding: utf-8 -*-
# tsha1 参考生成器（纯 Python，与 std/tsha1.tie 对照，仅用于向量生成与复现）。
# 设计（docs/superpowers/specs/2026-08-29-plugin-kernel-design.md §6.6）：
#   tsha1f-256：B 骨架 = BLAKE-ARX 主体 + T 轨旁路扰动（消息经 trit 位平面打包后
#     与状态混合）+ 24 基混合调度（每字节 3 位 x3 + 1 trit = 0..23 数字参与轮调度）。
#   tsha1r-128：轻量 SPN（Ascon 型：nibble S 盒 + 旋-异或线性扩散）+ trit 扰动 +
#     状态压缩（256 位内态压缩到 128 位输出）。
# trit 表示（层内标准）：位平面（bit-sliced）——每个 u64 存 32 trit，高 32 位为
#   幅值位平面、低 32 位为符号位平面；运算全走 &/^/|/<<。tie 以两个 32 位 i64
#   半字 (M=幅值, N=符号) 表示，等价于 (M<<32)|N。
# 常量定制（可复现）：标准种子 + PRNG 扩展。扩展=SHA-256(SEED || u64be(k)) 计数器
#   流（k=0,1,2,...），依序取字节填充 IV/官/sbox/rcon。有意区别于 BLAKE2 IV。
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

# 消息字节 -> (24 基数字 digit, trit 值 tv -1/0/1)。
# bits3=低3位；tf=高2位；tv=to_trit(tf-1) 饱和；digit = bits3*3 + (tv+1) in 0..23。
def byte_trit(b):
    bits3 = b & 7
    tf = (b >> 6) & 3
    t = tf - 1
    tv = -1 if t < 0 else (0 if t == 0 else 1)
    return bits3, tv

# 把 count 个 trit 分组按位平面打包：返回每个 32-trit 组的 (M幅值,N符号) 两个 32 位字。
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

# ---- std::tsha1f-256 ----
SEED_F = b"TSHA1-2026-f-256-v1"
def tsha1f_consts():
    st = byte_stream(SEED_F)
    iv = gen_words(st, 8)
    sig = []
    for _ in range(10):
        sig += gen_perm_16(st)
    return iv, sig

def g_f(v, a, b, c, d, x, y):
    v[a] = (v[a] + v[b] + x) & M32
    v[d] = rotr(v[d] ^ v[a], 16)
    v[c] = (v[c] + v[d]) & M32
    v[b] = rotr(v[b] ^ v[c], 12)
    v[a] = (v[a] + v[b] + y) & M32
    v[d] = rotr(v[d] ^ v[a], 8)
    v[c] = (v[c] + v[d]) & M32
    v[b] = rotr(v[b] ^ v[c], 7)

def tsha1f_compress(h, blk, t_lo, t_hi, last, iv, sig):
    m = []
    for k in range(16):
        v = 0
        for j in range(4):
            v |= blk[k * 4 + j] << (8 * j)
        m.append(v & M32)
    tvs = [byte_trit(blk[j])[1] for j in range(64)]
    M, N = planes(tvs, 64)
    M0, M1 = M[0], M[1]
    N0, N1 = N[0], N[1]
    skey = 0
    for j in range(64):
        bits3, tv = byte_trit(blk[j])
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    v = h[:] + iv[:]
    v[12] ^= t_lo
    v[13] ^= t_hi
    if last:
        v[14] ^= M32
    for r in range(12):
        sr = r if r < 10 else r - 10
        base = sr * 16
        rd = (skey + r * 7) & 15
        sx = [ (sig[base + j] + rd) & 15 for j in range(16) ]
        g_f(v, 0, 4, 8, 12, m[sx[0]], m[sx[1]])
        g_f(v, 1, 5, 9, 13, m[sx[2]], m[sx[3]])
        g_f(v, 2, 6, 10, 14, m[sx[4]], m[sx[5]])
        g_f(v, 3, 7, 11, 15, m[sx[6]], m[sx[7]])
        g_f(v, 0, 5, 10, 15, m[sx[8]], m[sx[9]])
        g_f(v, 1, 6, 11, 12, m[sx[10]], m[sx[11]])
        g_f(v, 2, 7, 8, 13, m[sx[12]], m[sx[13]])
        g_f(v, 3, 4, 9, 14, m[sx[14]], m[sx[15]])
        # T 轨旁路扰动：幅值/符号两平面分别旋转后 XOR 进状态
        v[2] ^= rotl(M0, (r * 3) & 31)
        v[6] ^= rotl(N0, (r * 5) & 31)
        v[10] ^= rotl(M1, (r * 7) & 31)
        v[14] ^= rotl(N1, (r * 11) & 31)
    for i in range(8):
        h[i] ^= v[i] ^ v[i + 8]

def carry32(a, b):
    return (a + b) >> 32

def tsha1f(msg, iv, sig):
    h = iv[:]
    h[0] ^= 0x01010000 ^ 32
    n = len(msg)
    t_lo = t_hi = 0
    pos = 0
    while pos + 64 < n:
        t_hi = (t_hi + carry32(t_lo, 64)) & M32
        t_lo = (t_lo + 64) & M32
        tsha1f_compress(h, list(msg[pos:pos + 64]), t_lo, t_hi, False, iv, sig)
        pos += 64
    rem = n - pos
    t_hi = (t_hi + carry32(t_lo, rem)) & M32
    t_lo = (t_lo + rem) & M32
    pad = list(msg[pos:]) + [0] * (64 - rem)
    tsha1f_compress(h, pad[:64], t_lo, t_hi, True, iv, sig)
    return ''.join('%08x' % w for w in h)

# ---- std::tsha1r-128 ----
SEED_R = b"TSHA1-2026-r-128-v1"
def tsha1r_consts():
    st = byte_stream(SEED_R)
    iv = gen_words(st, 8)
    sbox = gen_perm_16(st)
    rcon = []
    for _ in range(16):
        rcon.append(gen_words(st, 1)[0])
    return iv, sbox, rcon

def tsha1r_perm(s, r, M, N, sbox, rcon):
    for w in range(8):
        x = s[w]; nx = 0
        for nb in range(8):
            nx |= (sbox[(x >> (4 * nb)) & 0xF] << (4 * nb))
        s[w] = nx & M32
    s[0] ^= rotr(s[0], 7) ^ rotr(s[1], 19)
    s[1] ^= rotr(s[1], 11) ^ rotr(s[2], 23)
    s[2] ^= rotr(s[2], 13) ^ rotr(s[3], 29)
    s[3] ^= rotr(s[3], 17) ^ rotr(s[1], 31)
    s[4] ^= rotr(s[4], 5) ^ rotr(s[5], 21)
    s[5] ^= rotr(s[5], 3) ^ rotr(s[6], 27)
    s[6] ^= rotr(s[6], 9) ^ rotr(s[7], 15)
    s[7] ^= rotr(s[7], 25) ^ rotr(s[5], 7)
    s[0] ^= s[4]; s[1] ^= s[5]; s[2] ^= s[6]; s[3] ^= s[7]
    s[4] ^= s[0]; s[5] ^= s[1]; s[6] ^= s[2]; s[7] ^= s[3]
    s[0] ^= (rcon[r & 15] + r) & M32
    s[2] ^= M                      # trit 幅值平面
    if N:
        s[3] ^= N                  # trit 符号平面
def tsha1r(msg, iv, sbox, rcon):
    s = iv[:]
    n = len(msg); pos = 0
    while pos + 16 <= n:
        blk = list(msg[pos:pos + 16])
        x = [0, 0, 0, 0]
        for k in range(4):
            for j in range(4):
                x[k] |= blk[k * 4 + j] << (8 * j)
        for k in range(4):
            s[k] ^= x[k] & M32
        tvs = [byte_trit(blk[j])[1] for j in range(16)]
        Mm, Nm = planes(tvs, 16)
        M, N = Mm[0], Nm[0]
        for r in range(6):
            tsha1r_perm(s, r, M, N, sbox, rcon)
        pos += 16
    rem = n - pos
    blk = list(msg[pos:]) + [0] * (16 - rem)
    x = [0, 0, 0, 0]
    for k in range(4):
        for j in range(4):
            x[k] |= blk[k * 4 + j] << (8 * j)
    for k in range(4):
        s[k] ^= x[k] & M32
    s[7] ^= (n & M32)
    # 末块 trit 位平面（零填充后计算）→ 终筛轮带上扰动，短消息亦激活 trit 层
    tvs = [byte_trit(blk[j])[1] for j in range(16)]
    Mp, Np = planes(tvs, 16)
    for r in range(8):
        tsha1r_perm(s, r, Mp[0], Np[0], sbox, rcon)
    out = [s[i] ^ s[i + 4] for i in range(4)]
    return ''.join('%08x' % w for w in out)

def reps(c, n):
    return bytes([c]) * n

def main():
    iv_f, sig_f = tsha1f_consts()
    print("IV_F = " + "".join('%08x' % w for w in iv_f))
    print("SIG_F = " + "".join('%x' % s for s in sig_f))
    iv_r, sbox_r, rcon_r = tsha1r_consts()
    print("IV_R = " + "".join('%08x' % w for w in iv_r))
    print("SBOX_R = " + "".join('%x' % s for s in sbox_r))
    print("RCON_R = " + "".join('%08x' % w for w in rcon_r))
    for name, ln in [("empty",0),("abc",3),("a1000",1000),("b55",55),("b56",56),
                     ("b63",63),("b64",64),("b65",65),("b127",127),("b128",128),
                     ("b129",129),("b256",256)]:
        msg = b'' if ln==0 else (b'abc' if ln==3 else reps(ord('a'), ln))
        print("F %-5s %s" % (name, tsha1f(msg, iv_f, sig_f)))
    for name, ln in [("empty",0),("abc",3),("a1000",1000),("b15",15),("b16",16),
                     ("b17",17),("b31",31),("b32",32),("b33",33),("b128",128),("b256",256)]:
        msg = b'' if ln==0 else (b'abc' if ln==3 else reps(ord('a'), ln))
        print("R %-5s %s" % (name, tsha1r(msg, iv_r, sbox_r, rcon_r)))

if __name__ == "__main__":
    main()



