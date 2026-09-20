# GoPulse CI — 架构设计文档

> 面向小型团队的轻量 CI/CD 工具。Go 后端 + Vue 3 前端，单二进制交付，一台机器（笔记本或服务器）即可运行全流程：
> commit/push → 自动构建（Docker 隔离）→ 部署（本机 compose / SSH 远程）→ 健康检查 → 失败自动回滚 → LLM 智能诊断。

---

## 0. 已实现 / 规划分界

本文档同时覆盖**已实现**与**待实现**部分，用标记区分：

| 模块 | 状态 |
|------|------|
| 前端 Web 控制台（12 个页面 / 23 测试文件 / 167 用例 / 覆盖率 95.9%） | ✅ 已实现 |
| 后端 Go 服务（Scheduler / Builder / Deployer / Diagnoser） | ⬜ 规划中（M1 起步） |
| LLM 智能诊断的**服务端**实现 | ⬜ 规划中（前端已有完整展示层） |
| **自动化级别策略引擎**（LOA Policy Engine，第 5 节） | ⬜ 规划中（本课题核心创新点） |
| **诊断证据链**（结构化断言 + 日志行号锚点） | ⬜ 规划中（需前端配合改造，见 §7） |
| **人工反馈闭环与知识库**（验证计数 → LOA 演进） | ⬜ 规划中（需前端配合改造） |
| **全自动托管模式**（无人值守自动修复） | ⬜ 规划中（需前端配合改造） |
| **三种部署形态**（Ⅰ 个人开发者版 / Ⅱ 简易团队版 / Ⅲ 完整团队版，§3.8/§7） | ✅ 设计完成（`visual/deploy-modes.html` 交互式对照）；**三形态均为交付物**：M1–M4 按 Ⅰ→Ⅱ→Ⅲ 实现，M4 末全部可用并各自通过 E2E 验收 |

---

## 1. 系统全景

