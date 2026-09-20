# TODO — GoPulse CI

> 标记：✅ 完成 · 🔨 进行中 · ⬜ 待做 · ❄️ 暂缓（毕设范围外，进论文“未来工作”）
> 预计周期基于 16 周毕设时间表；前端已完成的部分原计划在 M3，实际已提前完成。
> **三种部署形态**（Ⅰ 个人开发者版 / Ⅱ 简易团队版 / Ⅲ 完整团队版，见 ARCHITECTURE §3.8/§7
> 与 `visual/deploy-modes.html`）：同一二进制按 profile 装配。**三形态均为交付物，不做花瓶** ——
> 实现顺序 Ⅰ→Ⅱ→Ⅲ（由简入繁的工程路径，非优先级排序），M4 末三形态全部可用并各自通过
> E2E 验收（见 M4 出口条件）。形态Ⅱ 为论文代表场景（零增量成本叙事）。

---

## M0 ✅ 设计与前端（已完成，提前）

- [x] 系统架构设计（分层 / 状态机 / 数据模型 / API 契约）
- [x] 论文级架构图 6 张（SVG，`diagrams/`）
- [x] 全流程原理讲解页 `visual/guide.html` + 三形态架构对照 `visual/deploy-modes.html`（交互实测通过）
- [x] Stitch 设计稿 13 屏 + 设计系统 DESIGN.md
- [x] 前端工程化：Vue 3 + Vite + TS + Tailwind，从 13 张静态稿重构
  - [x] 抽共用布局（顶栏/侧栏/状态栏），面包屑/标题由路由 meta 驱动
  - [x] 去 CDN 化：Tailwind 本地编译、图标内联 SVG、字体系统回落
  - [x] API 契约层 + Mock（唯一事实来源）+ USE_MOCK 一键切换
  - [x] SSE 日志流 composable（环形缓冲）+ 轮询 composable
- [x] 前端测试：23 文件 / 167 用例，覆盖率 95.9%（分支 87.5%）
  - [x] 回归钉住 14 个设计稿/实现缺陷（见 web/README.md 测试章节）

## M1 ⬜ 后端骨架（目标 2 周）

- [ ] Go 工程初始化：`cmd/devopsd` + `internal/` 分层（含 `internal/core/ports.go` 与
      `internal/adapters/` 骨架）+ Makefile（build/lint/race）
- [ ] **三接口定义（§3.8，形态解耦的地基，第一天就定，之后不再改）**：
      `TriggerSource` / `CheckoutStrategy` / `DeployTarget`；`main.go` 按 profile 装配（唯一 switch）
- [ ] **Spike：fsnotify 监视 `.git/HEAD` 与 `refs/heads/*` 的事件可靠性**（Windows
      ReadDirectoryChangesW）—— 形态Ⅰ触发的前提，spike 失败则轮询兜底升为主通道（77ms/次已实测）
- [ ] **API 契约冻结**：以 `web/openapi.yaml`（OpenAPI 3.1）为准；先决策 info 里
      列出的 6 个契约缺陷（buildNumber 全局唯一性、created_at 命名、secrets 作用域、
      时间格式、deployment 路径、错误体），改完同步前端 `types.ts`
- [ ] 配置加载（config.yaml + 环境变量密钥名 + **三份 profile 预设 personal/team-lite/team-full**，
      完整 YAML 见 `visual/deploy-modes.html` §5），启动时校验必填项
- [ ] SQLite 接入（modernc.org/sqlite 纯 Go）+ golang-migrate + 001_init.sql（8 张表；
      含形态字段 `projects.source_kind/repo_path`、`deploy_hosts.kind`，见 ARCHITECTURE §3.3）
- [ ] chi 路由骨架 + 请求日志（slog）+ recover 中间件
- [ ] REST：项目 CRUD、构建历史、`GET /api/runner`（对齐前端契约）
- [ ] **ManualTrigger + LocalWatchTrigger**：手动按钮与本地仓库监视各写一条 `queued` 记录 →
      前端可见（闭环第一条竖切）；LocalWatch 防抖 2s + 轮询兜底 5s + SHA 幂等去重
- [ ] **前端切换联调**：`VITE_USE_MOCK=false`，核对每个字段（以 `src/types.ts` 为契约）
- [ ] docker compose 开发环境（后端 + 挂载 data/）

## M2 ⬜ 构建执行（目标 3 周）

- [ ] **gitarchive 检出（形态Ⅰ，先做——零凭据零网络，最简路径）**：`git archive <sha> | tar -x`
      到 `data/workspaces/<build_id>/`（产物不含 .git，已实测）；SHA 不可达 → failed，不静默用 HEAD
