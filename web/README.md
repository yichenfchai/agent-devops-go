# GoPulse CI · 前端

面向小型团队的轻量 CI/CD 工具的 Web 控制台。由 stitch 设计稿重构而来 —— 从 13 张静态 HTML
变成可运行、可扩展、零 CDN 依赖的工程。

## 快速开始

```bash
npm install
npm run dev        # http://localhost:5173
```

其它命令：

```bash
npm run build          # 类型检查 + 生产构建（含 vue-tsc --noEmit）
npm run typecheck      # 只做类型检查
npm run preview        # 预览生产构建，默认 4173

npm run test           # Vitest 监听模式
npm run test:run       # 跑一次全部测试
npm run test:coverage  # 跑测试并生成覆盖率报告（coverage/index.html）
```

## 与设计稿的关系

13 个页面全部实现，路由如下：

| 路由 | 页面 | 对应设计稿 |
|------|------|-----------|
| `/projects` | 项目列表 | gopulse_ci_2 |
| `/projects/new` | 新建项目向导 | gopulse_ci_1 |
| `/projects/:id/builds` | 构建历史 | gopulse_ci_3 / gopulse_ci_11 |
| `/projects/:id/settings` | 项目设置 | gopulse_ci_10 |
| `/projects/:id/secrets` | 密钥管理 | gopulse_ci_5 |
| `/builds/:number` | 构建详情 · 运行中 | gopulse_ci_4 |
| `/builds/:number/failed` | 构建详情 · 失败 | gopulse_ci_7 |
| `/builds/:number/diagnosis` | AI 智能诊断 | gopulse_ci_ai |
| `/builds/:number/deployment` | 部署详情 | gopulse_ci_8 |
| `/hosts` | 部署目标管理 | gopulse_ci_6 |
| `/states` | 状态与反馈规范 | gopulse_ci_9 |
| `/login` | 登录 | gopulse_ci_12 |

### 重构时修掉的设计稿问题

| 设计稿里的问题 | 工程里怎么解决 |
|----------------|----------------|
| 13 个页面面包屑都写死成「项目 / web-api / 构建 #1091」 | 面包屑由 `route.meta.crumb` 生成，每页自动正确 |
| 13 个页面都没有 `<title>` | `router.afterEach` 统一设置文档标题 |
| 依赖 `cdn.tailwindcss.com`，断网变白板 | Tailwind 本地编译成 CSS，字体走系统回落 |
| 依赖 Material Symbols 字体图标，断网变成英文单词 | 全部换成内联 SVG（`src/components/icons.ts`） |
| 顶栏 / 侧栏 / 状态栏在 13 个文件里各复制一份 | 抽成 `components/layout/` 四个组件 |
| 同一构建号两个耗时、构建机三个名字 | `src/api/mock.ts` 作为唯一事实来源 |
| 无障碍属性几乎为零 | 表格 / 对话框 / 日志区补了 aria 与键盘可达性 |

## 目录结构

```
src/
├── api/
│   ├── client.ts        fetch 封装：超时、AbortSignal、错误归一化
│   ├── mock.ts          Mock 数据 —— 全站唯一事实来源
│   └── index.ts         领域 API，mock / 真实请求二选一
├── components/
│   ├── layout/          AppShell · AppTopbar · AppSidebar · AppStatusBar
│   ├── ui/              StatusBadge · StageList · StageRail · LogTerminal
│   │                    StatCard · SkeletonRows · EmptyState · PageHeader
│   ├── Icon.vue         内联 SVG 图标
│   ├── icons.ts         图标 path 表
│   └── RollbackDialog.vue
├── composables/
│   ├── useAsync.ts      统一 loading / error / retry / 卸载即取消
│   ├── useLogStream.ts  SSE 实时日志（mock 下自动回放）
│   └── usePolling.ts    轮询，页面切走自动停
├── views/               13 个页面
├── router.ts            路由 + 面包屑 + 文档标题
├── types.ts             与后端 pkg/api/types.go 对应
├── style.css            设计令牌的 @layer 封装
└── main.ts
```

## 设计令牌

配色、字体、圆角全部定义在 `tailwind.config.js`，来源是 stitch 的 `DESIGN.md`。
正文声明过的 13 个色值全部落进配置，保证代码与设计文档一一对应。

