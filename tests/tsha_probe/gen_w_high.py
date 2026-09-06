# -*- coding: utf-8 -*-
# gen_w_high.py：生成 TSHA1 v2 的 W>=16 多轨特化内核（table 动态索引 → struct 字段承载 lanes，
# 让 LLVM 全 SSA → 自动向量化）。语义逐式镜像 std/tsha1.tie 通用 compress 的 W>=16 分支：
#   · model 0 (f)  双轨 dual        R=12
#   · model 1 (r)  双轨 dual 半宽    R=8
#   · model 2 (b)  三轨 dual+sponge  R=14
#   · model 3 (x)  四轨 dual+sponge+lfsr  R=16
# 生成产物按 model 命名（compress_w{W}[f|h|b|x]）插入 std/tsha1_w48.tie，并分派。
# 用法：python gen_w_high.py f16 f17 f23 f26 r20:r r21:r r22:r r29:r r32:r b16 x16 ...
#   简写：fW（全宽双轨）、rW（半宽双轨）、bW（三轨）、xW（四轨）。
import sys

# ---------- 公用小件 ----------

def rotc(base, off):
    o = off % 32
    if o == 0:
        return base
    return "(%s + %d) & 31" % (base, o)

def maj_line(L):
    if L >= 3:
        return "var maj = quant3(s0m, s0n, s1m, s1n, s2m, s2n)"
    if L == 2:
        return "var maj = quant3(s0m, s0n, s1m, s1n, s0m, s0n)"
    return "var maj = quant3(s0m, s0n, s0m, s0n, s0m, s0n)"

def ring(rot, fields, L, struct, name, inj=True, rcon=True):
    # 单环 ring_mix 展开（fields 为该区间相对 0..L-1 的 (M,N) 字段名）。
    M = [f[0] for f in fields]
    N = [f[1] for f in fields]
    out = []
    out.append("func %s(l: %s, r: i64" % (name, struct))
    out.append("            , skey: i64")
    if inj:
        out.append("            , M0: i64, N0: i64, M1: i64, N1: i64, mA: i64")
    if rcon:
        out.append("            , rcon: table<i64>, rcon_idx: i64")
    out.append("            ) -> %s {" % struct)
    out.append("    var rA = (r * 3 + (skey & 7)) & 31")
    out.append("    var rB = (r * 7 + ((skey >> 3) & 7)) & 31")
    # S build
    for k in range(L):
        j2 = (k + 2) % L
        j3 = (k + 3) % L
        a = rotc("rA", 5 * k)
        b = rotc("rB", 7 * k + 3)
        out.append("    var (q%dm, q%dn) = tadd2(l.%s, l.%s," % (k, k, M[k], N[k]))
        out.append("                    %s(l.%s, %s), %s(l.%s, %s))" % (rot, M[j2], a, rot, N[j2], a))
        out.append("    var (s%dm, s%dn) = tadd2(q%dm, q%dn," % (k, k, k, k))
        out.append("                    %s(l.%s, %s), %s(l.%s, %s))" % (rot, M[j3], b, rot, N[j3], b))
    # write back
    for k in range(L):
        out.append("    l.%s = s%dm" % (M[k], k))
        out.append("    l.%s = s%dn" % (N[k], k))
    # tmul2 -> lanes[(k+1)%L]
    for k in range(L):
        k1 = (k + 1) % L
        k2 = (k + 2) % L
        out.append("    var (p%dm, p%dn) = tmul2(s%dm, s%dn, s%dm, s%dn)" % (k, k, k, k, k2, k2))
        out.append("    l.%s = (l.%s ^ p%dm) & 0xFFFFFFFF" % (M[k1], M[k1], k))
        out.append("    l.%s = (l.%s ^ p%dn) & 0xFFFFFFFF" % (N[k1], N[k1], k))
    # maj
    last = L - 1
    out.append("    " + maj_line(L))
    out.append("    l.%s = (l.%s ^ maj) & 0xFFFFFFFF" % (M[last], M[last]))
    out.append("    l.%s = (l.%s ^ %s(maj, (rB + 7) & 31)) & 0xFFFFFFFF" % (N[last], N[last], rot))
    if inj:
        out.append("    var (im, in2) = tadd2(l.%s, l.%s, %s(M0, %s), %s(N0, %s))" % (M[0], N[0], rot, rotc("mA", 0), rot, rotc("mA", 0)))
        out.append("    l.%s = im" % M[0])
        out.append("    l.%s = in2" % N[0])
        out.append("    var (jm, jn2) = tadd2(l.%s, l.%s, %s(M1, %s), %s(N1, %s))" % (M[1], N[1], rot, rotc("mA", 7), rot, rotc("mA", 7)))
        out.append("    l.%s = jm" % M[1])
        out.append("    l.%s = jn2" % N[1])
    if rcon:
        out.append("    l.%s = (l.%s ^ rcon[rcon_idx & 15]) & 0xFFFFFFFF" % (M[0], M[0]))
        out.append("    l.%s = (l.%s ^ %s(rcon[(rcon_idx + 1) & 15], (r * 5) & 31)) & 0xFFFFFFFF" % (N[last], N[last], rot))
    out.append("    return l")
    out.append("}")
    return out

