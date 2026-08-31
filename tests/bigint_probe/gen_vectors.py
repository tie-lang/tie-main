#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bigint 交叉向量生成器：用 Python 整数运算预计算期望值，生成
tests/bigint_probe/bigint_probe.tie（纯 tie 探针，硬编码断言，全平铺嵌套调用）。"""
import random
import math
import os
random.seed(20260829)

def H(x: int) -> str:
    if x < 0:
        return "-" + hex(-x)[2:]
    return hex(x)[2:]

def rnd(bits):
    return random.getrandbits(bits)

def rand_hex_by_bytes(nb):
    v = random.getrandbits(nb * 8)
    v |= (1 << (nb * 8 - 1)) | 1
    return hex(v)[2:]

def hex_rt():
    samples = ["0", "1", "2", "f", "ff", "ffffffff", "100000000",
               "ffffffffffffffff", "10000000000000000", "1ffffffffffffffff",
               "ffffffffffffffffffffffffffffffff",
               "100000000000000000000000000000000",
               "ffffffffffffffff00000000ffffffff",
               "1234567890abcdef1234567890abcdef",
               "0102030405060708090a0b0c0d0e0f10"]
    samples.append("".join(["ffffffff"] * 8))
    samples.append("".join(["ffffffff"] * 16))
    for _ in range(6):
        samples.append(rand_hex_by_bytes(random.choice([2, 3, 4, 8])))
    seen = set(); out = []
    for s in samples:
        s = s.lstrip("0") or "0"
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def add_cases():
    pairs = [("0", "0"), ("1", "1"), ("ffffffff", "1"),
             ("ffffffffffffffff", "1"), ("ffffffff", "ffffffff"),
             ("ffffffffffffffffffffffffffffffff", "1"),
             ("ffffffffffffffffffffffffffffffff", "ffffffff")]
    for _ in range(8):
        pairs.append((H(rnd(random.choice([64, 128, 256, 512]))), H(rnd(random.choice([64, 128, 256, 512])))))
    return [(a or "0", b or "0") for (a, b) in pairs]

def sub_cases():
    pairs = [("1", "1"), ("100000000", "1"), ("ffffffff", "80000000"),
             ("ffffffffffffffffffffffffffffffff", "ffffffff"),
             ("10000000000000000", "ffffffffffffffff")]
    for _ in range(8):
        a = rnd(random.choice([128, 256, 512]))
        b = rnd(random.choice([128, 256, 512])) % (a + 1)
        pairs.append((H(a), H(b) or "0"))
    return pairs

def mul_cases():
    pairs = [("0", "ffffffffffffffff"), ("1", "ffffffffffffffffffffffffffffffff"),
             ("ffffffff", "ffffffff"), ("100000000", "100000000"),
             ("ffffffff", "100000000"), ("ffffffffffffffff", "ffffffff"),
             ("deadbeef", "cafebabe"), ("12ab34cd56ef78", "908070605040302010")]
    for _ in range(8):
        pairs.append((H(rnd(random.choice([64, 128, 256, 300]))), H(rnd(random.choice([64, 128, 160, 300])))))
    return [(a or "0", b or "0") for (a, b) in pairs]

def divrem_cases():
    cases = [("ff", "10000000000000000000000000"), ("1", "2"),
             ("ffffffff", "100000000"), ("deadbeefcafebabe", "deadbeefcafebabe"),
             ("100000000", "100000000"),
             ("ffffffffffffffffffffffffffffffff", "7"),
             ("ffffffffffffffffffffffffffffffff", "100000000"),
             ("123456789abcdef0123456789abcdef0", "ffffffff"), ("0", "7"),
             ("123456789abcdef0123456789abcdef01", "123456789abcdef01"),
             ("ffffffffffffffffffffffffffffffffffffffff", "7fffffff00000001"),
             ("123456789abcdef0123456789abcdef", "3")]
    for _ in range(12):
        nb = random.choice([3, 4, 6])
        dv = rnd(nb * 32) | (1 << (nb * 32 - 1)) | 1
        nu = rnd(random.choice([nb * 32 + random.randint(16, 200), nb * 32 + random.randint(0, 20)]))
        if nu < dv:
            nu = dv + rnd(160) + 1
        cases.append((H(nu), H(dv)))
    return cases

def power_cases():
    out = [(3, 100, 1000000007), (2, 255, 2 ** 127 - 1),
           (123456789, 12345, 1000000007), (0, 100, 1000000007),
           (7, 0, 1000000007), (7, 5, 1), (7, 5, 0), (2, 3, 0x100000000),
           (0xffffffff, 0xffffffff, 0xffffffff)]
    for _ in range(6):
        b = rnd(random.choice([64, 128, 256]))
        e = rnd(random.choice([1, 8, 64, 256]))
        m = rnd(random.choice([64, 128, 256]))
        if m == 0:
            m = 1
        out.append((b, e, m))
    return out

def invmod_cases():
    cases = [(3, 7), (2, 1000000007), (3, 1000000007), (5, 17),
             (1, 1000000007), (7, 2 ** 127 - 1), (2, 4), (4, 8), (6, 9),
             (0, 5), (123456789, 1000000007)]
    for _ in range(8):
        m = rnd(random.choice([32, 64, 128])) | 1
        cases.append((rnd(32), m))
    return cases

def bit_cases():
    out = [("ffffffff", "00000001"), ("ffffffffffffffff", "1"), ("0f0f0f0f", "f0f0f0f0")]
    for _ in range(6):
        a = rnd(random.choice([64, 128, 256])); b = rnd(random.choice([64, 128, 256]))
        out.append((H(a) or "0", H(b) or "0"))
    res = []
    for (a, b) in out:
        res.append(("and", a, b)); res.append(("or", a, b))
    for _ in range(6):
        a = rnd(random.choice([64, 128, 256, 512]))
        k = random.choice([1, 4, 5, 31, 32, 33, 65, 128])
        res.append(("shl", H(a) or "0", str(k)))
        a2 = rnd(random.choice([64, 128, 256]))
        k2 = random.choice([1, 5, 31, 32, 64, 200])
        res.append(("shr", H(a2) or "0", str(k2)))
    return res

# ---- 生成探针（全平铺：无裸代码块、无临时变量声明，嵌套调用直接传表） ----
L = []
L.append('type tie<logic>')
L.append('// bigint_probe.tie：bigint 大数库交叉向量探针（Python 整数预生成，硬编码断言）。')
L.append('// 覆盖：from/to_hex 往返、add/sub 进位借位、mul 多 limb、divrem、powmod、invmod、')
L.append('// and/or/shl/shr/bitlen，及边界（0 除、模 0/模 1、奇偶模、无逆元）。')
L.append('import "../../std/bigint.tie"')
L.append('using bigint;')
L.append('')
L.append('func chk(name: string, got: string, want: string) {')
L.append('    if got == want {')
L.append('        println("PASS " + name)')
L.append('    } else {')
L.append('        println("FAIL " + name + " got=" + got)')
L.append('        println("      want=" + want)')
L.append('        exit(1)')
L.append('    }')
L.append('}')
L.append('')
L.append('func main() {')

k = 0
for s in hex_rt():
    k += 1
    L.append('    chk("hex_rt_%d", bigint.to_hex(bigint.from_hex("%s")), "%s")' % (k, s, s))

k = 0
for (a, b) in add_cases():
    k += 1
    want = H(int(a, 16) + int(b, 16))
    L.append('    chk("add_%d", bigint.to_hex(bigint.add(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, a, b, want))

k = 0
for (a, b) in sub_cases():
    k += 1
    want = H(int(a, 16) - int(b, 16))
    L.append('    chk("sub_%d", bigint.to_hex(bigint.sub(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, a, b, want))

k = 0
for (a, b) in [("0", "0"), ("1", "0"), ("0", "1"),
               ("1234567890abcdef", "1234567890abcdef"),
               ("ffffffffffffffffffffffffffffffff", "ffffffffffffffff0000000100000000"),
               ("00000000000000000000000000000001", "2")]:
    k += 1
    va, vb = int(a, 16), int(b, 16)
    want = 0 if va == vb else (1 if va > vb else -1)
    L.append('    chk("cmp_%d", to_string(bigint.cmp(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%d")' % (k, a, b, want))

k = 0
for (a, b) in mul_cases():
    k += 1
    want = H(int(a, 16) * int(b, 16))
    L.append('    chk("mul_%d", bigint.to_hex(bigint.mul(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, a, b, want))

k = 0
for (a, b) in divrem_cases():
    k += 1
    qwant, rwant = (0, 0) if int(b, 16) == 0 else divmod(int(a, 16), int(b, 16))
    L.append('    chk("dq_%d", bigint.to_hex(bigint.div(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, a, b, H(qwant)))
    L.append('    chk("dr_%d", bigint.to_hex(bigint.mod(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, a, b, H(rwant)))

# 边界：0 除、模 0、模 1
L.append('    chk("div0_q", bigint.to_hex(bigint.div(bigint.from_hex("1234"), bigint.from_hex("0"))), "0")')
L.append('    chk("div0_r", bigint.to_hex(bigint.mod(bigint.from_hex("1234"), bigint.from_hex("0"))), "0")')
L.append('    chk("mod1", bigint.to_hex(bigint.mod(bigint.from_hex("abcdef123456"), bigint.from_hex("1"))), "0")')

# 结构一致性：mul(q,b)+r == a（2 组，显式 divrem 元组）
cons = [("deadbeefcafebabe12", "1000000"), ("123456789abcdef0123456789abcdef01", "ffffffff")]
idx = 0
for (a, b) in cons:
    idx += 1
    qwant, rwant = divmod(int(a, 16), int(b, 16))
    L.append('    var dx%d = bigint.from_hex("%s")' % (idx, a))
    L.append('    var dy%d = bigint.from_hex("%s")' % (idx, b))
    L.append('    var (dq%d, dr%d) = bigint.divrem(dx%d, dy%d)' % (idx, idx, idx, idx))
    L.append('    chk("cons_q%d", bigint.to_hex(dq%d), "%s")' % (idx, idx, H(qwant)))
    L.append('    chk("cons_r%d", bigint.to_hex(dr%d), "%s")' % (idx, idx, H(rwant)))
    L.append('    chk("cons_mq_r%d", bigint.to_hex(bigint.add(bigint.mul(dq%d, dy%d), dr%d)), "%s")' % (idx, idx, idx, idx, H(int(a, 16))))

k = 0
for (b, e, m) in power_cases():
    k += 1
    want = 0 if (m == 0 or m == 1) else pow(b % m, e, m)
    L.append('    chk("pow_%d", bigint.to_hex(bigint.powmod(bigint.from_hex("%s"), bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, H(b), H(e), H(m), H(want)))

k = 0
for (a, m) in invmod_cases():
    k += 1
    if m <= 1:
        want = 0
    elif math.gcd(a, m) != 1:
        want = 0
    else:
        want = pow(a, -1, m)
    L.append('    chk("inv_%d", bigint.to_hex(bigint.invmod(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, H(a), H(m), H(want)))

k = 0
for (kind, av, bv) in bit_cases():
    k += 1
    if kind == "and":
        want = H(int(av, 16) & int(bv, 16))
        L.append('    chk("and_%d", bigint.to_hex(bigint.and(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, av, bv, want))
    elif kind == "or":
        want = H(int(av, 16) | int(bv, 16))
        L.append('    chk("or_%d", bigint.to_hex(bigint.or(bigint.from_hex("%s"), bigint.from_hex("%s"))), "%s")' % (k, av, bv, want))
    elif kind == "shl":
        want = H(int(av, 16) << int(bv))
        L.append('    chk("shl_%d", bigint.to_hex(bigint.shl_bits(bigint.from_hex("%s"), %s)), "%s")' % (k, av, bv, want))
    elif kind == "shr":
        want = H(int(av, 16) >> int(bv))
        L.append('    chk("shr_%d", bigint.to_hex(bigint.shr_bits(bigint.from_hex("%s"), %s)), "%s")' % (k, av, bv, want))

k = 0
for v in ["0", "1", "2", "f", "80", "ffffffff", "100000000", "7fffffffffffffff", "8000000000000000"]:
    k += 1
    want = int(v, 16).bit_length()
    L.append('    chk("bitlen_%d", to_string(bigint.bitlen(bigint.from_hex("%s"))), "%d")' % (k, v, want))

L.append('    println("bigint 探针全部通过")')
L.append('}')

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bigint_probe.tie")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("gen ok, assertions-lines:", len(L) - 14)