```
┌────────────────────────────────────────────────────────────────────────┐
│                         用户 / 开发者                                  │
│      git commit / push             浏览器访问 Web 控制台                │
└────────┬──────────────────────────────┬────────────────────────────────┘
         │                              │ HTTP / SSE
         ▼                              ▼
┌──────────────────────┐     ┌─────────────────────────────────────────┐
│ 触发源（三形态 §3.8）  │     │           Web 前端（Vue 3 SPA）          │
│ Ⅰ 本地 .git/ 监视     │     │  项目 · 构建 · 部署 · 密钥 · 设置        │
│ ⅡⅢ GitHub/GitLab     │     │  实时日志（EventSource）                 │
│    webhook            │     └────────────────┬────────────────────────┘
│ 手动触发（三形态共有） │                      │ /api/*（vite 代理 → :8080）
└─────────┬────────────┘                      ▼
          │ BuildRequest（幂等入队）
┌────────────────────────────────────────────────────────────────────────┐
│                     Go 后端（单二进制 devopsd，:8080）                   │
│                                                                        │
│  ┌──────────────  Access 层 ──────────────┐                            │
│  │ Trigger 入口(验签/监视) │ REST API │ Auth │ 幂等入队 → 202      │
│  └───────┬─────────────────┬─────────────┘                            │
│          ▼                 ▼                                           │
│  ┌──────────────  Core 层 ───────────────┐                            │
│  │ Scheduler（持久化队列·原子认领）        │                            │
│  │ State Machine（迁移校验·事件审计）      │                            │
│  │ Worker Pool（semaphore 限流 × N）       │                            │
│  │   ├─ Builder（Docker 隔离构建）         │                            │
│  │   ├─ Deployer（local compose / SSH 远程）│                           │
│  │   ├─ Diagnoser（LLM 异步诊断）          │                            │
│  │   └─ Log Pipe（ring buffer → SSE）      │                            │
│  └───────┬─────────────────┬─────────────┘                            │
│          │                 │                                           │
│  ┌───────▼─────────────────▼─────────────────────────────────────┐    │
│  │  ★ LOA Policy Engine（人机权责分配 · 本课题核心创新点）         │    │
│  │  ────────────────────────────────────────────────────────────  │    │
│  │  Analyzer Registry   受约束工具集：每类失败预先声明可查上下文   │    │
│  │                      与禁止访问项（AI 不能自行决定看什么）      │    │
│  │  Policy Resolver     (项目 × 失败类型 × 动作) → 自动化级别 LOA  │    │
│  │  Action Whitelist    引擎只能调注册过的动作，LLM 无法发明动作   │    │
│  │  Evidence Binder     诊断结论强制绑定日志行号，可点开验证       │    │
│  │  Approval Gate       LOA ≤4 的动作在此排队等待人工批准          │    │
│  │  Guardrail           熔断降级 / 预算限制 / 全量审计             │    │
│  │  Knowledge Store     已验证三元组 → 命中即免调 LLM，计数驱动演进│    │
│  └───────────────────────────┬───────────────────────────────────┘    │
│                              ▼                                        │
│  ┌────── Storage ──────┐  ┌──── External（全部接口化）────┐            │
│  │ SQLite（modernc）    │  │ Docker daemon（构建容器）      │           │
│  │ 14 张表(8基础+6LOA)  │  │ 部署目标（local compose / SSH）│           │
│  │ 日志分块 / 产物目录  │  │ LLM API（OpenAI 兼容协议）     │           │
│  └─────────────────────┘  └────────────────────────────────┘           │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 一次完整构建的生命周期

```
触发源（三选一，§3.8）：
  Ⅰ 本地仓库  fsnotify 监视 .git/HEAD·refs/heads/*（防抖2s）+ 轮询兜底 5s
  ⅡⅢ webhook  HMAC 验签 → 立即 202          手动：UI 按钮（三形态恒有）
      ──▶ (repo, sha, ref) 幂等入队 ──▶ Scheduler 原子认领
      ──▶ 项目类型检测(node/go/python…) ──▶ 生成 Pipeline 快照
      ──▶ Go 侧检出代码（Ⅰ git archive <sha> 零凭据 / ⅡⅢ fetch --depth=1 <sha>
           凭据不进容器，详见 §3.7–§3.8）
      ──▶ Docker 容器内执行（install → build，只读挂载已检出代码）
      ──▶ 日志经 Log Pipe 实时推送到浏览器（SSE）
      ──▶ 产物：docker commit → image tag（= commit SHA，不可变）
      ──▶ 部署（Ⅰ/Ⅱ 本机 compose up -d / Ⅲ save|ssh load → 远程 compose）
      ──▶ 健康检查 × N
      ├── 通过 → deployed（保留最近 K 个版本）
      └── 失败 ──▶ ★LOA 决策点★
            │  Analyzer 匹配失败类型 → Policy Resolver 查自动化级别
            ├── 命中知识库(已验证≥阈值) 且 LOA≥6 → 自动执行(重试/回滚/已验证修复)
            │        └── 写审计 → 事后通知人
            └── 未命中 或 LOA≤4 → LLM 异步诊断 → 证据链 → Approval Gate
                     └── 人工批准 → 执行；人工驳回 → 记录(负反馈)
```

**关键**：失败后不是无条件调 LLM，而是先过 LOA 决策点 —— 已知且已验证的失败直接自动修复，
未知失败才走「诊断 → 人批准」链路。这是「人为主导」与「全自动托管」共存的机制基础（见 §5）。

---

## 2. 前端架构（已实现）

### 2.1 技术栈与分层

```
src/
├── main.ts / App.vue          入口；登录页裸渲染，其余页套 AppShell
├── router.ts                  13 条路由 + meta.crumb（面包屑）+ afterEach 设标题
├── types.ts                   与后端 pkg/api/types.go 一一对应的类型契约
├── api/
│   ├── client.ts              fetch 封装：超时/AbortSignal/错误归一化
│   ├── mock.ts                Mock 数据 —— 全站唯一事实来源
│   └── index.ts               领域 API，USE_MOCK 二选一切换
├── composables/
│   ├── useAsync.ts            loading/error/retry/卸载即取消（竞态安全）
│   ├── useLogStream.ts        SSE 日志流；mock 下定时回放；环形缓冲 2000 行
│   └── usePolling.ts          轮询；上一次未完成不叠加；卸载即停
├── components/
│   ├── layout/                AppShell · AppTopbar · AppSidebar · AppStatusBar
│   ├── ui/                    StatusBadge · StageList · StageRail · LogTerminal
│   │                          StatCard · SkeletonRows · EmptyState · PageHeader
│   ├── Icon.vue + icons.ts    34 个内联 SVG 图标（零字体图标依赖）
│   └── RollbackDialog.vue     回滚确认（对比表 + 服务不可用警告）
└── views/                     12 个页面视图
```

### 2.2 关键设计决策

| 决策 | 理由 |
|------|------|
| **面包屑由路由 meta 生成** | 设计稿 13 页全写死「构建 #1091」；meta 是唯一来源，天然正确 |
| **`document.title` 在 `afterEach` 统一设置** | 设计稿 13 页全部没有 `<title>` |
| **Tailwind 本地编译，零 CDN** | `cdn.tailwindcss.com` 断网即白板；字体全部系统回落 |
| **图标全部内联 SVG** | Material Symbols 字体断网会显示成英文单词 |
| **`api/mock.ts` 是唯一事实来源** | 设计稿出现过「同一构建号两个耗时」「构建机三个名字」；一处定义，测试钉死 |
| **USE_MOCK 开关 + 同一 API 契约** | 后端就绪后 `.env` 改一行，调用方零改动；`mock.ts` 可整体删除 |
| **测试不 mock `mock.ts` 本身** | 数据一致性就是要被测的对象；23 文件/167 用例钉住 14 个历史缺陷 |

### 2.3 前端质量基线

```
测试        23 文件 / 167 用例全绿（Vitest + @vue/test-utils + jsdom）
覆盖率      语句 95.9% / 分支 87.5%；视图层 98.2%（12 个视图全部挂载级测试）
类型检查    vue-tsc --noEmit 零错误（strict 全开）
生产包      主包 115.6 kB (gzip 45.3) + CSS 22.4 kB (gzip 5.0)，零外链
```

测试钉住的真实缺陷（回归用例）：跨页数据矛盾 ×4、运行中构建显示失败日志、侧栏
「最长前缀」高亮错位、`deployed` 徽章文案语义错位、AbortSignal 监听器泄漏、
`useLogStream` 悬空 rejection、`&&` 短路日志顺序、圆点/对勾语义混淆等。

---

## 3. 后端架构（规划）

### 3.1 进程与目录

单二进制 `devopsd`，同一进程内分模块；配置可拆但默认不拆 —— 小团队一台机器足够。

```
devopsd/                            module: github.com/you/devopsd
├── cmd/devopsd/main.go             装配依赖（★全系统唯一形态分支点，§3.8）、启动、优雅关闭
├── internal/
│   ├── core/                       ★ ports.go：TriggerSource / CheckoutStrategy / DeployTarget
│   │                                 三接口定义；核心只依赖接口，不知道形态存在（§3.8）
│   ├── config/                     YAML 配置（profile 预设 personal/team-lite/team-full）+ 环境变量密钥
│   ├── httpapi/                    chi 路由：trigger 入口 / REST / SSE / auth
│   ├── scheduler/                  queue.go · pool.go · lifecycle.go
│   ├── build/                      state.go · executor.go · detect.go · pipeline.go
│   ├── deploy/                     deployer.go · health.go · rollback.go
│   ├── logpipe/                    pipe.go · ring.go · sink.go
│   ├── diagnose/                   llm.go · prompt.go · truncate.go · redact.go
│   ├── store/                      migrations/ · queries.sql（sqlc）
│   ├── crypto/                     AES-GCM 封装，主密钥只从环境变量读
│   ├── platform/                   dockerx / sshx / llmx —— 接口抽象，单测打桩
│   ├── vcs/                        GitHub / GitLab webhook 解析（§3.7）
│   └── adapters/                   ★ 三接口的全部实现（形态差异收敛于此，§3.8）
│       ├── localwatch/             fsnotify 监视本地 .git/ + 轮询兜底（形态Ⅰ）
│       ├── webhook/                HMAC 验签 + 事件归一化 + 幂等入队（形态Ⅱ/Ⅲ）
│       ├── manual/                 UI 手动触发（三形态恒有）
│       ├── gitarchive/             git archive <sha> 本地检出，零凭据（形态Ⅰ）
│       ├── gitfetch/               fetch --depth=1 <sha> + 凭据注入（形态Ⅱ/Ⅲ，§3.7）
│       ├── composelocal/           本机 docker compose 部署（形态Ⅰ/Ⅱ）
│       └── sshremote/              save|ssh load + FixedHostKey 远程部署（形态Ⅲ）
├── pkg/api/types.go                与前端 src/types.ts 对应
└── web/                            上面第 2 节的前端（构建产物由 go:embed 内嵌）
```

依赖方向（编译期强制）：`cmd → core ← adapters`。core 禁止 import 任何 adapter，
adapter 之间禁止互相 import（local-watch 不知道 webhook 的存在）。
新增第 4 种形态 = 新增一个 adapter + 一份 profile，core 与前端零改动。

### 3.2 核心数据流与并发模型

```
main
 ├── Scheduler goroutine      ×1   取任务；同项目串行化（防并发部署打架）
 ├── Worker Pool              ×N   chan struct{} 信号量限流
 │    └── per-build goroutine
 │         ├── Builder        ctx 超时（默认 30m），超时 kill 容器
 │         ├── Log Reader     容器 stdout → LogPipe（逐行时间戳）
 │         ├── Log Writer     批量落库（200 行或 2s flush）
 │         └── Diagnoser      失败时异步调 LLM，不阻塞状态流转
 ├── Trigger goroutines       ×3   每 TriggerSource 一个（local-watch/webhook/manual，按 profile 装配）
 ├── HTTP goroutines          ×M   每请求一个；trigger 入口只入队即回 202
 ├── Reconciler               ×1   孤儿构建恢复 / 超时清理 / 旧产物 GC
 └── signal handler           ×1   SIGTERM → 停止取新任务 → 宽限期 drain
```

**六条铁律**（并发正确性）：
1. 每个 goroutine 必须有明确退出路径（channel 关闭或 ctx 取消）
2. 谁创建 channel 谁关闭，且只在发送方关闭
3. 不在持锁时做 IO
4. 所有阻塞 IO 带 ctx 和超时（Docker/SSH/HTTP 都会挂住）
5. 清理逻辑用 `context.WithoutCancel`，否则取消后容器/连接泄漏
6. 全程 `go test -race`，竞态靠检测器找

### 3.3 数据模型（SQLite，8 张表）

```
users(id, email, password_hash, role, created_at)
deploy_hosts(id, name, kind,               -- kind: local | ssh（形态Ⅰ/Ⅱ 为 local，addr=127.0.0.1）
             addr, ssh_user, ssh_key_enc, ssh_host_key,   -- ssh 类才用，local 类为 NULL
             work_dir, compose_file, health_check_url, health_retries, keep_versions)
projects(id, owner_id→users, name,
         source_kind,                      -- local-repo | github | gitlab（§3.8 触发与检出的选择依据）
         repo_path,                        -- local-repo：本机仓库路径（形态Ⅰ）
         repo_provider, repo_full_name UQ, -- 远程仓库（形态Ⅱ/Ⅲ）
         default_branch, webhook_secret_enc, detected_type, pipeline_yaml,
         git_auth_type, git_credential_enc,   -- 代码检出凭据，AES-GCM，独立于 secrets（§3.7）
         deploy_host_id→deploy_hosts, build_timeout_s, auto_rollback)
secrets(id, project_id→projects, key, value_enc, UNIQUE(project_id,key))
builds(id, project_id, number UQ(项目内), state, trigger, ref, commit_sha,
       commit_message, commit_author, base_image, pipeline_json(快照),
       image_tag, artifact_path, exit_code, error_message,
       queued_at, started_at, finished_at, duration_ms,
       diagnosis, diagnosis_state)
build_events(id, build_id, from_state, to_state, reason, created_at)   -- 状态机审计
deployments(id, build_id, project_id, state, image_tag,
            previous_deployment_id→deployments(回滚链), started_at, finished_at)
log_chunks(id, build_id, seq UQ, content BLOB(压缩), byte_size)
```

索引要点：`builds(project_id, id DESC)`（历史页）、`builds(state) WHERE state IN
('queued','running','deploying')`（部分索引，调度器只查活跃构建）、
`log_chunks(build_id, seq)`（分段拉取）。

### 3.4 构建状态机

```
queued ─▶ running ─▶ succeeded ─▶ deploying ─▶ deployed
            │                          │           │
            ▼                          ▼           ▼(手动)
         failed ◀────────────── deploy_failed  rolled_back ◀─(自动)
            └──(异步标记)──▶ diagnosed   ※ 不参与主干，LLM 诊断完成位
```

- 迁移逐条校验，非法迁移拒绝；每次迁移写 `build_events`（可回放审计）
- `diagnosed` 是异步标记位：LLM 诊断失败不影响构建结果

### 3.5 对外 API（前端已按此契约实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/webhooks/{github\|gitlab}` | 验签 → 入队 → 202（无需登录；仅形态Ⅱ/Ⅲ装配此路由，§3.8） |
| GET/POST | `/api/projects` | 列表（含 lastBuild）/ 创建 |
| PATCH/DELETE | `/api/projects/{id}` | 配置 / 删除 |
| POST | `/api/projects/{id}/builds` | 手动触发 |
| GET | `/api/projects/{id}/builds` | 构建历史（cursor 分页） |
| GET | `/api/builds/{id}` · `/builds/{id}/stages` · `/logs` | 详情 / 阶段 / 日志 |
| GET | `/api/builds/{id}/logs/stream` | **SSE 实时日志** |
| GET | `/api/builds/{id}/diagnosis` | LLM 诊断结果 |
| POST | `/api/builds/{id}/rollback` | 回滚 |
| GET/POST | `/api/hosts` · `/api/hosts/{id}/test` | 部署目标 / 连通性测试 |
| GET/POST | `/api/secrets` | 密钥（值永不明文回传） |
| GET | `/api/runner` · `/api/builds/stats` | 构建机状态 / 统计 |

### 3.6 安全设计

| 项 | 做法 |
|----|------|
| Webhook | HMAC-SHA256 验签；`io.LimitReader` 1MB；同 commit+ref 幂等去重 |
| Secrets | AES-GCM 加密成 BLOB；**主密钥只从环境变量注入，不落库** |
| SSH | Host key 强制校验（`ssh.FixedHostKey`），防中间人；私钥加密存储 |
| 构建隔离 | 每任务独立容器；**不挂载 Docker socket**（防逃逸）；secrets 白名单注入 |
| LLM 诊断 | 日志尾部 8KB **脱敏后**才出网；诊断失败不影响构建结果 |
| 日志 | 大文本分块压缩，不进主表；构建日志 50MB 上限 |
| Git 凭据 | 存 `projects` 专用字段（AES-GCM），**绝不进 secrets 表**；仅 fetch 期间存在于内存，不写进 clone URL，不注入构建容器（详见 §3.7） |

### 3.7 代码检出与 Git 凭据管理

这是后端 M2 的实现前提，也是安全上最易出错的一环。核心原则：**检出由 Go 进程在容器外完成，凭据绝不进入构建容器**。

检出有两种策略，对应 §3.8 的 `CheckoutStrategy` 接口：

| 策略 | 适用形态 | 凭据 | 命令 |
|------|---------|------|------|
| `git-archive` | Ⅰ（本地仓库） | **零凭据** —— 本地磁盘读取无认证 | `git archive <sha> \| tar -x`（实测：精确导出任意历史 SHA，产物不含 `.git`） |
| `git-fetch` | Ⅱ/Ⅲ（远程仓库） | 需要，见下文 (2)–(5) | `git fetch --depth=1 origin <sha>` + `checkout` |

以下 (1)–(7) 主要针对 `git-fetch`；`git-archive` 是其严格子集（少了凭据与网络两个风险面）。

**（1）检出位置：Go 侧 clone，再把代码只读挂进构建容器**

| 方案 | 凭据暴露面 | 取舍 |
|------|-----------|------|
| **A. Go 侧检出（本设计采用）** | 凭据只在 Go 进程内存与 fetch 子进程中存在；容器只拿到已检出的代码目录 | clone 逻辑集中可控，凭据与构建脚本物理隔离 |
| B. 容器内 clone | 凭据须以环境变量传入容器 → 构建脚本 `env`/`set` 即可读到，并可能回显进日志 | 泄漏面大，与「secrets 白名单注入」的安全基调冲突，**不采用** |

采用 A 后，构建容器拿到的是 `data/workspaces/<build_id>/` 的只读挂载，容器内**没有任何 git 凭据**，与「不挂载 Docker socket」一致。

**（2）凭据存储：与构建 secrets 严格分离**

```
projects 表新增三列：
  git_auth_type       none | https_token | ssh_deploy_key
  git_credential_enc  AES-GCM 密文（PAT 或只读 deploy key 私钥）；none 时为 NULL
  clone_url 不单独存，由 repo_provider + repo_full_name 拼出
```

> **为什么不能复用 `secrets` 表**：`secrets` 的语义是「按白名单注入构建容器的环境变量」。
> git 凭据一旦进 `secrets`，就会随构建注入容器，正是方案 B 要避免的泄漏面。
> 因此 git 凭据走 `projects` 专用加密列，由 `internal/crypto` 用同一主密钥加解密，但**取用路径完全不同**：
> 只在 `internal/vcs` 检出时解密到内存，用完即清，永不出现在容器环境变量或 API 响应里。

**（3）支持的认证方式**

| 方式 | 适用 | 最小权限要求 |
|------|------|------------|
| `none` | 公开仓库 | 无需凭据 |
| `https_token`（主推） | GitHub / GitLab 私有仓库 | GitHub 用 **fine-grained PAT**，仅限目标仓库、Contents 只读；GitLab 用 **Deploy Token**（`read_repository`）。不要用 classic PAT 的全量 `repo` 权限 |
| `ssh_deploy_key`（可选） | 偏好 SSH 的团队 | 单仓库只读 deploy key |

**（4）检出流程：精确到 commit，浅克隆**

触发事件（webhook 或本地监视）都携带 `commit_sha`，必须检出**该 SHA**而非 `ref` 的最新提交（否则 ref 已前进时构建的不是触发那次提交，破坏可复现性）：

形态Ⅱ/Ⅲ（`git-fetch`，远程仓库）：

```bash
git init -q <workdir>
git -C <workdir> remote add origin <clone_url>          # URL 中不含凭据
# 凭据经环境变量注入临时 git 配置（见下），不进命令行参数、不进 URL
git -C <workdir> fetch -q --depth=1 origin <commit_sha>  # 按 SHA 浅取单个提交
git -C <workdir> checkout -q FETCH_HEAD
```

形态Ⅰ（`git-archive`，本地仓库）—— 无需 init/fetch/凭据，一条管道导出快照：

```bash
# 直接对用户的本地仓库执行，产物是纯净工作树（不含 .git），适合只读挂载进容器
git -C <repo_path> archive --format=tar <commit_sha> | tar -x -C <workdir>
```

- `--depth=1` 只取一个提交，省时省盘，契合轻量定位
- 按 SHA fetch：GitHub 已实测支持对**任意历史（非分支尖端）SHA** 执行 `fetch --depth=1`
  并 checkout（2026-09 于 git 2.45.1 + github.com 验证）；GitLab 侧的 SHA fetch 行为待后端
  接入时实测确认。为保证可移植性，统一采用**带回退的检出策略**：
  先 `fetch --depth=1 origin <commit_sha>`；失败则回退 `fetch --depth=1 origin <ref>`
  后 `checkout <commit_sha>`；若该 SHA 仍不可达（如被 force-push 覆盖），构建置 `failed`
  并报「检出失败：提交不可达」，不静默回退到 ref 最新提交（否则破坏可复现性）

**（5）凭据如何传给 git 而不泄漏**

关键：凭据**不写进 clone URL**（写进去会落到 `.git/config`、reflog 与可能的日志），也**不放命令行参数**（`-c http.extraHeader=...` 会被同机 `ps` 看到）。采用 git 2.31+ 的环境变量式临时配置注入：

```
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=http.extraHeader
GIT_CONFIG_VALUE_0=AUTHORIZATION: bearer <token>   # HTTPS token
# 或 SSH：GIT_SSH_COMMAND 指向临时只读 key + 固定 known_hosts（StrictHostKeyChecking=yes）
GIT_TERMINAL_PROMPT=0   # 禁止交互式提示（防卡死 + 防凭据回显）
```

凭据只存在于该 fetch 子进程的环境块中，进程退出即消失；Go 侧用 `defer` 清零内存里的明文。
（`GIT_CONFIG_COUNT` 注入机制已实测：注入值可被 `git config --get` 读到、不落盘到 `.git/config`、unset 后即消失 —— 2026-09 于 git 2.45.1 验证。）

**（6）日志脱敏与失效处理**

- `redact` 词表必须包含当前项目的 git token / deploy key 指纹，防 fetch 输出意外回显
- fetch 一律加 `-q`，正常路径不打印远端交互
- **区分失败类型**（与 §5 的 LOA 策略联动）：
  - `401/403`、`Authentication failed`、`could not read Username` → 判定为**凭据失效**，构建置 `failed`，`failure_kind=git_auth`，提示「更新 Git 凭据」；**不可自动重试**（重试无意义）
  - 连接超时、`Could not resolve host`、TLS 握手失败 → 判定为**瞬态网络失败**，`failure_kind=transient_network`，允许 LOA≥6 时自动重试
  - 这一区分正是 §5.1 Analyzer Registry 的两个内置失败类型

**（7）安全要点小结**

| 要点 | 做法 |
|------|------|
| 凭据不进容器 | Go 侧检出，容器只读挂载已检出代码（方案 A） |
| 凭据不进 secrets 表 | 走 `projects.git_credential_enc` 专用列，取用路径与构建 secrets 隔离 |
| 凭据不进 URL/参数/日志 | 环境变量式 `GIT_CONFIG_*` 注入；fetch `-q`；token 纳入 redact |
| 最小权限 | 单仓库只读（fine-grained PAT / Deploy Token / deploy key） |
| 可复现 | 精确检出的 `commit_sha` 与触发事件一致，非 ref 最新（两种策略同此原则） |
| 失效可诊断 | 区分凭据失效与网络瞬态失败，分别走「提示更新」与「可自动重试」（`git-archive` 无此两类失败，仅磁盘/SHA 不可达） |

### 3.8 部署形态与解耦设计（三种形态 · 同一内核）

> 交互式对照见 `visual/deploy-modes.html`（13 步流水线逐步对比、三份完整 profile、实测证据清单）。

同一二进制按资源约束分三种部署形态。**形态差异被严格约束在三个接口点内**，
核心（调度/状态机/构建/日志/LOA/诊断/回滚/存储/前端）三档 100% 共用，无条件分支：

| | Ⅰ 个人开发者版 | Ⅱ 简易团队版 | Ⅲ 完整团队版 |
|--|--|--|--|
| profile | `personal` | `team-lite` | `team-full` |
| 机器 | 1（笔记本） | 1（生产服务器**合设**） | 1+N（构建 VPS + 目标机） |
| 代码源 | 本地 git 仓库 | GitHub | GitHub / GitLab |
| 触发 | fsnotify 监视 `.git/` | webhook（HTTP+裸 IP 即可） | webhook |
| 检出 | `git archive <sha>` | `git fetch <sha>` | `git fetch <sha>` |
| 部署 | compose-local | compose-local（127.0.0.1） | ssh-remote ×N |
| 公网暴露 | **零** | 1 端口 | 构建机 :8080 + 目标机 :22 |
| max_concurrency | 2（给 IDE 留资源） | **1（与生产同机，强制串行）** | 4 |
| 交付角色 | ✅ 交付（离线 E2E 验收） | ✅ 交付 · 论文代表场景（合设 E2E 验收） | ✅ 交付（SSH E2E 验收） |

**三形态地位等同，均为真实交付物**（各自 E2E 验收清单见 TODO M4）；实现顺序 Ⅰ→Ⅱ→Ⅲ 只是由简入繁的工程路径，不是优先级排序。形态Ⅱ 为论文代表场景（零增量成本叙事）。

**三个接口点**（`internal/core/ports.go`，实现全部在 `internal/adapters/`）：

```go
// 差异点 1：任务从哪来
type TriggerSource interface {
    Kind() string                                    // "local-watch" | "webhook" | "manual"
    Watch(ctx context.Context, p *Project, emit func(BuildRequest)) error
}
// 差异点 2：代码怎么到手（产物保证：干净快照目录，不含 .git）
type CheckoutStrategy interface {
    Fetch(ctx context.Context, req CheckoutRequest) (workspace string, err error)
}
// 差异点 3：产物怎么上线
type DeployTarget interface {
    Deploy(ctx context.Context, req DeployRequest) error
    HealthCheck(ctx context.Context) (ok bool, err error)
    Rollback(ctx context.Context, to DeploymentID) error
}
```

**形态分支只存在于 `cmd/devopsd/main.go` 的一个 switch**（按 profile 装配 adapters），
core 与 adapters 互不感知；adapter 之间互不 import。依赖方向：`cmd → core ← adapters`。

**LocalWatchTrigger 要点**（形态Ⅰ，替代 webhook 的触发机制）：
- 只监视 `.git/HEAD` 与 `.git/refs/heads/*`，**绝不监视工作区文件**（否则每次 Ctrl+S 都触发）
- fsnotify 事件防抖 2s（rebase/merge 会连发 refs 更新，取最终 SHA 触发一次）
- 轮询兜底：每 5s `git rev-parse HEAD`（实测 77ms/次），防 fsnotify 丢事件；与监视器结果按 SHA 幂等去重
- 分支过滤：HEAD 为符号引用（实测内容 `ref: refs/heads/main`），仅配置的分支触发
- 合盖/关机期间错过的 commit：唤醒后由轮询发现并补触发（幂等去重防重复构建）
- fsnotify 跨平台性为设计依据（Windows ReadDirectoryChangesW / Linux inotify，**未实测**），
  M1 spike 第一项即验证监视 `.git/` 的事件可靠性；不写 `.git/hooks/`（不侵入用户仓库）

**合设形态（Ⅱ）的保命三件套**：`max_concurrency: 1` + 构建容器限额（`--cpus 1.5 --memory 1g`）
+ 构建前磁盘水位检查 —— 构建与生产同机时，资源尖峰直接传导为线上卡顿，这三项是配置级强制项。

**演进路径**：形态升级 = `scp devopsd devops.db data/ 新机器:` + 换 profile。
SQLite 单文件 + 单二进制的红利在此兑现：构建历史、知识库、LOA 演进积累随库整体迁移，不导出、不重建。

---

## 4. 人机权责分配模型（理论依据）

本课题的核心创新点**不是**「在 CI/CD 里接了个大模型」，而是**一套可控的人机权责分配机制**。
其理论基础是自动化级别（Levels of Automation, LOA）模型。

### 4.1 四类功能 × 十级量表

Parasuraman、Sheridan 与 Wickens 指出，自动化不应被视为「全有或全无」的单一开关，
而应按**功能类型**分解，每类功能独立地在「完全人工」到「完全自动」的连续谱上取值 [P1]：

| 功能类型 | 本系统中的对应环节 | 采用的自动化级别 |
|---------|------------------|----------------|
| 信息获取 Information Acquisition | 采集构建日志、容器退出码、diff、历史失败记录 | **高**（全自动，人不该做这个） |
| 信息分析 Information Analysis | 日志裁剪、错误特征提取、根因推断 | **高**（LOA 6–7，LLM 主战场） |
| 决策与行动选择 Decision & Action Selection | 采纳哪个修复方案、是否回滚 | **低**（LOA 2–4，人主导，AI 只提议） |
| 行动执行 Action Implementation | 改代码、重跑构建、部署 | **最低**（LOA ≤4，人执行或人批准） |

Sheridan 与 Verplank 提出的十级量表 [P2] 给出可引用的刻度（下表为 O'Hara 与 Higgins
在 BNL-91017-2010 中转述的 Sheridan 2002 细化版本 [P3]）：

| LOA | 含义 | 本系统使用场景 |
|-----|------|--------------|
| 1 | 计算机不提供任何协助 | — |
| 2 | 计算机建议多种做法 | 诊断模式：给出根因与多个候选修复方向 |
| 4 | 计算机选定一种，**人批准后执行** | **默认档位**：修复建议 → Approval Gate |
| 6 | 自动执行，**必须告知人** | 已验证修复的自动应用（事后通知） |
| 7 | 自动执行，人主动询问才告知 | 夜间定时构建的无人值守修复 |
| 8 | 自动执行并忽略人 | **本系统永不使用** |

### 4.2 为什么「人为主导」在小团队场景下是效率最优解

这一设计选择有实证依据，不是保守的妥协：

- Zhou 等对 LLM 辅助开发的混合方法研究（14 名开发者观察 + 22 名问卷，发表于 ICSE 2026）发现，
  **48.8%** 的开发者动作存在认知偏差，其中 **56.4%** 与 LLM 交互相关；
  且 LLM 相关动作的**撤销率达 29.46%**（238/808），统计显著高于非 LLM 动作 [P4]。
  → 全自动采纳 AI 结论会产生「看似在修、实为返工」的隐性成本。
- Romeo 与 Conti 对人机协作中自动化偏差（automation bias）的综述指出，
  提供决策建议时人会**更少审视**附加信息 [P5]。
  → 因此本系统不把诊断做成一段散文，而是强制绑定可点开验证的日志证据（§5.4）。
- Roy 等的实证评估发现，把事件相关的讨论记录作为额外上下文喂给模型，**性能并未显著提升** [P6]。
  → 上下文堆砌无用，信息的**筛选**才是关键，而筛选恰恰是人的优势。
- 小团队没有专职 SRE 复核 AI 结论，但**开发者本人就在场且持有完整业务上下文**。
  把决策权留在人手上，在本场景下是效率最优解，而非能力不足的表现。

### 4.3 与已有工作的定位差异

| 方案 | 决策环节 LOA | 依赖 | 与本课题的差异 |
|------|------------|------|--------------|
| LogSage [P7] | 接近 7–8（端到端自动检测与修复） | 企业内部知识库、私有模型、平台团队 | 面向大型组织；本课题面向小团队且决策权在人 |
| RCAgent [P8] | 高（自主智能体自由编排工具） | 多工具编排、阿里云平台 | 工具集由 AI 自主决定；本课题由人预先约束 |
| Bart [P9] | 2（仅给提示） | 外部互联网检索 | 效果受检索相关性制约；本课题基于项目自身日志 |
| **本系统** | **2–7 可配置（按失败类型演进）** | 一台 VPS + 一个 LLM 端点 | **混合自动化级别配置 + 级别随人工验证动态演进** |

> 本课题不追求在诊断精度上超越面向大型组织的专用方案，而是研究该类能力在
> **资源受限、无历史数据积累、无专职运维**场景下工程化落地的可行边界。

---

## 5. 自动化级别策略引擎（LOA Policy Engine，核心创新点）

### 5.1 受约束工具集：Analyzer Registry

借鉴 k8sgpt 把 SRE 经验**固化为 analyzer** 的做法（官方表述：*"SRE experience codified
into its analyzers"*）[P10] 与 HolmesGPT 的 toolset 抽象 [P11]：**AI 不能自己决定看什么**。
每类失败由人预先声明可查上下文与禁止访问项：

```yaml
# analyzers/npm_install.yaml
id: npm_install_failure
match:                       # 触发条件（确定性规则，非 LLM 判断）
  stage: 依赖安装
  exit_code: != 0
  log_pattern: "npm ERR!|ERESOLVE|404 Not Found"
context:                     # 白名单：只有这些能进 prompt
  - log_tail: 200
  - file_diff: package.json
  - fact: last_success_lockfile_hash
forbidden:                   # 黑名单：硬隔离，不靠 prompt 约束
  - secrets_table
  - ssh_private_key
  - other_projects_logs
actions:                     # 只能从注册动作里选
  - retry_build
  - clear_npm_cache
```

**这样做的三重收益**：① 安全边界由代码而非提示词保证；② 诊断可复现（同样的匹配条件必得同样的上下文）；
③ 「人为主导」有了具体机制 —— 人定义规则，AI 在规则内工作。

### 5.2 策略解析：Policy Resolver

自动化级别按 **(项目 × 失败类型 × 动作类型)** 三元组解析，而非全局开关：

```yaml
policy:
  default:                       LOA 4   # 新项目默认：AI 提议，人批准
  unknown_failure_type:          LOA 4   # 未知失败永不自动执行
  verified_hit:                          # 命中已验证知识库
    min_verifications: 3
    loa: 7                               # 无人值守自动执行，事后可审计
  destructive_action:            LOA 4   # 破坏性动作永远需要人批准（不可覆盖）
  schedule: nightly              LOA 7   # 夜间定时构建
  dependency_patch_update:       LOA 6   # 依赖小版本更新，自动执行后必须通知
```

### 5.3 LOA 动态演进：人工反馈闭环

这是本课题**最有价值的机制** —— 人不是自动化的对立面，人是自动化的**训练者**：

```
LOA 4（人批准）
   │  开发者标记诊断结果：✅准确 / ⚠️部分准确 / ❌无关
   ▼
沉淀为已验证三元组 (错误特征 → 根因 → 修复动作)
   │  同类失败第 N 次命中且 N ≥ min_verifications
   ▼
LOA 自动升至 7（无人值守）
   │  连续 2 次自动修复失败
   ▼
熔断降回 LOA 4 并通知人
```

| 收益 | 说明 |
|------|------|
| 降低成本 | 命中知识库直接返回，**不调 LLM** |
| 提升可信度 | 展示「本团队已验证 3 次」，比展示模型置信度更有说服力 |
| 适配冷启动 | 新项目无历史数据 —— 这正是 Hassan & Wang 等机器学习预测方法的软肋 [P12]；本方案靠人逐步积累，不需预训练 |

### 5.4 证据链强制绑定：Evidence Binder

诊断输出**不是散文**，而是结构化断言 + 日志行号锚点：

```json
{
  "rootCause": "TypeScript 类型检查失败",
  "evidence": [
    {"claim": "tsc 报告 3 处类型错误",
     "logLines": [1842, 1843, 1857],
     "verbatim": "error TS2345: Argument of type 'string'..."},
    {"claim": "错误集中在本次提交修改的文件",
     "diffHunk": "src/api/client.ts:45-52"}
  ],
  "suggestion": "将 fetch 的返回类型收窄为 Response | null",
  "confidenceBasis": "错误信息与 package.json 中 typescript 版本升级记录一致",
  "source": "llm"
}
```

前端把 `logLines` 渲染为可点击跳转到日志终端对应行的链接。**人不是在读结论，而是在验证据** ——
这直接对抗自动化偏差 [P5]。

设计约束（延续既有决策）：**不做**百分比置信度，无法解释来源的数字一律不展示；
`confidenceBasis` 是定性的依据说明，不是分数。

### 5.5 全自动托管模式的边界

全自动 **≠** AI 自动写补丁并合入。判据：**全自动只执行确定性的、已验证的、可回滚的动作**。

| 全自动模式**可以**做 | 全自动模式**永不**做 |
|---|---|
| 重试已知瞬态失败（网络抖动、镜像拉取超时） | 生成并应用 AI 新写的代码补丁 |
| 应用**知识库中已验证过的**修复动作 | 修改 secrets、SSH 密钥、部署凭据 |
| 健康检查失败后回滚到前序版本 | 删除数据、清理卷、强制覆盖 |
| 依赖小版本更新 + 全量测试通过后部署 | 未通过健康检查就继续推进 |
| 发通知、生成日报 | 任何未在白名单中的动作 |

### 5.6 安全护栏（Guardrail）

| 护栏 | 实现 |
|------|------|
| 动作白名单 | 引擎只能调用注册过的 `Action`；LLM 输出的动作名不在表内即拒绝 |
| 熔断降级 | 连续 2 次自动修复失败 → LOA 降回 4 + 通知人 |
| 预算限制 | 每天最多 N 次自动修复 / 最多 M 次 LLM 调用，超出转通知 |
| 全量审计 | 每个自动动作记录 (触发条件、命中规则、执行前后状态、耗时)，可回放 |
| 默认安全 | 新项目默认 LOA 4；全自动需人显式开启并配置策略 |
| 脱敏前置 | 出网前按 secrets 表逐项替换；`forbidden` 上下文由代码硬隔离 |

### 5.7 三种交互模式（借鉴 Aider）

Aider 的 ask / architect / code 三模式设计 [P13] 移植为诊断侧的三档交互：

| 模式 | 行为 | LOA | 是否实现 |
|------|------|-----|---------|
| **诊断模式** | 只给根因与证据，不给 patch | 2 | ✅ M5 |
| **修复方案模式** | 先出思路，人认可后再生成 diff | 4 | ✅ M5 |
| 自动应用模式 | 直接执行已验证修复 | 6–7 | ✅ M6（限白名单动作） |
| ~~自动写码模式~~ | AI 生成新补丁并合入 | 8 | ❌ **明确排除在范围外** |

Aider 官方推荐的 ask→code 工作流（先讨论清楚方案，再极简授权 "go ahead"）正是
**「人在前段投入判断、后段极简授权」**的交互形态，本系统的 Approval Gate 采用同一思路。

---

## 6. LLM 智能诊断链路

```
构建失败 ──▶ Analyzer Registry 匹配失败类型
        ├── 命中知识库且 LOA≥6 ──▶ 跳过 LLM，直接执行已验证动作 ──▶ 写审计
        └── 未命中或 LOA≤4 ──▶ 按 analyzer.context 白名单取上下文
             ──▶ 取日志尾部 8KB ──▶ redact()（按 secrets 表逐项替换）
             ──▶ truncate()（头 1KB 步骤名 + 尾 7KB 错误 + 中间 …省略…）
             ──▶ POST {base_url}/chat/completions（OpenAI 兼容）
             ──▶ 解析为结构化证据链（§5.4）→ 写回 builds.diagnosis
             ──▶ LOA≤4：进 Approval Gate 等人批准
             ──▶ 前端紫卡展示（原因 / 证据 / 建议 / 耗时 / tokens / 脱敏数）
```

- Go 侧只是 HTTP 客户端；推理在云端 / vLLM / Ollama（换 base_url 即可）
- 超时 90s + 指数退避重试 2 次；失败置 `diagnosis_state='failed'`，**不碰构建状态**
- 相同错误签名（日志尾部 hash）优先查知识库；命中即返回并累加验证计数，**不调 LLM**
- 提示词中强制要求以 JSON 输出证据链；解析失败降级为纯文本 rootCause（不带证据）
- **不做**百分比置信度 —— 无法解释来源，前端只展示定性元信息

---

## 7. 部署形态

三种形态共用同一交付物：**单二进制 `devopsd`（go:embed 内嵌前端）+ 一个 SQLite 文件 + data/ 目录**。
形态由启动参数 `-profile` 选择（**必填**，缺失即报错并列出三档；无隐式默认——三形态地位等同），不重新编译（详见 §3.8 与 `visual/deploy-modes.html`）。
**三种形态均为交付物**：M4 末各自通过端到端验收（Ⅰ 离线全链路 / Ⅱ webhook+合设共存 / Ⅲ SSH 分离部署），验收脚本即 TODO M4 的出口条件。

**形态Ⅰ 个人开发者版**（笔记本单机，零公网）

```
本地 git 仓库 ──fsnotify 监视 .git/──▶ devopsd（桌面 App 或 localhost:8080）
  ├─ git archive <sha> 检出（零凭据零网络）
  ├─ 本机 Docker 构建（--cpus 2 · max_concurrency 2）
  ├─ DeployTarget(compose-local)：docker compose up -d（目标 = 本机）
  └─ 健康检查 http://localhost:8080/healthz → 失败自动回滚
数据目录：%APPDATA%/GoPulse/（整目录即全部状态，可直接备份）
诊断端点可配本地 Ollama → 全链路可离线
```

**形态Ⅱ 简易团队版**（生产服务器合设，蹭已有公网 IP）

```
GitHub ──webhook POST──▶ http://<公网IP>:8080/api/webhooks/github（HMAC 验签）
  └─ devopsd 与生产服务同机 → 构建镜像零传输 → compose-local 上线
     ★ max_concurrency 1 + 容器限额 + 磁盘水位检查（与生产抢资源的三道闸）
2–5 人共享同一 Web UI；审批队列/知识库自此具备「他人验证」语义
```

**形态Ⅲ 完整团队版**（构建与生产分离）

```
构建 VPS：devopsd + Docker daemon（max_concurrency 4，专机专用）
      │ docker save | ssh docker load（无需私有 registry）
      ▼ ssh（FixedHostKey 强校验）
目标主机 ×N：docker-compose.yml + 最近 K 个版本镜像（供回滚）
```

前置条件：构建机装 Docker（或 podman）；形态Ⅲ目标机装 Docker + docker-compose。
`docker compose` 之外零外部依赖 —— 无数据库服务、无消息队列、无对象存储、无私有 registry。
形态Ⅰ/Ⅱ连 SSH 与公网入站都不需要（Ⅱ仅开放 webhook/UI 端口）。

---

## 8. LOA 引擎的数据模型与 API 扩展

### 8.1 新增数据表（在原 8 张表基础上增加 6 张，合计 14 张）

```sql
-- 失败类型定义（Analyzer Registry 的持久化形式；也可从 YAML 加载）
analyzers(id, key UQ, name, match_stage, match_exit_code, match_log_pattern,
          context_spec JSON,   -- 白名单：可进 prompt 的上下文
          forbidden_spec JSON, -- 黑名单：硬隔离项
          enabled, created_at)

-- 可执行动作白名单（引擎只能调这里注册的动作）
actions(id, key UQ, name, kind,            -- kind: retry|rollback|verified_fix|notify
        destructive BOOLEAN,               -- 破坏性动作强制 LOA≤4，不可被策略覆盖
        params_schema JSON, enabled)

-- 策略配置：(项目 × 失败类型 × 动作) → LOA
policies(id, project_id NULL→projects,     -- NULL 表示全局默认
         analyzer_key NULL, action_key NULL, loa INT, min_verifications INT,
         note, updated_at,
         UNIQUE(project_id, analyzer_key, action_key))

-- 已验证知识库（LOA 演进的核心）：错误特征 → 根因 → 修复动作
knowledge(id, project_id→projects, error_signature,   -- 日志尾部 hash
          analyzer_key, root_cause, action_key, action_params JSON,
          verified_count INT DEFAULT 0, rejected_count INT DEFAULT 0,
          auto_applied_count INT DEFAULT 0, loa_current INT DEFAULT 4,
          last_verified_at, created_at,
          UNIQUE(project_id, error_signature))

-- 审批队列（LOA≤4 的动作在此等待人工决定）
approvals(id, build_id→builds, action_key, action_params JSON,
          diagnosis_id, loa, state,        -- pending|approved|rejected|expired
          decided_by→users, decided_at, reason, created_at)

-- 自动执行审计（全自动模式的每一次动作，可回放）
automation_audit(id, build_id→builds, project_id, action_key,
                 trigger_reason,            -- 命中的 analyzer + policy
                 loa_before, loa_after,     -- 是否触发熔断降级
                 state_before JSON, state_after JSON,
                 outcome,                   -- success|failed|circuit_broken
                 latency_ms, created_at)
```

`builds` 表增加两列：`failure_kind`（匹配到的 analyzer key）、`loa_applied`（本次生效的自动化级别）。
`diagnosis` 列由纯文本改为 JSON，承载 §5.4 的证据链结构。

索引要点：`knowledge(project_id, error_signature)`（命中查询）、
`approvals(state) WHERE state='pending'`（部分索引，审批队列只查待决）、
`automation_audit(project_id, id DESC)`（审计回放）。

### 8.2 新增 API 端点

| 方法 | 路径 | 说明 | LOA |
|------|------|------|-----|
| GET | `/api/builds/{id}/diagnosis` | **改造**：返回结构化证据链而非纯文本 | — |
| POST | `/api/builds/{id}/diagnosis/feedback` | 人工标记 ✅/⚠️/❌（驱动知识沉淀与 LOA 演进） | 人 |
| GET | `/api/approvals?state=pending` | 待审批动作队列 | 人 |
| POST | `/api/approvals/{id}/approve` | 批准执行 | 人（LOA 4 的关口） |
| POST | `/api/approvals/{id}/reject` | 驳回（记为负反馈） | 人 |
| GET/PUT | `/api/projects/{id}/policy` | 项目级自动化策略配置 | 人 |
| GET | `/api/analyzers` | 可用失败类型分析器列表 | — |
| GET | `/api/actions` | 动作白名单（含 `destructive` 标记） | — |
| GET | `/api/projects/{id}/knowledge` | 已验证知识库（含 verified_count / loa_current） | — |
| GET | `/api/projects/{id}/automation/audit` | 自动执行审计流水（可回放） | — |
| GET | `/api/automation/stats` | 自动修复次数 / 熔断次数 / LLM 调用与预算余量 | — |

SSE 通道扩展：除日志流外增加 `event: loa`（自动化级别变更、熔断降级、审批请求到达），
使「夜间自动修复」在前端可实时可见。

---

## 9. 前端改造评估

**结论：现有 12 个页面全部保留，不需重构；需扩展 2 个页面、新增 3 个页面。**

### 9.1 不需要改的部分

| 现有资产 | 为何可原样保留 |
|---------|--------------|
| 12 个页面视图与 13 条路由 | LOA 引擎是失败后的新增分支，主干流程（构建/部署/日志/回滚）不变 |
| `api/client.ts`（超时/AbortSignal/错误归一化） | 新端点走同一封装，零改动 |
| `useAsync` / `usePolling` / `useLogStream` | 审批队列用 `usePolling`，LOA 事件走 `useLogStream` 扩展的 SSE |
| 全部 UI 组件（StatusBadge / StageList / LogTerminal / RollbackDialog…） | 证据链、审批卡复用现有卡片与徽章样式 |
| `USE_MOCK` 开关与 mock.ts 单一事实来源机制 | 新功能同样先写 mock 再联调，模式不变 |
| 167 个测试用例 | 不受影响；新功能另加测试 |

### 9.2 需扩展的 2 个页面

| 页面 | 改动 | 工作量 |
|------|------|-------|
| `BuildDiagnosisView.vue` | ① 诊断卡由「原因+建议」两段文字扩展为**证据链列表**，每条 `logLines` 渲染成可点击链接跳转到日志终端对应行；② 增加 ✅/⚠️/❌ **反馈按钮**；③ 命中知识库时显示「本团队已验证 N 次」徽章与 `source: knowledge` 标识 | 中 |
| `ProjectSettingsView.vue` | 增加**自动化策略**配置区：默认 LOA 档位、`min_verifications` 阈值、全自动模式开关（默认关闭）、破坏性动作保护（只读展示，不可关闭） | 中 |

`BuildFailedView.vue` 与 `LogTerminal` 需支持「跳转到指定行并高亮」——这是证据链可验证性的落点，
属小改动（`LogTerminal` 已有序号列，加 `scrollToLine(seq)` 即可）。

### 9.3 需新增的 3 个页面

| 页面 | 内容 | 优先级 |
|------|------|-------|
| `ApprovalsView.vue` **审批中心** | 待审批动作队列（动作名、触发原因、证据摘要、目标项目）+ 批准/驳回；这是 LOA 4 的人机关口，**M5 必需** | ★★★ |
| `KnowledgeView.vue` **知识库** | 已验证三元组列表：错误特征 → 根因 → 修复动作，含 verified_count / rejected_count / 当前 LOA；可视化「人如何训练系统」，**答辩展示价值高** | ★★ |
| `AutomationAuditView.vue` **自动化审计** | 自动执行流水（时间线 + 每次动作的触发规则、前后状态、结果、耗时）+ 熔断记录 + 预算余量；这是全自动模式「事后可审计」承诺的兑现，**M6 必需** | ★★ |

侧栏需增加对应导航项（AppSidebar 的路由表扩展，最长前缀匹配逻辑已就绪）。

### 9.4 契约变更（需同步 openapi.yaml 与 types.ts）

`Diagnosis` 接口扩展（**破坏性变更，需前后端同步**）：

```ts
export interface Diagnosis {
  rootCause: string
  suggestion: string
  evidence: Evidence[]          // 新增：证据链
  confidenceBasis: string | null // 新增：定性依据（非分数）
  source: 'llm' | 'knowledge'   // 新增：本次诊断来源
  analyzerKey: string | null    // 新增：命中的失败类型
  loaApplied: number            // 新增：本次生效的自动化级别
  model: string
  latencyMs: number
  inputTokens: number
  redactions: number
}

export interface Evidence {
  claim: string
  logLines?: number[]           // 可点击跳转的行号锚点
  verbatim?: string             // 日志原文摘录（已脱敏）
  diffHunk?: string             // 关联的代码 diff 位置
}
```

另需新增类型：`Policy` / `Approval` / `KnowledgeEntry` / `AutomationAuditEntry` / `AnalyzerInfo` / `ActionInfo` / `AutomationStats`，
以及对应的 `api/index.ts` 方法与 `mock.ts` 数据。

### 9.5 工作量与建议时序

| 阶段 | 前端工作 | 预估 |
|------|---------|------|
| M5 前 | `types.ts` + `mock.ts` 扩展、`ApprovalsView`、诊断页证据链改造 | 4–6 天 |
| M6 前 | `ProjectSettingsView` 策略区、`KnowledgeView`、`AutomationAuditView`、SSE `loa` 事件 | 4–6 天 |
| M7 | A/B 实验数据展示（撤销率/采纳率对比图）、答辩演示录屏 | 2–3 天 |

**建议**：沿用既有的「契约先行 + mock 驱动」模式 —— 先改 `types.ts` 与 `openapi.yaml`，
再写 `mock.ts` 数据与页面测试（保持覆盖率基线），最后才联调后端。这样后端可以并行开发，
且新页面从第一天起就有测试保护。

**范围警告**：全自动模式若做成独立子系统（自己的调度器与任务模型）会吃掉写论文的时间。
按 §5 的设计，它是在既有状态机上加一层策略判断 + 6 张表，约 1–2 周后端工作量。
自动执行的动作范围严格限定为三类：**瞬态失败重试、已验证修复应用、健康检查失败回滚**。
依赖自动更新等复杂场景若时间不够应砍掉。

---

## 10. 演进路线

详见 [TODO.md](./TODO.md)。里程碑：

| 里程碑 | 内容 | LOA 相关 |
|--------|------|---------|
| M1 | 后端骨架：**core/ports 三接口** + profile 装配、配置、存储、路由、鉴权、任务队列；**LocalWatchTrigger + ManualTrigger**（形态Ⅰ触发链路） | — |
| M2 | 构建执行：容器隔离、类型检测、状态机、审计；**gitarchive + gitfetch 两种检出** | — |
| M3 | 实时日志管道 + SSE | — |
| M4 | 部署与回滚：**composelocal + sshremote 两种部署**、健康检查、版本保留；**WebhookTrigger**（形态Ⅱ/Ⅲ触发链路） | — |
| M5 | **智能诊断（LOA 2/4）**：Analyzer Registry、证据链、Approval Gate、人工反馈 | ★ 人主导档 |
| M6 | **全自动托管（LOA 6/7）**：知识库命中自动执行、熔断降级、预算限制、审计回放 | ★ 托管档 |
| M7 | 并发打磨、压测、**A/B 对照实验** | ★ 实验组 |
| M8 | 论文与演示 | — |

前端已完成的部分对应 M3 的界面层与全站的 UI 契约；M5/M6 需前端配合改造（见 §9）。

**M7 的 A/B 对照实验是本课题创新点的验证方式** —— 同一批失败样本分别在
LOA 4（人批准）与 LOA 7（全自动）两种策略配置下运行，对比撤销率、采纳率、修复时间。
没有全自动模式，就无法证明人主导的价值（对照基线见 [P4] 报告的 29.46% 撤销率）。

---

## 参考文献（本文档引用）

> 著录格式 GB/T 7714—2015。标注 ✅ 者已经 Crossref API / 出版社页面核实元数据；
> 标注 ⚠️ 者为转引自权威二手来源，正式写入论文前需自行复核原文。

| 编号 | 文献 | 核实状态 |
|------|------|---------|
| [P1] | PARASURAMAN R, SHERIDAN T B, WICKENS C D. A model for types and levels of human interaction with automation[J]. IEEE Transactions on Systems, Man, and Cybernetics — Part A: Systems and Humans, 2000, 30(3): 286-297. DOI: 10.1109/3468.844354 | ✅ Crossref 已核（卷期页码作者全符） |
| [P2] | SHERIDAN T B, VERPLANK W L. Human and computer control of undersea teleoperators[R]. Cambridge: MIT Man-Machine Systems Laboratory, 1978. DOI: 10.21236/ADA057655 | ✅ Crossref/DTIC 已核（报告类型、1978、两位作者） |
| [P3] | O'HARA J M, HIGGINS J. Human-system interfaces to automatic systems: Review guidance and technical basis[R]. Upton: Brookhaven National Laboratory, BNL-91017-2010, 2010. 含 Sheridan 十级表、Endsley & Kaber 十级模型与 adaptive automation 讨论（PDF: nrc.gov/docs/ML1027/ML102720251.pdf） | ✅ 编号已核实并**更正**：初稿误标为 NUREG/CR-6635，而 NRC 官网显示该编号实为《Soft Controls: Technical Basis and Human Factors Review Guidance》(Stubler/O'Hara, 2000)。正确编号 BNL-91017-2010 经两个独立来源确认（GovInfo NUREG-CR-7264 参考文献条目 + SAGE 期刊引用格式） |
| [P4] | ZHOU X, SAGHI Z, SABOURI S, et al. Cognitive biases in LLM-assisted software development[C]//Proceedings of the 2026 IEEE/ACM 48th International Conference on Software Engineering (ICSE '26). 2026: 2440-2452. DOI: 10.1145/3744916.3773104 （预印本 arXiv:2601.08045，2026-01-12） | ✅ **Crossref 已核正式版**：ICSE '26 会议论文，6 位作者 Zhou/Saghi/Sabouri/Pandita/McGuire/Chattopadhyay，pp.2440-2452；摘要数字（48.8% / 56.4% / 29.46% (238/808) / 90 种偏差·15 类 taxonomy / 14 名观察 + 22 名问卷）已从 arXiv abs 页核对。**注：第一作者是 Zhou，Sabouri 仅为 arXiv 提交者** |
| [P5] | ROMEO G, CONTI D. Exploring automation bias in human–AI collaboration: a review and implications for explainable AI[J]. AI & Society, 2025, 41: 259-278. DOI: 10.1007/s00146-025-02422-7 | ✅ Crossref 已核（**在线首发 2025**；MDPI 二手引用标 2026 卷期，著录以 Crossref 为准） |
| [P6] | ROY D, ZHANG X, BHAVE R, et al. Exploring LLM-based agents for root cause analysis[C]//Companion Proceedings of the 32nd ACM International Conference on the Foundations of Software Engineering (FSE '24). Porto de Galinhas: ACM, 2024: 208-219. DOI: 10.1145/3663529.3663841 | ✅ Crossref 已核；「加入讨论记录无显著增益」出自 arXiv:2403.04123 摘要 |
| [P7] | XU W, LUO J, HUANG T, et al. LogSage: An LLM-based framework for CI/CD failure detection and remediation with industrial validation[C]//ASE 2025. Seoul: IEEE, 2025: 3742-3753. DOI: 10.1109/ASE63991.2025.00310 | ✅ Crossref 已核 |
| [P8] | WANG Z, LIU Z, ZHANG Y, et al. RCAgent: Cloud root cause analysis by autonomous agents with tool-augmented large language models[C]//CIKM '24. Boise: ACM, 2024: 4966-4974. DOI: 10.1145/3627673.3680016 | ✅ Crossref 已核 |
| [P9] | VASALLO C, PROKSCH S, ZEMP T, et al. Un-break my build: Assisting developers with build repair hints[C]//ICPC 2018. Gothenburg: ACM, 2018: 41-51. DOI: 10.1145/3196321.3196350 | ✅ Crossref 已核（8 人案例研究、修复时间缩短 41%） |
| [P10] | k8sgpt-ai/k8sgpt[EB/OL]. GitHub, Apache-2.0. 官方表述 "SRE experience codified into its analyzers"；内置 pod/pvc/event/log 等 analyzer | ⚠️ 项目 README 表述已核；**作为软件引用，论文中建议标注访问日期与 commit** |
| [P11] | HolmesGPT/holmesgpt[EB/OL]. GitHub. CNCF Sandbox 项目，Robusta 创建、微软参与贡献；agentic loop 查询实时可观测数据；toolset 以 YAML 声明工具集 | ⚠️ 同上 |
| [P12] | HASSAN F, WANG X. An empirical study of continuous integration failures in TravisTorrent[R]. San Antonio: UTSA, CS-TR-2018-001, 2018 | ✅ 机构主页与机构库已核 |
| [P13] | Aider chat modes: ask / architect / code[EB/OL]. aider.chat/docs/usage/modes.html | ⚠️ 官方文档已核；作为软件文档引用，建议标注访问日期 |

> 注：[P10]–[P13] 为开源项目与文档，属**软件/电子资源**类引用。若学院要求参考文献
> 全部为学术出版物，可将 k8sgpt / HolmesGPT / Aider 的设计思想在正文中描述为
> 「借鉴开源项目的 analyzer 机制与多模式交互设计」，并在致谢或脚注中给出项目地址。

---