def lfsr(rot, fields, L, struct, name):
    M = [f[0] for f in fields]
    N = [f[1] for f in fields]
    out = []
    out.append("func %s(l: %s, r: i64" % (name, struct))
    out.append("            , M0: i64, N0: i64, rcon: table<i64>")
    out.append("            ) -> %s {" % struct)
    out.append("    var fb: i64 = 0")
    for k in range(L):
        I = k
        J = (k + 1) % L
        out.append("    l.%s = (l.%s ^ %s(M0, (r * 3 + %d) & 31)) & 0xFFFFFFFF" % (M[I], M[I], rot, 5 * k))
        out.append("    l.%s = (l.%s ^ %s(N0, (r * 5 + %d) & 31)) & 0xFFFFFFFF" % (N[I], N[I], rot, 3 * k))
        out.append("    fb = (l.%s >> 16) ^ l.%s" % (M[I], N[I]))
        out.append("    l.%s = (l.%s ^ fb) & 0xFFFFFFFF" % (M[J], M[J]))
        out.append("    l.%s = (l.%s ^ fb) & 0xFFFFFFFF" % (N[J], N[J]))
        out.append("    l.%s = (l.%s ^ rcon[(r + %d) & 15]) & 0xFFFFFFFF" % (M[J], M[J], k))
        out.append("    l.%s = (l.%s ^ %s(rcon[(r + %d + 8) & 15], (r + %d) & 31)) & 0xFFFFFFFF" % (N[J], N[J], rot, k, 2 * k))
    out.append("    return l")
    out.append("}")
    return out

def couple_lines(a, b):
    return (
        "    var (sm, sn) = tadd2(l.M%d, l.N%d, l.M%d, l.N%d)" % (a, a, b, b)
        + "\n    l.M%d = sm" % a
        + "\n    l.N%d = sn" % a
        + "\n    var (pm, pn) = tmul2(l.M%d, l.N%d, l.M%d, l.N%d)" % (a, a, b, b)
        + "\n    l.M%d = (l.M%d ^ pm) & 0xFFFFFFFF" % (b, b)
        + "\n    l.N%d = (l.N%d ^ pn) & 0xFFFFFFFF" % (b, b)
    )

def absorb(W, rot, struct, suf=""):
    out = []
    out.append("func absorb%d%s(l: %s, Pw: Planes16, skey: i64) -> %s {" % (W, suf, struct, struct))
    out.append("    var w: i64 = 0")
    out.append("    while w < 16 {")
    out.append("        var pv: i64 = 0")
    for i in range(16):
        if i == 0:
            out.append("        if w == 0 {")
        elif i == 15:
            out.append("        } else {")
        else:
            out.append("        } else if w == %d {" % i)
        out.append("            pv = Pw.w%d" % i)
    out.append("        }")
    out.append("        if pv != 0 {")
    out.append("            var a = (w * 5 + ((skey >> (w & 7)) & 7)) & 31")
    out.append("            var an = w %% %d" % W)
    out.append("            var v = %s(pv, a)" % rot)
    out.append("            var v2 = %s(pv, a + 17)" % rot)
    for i in range(W):
        if i == 0:
            out.append("            if an == 0 {")
        elif i == W - 1:
            out.append("            } else {")
        else:
            out.append("            } else if an == %d {" % i)
        out.append("                var (t%dm, t%dn) = tadd2(l.M%d, l.N%d, v, v2)" % (i, i, i, i))
        out.append("                l.M%d = t%dm & 0xFFFFFFFF" % (i, i))
        out.append("                l.N%d = t%dn & 0xFFFFFFFF" % (i, i))
    out.append("            }")
    out.append("        }")
    out.append("        w = w + 1")
    out.append("    }")
    out.append("    return l")
    out.append("}")
    return out

