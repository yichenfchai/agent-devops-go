# 毕设学习资源清单

> 毕设主题：Go 轻量级 CI/CD 工具（Docker 构建隔离、SSH 部署回滚、LLM 构建失败诊断）
> 所有链接已于 2026-09 用 curl 验证可访问（✅ = 实测 200；⚠️ = 反爬或本机网络原因未测通，浏览器可正常打开）。
> 每章末尾标注了与毕设的相关度，⭐⭐⭐ = 直接影响毕设，⭐ = 背景补充。

---

## 一、Agent / LLM 开发（对应「构建失败诊断」模块）⭐⭐⭐

### 入门必读（按顺序）

- [ ] **Anthropic《Building Effective Agents》** ✅ — 公认最好的 agent 设计入门文，讲清 workflow vs agent、何时不该用 agent。答辩可直接引用
  https://www.anthropic.com/engineering/building-effective-agents
- [ ] **Prompt Engineering Guide** ✅ — 提示工程系统教程（含中文版），prompt 设计的速查手册
  https://www.promptingguide.ai
- [ ] **上交《动手学大模型 / Dive into LLMs》** ✅ — 上海交大张倬胜团队，54k+ star，公益免费。11 章「课件 PDF + 教程 + 可运行脚本」
  https://github.com/Lordog/dive-into-llms
  重点章节（与你毕设最相关）：
  - Ch2 提示学习与思维链：https://github.com/Lordog/dive-into-llms/tree/main/documents/chapter2
  - Ch9 GUI 智能体：https://github.com/Lordog/dive-into-llms/tree/main/documents/chapter9
  注意：代码是 Python，概念可迁移到 Go 实现；适合作论文参考文献
- [ ] **Hugging Face AI Agents Course** ⚠️（大陆需代理）— 免费系统课程，几小时建立 agent 全局认知
  https://huggingface.co/learn/agents-course
  GitHub 镜像仓库 ✅：https://github.com/huggingface/agents-course

### 工程实战

- [ ] **Datawhale《Deep Agents 实战》** ✅ — LangChain 官方大使出品，从零构建生产级 Agent：任务规划、子代理编排、长期记忆、Human-in-the-Loop、沙箱执行。中文、持续更新，B 站有配套视频
  https://github.com/datawhalechina/deepagents-in-action
- [ ] **LangGraph 官方文档** ✅ — 生产级有状态 agent 编排的事实标准，学它的 state/checkpoint 设计思想（Go 里自己实现同理）
  https://docs.langchain.com/oss/python/langgraph/overview

### Go 技术栈（毕设代码直接用）⭐⭐⭐

- [ ] **CloudWeGo Eino** ✅ — 字节开源的 Go 原生 LLM/Agent 框架，中文文档全，和你技术栈完全匹配，**首选**
  文档：https://cloudwego.cn/docs/eino/overview/
  源码：https://github.com/cloudwego/eino
- [ ] **MCP 官方 Go SDK** ✅ — Model Context Protocol 的 Go 实现，诊断模块想接工具生态就靠它
  https://github.com/modelcontextprotocol/go-sdk
- [ ] **OpenAI Function Calling 文档** ⚠️（403 反爬，浏览器正常）
  https://platform.openai.com/docs/guides/function-calling
- [ ] **Anthropic Tool Use 文档** ✅
  https://docs.anthropic.com/en/docs/agents-and-tools/tool-use

---

## 二、Go 程序设计 ⭐⭐⭐

### 入门 → 熟练

- [ ] **A Tour of Go** ✅ — 官方交互式入门，几小时过一遍
  https://go.dev/tour/
- [ ] **Effective Go** ✅ — 官方惯用法，写地道 Go 必读
  https://go.dev/doc/effective_go
- [ ] **Go by Example** ✅ — 每个知识点一个可运行小例子，当速查手册用
  https://gobyexample.com
- [ ] **Learn Go with Tests** ✅ — 测试驱动方式学 Go，同时把 testing 练了；有中文版（仓库内）
  https://github.com/quii/learn-go-with-tests

### 进阶 → 深入原理（论文素材也从这里挖）

- [ ] **《Go 语言设计与实现》（draveness）** ✅ — 调度器、channel、内存模型、GC 讲得最深，中文 Go 进阶首选
  https://draveness.me/golang
- [ ] **《Go 语言高级编程》（柴树杉/曹春晖）** ✅ — CGO、RPC、Web 框架实现、分布式等高阶主题，免费在线阅读
  https://chai2010.cn/advanced-go-programming-book/
  源码仓库：https://github.com/chai2010/advanced-go-programming-book
- [ ] **Go Code Review Comments** ✅ — Google 内部 Go 代码评审标准，写完代码对照自查
  https://github.com/golang/go/wiki/CodeReviewComments

### CI/CD 领域参考实现（读源码 = 最好的教程）⭐⭐⭐

- [ ] **Woodpecker CI** ✅ — Go 写的轻量 CI，server + agent + pipeline 架构和你的项目同构，**强烈建议通读**
  https://woodpecker-ci.org
- [ ] **Gitea act_runner** ✅ — Go 写的任务执行器，看它怎么调度容器跑 job
  https://gitea.com/gitea/act_runner
- [ ] **Drone CI** — Go 老牌 CI/CD，容器化构建范本
  https://github.com/harness/drone
- [ ] **GitHub Actions 文档** ✅ — pipeline/workflow/job/step 概念模型（业界事实标准）
  https://docs.github.com/en/actions
- [ ] **GitLab CI 文档** ✅ — YAML 语法设计 + runner 机制
  https://docs.gitlab.com/ee/ci/

