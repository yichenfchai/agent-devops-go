# 后端交接报告 — GoPulse CI

> **读者**：接手 Go 后端开发的工程师。
> **目的**：不看其它文档也能开工。本文覆盖：系统全貌、前端已完成的部分、
> 后端契约（必须遵守）、已知缺陷（动工前先决策）、建议的实施顺序、验收方式。
> **日期**：2026-09-17 · **前端状态**：已完成并通过全部测试（23 文件 / 167 用例）

---

## 1. 项目是什么（30 秒版）

面向小型团队的轻量 CI/CD 工具，毕业设计项目。交付形态是**一个 Go 单二进制
（`devopsd`）+ 一个 SQLite 文件**，跑在一台 VPS 上完成全流程：

```
git push → webhook → 入队 → Docker 容器内构建 → 产物镜像
        → SSH 部署到目标机（docker-compose）→ 健康检查
        ├─ 通过 → deployed
        └─ 失败 → ★LOA 决策点★
              ├─ 命中已验证知识库且 LOA≥6 → 自动执行(重试/回滚/已验证修复) → 写审计
              └─ 未知失败或 LOA≤4 → 日志脱敏 → 调 LLM → 证据链入库
                     → Approval Gate 等人批准（人主导档）
```

技术卖点（论文创新点，实现时不要偏离）：
1. **★ 可控的人机权责分配（LOA 策略引擎）—— 本课题第一创新点**。依据 Parasuraman
   等的四类自动化功能模型，在信息获取/分析环节高自动化，在决策/执行环节保留人主导；
   自动化级别按 (项目 × 失败类型 × 动作) 解析，并随人工验证次数**动态演进**。
   详见 ARCHITECTURE.md §4–§5，实现前先读。
2. Go 并发调度（信号量限流 worker pool + channel 日志管道 + 背压）
3. 项目类型自动检测 + Pipeline 自动生成（零配置接入）
4. LLM 构建失败智能诊断（Go 只做 HTTP 客户端，异步、可失败、不阻塞主流程；
   输出**结构化证据链**而非散文，不输出百分比置信度）
5. 单机轻量：无 Redis / 无消息队列 / 无 K8s，**不要引入任何外部中间件**

范围红线：单构建机、SSH+compose 原地替换部署。**不做**蓝绿/滚动/K8s/多租户。
**全自动模式 ≠ AI 自动写代码补丁并合入**（LOA 8 明确排除，见 ARCHITECTURE §5.5/§5.7）。

---

## 2. 仓库现状

```
graduation-project-cicd/
├── HANDOVER.md          ← 本文
├── README.md            项目门面
├── ARCHITECTURE.md      完整架构设计（分层/状态机/数据模型/安全）
├── TODO.md              M0–M8 里程碑清单（你的任务 = M1–M7）
├── DEPENDENCIES.md      依赖选型及理由（后端部分是你的采购清单）
├── diagrams/            6 张论文级 SVG 架构图
├── visual/              交互式架构演示页（答辩用）
└── web/                 ★ 前端工程（已完成，勿大改）
    ├── openapi.yaml     ★★ API 契约（OpenAPI 3.1，Redocly 校验通过）
    ├── src/types.ts     ★★ DTO 类型（与你的 Go struct 一一对应）
    ├── src/api/index.ts 前端实际调用的 17 个 API 方法（对应契约中 19 个 called 操作）
    ├── src/api/mock.ts  Mock 数据（当前前端靠它跑，字段语义的活文档）
    └── src/api/client.ts fetch 封装（/api 前缀、超时、错误归一化）
```

### 已完成 ✅

| 交付物 | 状态 | 验证方式 |
|--------|------|----------|
| 架构设计 + 6 张图 | 完成 | `diagrams/index.html` |
| 前端 12 个页面（Vue3+TS+Vite+Tailwind） | 完成 | `cd web && npm run dev` |
| 前端测试 167 用例，覆盖率 95.9% | 全绿 | `npm run test:run` |
| API 契约 openapi.yaml（26 操作/21 schema） | 完成，Redocly 0 error | `npx @redocly/cli lint openapi.yaml` |
| Mock 数据层（可整体删除） | 完成 | `web/src/api/mock.ts` |