def fin_synth(W, rot, struct, mixF, suf=""):
    out = []
    out.append("func fin_synth%d%s(h: ref table<i64>) {" % (W, suf))
    out.append("    var l = %s()" % struct)
    for i in range(W):
        j = (i + 1) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rot, j))
    out.append("    var sf: i64 = 0")
    out.append("    while sf < 4 {")
    out.append("        l = %s(l, sf, 0x13579BDF)" % mixF)
    out.append("        sf = sf + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, rot, i, (i * 5) & 31))
    out.append("}")
    return out

def emit_struct(W, struct):
    out = ["struct %s {" % struct]
    for i in range(W):
        out.append("    var M%d: i64 = 0" % i)
        out.append("    var N%d: i64 = 0" % i)
    out.append("}")
    return out

def emit_common(out, W, struct, rot, msk, suf="", R=None):
    # 返回 (var 名) 前缀后缀处理：压缩函数体内共前奏/共尾。
    pass

def fields(W, a, b):
    return [("M%d" % i, "N%d" % i) for i in range(a, b)]

ALLF = [16, 17, 23, 26]     # f/b/x 全宽 W
ALLR = [20, 21, 22, 29, 32]  # r 半宽 W

def gen_f(W):
    half = False; rot = "rrp"; msk = "0xFFFFFFFF"; suf = ""
    hm = "Lanes%d" % W
    struct = hm
    LA = (W + 1) // 2
    out = []
    out.append("// === W=%d 全宽双轨特化内核（f，n=88/92/96/128/144）——轨A lanes[0..%d)、轨B lanes[%d..%d)；R=12 ===" % (W, LA, LA, W))
    out += emit_struct(W, struct)
    out.append("")
    out += ring(rot, fields(W, 0, LA), LA, struct, "ring%d_mixA" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, LA, W), W - LA, struct, "ring%d_mixB" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, 0, W), W, struct, "ring%d_mixF" % W, inj=False, rcon=False)
    out.append("")
    out += absorb(W, rot, struct, suf)
    out.append("")
    out += fin_synth(W, rot, struct, "ring%d_mixF" % W, suf)
    out.append("")
    out.append("pub func compress_w%d(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % W)
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, R: i64) {")
    out += compress_dual_tail(W, struct, rot, msk, suf, "ring%d_mixA" % W, "ring%d_mixB" % W, "absorb%d" % W, "fin_synth%d" % W)
    return out

def gen_r(W):
    rot = "rrp16"; msk = "0xFFFF"; suf = "h"
    struct = "Lanes%dh" % W
    LA = (W + 1) // 2
    out = []
    out.append("// === W=%d 半宽双轨特化内核（r，n=88/92/96/128/144；rrp16/0xFFFF 掩码）——轨A lanes[0..%d)、轨B lanes[%d..%d)；R=8 ===" % (W, LA, LA, W))
    out += emit_struct(W, struct)
    out.append("")
    out += ring(rot, fields(W, 0, LA), LA, struct, "ring%d%s_mixA" % (W, suf), inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, LA, W), W - LA, struct, "ring%d%s_mixB" % (W, suf), inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, 0, W), W, struct, "ring%d%s_mixF" % (W, suf), inj=False, rcon=False)
    out.append("")
    out += absorb(W, rot, struct, suf)
    out.append("")
    out += fin_synth(W, rot, struct, "ring%d%s_mixF" % (W, suf), suf)
    out.append("")
    out.append("pub func compress_w%d%s(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % (W, suf))
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, R: i64) {")
    out += compress_dual_tail(W, struct, rot, msk, suf, "ring%d%s_mixA" % (W, suf), "ring%d%s_mixB" % (W, suf), "absorb%d%s" % (W, suf), "fin_synth%d%s" % (W, suf))
    return out

def compress_dual_tail(W, struct, rot, msk, suf, mixA, mixB, absn, fins):
    half_w = W // 2
    out = []
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = %s()" % struct)
    for i in range(W):
        j = (i + half_w) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rot, j))
    for i in range(W):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, i % 8, msk))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8, msk))
    out.append("    l.N0 = (l.N0 ^ (t_lo & %s)) & 0xFFFFFFFF" % msk)
    out.append("    l.N%d = (l.N%d ^ (t_hi & %s)) & 0xFFFFFFFF" % (half_w, half_w, msk))
    out.append("    if last {")
    out.append("        l.N%d = (l.N%d ^ 0xFFFFFFFF) & 0xFFFFFFFF" % (half_w, half_w))
    out.append("    }")
    out.append("    l = %s(l, Pw, skey)" % absn)
    out.append("    var mA: i64 = 0")
    out.append("    var mC: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        mC = (r * 7 + ((skey >> 12) & 7)) & 31")
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mA, rcon, r)" % mixA)
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mC, rcon, (r + 8) & 15)" % mixB)
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, rot, i, (i * 3) & 31))
    out.append("    %s(h)" % fins)
    out.append("}")
    return out