```
canvas #121316   surface #1f1f23   overlay #26282d   hover #292a2d
divider #2b2d30  edge    #393b40
ink    #e2e2e6   muted   #8c8f99   dim     #555861
primary #b1c5ff  success #87d894   danger  #ffb4ab
warning #ffb77c  ai      #e8b3ff
```

语义：蓝=主操作与选中，绿=通过/健康，红=失败，橙=排队/回滚，紫=仅 AI 诊断。

## 切换到真实后端

1. 复制 `.env.example` 为 `.env`，设 `VITE_USE_MOCK=false`
2. 确认 Go 服务在 `127.0.0.1:8080`（代理已配在 `vite.config.ts`）
3. `src/api/mock.ts` 可以整个删掉

API 契约见 `src/api/index.ts`，字段定义见 `src/types.ts`。

## 测试

`npm run test:run` —— **23 个测试文件 / 167 个用例，全部通过**。

| 层 | 覆盖率（语句） | 覆盖内容 |
|----|--------------|----------|
| `api/client.ts` | 100% | 超时、AbortSignal 取消、错误归一化、**监听器泄漏回归** |
| `components/ui` | 98.8% | 徽章语义、日志终端渲染与自适应高度、阶段列表状态与时长格式化 |
| `components/layout` | 100% | 面包屑随路由变化、侧栏最长匹配高亮、AppShell 骨架 |
| `composables` | 89.2% | `useAsync` 的取消与竞态、`useLogStream` 的环形缓冲、`usePolling` 的卸载即停 |
| `api`（mock/一致性） | 100% / 86.8% | mock 数据一致性、日志按构建号区分、深拷贝隔离 |
| `views`（全部 12 个） | 98.2% | 12 个视图全部有挂载级测试：加载·错误·空态、表单校验、交互与导航 |
| **整体** | **95.9%**（分支 87.5%） | |

所有视图都有真实的挂载测试（不再是「被路由顺带 import」的覆盖率假象）。

### 测试里钉住的历史缺陷

这些用例不只是"跑通就行"，每一条都对应一个真实踩过的坑：

| 用例 | 钉住的问题 |
|------|-----------|
| `router.spec.ts` 面包屑逐页不同 | 设计稿 13 个页面面包屑全写死成「构建 #1091」 |
| `router.spec.ts` 文档标题跟随路由 | 设计稿 13 个页面都没有 `<title>` |
| `BuildHistoryView` #1091 耗时是 28s | 设计稿构建历史表格写的是 48s，与其它 5 页矛盾 |
| `consistency` 构建机只有一个名字 | 设计稿里出现 3 个不同的构建机名 |
| `consistency` tsc 失败后无 vite 输出 | AI 页日志顺序在 `&&` 短路语义上讲不通 |
| `consistency` 运行中构建的日志无 error | 运行中的 #1092 曾显示 #1091 的失败日志 |
| `useLogStream` 超上限丢最旧的 | 日志无限增长会把内存吃光 |
| `useAsync` 销毁后不回写 | 切页后旧请求覆盖新页面数据的竞态 |
| `StatusBadge` deployed 用圆点 | 「运行中」曾用对勾（对勾语义是成功） |
| `layout` 子路由不被父级抢高亮 | `/projects/1/secrets` 曾高亮成「项目列表」 |
| `client` 请求结束摘掉 abort 监听 | 复用同一 signal 发 N 个请求会累积 N 个永不触发的监听 |
| `client` 超时/abort 真正传到 fetch | 测试桩必须模拟 fetch 对 signal 的 reject，否则测了个寂寞 |
| `DeploymentDetail` 部署成功徽章 | deployed 状态曾显示「运行中」，部署语境下语义错位 |
| `StatusBadge` deployed 文案 | 改为「部署成功」，项目列表语境用圆点表达「健康在跑」 |

测试里刻意不 mock `@/api/mock.ts` —— 数据一致性本身就是要被测的对象。

## 下一步

- [x] ~~补单元测试（Vitest）~~ —— 已完成，101 个用例
- [ ] 登录态与路由守卫（现在 `/login` 是独立裸页，还没接鉴权）
- [ ] 项目 id 目前硬编码为 1（侧栏与路由），需要改成从当前项目上下文推导
- [ ] SSE 断线重连的可见提示（`useLogStream` 已记录 `connected`，界面还没用满）
- [ ] 与后端联调，删掉 mock
