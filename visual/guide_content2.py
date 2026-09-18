# -*- coding: utf-8 -*-
"""guide 内容 · 第 2 部分：站点 ⑨–⑮ + 三条设计主线。"""

P2 = [

dict(id="s9", num="⑨", status="design",
 title="部署：SSH 与中间人攻击",
 sub="加密远程执行的原理，以及最容易被忽略的一道防御",
 sections=[
  dict(type="analogy", body="""
<strong>SSH = 加密的远程命令行。</strong><br><br>
你在自己电脑上敲命令，实际在几百公里外的服务器上执行，输出再传回来，全程加密 ——
像给服务器接了一根很长很长的键盘线和屏幕线，但中间没人能偷看。<br><br>
<code style="background:#1a2743">ssh deploy@10.0.0.8 "docker-compose up -d"</code><br>
意思：以 <code>deploy</code> 用户身份登录 <code>10.0.0.8</code>，执行引号里的命令。"""),

  dict(type="text", body="""
<p><strong>认证方式：密钥而非密码。</strong></p>"""),

  dict(type="flow", h="非对称密钥认证原理", body="""私钥（id_rsa）     ──▶ 存在 GoPulse 这边，AES-GCM 加密后放数据库
公钥（id_rsa.pub） ──▶ 放在目标服务器的 ~/.ssh/authorized_keys 里

连接时：
  服务器用【公钥】出一个「只有对应私钥才能解」的题
        │
        ▼
  GoPulse 用【私钥】解开 ──▶ 证明「我确实持有私钥」──▶ 允许登录

关键：【私钥从不在网络上传输】，传输的只是签名的应答"""),

  dict(type="warn", h="Host Key 校验：最容易被忽略、后果最严重的一环", body="""
<strong>中间人攻击场景：</strong>"""),

  dict(type="flow", body="""GoPulse 想连 10.0.0.8
        │
        ▼
攻击者在网络中间拦截，【伪装成 10.0.0.8】
        │
        ▼
GoPulse 把 SSH 认证信息、部署命令、代码全发给攻击者
        │
        ▼
攻击者拿到一切 ──▶ 你的服务器、代码、密钥全部沦陷"""),

  dict(type="text", body="""
<p><strong>防御原理：</strong>每台服务器的 SSH 服务有一个<em>主机密钥指纹</em>。
第一次连接时记录下来，以后每次连接都核对 —— 指纹不对就拒绝连接。</p>"""),

  dict(type="code", lang="go", body="""ssh.Dial(<span class="s">"tcp"</span>, addr, &amp;ssh.ClientConfig{
    User:            user,
    Auth:            []ssh.AuthMethod{ssh.PublicKeys(key)},
    HostKeyCallback: ssh.FixedHostKey(expectedKey),   <span class="c">// ← 关键这一行</span>
    Timeout:         <span class="n">10</span> * time.Second,               <span class="c">// 必须有超时</span>
})"""),

  dict(type="warn", h="反面教材：网上大量 Go SSH 示例代码在教人犯错", body="""
<code>ssh.InsecureIgnoreHostKey()</code> —— 很多教程用它，因为「省事，不用管指纹」。<br><br>
<strong>它完全关闭了中间人防御。</strong>名字里的 <code>Insecure</code> 不是玩笑。<br><br>
本项目架构明确要求用 <code>FixedHostKey</code>，前端「添加主机」表单里也有「目标机公钥指纹」字段，
还给了提示<em>「可在目标机执行 ssh-keyscan 获取」</em>。"""),

  dict(type="tip", h="部署前环境检查：为什么不能省", body="""
在真正部署前先探一下目标机：<br>
<code>docker 装了吗？ docker-compose 装了吗？ 磁盘够吗？ 工作目录可写吗？</code><br><br>
<strong>如果不检查：</strong>部署到一半发现目标机没装 docker，此时<em>旧版本已经停了、新版本起不来</em>
—— <strong>服务彻底中断</strong>。<br><br>
提前检查能把失败挡在「还没动线上」的阶段。这就是 <code>sshx.Runner.Probe()</code> 接口的用途。"""),

  dict(type="text", body="""
<p><strong>版本保留与回滚的实现。</strong>目标机上保留最近 K 个版本：</p>"""),

  dict(type="flow", body="""/srv/web-api/
  ├── current  ──▶ releases/a3f9c21      （软链接，指向当前版本）
  └── releases/
      ├── a3f9c21/    ← 当前
      ├── 7b1e044/    ← 上一个（回滚目标）
      └── c9d2e18/

回滚 = 把 current 软链接指回上一个版本 + 重新 docker-compose up -d
     ──▶ 因为镜像不可变，【回滚不需要重新构建】，几秒就能完成"""),

  dict(type="table", h="三种部署策略（本项目的取舍）", cols=["策略", "做法", "停机", "难度", "本项目"],
   rows=[["<strong>原地替换</strong>", "SSH + <span class='mono'>docker-compose up -d</span>", "有短暂停机（5–10 秒）", "★",
          "<span class='yes'>✅ 最小可用版，M4 实现</span>"],
         ["蓝绿", "备用端口起新容器 → 健康检查 → 切流量", "无", "★★★", "⬜ 暂缓（进未来工作）"],
         ["滚动", "多实例逐个替换", "无", "★★★", "⬜ 暂缓（需要多实例，超出小团队范围）"]]),
 ]),

dict(id="s10", num="⑩", status="design",
 title="健康检查：容器起来了 ≠ 服务能用",
 sub="新手最容易漏的一环，也是自动回滚的触发条件",
 sections=[
  dict(type="analogy", body="""
<strong>餐厅上菜不等于菜是好的。</strong><br><br>
服务员把盘子端上桌（<code>docker-compose up -d</code> 返回成功），
只说明「菜送到了」，不说明「菜没做坏」。<br><br>
健康检查就是<strong>尝一口</strong> —— 真的发一个请求，看服务是不是正常响应。"""),

  dict(type="warn", h="为什么必须有这一步：真实的失败场景", body="""
<code>docker-compose up -d</code> 返回成功，<strong>只代表「容器进程启动了」</strong>，
不代表「你的服务能正常响应请求」。"""),

  dict(type="flow", body="""真实的失败场景：
  · 服务启动 3 秒后因为配置错误崩溃
  · 服务起来了但连不上数据库，所有请求返回 500
  · 服务监听在错误的端口
  · 新版本有个 bug，首页就 panic

如果只看 docker 的返回值：
  系统报告「部署成功」 ──▶ 但用户访问全是 500
                       ──▶ 你以为没事，其实【线上已经炸了】"""),

  dict(type="flow", h="检查逻辑", body="""GET http://10.0.0.8:8080/healthz
        │
        ▼
   间隔 3 秒重试，最多 5 次
        │
   ┌────┴─────────────────────┐
   ▼                          ▼
连续 3 次返回 200          5 次都不行
   │                          │
   ▼                          ▼
健康 → deployed           失败 → 触发【自动回滚】"""),

  dict(type="kv", h="两个参数的设计理由", items=[
    ("为什么要重试", "服务启动需要时间（加载配置、连数据库、预热缓存）。刚 <span class='mono'>up -d</span> 完立刻探测，多半还没起来 —— <strong>这不代表失败</strong>。重试给了它启动的窗口"),
    ("为什么要求连续 3 次", "防止偶然一次成功就判定健康 —— 比如服务正在崩溃循环，偶尔有一次响应了。连续 3 次才算稳定")]),

  dict(type="text", body="""
<p><strong>自动回滚流程：</strong></p>"""),

  dict(type="flow", body="""健康检查失败
   │
   ▼
从部署记录里找到【上一个成功的 deployment】
   │
   ▼
用它的 image_tag 重新部署
   │
   ▼
再做一次健康检查
   │
   ├── 成功 ──▶ 状态 rolled_back，发通知
   │
   └── 还失败 ──▶ 【停下】，标记需要人工介入
                  （不要无限回滚 —— 那会变成回滚风暴）"""),

  dict(type="code", h="回滚链在数据库里是显式建模的", lang="sql", body="""<span class="k">CREATE TABLE</span> deployments (
    id                     <span class="k">INTEGER PRIMARY KEY AUTOINCREMENT</span>,
    build_id               <span class="k">INTEGER NOT NULL REFERENCES</span> builds(id),
    state                  <span class="k">TEXT NOT NULL</span>,   <span class="c">-- deploying|deployed|failed|rolled_back</span>
    image_tag              <span class="k">TEXT NOT NULL</span>,
    previous_deployment_id <span class="k">INTEGER REFERENCES</span> deployments(id),  <span class="c">-- ← 回滚目标</span>
    ...
);"""),

  dict(type="tip", h="为什么用外键而不是靠时间戳猜", body="""
<code>previous_deployment_id</code> 显式记录「回滚到哪个」。<br><br>
如果靠时间戳去猜「上一个部署是什么时候」，<strong>并发部署时时间戳可能不可靠</strong>
（两个部署几乎同时完成，谁先谁后取决于写入顺序）。<br><br>
<em>显式的关系永远比推断的关系可靠。</em>"""),
 ]),

dict(id="s11", num="⑪", status="design",
 title="状态机：整个系统的骨架",
 sub="所有环节串起来就是一张状态迁移图，以及三条设计原则",
 sections=[
  dict(type="flow", h="完整状态机", body="""        ┌──────────┐
        │ queued   │  已入队，等 worker
        └────┬─────┘
             ▼
        ┌──────────┐
        │ running  │  容器内构建中
        └────┬─────┘
        成功 │ │ 失败
      ┌──────┘ └──────┐
      ▼               ▼
┌───────────┐   ┌──────────┐
│ succeeded │   │  failed  │─ ─ ─ ─ ─ ┐ 异步，不阻塞主流程
└─────┬─────┘   └──────────┘          ┆
      ▼                               ▼
┌───────────┐              ┌────────────────┐
│ deploying │              │   diagnosed    │  虚线：只是补充信息，
└─────┬─────┘              └────────────────┘  不参与主干状态机
 成功 │ │ 失败
┌─────┘ └──────┐
▼              ▼
┌──────────┐ ┌───────────────┐
│ deployed │ │ deploy_failed │
└──────────┘ └───────┬───────┘
                     ▼
              ┌──────────────┐
              │ rolled_back  │
              └──────────────┘"""),

  dict(type="text", body="""<p><strong>三条设计原则：</strong></p>"""),

  dict(type="code", h="原则① 只允许沿边迁移，非法迁移直接拒绝", lang="go", body="""<span class="k">var</span> allowed = <span class="k">map</span>[State][]State{
    StateQueued:    {StateRunning, StateFailed},
    StateRunning:   {StateSucceeded, StateFailed},
    StateSucceeded: {StateDeploying},
    StateDeploying: {StateDeployed, StateDeployFailed},
    StateDeployFailed: {StateRolledBack, StateDeployFailed},
}

<span class="k">func</span> Transition(from, to State) <span class="k">error</span> {
    <span class="k">if</span> !contains(allowed[from], to) {
        <span class="k">return</span> fmt.Errorf(<span class="s">"非法状态迁移 %s → %s"</span>, from, to)
    }
    <span class="k">return nil</span>
}"""),

  dict(type="warn", h="为什么要这么严格：状态错乱是并发系统最难查的 bug", body="""
比如一个已经 <code>failed</code> 的构建，因为某个迟到的 goroutine 又把它改成 <code>running</code>
—— 界面上就出现<strong>「失败的构建正在运行」</strong>这种鬼故事。<br><br>
这类 bug 极难复现（依赖时序），极难排查。<br>
<strong>把迁移规则写死，非法迁移直接拒绝，能从根上消灭这一整类问题。</strong>"""),

  dict(type="code", h="原则② 每次迁移都写审计表", lang="sql", body="""<span class="k">CREATE TABLE</span> build_events (
    id          <span class="k">INTEGER PRIMARY KEY AUTOINCREMENT</span>,
    build_id    <span class="k">INTEGER NOT NULL REFERENCES</span> builds(id) <span class="k">ON DELETE CASCADE</span>,
    from_state  <span class="k">TEXT</span>,
    to_state    <span class="k">TEXT NOT NULL</span>,
    reason      <span class="k">TEXT</span>,          <span class="c">-- 为什么迁移（错误信息、谁触发的）</span>
    created_at  <span class="k">TEXT NOT NULL DEFAULT</span> (datetime(<span class="s">'now'</span>))
);"""),

  dict(type="tip", body="""
好处：出问题时可以<strong>回放</strong>这个构建的完整历史 —— 什么时候进队列、什么时候开始、为什么失败。<br><br>
这也是论文里能画「构建时序图」的数据来源，以及答辩时演示「全流程可追溯」的证据。"""),

  dict(type="text", body="""
<p><strong>原则③ 单 goroutine 串行处理同一构建的事件</strong> ——
避免多个 goroutine 同时改一个构建的状态，<em>从设计上消灭竞态，而不是靠加锁</em>。</p>
<p>「不加锁」比「加对了锁」更好：锁会带来死锁风险、性能开销，以及「我到底有没有漏加」的长期焦虑。</p>"""),

  dict(type="code", h="崩溃恢复：Reconciler 的职责", lang="text", body="""进程重启后，数据库里可能残留这样的记录：
  state = 'running'   但根本没有 goroutine 在跑它 ──▶ 「孤儿构建」

Reconciler goroutine 定期扫描：
  · running / deploying 超过 build_timeout 的 ──▶ 标记 failed(interrupted) 或按策略重试
  · 磁盘上残留的 workspace 目录            ──▶ 清理
  · 泄漏的构建容器                          ──▶ docker rm -f"""),
 ]),

dict(id="s12", num="⑫", status="design",
 title="失败诊断与 LOA：核心创新点",
 sub="人为主导的 AI 协助运维 —— 理论依据、八步机制、以及为什么小团队不能全自动",
 sections=[
  dict(type="text", body="""
<p><strong>传统 CI 与你这个系统的差别：</strong></p>"""),

  dict(type="flow", body="""传统 CI：  构建失败 ──▶ 甩给你 5000 行日志 ──▶ 自己找

GoPulse：  构建失败 ──▶ 分析日志 ──▶ 告诉你「错在哪、为什么、怎么改」
                              └──▶ 但【由你决定改不改】"""),

  dict(type="text", body="""<p>下面按<strong>八个步骤</strong>拆解，每一步都标注了它在「人主导」里扮演的角色。</p>"""),

  dict(type="code", h="第一步：日志裁剪", lang="text", body="""构建日志可能有几 MB，但 LLM 有上下文长度限制。
而且【塞太多反而效果差】── 这点有文献支撑：
  Roy et al. (FSE'24 Companion) 发现把事件讨论记录作为额外上下文喂给模型，
  性能【并未显著提升】──▶ 说明上下文堆砌无用，信息的【筛选】才是关键。

裁剪策略：
  取头部（前 ~50 行）  ──▶ 里面是「执行了什么命令」「什么环境」
      +
  取尾部（最后 8KB）   ──▶ 里面是真正的错误信息
      +
  中间用占位符省略     ──▶ "... [省略 12,847 行] ..."

为什么错误在尾部：程序是顺序执行的，崩溃发生在最后。
头部的价值是提供上下文（跑的是什么命令、哪个阶段）。"""),

  dict(type="code", h="第二步：脱敏（不能省）", lang="text", body="""日志里可能意外打印了敏感信息
  （比如某个脚本 echo $DATABASE_URL，或 npm 报错时带出 .npmrc 内容）

发给第三方 LLM API 前必须过滤：
  把该项目【所有已知的 secret 值】，在日志里替换成 [REDACTED]

否则你等于把用户的数据库密码发给了 OpenAI。"""),

  dict(type="text", body="""
<p><strong>第三步：Analyzer 圈定范围</strong> —— <em>这是「人为主导」的第一个实质机制。</em>
借鉴 k8sgpt 的思路（它把 SRE 经验固化为一个个 analyzer，官方表述是
"SRE experience codified into its analyzers"）。</p>"""),

  dict(type="code", h="核心原则：AI 不能自己决定看什么，人预先定义好", lang="yaml", body="""<span class="k">analyzer</span>: npm_install_failure
  <span class="k">触发条件</span>: 阶段 == <span class="s">"安装依赖"</span> AND 退出码 != <span class="n">0</span>
  <span class="k">可查上下文</span>:
    - 日志尾部 <span class="n">200</span> 行
    - <span class="k">package.json</span> 的 diff
    - 上次成功构建的 lockfile 哈希
  <span class="k">禁止查询</span>:
    - secrets 表
    - SSH 私钥
    - 其他项目的日志"""),

  dict(type="tip", h="Analyzer 的三重价值", body="""
<strong>① 安全</strong> —— 脱敏边界由<em>代码</em>定义，而不是靠 prompt 里写「请不要看密钥」。
prompt 约束是可以被绕过的（提示注入），代码约束不能。<br><br>
<strong>② 准确</strong> —— 缩小范围等于提高信噪比。<br><br>
<strong>③「人为主导」落地</strong> —— 人有<em>具体的装置</em>来控制 AI，而不是一句口号。
答辩时如果被问「人主导具体体现在哪」，这就是答案之一。"""),

  dict(type="text", body="""
<p><strong>第四步：LOA 策略决策。</strong>LOA = Level of Automation（自动化级别），
出自 Sheridan 的十级量表。理论依据是 <strong>Parasuraman, Sheridan &amp; Wickens (2000)</strong> 的模型 ——
自动化不是「全有或全无」，而是<em>四类功能各自独立地可以调自动化程度</em>：</p>"""),

  dict(type="table", h="四类功能 × 本系统的自动化级别", cols=["功能类型", "在 GoPulse 里对应", "自动化级别", "理由"],
   rows=[["信息获取", "收集构建日志、容器退出码、diff、历史失败", "<strong>高</strong>", "人不该干这个，纯机械"],
         ["信息分析", "日志裁剪、错误聚类、根因推断", "<strong>高</strong>", "LLM 的主场"],
         ["<strong>决策选择</strong>", "采纳哪个修复方案、是否回滚", "<strong>低（LOA 4）</strong>", "<strong>人主导</strong> —— AI 只提议"],
         ["<strong>行动执行</strong>", "改代码、重跑构建、部署", "<strong>最低</strong>", "<strong>人执行</strong> —— AI 不碰代码"]]),

  dict(type="tip", h="这个框架的价值：把口号变成可量化的设计决策", body="""
有了它，「人为主导」不再是模糊说法，而是可以精确表述的：<br><br>
<em>「本系统在信息获取与信息分析环节采用高自动化级别（Sheridan LOA 6–7），
在决策选择与行动执行环节刻意保留人的主导权（LOA 2–4）。」</em><br><br>
对照：LogSage（ASE 2025）那类端到端方案在决策环节接近 LOA 7–8。<br>
<strong>你不是做得少，是刻意在不同功能维度上选择了不同的自动化级别。</strong>"""),

  dict(type="table", h="Sheridan 十级量表（本系统用到的档位）", cols=["!LOA", "含义", "本系统"],
   rows=[["!2", "计算机建议多种做法", "诊断卡列出多个可能原因"],
         ["!4", "计算机选一种，<strong>人批准后执行</strong>", "<strong>← 默认档</strong>"],
         ["!6", "自动执行后必须告知人", "依赖小版本更新 + 通知"],
         ["!7", "自动执行，事后可审计", "知识库已验证 ≥3 次的已知失败"],
         ["!8", "自动执行并忽略人", "<span class='no'>本系统【永不启用】</span>"]]),

  dict(type="text", body="""
<p><strong>第五步：为什么小团队反而不能全自动</strong> —— <em>这是你的核心论证，有 CCF-A 顶会的实证支撑。</em></p>"""),

  dict(type="kv", h="Zhou et al., ICSE 2026（CCF-A）的实测数据", items=[
    ("研究对象", "混合方法：14 名开发者观察 + 22 名问卷"),
    ("认知偏差比例", "<strong>48.8%</strong> 的开发者动作存在认知偏差，其中 <strong>56.4%</strong> 与 LLM 交互相关"),
    ("撤销率", "LLM 相关动作的撤销率 <strong>29.46%</strong>（238/808），统计显著高于非 LLM 动作"),
    ("学术贡献", "建立了 90 种偏差 / 15 类的 taxonomy，经认知心理学家验证")]),

  dict(type="flow", h="论证链（论文里可以这样写）", body="""LLM 建议的撤销率偏高（近三成要回退）
        │
        ▼
全自动采纳会产生「看起来在修、实际在返工」的【隐性成本】
        │
        ▼
小团队【没有专职 SRE】复核 AI 结论
        │
        ▼
但【开发者本人就在场】，且有完整业务上下文
        │
        ▼
∴ 把决策权留给人，在小团队场景下【不是妥协，而是效率最优解】"""),

  dict(type="text", body="""
<p>另有 <strong>automation bias（自动化偏见）</strong>的研究支撑（Romeo &amp; Conti, <em>AI &amp; Society</em>）：
给出决策建议时，人会更少审视附加信息 —— <em>全自动会放大这个效应</em>。</p>"""),

  dict(type="text", body="""
<p><strong>第六步：证据链强制绑定</strong> —— <em>「人为主导」的第二个实质机制。</em>
诊断输出<strong>不能是一段散文</strong>，必须是结构化断言 + 可点击的日志行号：</p>"""),

  dict(type="code", lang="json", body="""{
  <span class="k">"root_cause"</span>: <span class="s">"TypeScript 类型检查失败"</span>,
  <span class="k">"evidence"</span>: [
    {
      <span class="k">"claim"</span>: <span class="s">"tsc 报告类型错误 TS2345"</span>,
      <span class="k">"log_lines"</span>: [<span class="n">41</span>, <span class="n">42</span>],
      <span class="k">"verbatim"</span>: <span class="s">"src/api/client.ts:42:18 - error TS2345: ..."</span>
    },
    {
      <span class="k">"claim"</span>: <span class="s">"错误位置正是本次提交修改的行"</span>,
      <span class="k">"diff_hunk"</span>: <span class="s">"src/api/client.ts:42"</span>
    }
  ],
  <span class="k">"suggestion"</span>: <span class="s">"读取环境变量后显式转换：const port = Number(process.env.PORT ?? 3000)"</span>,
  <span class="k">"confidence_basis"</span>: <span class="s">"错误信息与本次 diff 修改位置一致"</span>
}"""),

  dict(type="tip", h="这个设计对抗的正是 automation bias", body="""
前端把 <code>log_lines</code> 渲染成<strong>可点击跳转到日志终端对应行</strong>的链接。<br><br>
所以人不是在读结论，而是在<strong>验证据</strong>。<br><br>
而且它给了你一个别人没有的可测量指标：<em>证据定位准确率</em>（AI 引用的行号里是否真的包含该错误）。"""),

  dict(type="warn", h="为什么刻意不显示百分比置信度", body="""
原始设计稿写「置信度 99.4%」，已改掉。<br><br>
因为<strong>那个数字无法解释是怎么算出来的</strong> —— LLM 不会输出校准过的概率，
你也没有 ground truth 去标定它。答辩时一句「这个 99.4% 怎么来的」就能问穿。<br><br>
改成 <code>confidence_basis</code>（定性说明依据），<em>可辩护 &gt; 好看</em>。"""),

  dict(type="text", body="""
<p><strong>第七步：知识库与 LOA 动态演进</strong> —— <em>「人为主导」的第三个机制，也是最有意思的一环。</em>
<strong>人不只是「批准者」，人是「训练者」。</strong></p>"""),

  dict(type="flow", h="演进闭环", body="""开发者看完诊断 ──▶ 点 ✅准确 / ⚠️部分准确 / ❌无关
                          │
                          ▼
        标记为准确的 ──▶ 沉淀成【已验证三元组】
                          (错误特征 → 根因 → 修复动作)
                          │
                          ▼
              下次同类失败 ──▶ 先查知识库
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
   命中且 verified_count ≥ 3      未命中
              │                        │
              ▼                        ▼
   LOA 自动升到 7               LOA 4，调 LLM
   无需调 LLM，直接自动处理      通知人审批
              │
              ▼
   自动处理连续失败 2 次 ──▶ 【熔断】自动降回 LOA 4"""),

  dict(type="kv", h="三重好处", items=[
    ("降成本", "命中知识库不调 API，省 token 也省时间"),
    ("提可信度", "建议附带「本团队已验证 3 次」，比裸的 AI 输出可信得多"),
    ("解决冷启动", "Hassan &amp; Wang 那类机器学习方法需要历史数据训练，<strong>新项目根本用不了</strong>；本方案靠人在使用中逐步积累，<em>第一天就能用</em>")]),

  dict(type="tip", h="这就是「全自动托管模式」的正确实现方式", body="""
它<strong>不是与人主导对立的另一个开关</strong>，而是<em>人主导积累到一定程度后自然演化出的状态</em>。<br><br>
答辩时这个逻辑闭环很有力：<br>
&nbsp;&nbsp;「全自动模式会不会和你的『人为主导』创新点矛盾？」<br>
&nbsp;&nbsp;→「不矛盾。全自动的能力<strong>来自</strong>人主导阶段积累的已验证知识。
人是自动化的训练者，自动化级别随验证次数演进 —— 这正是 Parasuraman 模型里
adaptive automation（自适应自动化）的具体实现。」"""),

  dict(type="table", h="全自动模式的安全边界（这条务必守住）", cols=["全自动<strong>可以</strong>做", "全自动<strong>永不</strong>做"],
   rows=[["重试已知瞬态失败（网络抖动、镜像拉取超时）", "<span class='no'>生成并应用 AI 新写的代码补丁</span>"],
         ["应用<strong>已验证过的</strong>修复动作（知识库里有）", "<span class='no'>修改 secrets、SSH 密钥、部署凭据</span>"],
         ["健康检查失败后自动回滚到前序版本", "<span class='no'>删除数据、清理卷、强制覆盖</span>"],
         ["依赖小版本更新 + 全量测试通过后部署", "<span class='no'>未通过健康检查就继续推进</span>"],
         ["发通知、生成日报", "<span class='no'>跨越审批门槛的破坏性操作"]]),

  dict(type="text", body="""
<p><strong>判据：</strong>全自动只执行<em>「确定性的、已验证的、可回滚的」</em>动作。
凡是需要生成新内容的，一律回到 LOA 4。</p>
<p>配套<strong>六道护栏</strong>：① 动作白名单（AI 无法发明新动作）② 熔断降级 ③ 每日预算限制
④ 全量审计可回放 ⑤ <strong>默认关闭</strong>（新项目默认 LOA 4，全自动需人显式开启）⑥ 破坏性动作不可提权。</p>"""),

  dict(type="code", h="第八步：为什么诊断必须异步", lang="text", body="""构建失败 ──▶ 状态【立刻】置为 failed ──▶ 界面立刻显示失败
                    │
                    └──▶ 另开一个 goroutine 调 LLM（可能要 30 秒）
                              │
                              ▼
                    完成后把结果补写进记录，界面更新出诊断卡
                    （状态标记为 diagnosed，虚线状态，不改主干）

理由：
  · 用户最想知道的是「我的构建失败了」，这个必须【立刻】告诉他
  · 诊断是补充信息，不该让他多等 30 秒
  · LLM API 会超时、会挂 ──▶ 【诊断失败绝不能影响构建结果的正确性】"""),

  dict(type="table", h="测试失败为什么要单独一个 analyzer（LOA 4 而非更高）", cols=["失败类型", "!Analyzer", "!默认 LOA", "理由"],
   rows=[["编译 / 类型错误", "!build_compile_failure", "!4", "修复需改代码，必须人判断"],
         ["<strong>单元测试失败</strong>", "!unit_test_failure", "!<strong>4</strong>",
          "<strong>最危险的一类</strong> —— 可能是代码错，也可能是测试本身该改"],
         ["依赖安装失败", "!dependency_failure", "!6–7", "常见瞬态（网络 / registry）"],
         ["超时", "!timeout_failure", "!7", "确定性可重试"]]),

  dict(type="tip", h="单元测试失败是「人为主导」最有力的应用场景", body="""
测试失败有<strong>两种完全相反的成因</strong>：<br>
&nbsp;&nbsp;① 代码引入了 bug → 该修代码<br>
&nbsp;&nbsp;② 需求变了 → 该改测试<br><br>
<strong>AI 无法可靠区分这两者</strong>，而这恰恰是 Zhou et al. 那 29.46% 撤销率的主要来源之一。<br>
<em>人在这里有不可替代的判断力。</em>"""),
 ]),

dict(id="s13", num="⑬", status="done",
 title="前端：把这一切呈现出来",
 sub="SPA 原理、分层架构、以及「用架构消灭一类 bug」的三个实例",
 sections=[
  dict(type="analogy", body="""
<strong>SPA（单页应用）vs 传统网站</strong><br><br>
传统网站：每点一个链接就向服务器要一个新 HTML 页面，整页刷新、白屏一下 —— 像翻一本书，每次翻页都要重新拿书。<br>
SPA：<strong>只加载一次</strong>，之后所有「翻页」都由 JavaScript 在浏览器里替换内容 —— 像用平板看电子书，点了就换，不白屏。<br><br>
代价：需要<strong>前端路由</strong>（<code>vue-router</code>）来管理 URL 和页面的对应关系。"""),

  dict(type="kv", h="技术栈", items=[
    ("框架", "Vue 3（Composition API + <span class='mono'>&lt;script setup&gt;</span>）"),
    ("构建", "Vite 6 —— 开发时热更新毫秒级，生产构建 Rollup 打包"),
    ("语言", "TypeScript —— <strong>types.ts 是前后端契约的唯一事实来源</strong>"),
    ("样式", "Tailwind CSS（<strong>本地编译，不依赖 CDN</strong>）"),
    ("图标", "34 个内联 SVG —— 不依赖 Google Fonts，断网也能显示"),
    ("测试", "Vitest + @vue/test-utils + jsdom，23 文件 / 167 用例 / 95.9% 覆盖率")]),

  dict(type="code", h="目录分层：每一层只依赖它下面的层", lang="text", body="""src/
├── types.ts          ← 所有数据结构的 TS 定义（唯一事实来源）
├── api/
│   ├── client.ts     ← HTTP 封装：超时、重试、abort、错误归一化
│   ├── index.ts      ← 17 个 API 方法
│   └── mock.ts       ← 假数据（开发时用，也是【验收样例】）
├── composables/      ← 可复用的响应式逻辑
│   ├── useAsync.ts       通用异步：loading / error / data / 取消
│   ├── useLogStream.ts   SSE 日志流 + 环形缓冲
│   └── usePolling.ts     定时轮询（卸载即停）
├── components/
│   ├── layout/       ← 顶栏、侧栏、状态栏（全局共用【一份】）
│   └── ui/           ← StatusBadge、LogTerminal、StageList…
└── views/            ← 13 个页面

依赖方向：views ──▶ components ──▶ composables ──▶ api ──▶ types
          【没有循环依赖，改一处不会波及全局】"""),

  dict(type="tip", h="关键设计：契约先行（Contract-First）", body="""
<code>types.ts</code> 和 <code>openapi.yaml</code> 定义了前后端之间的<strong>数据契约</strong>。<br><br>
前端按契约写好，用 <code>mock.ts</code> 提供假数据先跑通；后端按同一份契约实现；联调时开关一拨：<br>
<code style="background:#1a2743">VITE_USE_MOCK=false</code> → 从假数据切到真后端<br><br>
<strong>价值：</strong>前后端可以完全<em>并行开发，互不阻塞</em>。
这也是交接文档里反复强调「以 types.ts 为契约」的原因 ——
<code>mock.ts</code> 同时充当<strong>验收样例</strong>：后端返回与 mock 同形状的数据，167 个测试断言的一切天然成立。"""),

  dict(type="text", body="""<p><strong>三个「用架构消灭一类 bug」的实例</strong> —— 这些是设计稿里真实存在的问题：</p>"""),

  dict(type="warn", h="实例① 面包屑：13 个页面全部硬编码成同一个字符串", body="""
原始设计稿（Stitch 生成）里，13 个页面的顶栏面包屑<strong>全部写死</strong>为
<code>项目 / web-api / 构建 #1091</code> —— 所以在<strong>项目列表页</strong>也显示「构建 #1091」，明显错误。<br><br>
逐个改 13 处？不，那样以后新增页面还会犯同样的错。"""),

  dict(type="code", h="改成从路由元信息自动生成 —— 让这类 bug 不可能发生", lang="ts", body="""<span class="c">// 路由定义时声明</span>
{ path: <span class="s">'/projects'</span>,            meta: { crumb: [<span class="s">'项目'</span>] } }
{ path: <span class="s">'/projects/:id/builds'</span>, meta: { crumb: [<span class="s">'项目'</span>, <span class="s">'web-api'</span>, <span class="s">'构建历史'</span>] } }
{ path: <span class="s">'/builds/:n/diagnosis'</span>, meta: { crumb: [<span class="s">'项目'</span>, <span class="s">'web-api'</span>, <span class="s">'构建'</span>] } }

<span class="c">// 顶栏组件读 route.meta.crumb 渲染</span>
<span class="c">// ──▶ 每页天然正确，【不可能写错】，新增页面自动就有</span>"""),

  dict(type="tip", body="""
<strong>这是「用架构消灭一类 bug」的典型例子</strong> ——
不是修好 13 处，而是让这 13 处<em>不可能出错</em>。<br><br>
同样的思路还解决了：<br>
&nbsp;&nbsp;· <strong>实例②</strong> 13 个页面都没有 <code>&lt;title&gt;</code> → 改为 <code>router.afterEach</code> 统一设置<br>
&nbsp;&nbsp;· <strong>实例③</strong> 顶栏/侧栏/状态栏在 13 个文件里各复制一份 → 抽成 <code>components/layout/</code> 四个组件<br><br>
而且这三条都写成了<strong>回归测试</strong>，以后改坏了会立刻被测出来。"""),

  dict(type="table", h="另外两个值得一提的实现细节", cols=["细节", "原理"],
   rows=[["前端也有环形缓冲", "<span class='mono'>useLogStream</span> 里同样限制日志行数，超出丢最旧的 —— 长时间开着页面看日志，不能把浏览器内存吃光"],
         ["组件卸载即停止轮询", "<span class='mono'>usePolling</span> 在 <span class='mono'>onUnmounted</span> 里清理定时器。不清理的话，你切走了页面后台还在每秒请求一次 —— <strong>内存泄漏 + 无效请求</strong>"]]),

  dict(type="warn", h="这个测试抓到的真 bug：侧栏高亮错位", body="""
<code>AppSidebar</code> 原本用「第一个前缀命中」匹配路径："""),

  dict(type="flow", body="""访问 /projects/1/secrets
     │
     ▼  遍历导航项
'/projects' 先命中 startsWith ──▶ 返回 '/projects'
     │
     ▼
侧栏高亮的是【项目列表】，不是【密钥管理】   ✗

修法：改成【最长匹配】，并让 /builds/* 归到「构建历史」
     （否则构建详情页没有任何高亮项）

──▶ 这个 bug 是【测试自己抓出来的】，写代码时没意识到"""),
 ]),

dict(id="s14", num="⑭", status="design",
 title="数据是怎么存的",
 sub="8 张基础表 + 6 张 LOA 表，以及密钥加密的原理",
 sections=[
  dict(type="table", h="8 张基础表", cols=["!表名", "存什么", "设计要点"],
   rows=[["!users", "用户", "bcrypt/argon2 密码哈希，<strong>不存明文</strong>"],
         ["!projects", "项目", "仓库地址、检测类型、pipeline 覆盖、超时配置、<strong>git 凭据（加密）</strong>"],
         ["!deploy_hosts", "部署目标", "地址、<strong>加密私钥</strong>、<strong>主机公钥指纹</strong>、健康检查配置"],
         ["!secrets", "项目级环境变量", "AES-GCM 加密成 BLOB"],
         ["!builds", "构建", "状态、触发源、SHA、<strong>pipeline 快照</strong>、诊断结果"],
         ["!build_events", "状态迁移审计", "from/to/reason/时间 —— 支持完整回放"],
         ["!deployments", "部署记录", "含 <span class='mono'>previous_deployment_id</span> <strong>回滚链</strong>"],
         ["!log_chunks", "日志分块", "BLOB 可压缩，<span class='mono'>UNIQUE(build_id, seq)</span>"]]),

  dict(type="table", h="分工原则：什么数据放哪里", cols=["数据类型", "存哪", "为什么"],
   rows=[["结构化元数据", "SQLite", "要查询、要索引、要事务"],
         ["日志正文", "<span class='mono'>log_chunks</span> BLOB", "大文本，一行一存会撑爆主表"],
         ["构建产物（镜像）", "Docker registry / 本地磁盘", "二进制大文件不进数据库"],
         ["密钥", "数据库，但 <strong>AES-GCM 加密</strong>", "见下"]]),

  dict(type="text", body="""
<p><strong>密钥加密的原理。</strong>AES-GCM 是「认证加密」，同时提供两个保证：</p>"""),

  dict(type="kv", items=[
    ("加密 (confidentiality)", "没密钥看不懂"),
    ("认证 (integrity)", "内容被改过<strong>会发现</strong>（GCM 自带认证标签，篡改即校验失败）")]),

  dict(type="code", h="主密钥从哪来 —— 这是安全设计的关键", lang="yaml", body="""<span class="c"># config.yaml</span>
<span class="k">crypto</span>:
  master_key_env: <span class="s">"DEVOPS_MASTER_KEY"</span>    <span class="c"># ← 只是【变量名】，不是值</span>

<span class="c"># 真正的密钥在环境变量里，由部署时注入：</span>
<span class="c">#   export DEVOPS_MASTER_KEY="***"</span>
<span class="c">#</span>
<span class="c"># 【绝不写进数据库，绝不写进配置文件】</span>"""),

  dict(type="tip", h="为什么要这样分离", body="""
数据库文件可能被<strong>备份、被拷走、被误提交到 git</strong>。<br><br>
如果密钥也在里面，等于<em>锁和钥匙放在同一个抽屉</em>。<br><br>
分离之后：<strong>光有数据库文件，拿不到任何明文。</strong><br><br>
这也是为什么 <code>DEPENDENCIES.md</code> 里所有敏感配置项都写成 <code>*_env</code>（存变量名）而不是存值。"""),

  dict(type="code", h="为什么选 SQLite 而不是 PostgreSQL", lang="text", body="""驱动：modernc.org/sqlite  ──▶ 【纯 Go 实现，无 CGO】

这一点是决定性的：
  · 有 CGO  → 交叉编译困难，Windows 上构建要装 gcc，单二进制分发变复杂
  · 纯 Go   → GOOS=linux GOARCH=amd64 go build 一条命令出 Linux 二进制
            ──▶ 真的能做到「scp 上去就能跑」

小团队场景下单机 SQLite 完全够用（几万条构建记录毫无压力），
需要时可通过 store 接口切换到 PostgreSQL（sqlc 支持双方言）。"""),
 ]),

dict(id="s15", num="⑮", status="design",
 title="整个系统的进程模型",
 sub="为什么「单二进制」是这个项目最重要的卖点之一",
 sections=[
  dict(type="flow", h="一个二进制 devopsd 内部", body="""一个二进制 devopsd
│
├── HTTP 服务器（每请求一个 goroutine）
│     ├── REST API
│     ├── SSE 日志流
│     └── Webhook 接收
│
├── Scheduler goroutine（1 个）
│     └── 循环：从 DB 原子认领 queued 任务 ──▶ 丢进 pool
│
├── Worker Pool（N 个，信号量限流，默认 4）
│     └── 每个构建一个 goroutine
│           ├── 检出代码（Go 侧，持凭据）
│           ├── 起容器执行（Docker SDK）
│           ├── 日志读取 goroutine
│           ├── 日志落库 goroutine
│           ├── 部署（SSH）
│           └── 失败时：诊断 goroutine（调 LLM）
│
├── Reconciler goroutine（1 个）
│     └── 定期：清理超时任务、恢复孤儿构建、删过期 workspace
│
└── Signal handler（1 个）
      └── 收到 SIGTERM ──▶ 停止取新任务 ──▶ 等在跑的完成（宽限期 5 分钟）──▶ 退出"""),

  dict(type="table", h="对比：部署一个 CI 系统需要什么", cols=["", "!Jenkins", "!GoPulse"],
   rows=[["运行时", "需要装 Java（JRE/JDK）", "<span class='yes'>无（静态二进制）</span>"],
         ["数据库", "通常另装一个", "<span class='yes'>一个 SQLite 文件</span>"],
         ["插件", "装一堆插件，版本冲突是常态", "<span class='yes'>无插件概念</span>"],
         ["配置", "web 界面点很多下 + Jenkinsfile", "<span class='yes'>一个 config.yaml</span>"],
         ["部署方式", "war 包丢进 servlet 容器", "<span class='yes'><span class='mono'>scp devopsd &amp;&amp; ./devopsd</span></span>"],
         ["空闲内存", "数百 MB 起", "<span class='yes'>对标 Woodpecker：server ≈100MB</span>"]]),

  dict(type="tip", h="优雅关闭为什么重要", body="""
如果你 <code>kill</code> 掉进程时正好有构建在跑，<strong>容器会变成孤儿</strong> ——
没人清理，占着磁盘和内存，跑上几十次就把机器塞满了。<br><br>
收到 SIGTERM 后：停止接新任务 → 等在跑的完成（给 5 分钟宽限期）→ 清理 → 退出。<br>
<em>这就是 <code>sync.WaitGroup</code> 在 Pool 里的用途。</em>"""),
 ]),
]