def gen_b(W):
    # b 三轨：track0=[0,LA2) dual, track1=[LA2,LA2+LB2) dual, track2=[LA2+LB2,W) sponge(rate2)
    rot = "rrp"; msk = "0xFFFFFFFF"
    struct = "Lanes%db" % W
    LA2 = (W + 2) // 3; LB2 = (W + 2) // 3; LC2 = W - LA2 - LB2
    while LC2 < 1:
        LA2 -= 1; LC2 = W - LA2 - LB2
    rate2 = (LC2 + 1) // 2
    c_len = LC2 - rate2
    tc_s = LA2 + LB2
    out = []
    out.append("// === W=%d 三轨特化内核（b，n=88/92/96/128/144）——轨A[0..%d)、轨B[%d..%d)、海绵[%d..%d) rate2=%d；R=14 ===" % (W, LA2, LA2, tc_s, tc_s, W, rate2))
    out += emit_struct(W, struct)
    out.append("")
    out += ring(rot, fields(W, 0, LA2), LA2, struct, "ring%db_mixA" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, LA2, tc_s), LB2, struct, "ring%db_mixB" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, tc_s, tc_s + rate2), rate2, struct, "ring%db_sponge_r" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, tc_s + rate2, W), c_len, struct, "ring%db_sponge_c" % W, inj=False, rcon=True)
    out.append("")
    out += ring(rot, fields(W, 0, W), W, struct, "ring%db_mixF" % W, inj=False, rcon=False)
    out.append("")
    out += absorb(W, rot, struct, "b")
    out.append("")
    out += fin_synth(W, rot, struct, "ring%db_mixF" % W, "b")
    out.append("")
    out.append("pub func compress_w%db(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % W)
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, bcon: table<i64>, R: i64) {")
    out += compress_b_tail(W, struct, rot, msk, LA2, LB2, rate2, c_len, tc_s,
                           "ring%db_mixA" % W, "ring%db_mixB" % W, "ring%db_sponge_r" % W, "ring%db_sponge_c" % W,
                           "absorb%db" % W, "fin_synth%db" % W)
    return out

def compress_b_tail(W, struct, rot, msk, LA2, LB2, rate2, c_len, tc_s, mixA, mixB, spr, spc, absn, fins):
    half_w = W // 2
    out = []
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = %s()" % struct)
    for i in range(W):
        j = (i + half_w) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rot, j))
    for i in range(W):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, i % 8, msk))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8, msk))
    out.append("    l.N0 = (l.N0 ^ (t_lo & %s)) & 0xFFFFFFFF" % msk)
    out.append("    l.N%d = (l.N%d ^ (t_hi & %s)) & 0xFFFFFFFF" % (half_w, half_w, msk))
    out.append("    if last {")
    out.append("        l.N%d = (l.N%d ^ 0xFFFFFFFF) & 0xFFFFFFFF" % (half_w, half_w))
    out.append("    }")
    out.append("    l = %s(l, Pw, skey)" % absn)
    out.append("    var mA: i64 = 0")
    out.append("    var mC: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        mC = (r * 7 + ((skey >> 12) & 7)) & 31")
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mA, rcon, r)" % mixA)
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mC, rcon, (r + 8) & 15)" % mixB)
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mA, bcon, (r + 3) & 15)" % spr)
    out.append("        l = %s(l, r, skey, bcon, (r + 11) & 15)" % spc)
    # 轨间耦合（b，tcount==3；ta_l/ tb_l/ tc_l > 1 恒成立 ⇒ a1=1,b1=LA2+1,tc1=tc_s+1；
    #   tc_l>rate2+1 ⇒ cap1=tc_s+rate2+1）
    out.append("        %s" % couple_lines(0, tc_s))
    out.append("        %s" % couple_lines(LA2, tc_s + 1))
    out.append("        %s" % couple_lines(1, tc_s + rate2))
    out.append("        %s" % couple_lines(LA2 + 1, tc_s + rate2 + 1))
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, rot, i, (i * 3) & 31))
    out.append("    %s(h)" % fins)
    out.append("}")
    return out