- [ ] 持久化队列：原子认领（`UPDATE...RETURNING`）、背压（满则 503）
- [ ] Worker Pool：信号量限流、per-build ctx 超时、panic recover
- [ ] **gitfetch 检出（形态Ⅱ/Ⅲ，详见 ARCHITECTURE §3.7，安全最易错）**：
      Go 侧 `git init`+`fetch --depth=1 <commit_sha>`+`checkout`，凭据走 `projects.git_credential_enc`
      （AES-GCM，**不进 secrets 表**），经 `GIT_CONFIG_COUNT` 环境变量注入、不写 URL/参数；
      检出到 `data/workspaces/<build_id>/`；区分 `git_auth`(不可重试) 与 `transient_network`(可重试)；
      `GIT_TERMINAL_PROMPT=0`、fetch `-q`、token 纳入 redact
      （GitHub webhook 触发链路整体移至 M4——形态Ⅰ不依赖它；形态Ⅱ/Ⅲ 在 M4 合流）
- [ ] 项目类型检测 detect.go（`package.json`/`go.mod`/`Dockerfile`… 规则表）
- [ ] Pipeline 快照生成并写入 `builds.pipeline_json`
- [ ] Builder：docker SDK 建容器（**只读挂载已检出代码目录**）→ 执行步骤 → 产物收集 → `defer` 清理
      （清理用 `context.WithoutCancel`）
- [ ] 先用 `os/exec` 封 docker CLI 跑通，再换 SDK（降低学习曲线风险）
- [ ] 状态机 state.go：迁移表校验 + `build_events` 审计
- [ ] Reconciler：孤儿构建标记 `failed(interrupted)`；清理残留 `data/workspaces/<id>/`
- [ ] 测试：`-race` 全绿；detect/queue/state 单测；platform 打桩；
      **检出专项测试**：凭据不出现在容器 env / clone URL / 日志；commit_sha 不可达时正确置 failed

## M3 ⬜ 实时日志（目标 1 周）

- [ ] Log Pipe：fan-out + ring buffer + 慢订阅者丢弃（不阻塞生产者）
- [ ] SSE 端点 `GET /api/builds/{id}/logs/stream`（对齐前端 `useLogStream`）
- [ ] 日志分块落库（压缩）+ `GET /logs` 分段拉取
- [ ] 联调：浏览器实时滚动、断线重连、`LINES/BUFFER` 计数
- [ ] 前端补充：断线可见提示（`connected` 状态已具备）

## M4 ⬜ 部署与回滚 + 形态Ⅱ/Ⅲ触发链路（目标 3 周）

- [ ] **composelocal 部署（形态Ⅰ/Ⅱ，先做）**：本机 `docker compose up -d` 新镜像 →
      步骤时间线（对齐前端部署详情页）；`deploy_hosts.kind=local` 跳过 SSH
- [ ] **WebhookTrigger（形态Ⅱ/Ⅲ）**：GitHub webhook HMAC 验签、`io.LimitReader` 1MB、
      (repo,sha,ref) 幂等去重、立即 202、事件解析归一化（GitLab 解析器留接口）
- [ ] 部署目标管理 API：主机 CRUD（kind=local/ssh）、连通性测试（docker/compose 预检）
- [ ] **sshremote 部署（形态Ⅲ）**：sshx 私钥解密注入、**Host key 强制校验**、
      `docker save | ssh docker load` 镜像传输（无私有 registry）、执行回报
- [ ] Deployer 统一编排：两种 DeployTarget 走同一步骤时间线
- [ ] **profile 必填校验**：`-profile` 缺失即报错并列出三档（无隐式默认，三形态地位等同）

**★ M4 出口条件 = 三形态 E2E 验收全过（缺一即 M4 不算完成）**：

| 形态 | 验收脚本（可重复执行） | 通过标准 |
|------|----------------------|---------|
| Ⅰ personal | 断网状态：新建本地仓库 → `git commit` → 界面 2s 内出现构建 → Docker 构建 → compose-local 部署 → 健康检查 → **故意改坏代码再 commit → 自动回滚** | 全程零网络请求；同一 commit 不重复触发 |
| Ⅱ team-lite | 本机 Docker 起 toy 生产服务 + devopsd 合设（限额生效验证）：`curl` 模拟 GitHub webhook（自算 HMAC）触发构建部署；再用 cloudflared 隧道接真 GitHub push 跑通一次并录屏 | 构建期间 toy 服务 P95 延迟劣化 < 20%（三道闸有效）；webhook 幂等（重放同一 payload 不重复构建） |
| Ⅲ team-full | WSL2 发行版充当目标机：webhook 触发 → 构建机 `docker save \| ssh docker load` → 远程 compose → 健康检查 → SSH 断连/主机密钥不匹配时正确失败（不静默） | 镜像传输+部署全链路真实走通；FixedHostKey 拒绝伪造主机 |

