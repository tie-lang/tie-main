# -*- coding: utf-8 -*-
# ============================================================================
# gen_tsha1_core.py —— TSHA1 v2「状态随输出位长」唯一真源（canonical core）
# ----------------------------------------------------------------------------
# 本模块是 state-per-n 重构的**唯一规格实现**：参考生成器（gen_tsha1fr/
# gen_tsha1bx/gen_tsha1x）与 std/tsha1.tie 的实现必须与本文件**逐式一致**
# （同一公式、同一掩码、同一编码、同一初始化顺序）。
# 设计依据：
#   docs/superpowers/specs/2026-08-30-tsha1-state-per-n-design.md（结构）
#   docs/superpowers/specs/2026-08-30-tsha1-security-design.md     （档位）
#
# v2 核心概念：
#   - 位长 n（48 进制符号数）决定内部状态字宽 W：
#       f/b/x：每字 32 trit（(M,N) 各 32 位）→ W = max(1, ⌈n·L48/32⌉)
#       r    ：每字 16 trit（(M,N) 各 16 位）→ W = max(1, ⌈n·L48/(16·log2 3)⌉)
#   - 轨分配退化表：W≥16 原轨数（f/r 双、b 三、x 四）；8≤W<16 双轨；
#     4≤W<8 单轨环式；1≤W<4 直接置换（同样单轨环式）。
#   - 通用原语 ring_mix：任意长度 L 的环式扩散（tadd2 + 乘积 + majority +
#     消息注入 + 轮常量），值语义对任意 W 机械确定。
#   - 输出管线：状态全宽 → 池 hex → 按 base 编码 → 截断 n 符号；无 XOF，不足拒绝。
#
# 表示：字 k = (lanes[2k]=M, lanes[2k+1]=N)，各 32 位掩码；r 的 M/N 低 16 位有效，
#   旋转一律 rrp16（16 位循环），其余模型 rrp（32 位循环）。
# 常量：SEED + SHA-256(SEED ‖ u64be(k)) 计数器流；IV 按 W 取前 W 字，RCON 16 字。
# ============================================================================
import math
import hashlib

M32 = 0xFFFFFFFF
L48 = 5.584962500721156             # log2(48)
TRIT16 = 16.0 * math.log2(3.0)      # 25.359… r 每字信息量

SEED_MODEL = {
    'f': b"TSHA1-2026-f-256-v1",
    'r': b"TSHA1-2026-r-128-v1",
    'b': b"TSHA1-2026-b-256-v1",
    'x': b"TSHA1-2026-x-256-v1",
}
SEED_BSCON = b"TSHA1-2026-b-sponge-v1"
SEED_XDCON = b"TSHA1-2026-x-lfsr-v1"

# ----------------------------------------------------------------------------
# 常量（可复现）
# ----------------------------------------------------------------------------
def _word(stream):
    v = 0
    for _ in range(4):
        v = ((v << 8) | next(stream)) & M32
    return v

def _stream(seed):
    k = 0
    while True:
        for b in hashlib.sha256(seed + k.to_bytes(8, 'big')).digest():
            yield b
        k += 1

def gen_iv_rcon(model):
    st = _stream(SEED_MODEL[model])
    iv = [_word(st) for _ in range(32)]     # IV 预取 32 字（W 最大 32）
    rcon = [_word(st) for _ in range(16)]
    return iv, rcon

def gen_bcon():
    return [_word(_stream(SEED_BSCON)) for _ in range(16)]

def gen_xdcon():
    return [_word(_stream(SEED_XDCON)) for _ in range(16)]

# ----------------------------------------------------------------------------
# 位平面原语（与 v1 一致）
# ----------------------------------------------------------------------------
def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & M32

def rrp(x, r):
    return rotr(x, r & 31)

def rrp16(x, r):
    return rotr(x & 0xFFFF, r & 15)

def tadd2(Ma, Na, Mb, Nb):
    aP = Ma & (~Na); aN = Ma & Na
    bP = Mb & (~Nb); bN = Mb & Nb
    o_pos = ((~Ma & Mb & ~Nb) | (Ma & ~Na & ~Mb) | (aN & bN)) & M32
    o_neg = ((~Ma & Mb & Nb) | (Ma & Na & ~Mb) | (aP & bP)) & M32
    return (o_pos | o_neg) & M32, o_neg & M32

def tmul2(Ma, Na, Mb, Nb):
    amp = (Ma & Mb) & M32
    no = ((Na ^ Nb) & amp) & M32
    return amp, no

