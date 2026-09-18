# 依赖清单

> 分两部分：前端（已实现，版本取自 `web/package.json` 实际安装）与后端（M1 规划）。
> 每一项都写明「为什么选它」—— 答辩被问到技术选型时直接引用。

---

## 一、前端依赖（已实现）

### 1.1 运行时依赖（dependencies，2 个）

| 包 | 版本 | 作用 | 为什么是它 / 备选方案对比 |
|----|------|------|--------------------------|
| `vue` | ^3.5.13 | UI 框架 | Composition API + `<script setup>` 让逻辑复用靠 composables 而非 mixin；比 React 少一层状态管理样板（内置响应式）；比 Svelte 生态更稳。**不用 Nuxt**——本项目是纯控制台 SPA，无 SEO 需求，SSR 只会增加复杂度 |
| `vue-router` | ^4.5.0 | 路由 | 官方标配。用了两个非常规能力：`meta.crumb` 驱动面包屑、`afterEach` 统一设 `document.title`——这两处直接治好设计稿「13 页面包屑写死 / 全部没有 title」的缺陷 |

> 运行时只有 2 个直接依赖。**没有 axios**（原生 fetch + 60 行封装足够，见下）、
> **没有 pinia**（服务端状态靠 useAsync 局部管理，全局状态目前只有路由上下文）、
> **没有组件库**（设计系统来自 Stitch 的 DESIGN.md，手写 8 个 UI 组件反而更贴稿、
> 体积更小：主包 gzip 45 kB 含框架）。

### 1.2 开发期依赖（devDependencies，12 个）

#### 构建链

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `vite` | ^6.0.7 | 构建与 dev server | ESM 原生按需编译，冷启动 <1s；按路由自动代码分割（12 个 view 各自成 chunk） |
| `@vitejs/plugin-vue` | ^5.2.1 | Vite 的 Vue SFC 插件 | 官方 |
| `typescript` | ^5.7.2 | 类型系统 | `strict` 全开 + `noUnusedLocals/Parameters`——构建期抓出过 14 个错误 |
| `vue-tsc` | ^2.2.0 | 对 `.vue` 文件跑 TS 检查 | 纯类型检查（`--noEmit`），不参与产物 |
| `tailwindcss` | ^3.4.17 | 原子化 CSS | 设计令牌（13 色/字体/圆角）全部进 config，代码与 DESIGN.md 一一对应。**关键：本地编译**，替换掉设计稿的 `cdn.tailwindcss.com`（官方明说不可用于生产，且断网即白板）。选 v3 而非 v4：v4 的 CSS-first 配置与本项目「令牌即文档」的注释风格匹配度反而低，且 v3 生态插件更全 |
| `postcss` | ^8.4.49 | Tailwind 的处理管线 | Tailwind 是 PostCSS 插件 |
| `autoprefixer` | ^10.4.20 | 自动补全浏览器前缀 | 标配 |

#### 测试链

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `vitest` | ^2.1.9 | 测试框架 | 与 Vite 共用同一份配置和转换管线（`mergeConfig` 复用 alias），不用另维护 jest.config；ESM 原生支持 |
| `@vitest/coverage-v8` | ^2.1.9 | 覆盖率 | v8 原生插桩，比 babel-plugin-istanbul 快一个量级；产出 text/html/json-summary 三种报告 |
| `@vue/test-utils` | ^2.5.1 | 组件挂载与交互 | `mount` 真实渲染子树；`flushPromises` 处理异步断言 |
| `jsdom` | ^25.0.1 | 浏览器环境模拟 | vitest environment。已知缺口及补法都写在 `src/test/setup.ts`（matchMedia、scrollTo、EventSource 由测试自注入 Fake） |

#### 类型与杂项

| 包 | 版本 | 作用 | 说明 |
|----|------|------|------|
| `@types/node` | ^22.10.5 | Node API 类型 | 仅 `vite.config.ts` 用到 `node:url`；TS 触碰不到 src 内任何 Node API（保证产物可跑在浏览器） |

### 1.3 前端「不引入」清单（同等重要）

