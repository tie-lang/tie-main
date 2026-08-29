# 生成 SHAKE128/256 交叉核对向量（NIST hashlib.shake_128/_256，标准参考实现），
# 与 tests/shake_probe/shake_probe.tie 中固化值一一对应。
# 用法: python gen_vectors.py
import hashlib

def xof(o, msg, n):
    return (hashlib.shake_128 if o == 128 else hashlib.shake_256)(msg).hexdigest(n)

CASES = [
    # (消息, 消息hex注记, outlen)
    (b"",     "empty", 32),
    (b"abc",  "abc",   32),
    # outlen 非 32 倍（48/64）
    (b"",  "empty", 48), (b"",  "empty", 64),
    (b"abc","abc",   48), (b"abc","abc",   64),
    # 非 8 倍（XOF 任意字节长度）
    (b"",  "empty", 17),
    # 跨 rate 块多段挤压：SHAKE128 rate=168 / SHAKE256 rate=136
    (b"abc","abc", 168), (b"abc","abc", 169), (b"abc","abc", 136),
    (b"",  "empty", 136),
]
for o in (128, 256):
    for msg, tag, n in CASES:
        print("SHAKE%d  msg=%-6s outlen=%-3d = %s" % (o, tag, n, xof(o, msg, n)))