- [ ] 验收脚本固化到 `scripts/e2e-{personal,lite,full}.sh`（论文「系统测试」章直接引用，答辩可现场跑形态Ⅰ）
- [ ] 健康检查：HTTP 探活 × N 次间隔重试
- [ ] 自动回滚：健康检查失败 → 重部署上一成功版本 → `rolled_back`
- [ ] 回滚 API + 版本历史（对齐前端版本历史 UI）
- [ ] secrets：AES-GCM 加密存储、构建期白名单注入、日志脱敏 redact()
- [ ] 部署日志走同一条 Log Pipe

## M5 ⬜ 智能诊断 · 人主导档 LOA 2/4（目标 3 周）

> 本课题核心创新点的前半部分。理论依据见 ARCHITECTURE.md §4–§5。

- [ ] **Analyzer Registry**：失败类型定义（match 条件 + context 白名单 + forbidden 黑名单 + actions）
      以 YAML 加载，`internal/loa/analyzer.go`
- [ ] **受约束上下文构造**：只按 `analyzer.context` 取数据；`forbidden` 由代码硬隔离，不靠提示词
- [ ] **Action Whitelist**：动作注册表（retry / rollback / verified_fix / notify），
      `destructive` 标记的动作强制 LOA≤4 且不可被策略覆盖
- [ ] **Policy Resolver**：(项目 × 失败类型 × 动作) → LOA；新项目默认 LOA 4
- [ ] llmx：OpenAI 兼容客户端（超时 90s、退避重试 ×2、可换 base_url）
- [ ] truncate：头 1KB + 尾 7KB + 省略占位；redact：按 secrets 表逐项替换后才出网
- [ ] **证据链结构化输出**：提示词强制 JSON（claim / logLines / verbatim / diffHunk），
      解析失败降级为纯文本 rootCause；**不输出百分比置信度**
- [ ] **Approval Gate**：LOA≤4 的动作写入 `approvals` 表排队；approve/reject 端点
- [ ] **人工反馈闭环**：`POST /builds/{id}/diagnosis/feedback`（✅/⚠️/❌）→
      写入 `knowledge` 表，累加 verified_count / rejected_count
- [ ] 异步诊断：`diagnosis_state` 状态位，失败不碰构建状态
- [ ] 建表 `002_loa.sql`（第二个迁移）：`analyzers` / `actions` / `policies` / `knowledge` /
      `approvals` / `automation_audit`（6 张，合计 14 张）；
      同时 `ALTER TABLE builds` 增加 `failure_kind`、`loa_applied` 两列，
      `diagnosis` 列由纯文本改为 JSON（承载证据链）
- [ ] **前端配合**（见 ARCHITECTURE §9.2–9.4）：`types.ts` + `openapi.yaml` 契约先行 →
      `mock.ts` 数据 → `ApprovalsView.vue`（审批中心）→ 诊断页证据链改造 + 反馈按钮 →
      `LogTerminal.scrollToLine(seq)` 行号跳转高亮
- [ ] 评估实验：10–20 组失败样本的诊断命中率、**证据定位准确率**（引用行号是否真含该错误）、
      平均耗时、token 成本（论文数据）

## M6 ⬜ 全自动托管 · LOA 6/7（目标 2 周）

> 核心创新点的后半部分，也是 M7 对照实验的必要条件（没有全自动就无法证明人主导的价值）。
> **范围红线**：只做三类自动动作 —— 瞬态失败重试、已验证修复应用、健康检查失败回滚。
> 依赖自动更新等复杂场景时间不够就砍掉。全自动 **≠** AI 自动写补丁并合入。

- [ ] **知识库命中路径**：error_signature 命中且 verified_count ≥ min_verifications →
      跳过 LLM 直接执行已验证动作，`source='knowledge'`
- [ ] **LOA 动态演进**：验证计数达阈值自动升 LOA；连续 2 次自动修复失败 → **熔断降回 LOA 4** + 通知
- [ ] **预算限制**：每天最多 N 次自动修复 / M 次 LLM 调用，超出转通知
- [ ] **全量审计**：`automation_audit` 表记录 (触发规则、loa_before/after、前后状态、结果、耗时)，可回放
- [ ] **默认安全**：新项目默认关闭全自动，需人显式开启并配置策略
- [ ] SSE 扩展 `event: loa`（级别变更 / 熔断降级 / 审批请求到达）
- [ ] **前端配合**：`ProjectSettingsView` 自动化策略配置区、`KnowledgeView.vue`（知识库）、
      `AutomationAuditView.vue`（审计流水 + 熔断记录 + 预算余量）
- [ ] 演示脚本：夜间构建失败 → 系统自动修复 → 早晨开发者看到完整审计记录（答辩录屏素材）

## M7 ⬜ 并发打磨与 A/B 对照实验（目标 3 周）

