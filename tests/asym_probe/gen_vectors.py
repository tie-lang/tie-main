# gen_vectors.py —— Ed25519 / X25519 交叉向量生成器（Python / PyNaCl 为独立对照实现）。
# 作用：
#   1) 计算并打印 bigint 需要的全部曲线常量（p, l, d, Bx, By, 以及 sqrt 算法 EXP、
#      sqrt(-1)、掩码），全部转小写十六进制（bigint.from_hex 吃大端 hex）。
#   2) 用 PyNaCl（libsodium，RFC 8032/7748 的独立高效实现）交叉核实/推导测试向量，
#      供探针硬编码断言：Ed25519 的 (seed, msg) -> (pubkey, sig)，X25519 的私钥/DH。
# PyNaCl 的 EdDSA 遵循 RFC 8032（SHA-512），scalarmult 遵循 RFC 7748。
# 运行：python3 tests/asym_probe/gen_vectors.py
import nacl.signing
import nacl.bindings
import os

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, P - 2, P)) % P   # 扭曲常数 d（a=-1 曲线：d = -121665/121666）
BY = 4 * pow(5, P - 2, P) % P
BX = 15112221349535400772501151409588531511454012693041857206046113283949847762202
EXP = (P + 3) // 8                 # = 2^252 - 2
SQRT_NEG_ONE = pow(2, (P - 1) // 4, P)   # sqrt(-1) mod p
MASK255 = 2**255 - 1

def hfull(n, width): return format(n, "0%dx" % width).lower()

print("== base point / field constants (bigint inline) ==")
print("P   =", hfull(P, 64))
print("L   =", hfull(L, 64))
print("D   =", hfull(D, 64))
print("BX  =", hfull(BX, 64))
print("BY  =", hfull(BY, 64))
print("EXP =", hfull(EXP, 62))          # 2^252-2 (62 hex)
print("SQR =", hfull(SQRT_NEG_ONE, 64))
print("MASK= %x" % MASK255)

def emit(seedh, msg, label):
    s = bytes.fromhex(seedh) if len(seedh) == 64 else seedh
    _sk = nacl.signing.SigningKey(s)
    sig = _sk.sign(msg).signature
    print("--" + label + "--")
    print("seed =", s.hex())
    print("pub  =", _sk.verify_key.encode().hex())
    print("msg  =", msg.hex() if msg else "(empty)")
    print("sig  =", sig.hex())

print("\n== Ed25519 RFC 8032 vector 1 (task-specified) ==")
emit("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60", b"", "rfc1")

print("\n== Ed25519 vector 2 / 3 / RFC1-abc (内存核对) ==")
emit("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb", bytes([0x72]), "rfc2")
emit("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7", bytes.fromhex("af82"), "rfc3")
emit("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60", b"abc", "rfc1abc")

print("\n== Ed25519 long-message vector ==")
mem = bytes(range(32)) * 4          # 128 字节长消息（覆盖多块 + 边界）
emit("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7", mem, "long")

def emseed(seed, m, label):
    _sk = nacl.signing.SigningKey(seed)
    print("--" + label + "--")
    print("seed =", seed.hex())
    print("pub  =", _sk.verify_key.encode().hex())
    print("msg  =", m.hex() if m else "(empty)")
    print("sig  =", _sk.sign(m).signature.hex())

print("\n== Ed25519 random roundtrip set ==")
for i in range(3):
    emseed(os.urandom(32), os.urandom([0, 30, 200][i]), "rand%d" % i)

print("\n== X25519 RFC 7748 vector 1 (task-specified) ==")
k1 = bytes.fromhex("77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a")
u1 = bytes.fromhex("de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f")
print("sk   =", k1.hex())
print("u    =", u1.hex())
print("shared=", nacl.bindings.crypto_scalarmult(k1, u1).hex())

print("\n== X25519 RFC 7748 vector 2 ==")
k2 = bytes.fromhex("4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742")
u2 = bytes.fromhex("e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c")
print("sk   =", k2.hex())
print("u    =", u2.hex())
print("shared=", nacl.bindings.crypto_scalarmult(k2, u2).hex())

print("\n== X25519 base-point9 scalarmult ==")
base9 = bytearray(32); base9[0] = 9; base9 = bytes(base9)
for khex in ["77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a",
             "a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4",
             "0000000000000000000000000000000000000000000000000000000000000009"]:
    print("sk   =", khex)
    print("pub(u)=", nacl.bindings.crypto_scalarmult(bytes.fromhex(khex), base9).hex())