### 待做 ⬜（全部是你的）

M1 骨架 → M2 构建执行 → M3 SSE 实时日志 → M4 部署回滚
→ **M5 智能诊断·人主导档 LOA 2/4** → **M6 全自动托管·LOA 6/7** → M7 并发打磨与 A/B 对照实验。
每个里程碑的验收标准见 `TODO.md`，此处不重复。

**M5/M6 是本课题的核心创新点所在**，不要当成"最后加个 AI 功能"来做 ——
Analyzer Registry、Action Whitelist、Policy Resolver、Approval Gate、Knowledge Store
这五个组件决定了论文能不能立住。开工前先读 ARCHITECTURE.md §4–§5、§8。

---

## 3. 系统架构（后端视角）

### 3.1 进程内模块

单二进制，模块间用 Go interface 解耦（`internal/platform/` 下三个外部依赖
全部接口化：Docker / SSH / LLM —— 单测打桩，不起真容器）。

```
cmd/devopsd/main.go        装配 + 启动 + 优雅关闭（SIGTERM → drain）
internal/
  config/                  YAML + 环境变量（密钥只存环境变量名，不存值）
  httpapi/                 chi 路由：webhook / REST / SSE / auth / approvals
  scheduler/               持久化队列（SQLite 行即队列）+ worker pool + 生命周期
  build/                   状态机 / 执行编排 / 项目检测 / pipeline 生成
  deploy/                  SSH 执行 / 健康检查 / 回滚
  logpipe/                 fan-out 广播 + ring buffer + 批量落库
  diagnose/                LLM 客户端 + 裁剪 + 脱敏 + prompt + 证据链解析
  loa/            ★新增★   核心创新点模块（详见 ARCHITECTURE.md §5）
    analyzer.go              Analyzer Registry：失败类型匹配 + context 白名单 + forbidden 黑名单
    action.go                Action Whitelist：注册动作（retry/rollback/verified_fix/notify）
                               destructive 动作强制 LOA≤4，不可被策略覆盖
    policy.go                Policy Resolver：(项目 × 失败类型 × 动作) → LOA
    evidence.go              Evidence Binder：诊断结论强制绑定日志行号锚点
    approval.go              Approval Gate：LOA≤4 动作排队等人批准
    knowledge.go             Knowledge Store：已验证三元组 + 验证计数 → 驱动 LOA 演进
    guardrail.go             熔断降级 / 预算限制 / 审计写入
  store/                   sqlc 生成查询 + goose 迁移
  crypto/                  AES-GCM（secrets、SSH 私钥、webhook secret、git 凭据）
  platform/{dockerx,sshx,llmx}/   外部依赖接口 + 实现
  vcs/                     GitHub/GitLab 事件解析 → 统一内部事件；checkout.go 代码检出（§3.7）
pkg/api/types.go           对外 DTO —— 必须与 web/src/types.ts 对齐
```

`internal/loa/` 是本课题区别于普通 CI 工具的关键模块。**设计约束**：
LLM 的输出只能用于填充 `evidence`（自然语言结论 + 日志行号引用），
**不能**由 LLM 决定调用哪个动作 —— 动作必须来自 `action.go` 的注册表，
且必须先经 `policy.go` 解析出的 LOA 判断是自动执行还是进审批队列。
这条边界一旦破了，"人为主导"的创新点就不成立了。

### 3.2 goroutine 拓扑（并发模型，M7 压测的对象）