def gen_x(W):
    rot = "rrp"; msk = "0xFFFFFFFF"
    struct = "Lanes%dx" % W
    a = (2 * W + 6) // 7
    while 3 * a >= W:
        a -= 1
    d = W - 3 * a
    while d < 1:
        a -= 1; d = W - 3 * a
    rate4 = (a + 1) // 2
    c_len = a - rate4
    tc_s = 2 * a
    ts3 = 3 * a
    out = []
    out.append("// === W=%d 四轨特化内核（x，n=88/92/96/128/144）——轨A[0..%d)、轨B[%d..%d)、海绵[%d..%d) rate4=%d、LFSR[%d..%d)；R=16 ===" % (W, a, a, 2 * a, 2 * a, 3 * a, rate4, ts3, W))
    out += emit_struct(W, struct)
    out.append("")
    out += ring(rot, fields(W, 0, a), a, struct, "ring%dx_mixA" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, a, 2 * a), a, struct, "ring%dx_mixB" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, 2 * a, 2 * a + rate4), rate4, struct, "ring%dx_sponge_r" % W, inj=True, rcon=True)
    out.append("")
    out += ring(rot, fields(W, 2 * a + rate4, 3 * a), c_len, struct, "ring%dx_sponge_c" % W, inj=False, rcon=True)
    out.append("")
    out += lfsr(rot, fields(W, ts3, W), d, struct, "lfsr%dx_mix" % W)
    out.append("")
    out += ring(rot, fields(W, 0, W), W, struct, "ring%dx_mixF" % W, inj=False, rcon=False)
    out.append("")
    out += absorb(W, rot, struct, "x")
    out.append("")
    out += fin_synth(W, rot, struct, "ring%dx_mixF" % W, "x")
    out.append("")
    out.append("pub func compress_w%dx(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % W)
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, bcon: table<i64>, xdcon: table<i64>, R: i64) {")
    out += compress_x_tail(W, struct, rot, msk, a, rate4, c_len, d, tc_s, ts3,
                           "ring%dx_mixA" % W, "ring%dx_mixB" % W, "ring%dx_sponge_r" % W, "ring%dx_sponge_c" % W,
                           "lfsr%dx_mix" % W, "absorb%dx" % W, "fin_synth%dx" % W)
    return out

def compress_x_tail(W, struct, rot, msk, a, rate4, c_len, d, tc_s, ts3, mixA, mixB, spr, spc, lf, absn, fins):
    half_w = W // 2
    out = []
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = %s()" % struct)
    for i in range(W):
        j = (i + half_w) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rot, j))
    for i in range(W):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, i % 8, msk))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8, msk))
    out.append("    l.N0 = (l.N0 ^ (t_lo & %s)) & 0xFFFFFFFF" % msk)
    out.append("    l.N%d = (l.N%d ^ (t_hi & %s)) & 0xFFFFFFFF" % (half_w, half_w, msk))
    out.append("    if last {")
    out.append("        l.N%d = (l.N%d ^ 0xFFFFFFFF) & 0xFFFFFFFF" % (half_w, half_w))
    out.append("    }")
    out.append("    l = %s(l, Pw, skey)" % absn)
    out.append("    var mA: i64 = 0")
    out.append("    var mC: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        mC = (r * 7 + ((skey >> 12) & 7)) & 31")
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mA, rcon, r)" % mixA)
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mC, rcon, (r + 8) & 15)" % mixB)
    out.append("        l = %s(l, r, skey, M0, N0, M1, N1, mA, bcon, (r + 3) & 15)" % spr)
    out.append("        l = %s(l, r, skey, bcon, (r + 11) & 15)" % spc)
    out.append("        l = %s(l, r, M0, N0, xdcon)" % lf)
    # 轨间耦合（x，tcount==4）：rate/tc_l > rate4+1 恒成立 ⇒ cap1=tc_s+rate4+1；再加 LFSR 逐字耦合 kd%a
    out.append("        %s" % couple_lines(0, tc_s))
    out.append("        %s" % couple_lines(a, tc_s + 1))
    out.append("        %s" % couple_lines(1, tc_s + rate4))
    out.append("        %s" % couple_lines(a + 1, tc_s + rate4 + 1))
    for kd in range(d):
        out.append("        %s" % couple_lines(kd % a, ts3 + kd))
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, rot, i, (i * 3) & 31))
    out.append("    %s(h)" % fins)
    out.append("}")
    return out

if __name__ == "__main__":
    specs = sys.argv[1:] or ["f16", "r20", "b16", "x16"]
    out = []
    for sp in specs:
        c = sp[0]
        W = int(sp[1:])
        if c == "f":
            if W in ALLF: out += gen_f(W)
        elif c == "r":
            if W in ALLR: out += gen_r(W)
        elif c == "b":
            if W in ALLF: out += gen_b(W)
        elif c == "x":
            if W in ALLF: out += gen_x(W)
        out.append("")
    sys.stdout.write("\n".join(out) + "\n")