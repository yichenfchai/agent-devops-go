# -*- coding: utf-8 -*-
"""部署形态可视化 · 外壳：CSS / JS / 渲染函数（与 guide.html 同一套设计令牌）"""
import html as _h

# ---------- 设计令牌（沿用 visual/ 既有配色语义） ----------
CSS = """
:root{
  --bg:#121316; --panel:#1f1f23; --panel2:#26282d; --hover:#292a2d;
  --line:#2b2d30; --line2:#393b40;
  --tx:#e2e2e6; --tx2:#8c8f99; --tx3:#555861;
  --blue:#b1c5ff; --green:#87d894; --red:#ffb4ab; --orange:#ffb77c; --purple:#e8b3ff;
  --mono:'JetBrains Mono','Cascadia Code',Consolas,monospace;
  --ui:'Geist','Segoe UI','Microsoft YaHei',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--tx);font-family:var(--ui);font-size:14px;line-height:1.65}
a{color:var(--blue);text-decoration:none}
::selection{background:#3a4a7a}

/* 布局：左侧固定导航 + 主区 */
#side{position:fixed;left:0;top:0;bottom:0;width:216px;background:var(--panel);
  border-right:1px solid var(--line);padding:18px 0;overflow-y:auto;z-index:10}
#side h1{font-size:15px;padding:0 18px 4px;letter-spacing:.5px}
#side .sub{font-size:11px;color:var(--tx2);padding:0 18px 14px;font-family:var(--mono)}
#side a{display:block;padding:7px 18px;color:var(--tx2);font-size:13px;border-left:2px solid transparent}
#side a:hover{color:var(--tx);background:var(--hover)}
#side a.on{color:var(--blue);border-left-color:var(--blue);background:#232a3d}
#side .grp{font-size:11px;color:var(--tx3);padding:12px 18px 4px;letter-spacing:1px}
#main{margin-left:216px;padding:28px 36px 80px;max-width:1180px}

/* 通用块 */
section{margin-bottom:52px;scroll-margin-top:16px}
h2{font-size:20px;margin-bottom:4px}
h2 .n{color:var(--blue);font-family:var(--mono);margin-right:8px}
h3{font-size:15px;margin:22px 0 10px;color:var(--tx)}
.lead{color:var(--tx2);font-size:13px;margin-bottom:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px 20px;margin:14px 0}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}
th{color:var(--tx2);font-weight:600;text-align:left;font-size:12px;letter-spacing:.4px}
th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top}
tr:hover td{background:var(--hover)}
.mono{font-family:var(--mono);font-size:12.5px}
.tag{display:inline-block;font-size:11px;font-family:var(--mono);padding:1px 8px;border-radius:2px;
  border:1px solid var(--line2);color:var(--tx2);margin-right:6px}
pre{background:#18191c;border:1px solid var(--line);border-radius:6px;padding:14px 16px;
  overflow-x:auto;font-family:var(--mono);font-size:12.5px;line-height:1.6;margin:12px 0}
pre .c{color:var(--tx3)} pre .k{color:var(--purple)} pre .s{color:var(--green)} pre .hl{color:var(--orange)}

/* 形态卡 */
.topo{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px;margin:16px 0}
.tcard{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden;
  display:flex;flex-direction:column}
.tcard.active{border-color:var(--blue)}
.tcard header{padding:14px 18px 10px;border-bottom:1px solid var(--line);cursor:pointer}
.tcard header .num{font-family:var(--mono);font-size:11px;color:var(--blue);letter-spacing:1px}
.tcard header h3{margin:2px 0 2px;font-size:16px}
.tcard header .en{font-family:var(--mono);font-size:11px;color:var(--tx3)}
.tcard header .sl{font-size:12px;color:var(--tx2);margin-top:6px}
.tcard .fig{padding:14px 16px;background:#18191c;border-bottom:1px solid var(--line);
  font-family:var(--mono);font-size:11.5px;line-height:1.55;white-space:pre;overflow-x:auto;color:#c9cdd6}
.tcard .fig .b{color:var(--blue)} .tcard .fig .g{color:var(--green)}
.tcard .fig .o{color:var(--orange)} .tcard .fig .r{color:var(--red)} .tcard .fig .d{color:var(--tx3)}
.tbody{padding:4px 18px 16px}
.frow{display:flex;gap:10px;padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}
.frow:last-child{border-bottom:none}
.frow .k{flex:0 0 78px;color:var(--tx2);font-size:12px}
.frow .v{flex:1}
.risk{margin-top:10px;padding:10px 12px;background:#241f1d;border:1px solid #4a3527;border-radius:6px}
.risk .t{font-size:12px;color:var(--orange);font-weight:600;margin-bottom:4px}
.risk li{font-size:12px;color:var(--tx2);margin:4px 0 4px 16px}
.risk b{color:var(--tx);font-weight:600}

/* 流水线对比表 */
.pipe td.step{font-family:var(--mono);color:var(--tx3);width:34px;text-align:center}
.pipe td.name{width:104px;font-weight:600;font-size:12.5px}
.pipe tr.diff td{background:#232a3d}
.pipe tr.diff:hover td{background:#2a3350}
.pipe .diffmark{color:var(--orange);font-family:var(--mono);font-size:11px}
.legend{font-size:12px;color:var(--tx2);margin:8px 0}
.legend .sw{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:-1px;margin:0 5px 0 14px}

/* profile 页签 */
.tabs{display:flex;gap:8px;margin:14px 0 0}
.tabs button{background:var(--panel);border:1px solid var(--line);color:var(--tx2);
  padding:7px 16px;border-radius:6px 6px 0 0;cursor:pointer;font-family:var(--ui);font-size:13px;
  border-bottom:none}
.tabs button.on{background:var(--panel2);color:var(--blue);border-color:var(--line2)}
.tabpane{display:none}
.tabpane.on{display:block}

/* 演进路径 */
.evo{display:flex;flex-direction:column;gap:12px;margin:14px 0}
.evrow{display:grid;grid-template-columns:120px 1fr;gap:14px;background:var(--panel);
  border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.evrow .arrow{font-family:var(--mono);font-size:15px;color:var(--blue);padding-top:2px}
.evrow .arrow small{display:block;color:var(--tx3);font-size:11px;font-family:var(--ui)}
.evrow .what{font-size:13px}
.evrow .why{font-size:12px;color:var(--tx2);margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}

/* 实测证据 */
.ev-ok{color:var(--green);font-family:var(--mono)}
.ev-warn{color:var(--orange);font-family:var(--mono)}

/* 共享内核网格 */
.core-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin:14px 0}
.core-item{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.core-item .p{font-family:var(--mono);font-size:12.5px;color:var(--blue)}
.core-item .d{font-size:12.5px;color:var(--tx);margin:4px 0}
.core-item .n{font-size:11.5px;color:var(--tx2)}

.callout{border-left:3px solid var(--blue);background:#1c2233;padding:12px 16px;border-radius:0 6px 6px 0;
  margin:14px 0;font-size:13px}
.callout.warn{border-left-color:var(--orange);background:#241f1d}
.callout b{color:var(--blue)} .callout.warn b{color:var(--orange)}

footer{margin-top:60px;padding-top:16px;border-top:1px solid var(--line);
  color:var(--tx3);font-size:12px;font-family:var(--mono)}
@media print{
  #side{display:none} #main{margin-left:0;max-width:none}
  .tcard,.card,.evrow,.core-item{break-inside:avoid}
  body{background:#fff;color:#111}
  .tcard .fig,pre{background:#f6f6f6;color:#222}
}
@media (max-width:900px){#side{display:none}#main{margin-left:0;padding:20px}}
"""

