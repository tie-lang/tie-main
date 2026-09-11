# -*- coding: utf-8 -*-
# tsha1 p.7.1.8 —— 补齐 f/b/x/r × 位长 {16,24,32} 的 KAT 向量表生成器
# ----------------------------------------------------------------------------
# 唯一语义源：同目录 gen_tsha1_core.py（state-per-n 重构的 canonical core）。
# 本脚本仅调用 core 的 digest / encode / words_for，补齐 p.7.1.8 里程碑要求的
# 「f/b/x 至少 16/24/32，r 对齐 16/24/32」各位长（既有 f/b/x/r probe 仅抽检
# {2,8,16,48,64,69,88,92,96,128,144}，缺 24/32）的已知答案向量。
# 消息集对齐设计稿 §6.6「空串/abc/长消息/边界长度」。
# ----------------------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_tsha1_core as core

MODELS = ('f', 'b', 'x', 'r')
N_SET = (16, 24, 32)


def messages():
    return [
        ("empty", b""),
        ("abc", b"abc"),
        ("a1000", b"a" * 1000),     # 长消息（多块）
        ("a64", b"a" * 64),         # 边界长度（= 满一块，触及末块零填补充分支）
    ]


def main():
    for model in MODELS:
        print("TSHA1%s p.7.1.8 KAT vectors (16/24/32)" % model.upper())
        for name, msg in messages():
            print("[%s len=%d]" % (name, len(msg)))
            for n in N_SET:
                b48 = core.encode(model, msg, n, base=48)
                b16 = core.encode(model, msg, n, base=16)
                print("  %-8s n=%-3d b48=%s" % (name, n, b48))
                print("             b16=%s" % b16)
        print()


if __name__ == "__main__":
    main()