```
main
 ├── Scheduler          ×1   取任务；同一项目串行化（防两个部署同时改一台机器）
 ├── Worker Pool        ×N   chan struct{} 信号量限流（默认 N=4，可配）
 │    └── per-build goroutine
 │         ├── Builder        Docker 容器执行；ctx 超时（默认 30m）超时 kill
 │         ├── Log Reader     容器 stdout → LogPipe（逐行加时间戳）
 │         ├── Log Writer     批量落库（200 行或 2s flush 一次）
 │         └── Diagnoser      失败时异步调 LLM，独立 goroutine
 ├── HTTP server        ×M   每请求一个（net/http 默认模型）
 │    └── SSE handler        订阅 LogPipe，慢客户端丢弃不阻塞
 ├── Reconciler         ×1   30s 周期：孤儿构建标记 failed(interrupted)、超时清理、旧产物 GC
 └── signal handler     ×1   SIGTERM → 停止取新任务 → WaitGroup 宽限期 drain
```

六条铁律（代码评审按这个卡）：
1. 每个 goroutine 必须有明确退出路径（channel close 或 ctx cancel）
2. 谁创建 channel 谁关闭，只在发送方关闭
3. 不持锁做 IO
4. 所有阻塞 IO 带 ctx + 超时（Docker/SSH/HTTP 都会挂）
5. **清理逻辑用 `context.WithoutCancel`**（否则取消后容器/连接泄漏 —— 最经典的坑）
6. 测试全程 `-race`

### 3.3 构建状态机

```
queued → running → succeeded → deploying → deployed
           │                       │           │(手动)
           ▼                       ▼           ▼
        failed ◀────────────  deploy_failed → rolled_back ←(自动回滚也到这)

diagnosis_state: none → pending → done/failed   （独立字段，异步，不影响主干）
```

- 迁移表硬编码校验，非法迁移返回错误并记日志
- 每次迁移 INSERT 一行 `build_events`（审计 + 论文里的时序回放图）
- 崩溃恢复：启动时把所有 `running/deploying` 的孤儿行标记 `failed(interrupted)`

### 3.4 数据模型（14 张表，SQLite）

完整 DDL 见 `ARCHITECTURE.md` §3.3（基础 8 张）与 §8.1（LOA 引擎新增 6 张）。要点：

| 表 | 关键约束/索引 | 为什么 |
|----|--------------|--------|
| `builds` | `UNIQUE(project_id, number)`；部分索引 `WHERE state IN ('queued','running','deploying')` | number 是项目内序号；调度器只查活跃行 |
| `builds.pipeline_json` | 每次构建存**执行时快照** | 检测规则以后改了，历史构建仍可复现 |
| `builds.failure_kind` / `loa_applied` | 新增两列 | 记录本次命中的失败类型与生效的自动化级别（论文实验要按 LOA 分组统计）；`failure_kind` 含 `git_auth`(凭据失效,不可重试) / `transient_network`(可重试) 等 |
| `projects.git_auth_type` / `git_credential_enc` | AES-GCM 专用列，**独立于 `secrets`** | 代码检出凭据；secrets 语义是「注入容器的 env」，git 凭据只在 `internal/vcs` 解密到内存、用完清零，绝不进容器（§3.7） |
| `builds.diagnosis` | 由纯文本改为 **JSON** | 承载证据链结构（claim / logLines / verbatim / diffHunk） |
| `build_events` | append-only | 状态机审计 |
| `deployments.previous_deployment_id` | 自引用外键 | 回滚链显式建模，不靠时间戳猜 |
| `log_chunks` | `UNIQUE(build_id, seq)`，content 压缩 BLOB | 大日志不进主表；seq 支撑 SSE 断线补发与**证据链行号锚点** |
| `secrets` / `deploy_hosts.ssh_key_enc` / `projects.webhook_secret_enc` | AES-GCM BLOB | 主密钥只在环境变量，DB 文件泄漏≠secret 泄漏 |
| `knowledge` ★ | `UNIQUE(project_id, error_signature)` | LOA 演进的核心：验证计数达阈值才允许自动执行 |
| `approvals` ★ | 部分索引 `WHERE state='pending'` | LOA≤4 动作的人机审批队列 |
| `automation_audit` ★ | `(project_id, id DESC)` | 全自动模式每个动作可回放；熔断记录 loa_before/loa_after |
| `analyzers` / `actions` / `policies` ★ | `actions.destructive` 布尔 | 白名单与策略配置；破坏性动作强制 LOA≤4 |