### 毕设三大依赖库

- [ ] **Docker Go Client** ✅ — 构建模块直接调它
  https://pkg.go.dev/github.com/docker/docker/client
  Docker 官方文档：https://docs.docker.com/
- [ ] **golang.org/x/crypto/ssh** ✅ — 部署模块远程执行
  https://pkg.go.dev/golang.org/x/crypto/ssh
- [ ] **pkg/sftp** — SSH 文件传输
  https://github.com/pkg/sftp
- [ ] **testcontainers-go** ✅ — 测试里起真实 Docker 容器验证构建模块，毕设测试章节的亮点
  https://golang.testcontainers.org
- [ ] **testify** — Go 断言/mock 标准选择
  https://github.com/stretchr/testify

---

## 三、TypeScript ⭐⭐

### 主线教程（按顺序）

- [ ] **TypeScript 官方 Handbook** ✅ — 最权威、最新的教程，从 The Basics 读到 Narrowing、Generics、Utility Types
  https://www.typescriptlang.org/docs/handbook/intro.html
- [ ] **Total TypeScript 免费教程（Matt Pocock）** ✅ — 练习驱动的免费入门课，社区公认最好的 TS 教学者
  https://www.totaltypescript.com/tutorials/beginners-typescript
  全部免费教程列表：https://www.totaltypescript.com/tutorials
- [ ] **TypeScript 入门教程（徐超 / ts.xcatliu.com）** ✅ — 中文入门书，结构清晰，适合快速过一遍
  https://ts.xcatliu.com
- [ ] **TypeScript 中文手册翻译（zhongsp）** ✅ — 官方文档中文翻译，跟进版本更新
  https://github.com/zhongsp/TypeScript

### 练习与进阶

- [ ] **type-challenges** ✅ — TS 类型体操练习场，从 easy 开始刷；毕设用不到 hard，但 medium 值得做
  https://github.com/type-challenges/type-challenges
- [ ] **Exercism TypeScript Track** ⚠️（403 反爬，浏览器正常）— 做题 + 免费导师批改
  https://exercism.org/tracks/typescript

---

## 四、Node.js ⭐⭐

### 主线教程（按顺序，中文优先）

- [ ] **Node.js 官方 Learn 板块（中文版）** ✅ — 官方教程，Getting Started → Asynchronous → HTTP server 一路跟下来
  https://nodejs.org/zh-cn/learn （英文版：https://nodejs.org/en/learn）
- [ ] **Node.js 中文文档站（nodejs.cn）** ✅ — 官方 API 文档 + 教程的中文站，查 API 时比机翻舒服
  https://www.nodejs.cn/
- [ ] **JavaScript 现代教程（中文版）** ✅ — Node 的地基是 JS；JS 基础不牢先把 Part 1 过一遍
  https://zh.javascript.info （英文版：https://javascript.info）
- [ ] **菜鸟教程 Node.js** ✅ — 中文速成，适合快速过语法点（深度一般，当字典用）
  https://www.runoob.com/nodejs/nodejs-tutorial.html
- [ ] **Node.js Roadmap** ✅ — roadmap.sh 的知识地图，查漏补缺用
  https://roadmap.sh/nodejs

### 工程化最佳实践（Yoni Goldberg 三件套，业界标准）⭐⭐⭐

- [ ] **Node.js Best Practices（中文版）** ✅ — 80+ 条最佳实践：项目结构、错误处理、安全、Docker
  https://github.com/goldbergyoni/nodebestpractices/blob/master/README.chinese.md
- [ ] **JavaScript Testing Best Practices** ✅
  https://github.com/goldbergyoni/javascript-testing-best-practices
- [ ] **Node.js Testing — Beyond the Basics** ✅ — 集成测试进阶
  https://github.com/goldbergyoni/nodejs-testing-best-practices

---

## 五、部署运维 / Linux 补充 ⭐

- [ ] **鸟哥的 Linux 私房菜（基础篇）** ✅ — 重点看：进程管理、systemd、文件权限、journalctl
  https://linux.vbird.org/linux_basic/
- [ ] **DevOps Roadmap** ✅ — 知识地图
  https://roadmap.sh/devops
- [ ] **Ansible 文档** ✅ — 部署与回滚思路参考（releases/ + current 软链切换方案可直接搬进毕设）
  https://docs.ansible.com/
- [ ] **《凤凰架构》（周志明）** ✅ — 免费在线，架构演进与可靠性章节可作论文理论素材
  https://icyfenix.cn

---

## 建议学习路径（结合毕设时间线）

| 阶段 | 内容 | 资源 |
|---|---|---|
| 第 1-2 周 | Docker Go SDK + x/crypto/ssh 写 demo：Go 起容器跑 `go build`、SSH 远程执行拿输出 | 第二部分「毕设三大依赖库」 |
| 第 3 周 | 定 pipeline 模型和整体架构 | Woodpecker 源码 + GitHub Actions 文档 |
| 第 4 周 | Go 工程化打磨（边写边学） | Learn Go with Tests + Code Review Comments |
| 第 5-6 周 | LLM 诊断模块最小链路：日志尾部 → prompt → 流式结构化诊断 | Building Effective Agents + Eino + 上交 Ch2 |
| 穿插 | TS/Node（如果做 Web 前端或 CLI 工具链） | 第三、四部分主线教程 |

> 提醒：LLM 诊断模块别贪大，「取构建日志 → 组 prompt → 流式返回结构化诊断（错误分类/原因/修复建议）」这条最小链路就够毕设分量；agent 化自主工具调用可写进论文「展望」。
