# -*- coding: utf-8 -*-
# tests/hash2_probe/gen_vectors.py —— 参照生成器
# 来源：hashlib（sha3/md5/sha1）、pip 包 blake3 / xxhash / siphashc。
import hashlib
import blake3
import xxhash
import siphashc

def reps(c, n):
    return bytes([c]) * n

def msg_for(ln):
    if ln == 0:
        return b""
    if ln == 3:
        return b"abc"
    return reps(ord("a"), ln)

def main():
    lens = [0, 3, 55, 56, 64, 65, 128, 129, 256]
    print("== sha3 ==")
    for ln in lens:
        m = msg_for(ln)
        print("sha3-256 len=%d %s" % (ln, hashlib.sha3_256(m).hexdigest()))
        print("sha3-512 len=%d %s" % (ln, hashlib.sha3_512(m).hexdigest()))
    print("== blake3 ==")
    for ln in lens:
        print("blake3 len=%d %s" % (ln, blake3.blake3(msg_for(ln)).hexdigest()))
    print("== xxh3_64 ==")
    for ln in lens:
        v = xxhash.xxh3_64(msg_for(ln)).intdigest()
        print("xxh3 len=%d u64=%016x signed=%d" % (ln, v, v if v < 2**63 else v - 2**64))
    print("== siphash(key=0) ==")
    for ln in lens:
        print("sip len=%d hex=%016x" % (ln, siphashc.siphash(bytes(16), msg_for(ln))))
    print("== md5 ==")
    for ln in lens:
        print("md5 len=%d %s" % (ln, hashlib.md5(msg_for(ln)).hexdigest()))
    print("== sha1 ==")
    for ln in lens:
        print("sha1 len=%d %s" % (ln, hashlib.sha1(msg_for(ln)).hexdigest()))

if __name__ == "__main__":
    main()