★ = LOA 引擎新增（M5/M6）。**`log_chunks.seq` 是证据链行号锚点的基础** ——
诊断里引用的 `logLines` 必须能对回 `seq`，否则前端的"点击跳转到日志行"无法实现。

认领队列的原子性（多协程/未来多实例安全）：
```sql
UPDATE builds SET state='running', started_at=... 
WHERE id IN (SELECT id FROM builds WHERE state='queued' ORDER BY id LIMIT ?)
RETURNING ...;
```

### 3.5 关键流程的正确性要点

**Webhook（最容易被做错的地方）**
- 验签：GitHub `X-Hub-Signature-256: sha256=<hex>`（HMAC-SHA256，每项目独立 secret）；GitLab `X-Gitlab-Token` 明文比对
- 请求体 `io.LimitReader` 1MB，超限 413
- **验签通过 → 解析 → 入队 → 立即 202**。绝不同步构建（平台 10s 超时 → 重试风暴）
- 幂等：同 `repo+sha+ref` 短窗口去重（内存 LRU 即可），命中返回 202 + `deduplicated:true`
- 队列满返回 503（背压，平台会重试）—— 这是设计行为不是错误

**代码检出（M2 前置，安全最易错，详见 ARCHITECTURE §3.7）**
- **检出在 Go 侧做，不在构建容器里 clone**：凭据若以 env 传进容器，构建脚本 `env`/`set` 即可读到 → 泄漏面大，违反「secret 白名单注入」基调
- 检出到 `data/workspaces/<build_id>/`，再**只读挂载**进构建容器；容器内无任何 git 凭据
- **凭据存 `projects.git_credential_enc`（AES-GCM），绝不进 `secrets` 表** —— secrets 的语义是「注入容器的 env」，git 凭据走独立取用路径，只在 `internal/vcs` 解密到内存、用完 `defer` 清零
- 凭据注入用 git 2.31+ 的 `GIT_CONFIG_COUNT` 环境变量式临时配置（`http.extraHeader: AUTHORIZATION: bearer ***`），**不写进 clone URL、不放命令行参数**（两者都会落盘或被 `ps` 看到）；已实测注入值不落盘、unset 即消失
- **精确检出 webhook 的 `commit_sha`，不是 ref 最新**（否则 ref 已前进时构建的不是触发那次提交，破坏可复现）；`--depth=1` 浅取
- GitHub 已实测支持按任意历史 SHA 浅 fetch + checkout；带回退策略：`fetch <sha>` → 失败回退 `fetch <ref>` + `checkout <sha>` → 仍不可达则 `failed`，不静默用 ref 最新
- `git_auth_type`: `none`(公开) | `https_token`(主推，fine-grained PAT / GitLab Deploy Token，单仓库只读) | `ssh_deploy_key`
- **区分失败类型**（喂给 §5 LOA 策略）：`401/403`/`Authentication failed` → `failure_kind=git_auth`，提示更新凭据，**不可自动重试**；连接超时/DNS/TLS → `failure_kind=transient_network`，允许 LOA≥6 自动重试
- `GIT_TERMINAL_PROMPT=0`（防交互卡死 + 防凭据回显）；fetch 加 `-q`；git token 纳入 `redact` 词表

**构建**
- 每任务一个容器：create → start → wait → 收集产物（docker commit 或 tar）→ **defer remove（用 WithoutCancel）**
- 代码目录**只读**挂载进容器（见上「代码检出」）；容器不挂 Docker socket（防逃逸）；secret 按项目白名单注入 env
- 日志从 `ContainerLogs` 流式读，逐行推进 LogPipe

