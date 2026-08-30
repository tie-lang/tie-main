# -*- coding: utf-8 -*-
"""TSHA1 家族总体架构图生成脚本（PIL）。输出 docs/papers/tsha1-arch.png
描述对 std/tsha1.tie 重构后的设计：f/b/r 复用同一「三进制双轨并行 + 最后综合」内核，
仅轮数/常量/输出字数不同；tsha1x 对 f+b 输出排列组合再算。"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsha1-arch.png")
W, H = 1500, 850
F = "C:/Windows/Fonts/simhei.ttf"

im = Image.new("RGB", (W, H), "#ffffff")
d = ImageDraw.Draw(im)

def font(sz):
    return ImageFont.truetype(F, sz)

f_box = font(19)
f_small = font(16)

def box(x, y, w, h, text, fill="#eef4ff", edge="#33475b", fs=None, lines=None):
    d.rectangle([x, y, x + w, y + h], fill=fill, outline=edge, width=2)
    if lines is None:
        lines = [text]
    f = fs or f_box
    # 自动缩减字号直到全部行能放下
    while max(d.textlength(t, font=f) for t in lines) > w - 16 and f.size > 12:
        f = ImageFont.truetype(F, f.size - 1)
    th = sum(d.textbbox((0, 0), t, font=f)[3] for t in lines)
    cy = y + h / 2 - th / 2
    for t in lines:
        tw = d.textlength(t, font=f)
        tb = d.textbbox((0, 0), t, font=f)
        d.text((x + w / 2 - tw / 2, cy - tb[3] / 2), t, font=f, fill="#1a2733")
        cy += d.textbbox((0, 0), t, font=f)[3] + 2

def arrow(x1, y1, x2, y2, color="#33475b", wd=3):
    d.line([x1, y1, x2, y2], fill=color, width=wd)
    ang = math.atan2(y2 - y1, x2 - x1)
    s = 12
    d.line([x2, y2, x2 - s * math.cos(ang - 0.4), y2 - s * math.sin(ang - 0.4)], fill=color, width=wd)
    d.line([x2, y2, x2 - s * math.cos(ang + 0.4), y2 - s * math.sin(ang + 0.4)], fill=color, width=wd)

# ---- 顶层：输入 ----
box(570, 26, 340, 58, "消息 M（任意字节串）", fill="#fdf3dc", edge="#a8863d",
    lines=["消息 M（任意字节串）"])

# 填充层
box(528, 112, 394, 62, "纯零填充 + 64 位计数器 t（mod 2^64）",
    lines=["纯零填充 + 64 位计数器 t", "（mod 2^64，长度绑定）"])
arrow(740, 84, 740, 112)

# ---- 主线到四模型（f/b/x/r）----
cols = [
    (76,  "tsha1f-256", "快速模型", ["三进制双轨并行 R_F=12", "trit 位平面（平衡加/乘/多数）", "双轨耦合 + 轮常量，末段 S=4 综合"], "#e8f4f8"),
    (424, "tsha1b-256", "复杂模型", ["三轨并行：双轨 + 第三轨海绵 R_B=14", "海绵吸收 / 8 字置换 / 双轨耦合", "末段 S=4 综合"], "#f3eef9"),
    (772, "tsha1x-256", "加强模型", ["四轨并行：双轨 + 海绵 + LFSR R_X=16", "LFSR 反馈⊕量化门控去线性化", "末段 fin_synth_x S=4 综合"], "#fdeeee"),
    (1120,"tsha1r-128", "轻量模型", ["三进制双轨并行 R_R=8", "trit 位平面扩散（轮数最少）", "末段 S=4 综合，仅取前 4 字"], "#eef9ef"),
]
bw, bh, tmp_top = 304, 62, 260
center_x = [x + bw / 2 for (x, _, _, _, _) in cols]

arrow(740, 174, 740, 196)
d.line([740, 196, center_x[-1], 196], fill="#33475b", width=3)      # 水平主线延伸到最后一栏中心
d.line([center_x[-1], 196, center_x[-1], tmp_top - 14], fill="#33475b", width=3)  # 尾段向下
for cx, (x, name, tag, steps, fill) in zip(center_x, cols):
    d.line([cx, 196, cx, tmp_top - 14], fill="#33475b", width=3)  # 每栏立柱
    box(x, tmp_top, bw, 58, name + "（" + tag + "）", fill="#ffffff", edge="#33475b",
        lines=[name + "（" + tag + "）"])
    y = tmp_top + 72
    for s in steps:
        box(x + 14, y, bw - 28, 54, s, fill=fill, edge="#7d8ea3", fs=f_small)
        y += 66

# ---- 底部输出：四栏底部统一箭头，输出框覆盖全域 ----
out_top = 700
for cx in center_x:
    arrow(cx, 530, cx, out_top - 6, color="#7d8ea3", wd=3)   # 530 = 第 3 步盒底部+下方
box(76, out_top, 1348, 76, "", fill="#ffffff", edge="#33475b")
box(76, out_top, 1348, 76,
    "任选一模型：位长 n 显式指定，n∈{2,3,4,6,8,12,16,24,32,48,64,88,96}（48 进制符号个数）",
    fs=font(19), lines=["任选一模型：位长 n 显式指定，n∈{2,3,4,6,8,12,16,24,32,48,64,88,96}（48 进制符号个数）",
                        "→ Base48 编码（n 个字符）｜ 其它进制 {2,3,8,16} 按信息量换算 ｜ _hex 可选（64/32）"])

im.save(OUT, dpi=(200, 200))
print("saved:", OUT, im.size)