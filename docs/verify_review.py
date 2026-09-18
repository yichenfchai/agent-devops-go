# -*- coding: utf-8 -*-
"""文献综述引用完整性 + 格式校验。
从生成的 docx 直接读取校验（不依赖 py 源），确保产物本身正确。
"""
import re, os, sys
from collections import Counter
import docx
from docx.shared import Pt

PATH = r"C:\Users\tyc\Desktop\《毕业设计（论文）》文献综述-填写版.docx"
d = docx.Document(PATH)

# 分离正文与参考文献
paras = [p for p in d.paragraphs]
ref_start = None
for i, p in enumerate(paras):
    if p.text.strip() == "参考文献":
        ref_start = i; break

body_txt = "\n".join(p.text for p in paras[:ref_start])
ref_txt = "\n".join(p.text for p in paras[ref_start + 1:])

# 1) 引用编号
cited = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", body_txt)))
listed = [int(x) for x in re.findall(r"^\[(\d+)\]", ref_txt, re.M)]

print("=" * 64)
print("【引用完整性】")
print("  正文引用编号:", cited)
print("  文献表编号:  ", listed)
dangling = [n for n in cited if n not in listed]
uncited = [n for n in listed if n not in cited]
print("  悬空引用(正文引了但表中无):", dangling if dangling else "无 ✓")
print("  未被引用(表中有但正文未引):", uncited if uncited else "无 ✓")
print("  编号连续 1..%d:" % len(listed), "是 ✓" if listed == list(range(1, len(listed) + 1)) else "否 ✗ %s" % listed)

# 2) 每条文献被引次数
print("\n【每条文献被引次数】")
zero = []
for n in listed:
    cnt = len(re.findall(r"\[%d\]" % n, body_txt))
    if cnt == 0:
        zero.append(n)
print("  被引 0 次的文献:", zero if zero else "无 ✓（%d 条全部在正文被引用）" % len(listed))

# 3) 参考文献著录完整性
print("\n【参考文献著录检查】")
bad = []
for line in ref_txt.split("\n"):
    line = line.strip()
    if not line:
        continue
    m = re.match(r"^\[(\d+)\]\s*(.+)$", line)
    if not m:
        bad.append(("格式异常", line[:40])); continue
    body = m.group(2)
    if not re.search(r"\[(M|J|C|D|R|EB/OL)\]", body):
        bad.append(("缺文献类型标识", line[:44]))
print("  著录异常:", bad if bad else "无 ✓（全部含 [M]/[J]/[C]/[D]/[R]/[EB/OL] 标识）")

# 4) 格式核验（抽样）
print("\n【格式抽样核验】")
h1 = next(p for p in paras if p.text.strip().startswith("1 引言"))
r0 = h1.runs[0]
print("  一级标题 '1 引言': 字体=%s 字号=%s 加粗=%s" % (
    r0.font.name, r0.font.size.pt if r0.font.size else None, r0.font.bold))

h2 = next(p for p in paras if p.text.strip().startswith("2.1"))
r0 = h2.runs[0]
print("  二级标题 '2.1…':   字号=%s 加粗=%s" % (
    r0.font.size.pt if r0.font.size else None, r0.font.bold))

# 找一段真正的正文（在 "1 引言" 与 "参考文献" 之间，且非标题）
i1 = next(i for i, p in enumerate(paras) if p.text.strip() == "1 引言")
ir = next(i for i, p in enumerate(paras) if p.text.strip() == "参考文献")
sample = next(p for p in paras[i1 + 1:ir] if len(p.text) > 120)
pf = sample.paragraph_format
print("  正文段落: 行距规则=%s 行距=%s磅 首行缩进=%s twips" % (
    pf.line_spacing_rule,
    pf.line_spacing.pt if pf.line_spacing else None,
    pf.first_line_indent.twips if pf.first_line_indent else None))
print("  正文字号: %s pt (小四=12)" % (sample.runs[0].font.size.pt if sample.runs[0].font.size else None))

refp = next(p for p in paras[ref_start + 1:] if p.text.strip().startswith("[1]"))
print("  参考文献条目: 字号=%s 行距=%s磅" % (
    refp.runs[0].font.size.pt if refp.runs[0].font.size else None,
    refp.paragraph_format.line_spacing.pt if refp.paragraph_format.line_spacing else None))

# 5) 中文字体核验（eastAsia）
from docx.oxml.ns import qn
def ea(run):
    rf = run._element.find(qn("w:rPr"))
    if rf is None: return None
    f = rf.find(qn("w:rFonts"))
    return f.get(qn("w:eastAsia")) if f is not None else None
cn_run = next((r for r in sample.runs if re.search(r"[\u4e00-\u9fff]", r.text)), None)
en_run = next((r for r in sample.runs if re.search(r"[A-Za-z]", r.text)), None)
print("  中文 run eastAsia 字体:", ea(cn_run) if cn_run else "无中文")
print("  英文 run ascii 字体:   ", en_run.font.name if en_run else "无英文")

# 6) 引言中关于文献构成的自我陈述，须与实际引用一致（防止自我陈述失真）
print("\n【文献构成陈述核验】")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 直接从文献表文本重建统计
_reflines = [l.strip() for l in ref_txt.split("\n") if l.strip().startswith("[")]
_tc = Counter()
for l in _reflines:
    m = re.search(r"\[(M|J|C|D|R|EB/OL)\]", l)
    if m: _tc[m.group(1)] += 1
NAME = {"M": ("专著","部"), "J": ("期刊论文","篇"), "C": ("会议论文","篇"),
        "D": ("学位论文","篇"), "R": ("技术报告","份"), "EB/OL": ("电子资源","项")}
ORDER = ["M","J","C","D","R","EB/OL"]
_parts = "、".join("%s %d %s" % (NAME[t][0], _tc[t], NAME[t][1]) for t in ORDER if _tc.get(t))
_cn = sum(1 for l in _reflines if re.search(r"[\u4e00-\u9fff]", l[:14]))
_yrs = [max(int(y) for y in re.findall(r"(19\d\d|20\d\d)", l)) for l in _reflines if re.findall(r"(19\d\d|20\d\d)", l)]
expect = "共 %d 篇，其中%s；中文文献 %d 篇，时间跨度自 %d 年至 %d 年" % (
    len(_reflines), _parts, _cn, min(_yrs), max(_yrs))
print("  实际统计:", expect)
_ok = expect.split("，其中")[1] in body_txt
print("  正文陈述与实际一致:", "是 ✓" if _ok else "否 ✗ 需修正")
print("  类型分布:", dict(_tc), "| 类型标识缺失:", len(_reflines) - sum(_tc.values()))

# 7) 统计
print("\n【统计】")
print("  正文字数(不含文献):", len(body_txt.replace("\n", "").replace(" ", "")))
print("  参考文献条数:", len(listed))
print("  总段落数:", len(paras))