**部署**
- SSH `HostKeyCallback` 必须校验（`ssh.FixedHostKey` 或 known_hosts），这是论文安全章节的论点，不能省
- 部署前环境预检：docker / docker-compose 存在性（`/hosts/{id}/test` 同款逻辑）
- 健康检查：GET healthCheckUrl × N 次（间隔 3s），全过才 `deployed`
- 失败且 `auto_rollback=1`：取 `previous_deployment_id` 的 image_tag 重新部署 → `rolled_back`
- 版本保留：目标机保留最近 K 个镜像 tag，超出清理

**LLM 诊断**
- 触发：构建/部署进入 failed 系状态后，独立 goroutine
- 输入：日志头 1KB + 尾 7KB（中间省略占位）；**先按 secrets 表逐项脱敏再出网**
- OpenAI 兼容 POST `{base_url}/chat/completions`；超时 90s；指数退避重试 2 次
- 结果写 `builds.diagnosis` + `diagnosis_state='done'`；任何失败写 `'failed'`，**绝不改构建状态**
- 可选优化：日志尾部 hash 做缓存键，相同错误不重复烧 token

---

## 4. API 契约（你必须遵守的部分）

**唯一事实来源：`web/openapi.yaml`**（OpenAPI 3.1，Redocly lint 通过）。
每个操作带 `x-frontend` 标记：

- `called`（19 个）：前端已在调用，**路径、方法、字段名、语义都不能改**
- `ui-only`（5 个）：界面有按钮但前端 api 层未接线（保存设置/删除项目/删除密钥/添加主机/重新诊断）——你实现后，前端接线是小事
- `backend-only`（2 个）：webhook / login（SSE 流标为 called，走 EventSource 而非 fetch）

DTO 形状以 `web/src/types.ts` 为准（camelCase JSON）。Go 侧建议：

```go
type Build struct {
    ID            int64      `json:"id"`
    ProjectID     int64      `json:"projectId"`
    Number        int        `json:"number"`
    State         BuildState `json:"state"`
    Trigger       Trigger    `json:"trigger"`
    Ref           string     `json:"ref"`
    CommitSha     string     `json:"commitSha"`
    CommitMessage string     `json:"commitMessage"`
    CommitAuthor  string     `json:"commitAuthor"`
    BaseImage     *string    `json:"baseImage"`     // 可空字段一律指针 + omitempty 慎用
    ImageTag      *string    `json:"imageTag"`      // 前端显式判 null，不要省略字段
    ExitCode      *int       `json:"exitCode"`
    QueuedAt      string     `json:"queuedAt"`
    StartedAt     *string    `json:"startedAt"`
    FinishedAt    *string    `json:"finishedAt"`
    DurationMs    *int64     `json:"durationMs"`
    Diagnosis     *Diagnosis `json:"diagnosis"`
}
```

注意：**可空字段必须显式输出 `null`**，不要 `omitempty` 省略 ——
前端 TypeScript 类型是 `string | null`，`undefined` 和 `null` 语义不同，
且 167 个测试里有多处断言依赖字段存在。

### SSE 协议（`GET /builds/{n}/logs/stream`）

前端用原生 `EventSource`，协议必须严格是：

```
data: {"seq":41,"ts":"10:24:32","text":"...","level":"error"}\n\n
```

- 每帧一个 LogLine JSON，`data:` 前缀，空行结尾
- 新订阅先补发 ring buffer 最近 N 行
- 支持 `Last-Event-ID` 头（值=seq），断线重连按 seq 补发
- 构建终态后发完剩余日志即关闭连接（前端 `onerror` 会置「未连接」态）
- 响应头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、`Connection: keep-alive`
- 慢消费者**丢弃**（前端有 2000 行环形缓冲兜底，不会崩）

### 联调切换

```bash
cd web
cp .env.example .env      # VITE_USE_MOCK=false
npm run dev               # vite 已把 /api 代理到 127.0.0.1:8080
```

`web/src/api/mock.ts` 的字段值就是验收样例（#1091 失败构建、#1092 运行中、
a3f9c21、28140ms、build-runner-01……）。**联调时让后端返回与 mock 同形状的数据，
前端 167 个测试所断言的一切就都成立。** mock.ts 在全面联调后可整体删除。