JS = """
// 侧栏高亮（IntersectionObserver，滚动驱动）
const links=[...document.querySelectorAll('#side a')];
const secs=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
const io=new IntersectionObserver(es=>{
  es.forEach(e=>{ if(e.isIntersecting){
    links.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id));
  }});
},{rootMargin:'-10% 0px -80% 0px'});
secs.forEach(s=>io.observe(s));

// profile 页签
document.querySelectorAll('.tabs').forEach(bar=>{
  bar.addEventListener('click',ev=>{
    const b=ev.target.closest('button'); if(!b)return;
    const paneId=b.dataset.pane;
    bar.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
    document.querySelectorAll('.tabpane[data-group="'+bar.dataset.group+'"]')
      .forEach(p=>p.classList.toggle('on',p.id===paneId));
  });
});

// 流水线差异过滤
const diffOnly=document.getElementById('diffOnly');
if(diffOnly) diffOnly.addEventListener('change',()=>{
  document.querySelectorAll('.pipe tr.diffable').forEach(tr=>{
    tr.style.display=(diffOnly.checked && !tr.classList.contains('diff'))?'none':'';
  });
});

// 形态卡「聚焦」：点击 header 高亮并在流水线表中联动过滤该形态列
const COLS={personal:3,lite:4,full:5};
document.querySelectorAll('.tcard header').forEach(h=>{
  h.addEventListener('click',()=>{
    const id=h.closest('.tcard').dataset.topo;
    const wasOn=h.closest('.tcard').classList.contains('active');
    document.querySelectorAll('.tcard').forEach(c=>c.classList.remove('active'));
    const tbl=document.querySelector('table.pipe');
    tbl.querySelectorAll('td').forEach(td=>td.style.opacity='');
    if(!wasOn){
      h.closest('.tcard').classList.add('active');
      const col=COLS[id];
      tbl.querySelectorAll('tr').forEach(tr=>{
        [...tr.children].forEach((td,i)=>{ if(i>1) td.style.opacity=(i+1===col)?'1':'0.35'; });
      });
    }
  });
});
"""