MAINLINES = [
 dict(title="主线一：宁可失败，不可静默错误",
   pre="""队列满       → 返回 503，不硬塞进内存
检出不到 SHA → 标记失败，绝不悄悄用分支最新代码
健康检查不过 → 回滚，绝不报告「部署成功」
慢订阅者     → 丢日志行并计数，绝不阻塞构建
诊断失败     → 不影响构建结果，绝不用假数据填充""",
   body="CI 系统的信任来自于「它不会骗你」。一次「显示成功但线上是坏的」就能让用户永远不再信任它。"),
 dict(title="主线二：机器做机械的事，人做判断的事",
   pre="""机器做：收集日志、裁剪、脱敏、调 LLM
        匹配知识库、执行【已验证】的动作

人做：  决定采纳哪个建议
        判断「是代码错了还是测试该改」
        批准破坏性操作

而人做的判断会被沉淀成知识库
   ──▶ 让机器下次能自动做
       ↑ 这就是 LOA 动态演进""",
   body="「人为主导」不是能力不足的妥协，而是基于 ICSE'26 实证数据（29.46% 撤销率）的效率最优解。"),
 dict(title="主线三：一切可追溯",
   pre="""pipeline_json 快照 → 当时到底跑了什么命令
build_events 审计  → 状态怎么变的、为什么
log_chunks         → 完整的原始输出
deployments 回滚链 → 上一个版本是哪个
diagnosis 证据链   → AI 为什么这么说，行号可点开验证
automation_audit   → 自动执行了什么、依据哪条规则""",
   body="这既是工程要求（出问题能查），也是学术要求 —— 论文里的实验数据全部从这些表来。"),
]
