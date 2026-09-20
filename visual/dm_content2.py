# -*- coding: utf-8 -*-
"""部署形态可视化 · 内容 II：共享内核 + profile 配置 + 演进路径 + 实测证据 + 前端影响"""

# ============ 共享内核：三形态 100% 复用的部分（不重复造轮子的直接体现） ============
SHARED_CORE = [
    ("scheduler/", "队列原子认领 · Worker Pool（semaphore 限流）· 背压（503）· 优雅关闭", "形态差异仅体现在 max_concurrency 配置值（2/1/4）"),
    ("build/state.go", "9 状态机 + 迁移白名单 + build_events 审计", "三形态共用同一状态机，无分叉"),
    ("build/detect.go", "项目类型检测规则表 + pipeline_json 执行快照", "规则引擎与形态无关"),
    ("logpipe/", "环形缓冲 · 批量落库 · fan-out 扇出 · 慢订阅者丢弃", "SSE 推流三形态一致（个人版是 localhost，团队版走公网同源）"),
    ("loa/", "Analyzer Registry · Policy Resolver · 证据链 · 知识库 · LOA 动态演进 · 熔断/预算/审计", "核心创新点，形态无关；团队形态下审批与验证语义更完整"),
    ("diagnose/", "日志裁剪（头+尾8KB）· redact 脱敏 · OpenAI 兼容客户端 · 异步不阻塞", "端点可配置：云 API（Ⅱ/Ⅲ）或本地 Ollama（Ⅰ 可全离线）"),
    ("deploy/health.go", "健康检查（重试/间隔/连续 N 次判定）", "仅探测 URL 不同（localhost vs 目标机），逻辑同一份"),
    ("deploy/rollback.go", "previous_deployment_id 显式回滚链 · 保留 K 版", "回滚动作经 DeployTarget 接口，local/ssh 各自实现"),
    ("store/", "14 张表 schema · sqlc 查询 · 迁移版本化", "三形态同一 schema；projects.deploy_kind 区分 local/ssh"),
    ("crypto/", "AES-GCM 封装 · 主密钥仅环境变量", "个人版几乎无密可存（本地检出零凭据）；团队版存 webhook secret / git 凭据 / SSH 私钥"),
    ("httpapi/", "chi 路由 · REST · SSE · JWT/RBAC · 限流", "webhook 路由仅在 Ⅱ/Ⅲ 注册（装配期决定，非运行期开关）"),
    ("web/（前端）", "13 页面 · 167 测试 · mock 契约 · go:embed 内嵌", "同一份前端；仅新建项目向导多一种「本地目录」项目类型（见下方前端影响）"),
]

# ============ 三个 profile（完整 YAML，配置文件即产品分档） ============
PROFILES = [
    ("personal", "形态Ⅰ 个人开发者版", '''profile: personal
server:
  addr: "127.0.0.1:8080"        # 只监听回环，不对局域网暴露
storage:
  data_dir: "${APPDATA}/GoPulse" # 整目录即全部状态，可直接备份/迁移
trigger:
  kind: local-watch
  watch_paths: ["~/code/web-api"]
  debounce: 2s
  poll_interval: 5s              # rev-parse 兜底（实测 77ms/次）
  branches: [main]               # 仅监视配置的分支
checkout:
  kind: git-archive              # 零凭据：本地仓库导出快照
scheduler:
  max_concurrency: 2             # 给 IDE/浏览器留资源
build:
  container_limits: { cpus: "2", memory: 4g }
deploy:
  kind: compose-local            # 目标 = 本机 Docker
  health_url: "http://localhost:8080/healthz"
diagnose:
  base_url: "http://localhost:11434/v1"   # 本地 Ollama → 全离线；可换云 API
  model: "qwen2.5-coder:7b"'''),
    ("team-lite", "形态Ⅱ 简易团队版（合设）", '''profile: team-lite
server:
  addr: "0.0.0.0:8080"           # 公网可达；防火墙仅放行 8080
  base_url: "http://203.0.113.45:8080"   # webhook 回调地址（裸 IP 可用，已核实）
trigger:
  kind: webhook
  providers: [github]
  secret_store: encrypted        # 每项目独立 webhook secret（AES-GCM）
checkout:
  kind: git-fetch                # §3.7：GIT_CONFIG_COUNT 注入凭据，不落盘
scheduler:
  max_concurrency: 1             # ★ 与生产同机 → 强制串行
build:
  container_limits: { cpus: "1.5", memory: 1g }   # ★ 给生产服务留余量
  disk_watermark: 5GB            # 低于水位拒绝入队（防构建塞满磁盘）
deploy:
  kind: compose-local            # 目标就是本机；deploy_hosts.addr = 127.0.0.1
  health_url: "http://localhost:8080/healthz"
  auto_rollback: true
auth:
  multi_user: true               # 2–5 人共享 UI + 简单角色
diagnose:
  base_url: "https://api.example.com/v1"
  model: "gpt-4o-mini"'''),
    ("team-full", "形态Ⅲ 完整团队版（分设）", '''profile: team-full
server:
  addr: "0.0.0.0:8080"
  base_url: "https://ci.example.com"      # 建议配域名+证书（webhook 走 HTTPS 更稳）
trigger:
  kind: webhook
  providers: [github, gitlab]    # 双平台事件归一化（internal/vcs）
checkout:
  kind: git-fetch
scheduler:
  max_concurrency: 4             # 专机专用，可并行
  queue_capacity: 200
build:
  container_limits: { cpus: "2", memory: 4g }
deploy:
  kind: ssh-remote               # 1..N 台目标机
  hosts_from: db                 # deploy_hosts 表（私钥 AES-GCM · FixedHostKey）
  transfer: "save-ssh-load"      # docker save | ssh docker load（无需 registry）
  keep_versions: 5
auth:
  multi_user: true
  rbac: [admin, member]
diagnose:
  base_url: "https://api.example.com/v1"
  model: "gpt-4o-mini"'''),
]

