# -*- coding: utf-8 -*-
# ascon_mac 向量参考生成器（使用官方 pyascon，与 std/ascon_mac.tie 对照）。
# 与 tie 探针共用同一组向量。需先: pip install ascon
import ascon

KEY = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
CASES = [
    ("empty", b""),
    ("abc", b"abc"),
    ("a32", b"a" * 32),
    ("long", b"Ascon-MAC-128 test message for robust verification."),
]

for name, msg in CASES:
    tag = ascon.mac(KEY, msg, "Ascon-Mac", 16).hex()
    print("%-5s %s" % (name, tag))