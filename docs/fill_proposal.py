# -*- coding: utf-8 -*-
"""把开题报告内容填入学院模板。
格式要求（模板注明）：中文宋体 / 英文 Times New Roman / 五号(10.5pt) / 22磅行距。
"""
import copy, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_LINE_SPACING
from proposal_content import TITLE, S1, S2, S3
from proposal_content2 import S4_PLAN, S4_SCHED, S4_RESULT, REF_KEYS
from refs import REFDB

TPL = r"C:\Users\tyc\Desktop\毕业设计（论文）材料模板\《毕业设计（论文）》开题报告.docx"
OUT = r"C:\Users\tyc\Desktop\《毕业设计（论文）》开题报告-填写版.docx"

KEY_RE = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")


def blocks_to_text(blocks):
    """把结构化块拍平成文本，用于扫描引用键的出现顺序。"""
    out = []
    for kind, val in blocks:
        if kind == "t":
            for row in val[1:]:
                out.append(" ".join(row))
        else:
            out.append(val)
    return "\n".join(out)


def build_numbering(blocks):
    """GB/T 7714 顺序编码制：按正文首次出现顺序给键编号。"""
    text = blocks_to_text(blocks)
    num = {}
    for m in KEY_RE.finditer(text):
        k = m.group(1)
        if k not in REFDB:
            raise KeyError("未登记的文献键: %s" % k)
        if k not in num:
            num[k] = len(num) + 1
    return num


def sub_keys(s, num):
    return KEY_RE.sub(lambda m: "[%d]" % num[m.group(1)], s)


ALL_BLOCKS = S1 + S2 + S3 + S4_PLAN + S4_SCHED + S4_RESULT
NUM = build_numbering(ALL_BLOCKS)

# 校验：REF_KEYS 声明与正文实际引用必须一致（不允许列未引用的文献）
used = set(NUM)
declared = set(REF_KEYS)
if declared - used:
    raise AssertionError("REF_KEYS 声明了但正文未引用: %s" % sorted(declared - used))
if used - declared:
    raise AssertionError("正文引用了但 REF_KEYS 未声明: %s" % sorted(used - declared))

# 参考文献表按编号顺序生成
REFS = [REFDB[k] for k in sorted(NUM, key=lambda x: NUM[x])]
print("引用文献 %d 条，编号 1..%d" % (len(REFS), len(REFS)))


def set_run(run, bold=False, size=10.5):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "宋体")


def para_fmt(p, first_indent=True):
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(22)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if first_indent:
        pf.first_line_indent = Pt(21)   # 五号字两字符


def clear_cell(cell):
    # 保留第一个段落，其余删除
    tc = cell._tc
    for p in cell.paragraphs[1:]:
        tc.remove(p._element)
    p0 = cell.paragraphs[0]
    for r in list(p0.runs):
        r._element.getparent().remove(r._element)
    return p0


def add_para(cell, text, bold=False, indent=True, size=10.5):
    p = cell.add_paragraph()
    r = p.add_run(text)
    set_run(r, bold=bold, size=size)
    para_fmt(p, first_indent=indent)
    return p


def fill_cell(cell, blocks, numbered_prefix=None):
    """blocks: list of (kind, text) 或 ('t', rows)；text 中的 [[key]] 自动替换为 [n]"""
    p0 = clear_cell(cell)
    first = True
    idx = 0
    for kind, text in blocks:
        if kind == "t":
            # 进度表以文本行呈现（模板单元格内嵌表格兼容性差）
            rows = text
            header = rows[0]
            for row in rows[1:]:
                idx += 1
                line = f"{row[0]}（{row[1]}）：{row[2]}。成果：{row[3]}。"
                line = sub_keys(line, NUM)
                if first:
                    r = p0.add_run(line); set_run(r); para_fmt(p0); first = False
                else:
                    add_para(cell, line)
            continue
        text = sub_keys(text, NUM)
        idx += 1
        if kind == "h":
            if first:
                r = p0.add_run(text); set_run(r, bold=True); para_fmt(p0, first_indent=False); first = False
            else:
                add_para(cell, text, bold=True, indent=False)
        else:  # p / b
            if first:
                r = p0.add_run(text); set_run(r); para_fmt(p0); first = False
            else:
                add_para(cell, text, indent=(kind == "p"))


doc = docx.Document(TPL)

# ── 封面：题目 ──
for p in doc.paragraphs:
    if p.text.strip().startswith("题目"):
        # 保留“题目:”前缀，在其后 run 里写入
        for r in p.runs:
            if "题目" in r.text:
                r.text = "题目:  " + TITLE
                set_run(r, bold=False, size=14)
                break
        else:
            r = p.add_run("  " + TITLE); set_run(r, size=14)
        # 清掉后面的空白 run
        break

tb = doc.tables[0]
rows = tb.rows

# 行1 = 第1栏内容（原为格式说明，替换）
fill_cell(rows[1].cells[0], S1)
# 行3 = 第2栏
fill_cell(rows[3].cells[0], S2)
# 行5 = 第3栏
fill_cell(rows[5].cells[0], S3)
# 行7 = 第4栏（方案+进度+成果）
fill_cell(rows[7].cells[0], S4_PLAN + S4_SCHED + S4_RESULT)
# 行9 = 参考文献
ref_blocks = [("p", f"[{i+1}] {r}") for i, r in enumerate(REFS)]
fill_cell(rows[9].cells[0], ref_blocks)

doc.save(OUT)
print("saved:", OUT)
