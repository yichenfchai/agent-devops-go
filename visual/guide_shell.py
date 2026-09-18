# -*- coding: utf-8 -*-
"""guide.html 的外壳：CSS + HTML 骨架 + 渲染函数。内容与模板分离。"""

CSS = r"""
:root{
  --bg:#080d17; --panel:#0f1728; --panel2:#141f35; --panel3:#1a2743;
  --line:#243352; --line2:#2f4066;
  --fg:#e8eefb; --muted:#8ba0c4; --dim:#5f7396;
  --blue:#4d8dfb; --green:#34d399; --amber:#fbbf24; --red:#f87171; --purple:#a78bfa;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;background:var(--bg);color:var(--fg);
  font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Source Han Sans SC",system-ui,-apple-system,sans-serif;
  font-size:14.5px;line-height:1.75;-webkit-font-smoothing:antialiased;
}
a{color:var(--blue)}
code,kbd,pre{font-family:var(--mono)}

/* ---------- 布局 ---------- */
.shell{display:grid;grid-template-columns:264px 1fr;max-width:1560px;margin:0 auto}
@media(max-width:1000px){.shell{grid-template-columns:1fr}.side{display:none}}

.side{
  position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
  border-right:1px solid var(--line);padding:22px 16px 40px;background:var(--panel);
}
.side h2{margin:0 0 3px;font-size:15px;letter-spacing:-.2px}
.side .tag{color:var(--dim);font-size:11px;margin:0 0 16px;letter-spacing:.06em}
.side input{
  width:100%;background:var(--bg);border:1px solid var(--line2);color:var(--fg);
  border-radius:7px;padding:7px 10px;font-size:12.5px;font-family:inherit;margin-bottom:14px;
}
.side input:focus{outline:none;border-color:var(--blue)}
.navgrp{margin-bottom:14px}
.navgrp>.lbl{font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;color:var(--dim);
  font-weight:700;margin:0 0 6px;padding-left:8px}
.nav a{
  display:flex;align-items:baseline;gap:7px;padding:5px 8px;border-radius:6px;
  color:var(--muted);text-decoration:none;font-size:12.5px;line-height:1.45;transition:.13s;
  border-left:2px solid transparent;
}
.nav a:hover{background:var(--panel2);color:var(--fg)}
.nav a.on{background:var(--panel3);color:#fff;border-left-color:var(--blue)}
.nav a .n{font-family:var(--mono);font-size:11px;color:var(--dim);flex:none;width:18px}
.nav a.on .n{color:var(--blue)}
.nav a.hide{display:none}
.nav .st{margin-left:auto;font-size:9.5px;flex:none;opacity:.85}

.main{padding:30px 40px 90px;min-width:0}
@media(max-width:1000px){.main{padding:22px 18px 60px}}

/* ---------- 页头 ---------- */
header.top{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}
h1{margin:0 0 6px;font-size:24px;letter-spacing:-.3px}
.lede{color:var(--muted);margin:0 0 16px;font-size:13.5px;max-width:900px}
.legend{display:flex;gap:8px;flex-wrap:wrap;font-size:11.5px}
.chip{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line2);
  background:var(--panel2);border-radius:20px;padding:3px 11px;color:var(--muted)}
.chip b{font-weight:600}
.chip.done{border-color:#1d5c46;color:#7ee2b8;background:#0d231c}
.chip.plan{border-color:#5a4410;color:#e5c07b;background:#1d1708}

/* ---------- 进度条 ---------- */
.prog{position:sticky;top:0;z-index:20;background:rgba(8,13,23,.94);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);margin:-30px -40px 26px;padding:9px 40px;
  display:flex;align-items:center;gap:12px;font-size:11.5px;color:var(--dim)}
@media(max-width:1000px){.prog{margin:-22px -18px 20px;padding:9px 18px}}
.prog .bar{flex:1;height:4px;background:var(--panel3);border-radius:3px;overflow:hidden}
.prog .bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--blue),var(--green));
  transition:width .18s}
.prog button{background:var(--panel2);border:1px solid var(--line2);color:var(--muted);
  border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer;font-family:inherit}
.prog button:hover{color:var(--fg);border-color:var(--blue)}

/* ---------- 站点 ---------- */
.station{scroll-margin-top:64px;margin-bottom:34px;border:1px solid var(--line);
  border-radius:13px;background:var(--panel);overflow:hidden}
.station.done{border-color:#1d5c46}
.station.plan{border-color:#4a3a12}
.shead{padding:16px 20px 14px;border-bottom:1px solid var(--line);
  display:flex;align-items:flex-start;gap:13px;cursor:pointer;user-select:none}
.station.done .shead{background:linear-gradient(180deg,#0c211b,#0f1728)}
.station.plan .shead{background:linear-gradient(180deg,#1c1608,#0f1728)}
.snum{font-family:var(--mono);font-size:19px;font-weight:700;color:var(--blue);flex:none;
  width:30px;line-height:1.3}
.station.plan .snum{color:var(--amber)}
.stitle{flex:1;min-width:0}
.stitle h2{margin:0;font-size:16.5px;letter-spacing:-.2px;line-height:1.4}
.stitle .sub{color:var(--muted);font-size:12.5px;margin:3px 0 0;line-height:1.55}
.sbadge{flex:none;display:flex;gap:6px;align-items:center;padding-top:3px}
.b{font-size:10px;letter-spacing:.05em;border-radius:4px;padding:2px 7px;font-weight:600;white-space:nowrap}
.b.done{background:#12352a;color:#7ee2b8;border:1px solid #1d5c46}
.b.plan{background:#2a2110;color:#e5c07b;border:1px solid #5a4410}
.b.part{background:#101f38;color:#8fc0ff;border:1px solid #1e3a80}
.chev{flex:none;color:var(--dim);transition:transform .2s;font-size:12px;padding-top:5px}
.station.fold .chev{transform:rotate(-90deg)}
.station.fold .sbody{display:none}
.sbody{padding:18px 20px 20px}

/* ---------- 内容块 ---------- */
.blk{margin-bottom:18px}
.blk:last-child{margin-bottom:0}
.blk>h3{margin:0 0 9px;font-size:12px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--dim);font-weight:700;display:flex;align-items:center;gap:7px}
.blk>h3::before{content:"";width:3px;height:12px;background:var(--line2);border-radius:2px}
.blk>h3.k-warn::before{background:var(--red)}
.blk>h3.k-tip::before{background:var(--green)}
.blk>h3.k-code::before{background:var(--purple)}
.blk>h3.k-analogy::before{background:var(--amber)}
.blk p{margin:0 0 9px}
.blk p:last-child{margin-bottom:0}
.blk strong{color:#fff;font-weight:600}
.blk em{color:var(--amber);font-style:normal}
.blk ul,.blk ol{margin:0 0 9px;padding-left:22px}
.blk li{margin-bottom:5px}
.blk li::marker{color:var(--dim)}
code:not(pre code){background:var(--panel3);border:1px solid var(--line2);border-radius:4px;
  padding:1px 5px;font-size:12.5px;color:#a8d4ff}

/* 类比框 */
.analogy{border-left:3px solid var(--amber);background:#1a1608;border-radius:0 8px 8px 0;
  padding:12px 15px;font-size:13.5px;color:#f0dcae}
.analogy .t{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:#c9a44e;
  font-weight:700;margin-bottom:5px}

/* 坑 / 提示 */
.warn,.tip{border-radius:8px;padding:12px 15px;font-size:13.5px}
.warn{background:#1e1010;border:1px solid #5c2020;border-left:3px solid var(--red)}
.tip{background:#0d231c;border:1px solid #1d5c46;border-left:3px solid var(--green)}
.warn .t,.tip .t{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;margin-bottom:5px}
.warn .t{color:#f08a8a}.tip .t{color:#7ee2b8}

/* 代码块 */
.codewrap{position:relative}
.codewrap .lang{position:absolute;top:7px;right:10px;font-size:9.5px;letter-spacing:.09em;
  text-transform:uppercase;color:var(--dim);font-family:var(--mono)}
pre{margin:0;background:#060a12;border:1px solid var(--line);border-radius:8px;
  padding:13px 15px;overflow-x:auto;font-size:12.3px;line-height:1.68;color:#cfe0f5}
pre .c{color:#5f7396;font-style:italic}
pre .k{color:#7aa7ff}
pre .s{color:#8ee6b0}
pre .n{color:#e5c07b}
pre .bad{color:#ff9b9b}
pre .good{color:#7ee2b8}

/* 表格 */
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:12.8px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-weight:600;font-size:11.5px;
  letter-spacing:.05em;white-space:nowrap}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--panel2)}
td.mono,th.mono{font-family:var(--mono);font-size:12px}
td .yes{color:var(--green)}td .no{color:var(--red)}

/* 流程图 */
.flow{background:#060a12;border:1px solid var(--line);border-radius:8px;padding:15px;
  overflow-x:auto;font-family:var(--mono);font-size:12px;line-height:1.6;
  white-space:pre;color:#9fc4ee}

/* 键值对 */
.kv{display:grid;grid-template-columns:minmax(120px,auto) 1fr;gap:0;
  border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:13px}
.kv>div{padding:8px 13px;border-bottom:1px solid var(--line)}
.kv>div:nth-child(4n+1),.kv>div:nth-child(4n+2){background:var(--panel2)}
.kv .k{color:var(--muted);font-weight:600}
.kv>div:nth-last-child(-n+2){border-bottom:none}

/* 总览动画 */
.pipeline{border:1px solid var(--line);border-radius:13px;background:var(--panel);padding:20px;margin-bottom:30px}
.pipeline h2{margin:0 0 4px;font-size:16px}
.pipeline .sub{color:var(--muted);font-size:12.5px;margin:0 0 18px}
.prow{display:flex;gap:7px;flex-wrap:wrap;align-items:stretch}
.pnode{flex:1 1 108px;min-width:104px;border:1px solid var(--line2);border-radius:8px;
  background:var(--panel2);padding:9px 10px;cursor:pointer;transition:.2s;position:relative;
  text-decoration:none;color:inherit;display:block}
.pnode:hover{border-color:var(--blue);transform:translateY(-2px)}
.pnode .pn{font-family:var(--mono);font-size:10px;color:var(--dim)}
.pnode .pt{font-size:12px;font-weight:600;margin-top:2px;line-height:1.35}
.pnode.act{border-color:var(--blue);background:#16233d;box-shadow:0 0 0 1px var(--blue),0 8px 24px -12px var(--blue)}
.pnode.act .pn{color:var(--blue)}
.pnode.ok{border-color:#1d5c46;background:#0d231c}
.pnode.ok .pn{color:var(--green)}
.pnode.fail{border-color:#5c2020;background:#1e1010}
.pnode.fail .pn{color:var(--red)}
.pctl{display:flex;gap:8px;align-items:center;margin-top:16px;flex-wrap:wrap}
.pctl button{background:var(--panel2);border:1px solid var(--line2);color:var(--fg);
  border-radius:7px;padding:6px 14px;font-size:12.5px;cursor:pointer;font-family:inherit;transition:.15s}
.pctl button:hover{border-color:var(--blue)}
.pctl button:disabled{opacity:.4;cursor:not-allowed}
.pctl .msg{color:var(--muted);font-size:12.5px;flex:1;min-width:200px;font-family:var(--mono)}
.pctl label{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--muted);cursor:pointer}

/* 三主线 */
.mainlines{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:30px}
@media(max-width:900px){.mainlines{grid-template-columns:1fr}}
.ml{border:1px solid var(--line);border-radius:11px;padding:15px 16px;background:var(--panel)}
.ml h3{margin:0 0 8px;font-size:14px}
.ml pre{font-size:11.6px;line-height:1.62}
.ml p{margin:0;color:var(--muted);font-size:12.5px}

footer{border-top:1px solid var(--line);margin-top:40px;padding-top:18px;color:var(--dim);font-size:12px}
.top-link{position:fixed;right:22px;bottom:22px;width:40px;height:40px;border-radius:50%;
  background:var(--panel3);border:1px solid var(--line2);color:var(--fg);cursor:pointer;
  display:none;align-items:center;justify-content:center;font-size:16px;z-index:30}
.top-link.show{display:flex}
.top-link:hover{border-color:var(--blue)}
@media print{
  .side,.prog,.top-link,.pctl{display:none!important}
  .shell{display:block}.main{padding:0}
  .station.fold .sbody{display:block}
  body{background:#fff;color:#000;font-size:11pt}
  .station,.pipeline,.ml{break-inside:avoid;border-color:#bbb;background:#fff}
  pre,.flow{background:#f6f6f6;color:#111;border-color:#ccc}
  .shead{background:#f0f0f0!important}
}
"""