# ---------- 渲染函数 ----------
def esc(s): return _h.escape(str(s), quote=False)

def render_topo(t):
    """形态卡：拓扑图右框自动闭合（按显示宽度计算，中文按 2 列）"""
    import unicodedata
    def w(s):
        return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)
    def box_lines(title, body):
        # 开放式右边框：CJK/ASCII 混排在等宽字体下宽度比并非精确 2:1
        # （Consolas 0.55em vs CJK fallback 1em），闭合右边框在不同字体下必然错位。
        # 开放右侧从根上消除对齐问题，且是 CJK 密集 ASCII 图的通行做法。
        # 内容行显示宽 = 2（"│ " 前缀）+ w(ln)；顶/底线须不窄于最宽内容行
        max_w = max([w(x) for x in body] + [10])
        top_bar = max(2, max_w + 2 - 2 - w(title) - 1)   # ┌─(2) + title + 空格 + ─×N ≥ max_w+2
        out = ['┌─ ' + title + ' ' + '─' * top_bar]
        for ln in body:
            out.append('│ ' + ln)
        out.append('└' + '─' * (max_w + 1))              # └(1) + ─×(max_w+1) = max_w+2 ✓
        return out
    fig = box_lines(t['box'], t['body'])
    if t.get('box2'):
        fig += ['', '        ▲  │ ssh（FixedHostKey）· docker save | ssh docker load', '        │  ▼']
        fig += box_lines(t['box2'], t['body2'])
    fig = '\n'.join(fig)

    facts = ''.join(f'<div class="frow"><div class="k">{esc(k)}</div><div class="v">{v}</div></div>'
                    for k, v in t['facts'])
    risks = ''.join(f'<li><b>{esc(a)}</b> —— {esc(b)}</li>' for a, b in t['risks'])
    return f'''
<div class="tcard" data-topo="{t['id']}">
  <header><div class="num">{esc(t['num'])}</div><h3>{esc(t['name'])}</h3>
    <div class="en">{esc(t['en'])}</div><div class="sl">{esc(t['slogan'])}</div></header>
  <div class="fig">{esc(fig)}</div>
  <div class="tbody">{facts}
    <div class="risk"><div class="t">⚠ 风险与对策</div><ul>{risks}</ul></div>
  </div>
</div>'''

def render_pipeline(rows):
    trs = []
    for n, name, a, b, c, diff in rows:
        cls = 'diffable' + (' diff' if diff else '')
        mark = '<span class="diffmark">◆</span>' if diff else ''
        trs.append(f'<tr class="{cls}"><td class="step">{n}</td><td class="name">{esc(name)} {mark}</td>'
                   f'<td class="mono">{a}</td><td class="mono">{b}</td><td class="mono">{c}</td></tr>')
    return f'''
<table class="pipe">
<thead><tr><th>#</th><th>流水线步骤</th><th>Ⅰ 个人开发者版</th><th>Ⅱ 简易团队版</th><th>Ⅲ 完整团队版</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table>
<div class="legend"><span class="sw" style="background:#232a3d;border:1px solid #3a4a7a"></span>蓝底 ◆ = 形态差异步骤（13 步中仅 4 步不同）
<label style="margin-left:18px;cursor:pointer"><input type="checkbox" id="diffOnly"> 只看差异步骤</label>
<span style="margin-left:14px;color:var(--tx3)">（点击形态卡标题可在下表聚焦对应列）</span></div>'''

def render_profiles(profiles):
    btns, panes = [], []
    for i, (pid, label, yaml_text) in enumerate(profiles):
        on = ' on' if i == 0 else ''
        btns.append(f'<button data-pane="pf-{pid}" class="{on.strip()}">{esc(label)}</button>')
        panes.append(f'<div class="tabpane{on}" id="pf-{pid}" data-group="profiles"><pre>{esc(yaml_text)}</pre></div>')
    return f'<div class="tabs" data-group="profiles">{"".join(btns)}</div>{"".join(panes)}'
