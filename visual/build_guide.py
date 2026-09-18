# -*- coding: utf-8 -*-
"""生成 guide.html —— 全流程原理详解（学习材料版）。

    python build_guide.py

内容与模板分离：
    guide_shell.py     CSS / JS / 渲染函数
    guide_content1.py  站点 ①–⑧
    guide_content2.py  站点 ⑨–⑮ + 三条主线
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guide_shell import CSS, JS, render_station          # noqa: E402
from guide_content1 import P1                            # noqa: E402
from guide_content2 import P2, MAINLINES                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "guide.html")

STATIONS = P1 + P2

# 全流程动画的节点顺序（对应站点 id）与解说词
PIPE = [
    ("s1",  "触发",       "git push → GitHub 发出 webhook POST"),
    ("s2",  "入队",       "验签 → 限长 → 写 queued 记录 → 立刻回 202"),
    ("s3",  "调度",       "原子认领任务 → 占一个车位 → 开 goroutine"),
    ("s4",  "检出",       "Go 侧 git fetch <sha> --depth=1（凭据不进容器）"),
    ("s5",  "检测",       "扫标记文件 → 推断类型 → 生成 Pipeline 快照"),
    ("s6",  "构建",       "容器内 install → build，退出码判定成败"),
    ("s7",  "日志",       "fan-out → 环形缓冲 + 批量落库 + SSE 实时推送"),
    ("s8",  "产物",       "docker commit → web-api:a3f9c21（不可变 tag）"),
    ("s9",  "部署",       "SSH（校验 Host Key）→ docker-compose up -d"),
    ("s10", "健康检查",   "GET /healthz 连续 3 次 200 → deployed；失败 → 自动回滚"),
    ("s11", "状态机",     "9 个状态、只允许沿边迁移、每次迁移写审计"),
    ("s12", "诊断",       "LOA 策略引擎 → analyzer → 证据链诊断 → 人做决策"),
]

GROUPS = [
    ("接入与调度", ["s1", "s2", "s3"]),
    ("构建执行", ["s4", "s5", "s6", "s7", "s8"]),
    ("部署与状态", ["s9", "s10", "s11"]),
    ("智能诊断", ["s12"]),
    ("工程实现", ["s13", "s14", "s15"]),
]

BADGE_SHORT = {"done": '<span class="st" style="color:#7ee2b8">●</span>',
               "design": '<span class="st" style="color:#e5c07b">○</span>',
               "mixed": '<span class="st" style="color:#8fc0ff">◐</span>'}


def build_nav():
    by_id = {s["id"]: s for s in STATIONS}
    out = []
    for label, ids in GROUPS:
        links = []
        for i in ids:
            s = by_id[i]
            links.append('<a href="#%s" data-t="%s"><span class="n">%s</span>'
                         '<span>%s</span>%s</a>'
                         % (i, i, s["num"], s["title"].split("：")[0], BADGE_SHORT[s["status"]]))
        out.append('<div class="navgrp"><div class="lbl">%s</div><div class="nav">%s</div></div>'
                   % (label, "".join(links)))
    return "".join(out)


def build_pipeline():
    nodes = "".join(
        '<a class="pnode" data-goto="%s" data-msg="%s">'
        '<div class="pn">%s</div><div class="pt">%s</div></a>'
        % (sid, msg.replace('"', "&quot;"), sid.upper().replace("S", ""), title)
        for sid, title, msg in PIPE)
    return """
<div class="pipeline">
  <h2>一次 push 的完整旅程</h2>
  <p class="sub">点「播放」看整条链路走完；勾选「模拟构建失败」会在第 ⑥ 步中断并转入诊断。
     点任意节点直接跳到该站的详细讲解。</p>
  <div class="prow">%s</div>
  <div class="pctl">
    <button id="pbtn">▶ 播放全流程</button>
    <label><input type="checkbox" id="chk-fail"> 模拟构建失败（走诊断路径）</label>
    <span class="msg" id="pmsg">待播放 · 共 %d 站</span>
  </div>
</div>""" % (nodes, len(PIPE))


def build_mainlines():
    cards = "".join(
        '<div class="ml"><h3>%s</h3><pre>%s</pre><p>%s</p></div>'
        % (m["title"], m["pre"], m["body"]) for m in MAINLINES)
    return ('<div class="mainlines">%s</div>' % cards)


def build():
    n_done = sum(1 for s in STATIONS if s["status"] == "done")
    n_plan = sum(1 for s in STATIONS if s["status"] == "design")
    n_mix = sum(1 for s in STATIONS if s["status"] == "mixed")
    html = io.StringIO()
    w = html.write
    w("<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n")
    w("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n")
    w("<title>GoPulse CI · 全流程原理详解</title>\n")
    w("<style>%s</style>\n</head>\n<body>\n" % CSS)
    w('<div class="shell">\n')

    # ---- 侧栏 ----
    w('<aside class="side"><h2>GoPulse CI</h2>'
      '<p class="tag">全流程原理详解 · 学习材料</p>'
      '<input id="q" type="search" placeholder="搜索章节…" aria-label="搜索章节">'
      '%s</aside>\n' % build_nav())

    # ---- 主体 ----
    w('<main class="main">\n')
    w('<header class="top"><h1>从 git push 到自动部署：全流程原理详解</h1>'
      '<p class="lede">15 个站点，每站按「发生了什么 → 小白类比 → 技术细节 → 踩过的坑」四层展开。'
      '写给自己复习用，也可以直接拿去给同学讲。'
      '<strong>注意每站右上角的实现状态标记</strong> —— 标「后端待实现」的部分是<em>设计原理</em>，'
      '不是已运行的代码。</p>'
      '<div class="legend">'
      '<span class="chip done"><b>%d</b> 站前端已实现</span>'
      '<span class="chip"><b>%d</b> 站前后端都有（前端 ✅ / 后端 ⬜）</span>'
      '<span class="chip plan"><b>%d</b> 站后端待实现（仅有设计）</span>'
      '<span class="chip">共 15 站 · 含代码与流程图</span>'
      '</div></header>\n' % (n_done, n_mix, n_plan))

    w('<div class="prog"><span>阅读进度</span><div class="bar"><i id="prog-fill"></i></div>'
      '<span id="prog-pct">0%</span><button id="btn-fold">全部折叠</button></div>\n')

    w(build_pipeline())

    for s in STATIONS:
        w(render_station(s))
        w("\n")

    w('<h2 style="font-size:18px;margin:38px 0 14px">归纳：三条贯穿全局的设计主线</h2>')
    w(build_mainlines())

    w('<footer>GoPulse CI · 面向小型团队的轻量 CI/CD · 毕业设计学习材料<br>'
      '配套文档：ARCHITECTURE.md（架构设计）· HANDOVER.md（后端交接）· '
      'TODO.md（里程碑）· DEPENDENCIES.md（依赖选型）· openapi.yaml（API 契约）<br>'
      '演示用交互可视化见同目录 index.html</footer>\n')
    w('</main>\n</div>\n')
    w('<button class="top-link" id="totop" aria-label="回到顶部">↑</button>\n')
    w("<script>%s</script>\n</body>\n</html>\n" % JS)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html.getvalue())
    print("已生成 %s（%d bytes）" % (OUT, os.path.getsize(OUT)))
    print("站点数：%d（前端已实现 %d / 混合 %d / 后端待实现 %d）"
          % (len(STATIONS), n_done, n_mix, n_plan))


if __name__ == "__main__":
    build()
