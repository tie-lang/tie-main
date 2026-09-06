# -*- coding: utf-8 -*-
# gen_w_small.py：生成 TSHA1 单环（L=W<8）特化内核（LanesW / ringW_mix / absorbW /
# fin_synthW / compress_wW），逐式镜像 tsha1_w48.tie 通用 ring_mix 单环语义
# （start=0, L=W, kind=1；inj 注入 M0/N0→w0、M1/N1→w1；rcon_idx=r）。
# 输出到 stdout，审查后插入 std/tsha1_w48.tie。
# 用法：python gen_w_small.py [W...]   （默认 3 5 6）
import sys

def rotc(base, off):
    o = off % 32
    if o == 0:
        return base
    return "(%s + %d) & 31" % (base, o)

def ring(fields, L, name, rot, inj=True, rcon=True, nm=None):
    M = [f[0] for f in fields]
    N = [f[1] for f in fields]
    if nm is None:
        nm = "Lanes%d" % L
    out = []
    out.append("func %s(l: %s, r: i64" % (name, nm))
    out.append("            , skey: i64")
    if inj:
        out.append("            , M0: i64, N0: i64, M1: i64, N1: i64, mA: i64")
    if rcon:
        out.append("            , rcon: table<i64>, rcon_idx: i64")
    out.append("            ) -> %s {" % nm)
    out.append("    var rA = (r * 3 + (skey & 7)) & 31")
    out.append("    var rB = (r * 7 + ((skey >> 3) & 7)) & 31")
    # phase 1: S build (single ring: j2=(k+2)%L, j3=(k+3)%L)
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
    # maj (L>=3: quant3(s0,s1,s2))
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

def gen(W, rot="rrp", half=False):
    nm = ("Lanes%dh" if half else "Lanes%d") % W
    rr = rot
    msk = "0xFFFF" if half else "0xFFFFFFFF"
    suf = "h" if half else ""
    out = []
    out.append("// ============================================================================")
    kind = "r 半宽" if half else "全宽"
    out.append("// W=%d 单环特化内核（n=%s %s；L=W 单环）——语义与通用 ring_mix 单环逐式一致。" % (W, "/".join(str(n) for n in N_OF_W.get(W, [W])), kind))
    out.append("// ============================================================================")
    out.append("struct %s {" % nm)
    for i in range(W):
        out.append("    var M%d: i64 = 0" % i)
        out.append("    var N%d: i64 = 0" % i)
    out.append("}")
    out.append("")
    fields = [("M%d" % i, "N%d" % i) for i in range(W)]
    out += ring(fields, W, "ring%d%s_mix" % (W, suf), rr, inj=True, rcon=True, nm=nm)
    out.append("")
    out += ring(fields, W, "ring%d%s_mixF" % (W, suf), rr, inj=False, rcon=False, nm=nm)
    out.append("")
    out += absorb(W, rr, suf)
    out.append("")
    out.append("// W=%d %s终筛" % (W, kind))
    out.append("func fin_synth%d%s(h: ref table<i64>) {" % (W, suf))
    out.append("    var l = %s()" % nm)
    for i in range(W):
        j = (i + 1) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rr, j))
    out.append("    var sf: i64 = 0")
    out.append("    while sf < 4 {")
    out.append("        l = ring%d%s_mixF(l, sf, 0x13579BDF)" % (W, suf))
    out.append("        sf = sf + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, rr, i, (i * 5) & 31))
    out.append("}")
    out.append("")
    out.append("// W=%d %s单块压缩（%s，R 各档）" % (W, kind, "r 半宽 R=8" if half else "f/b/x 共用"))
    out.append("pub func compress_w%d%s(h: ref table<i64>, msg: string, pos: i64, nbytes: i64," % (W, suf))
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, R: i64) {")
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = %s()" % nm)
    half_w = W // 2
    for i in range(W):
        j = (i + half_w) % W
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = %s(h[%d], 7)" % (i, rr, j))
    for i in range(W):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, i % 8, msk))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & %s)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8, msk))
    out.append("    l.N0 = (l.N0 ^ (t_lo & %s)) & 0xFFFFFFFF" % msk)
    out.append("    l.N%d = (l.N%d ^ (t_hi & %s)) & 0xFFFFFFFF" % (W // 2, W // 2, msk))
    out.append("    if last {")
    out.append("        l.N%d = (l.N%d ^ 0xFFFFFFFF) & 0xFFFFFFFF" % (W // 2, W // 2))
    out.append("    }")
    out.append("    l = absorb%d%s(l, Pw, skey)" % (W, suf))
    out.append("    var mA: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        l = ring%d%s_mix(l, r, skey, M0, N0, M1, N1, mA, rcon, r)" % (W, suf))
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(W):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ %s(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, rr, i, (i * 3) & 31))
    out.append("    fin_synth%d%s(h)" % (W, suf))
    out.append("}")
    return out

# n -> W 映射（全宽 f/b/x 模型）
N_OF_W = {}
import math
def words_for(n):
    return max(1, math.ceil(n * 1745300781475361 / 10000000000000000))
for n in [2,3,4,6,8,12,16,24,32,48,64,69,88,92,96,128,144]:
    w = words_for(n)
    N_OF_W.setdefault(w, []).append(n)

if __name__ == "__main__":
    ws = [int(x) for x in sys.argv[1:]] or [3, 5, 6]
    out = []
    for W in ws:
        out += gen(W)
        out.append("")
    import sys as _sys
    _sys.stdout.write("\n".join(out) + "\n")