### ★ LOA 引擎的契约变更（M5/M6，动工前必读）

现有的 26 个操作是**已冻结**的，不要动。LOA 引擎带来的是一批**新增**端点
（完整定义见 ARCHITECTURE.md §8.2）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/builds/{id}/diagnosis/feedback` | 人工标记 ✅/⚠️/❌，驱动知识沉淀与 LOA 演进 |
| GET | `/api/approvals?state=pending` | 待审批动作队列 |
| POST | `/api/approvals/{id}/approve` · `/reject` | 批准 / 驳回（LOA 4 的人机关口） |
| GET/PUT | `/api/projects/{id}/policy` | 项目级自动化策略配置 |
| GET | `/api/analyzers` · `/api/actions` | 失败类型分析器 / 动作白名单（含 `destructive`） |
| GET | `/api/projects/{id}/knowledge` | 已验证知识库（verified_count / loa_current） |
| GET | `/api/projects/{id}/automation/audit` | 自动执行审计流水（可回放） |
| GET | `/api/automation/stats` | 自动修复次数 / 熔断次数 / LLM 预算余量 |

**一处破坏性变更**：`GET /builds/{id}/diagnosis` 的返回体从「`rootCause` + `suggestion`
两段纯文本」扩展为**结构化证据链**（新增 `evidence[]` / `confidenceBasis` / `source` /
`analyzerKey` / `loaApplied`，见 ARCHITECTURE §9.4 的 `Diagnosis` 定义）。

- 前端现有的诊断卡只读 `rootCause` / `suggestion`，**这两个字段名与语义不变**，
  所以旧页面不会崩；新增字段是纯增量。
- 但 `types.ts` 与 `openapi.yaml` 里的 `Diagnosis` schema 需要扩展，
  **按 §5 的同一流程走**：先改契约 → 改 types.ts / mock.ts → 跑测试 → 再写 Go。
- SSE 通道增加 `event: loa`（级别变更 / 熔断降级 / 审批请求到达）。
  这是**新事件类型**，不影响现有 `data:` 日志帧；前端老版本忽略未知事件即可。

**时序建议**：M5 开工前先和前端把 `Diagnosis` 扩展与 `approvals` 的契约定下来
（沿用 mock 驱动模式，前端可以先拿假数据把审批中心页面做出来）。

---

## 5. 已知契约缺陷 —— 动工前先决策（M1 第一项任务）

这些是前端快速迭代留下的债，openapi.yaml 的 `info.description` 里有同样清单。
**先改契约再写实现**，否则会把缺陷固化进数据库：

| # | 缺陷 | 建议决策 | 影响面 |
|---|------|---------|--------|
| 1 | `/builds/{buildNumber}`：number 仅项目内唯一，全局会撞 | 改用全局唯一 build id，或路径带项目 `/projects/{pid}/builds/{n}` | 前端 router + api 约 6 处，半小时改完 |
| 2 | `Project.created_at` 是唯一 snake_case | 统一 `createdAt` | types.ts 1 行 + mock 1 行 |
| 3 | secrets 前端调全局 `/secrets`，库里是项目级 | 改 `/projects/{pid}/secrets` | 前端 api 2 个方法 |
| 4 | 时间字段是人类文案（"3 分钟前"）非 ISO 8601 | 后端返回 ISO/epoch，相对时间前端算 | **最大的一条**：前端需要加一个 timeAgo 工具函数 + 各视图小改；不做的话无法排序/缓存过期 |
| 5 | `/deployments/{buildNumber}` 风格不一致 | 改 `/builds/{n}/deployment` | 前端 1 行 |
| 6 | 错误响应体未定义 | 采用 openapi 里的 `Error` schema（`{error, code}`） | 前端 client.ts 顺手解析 body 展示 |

决策完 → 改 openapi.yaml → 改 types.ts / api/index.ts → 跑 `npm run test:run`
（测试会告诉你哪些断言要跟着改）→ 再开始写 Go。**契约冻结后不再改。**

其它已知技术债（不阻塞后端，见 TODO.md）：前端项目 id 硬编码为 1；
`Secret.isSecret=false` 时缺 `displayValue` 字段（mock 硬编码了 'production'）。

---

## 6. 建议实施顺序（每步都有可演示物）

**原则：垂直切片，不要横向铺层。** 第一周就打通一条最窄的全流程，
之后每步替换成真的。任何一天停下来，都有能演示的东西。

```
第 1 步（骨架竖切）：
  POST /projects（写库）→ GET /projects（读库）→ 前端关掉 mock 能看到项目列表
  含：config、goose 迁移、chi 路由、slog、sqlc 跑通