| 刻意不用 | 理由 |
|----------|------|
| axios | `client.ts` 60 行封装已覆盖：超时、AbortSignal 传播、错误归一化 ApiError、204 处理。引 axios 反而要再学一层拦截器模型 |
| pinia | 目前没有跨页面共享的可变状态；`useAsync` 实例级缓存 + 路由参数已够。等出现真正的全局状态（如当前用户）再引 |
| Element/AntD 等组件库 | 8 个 UI 组件手写共 ~400 行，完全贴合设计稿；引库至少 +80 kB 且要深度覆写主题 |
| 图标库（Material Icons / lucide） | 34 个图标内联 SVG path（`icons.ts` 约 2 KB），零请求、断网可用、可 tree-shake |
| Moment/Dayjs | 只用到相对时间展示（"3 分钟前"），后端返回现成文案 |

### 1.4 前端依赖审计数据

```
直接依赖      2 运行时 + 12 开发期
npm install   127 包（生产链）+ 169 包（测试链，npm install -D 追加）
主包体积      115.6 kB（gzip 45.3 kB）—— 含 Vue 运行时 + 路由 + 全部首屏代码
路由分包      12 个 view 独立 chunk（0.5–8.1 kB each，按需加载）
CSS           22.4 kB（gzip 5.0 kB）—— Tailwind 只产出生成页用到的类
外链请求      0（字体系统回落、图标内联、无任何 CDN）
```

---

## 二、后端依赖（M1 规划，Go 1.22+）

> 全部官方维护或社区标准件；原则：**能用标准库不引第三方，能单二进制不引服务**。

### 2.1 Web 层

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `github.com/go-chi/chi/v5` | v5 | 路由 | 贴近标准库 API、零反射、中间件模型简单。**不选 gin/echo**：不需要它们的绑定/校验生态，chi 的 `middleware.Use` 与标准库 `http.Handler` 完全兼容，SSE 长连接也好写。Go 1.22 的 `net/http` 增强路由（`GET /builds/{id}`）是备选——若 M1 时确认够用，chi 也可以去掉 |
| `golang.org/x/crypto` | latest | bcrypt（口令哈希） | 口令存哈希不存明文；argon2id 更强但 bcrypt 在本项目威胁模型下足够且更省心 |
| `github.com/golang-jwt/jwt/v5` | v5 | 会话令牌 | stateless 会话；密钥从环境变量注入 |

### 2.2 存储层

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `modernc.org/sqlite` | latest | SQLite 驱动 | **纯 Go 无 CGO**——这是选它的决定性理由：Windows 上不用装 gcc 就能 `go build`，交叉编译出 Linux 单文件零烦恼。备选 `mattn/go-sqlite3`（CGO、性能略好）在跨平台编译场景得不偿失。SQLite 单写者与「单构建机」定位天然匹配；WAL 模式缓解读写并发 |
| `github.com/pressly/goose/v3` | v3 | schema 迁移 | 单二进制可内嵌迁移 SQL；比 golang-migrate 轻（后者要目录约定和 CLI）。备选 golang-migrate 功能更全但本项目只需 up |
| `github.com/sqlc-dev/sqlc` | latest | 编译期生成类型安全查询 | 写 SQL → 生成 Go 代码，拼错列名编译期就报错。比 ORM（GORM）多一层显式 SQL、比手写 `db.Query` 少一类扫描错误 |
| `github.com/mattn/go-sqlite3` | ❌ 不用 | — | CGO 依赖见上 |

### 2.3 构建执行层

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `github.com/docker/docker/client` | latest | Docker SDK | 容器全生命周期：create/start/wait/logs/commit/remove。风险已知：SDK 学习曲线陡，**缓解措施是先用 `os/exec` 封 docker CLI 跑通全流程，再替换成 SDK**（TODO M2） |
| `github.com/moby/moby/api` | (随 SDK) | 容器类型定义 | SDK 依赖 |
| `github.com/docker/go-connections` | (随 SDK) | 端口/挂载配置类型 | SDK 依赖 |