# ============ 演进路径：形态之间怎么升级（数据不丢、代码不改） ============
EVOLUTION = [
    ("Ⅰ → Ⅱ", "个人 → 简易团队",
     "把 devopsd 和数据目录搬到生产服务器；profile 换 team-lite；项目配置从「本地目录」改「GitHub 仓库」（UI 上改一次，或改 projects 表一行）",
     "devops.db + data/ 直接 scp —— SQLite 单文件数据库的迁移成本就是拷贝文件；构建历史、知识库、已验证三元组全部保留（LOA 演进不断档）"),
    ("Ⅱ → Ⅲ", "简易团队 → 完整团队",
     "新 VPS 上 scp 二进制 + 数据目录；profile 换 team-full；deploy_hosts 把 127.0.0.1 改成真实目标机地址 + SSH 私钥",
     "同样是搬文件；webhook URL 在 GitHub 仓库设置里改一次指向新构建机"),
    ("Ⅰ → Ⅲ", "个人 → 完整团队",
     "两步合一：搬机器 + 换 profile + 配 deploy_hosts",
     "知识库若希望保留，随 devops.db 一起迁移即可"),
]

# ============ 实测证据表：所有「已核实/实测」断言的出处（可复核） ============
EVIDENCE = [
    ("git archive 按任意历史 SHA 导出干净快照（不含 .git）", "本机 git 2.45.1 实测", "对含两个 commit 的测试仓库，archive 第一个历史 SHA → tar 解出内容与该提交一致，目录无 .git"),
    ("git rev-parse HEAD 成本 77ms", "本机实测", "time git rev-parse HEAD → real 0m0.077s；轮询兜底每 5s 一次的开销可忽略"),
    (".git/HEAD 为可监视的符号引用文件", "本机实测", "内容为 ref: refs/heads/main，切分支时随之变化 → fsnotify 监视点成立"),
    ("GIT_CONFIG_COUNT 环境变量注入 git 配置，不落盘", "本机实测", "注入值可被 git config --get 读到；.git/config 无痕迹；unset 后回落全局值"),
    ("GitHub 支持按任意历史 SHA 浅 fetch", "对 octocat/Hello-World 实测", "取非分支尖端 SHA 553c207 → 全新客户端 fetch --depth=1 成功 → checkout 后 HEAD 一致"),
    ("GitHub webhook 允许纯 HTTP + 裸 IP（无域名/证书）", "GitHub 官方文档核实", "docs.github.com：URL 非 HTTPS 时不显示 SSL 验证选项（http 为受支持形态）；多处官方示例用 http://localhost"),
    ("Docker Desktop 对个人/教育/小企业（<250人且<$10M）免费", "Docker 官方 license 页核实", "docs.docker.com/subscription/desktop-license"),
    ("本机现状：无 docker CLI、无可用 WSL 发行版", "本机实测", "形态Ⅰ演示前需安装 Docker Desktop 或 podman —— 已列入 M1 前置"),
    ("fsnotify 跨平台（Windows ReadDirectoryChangesW / Linux inotify）", "fsnotify 库公开文档（未实测）", "标注为设计依据而非实测结论；M1 spike 第一项即验证监视 .git/ 的事件可靠性"),
]

# ============ 前端影响（现有 13 页面 / 167 测试的改动面） ============
FRONTEND_IMPACT = [
    ("新建项目向导", "小改", "「连接仓库」步骤增加项目类型二选一：GitHub/GitLab URL（Ⅱ/Ⅲ）｜本地目录选择器（Ⅰ，桌面形态弹原生目录框，浏览器形态填路径）"),
    ("部署目标管理", "小改", "deploy_hosts 增加 kind=local 卡片样式（显示「本机 Docker」，无 SSH 字段）；表单按 kind 切换字段组"),
    ("项目列表 / 构建历史 / 详情 / 日志 / 诊断 / 审批 / 知识库 / 审计", "零改动", "触发源、检出、部署方式对上游页面透明 —— builds.trigger 字段已能区分 push/manual，可增加 local-commit 枚举值"),
    ("登录 / 设置 / 状态页", "零改动", "多用户仅由 profile 决定是否启用；前端按 /api/runner 返回的能力位渲染"),
    ("契约", "增量", "openapi.yaml：projects 增 deployKind/sourceKind 字段；枚举 trigger 增 local-commit；均为向后兼容的新增，不动现有字段"),
]
