# GoPulse CI

> 面向小型团队的轻量 CI/CD 工具 —— 毕业设计 · 零增量基础设施：装在你已有的机器上
> commit/push → 自动构建（Docker 隔离）→ 部署（本机 compose / SSH 远程）→ 健康检查 → 失败自动回滚 → LLM 智能诊断
> **核心特色：人为主导的 AI 辅助运维 —— 自动化级别（LOA）可按失败类型配置，并随人工验证动态演进**

单二进制 + 一个 SQLite 文件，无外部数据库、无消息队列、无对象存储。
**三种部署形态全部为真实交付物**（各有硬性端到端验收，见 TODO M4），同一二进制按 `-profile` 显式装配（无隐式默认，三形态地位等同）：

| 形态 | profile | 机器 | 触发 | 部署 | 成本 |
|------|---------|------|------|------|------|
| Ⅰ 个人开发者版 | `personal` | 笔记本 ×1，零公网 | 监视本地 `.git/` | 本机 compose | 0 |
| Ⅱ 简易团队版（论文代表场景） | `team-lite` | 生产服务器合设 ×1 | GitHub webhook | 本机 compose | 0 |
| Ⅲ 完整团队版 | `team-full` | 构建 VPS + 目标机 ×N | webhook | SSH 远程 | 1 台构建机 |

实现顺序 Ⅰ→Ⅱ→Ⅲ（由简入繁，每步只加 adapter），M4 末三形态全部可用并分别通过 E2E 验收。
形态对照详见 `visual/deploy-modes.html`（13 步流水线仅 4 步差异）与 `ARCHITECTURE.md` §3.8/§7。

## 仓库结构

```
graduation-project-cicd/
├── ARCHITECTURE.md      架构设计文档（分层/状态机/数据模型/API/安全/★LOA 引擎★/★三形态解耦★）
├── TODO.md              里程碑清单（M0–M8）与技术债
├── DEPENDENCIES.md      详细依赖清单（前端已实现 / 后端规划）
├── diagrams/            论文级架构图 6 张（SVG）+ 生成脚本
├── visual/              交互式可视化 ×3（index=答辩演示 · guide=全流程原理 · deploy-modes=三形态对照）
└── web/                 前端工程 ✅（Vue 3 + Vite + TS + Tailwind）
    ├── openapi.yaml     API 契约（OpenAPI 3.1，由前端调用反推，后端按此实现）
    └── devopsd/         后端工程 ⬜（Go，M1 启动，见 TODO）
```

## 当前状态

| 部分 | 状态 | 质量基线 |
|------|------|----------|
| 架构设计 / 图 / 可视化 | ✅ | 6 张矢量图 + 3 个交互式页面（演示/原理/三形态） |
| 前端 Web 控制台 | ✅ | 12 页面 · 167 测试全绿 · 覆盖率 95.9% · 零 CDN |
| LOA 策略引擎设计 | ✅ 设计完成 | 见 ARCHITECTURE §4–§5、§8（理论依据 + 数据模型 + API） |
| **三形态解耦设计** | ✅ 设计完成 | 见 ARCHITECTURE §3.8/§7 + `visual/deploy-modes.html`（三接口点 + 三份 profile + 实测证据） |
| Go 后端 | ⬜ M1 起步 | 契约已定（`web/src/types.ts` = 后端 DTO） |
| 前端 LOA 相关页面 | ⬜ 待做 | 扩展 2 页 + 新增 3 页，见 ARCHITECTURE §9 |

## 快速开始（前端，当前可跑）

```bash
cd web
npm install
npm run dev          # http://localhost:5173，Mock 数据，无需后端
```

全部命令：

```bash
npm run dev           # 开发服务器
npm run build         # 类型检查 + 生产构建
npm run test:run      # 167 个测试
npm run test:coverage # 覆盖率报告 → coverage/index.html
```

切真实后端（M1 完成后）：

```bash
cp .env.example .env  # VITE_USE_MOCK=false
# vite 已把 /api 代理到 127.0.0.1:8080
```

## 文档导航

| 想了解 | 看 |
|--------|-----|
| **后端交接（给接手 Go 后端的人，自包含）** | `HANDOVER.md` |
| **三种部署形态怎么选、怎么解耦、怎么演进** | `visual/deploy-modes.html` + `ARCHITECTURE.md` §3.8 |
| 系统怎么分层、状态机、数据模型、安全设计 | `ARCHITECTURE.md` §1–§3 |
| **★ 人机权责分配的理论依据（LOA 模型）** | `ARCHITECTURE.md` §4 |
| **★ LOA 策略引擎设计（Analyzer/白名单/审批/知识库/护栏）** | `ARCHITECTURE.md` §5 |
| LOA 引擎的数据表与新增 API | `ARCHITECTURE.md` §8 |
| **前端要不要改、改哪里、工作量多少** | `ARCHITECTURE.md` §9 |
| 做到哪了、接下来做什么 | `TODO.md` |
| 用了哪些依赖、为什么选 | `DEPENDENCIES.md` |
| 前端细节（目录/设计令牌/测试战果） | `web/README.md` |
| 论文插图 | `diagrams/index.html`（可导出 PDF） |
| 答辩交互演示 | `visual/index.html`（流水线动画含失败诊断分支） |
| 给自己/同学讲原理（小白友好，15 站逐层拆解） | `visual/guide.html` |
| 开题报告（27 条）/ 文献综述（40 条），全部 Crossref/官网核实 | `docs/`（内容与填充分离，可重跑生成） |

## 技术栈一览

**前端（已实现）**：Vue 3.5 · TypeScript 5.7（strict）· Vite 6 · Tailwind 3.4 ·
Vue Router 4 · Vitest 2.1 · 内联 SVG 图标 · 零运行时 UI 库

**后端（规划）**：Go 1.22+ · chi · modernc.org/sqlite（纯 Go 无 CGO）·
sqlc · golang-migrate · docker SDK · x/crypto/ssh · fsnotify（形态Ⅰ本地仓库监视）·
log/slog · Prometheus client

**智能诊断**：OpenAI 兼容协议（云端 / vLLM / Ollama 三选一，换 base_url 即可）；
日志尾部 8KB 脱敏后送审，异步执行，失败不影响构建结果。
输出为**结构化证据链**（结论 + 日志行号锚点 + 原文摘录），不输出无法解释来源的置信度分数。

**★ LOA 策略引擎（核心创新点）**：Go 实现于 `internal/loa/`，无新增外部依赖。
自动化级别按 (项目 × 失败类型 × 动作) 解析；AI 只能在人预先声明的
`context` 白名单内取上下文、只能调用 `actions` 白名单内的动作；
破坏性动作强制 LOA≤4 且不可被策略覆盖；已验证知识达阈值后自动提级，
连续失败即熔断降级。详见 `ARCHITECTURE.md` §5。
