# -*- coding: utf-8 -*-
"""TSHA1 学术论文 docx 生成脚本（python-docx）。
排版：A4；正文宋体小四(12pt) 1.5 倍行距 + 首行缩进 2 字符；标题黑体三号居中；
英文 Abstract Times New Roman；表格 Table Grid。
"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

OUT = os.environ.get("TSHA1_PAPER_OUT",
                     os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsha1-paper.docx"))

doc = Document()

# ---- 页面：A4 + 页边距 ----
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.left_margin = sec.right_margin = Cm(3.17)

def _set_font(run, zh, en, size, bold=False, italic=False, color=None):
    run.font.name = en
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    r = run._element.rPr.rFonts
    r.set(qn("w:eastAsia"), zh)

def para(text="", zh="宋体", en="Times New Roman", size=12, bold=False,
         align=None, indent=True, space_after=6, italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    if indent:
        pf.first_line_indent = Pt(size * 2)   # 首行缩进 2 字符
    if align is not None:
        p.alignment = align
    if text:
        if "**" in text:
            # 支持 **加粗** 内联标记（python-docx 不解析 Markdown，手动分段渲染）
            for k, seg in enumerate(text.split("**")):
                if not seg:
                    continue
                r = p.add_run(seg)
                _set_font(r, zh, en, size, bold=(bold or (k % 2 == 1)), italic=italic)
        else:
            r = p.add_run(text)
            _set_font(r, zh, en, size, bold=bold, italic=italic)
    return p

def heading(text, size=14):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.5
    r = p.add_run(text)
    _set_font(r, "黑体", "Times New Roman", size, bold=True)
    return p

def add_table(headers, rows, caption):
    para(caption, zh="黑体", size=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=4)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.cell(0, j)
        cell.text = ""
        r = cell.paragraphs[0].add_run(h)
        _set_font(r, "黑体", "Times New Roman", 10.5, bold=True)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = t.cell(i + 1, j)
            cell.text = ""
            r = cell.paragraphs[0].add_run(v)
            _set_font(r, "宋体", "Times New Roman", 10.5)
            if j == 0:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para("", size=6, indent=False, space_after=4)
    return t

# ================= 标题 =================
para("TSHA1：一种多原语确定性组合的安全杂凑函数家族", zh="黑体", size=16,
     align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=2)
para("——新型构造、强度梯度与可论证安全性质（基于自举语言 TIE 的纯语言实现）", zh="黑体", size=12,
     align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=10)
para("侯杨宝鑫，TIE 项目团队", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=2)
para("（侯杨宝鑫为 TIE 项目团队成员；单位：TIE Language Project）", zh="楷体", size=10.5,
     align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=10)

# ================= 中文摘要 =================
heading("摘　要", size=12)
para("TSHA1 是为自举编程语言 TIE 设计并完全以该语言实现的**新型安全杂凑函数家族**，"
     "包含快速档 tsha1f、复杂档 tsha1b、加强档 tsha1x 与轻量档 tsha1r。其“新型”体现在"
     "构造而非机理：不以单一原语为卖点，而是将已经充分公开分析的 BLAKE 型 ARX 轮、"
     "Ascon 型位切片 SPN 作为结构骨架，叠加自主设计的 trit 位平面旁路扩散与 f+b 输出"
     "排列组合再算，形成四档速度/强度梯度。“更安全”体现在四方面可论证性质：其一，"
     "计数器式纯零填充与 64 位长度绑定在结构上免疫 Merkle–Damgård 型长度扩展攻击；"
     "其二，全部轮常量由“标准种子＋PRNG 扩展”确定性生成、可复现，杜绝猜测常量与"
     "后门注入疑虑；其三，结构信任完全继承已审原语体系，自创层仅限参数/常量/轮数/"
     "排列组合序，安全性可随组合逐一论证；其四，多扩散构件交叠（ARX＋SPN＋位平面）"
     "与加强档的排列组合再算共同抬高结构化攻击的破解成本。实现为纯 TIE、零外部依赖，"
     "摘要默认采用自行设计的 Base48（48 符号连续字符集）输出，便于人类抄写与审计链标识；"
     "探针以跨平台交叉生成的已知答案向量逐字节核对。基准实测（TIE 自写编译器/IR 执行层）"
     "大消息稳态吞吐 tsha1f≈34 MB/s、tsha1b≈22、tsha1r≈22、tsha1x≈13，档位间速度差"
     "与强度梯度设计相符。该家族已作为插件化内核审计链的指纹与凭证签名哈希底座投入使用。",
     size=12, space_after=6)
p = para("", size=12, indent=False, space_after=10)
r0 = p.add_run("关键词：")
_set_font(r0, "黑体", "Times New Roman", 12, bold=True)
for w in ["新型安全杂凑", "确定性组合构造", "抗长度扩展", "多扩散构件", "ARX", "SPN", "强度梯度", "Base48"]:
    p.add_run(w + " ")

# ================= English Abstract =================
heading("Abstract", size=12)
para("TSHA1 is a new family of cryptographic hash functions designed for and fully implemented "
     "in the self-hosting programming language TIE, comprising four variants: tsha1f (fast), "
     "tsha1b (complex), tsha1x (strengthened) and tsha1r (lightweight). Its novelty lies in "
     "construction rather than a single primitive: well-analyzed BLAKE-style ARX rounds and "
     "Ascon-style bit-sliced SPN layers serve as the structural backbone, on top of which a "
     "self-designed trit bit-plane bypass diffusion and an f+b output permutation chain are "
     "superimposed, yielding a four-variant speed/strength hierarchy. Improved security is "
     "argued on four verifiable grounds: (i) counter-based zero padding with a 64-bit length "
     "binding structurally defeats Merkle–Damgård-style length-extension attacks; (ii) all "
     "round constants are deterministically derived from a standard seed via PRNG extension "
     "and are fully reproducible, ruling out guess-constant or backdoor concerns; (iii) "
     "structural trust is inherited entirely from previously audited primitives, and the "
     "self-designed layer is restricted to parameters/constants/rounds/permutation order, "
     "so that security can be argued compositionally; and (iv) the interplay of multiple "
     "diffusion components (ARX + SPN + bit-planes), combined with the strengthened "
     "variant's permutation re-hashing, raises the cost of structural cryptanalysis. The "
     "implementation is pure TIE with no external dependency; digests are encoded by default "
     "in a purpose-built Base48 alphabet for human transcription. Known-answer vectors "
     "cross-generated with the platform are verified byte-for-byte. Benchmarks on the TIE "
     "self-hosted execution layer show ≈34/22/22/13 MB/s for f/b/r/x on large messages, "
     "matching the intended hierarchy. TSHA1 has been adopted as the fingerprint and "
     "credential-signing hash foundation of the plug-in kernel audit chain.",
     size=12, space_after=6)
p = para("", size=12, indent=False, space_after=10)
r0 = p.add_run("Keywords: ")
_set_font(r0, "宋体", "Times New Roman", 12, italic=True)
for w in ["new design hash", "deterministic composition", "length-extension resistance",
          "multi-diffusion construction", "ARX", "SPN", "strength hierarchy", "Base48"]:
    p.add_run(w + " ")

# ================= 1 引言 =================
heading("1　引言")
para("哈希函数是现代密码体系的地基，其安全性直接决定签名、消息认证、密钥派生与完整性"
     "审计的可靠性。标准算法虽经长期沉淀而高度成熟，仍存在结构性局限：MD5/SHA-1 已出现"
     "可证明的碰撞攻击；SHA-2 的 Merkle–Damgård 结构公开了长度扩展攻击面；SHA-3 虽结构"
     "免疫，但其海绵构造以吞吐换取状态规模，在受限环境中开销不小。与此同时，越来越多"
     "自给自足的平台希望拥有“可自持、可复现、安全性质可明确论证”的自有哈希体系，而非"
     "仅仅封装外部标准实现。TIE 便是一个以自身编译器（tiec）构建的自举编程语言系统："
     "其前端、中端、后端与标准库全部以 TIE 编写，形成“tie 写 tiec、tie 写 tie 库”的闭环。"
     "在向全平台插件化架构演进的过程中，平台需要一个完全由 TIE 自身实现、随自举闭环一致"
     "交付的安全哈希底座，用于插件审计链的完整性指纹、包树根校验与凭证签名对象绑定。")
para("本文提出的 TSHA1（全称 TIE Secure Hash Algorithm 1.0，下文简称 TSHA1）正是面向"
     "“新型、更安全”这一目标设计的。"
     "其**新颖性**体现为确定性组合构造：以经充分公开分析的 BLAKE 型 ARX 轮与 Ascon 型"
     "位切片 SPN 为结构骨架，叠加自主设计的 trit 位平面旁路扩散与 f+b 输出排列组合再算，"
     "构成四档强度梯度；自创层严格限于参数、常量、轮数与排列组合序。其**更强的安全性质**"
     "可归纳为五点：(1) 计数器式纯零填充与 64 位长度绑定在结构上免疫长度扩展攻击；"
     "(2) 常量由“标准种子＋PRNG 扩展”确定性生成、可复现，排除猜测常量与后门注入疑虑；"
     "(3) 结构信任完全继承已审原语，未引入任何未经审计的新结构断言，安全性可组合论证；"
     "(4) ARX、SPN 与位平面三类扩散构件交叠，配合加强档的排列组合再算，整体抬高结构化"
     "攻击的破解成本；(5) 四档梯度使同一族可同时满足快速指纹、复杂强度与签名对象级防护。"
     "trit 位平面扩散在这一构造中扮演扩散构件角色（§3.2），其实现受益于 TIE 语言对平衡"
     "三进制的一等支持，但并非本文主张的主体。")
para("本文组织如下：第 2 节综述相关工作；第 3 节给出 TSHA1 设计与四档结构；第 4 节讨论"
     "安全性质与已知限制；第 5 节报告纯 TIE 实现、向量验证与基准；第 6 节说明其在插件"
     "审计链中的应用；第 7 节总结与展望。")

para("现状与当前存在的问题。就本研究启动时而言：(1) 平台对标准哈希（SHA-2/3、BLAKE2/3）"
     "已有标准库实现，但作为外部标准算法，其常量与参数不体现平台语境，难以满足“自持有、"
     "且随自举闭环逐字节复现”的审计链强需求；(2) 标准算法各自存在结构性局限（长度扩展、"
     "温室化参数、退出审计较难的长期依赖），而评估一个“既有实力又可控”的自有族需要可论证"
     "的安全机制，而非经验式拼装；(3) 平台执行模型（有符号 64 位、表驱动、字符串 {ptr,len} "
     "逐字节语义）对通用算法的移植存在适配成本与验证噪音；(4) 插件化审计链需要“文件级快速"
     "指纹—包级强指纹—签名对象”的分层哈希底座，单一算法难以同时满足成本与强度梯度。")
para("针对上述现状，TSHA1 着力解决以下问题：（1）自持——以纯 TIE 实现四档哈希，零外部"
     "运行时依赖，常量按“标准种子＋PRNG 扩展”可复现（§3.7），并随自举闭环交付（§5.1）；"
     "（2）安全机制可论证——抗长度扩展的结构设计（§3.3）、可复现常量（§3.7）、结构信任"
     "继承已审原语与多扩散构件交叠（§4），使“更安全”不依赖对未验证结构的断言；（3）"
     "档位深度——四档按速度/强度梯度组织，实测 f≈34 > b≈r≈22 > x≈13 MB/s（§5.3），"
     "单调满足审计链 per-file / 包树根 / 签名对象的三级需求（§6）；（4）适配验证——全部"
     "实现遵循 i64 无溢出论证与逐字节模型，探针以跨平台交叉生成的 KAT 逐字节核对，并与"
     "常规回归体系解耦验证（§5.2）。")

# ================= 2 相关工作 =================
heading("2　相关工作")
para("现代杂凑函数的设计沿两条主线演进：(1) ARX（加-旋-异或）路线，以 BLAKE"
     "[3][4] 为代表，其 G 函数将模 2^32 加法、循环旋转与异或组合，轮数较少即可获得良好"
     "雪崩与扩散；BLAKE2（RFC 7693）[3] 与 BLAKE3 [5] 进一步在并行与速度上优化，"
     "BLAKE3 采用二叉树结构支持多核与 XOF 输出。(2) SPN（代换-置换网络）路线，以"
     "Keccak（SHA-3，FIPS 202）[2][11] 的海绵结构与 Ascon（NIST 轻量级加密标准，"
     "Feistel-SPN 混合）[6] 为代表，非线性特征清晰、侧信道设计友好。此外 SHA-2"
     "（FIPS 180-4）[1] 与 SHA-3 均由美国 NIST 标准化，是联邦与现代协议的事实标准。")
para("在杂凑函数的验证与部署侧，已知答案向量（KAT）与测试向量生成器、NIST ACVP"
     "自动化验证、以及常数时间实现审查是通用工程实践。后量子时代 NIST 已发布 ML-KEM"
     "（FIPS 203）[7]、ML-DSA（FIPS 204）[12] 与 SLH-DSA（FIPS 205）[8]，其中 SLH-DSA"
     "以哈希基构建，与本文的“以自有哈希支撑平台”思路一致。TIE 平台的既有安全底座还"
     "包括 SHA-256/SHA-3/Keccak、BLAKE2、BLAKE3、Toom/分基大数（bigint）、Ed25519/X25519"
     "纯语言实现与各类 KDF/MAC 原语，TSHA1 与之在库中并存、互不替代：TSHA1 承担平台自有"
     "标准的、可随自举闭环交付的签名/指纹底座角色。")

# ================= 3 设计 =================
heading("3　TSHA1 设计")

heading("3.1　总体架构与四档定位", size=12)
para("TSHA1 家族采用“同族多档”策略：共享输出编码、验证探针与常量派生框架，但各档以"
     "不同结构骨架权衡速度与强度（表 1）。快速档 tsha1f 与轻量档 tsha1r 满足批量与嵌入式"
     "需求；复杂档 tsha1b 与加强档 tsha1x 为签名、密钥绑定等高强度场景提供纵深。")
add_table(
    ["档位", "输出位长", "结构骨架", "定位"],
    [
        ["tsha1f", "256", "BLAKE-ARX 主体 + T 轨旁路扰动 + 24 基调度", "快速，海量小文件指纹"],
        ["tsha1b", "256", "A 骨架双轨并行（ARX+trit 互转）+ S-盒/SPN 强化", "复杂强度，审计链"],
        ["tsha1x", "256", "f+b 输出多次排列组合再算（NX=6 固定序）", "加强，签名对象/凭证"],
        ["tsha1r", "128", "轻量 SPN（S-盒+旋-异或+轮常量）+ trit 终筛", "嵌入式/超小消息"],
    ],
    "表 1　TSHA1 四档定位")

# 图 1：家族总体架构
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsha1-arch.png")
if os.path.exists(IMG):
    doc.add_picture(IMG, width=Cm(14.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para("图 1　TSHA1 家族总体架构（四档互斥选择；trit 位平面包装层作用于各档 T 轨/终筛）",
         zh="黑体", size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False, space_after=8)

heading("3.2　trit 位平面扩散层（扩散构件）", size=12)
para("TSHA1 以“多扩散构件交叠”作为安全增强的核心手段之一：除 ARX 模加扩散与 SPN 位切片"
     "非线性外，家族引入平衡三进制位平面作为旁路扩散构件。每个 64 位双字装填 32 个 trit，"
     "高 32 位为幅值位平面 M（第 i 位=1 当且仅当第 i 个 trit 非零），低 32 位为符号位平面 N"
     "（第 i 位=1 当且仅当第 i 个 trit 为负），即等价于 (M<<32)|N。由于 M、N 均保持 <2^32，"
     "任何位操作都不进入符号位，全部扩散运算可表达为 &、^、|、<<，避免逐 trit 模 3 的慢点"
     "与条件分支。消息经饱和映射（字节高二位 0→−1、1→0、2/3→+1）注入位平面，为 ARX/SPN "
     "主体之外再叠加一层低开销、非线性的旁路扰动。该构件在 TIE 中的实现直接受益于语言对"
     "平衡三进制的一等支持（−1t/0t/1t 字面量、to_trit/trit_val），但在本文构造中它仅作为"
     "扩散构件之一，与 ARX、SPN 并列；TSHA1 的安全主张不依赖对三进制的结构性创新。")

heading("3.3　tsha1f：B 骨架（快速档）", size=12)
para("tsha1f 由三部分组成：(1) BLAKE-ARX 主体——G 函数与 BLAKE2s 同构，可交叉验证；"
     "(2) T 轨旁路扰动——消息首先经 trit 置换/扰动，打包为位平面后进入 ARX 轮；"
     "(3) 24 基混合调度——每字节取 3 位×3 与 1 trit 构成 0..23 的调度数字参与轮调度。"
     "消息填充采用纯零填充（不含 0x80 与显式长度位），长度由 64 位计数器 t 的两半（t_lo、"
     "t_hi，各 32 位，模 2^64）承载；轮数 12，每轮由 σ 置换与由 24 基 skey 派生的轮"
     "调制 rd 共同驱动。摘要为每字大端字节序、共 8 字 256 位。逐字处理采用 str_byte + len，"
     "因此任意 UTF-8 原始字节序列均可哈希。")

heading("3.4　tsha1b：A 骨架（复杂档）", size=12)
para("tsha1b 采用双轨并行压缩：B 轨运行 ARX 轮（G 函数与 σ 调度），T 轨运行 trit 位平面"
     "扩散（trit 加法/旋转/混洗全部以位平面运算实现），两轨每轮互联互转——B 轨输出分段"
     "展开入 T 轨，T 轨结果经 majority 量化回 B 轨。在此基础上每 3 轮插入一层 SPN 强化："
     "Ascon 型 nibble S-盒（16 项双射）＋旋-异或线性扩散＋轮常量。B 轨轮数为 14，不小于"
     "tsha1f 的 12，为保守强化；S-盒与轮常量由独立种子派生。")

heading("3.5　tsha1x：加强档（f+b 排列组合再算）", size=12)
para("tsha1x 对 tsha1f 与 tsha1b 的输出做多次确定性排列组合再计算：首状态为 "
     "digest_f(msg)‖digest_b(msg)（128 hex 字符），随后迭代 NX=6 轮，每轮对上一状态分别"
     "再作 digest_f 与 digest_b，并依固定排列表 PATT（24 个 pick，行主序 " 
     "u0w0u1w1w2u2w3u3…）选取其 16-hex 四分重新拼接为 64-hex 状态，最终取 256 位。"
     "排列组合次数与顺序全部固化、可复现，显著提高将 f、b 两档级联分解的破解难度。")

heading("3.6　tsha1r：轻量档（128 位，嵌入式）", size=12)
para("tsha1r 面向嵌入式/受限环境：以 128 位速率海绵式吸收、长度绑定与终筛轮输出 128 位。"
     "非线性层为 SPN 型（nibble S-盒 → 旋-异或线性扩散 → 轮常量 → trit 扰动），末块计算"
     " trit 位平面并带入终筛轮，使短消息亦激活 trit 层。其单次固定开销四档中最低，适合"
     "海量小对象的快速指纹（16 字节 → Base48 23 字符）。")

heading("3.7　常量派生", size=12)
para("为避免任何猜测常量与实现后门争议，全部轮常量（IV、σ 置换、S-盒、轮常量）按"
     "“标准种子＋PRNG 扩展固化”方式生成：扩展流为 SHA-256(SEED ‖ u64be(k))（k=0,1,2,…）"
     "计数器流，依序取字节填充。各档种子形如 “TSHA1-2026-<档>-<位长>-v1”（如 "
     "SEED_F=“TSHA1-2026-f-256-v1”、SEED_R=“TSHA1-2026-r-128-v1”）。该过程可复现"
     "（tests/tsha_probe/gen_vectors.py），且 IV 与 BLAKE2 的 6a09e667… 有意区分。")

heading("3.8　Base48 输出编码", size=12)
para("默认输出使用自行设计的 Base48 编码（命名空间 b48）：字符台为 48 符号连续集合"
     "“0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKL”（10 数字＋26 小写＋12 大写，"
     "顺序即数值 0..47）。n 字节（8n 位）到 m 个 Base48 字符的换算为 m=ceil(8n/log2(48))，"
     "取整采用精确有理近似 m=(n×1432407)/1000000+1；编码实现为 base-256 字节数组的反复"
     "长除 48（进位中间量 <2^13，无溢出），解码为反复“×48+digit”（同样无溢出），并采用"
     "长度保留设计使 encode/decode 互为精确逆（前导零字节完整往返）。256 位摘要输出 46 字符、"
     "128 位输出 23 字符，比 hex（64/32）短约 28%，便于审计链 ID 与凭证的人类抄写校验。"
     "同时保留 _hex 变体以满足十六进制生态需求。字符台用户选定，集合内含 0↔o、1↔l/I "
     "视觉相近对，属换取字符连续性的取舍，在实现中明确注释说明。")

# ================= 4 安全性质 =================
heading("4　安全性质与论证")
para("TSHA1“更安全”的主张建立在四类可论证机制上，而非经验式声明：(a) 结构层面——"
     "抗长度扩展（计数器式纯零填充＋64 位长度绑定，§3.3）与抗冲击面收窄（状态与输出"
     "解耦）；(b) 构造层面——多扩散构件交叠（ARX 模加＋SPN 位切片＋trit 位平面旁路）"
     "通过三个异源扩散通道交织，显著抬高差分/代数类结构化攻击所需的多轮追踪复杂度；"
     "加强档 x 的 f+b 排列组合再算（§3.5）进一步将攻击者对单结构的利用性切割；(c) "
     "信任层面——结构信任完全继承已审原语（BLAKE2 G 函数、Ascon S-盒/线性层），自创层"
     "严格限于参数/常量/轮数/排列组合序，未引入任何未经审计的新结构断言，安全性可随"
     "组合逐一论证；(d) 工程层面——常量种子化可复现（§3.7）、实现纯 TIE 可自举交付"
     "（§5.1）、KAT 逐字节核对（§5.2），从源头排除后门注入与实现漂移。")
para("以下逐点说明安全边界与已知限制：(1) 结构信任边界——自创层未宣称新结构贡献，"
     "属确定性组合，家族在说明文档中以 security-notes 声明**未经独立审计**，正式部署前"
     "应由第三方密码学审计复核；(2) 雪崩与差分——ARX 提供逐位模加扩散、SPN 提供字节级"
     "非线性、trit 位平面提供旁路扰动，向量探针判定实现与生成器一致，但一致性验证不等同"
     "于统计雪崩检验，后续将补做严格的差分/雪崩统计测试；(3) 长度扩展免疫——计数器式"
     "填充（f/b）与速率吸收＋长度绑定（r）在结构上杜绝 Merkle–Damgård 型长度扩展；"
     "(4) 常数时间——TIE 数值执行语义不提供硬件级常数时间保证（无 volatile、无恒定时间"
     "指令特判），位平面打包与 24 基调度引入的分支循环在原理上允许时间侧信道差异；"
     "TSHA1 当前用于完整性指纹与签名对象哈希，不直接处理机密数据；若后续用于常时间敏感"
     "场景，须在平台层落实常数时间保证并复核；(5) 输出编码——Base48 默认输出（§3.8）"
     "不改变内部 256/128 位摘要字节，decode(b48) 与 hex 逐字节一致。")

# ================= 5 实现与评估 =================
heading("5　实现与评估")

heading("5.1　纯 TIE 实现", size=12)
para("全部算法以 TIE 编写（std/tsha1.tie、std/base48.tie，命名空间 tsha/b48），仅依赖"
     "语言底座原语（str_len/str_char/table 动态表/i64 位运算），零外部运行时依赖；字符串"
     "按 {ptr,len} 二进制安全模型逐字节读写，支持含 NUL 在内的任意字节输入。验证探针"
     "（tests/tsha_probe/）以编译-运行方式断言四档全部 KAT 与 hex↔Base48 往返一致，"
     "编译零错误；探针独立于常规回归（regress-s21）运行。")

heading("5.2　已知答案向量（KAT）", size=12)
add_table(
    ["输入", "tsha1f（64 hex）", "tsha1r（32 hex）"],
    [
        ["空串 \"\"", "049a7e45 9a4558bc ed881efe f7b15a0f 29a306bd 95cd8986 45df15d9 895fcd9e", "1d41e39e ce695096 448cf494 7429d6cd"],
        ["\"abc\"", "2c3fe6f9 73eb8ea1 50c24d8c 5a20ea38 f0a4d559 0c58b868 806dacd3 2eda3cd4", "2539601d 26712894 58b7c068 3324edd6"],
        ["1000×'a'", "9f74677d 24005bc3 07237035 d0ebacad 5ca178b8 378938f7 b40c7976 f1611336", "—"],
    ],
    "表 2　TSHA1 已知答案向量（KAT，与平台生成器交叉核对）")

heading("5.3　性能基准", size=12)
para("基准方法：计时原语为秒级粒度，故采用“目标时长循环”——对每个（档位，消息长度）"
     "组合重复哈希至累计≥2 s，以总数据量/耗时折算吞吐；消息构造使用 StringBuilder 原地"
     "追加（规避字符串 + 的 O(n²) 拼接陷阱——该陷阱与治理详见语言文档）。环境为 TIE 自写"
     "编译器前端驱动、LLVM 后端生成 x86_64 可执行文件的执行层。实测大消息稳态吞吐与短消息"
     "哈希率见表 3。")
add_table(
    ["档位", "2 KB（hash/s）", "2 KB（MB/s）", "32 KB（hash/s）", "512 KB（hash/s）", "512 KB（MB/s）"],
    [
        ["tsha1f", "3935", "7", "1009", "69", "34"],
        ["tsha1b", "6578", "12", "648", "44", "22"],
        ["tsha1x", "2341", "4", "383", "26", "13"],
        ["tsha1r", "8718", "17", "702", "45", "22"],
    ],
    "表 3　TSHA1 四档基准实测（目标时长 2s 采样，短消息档含秒级量化误差）")
para("观察：(1) 大消息稳态吞吐排序 f≈34 > b≈22 ≈ r≈22 > x≈13 MB/s，与设计档位一致——"
     "快速档最快，加强档以约 2.6× 时间代价提供最高抗破解强度；(2) 短消息（2 KB）单次固定"
     "开销排序与之不同：r 最低（8718 hash/s），b 次之，f 的 B 骨架单次固定开销反而高于 b"
     "——因此海量小文件指纹场景宜选 r 或 b，长消息批量场景选 f；(3) 绝对吞吐受 TIE 自写"
     "编译器/IR 执行层的软件实现约束（无 SIMD），较原生 C（BLAKE2s 可达 GB/s 级）低 2~3 "
     "个数量级，但对审计链 per-file 指纹与低频签名对象场景完全充足。")

# ================= 6 应用 =================
heading("6　应用：插件化内核审计链")
para("TIE 全平台插件化内核以“核心微内核（机制）+注册表+审计器+加载器”为骨架，所加载"
     "插件（包）须通过八级审计链：①指纹树重算→②包内验签→③公钥指纹锚定→④IR 版本→"
     "⑤id/version→⑥字段白名单→⑦依赖解析→⑧注册仲裁。其中指纹模型采用 TSHA1："
     "单文件级指纹用快速档 tsha1f，整包树根（即签名对象）用加强档 tsha1x；凭证区的"
     " Ed25519 纯 TIE 实现（RFC 8032 向量绿）对 tsha1x 树根签名。该分层与基准实测吻合："
     "文件级批量校验取最实惠的快速档，跨包完整性/冒名抵御取最高强度档，二者速度差约 2.6×"
     "构成清晰的成本梯度。")

# ================= 7 结论 =================
heading("7　结论与展望")
para("本文提出了 TSHA1——一个完全以自举语言 TIE 实现的**新型安全杂凑函数家族**。其"
     "新颖性在于确定性组合构造：以经公开分析的 BLAKE 型 ARX 与 Ascon 型 SPN 为结构骨架，"
     "叠加 trit 位平面旁路扩散与 f+b 排列组合再算，形成四档速度/强度梯度；更强的安全性质"
     "来自四类可论证机制——结构层面抗长度扩展、构造层面多扩散构件交叠、信任层面结构继承"
     "已审原语、工程层面常量可复现与纯 TIE 自举交付。实现为纯 TIE、零外部依赖，探针逐字节"
     "核对 KAT、字节边界全覆盖；基准结果与档位设计一致，并已投入插件化内核的指纹与凭证"
     "签名底座。后续工作包括：严格的差分/雪崩统计检验与独立第三方安全审计；将位平面扩散"
     "与既有 Keccak/Ascon 置换统一为可配置扩散内核以降低维护面；在编译器执行层实现字符串"
     "就地追加等语言级性能优化后重新量化吞吐；以及将 TSHA1 与后量子签名（SLH-DSA 纯 TIE "
     "前沿）组合为审计链的长期凭证方案。")

# ================= 参考文献 =================
heading("参考文献")
refs = [
    "NIST. FIPS 180-4: Secure Hash Standard (SHA-2)[S]. Gaithersburg: NIST, 2015.",
    "NIST. FIPS 202: SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions[S]. Gaithersburg: NIST, 2015.",
    "Saarinen M J O, Aumasson J P. RFC 7693: The BLAKE2 Cryptographic Hash and Message Authentication Code (MAC)[S]. IETF, 2015.",
    "Aumasson J P, Neves S, Wilcox-O'Hearn Z, Winnerlein C. BLAKE2: Simpler, Smaller, Fast as MD5[C]// ACNS 2013, LNCS 7954. Springer, 2013: 119-135.",
    "O'Connor J P, Aumasson J P, Neves S, Wilcox-O'Hearn Z. BLAKE3: One Function, Fast Everywhere[R/OL]. 2020. https://github.com/BLAKE3-team/BLAKE3.",
    "Dobraunig C, Eichlseder M, Mendel F, Schläffer M. Ascon v1.2: Lightweight Authenticated Encryption and Hashing[R]. NIST Lightweight Cryptography Finalist, 2021.",
    "NIST. FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)[S]. Gaithersburg: NIST, 2024.",
    "NIST. FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)[S]. Gaithersburg: NIST, 2024.",
    "Bernstein D J. Curve25519: New Diffie-Hellman Speed Records[C]// PKC 2006, LNCS 3958. Springer, 2006: 207-228.",
    "Josefsson S, Liusvaara I. RFC 8032: Edwards-Curve Digital Signature Algorithm (EdDSA)[S]. IETF, 2017.",
    "Bertoni G, Daemen J, Peeters M, Van Assche G. The Keccak Reference[R]. Keccak Team, 2011.",
    "NIST. FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)[S]. Gaithersburg: NIST, 2024.",
    "Krawczyk H, Bellare M, Canetti R. RFC 2104: HMAC: Keyed-Hashing for Message Authentication[S]. IETF, 1997.",
    "TIE Language Project. TIE: A Self-Hosting Programming Language — AGENTS.md, Architecture Notes and Design Specs[R/OL]. 2026. tie-lang.",
]
for i, r in enumerate(refs):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0.9)
    pf.first_line_indent = Cm(-0.9)   # 悬挂缩进
    pf.space_after = Pt(4)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.3
    run = p.add_run("[%d] %s" % (i + 1, r))
    _set_font(run, "宋体", "Times New Roman", 10.5)

doc.save(OUT)
print("saved:", OUT)