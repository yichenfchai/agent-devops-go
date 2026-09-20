# -*- coding: utf-8 -*-
"""部署形态可视化 · 生成器：python build_deploy_modes.py → deploy-modes.html"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dm_shell import CSS, JS, esc, render_topo, render_pipeline, render_profiles
from dm_content1 import TOPOLOGIES, PIPELINE, INTERFACES_GO, WIRING_GO, DEP_RULE, ADAPTER_MATRIX
from dm_content2 import SHARED_CORE, PROFILES, EVOLUTION, EVIDENCE, FRONTEND_IMPACT

NAV = [
    ("grp", "总览"),
    ("s0", "为什么是三种形态"),
    ("s1", "三形态拓扑对照"),
    ("grp", "解耦设计"),
    ("s2", "13 步流水线对比"),
    ("s3", "三个解耦点（接口层）"),
    ("s4", "共享内核（100% 复用）"),
    ("grp", "落地"),
    ("s5", "Profile 配置（三档）"),
    ("s6", "形态演进路径"),
    ("s7", "前端影响面"),
    ("s8", "实测证据清单"),
]

def nav_html():
    out = []
    for kind, val in NAV:
        if kind == "grp":
            out.append(f'<div class="grp">{esc(val)}</div>')
        else:
            titles = {"s0":"为什么是三种形态","s1":"三形态拓扑对照","s2":"13 步流水线对比",
                      "s3":"三个解耦点","s4":"共享内核","s5":"Profile 配置","s6":"演进路径",
                      "s7":"前端影响面","s8":"实测证据清单"}
            out.append(f'<a href="#{kind}">{esc(titles[kind])}</a>')
    return "\n".join(out)

def sec(id_, n, title, lead, body):
    return (f'<section id="{id_}"><h2><span class="n">{esc(n)}</span>{esc(title)}</h2>'
            f'<div class="lead">{lead}</div>{body}</section>')

# ---------- 各章节 ----------
S0 = '''
<p style="font-size:13.5px">同一个二进制 <span class="mono">devopsd</span>，靠三个接口点 + 一份 profile 配置，
覆盖从「一台笔记本、零公网依赖」到「构建机与多台生产机分离」的全部场景。
三档之间<b style="color:var(--blue)">不是三个产品</b>，而是同一软件在三种资源约束下的部署形态 ——
差异被严格约束在<b>触发、检出、部署</b>三个接口点内，核心（调度 / 状态机 / 构建 / 日志 / LOA / 诊断 / 回滚 / 存储 / 前端）三档 100% 共用。</p>
<div class="callout"><b>不重复造轮子的三条纪律：</b>
① 核心不知道形态存在（<span class="mono">internal/core</span> 禁止 import 任何 adapter）；
② 形态差异全部收敛到 <span class="mono">cmd/devopsd/main.go</span> 的一个 switch；
③ 新增第 4 种形态 = 新增一个 adapter + 一份 profile，核心与前端零改动。</div>
<table>
<thead><tr><th></th><th>Ⅰ 个人开发者版</th><th>Ⅱ 简易团队版</th><th>Ⅲ 完整团队版</th></tr></thead>
<tbody>
<tr><td><b>profile</b></td><td class="mono">personal</td><td class="mono">team-lite</td><td class="mono">team-full</td></tr>
<tr><td><b>机器数</b></td><td>1（笔记本）</td><td>1（生产服务器合设）</td><td>1+N（构建 VPS + 目标机）</td></tr>
<tr><td><b>代码源</b></td><td>本地 git 仓库</td><td>GitHub</td><td>GitHub / GitLab</td></tr>
<tr><td><b>触发</b></td><td>fsnotify 监视 .git/</td><td>webhook（HTTP+裸 IP 即可）</td><td>webhook</td></tr>
<tr><td><b>检出</b></td><td class="mono">git archive &lt;sha&gt;</td><td class="mono">git fetch &lt;sha&gt;</td><td class="mono">git fetch &lt;sha&gt;</td></tr>
<tr><td><b>部署</b></td><td>compose-local</td><td>compose-local（127.0.0.1）</td><td>ssh-remote ×N</td></tr>
<tr><td><b>公网暴露</b></td><td style="color:var(--green)">零</td><td>1 个端口（:8080）</td><td>构建机 :8080 + 目标机 :22</td></tr>
<tr><td><b>月成本</b></td><td style="color:var(--green)">0</td><td style="color:var(--green)">0（蹭已有生产机）</td><td>1 台 VPS</td></tr>
<tr><td><b>并发</b></td><td class="mono">max_concurrency 2</td><td class="mono">1（强制串行）</td><td class="mono">4</td></tr>
<tr><td><b>用户</b></td><td>单用户</td><td>2–5 人共享</td><td>团队 + RBAC</td></tr>
<tr><td><b>论文角色</b></td><td style="color:var(--blue)">实现与演示主线（离线可演）</td><td>第二形态（配置即得）</td><td>架构蓝图（可扩展性论述）</td></tr>
</tbody></table>
<p style="font-size:12.5px;color:var(--tx2)">递进逻辑：每一档只比上一档多一台机器 / 一层网络依赖。
「简易团队版」在代码上与「完整团队版」同路径 —— 仅 <span class="mono">deploy_hosts.addr</span> 填 127.0.0.1，
它本质是一份配置，不是一个开发任务。</p>
'''

S1 = '<div class="topo">' + ''.join(render_topo(t) for t in TOPOLOGIES) + '</div>'

S2 = render_pipeline(PIPELINE) + '''
<div class="callout">13 步中仅 <b>4 步</b>（触发 / 验签 / 检出 / 部署）存在形态差异，且全部落在接口点之后；
其余 9 步 —— 幂等入队、原子认领、检测快照、容器构建、日志管道、镜像产物、健康检查、LOA 诊断、回滚 ——
三档<b>逐字节共用同一实现</b>。这就是「拆三档但只写一份核心」的量化依据。</div>'''

S3 = f'''
<h3>3.1 核心只定义接口（ports）</h3>
<pre>{esc(INTERFACES_GO)}</pre>
<h3>3.2 装配：全系统唯一的形态分支点</h3>
<pre>{esc(WIRING_GO)}</pre>
<h3>3.3 依赖方向（编译期强制）</h3>
<pre>{chr(10).join(DEP_RULE)}</pre>
<h3>3.4 adapter 矩阵：形态 × 接口点</h3>
<table><thead><tr><th>接口</th><th>形态 Ⅰ</th><th>形态 Ⅱ / Ⅲ</th><th>恒有</th></tr></thead><tbody>
{''.join(f'<tr><td class="mono">{esc(a)}</td><td class="mono">{esc(b)}</td><td class="mono">{esc(c)}</td><td class="mono">{esc(d)}</td></tr>' for a,b,c,d in ADAPTER_MATRIX)}
</tbody></table>
<div class="callout warn"><b>与「一切皆插件」的关系：</b>这三个接口与 analyzer/action/detector 注册表是同一套哲学的两层 ——
接口层解耦「部署形态」，注册表层解耦「诊断能力扩展」。两者互不感知：
换形态不影响插件，装插件不影响形态。</div>'''

S4 = f'''
<p style="font-size:13px">以下 12 个模块在三档中<b>不存在任何条件分支</b>，形态差异要么在接口点之外，要么已收敛为配置值：</p>
<div class="core-grid">
{''.join(f'<div class="core-item"><div class="p">{esc(p)}</div><div class="d">{esc(d)}</div><div class="n">{esc(n)}</div></div>' for p,d,n in SHARED_CORE)}
</div>'''

S5 = render_profiles(PROFILES) + '''
<div class="callout">三份 profile 就是「产品分档」的全部实现 —— <b>没有三套代码，只有三份 YAML</b>。
标 ★ 的两行是形态Ⅱ的命门：与生产同机时，串行 + 限额不是优化项，是保命项。</div>'''

_evo_rows = "".join(
    '<div class="evrow"><div class="arrow">' + esc(a) + '<small>' + esc(b) + '</small></div>'
    '<div><div class="what">' + c + '</div><div class="why">为什么不丢数据：' + esc(d) + '</div></div></div>'
    for a, b, c, d in EVOLUTION)

S6 = f'''
<div class="evo">
{_evo_rows}
</div>
<div class="callout"><b>迁移成本 = 拷贝文件。</b>SQLite 单文件数据库 + 单二进制的设计在这里兑现价值：
形态升级不导出/不重建/不停机迁移，<span class="mono">scp devopsd devops.db data/ 新机器:</span> 即完成。
构建历史、知识库、已验证三元组（LOA 演进的积累）随库整体带走。</div>'''

S7 = f'''
<table><thead><tr><th>前端资产</th><th>改动量</th><th>说明</th></tr></thead><tbody>
{''.join(f'<tr><td>{esc(a)}</td><td><b style="color:{"var(--orange)" if b!="零改动" else "var(--green)"}">{esc(b)}</b></td><td>{c}</td></tr>' for a,b,c in FRONTEND_IMPACT)}
</tbody></table>
<p style="font-size:12.5px;color:var(--tx2)">现有 13 页面 / 167 测试 / openapi 契约全部保值；
改动集中在向导一处新增项目类型 + 部署目标卡片一种新 kind，均为向后兼容的增量。</p>'''

S8 = f'''
<table><thead><tr><th>断言</th><th>验证方式</th><th>证据摘要</th></tr></thead><tbody>
{''.join(f'<tr><td>{esc(a)}</td><td><span class="{"ev-ok" if "未实测" not in b else "ev-warn"}">{esc(b)}</span></td><td style="color:var(--tx2)">{esc(c)}</td></tr>' for a,b,c in EVIDENCE)}
</tbody></table>
<div class="callout warn"><b>诚实边界：</b>标橙色「未实测」的条目是设计依据而非实测结论，M1 的第一项 spike 就是补验；
本机当前无 docker CLI（已实测确认），形态Ⅰ演示前需先安装容器引擎 —— 已列入前置清单，不隐瞒。</div>'''

SECTIONS = [
    sec("s0", "§0", "为什么是三种形态", "从资源约束出发的产品分档，而非功能阉割。", S0),
    sec("s1", "§1", "三形态拓扑对照", "点击卡片标题可在 §2 流水线表中聚焦对应列。", S1),
    sec("s2", "§2", "13 步流水线对比", "同一核心流程在三档下的逐步对照 —— 差异一目了然。", S2),
    sec("s3", "§3", "三个解耦点（接口层）", "TriggerSource · CheckoutStrategy · DeployTarget —— 全系统仅有的形态分支。", S3),
    sec("s4", "§4", "共享内核（100% 复用）", "12 个模块无条件分支，三档逐字节共用。", S4),
    sec("s5", "§5", "Profile 配置（三档）", "配置文件即产品分档 —— 完整 YAML，可直接作为 config 预设落地。", S5),
    sec("s6", "§6", "形态演进路径", "用户长大了怎么办：升级 = 搬文件 + 换 profile。", S6),
    sec("s7", "§7", "前端影响面", "现有 13 页面 / 167 测试的改动清单。", S7),
    sec("s8", "§8", "实测证据清单", "所有「已核实/实测」断言的出处，可复核。", S8),
]

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GoPulse CI · 三种部署形态架构设计</title>
<style>{CSS}</style></head><body>
<nav id="side">
<h1>GoPulse CI</h1><div class="sub">deploy-modes · v1.0</div>
{nav_html()}
</nav>
<main id="main">
<header style="margin-bottom:36px">
<h2 style="font-size:24px">三种部署形态 · 架构设计</h2>
<p class="lead" style="margin-top:8px">个人开发者版（无 GitHub · 无 VPS）→ 简易团队版（合设 · 蹭生产机）→ 完整团队版（构建/目标分离）。
同一二进制，三个接口点，三份 profile。所有技术断言附实测出处（§8），设计推断单独标注。</p>
</header>
{''.join(SECTIONS)}
<footer>GoPulse CI · deploy-modes.html · 由 build_deploy_modes.py 生成（内容: dm_content1/2.py · 外壳: dm_shell.py）
· 零外部依赖 · 打印友好（Ctrl+P 导出 PDF）</footer>
</main>
<script>{JS}</script>
</body></html>'''

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy-modes.html")
with io.open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"written: {out}  ({len(HTML)} chars)")
