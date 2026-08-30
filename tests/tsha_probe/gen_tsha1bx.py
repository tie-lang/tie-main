# -*- coding: utf-8 -*-
# tsha1b v2 —— KAT 向量表生成器
# ----------------------------------------------------------------------------
# 唯一语义源：同目录 gen_tsha1_core.py（state-per-n 重构的 canonical core）。
# 本脚本不再自带任何哈希/编码/常量逻辑，仅调用 core 的 digest / encode /
# words_for 输出 b 的 KAT 向量表（全宽 hex + base48 前 n 符号）。
# 设计依据：
#   docs/superpowers/specs/2026-08-30-tsha1-state-per-n-design.md（结构）
# ----------------------------------------------------------------------------
import os
import sys

# 保证可被当作独立脚本运行，也能被同目录脚本 import。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_tsha1_core as core

MODEL = 'b'
N_SET = (2, 8, 16, 48, 64, 69, 92, 96, 128, 144)


def messages():
    return [
        ("empty", b""),
        ("abc", b"abc"),
        ("a1000", b"a" * 1000),
        ("a55", b"a" * 55),
        ("a56", b"a" * 56),
        ("a63", b"a" * 63),
        ("a64", b"a" * 64),
        ("a65", b"a" * 65),
        ("a127", b"a" * 127),
        ("a128", b"a" * 128),
        ("a129", b"a" * 129),
        ("a256", b"a" * 256),
    ]


def main():
    print("TSHA1b KAT vectors (state-per-n v2, source=gen_tsha1_core)")
    for name, msg in messages():
        print("[%s len=%d]" % (name, len(msg)))
        for n in N_SET:
            if not core.is_bits48(n):
                continue
            full = core.digest(MODEL, msg, n)
            b48 = core.encode(MODEL, msg, n)
            print("  n=%-3d W=%-2d full=%s  b48=%s" %
                  (n, core.words_for(n, MODEL), full, b48))


if __name__ == "__main__":
    main()