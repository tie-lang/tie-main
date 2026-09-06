# -*- coding: utf-8 -*-
# gen_w_dual.py：生成 TSHA1 双轨特化内核（8<=W<16；轨A lanes[0..LA)、轨B lanes[LA..W)，
# LA=(W+1)/2；轨A 用 mA/rcon_idx=r、轨B 用 mC/rcon_idx=(r+8)&15；末块折回 N 平面偏移
# i*3；fin_synth 全 W 单环 L=W）。半宽（half=True，r 模型）rot=rrp16、iv/t 掩码 0xFFFF；
# 全宽（half=False）rot=rrp、掩码 0xFFFFFFFF。逐式镜像 tsha1_w48.tie 的 compress_w11h
# （r 半宽双轨）与 compress_w12（全宽双轨）语义。输出到 stdout。
# 用法：python gen_w_dual.py W1:h W2  ...   冒号后缀 h 表示半宽，如 8:h 15:h 12
import sys

def rotc(base, off):
    o = off % 32
    if o == 0:
        return base
    return "(%s + %d) & 31" % (base, o)

def ring(rot, fields, L, struct, name, inj=True, rcon=True):
    # fields: list of (M_name, N_name) length L
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
    # phase 1: S build
    for k in range(L):
        j2 = (k + 2) % L
        j3 = (k + 3) % L
        a = rotc("rA", 5 * k)
        b = rotc("rB", 7 * k + 3)
        out.append("    var (q%dm, q%dn) = tadd2(l.%s, l.%s," % (k, k, M[k], N[k]))
        out.append("                    %s(l.%s, %s), %s(l.%s, %s))" % (rot, M[j2], a, rot, N[j2], a))
        out.append("    var (s%dm, s%dn) = tadd2(q%dm, q%dn," % (k, k, k, k))
        out.append("                    %s(l.%s, %s), %s(l.%s, %s))" % (rot, M[j3], b, rot, N[j3], b))
    # phase 2: write back
    for k in range(L):
        out.append("    l.%s = s%dm" % (M[k], k))
        out.append("    l.%s = s%dn" % (N[k], k))
    # phase 3: tmul2 -> lanes[(k+1)%L]
    for k in range(L):
        k1 = (k + 1) % L
        k2 = (k + 2) % L
        out.append("    var (p%dm, p%dn) = tmul2(s%dm, s%dn, s%dm, s%dn)" % (k, k, k, k, k2, k2))
        out.append("    l.%s = (l.%s ^ p%dm) & 0xFFFFFFFF" % (M[k1], M[k1], k))
        out.append("    l.%s = (l.%s ^ p%dn) & 0xFFFFFFFF" % (N[k1], N[k1], k))
    # maj
    last = L - 1
    out.append("    var maj = quant3(s0m, s0n, s1m, s1n, s2m, s2n)")
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

def absorb(W, rot, suf=""):
    out = []
    out.append("func absorb%d%s(l: Lanes%d%s, Pw: Planes16, skey: i64) -> Lanes%d%s {" % (W, suf, W, suf, W, suf))
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

def fin_synth(W, rot, suf=""):
    out = []
    out.append("func fin_synth%d%s(h: ref table<i64>) {" % (W, suf))
    out.append("    var l = Lanes%d%s()" % (W, suf))
    for i in range(W):
        j = (i + 1) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rot, j))
    out.append("    var sf: i64 = 0")
    out.append("    while sf < 4 {")
    out.append("        l = ring%d%s_mixF(l, sf, 0x13579BDF)" % (W, suf))
    out.append("        sf = sf + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, rot, i, (i * 5) & 31))
    out.append("}")
    return out

def gen(W, half):
    nm = ("Lanes%dh" if half else "Lanes%d") % W
    rr = "rrp16" if half else "rrp"
    msk = "0xFFFF" if half else "0xFFFFFFFF"
    suf = "h" if half else ""
    LA = (W + 1) // 2
    half_w = W // 2
    out = []
    out.append("// ============================================================================")
    kind = "r 半宽" if half else "全宽"
    out.append("// W=%d 双轨特化内核（%s；轨A lanes[0..%d)、轨B lanes[%d..%d)，LA=%d）——" % (W, kind, LA, LA, W, LA))
    out.append("//   语义与通用 ring_mix 双轨（8<=W<16）逐式一致：轨A mA/rcon_idx=r、轨B mC/rcon_idx=(r+8)&15。")
    out.append("// ============================================================================")
    out.append("struct %s {" % nm)
    for i in range(W):
        out.append("    var M%d: i64 = 0" % i)
        out.append("    var N%d: i64 = 0" % i)
    out.append("}")
    out.append("")
    fieldsA = [("M%d" % i, "N%d" % i) for i in range(LA)]
    fieldsB = [("M%d" % i, "N%d" % i) for i in range(LA, W)]
    fieldsF = [("M%d" % i, "N%d" % i) for i in range(W)]
    out += ring(rr, fieldsA, LA, nm, "ring%d%s_mixA" % (W, suf), inj=True, rcon=True)
    out.append("")
    out += ring(rr, fieldsB, W - LA, nm, "ring%d%s_mixB" % (W, suf), inj=True, rcon=True)
    out.append("")
    out += ring(rr, fieldsF, W, nm, "ring%d%s_mixF" % (W, suf), inj=False, rcon=False)
    out.append("")
    out += absorb(W, rr, suf)
    out.append("")
    out += fin_synth(W, rr, suf)
    out.append("")
    out.append("// W=%d %s单块压缩（%s，R=8）" % (W, kind, "r 半宽" if half else "f/b/x 共用"))
    out.append("pub func compress_w%d%s(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % (W, suf))
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, R: i64) {")
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = %s()" % nm)
    for i in range(W):
        j = (i + half_w) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rr, j))
    for i in range(W):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, i % 8, msk))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8, msk))
    out.append("    l.N0 = (l.N0 ^ (t_lo & %s)) & 0xFFFFFFFF" % msk)
    out.append("    l.N%d = (l.N%d ^ (t_hi & %s)) & 0xFFFFFFFF" % (half_w, half_w, msk))
    out.append("    if last {")
    out.append("        l.N%d = (l.N%d ^ 0xFFFFFFFF) & 0xFFFFFFFF" % (half_w, half_w))
    out.append("    }")
    out.append("    l = absorb%d%s(l, Pw, skey)   // F1-2：位平面吸收（IV/计数器混入之后、轮循环之前，每块一次）" % (W, suf))
    out.append("    var mA: i64 = 0")
    out.append("    var mC: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        mC = (r * 7 + ((skey >> 12) & 7)) & 31")
    out.append("        l = ring%d%s_mixA(l, r, skey, M0, N0, M1, N1, mA, rcon, r)" % (W, suf))
    out.append("        l = ring%d%s_mixB(l, r, skey, M0, N0, M1, N1, mC, rcon, (r + 8) & 15)" % (W, suf))
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, rr, i, (i * 3) & 31))
    out.append("    fin_synth%d%s(h)" % (W, suf))
    out.append("}")
    return out

if __name__ == "__main__":
    specs = sys.argv[1:] or ["12"]
    out = []
    for sp in specs:
        sp = sp.strip()
        if sp.endswith(":h"):
            half = True
            W = int(sp[:-2])
        else:
            half = False
            W = int(sp)
        out += gen(W, half)
        out.append("")
    sys.stdout.write("\n".join(out) + "\n")