- [ ] 优雅关闭：SIGTERM → 停取新任务 → 宽限期 drain
- [ ] Prometheus 指标：构建并发数、队列深度、P95 排队延迟、goroutine 数
- [ ] `GET /metrics` + pprof（`/debug/pprof` 仅本地）
- [ ] 并发压测：N=1/2/4/8/16 × 64 任务，采集吞吐/内存/排队延迟
      （论文实验章节的数据来源，M2 起就接好 Prometheus）
- [ ] **形态资源对比**（论文「部署形态」章数据）：同一构建任务分别在
      personal（限额2cpu）/ team-lite（限额1.5cpu+串行）/ team-full（4并发）三档 profile 下
      采集端到端延迟与峰值内存；合设形态加测「构建期间生产端点 P95 延迟」以验证三道闸有效
- [ ] 对比实验：与 Jenkins / GitLab CI / **Woodpecker CI**（同为 Go + SQLite 的轻量方案，
      官方称空闲时 server ≈100MB、agent ≈30MB，可作资源基线）比安装耗时、空闲内存、配置行数、端到端延迟
- [ ] ★ **A/B 对照实验（创新点的验证方式）**：同一批失败样本分别在
      LOA 4（人批准）与 LOA 7（全自动）下运行，对比
      **撤销率**（对标 Zhou et al. ICSE'26 报告的 29.46%）、**采纳率**、**修复时间**
      （对标 Bart 工具的 41% 缩短）
- [ ] 端到端演示脚本固化（含失败诊断、人批准、自动修复、回滚四条分支）
- [ ] 全站 `-race` + 压测无泄漏（goroutine 数回落后持平）
- [ ] 前端：A/B 实验数据展示（撤销率/采纳率对比图）

## M8 ⬜ 论文与答辩（目标 2 周）

- [ ] 论文初稿（架构图 6 张可直接复用 `diagrams/`；需补 LOA 策略引擎与演进机制图；
      「部署形态与产品分档」一章素材取 `visual/deploy-modes.html` §0/§2/§3 ——
      13 步流水线仅 4 步形态差异 + 三接口点 + 实测证据表）
- [ ] 创新点表述：**混合自动化级别配置 + 级别随人工验证动态演进**（不要写成「接了个大模型」）
- [ ] 对比实验表格 + 压测图表 + A/B 实验结果
- [ ] 演示录屏（备份！答辩现场网络不可信）
- [ ] 答辩 Q&A 准备：为什么 202 立即返回、回滚链怎么建模、诊断为何异步、
      限流参数怎么定、SQLite 够不够用、
      ★ **为什么人为主导不是能力不足**（答：Zhou et al. ICSE'26 的 29.46% 撤销率 +
      automation bias + 小团队无专职 SRE 但开发者本人在场）、
      ★ **全自动模式是否自我否定创新点**（答：二者是同一策略引擎的不同 LOA 配置，
      且全自动是人主导阶段积累知识的消费者；A/B 实验正是靠它做对照组）

---

## 暂缓 / 未来工作（❄️ 写进论文展望，不实现）

- ❄️ 蓝绿 / 滚动发布（当前只做原地替换 + 回滚）
- ❄️ 多构建机调度（当前单机 Worker Pool）
- ❄️ PR 预览环境（每 PR 临时容器 + 评论回链）
- ❄️ Docker Registry 集成（当前本机 tag + tar）
- ❄️ 通知渠道扩展（Webhook 之外：邮件 / IM）
- ❄️ GitLab 全量支持（当前先 GitHub 打深；形态Ⅲ蓝图中 GitLab webhook 解析器只留接口）
- ❄️ Wails 桌面壳（形态Ⅰ的第二交付形态：原生窗口+托盘；核心无头化后加壳即可，6–10 天机动项）
- ❄️ 专注模式（形态Ⅰ：检测用户输入活动时暂缓自动触发 —— profile 开关已留位）
- ❄️ 多用户团队协作（审计日志、细粒度 RBAC）
- ❄️ **AI 自动写代码补丁并合入**（LOA 8）—— 本课题**明确排除**，理由见 ARCHITECTURE §5.5/§5.7
      （Zhou et al. ICSE'26 报告 LLM 相关动作撤销率 29.46%；全自动写码在小团队无人复核时风险不可控）
- ❄️ 依赖自动更新的全自动托管（Renovate 式）—— M6 时间不够则砍，只做三类确定性动作

## 已知技术债

- [ ] 前端侧栏与路由里项目 id 硬编码为 `1`（需要项目上下文推导，M1 联调时一起改）
- [ ] `api/client.ts` 的 BASE 写死 `/api`，部署到反向代理子路径时需要配置化
- [ ] DESIGN.md 的 YAML token 与正文 13 色值未对齐（手改一次即可，tailwind.config.js 已是准的）
- [ ] `log_chunks.content` 的压缩格式未定（候选 zstd），落库前先定协议
