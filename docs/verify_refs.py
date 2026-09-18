# -*- coding: utf-8 -*-
"""开题报告引用完整性校验（键引用版）。
交叉核对：正文 [[key]] 引用 ↔ REF_KEYS 声明 ↔ refs.REFDB 著录，
确保无悬空引用、无未登记键、无声明未用/用了未声明，且编号连续。
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proposal_content import TITLE, S1, S2, S3
from proposal_content2 import S4_PLAN, S4_SCHED, S4_RESULT, REF_KEYS
from refs import REFDB

def blocks_text(blocks):
    out = []
    for kind, val in blocks:
        if kind == "t":
            for row in val[1:]:
                out.append(" ".join(row))
        else:
            out.append(val)
    return "\n".join(out)

body = "\n".join(blocks_text(b) for b in
                 [S1, S2, S3, S4_PLAN, S4_SCHED, S4_RESULT])

KEY_RE = re.compile(r"\[\[([A-Za-z0-9_]+)\]\]")
used_ordered = []
for m in KEY_RE.finditer(body):
    k = m.group(1)
    if k not in used_ordered:
        used_ordered.append(k)

print("=" * 64)
print("【1】正文引用键数:", len(used_ordered))
print("【2】REF_KEYS 声明数:", len(REF_KEYS))
print("【3】refs.REFDB 文献库总数:", len(REFDB))

# 未登记的键（正文引用但 REFDB 没有）
unreg = [k for k in used_ordered if k not in REFDB]
print("\n【未登记键】(正文引用但库中无著录):", unreg or "无 ✓")

# 声明未用 / 用了未声明
declared = set(REF_KEYS)
used = set(used_ordered)
print("【声明但未在正文引用】:", sorted(declared - used) or "无 ✓")
print("【正文引用但未声明】:", sorted(used - declared) or "无 ✓")

# REF_KEYS 内部无重复、全部在 REFDB
dup = [k for k in set(REF_KEYS) if REF_KEYS.count(k) > 1]
notdb = [k for k in REF_KEYS if k not in REFDB]
print("【REF_KEYS 重复项】:", dup or "无 ✓")
print("【REF_KEYS 中缺著录】:", notdb or "无 ✓")

# 模拟顺序编码制编号，检查是否连续 1..N
num = {}
for k in used_ordered:
    num[k] = len(num) + 1
print("\n【顺序编码】编号 1..%d %s" % (
    len(num), "连续 ✓" if sorted(num.values()) == list(range(1, len(num)+1)) else "✗"))

# 每条被引次数
print("\n【每条文献被引次数】")
zero = []
for k in used_ordered:
    cnt = len(re.findall(r"\[\[%s\]\]" % re.escape(k), body))
    if cnt == 0:
        zero.append(k)
print("  被引 0 次:", zero or "无 ✓（全部被引用）")

# 残留裸编号（不该再有 [数字] 这种手写编号）
bare = re.findall(r"(?<!\[)\[\d{1,3}\](?!\])", body)
print("【残留手写编号 [n]】:", bare or "无 ✓")

# 著录类型标识
print("\n【著录类型标识检查】")
bad = []
for k in used_ordered:
    r = REFDB[k]
    if not re.search(r"\[(M|J|C|D|R|EB/OL)\]", r):
        bad.append((k, r[:44]))
print("  缺类型标识:", bad or "无 ✓")

# 正文数字主张（供人工溯源）
print("\n【正文数字主张（需可溯源）】")
for n in re.findall(r"[^。；\n]*\d[\d.,%]*[^。；\n]*", body):
    n = n.strip()
    if re.search(r"20\d\d[.\-]", n) or re.match(r"^\d\.\d", n) or re.match(r"^[①-⑳]", n):
        continue
    if any(x in n for x in ["GB", "OpenAPI", "Go ", "SSH", "SSH", "token", "SQL"]):
        continue
    if len(n) > 6:
        print("  ·", n[:76])