JS = r"""
(function(){
  var $=function(s,c){return (c||document).querySelector(s)};
  var $$=function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};

  /* ---- 折叠 ---- */
  $$('.shead').forEach(function(h){
    h.addEventListener('click',function(){h.parentNode.classList.toggle('fold')});
  });
  $('#btn-fold').addEventListener('click',function(){
    var any=$$('.station:not(.fold)').length;
    $$('.station').forEach(function(s){s.classList.toggle('fold',!!any)});
    this.textContent=any?'全部展开':'全部折叠';
  });

  /* ---- 侧栏高亮 + 进度 ---- */
  var stations=$$('.station'), links=$$('.nav a[data-t]');
  var bar=$('#prog-fill'), pct=$('#prog-pct');
  function onScroll(){
    var y=window.scrollY+120, cur=stations[0];
    stations.forEach(function(s){ if(s.offsetTop<=y) cur=s });
    links.forEach(function(a){a.classList.toggle('on',a.dataset.t===cur.id)});
    var h=document.documentElement.scrollHeight-window.innerHeight;
    var p=h>0?Math.min(100,Math.round(window.scrollY/h*100)):0;
    bar.style.width=p+'%'; pct.textContent=p+'%';
    $('#totop').classList.toggle('show',window.scrollY>600);
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  links.forEach(function(a){
    a.addEventListener('click',function(e){
      var t=document.getElementById(a.dataset.t);
      if(!t)return;
      e.preventDefault();
      t.classList.remove('fold');
      window.scrollTo({top:t.offsetTop-58,behavior:'smooth'});
      history.replaceState(null,'','#'+a.dataset.t);
    });
  });

  /* ---- 侧栏搜索 ---- */
  $('#q').addEventListener('input',function(){
    var q=this.value.trim().toLowerCase();
    links.forEach(function(a){
      var hit=!q||a.textContent.toLowerCase().indexOf(q)>=0;
      a.classList.toggle('hide',!hit);
    });
    $$('.navgrp').forEach(function(g){
      g.style.display=g.querySelectorAll('a:not(.hide)').length?'':'none';
    });
  });

  /* ---- 全流程动画 ---- */
  var nodes=$$('.pnode'), msg=$('#pmsg'), failBox=$('#chk-fail');
  var timer=null, pbtn=$('#pbtn');
  var FAIL_IDX=5;              /* nodes[5] = ⑥ 构建，失败剧本在这里中断 */
  function reset(){
    nodes.forEach(function(n){n.className='pnode'});
    if(timer){clearTimeout(timer);timer=null}
    pbtn.disabled=false; pbtn.textContent='▶ 播放全流程';
  }
  function done(text){
    if(timer){clearTimeout(timer);timer=null}
    pbtn.disabled=false; pbtn.textContent='▶ 重播';
    msg.textContent=text;
  }
  function play(){
    reset();
    var willFail=failBox.checked, failIdx=willFail?FAIL_IDX:-1, i=0;
    pbtn.disabled=true; pbtn.textContent='播放中…';
    (function step(){
      if(i>0){
        var prev=nodes[i-1];
        prev.classList.remove('act');
        prev.classList.add((i-1)===failIdx?'fail':'ok');
      }
      if(i>0&&(i-1)===failIdx){
        /* 构建失败：后续节点回到未激活态，链路终止于诊断 */
        nodes.forEach(function(x,k){ if(k>i-1) x.className='pnode' });
        done('阶段退出码 != 0 → 构建失败 ──▶ 转 ⑫ LOA 策略引擎诊断');
        return;
      }
      if(i>=nodes.length){
        done('部署成功 → 健康检查通过 → 状态 deployed');
        return;
      }
      nodes[i].classList.add('act');
      msg.textContent=nodes[i].dataset.msg||nodes[i].querySelector('.pt').textContent;
      i++;
      timer=setTimeout(step,1300);
    })();
  }
  pbtn.addEventListener('click',play);
  nodes.forEach(function(n){
    n.addEventListener('click',function(e){
      e.preventDefault();
      if(timer)return;
      var t=document.getElementById(n.dataset.goto);
      if(t){t.classList.remove('fold');window.scrollTo({top:t.offsetTop-58,behavior:'smooth'});
            history.replaceState(null,'','#'+n.dataset.goto)}
    });
  });

  /* ---- 锚点直达 ---- */
  if(location.hash){
    var t=document.getElementById(location.hash.slice(1));
    if(t){t.classList.remove('fold');setTimeout(function(){
      window.scrollTo({top:t.offsetTop-58})},60)}
  }
  $('#totop').addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});
  onScroll();
})();
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_block(b):
    """把一个内容块渲染成 HTML。类型见 STATIONS 数据文件。"""
    k = b["type"]
    if k == "text":
        return '<div class="blk">%s</div>' % b["body"]
    if k == "analogy":
        return ('<div class="blk"><h3 class="k-analogy">小白类比</h3>'
                '<div class="analogy"><div class="t">打个比方</div>%s</div></div>') % b["body"]
    if k == "warn":
        return ('<div class="blk"><h3 class="k-warn">%s</h3><div class="warn">'
                '<div class="t">坑 / 必须守住</div>%s</div></div>') % (b.get("h", "踩过的坑"), b["body"])
    if k == "tip":
        return ('<div class="blk"><h3 class="k-tip">%s</h3><div class="tip">'
                '<div class="t">为什么这样设计</div>%s</div></div>') % (b.get("h", "为什么这样"), b["body"])
    if k == "code":
        return ('<div class="blk"><h3 class="k-code">%s</h3><div class="codewrap">'
                '<span class="lang">%s</span><pre>%s</pre></div></div>') % (
            b.get("h", "技术细节"), b.get("lang", "text"), b["body"])
    if k == "flow":
        return '<div class="blk"><h3>%s</h3><div class="flow">%s</div></div>' % (
            b.get("h", "流程"), b["body"])
    if k == "table":
        head = "".join('<th%s>%s</th>' % (' class="mono"' if c.startswith("!") else "",
                                         c.lstrip("!")) for c in b["cols"])
        rows = []
        for r in b["rows"]:
            tds = []
            for c in r:
                cls = ' class="mono"' if isinstance(c, str) and c.startswith("!") else ""
                tds.append("<td%s>%s</td>" % (cls, c.lstrip("!") if isinstance(c, str) else c))
            rows.append("<tr>%s</tr>" % "".join(tds))
        return ('<div class="blk"><h3>%s</h3><div class="tw"><table><thead><tr>%s</tr></thead>'
                '<tbody>%s</tbody></table></div></div>') % (b.get("h", "对比"), head, "".join(rows))
    if k == "kv":
        cells = "".join('<div class="k">%s</div><div>%s</div>' % (a, c) for a, c in b["items"])
        return '<div class="blk"><h3>%s</h3><div class="kv">%s</div></div>' % (b.get("h", "要点"), cells)
    raise ValueError("未知块类型: %s" % k)


BADGE = {"done": ('<span class="b done">前端已实现</span>', "done"),
         "design": ('<span class="b plan">后端待实现</span>', "plan"),
         "mixed": ('<span class="b part">前端已实现</span><span class="b plan">后端待实现</span>', "plan")}


def render_station(s):
    badge, cls = BADGE[s["status"]]
    body = "".join(render_block(b) for b in s["sections"])
    return ('<section class="station %s" id="%s"><div class="shead">'
            '<span class="snum">%s</span><div class="stitle"><h2>%s</h2><p class="sub">%s</p></div>'
            '<span class="sbadge">%s</span><span class="chev">▼</span></div>'
            '<div class="sbody">%s</div></section>') % (
        cls, s["id"], s["num"], s["title"], s["sub"], badge, body)