第 2 步（假构建闭环）：
  POST /projects/{id}/builds → 写 queued 行 → 极简 worker（sleep 5s）→ succeeded
  GET /builds/{n} /stages /logs 返回假数据 → 前端构建历史页活了

第 3 步（真构建）：
  worker 换成 Docker 执行 + detect.go 项目检测 + LogPipe 落库
  先用 os/exec 封 docker CLI，跑通后再换 SDK（降风险）

第 4 步（SSE）：
  /logs/stream + ring buffer + Last-Event-ID → 前端实时日志滚动

第 5 步（部署回滚）：
  sshx + compose up -d + 健康检查 + 自动回滚 + /hosts /deployments

第 6 步（LLM 诊断 + LOA 人主导档）：★ 核心创新点前半 ★
  6a. Analyzer Registry + Action Whitelist + Policy Resolver（先不做 LLM，纯规则也能跑）
  6b. llmx + truncate + redact + 证据链 JSON 解析 → 前端紫卡出真数据
  6c. Approval Gate（approvals 表 + approve/reject 端点）
  6d. 人工反馈闭环（feedback 端点 → knowledge 表验证计数）
  演示物：故意失败构建 → 诊断卡带可点击的日志行号 → 人点批准 → 动作执行

第 7 步（全自动托管档）：★ 核心创新点后半 ★
  知识库命中路径（verified_count ≥ 阈值 → 跳过 LLM 直接执行）
  + LOA 动态演进 + 熔断降级 + 预算限制 + automation_audit 全量审计
  + SSE event: loa
  演示物：同类失败第 3 次 → 系统自动修复 → 审计页可回放全过程

第 8 步（加固与实验）：
  限流/优雅关闭/孤儿恢复/Prometheus/pprof + 压测（N=1..16 × 64 任务）
  + ★A/B 对照实验（LOA 4 vs LOA 7 的撤销率/采纳率/修复时间）→ 论文实验数据
