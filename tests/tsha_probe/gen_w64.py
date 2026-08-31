# -*- coding: utf-8 -*-
# gen_w64.py：生成 TSHA1 n=64（W=12）双轨特化内核（Lanes12 / ring12 / absorb12 /
# fin_synth12 / compress_w12），逐式镜像 tsha1_w48.tie 的 ring_mix 语义（L=6 双轨、
# fin_synth L=12 全环）。输出到 stdout，审查后插入 std/tsha1_w48.tie。
import sys

def rotc(base, off):
    o = off % 32
    if o == 0:
        return base
    return "(%s + %d) & 31" % (base, o)

def ring(rot, fields, L, name, inj=True, rcon=True):
    # fields: list of (M_name, N_name) length L
    M = [f[0] for f in fields]
    N = [f[1] for f in fields]
    out = []
    out.append("func %s(l: Lanes12, r: i64" % name)
    out.append("            , skey: i64")
    if inj:
        out.append("            , M0: i64, N0: i64, M1: i64, N1: i64, mA: i64")
    if rcon:
        out.append("            , rcon: table<i64>, rcon_idx: i64")
    out.append("            ) -> Lanes12 {")
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

def gen():
    out = []
    # struct Lanes12
    out.append("struct Lanes12 {")
    for i in range(12):
        out.append("    var M%d: i64 = 0" % i)
        out.append("    var N%d: i64 = 0" % i)
    out.append("}")
    out.append("")
    # ring12_mixA (track 0, lanes 0..5)
    fieldsA = [("M%d" % i, "N%d" % i) for i in range(6)]
    out += ring("rrp", fieldsA, 6, "ring12_mixA", inj=True, rcon=True)
    out.append("")
    # ring12_mixB (track 1, lanes 6..11)
    fieldsB = [("M%d" % i, "N%d" % i) for i in range(6, 12)]
    out += ring("rrp", fieldsB, 6, "ring12_mixB", inj=True, rcon=True)
    out.append("")
    # ring12_mixF (fin_synth full ring, lanes 0..11)
    fieldsF = [("M%d" % i, "N%d" % i) for i in range(12)]
    out += ring("rrp", fieldsF, 12, "ring12_mixF", inj=False, rcon=False)
    out.append("")
    # absorb12
    out.append("func absorb12(l: Lanes12, Pw: Planes16, skey: i64) -> Lanes12 {")
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
    out.append("            var an = w % 12")
    out.append("            var v = rrp(pv, a)")
    out.append("            var v2 = rrp(pv, a + 17)")
    for i in range(12):
        if i == 0:
            out.append("            if an == 0 {")
        elif i == 11:
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
    out.append("")
    # fin_synth12
    out.append("func fin_synth12(h: ref table<i64>) {")
    out.append("    var l = Lanes12()")
    for i in range(12):
        j = (i + 1) % 12
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = rrp(h[%d], 7)" % (i, j))
    out.append("    var sf: i64 = 0")
    out.append("    while sf < 4 {")
    out.append("        l = ring12_mixF(l, sf, 0x13579BDF)")
    out.append("        sf = sf + 1")
    out.append("    }")
    for i in range(12):
        out.append("    h[%d] = (l.M%d ^ rrp(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, (i * 5) & 31))
    out.append("}")
    out.append("")
    # compress_w12
    out.append("pub func compress_w12(h: ref table<i64>, msg: string, pos: i64, nbytes: i64,")
    out.append("            t_lo: i64, t_hi: i64, last: bool,")
    out.append("            iv: table<i64>, rcon: table<i64>, R: i64) {")
    out.append("    var (M0, N0, M1, N1, Pw, skey) = w48_planes_skey(msg, pos, nbytes)")
    out.append("    var l = Lanes12()")
    for i in range(12):
        j = (i + 6) % 12   # W/2 = 6
        out.append("    l.M%d = h[%d] & 0xFFFFFFFF" % (i, i))
        out.append("    l.N%d = rrp(h[%d], 7)" % (i, j))
    for i in range(12):
        out.append("    l.M%d = (l.M%d ^ (iv[%d] & 0xFFFFFFFF)) & 0xFFFFFFFF" % (i, i, i % 8))
        out.append("    l.N%d = (l.N%d ^ (iv[%d] & 0xFFFFFFFF)) & 0xFFFFFFFF" % (i, i, (i + 4) % 8))
    out.append("    l.N0 = (l.N0 ^ (t_lo & 0xFFFFFFFF)) & 0xFFFFFFFF")
    out.append("    l.N6 = (l.N6 ^ (t_hi & 0xFFFFFFFF)) & 0xFFFFFFFF")
    out.append("    if last {")
    out.append("        l.N6 = (l.N6 ^ 0xFFFFFFFF) & 0xFFFFFFFF")
    out.append("    }")
    out.append("    l = absorb12(l, Pw, skey)   // F1-2：位平面吸收（IV/计数器混入之后、轮循环之前，每块一次）")
    out.append("    var mA: i64 = 0")
    out.append("    var mC: i64 = 0")
    out.append("    var r: i64 = 0")
    out.append("    while r < R {")
    out.append("        mA = (r * 5 + ((skey >> 6) & 7)) & 31")
    out.append("        mC = (r * 7 + ((skey >> 12) & 7)) & 31")
    out.append("        l = ring12_mixA(l, r, skey, M0, N0, M1, N1, mA, rcon, r)")
    out.append("        l = ring12_mixB(l, r, skey, M0, N0, M1, N1, mC, rcon, (r + 8) & 15)")
    out.append("        r = r + 1")
    out.append("    }")
    for i in range(12):
        out.append("    h[%d] = (h[%d] ^ l.M%d ^ rrp(l.N%d, %d)) & 0xFFFFFFFF" % (i, i, i, i, (i * 3) & 31))
    out.append("    fin_synth12(h)")
    out.append("}")
    return out

if __name__ == "__main__":
    text = "\n".join(gen())
    sys.stdout.write(text + "\n")