### 2.4 部署执行层

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `golang.org/x/crypto/ssh` | latest | SSH 客户端 | golang.org/x 官方维护。三件硬要求写进代码：HostKeyCallback 必须校验（`ssh.FixedHostKey`，防中间人）、私钥解密后才进内存、连接 15s 超时 |
| `github.com/pkg/sftp` | ❌ 不用 | SFTP | 产物走 registry tag / tar + compose 拉取，不需要 SFTP 通道 |

### 2.5 LLM 诊断层

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| （无第三方包） | — | OpenAI 兼容客户端 | **标准库 `net/http` + `encoding/json` 手写**：协议就是一个 POST `/chat/completions`，引 openai-go 反而把协议细节藏进抽象层；且要同时兼容 OpenAI/vLLM/Ollama 三种 base_url，手写 80 行最透明。超时 90s、退避重试 ×2、上下文裁剪、脱敏都在自己代码里可见 |

### 2.6 可观测性

| 包 | 版本 | 作用 | 选型说明 |
|----|------|------|----------|
| `log/slog` | 标准库（Go 1.21+） | 结构化日志 | 标准库，零依赖；JSON handler 供采集，text handler 供开发 |
| `github.com/prometheus/client_golang` | latest | 指标 | 构建并发数、队列深度、P95 排队延迟、goroutine 数——论文压测章节的数据来源。M2 就接上，不要等 M6 补数据 |

### 2.7 工程配套

| 包 | 作用 |
|----|------|
| `golangci-lint`（CLI，非依赖） | 聚合 linter；CI 里 `go vet` + `golangci-lint run` 双闸 |
| `go test -race`（内置） | 竞态检测——并发正确性的最终裁判，所有测试命令默认带 |

### 2.8 后端「不引入」清单

| 刻意不用 | 理由 |
|----------|------|
| GORM / ent | sqlc 已覆盖类型安全；ORM 的 N+1 与隐式行为在状态机更新场景是负资产 |
| Redis / NATS | 队列就是 SQLite 的 `queued` 状态行 + 内存 channel，单机场景引入外部中间件违背「单二进制」定位 |
| Cobra | `flag` 标准库够用（只有 `-config` 一个参数） |
| Viper | 同上，YAML 解析 `gopkg.in/yaml.v3` 一个包搞定 |
| Kubernetes client | 单机 Docker 就是全部，K8s 在论文"未来工作" |
| goroutine 泄漏检测库（goleak） | `runtime.NumGoroutine()` 前后对比已写入测试规范；需要更强时再引 uber-go/goleak |

---

## 三、依赖治理原则

1. **运行时依赖最小化**：前端 2 个、后端目标 ≤ 10 个直接依赖。每个新依赖都要过
   「不用它会多写多少代码、用了它多背多少风险」的账。
2. **零 CDN、零运行时网络请求**（前端）：构建产物必须离线可用——答辩现场网络不可信。
3. **纯 Go 编译**（后端）：`CGO_ENABLED=0` 交叉编译出 Linux 单文件，是"单二进制交付"
   承诺的技术底线。
4. **锁文件入库**：`package-lock.json` 已提交；Go 侧 `go.sum` 同理——可复现构建。
5. **升级策略**：毕设周期内锁 minor 版本（`^` 只吃 patch）；论文答辩后无所谓。

## 四、Go 依赖总览（M1 完成后的 go.mod 预览）

```go
require (
    github.com/go-chi/chi/v5        // 路由
    github.com/golang-jwt/jwt/v5    // 会话
    github.com/prometheus/client_golang // 指标
    github.com/pressly/goose/v3     // 迁移
    github.com/sqlc-dev/sqlc        // (CLI，不进 go.mod)
    golang.org/x/crypto             // bcrypt + ssh
    modernc.org/sqlite              // SQLite 驱动（纯 Go）
    github.com/docker/docker/client // M2: 构建容器
    gopkg.in/yaml.v3                // 配置解析
)

// 标准库顶掉的位置：日志(slog)、HTTP client(LLM)、flag、testing -race
```
