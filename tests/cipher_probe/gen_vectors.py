# -*- coding: utf-8 -*-
# 对称加密家族向量参考生成器（交叉核对用，与 tie 探针共用同一组向量）。
#   依赖：pycryptodome（AES/ChaCha20）、pyascon（Ascon-128a AEAD）。
#   AES ECB 用 FIPS 197 官方向量 + pycryptodome ECB 复核; CBC 用 pycryptodome AES（PKCS7）;
#   ChaCha20 用 RFC 8439 官方 + pycryptodome ChaCha20; Ascon-128a AEAD 用官方 pyascon。
import ascon
from Crypto.Cipher import AES, ChaCha20
from Crypto.Util.Padding import pad, unpad

HX = lambda b: b.hex()

# ---- AES ----
kt128 = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
kt256 = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
pt = bytes.fromhex("00112233445566778899aabbccddeeff")
print("FIPS17_128_enc=", HX(AES.new(kt128, AES.MODE_ECB).encrypt(pt)))
print("FIPS17_256_enc=", HX(AES.new(kt256, AES.MODE_ECB).encrypt(pt)))

iv = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
print("cbc_128_empty_enc=", HX(AES.new(kt128, AES.MODE_CBC, iv).encrypt(pad(b"", 16))))
for name, m in [("cbc_128_short", b"hi"), ("cbc_128_blk1", pt), ("cbc_128_2blk", pt * 2)]:
    e = AES.new(kt128, AES.MODE_CBC, iv).encrypt(pad(m, 16))
    d = unpad(AES.new(kt128, AES.MODE_CBC, iv).decrypt(e), 16)
    print(f"{name}_enc=", HX(e), f"rt={d == m}")
e = AES.new(kt256, AES.MODE_CBC, iv).encrypt(pad(pt, 16))
d = unpad(AES.new(kt256, AES.MODE_CBC, iv).decrypt(e), 16)
print("cbc_256_blk1_enc=", HX(e), f"rt={d == pt}")

# ---- ChaCha20 独立参考实现（RFC 8439，纯 Python，与 tie 版互为独立实现）----
_ROT = lambda v, r: ((v << r) & 0xFFFFFFFF) | (v >> (32 - r))
def _qr(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = _ROT(x[d], 16)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = _ROT(x[b], 12)
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF; x[d] ^= x[a]; x[d] = _ROT(x[d], 8)
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF; x[b] ^= x[c]; x[b] = _ROT(x[b], 7)
def _chacha_block(key, counter, nonce):
    c = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    k = [int.from_bytes(key[i:i+4], "little") for i in range(0, 32, 4)]
    n = [int.from_bytes(nonce[i:i+4], "little") for i in range(0, 12, 4)]
    x = c + k + [counter & 0xFFFFFFFF] + n
    w = list(x)
    for _ in range(10):
        _qr(w, 0, 4, 8, 12); _qr(w, 1, 5, 9, 13); _qr(w, 2, 6, 10, 14); _qr(w, 3, 7, 11, 15)
        _qr(w, 0, 5, 10, 15); _qr(w, 1, 6, 11, 12); _qr(w, 2, 7, 8, 13); _qr(w, 3, 4, 9, 14)
    ks = bytearray()
    for i in range(16):
        ks += ((w[i] + x[i]) & 0xFFFFFFFF).to_bytes(4, "little")
    return bytes(ks)
def chacha20_ref(key, nonce, counter, data):
    ctr = counter
    out = bytearray()
    for off in range(0, len(data), 64):
        ks = _chacha_block(key, ctr, nonce)
        blk = data[off:off+64]
        out += bytes(a ^ b for a, b in zip(blk, ks))
        ctr += 1
    return bytes(out)

ckey = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
cnonce = bytes.fromhex("000000000000004a00000000")
msg_rfc = bytes.fromhex("4c616469657320616e642047656e746c656d656e206f662074686520636c617373206f66202739393a204966204920636f756c64206f6666657220796f75206f6e6c79206f6e652074697020666f7220746865206675747572652c2073756e73637265656e20776f756c642062652069742e")
assert len(msg_rfc) == 114
# RFC 8439 §2.3.2：counter=1
print("chacha_rfc_ct=", HX(chacha20_ref(ckey, cnonce, 1, msg_rfc)))
print("chacha_long_ct=", HX(chacha20_ref(ckey, cnonce, 1, msg_rfc * 3)))
print("chacha_empty_ct=", HX(chacha20_ref(ckey, cnonce, 1, b"")))
print("chacha_c0=", HX(chacha20_ref(ckey, bytes.fromhex("000000000000000000000000"), 0,
                                   b"hello ascon cipher probe 000")))

# ---- Ascon-128a AEAD（官方 pyascon，rate=16, a=12, b=8）----
akey = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
anonce = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
def aead_enc(ad, msg):
    return ascon.encrypt(akey, anonce, ad, msg, variant="Ascon-128a")
def aead_dec(ad, ct):
    return ascon.decrypt(akey, anonce, ad, ct, variant="Ascon-128a")
cases = [("empty", b"", b""), ("ad_only", b"AD", b""), ("msg_short", b"", b"ab"),
         ("both", b"ASCON", b"ascon"), ("1blk", b"associated data block", b"x" * 16),
         ("2blk", b"ad" * 9, b"plaintext" * 4), ("long_ad", b"0123456789abcdef" * 3, b""),
         ("long", b"ad block" * 4, b"0123456789abcdef" * 3 + b"tail")]
for name, ad, msg in cases:
    ct = aead_enc(ad, msg)
    d = aead_dec(ad, ct)
    print(f"ascon_{name}_ct=", HX(ct), f"rt={d == msg and d is not None}")