# -*- coding: utf-8 -*-
"""部署形态可视化 · 内容 I：三形态定义 + 接口层 + 13 步流水线对比
所有实测断言均在本机验证过（见 dm_content2.EVIDENCE），设计推断单独标注。"""

# ============ 三个形态 ============
# body: 拓扑图主体行（右边框由生成器按显示宽度自动闭合，避免手工对齐错误）
TOPOLOGIES = [
    dict(
        id="personal", num="形态 Ⅰ", name="个人开发者版", en="profile: personal",
        slogan="零公网 · 零成本 · 可完全离线",
        box="你的笔记本（唯一一台机器）",
        body=[
            "本地 git 仓库  ~/code/web-api",
            "  │  commit → .git/HEAD · refs/heads/* 变化",
            "  ▼",
            "devopsd（Wails 桌面 App，或 localhost:8080 服务 + 浏览器）",
            "  ├─ LocalWatchTrigger   fsnotify 监视 .git/ · 防抖 2s · 轮询兜底 5s（77ms/次，实测）",
            "  ├─ git archive <sha>   干净快照：零凭据 · 零网络 · 不含 .git（实测）",
            "  ├─ 本机 Docker 构建    --cpus 2 · max_concurrency 2（给 IDE 留资源）",
            "  ├─ LogPipe → SSE       浏览器实时日志（环形缓冲 + 慢订阅者丢弃）",
            "  ├─ DeployTarget(local) docker compose up -d（目标 = localhost）",
            "  ├─ 健康检查            http://localhost:8080/healthz · 失败自动回滚",
            "  └─ LOA 引擎            失败 → analyzer → LLM（云 API 或本地 Ollama）",
            "",
            "数据目录：%APPDATA%/GoPulse/（devops.db + artifacts + logs，整目录即全部状态）",
        ],
        facts=[
            ("代码源", "本地 git 仓库（你本来就在用的工作目录，无需 push）"),
            ("触发", "fsnotify 监视 .git/HEAD 与 refs/heads/*，防抖 2s；5s 轮询 rev-parse HEAD 兜底"),
            ("检出", "git archive &lt;sha&gt; | tar -x —— 不需要任何 git 凭据"),
            ("部署", "compose-local（127.0.0.1），无 SSH"),
            ("公网暴露", "无 —— 零入站端口，无需域名/证书/穿透"),
            ("月成本", "0"),
            ("适用", "独立开发者、学生项目、离线环境"),
            ("交付角色", "✅ 交付物（离线 E2E 验收）；答辩可现场演示：全链路离线，不依赖教室网络"),
        ],
        risks=[
            ("构建抢开发机资源", "容器限额 --cpus/--memory + max_concurrency=2；可选「专注模式」（检测输入活动时暂缓自动触发）"),
            ("依赖容器引擎", "Windows/macOS 需 Docker Desktop（个人/教育免费，官方 license 已核实）或 podman；Linux 原生 Docker"),
            ("笔记本非 7×24", "自动触发仅在开机时生效；合盖期间错过的 commit 由轮询兜底在唤醒后补触发（SHA 幂等去重防重复）"),
        ],
    ),
    dict(
        id="lite", num="形态 Ⅱ", name="简易团队版", en="profile: team-lite",
        slogan="蹭已有的生产服务器 · 增量成本为零",
        box="生产服务器（唯一一台机器，自带公网 IP）",
        body=[
            "GitHub ──webhook POST──▶ http://<公网IP>:8080/api/webhooks/github",
            "  │  HMAC-SHA256 验签（纯 HTTP + 裸 IP 即可，GitHub 官方支持，已核实）",
            "  ▼",
            "devopsd :8080（与生产服务同机，防火墙仅放行这一个端口）",
            "  ├─ WebhookTrigger      验签 → 事件归一化 → (repo,sha,ref) 幂等入队 → 立即 202",
            "  ├─ git fetch <sha>     远程检出：GIT_CONFIG_COUNT 注入凭据，不落盘不进 argv（实测）",
            "  ├─ Docker 构建         --cpus 1.5 --memory 1g · max_concurrency 1（串行，给生产留余量）",
            "  ├─ 构建前磁盘水位检查   低于阈值拒绝入队（防止构建塞满磁盘拖垮生产）",
            "  ├─ DeployTarget(local) compose up -d（deploy_hosts.addr = 127.0.0.1，跳过 SSH）",
            "  ├─ 健康检查            http://localhost:8080/healthz · 失败自动回滚上一版本镜像",
            "  └─ LOA 引擎            审批队列开始有「他人」—— 同事批准，知识库团队验证",
            "",
            "团队 2–5 人共享同一个 Web UI（多用户 + 简单角色）",
        ],
        facts=[
            ("代码源", "GitHub（必须先 push —— 这是与形态Ⅰ的本质区别）"),
            ("触发", "GitHub webhook → 公网 IP 直达，无需域名/证书/反代/穿透（最小配置 4 件事）"),
            ("检出", "git fetch &lt;sha&gt;，凭据走 §3.7 的 GIT_CONFIG_COUNT 方案"),
            ("部署", "compose-local：目标就是本机，镜像零传输"),
            ("公网暴露", "仅 :8080（webhook + UI 同端口）；建议防火墙限源"),
            ("月成本", "0（复用已在付费的生产服务器）"),
            ("适用", "2–5 人小团队，已有生产服务器，项目为轻服务"),
            ("交付角色", "✅ 交付物 · 论文代表场景（合设 E2E 验收）；现场演示可用 curl 模拟 webhook + 本机 toy 服务离线跑通，真 GitHub 联动录屏备用"),
        ],
        risks=[
            ("构建与生产抢资源（本形态最大风险）", "max_concurrency=1 强制串行 + 容器 CPU/内存限额 + 磁盘水位检查；重构建项目应升级形态Ⅲ"),
            ("构建尖峰影响线上响应", "构建窗口可配置（如避开业务高峰）；健康检查失败自动回滚兜底"),
            ("同机安全边界", "构建容器不挂 docker.sock、代码只读挂载（既有设计），容器逃逸不等于生产数据沦陷"),
        ],
    ),
    dict(
        id="full", num="形态 Ⅲ", name="完整团队版", en="profile: team-full",
        slogan="构建与生产分离 · 现有 ARCHITECTURE.md 的主体蓝图",
        box="构建 VPS（1–2 核即可）",
        body=[
            "GitHub / GitLab ──webhook──▶ devopsd :8080",
            "  ├─ WebhookTrigger      验签 → 幂等入队 → 202（同形态Ⅱ）",
            "  ├─ git fetch <sha>     远程检出（同形态Ⅱ）",
            "  ├─ Docker 构建         max_concurrency 4（专机专用，可并行）",
            "  ├─ 镜像 tag = commit SHA（不可变，回滚秒级）",
            "  └─ LOA 引擎 + 知识库 + 审批队列 + RBAC（完整团队语义）",
        ],
        box2="目标主机 ×N（生产 / 预发 / 测试）",
        body2=[
            "构建 VPS ──docker save | ssh docker load──▶ 目标机（无需私有 registry）",
            "  ├─ SSH 部署            FixedHostKey 强校验（拒绝 InsecureIgnoreHostKey）",
            "  ├─ compose up -d       current → releases/<sha> 软链切换",
            "  ├─ 健康检查            目标机 URL · 连续 3 次 200 判成功",
            "  └─ 失败自动回滚        previous_deployment_id 显式回滚链 · 保留最近 K 版",
        ],
        facts=[
            ("代码源", "GitHub / GitLab（webhook 双平台解析归一化）"),
            ("触发", "webhook（同形态Ⅱ）"),
            ("检出", "git fetch &lt;sha&gt;（同形态Ⅱ）"),
            ("部署", "ssh-remote：docker save | ssh docker load 流式传输，省掉私有 registry 组件"),
            ("公网暴露", "构建机 :8080 入站；目标机仅 SSH（22）入站且限构建机源 IP"),
            ("月成本", "构建 VPS ×1（目标机是本来就有的生产机）"),
            ("适用", "正式团队、多项目、多目标环境、构建较重"),
            ("交付角色", "✅ 交付物（SSH E2E 验收，WSL2 发行版可充当目标机）；论文「可扩展性」论述"),
        ],
        risks=[
            ("多一台机器的运维", "仍是单二进制 + SQLite：scp 两个文件即完成迁移（见「演进路径」）"),
            ("镜像传输带宽", "save|ssh load 为流式 gzip；大镜像首次传输慢，增量层复用后收敛"),
            ("SSH 凭据管理", "私钥 AES-GCM 加密入库 + host key 强校验（§3.6/§3.7 既有设计）"),
        ],
    ),
]