```

每步完成的定义：**对应前端页面用真实后端跑通 + `go test -race ./...` 全绿**。

---

## 7. 环境与验收

### 开发环境要求

- Go 1.22+（`CGO_ENABLED=0` 必须可编译 —— modernc sqlite 是纯 Go，别换 mattn 驱动）
- Docker Desktop（构建执行用）
- Node 20+（跑前端联调；本机已装 v24）
- 目标机：任意装了 docker + docker-compose 的 Linux（WSL2 发行版即可充当）

### 后端验收清单（对照 TODO.md M1–M7）

```bash
go vet ./... && golangci-lint run      # 静态检查
go test -race ./...                     # 全部单测（platform 打桩，无需真 Docker）
go build -o devopsd ./cmd/devopsd       # 单二进制
```

功能验收（前端联调，`VITE_USE_MOCK=false`）：
1. 创建项目 → webhook 配置页给出 URL+secret → GitHub 实仓 push 触发
2. 构建实时日志滚动 → 成功后自动部署 → 打开目标机 URL 见新版本
3. 提交语法错误 → 构建失败 → AI 诊断卡出现真实建议，**且证据链里的日志行号可点击跳转到对应行**
4. 部署后杀掉应用进程 → 健康检查失败 → 自动回滚 → 旧版本恢复
5. 同时触发 5 个构建 → 并发 ≤ N，其余排队，无死锁无泄漏
6. `kill -TERM devopsd` → 在跑的构建完成或被标记，重启后孤儿恢复

**LOA 引擎专项验收（M5/M6，创新点的验收）：**

7. **受约束上下文**：构造一个 secrets 里有值的构建失败 → 检查发往 LLM 的 payload，
   确认敏感值已被替换，且 `forbidden` 声明的上下文（其他项目日志、SSH 私钥）根本没被读取
   （建议在此处加断言测试，而不只是人工看日志）
8. **动作白名单**：让 LLM 返回一个未注册的动作名 → 引擎必须拒绝执行并记录审计，不得崩溃
9. **审批关口**：默认策略（LOA 4）下触发失败 → 动作进入 `approvals` 且**不执行** →
   前端批准后执行 → 驳回则记录负反馈且不执行
10. **破坏性动作不可提权**：把策略配成 LOA 7 后触发一个 `destructive` 动作 →
    仍必须停在审批队列（策略不能覆盖硬约束）
11. **知识沉淀与演进**：同一类失败连续人工标记 ✅ 三次 →
    `knowledge.verified_count` 达阈值 → 第四次同类失败**不调 LLM**、自动执行、写审计
12. **熔断降级**：连续两次自动修复失败 → LOA 降回 4 + 产生通知 + `automation_audit` 记录
    `outcome='circuit_broken'` 与 `loa_before/loa_after`
13. **预算限制**：把每日自动修复上限设为 1 → 第二次触发时不再自动执行，转为通知
14. **诊断失败不影响主干**：把 LLM base_url 指向不通的地址 → 构建状态照常流转为 `failed`，
    `diagnosis_state='failed'`，流水线不阻塞
15. **审计可回放**：任取一次自动执行记录，能从 `automation_audit` 还原出
    触发规则、前后状态、耗时（论文里"全自动可审计"的兑现）

### 前端回归（改契约后必跑）

```bash
cd web
npm run test:run      # 167 用例必须全绿
npm run build         # vue-tsc 类型检查 + 构建
```

前端测试里有大量**数据一致性回归断言**（#1091=28140ms、build-runner-01 唯一命名、
tsc 失败日志不得出现 vite banner 等）。后端返回的数据若与 mock 形状一致，
这些断言天然成立；若你有意改语义，先改测试再改实现，不要反过来。

---

## 8. 快速上手命令

```bash
# 看前端跑起来的样子（mock 数据，无需后端）
cd web && npm install && npm run dev     # http://localhost:5173

# 契约文档
npx @redocly/cli lint openapi.yaml       # 校验
npx @redocly/cli preview-docs openapi.yaml  # 浏览器里读（推荐先做这个）

# 生成 Go 骨架（可选，M1 用）
go install github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@latest
oapi-codegen -package api -generate types,chi openapi.yaml > pkg/api/generated.go
# 注意：生成物只做参考底稿，DTO 手写在 pkg/api/types.go 更可控

# 架构图 / 演示
start diagrams/index.html    # 6 张论文图
start visual/index.html      # 交互演示（含失败诊断动画）
```

---

## 9. 联系方式与边界

- **不要改**：`web/src/components/`、`web/src/views/` 的视觉与文案
  （与 Stitch 设计稿对齐过、经过逐屏视觉核验；契约缺陷 #1–#6 涉及的
  types.ts / api/index.ts / router.ts 修改除外，且改完必须 167 测试全绿）
- **不要引入**：Redis、消息队列、K8s client、ORM（理由见 DEPENDENCIES.md「不引入清单」）
- **拿不准就查**：ARCHITECTURE.md（设计全貌）、DEPENDENCIES.md（选型理由）、
  TODO.md（任务分解）、openapi.yaml info.description（契约缺陷）

祝顺利。前端这边 167 个测试会替你把关 —— 它们比文档更诚实。
