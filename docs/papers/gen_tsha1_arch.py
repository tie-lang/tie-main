# -*- coding: utf-8 -*-
"""TSHA1 家族总体架构图生成脚本（PIL）。输出 docs/papers/tsha1-arch.png"""
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
box(560, 112, 360, 62, "", fill="#ffffff", edge="#33475b")
box(560, 112, 360, 62, "纯零填充 + 64 位计数器 t（mod 2^64）",
    lines=["纯零填充 + 64 位计数器 t", "（mod 2^64，长度绑定）"])
arrow(740, 84, 740, 112)

# ---- 主线到五栏（四档 + trit 特写）----
cols = [
    (30,  "tsha1f-256", "快速档", ["T 轨旁路扰动", "BLAKE-ARX ×12", "24 基混合调度"], "#e8f4f8"),
    (318, "tsha1b-256", "复杂档", ["B 轨 ARX ×14", "T 轨 trit 位平面", "每 3 轮 SPN 强化"], "#f3eef9"),
    (606, "tsha1x-256", "加强档", ["f+b 输出排列组合", "再算 NX=6 固定序", "签名对象级强度"], "#fdeeee"),
    (894, "tsha1r-128", "轻量档", ["轻量 SPN 吸收", "长度绑定 + 终筛轮", "trit 终筛扰动"], "#eef9ef"),
    (1182,"trit 位平面", "包装层", ["u64=(M<<32)|N", "幅值 M / 符号 N 两平面", "运算走 &^|<<，无 mod3"], "#fbf6ea"),
]
bw, bh, tmp_top = 264, 62, 244
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

# ---- 底部输出：五栏底部统一箭头，输出框覆盖全域 ----
out_top = 700
for cx in center_x:
    arrow(cx, 466, cx, out_top - 6, color="#7d8ea3", wd=3)   # 466 = 第 3 步底部下方
box(230, out_top, 1200, 72, "", fill="#ffffff", edge="#33475b")
box(230, out_top, 1200, 72, "任选一档：摘要输出 → Base48（46 / 23 字符）  ｜  _hex 十六进制可选",
    fs=font(21), lines=["任选一档：摘要输出 → Base48（46 / 23 字符）", "｜  _hex 十六进制可选"])

im.save(OUT, dpi=(200, 200))
print("saved:", OUT, im.size)