def quant3(m0, n0, m1, n1, m2, n2):
    A = m0 & (~n0); B = m1 & (~n1); C = m2 & (~n2)
    return ((A & B) | (B & C) | (C & A)) & M32

# ----------------------------------------------------------------------------
# 字宽与轨分配
# ----------------------------------------------------------------------------
def words_for(n, model):
    if model == 'r':
        return max(1, int(math.ceil(n * L48 / TRIT16)))
    return max(1, int(math.ceil(n * L48 / 32.0)))

def is_bits48(n):
    return n in (2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 69, 88, 92, 96, 128, 144)

def is_base_ok(base):
    return base in (2, 3, 8, 16, 48)

def alloc_tracks(model, W):
    """返回轨道表；每项：(字索引列表, 类型[, rate])；类型 dual/sponge/ring/lfsr"""
    if W >= 16:
        if model in ('f', 'r'):
            LA = (W + 1) // 2
            return [(list(range(LA)), 'dual'), (list(range(LA, W)), 'dual')]
        if model == 'b':
            LA = (W + 2) // 3
            LB = (W + 2) // 3
            LC = W - LA - LB
            while LC < 1:
                LA -= 1
                LC = W - LA - LB
            rate = (LC + 1) // 2
            cap = LC - rate
            return [(list(range(LA)), 'dual'),
                    (list(range(LA, LA + LB)), 'dual'),
                    (list(range(LA + LB, W)), 'sponge', rate)]
        # x 四轨：A=B=C=⌈2W/7⌉，D = 剩余 LFSR
        a = (2 * W + 6) // 7
        while 3 * a >= W:
            a -= 1
        if a < 1:
            a = 1
        d = W - 3 * a
        while d < 1:
            a -= 1
            d = W - 3 * a
        aS, aE = 0, a
        bS, bE = a, 2 * a
        return [(list(range(aS, aE)), 'dual'),
                (list(range(bS, bE)), 'dual'),
                (list(range(bE, bE + a)), 'sponge', (a + 1) // 2),
                (list(range(3 * a, W)), 'lfsr')]
    if W >= 8:
        LA = (W + 1) // 2
        return [(list(range(LA)), 'dual'), (list(range(LA, W)), 'dual')]
    return [(list(range(W)), 'ring')]

# ----------------------------------------------------------------------------
# 消息预处理：单遍 trit 化（planes + skey 一次扫描）
# ----------------------------------------------------------------------------
def block_planes_skey(blk):
    tvs = [0] * 64
    M = [0, 0]
    N = [0, 0]
    skey = 0
    for j in range(64):
        b = blk[j]
        bits3 = b & 7
        tf = (b >> 6) & 3
        t = tf - 1
        tv = -1 if t < 0 else (0 if t == 0 else 1)
        tvs[j] = tv
        dig = bits3 * 3 + (tv + 1)
        skey = (skey * 24 + dig) & M32
    for p in range(64):
        tv = tvs[p]
        if tv == 0:
            continue
        w = p // 32
        bit = p % 32
        M[w] |= (1 << bit)
        if tv < 0:
            N[w] |= (1 << bit)
    return M, N, skey, tvs

# ----------------------------------------------------------------------------
# 通用环式扩散（值语义的唯一定义）
# ----------------------------------------------------------------------------
def _rot_lane(x, r, half):
    return rrp16(x, r) if half else rrp(x, r)

def ring_mix(lanes, idx, r, skey, rcon, half, inject, rcon_idx):
    """对 idx（L 个字）做一轮环式扩散。lanes 长度 2·W（在轨上原位修改）。
    固定顺序：
      1) S[k]  = tadd2(W_k, rrp(W_{k+2}, a_k), …… ) —— a_k=(rA+5k)&31, b_k=(rB+7k+3)&31
      2) 写回 W_k = S[k]；乘积 tmul2(S_k, S_{k+2}) 异或入 W_{k+1}（M、N）
      3) quant3(S_0..S_2) 注入 W_{L-1}（M 与旋转后的 N）
      4) 消息平面注入（inject 非空时）：轨首字 + 次字
      5) 轮常量 rcon[rcon_idx] 错位注入
    """
    L = len(idx)
    if L == 0:
        return
    rA = (r * 3 + (skey & 7)) & 31
    rB = (r * 7 + ((skey >> 3) & 7)) & 31
    S = [None] * L
    for k in range(L):
        i = idx[k]
        j2 = idx[(k + 2) % L]
        j3 = idx[(k + 3) % L]
        a = (rA + 5 * k) & 31
        b = (rB + 7 * k + 3) & 31
        S[k] = tadd2(lanes[2 * i], lanes[2 * i + 1],
                     _rot_lane(lanes[2 * j2], a, half), _rot_lane(lanes[2 * j2 + 1], a, half))
        # 第三操作数（j3）以「旋转+平衡加再并入」方式参与，与原语同构可复现
        (sm, sn2) = tadd2(S[k][0], S[k][1],
                          _rot_lane(lanes[2 * j3], b, half), _rot_lane(lanes[2 * j3 + 1], b, half))
        S[k] = (sm, sn2)
    for k in range(L):
        i = idx[k]
        lanes[2 * i] = S[k][0] & M32
        lanes[2 * i + 1] = S[k][1] & M32
    for k in range(L):
        p = tmul2(S[k][0], S[k][1], S[(k + 2) % L][0], S[(k + 2) % L][1])
        i1 = idx[(k + 1) % L]
        lanes[2 * i1] = (lanes[2 * i1] ^ p[0]) & M32
        lanes[2 * i1 + 1] = (lanes[2 * i1 + 1] ^ p[1]) & M32
    if L >= 3:
        maj = quant3(S[0][0], S[0][1], S[1][0], S[1][1], S[2][0], S[2][1])
    elif L == 2:
        maj = quant3(S[0][0], S[0][1], S[1][0], S[1][1], S[0][0], S[0][1])
    else:
        maj = quant3(S[0][0], S[0][1], S[0][0], S[0][1], S[0][0], S[0][1])
    il = idx[L - 1]
    lanes[2 * il] = (lanes[2 * il] ^ maj) & M32
    lanes[2 * il + 1] = (lanes[2 * il + 1] ^ _rot_lane(maj, (rB + 7) & 31, half)) & M32
    if inject is not None:
        (M0, N0, M1, N1), mA, mB = inject
        i0 = idx[0]
        s = tadd2(lanes[2 * i0], lanes[2 * i0 + 1],
                  _rot_lane(M0, mA, half), _rot_lane(N0, mA, half))
        lanes[2 * i0] = s[0] & M32
        lanes[2 * i0 + 1] = s[1] & M32
        if L >= 2:
            i1 = idx[1]
            s = tadd2(lanes[2 * i1], lanes[2 * i1 + 1],
                      _rot_lane(M1, (mA + 7) & 31, half), _rot_lane(N1, (mA + 7) & 31, half))
            lanes[2 * i1] = s[0] & M32
            lanes[2 * i1 + 1] = s[1] & M32
    i0 = idx[0]
    lanes[2 * i0] = (lanes[2 * i0] ^ rcon[rcon_idx & 15]) & M32
    il = idx[L - 1]
    lanes[2 * il + 1] = (lanes[2 * il + 1] ^
                         _rot_lane(rcon[(rcon_idx + 1) & 15], (r * 5) & 31, half)) & M32

def _couple(lanes, a, b, half):
    s = tadd2(lanes[2 * a], lanes[2 * a + 1], lanes[2 * b], lanes[2 * b + 1])
    lanes[2 * a] = s[0] & M32
    lanes[2 * a + 1] = s[1] & M32
    p = tmul2(lanes[2 * a], lanes[2 * a + 1], lanes[2 * b], lanes[2 * b + 1])
    lanes[2 * b] = (lanes[2 * b] ^ p[0]) & M32
    lanes[2 * b + 1] = (lanes[2 * b + 1] ^ p[1]) & M32

def lfsr_mix(lanes, td, r, skey, M0, N0, rcon, half):
    L = len(td)
    if L == 0:
        return
    for k in range(L):
        i = td[k]
        j = td[(k + 1) % L]
        s0 = (r * 3 + 5 * k) & 31
        s1 = (r * 5 + 3 * k) & 31
        lanes[2 * i] = (lanes[2 * i] ^ _rot_lane(M0, s0, half)) & M32
        lanes[2 * i + 1] = (lanes[2 * i + 1] ^ _rot_lane(N0, s1, half)) & M32
        fb = (lanes[2 * i] >> 16) ^ lanes[2 * i + 1]
        lanes[2 * j] = (lanes[2 * j] ^ fb) & M32
        lanes[2 * j + 1] = (lanes[2 * j + 1] ^ fb) & M32
        lanes[2 * j] = (lanes[2 * j] ^ rcon[(r + k) & 15]) & M32
        lanes[2 * j + 1] = (lanes[2 * j + 1] ^
                            _rot_lane(rcon[(r + k + 8) & 15], (r + 2 * k) & 31, half)) & M32

def fin_synth(h, half):
    """S=4 轮全 W 字单环收束（rcon=0 表），随后投影。"""
    W = len(h)
    if W == 1:
        return
    lanes = [0] * (2 * W)
    for i in range(W):
        lanes[2 * i] = h[i] & M32
        lanes[2 * i + 1] = _rot_lane(h[(i + 1) % W], 7, half)
    zero = [0] * 16
    for r in range(4):
        ring_mix(lanes, list(range(W)), r, 0x13579BDF, zero, half, None, r)
    for i in range(W):
        h[i] = (lanes[2 * i] ^ _rot_lane(lanes[2 * i + 1], (i * 5) & 31, half)) & M32

# ----------------------------------------------------------------------------
# 单块压缩（f/r 双轨；b 三轨+海绵；x 四轨+LFSR；W<16 退化）
# ----------------------------------------------------------------------------
def compress(model, h, blk, t_lo, t_hi, last, iv, rcon, bcon, xdcon, half):
    W = len(h)
    Mp, Np, skey, _ = block_planes_skey(blk)
    M0, N0, M1, N1 = Mp[0], Np[0], Mp[1], Np[1]
    lanes = [0] * (2 * W)
    mplan = (0xFFFF if half else M32)
    for i in range(W):
        lanes[2 * i] = h[i] & M32
        lanes[2 * i + 1] = _rot_lane(h[(i + W // 2) % W], 7, half)
    for i in range(W):
        lanes[2 * i] = (lanes[2 * i] ^ (iv[i % 8] & mplan)) & M32
        lanes[2 * i + 1] = (lanes[2 * i + 1] ^ (iv[(i + 4) % 8] & mplan)) & M32
    lanes[1] = (lanes[1] ^ (t_lo & mplan)) & M32
    hi = 2 * (W // 2) + 1
    lanes[hi] = (lanes[hi] ^ (t_hi & mplan)) & M32
    if last:
        lk = 2 * ((W // 2) % W) + 1
        lanes[lk] = (lanes[lk] ^ M32) & M32

    tracks = alloc_tracks(model, W)
    R = {'f': 12, 'r': 8, 'b': 14, 'x': 16}[model]
    for r in range(R):
        mA = (r * 5 + ((skey >> 6) & 7)) & 31
        mB = (r * 11 + ((skey >> 9) & 7)) & 31
        mC = (r * 7 + ((skey >> 12) & 7)) & 31
        mD = (r * 13 + ((skey >> 15) & 7)) & 31
        inj0 = ((M0, N0, M1, N1), mA, mB)
        inj1 = ((M0, N0, M1, N1), mC, mD)
        dual_seen = 0
        for t in tracks:
            idx = t[0]
            kind = t[1]
            if kind == 'dual':
                inj = inj0 if dual_seen == 0 else inj1
                rc_idx = r if dual_seen == 0 else (r + 8) & 15
                ring_mix(lanes, idx, r, skey, rcon, half, inj, rc_idx)
                dual_seen += 1
            elif kind == 'ring':
                ring_mix(lanes, idx, r, skey, rcon, half, inj0, r)
            elif kind == 'sponge':
                rate = t[2]
                r_idx = idx[:rate]
                c_idx = idx[rate:]
                ring_mix(lanes, r_idx, r, skey, bcon, half, inj0, (r + 3) & 15)
                if c_idx:
                    ring_mix(lanes, c_idx, r, skey, bcon, half, None, (r + 11) & 15)
            else:  # lfsr
                lfsr_mix(lanes, idx, r, skey, M0, N0, xdcon, half)
        # 轨间耦合（仅 b 三轨 / x 四轨 的 W≥16 形态）
        if model == 'b' and len(tracks) == 3:
            ta = tracks[0][0]; tb = tracks[1][0]; tc = tracks[2][0]
            rate = tracks[2][2]
            cap0 = tc[rate]
            cap1 = tc[rate + 1] if len(tc) > rate + 1 else tc[rate]
            a1 = ta[1] if len(ta) > 1 else ta[0]
            b1 = tb[1] if len(tb) > 1 else tb[0]
            _couple(lanes, ta[0], tc[0], half)
            _couple(lanes, tb[0], tc[1] if len(tc) > 1 else tc[0], half)
            _couple(lanes, a1, cap0, half)
            _couple(lanes, b1, cap1, half)
        if model == 'x' and len(tracks) == 4:
            ta = tracks[0][0]; tb = tracks[1][0]; tc = tracks[2][0]; td = tracks[3][0]
            rate = tracks[2][2]
            cap0 = tc[rate]
            cap1 = tc[rate + 1] if len(tc) > rate + 1 else tc[rate]
            a1 = ta[1] if len(ta) > 1 else ta[0]
            b1 = tb[1] if len(tb) > 1 else tb[0]
            _couple(lanes, ta[0], tc[0], half)
            _couple(lanes, tb[0], tc[1] if len(tc) > 1 else tc[0], half)
            _couple(lanes, a1, cap0, half)
            _couple(lanes, b1, cap1, half)
            for k in range(len(td)):
                _couple(lanes, ta[k % len(ta)], td[k], half)

    for i in range(W):
        h[i] = (h[i] ^ lanes[2 * i] ^ _rot_lane(lanes[2 * i + 1], (i * 3) & 31, half)) & M32
    fin_synth(h, half)
    return h

# ----------------------------------------------------------------------------
# 摘要驱动 + 输出编码（无 XOF；状态全宽 → 池 hex；不足拒绝）
# ----------------------------------------------------------------------------
def digest(model, msg, n):
    """msg 为 bytes；返回该 (model,msg,n) 的**状态全宽 hex**（8W 个 hex 字符）。"""
    if not is_bits48(n):
        return ''
    W = words_for(n, model)
    iv, rcon = gen_iv_rcon(model)
    half = (model == 'r')
    mplan = (0xFFFF if half else M32)
    h = [(iv[i] & mplan) for i in range(W)]
    h[0] = (h[0] ^ 0x01010000 ^ 32) & M32
    bcon = gen_bcon() if model in ('b', 'x') else None
    xdcon = gen_xdcon() if model == 'x' else None
    t_lo = 0
    t_hi = 0
    nbytes = len(msg)
    pos = 0
    while pos + 64 < nbytes:
        blk = msg[pos:pos + 64]
        t_hi = (t_hi + ((t_lo + 64) >> 32)) & M32
        t_lo = (t_lo + 64) & M32
        compress(model, h, blk, t_lo, t_hi, False, iv, rcon, bcon, xdcon, half)
        pos += 64
    rem = nbytes - pos
    blk = (msg[pos:pos + 64]).ljust(64, b'\x00')
    t_hi = (t_hi + ((t_lo + rem) >> 32)) & M32
    t_lo = (t_lo + rem) & M32
    compress(model, h, blk, t_lo, t_hi, True, iv, rcon, bcon, xdcon, half)
    return ''.join('%08x' % (h[i] & M32) for i in range(W))

def pool_from_digest(hexstr):
    """状态全宽 hex → 十六进制池（即 hexstr 自身；每字 16 hex 字符）。"""
    return hexstr

def encode(model, msg, n, base=48):
    """对外：输出 n 个符号（48 进制口径）。base48 → 截断池；其他进制先取 b0 字节再重编码。"""
    if not is_bits48(n):
        return ''
    if not is_base_ok(base):
        return ''
    hexstr = digest(model, msg, n)
    if base == 48:
        return b48_encode(hexstr)[:n]
    b0 = (n * 698121) // 1000000          # ⌊n·L48/8⌋ 字节
    pool = hexstr
    if len(pool) // 2 < b0:               # 状态不足 → 拒绝（无 XOF）
        return ''
    bb48 = pool[:2 * b0]
    if base == 16:
        return bb48
    m = base_chars(b0, base)
    return pad_radix(bb48, base, m)

B48_ALPH = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def b48_encode(hexstr):
    """hex 串 → base48（大数除法，取整字符集）。"""
    if not hexstr:
        return ''
    num = int(hexstr, 16)
    if num == 0:
        return '0'
    out = []
    while num > 0:
        num, r = divmod(num, 48)
        out.append(B48_ALPH[r])
    return ''.join(reversed(out))

def base_chars(byte_count, base):
    return (int(math.ceil(byte_count * 8.0 / math.log2(base))))

def pad_radix(hexstr, base, m):
    num = int(hexstr, 16)
    if num == 0:
        return '0' * m
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'[:base]
    out = []
    while num > 0:
        num, r = divmod(num, base)
        out.append(chars[r])
    s = ''.join(reversed(out))
    while len(s) < m:
        s = '0' + s
    return s

# ----------------------------------------------------------------------------
# 自检入口：python gen_tsha1_core.py
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    for model in ('f', 'r', 'b', 'x'):
        for n in (2, 8, 48, 69, 92, 96):
            d = digest(model, b'abc', n)
            body = encode(model, b'abc', n)
            print('%-1s n=%-3d W=%-2d hexlen=%d b48=%s' %
                  (model, n, words_for(n, model), len(d), body[:16]))
        print()