# ============ 13 步流水线对比（diff=True 的行即形态差异所在） ============
PIPELINE = [
    (1,  "触发事件",     "监视本地 .git/（fsnotify+防抖+轮询兜底）", "GitHub webhook POST", "GitHub/GitLab webhook POST", True),
    (2,  "真实性校验",   "无需（本地磁盘读取，不存在伪造通道）",     "HMAC-SHA256 验签",   "HMAC-SHA256 验签",           True),
    (3,  "幂等入队",     "(repo,sha,ref) 去重 → builds 表 queued",  "同左",               "同左",                       False),
    (4,  "调度认领",     "UPDATE…RETURNING 原子认领 · 同项目串行",   "同左",               "同左",                       False),
    (5,  "代码检出",     "git archive &lt;sha&gt;（零凭据零网络）",   "git fetch &lt;sha&gt;（凭据注入）", "git fetch &lt;sha&gt;（凭据注入）", True),
    (6,  "检测+快照",    "规则引擎识别项目类型 → pipeline_json 快照", "同左",               "同左",                       False),
    (7,  "容器构建",     "Docker 隔离 · 限额 2cpu",                  "Docker 隔离 · 限额 1.5cpu/1g", "Docker 隔离 · 并行 ×4",  False),
    (8,  "实时日志",     "LogPipe 环形缓冲 → SSE 扇出 → 批量落库",    "同左",               "同左",                       False),
    (9,  "产物镜像",     "commit 为 web-api:&lt;sha&gt;（本机 daemon）", "同左",             "同左",                       False),
    (10, "部署",         "compose-local（localhost）",               "compose-local（127.0.0.1）", "save|ssh load → 远程 compose", True),
    (11, "健康检查",     "http://localhost:8080/healthz",            "http://localhost:8080/healthz", "目标机 URL · 重试 5 次",  False),
    (12, "失败诊断",     "LOA 决策 → analyzer → LLM（可本地 Ollama）", "LOA → analyzer → LLM", "LOA → analyzer → LLM",       False),
    (13, "回滚",         "上一版本镜像 · 软链切换 · 秒级",            "同左",               "同左（经 SSH）",              False),
]

# ============ 接口层：全系统仅有的三个解耦点 ============
INTERFACES_GO = '''// internal/core/ports.go —— 核心只定义接口，不知道任何形态的存在

// 差异点 1：任务从哪来
type TriggerSource interface {
    Kind() string                                        // "local-watch" | "webhook" | "manual"
    Watch(ctx context.Context, p *Project,
          emit func(BuildRequest)) error                 // 发现新任务即 emit；阻塞直到 ctx 取消
}

// 差异点 2：代码怎么到手
type CheckoutStrategy interface {
    Fetch(ctx context.Context, req CheckoutRequest) (workspace string, err error)
    // CheckoutRequest{ Repo, Ref, CommitSHA }  → workspace 为干净快照目录（保证不含 .git）
}

// 差异点 3：产物怎么上线
type DeployTarget interface {
    Deploy(ctx context.Context, req DeployRequest) error // 镜像 tag + compose 配置 → 上线
    HealthCheck(ctx context.Context) (ok bool, err error)
    Rollback(ctx context.Context, to DeploymentID) error
}'''

WIRING_GO = '''// cmd/devopsd/main.go —— 全系统唯一知道「形态」的地方
func wire(cfg *config.Config) (*App, error) {
    var trig []core.TriggerSource
    switch cfg.Profile.Trigger {            // ← 全部形态分支收敛于这一个 switch
    case "local-watch":
        trig = append(trig, localwatch.New(cfg.Repo))       // fsnotify + 轮询兜底
    case "webhook":
        trig = append(trig, webhook.New(cfg.Server, store)) // chi 路由 POST /api/webhooks/*
    }
    trig = append(trig, manual.New(store))                  // 手动按钮：三形态都有

    var checkout core.CheckoutStrategy
    switch cfg.Profile.Checkout {
    case "git-archive": checkout = gitarchive.New()         // 本地仓库
    case "git-fetch":   checkout = gitfetch.New(cfg.Crypto) // 远程 + 凭据注入
    }

    deploy := deployregistry.Of(cfg.Profile.Deploy)         // "compose-local" | "ssh-remote"

    return NewApp(trig, checkout, deploy, core.Shared(...)) // 共享核心：调度/状态机/LOA/日志/存储
}'''

DEP_RULE = [
    "依赖方向（编译期强制，go vet + 目录约定双重保证）：",
    "",
    "  cmd/devopsd ──▶ internal/core ◀── internal/adapters/{localwatch,webhook,gitarchive,",
    "        │              ▲                     gitfetch,composelocal,sshremote}",
    "        │              │",
    "        └────装配──────┘   core 定义接口；adapters 实现接口；cmd 按 profile 装配",
    "",
    "  ✗ 禁止：internal/core import 任何 adapter（核心不知道形态存在）",
    "  ✗ 禁止：adapter 之间互相 import（local-watch 不知道 webhook 的存在）",
    "  ✓ 新增第 4 种形态 = 新增 adapter + 新增 profile，core 与前端零改动",
]

ADAPTER_MATRIX = [
    ("TriggerSource", "local-watch（Ⅰ）", "webhook（Ⅱ/Ⅲ）", "manual（Ⅰ/Ⅱ/Ⅲ 恒有）"),
    ("CheckoutStrategy", "git-archive（Ⅰ）", "git-fetch（Ⅱ/Ⅲ）", "—"),
    ("DeployTarget", "compose-local（Ⅰ/Ⅱ）", "ssh-remote（Ⅲ）", "—"),
]
