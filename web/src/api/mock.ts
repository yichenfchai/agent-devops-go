/**
 * Mock 数据 —— 全站唯一事实来源。
 *
 * 设计稿里有几处跨页对不上的地方（同一构建号两个耗时、构建机三个名字），
 * 在这里统一成一套。所有页面都从这里取数，不可能再出现矛盾。
 *
 * 后端就绪后把 VITE_USE_MOCK 设为 false，整个文件可以删掉。
 */
import type {
  Build, BuildStats, DeployHost, Deployment, LogLine, Project, RunnerInfo, Secret, Stage,
} from '@/types'

/** 全站共用的构建机 —— 只有一个名字 */
export const RUNNER: RunnerInfo = {
  name: 'build-runner-01',
  os: 'Ubuntu 22.04 LTS',
  version: 'v1.4.2',
  state: 'idle',
  queued: 0,
}

/** 构建 #1091 的耗时 —— 所有页面统一引用这个常量 */
export const BUILD_1091_DURATION_MS = 28_140

export const projects: Project[] = [
  {
    id: 1, name: 'web-api', repoProvider: 'github', repoFullName: 'acme/web-api',
    defaultBranch: 'main', detectedType: 'Node.js', deployHostId: 1,
    lastBuild: { number: 1091, state: 'failed', finishedAt: '3 分钟前', durationMs: BUILD_1091_DURATION_MS },
    deployed: true, created_at: '2026-06-02',
  },
  {
    id: 2, name: 'admin-dashboard', repoProvider: 'github', repoFullName: 'acme/admin-dashboard',
    defaultBranch: 'main', detectedType: 'Node.js', deployHostId: 1,
    lastBuild: { number: 1090, state: 'failed', finishedAt: '1 小时前', durationMs: 34_000 },
    deployed: true, created_at: '2026-06-11',
  },
  {
    id: 3, name: 'docs-site', repoProvider: 'github', repoFullName: 'acme/docs-site',
    defaultBranch: 'main', detectedType: 'Node.js', deployHostId: 2,
    lastBuild: { number: 1088, state: 'deployed', finishedAt: '昨天', durationMs: 19_000 },
    deployed: true, created_at: '2026-07-03',
  },
  {
    id: 4, name: 'payment-service', repoProvider: 'github', repoFullName: 'acme/payment-service',
    defaultBranch: 'develop', detectedType: 'Node.js', deployHostId: null,
    lastBuild: null, deployed: false, created_at: '2026-08-19',
  },
]

export const hosts: DeployHost[] = [
  {
    id: 1, name: 'prod-vps-01', addr: '10.0.0.8:22', sshUser: 'deploy',
    workDir: '/srv/web-api', composeFile: 'docker-compose.yml',
    healthCheckUrl: 'http://10.0.0.8:8080/healthz', healthRetries: 5, keepVersions: 5,
    status: 'ok', statusDetail: 'SSH-2.0-OpenSSH_8.9p1',
    usedBy: ['web-api', 'admin-dashboard', 'payment-service'],
  },
  {
    id: 2, name: 'docs-vps', addr: '10.0.0.12:22', sshUser: 'deploy',
    workDir: '/srv/docs-site', composeFile: 'docker-compose.yml',
    healthCheckUrl: 'http://10.0.0.12:8080/healthz', healthRetries: 3, keepVersions: 3,
    status: 'unreachable',
    statusDetail: '上次校验失败：ssh: connect to host 10.0.0.12 port 22: Connection refused',
    usedBy: ['docs-site'],
  },
]

export const secrets: Secret[] = [
  { id: 1, key: 'DATABASE_URL', updatedAt: '3 天前', isSecret: true },
  { id: 2, key: 'JWT_SECRET',   updatedAt: '1 周前', isSecret: true },
  { id: 3, key: 'NODE_ENV',     updatedAt: '1 小时前', isSecret: false },
]

export const stats: BuildStats = {
  total: 128, successRate: 92.2, avgDurationMs: 41_000, monthlyDeploys: 37,
}

/** 构建 #1091 的六个阶段 */
export const stages1091: Stage[] = [
  { index: 1, name: '检出代码',       command: 'git clone --depth=1',              status: 'passed',  durationMs: 4_200 },
  { index: 2, name: '安装依赖',       command: 'npm ci',                           status: 'passed',  durationMs: 12_400 },
  { index: 3, name: '执行构建',       command: 'tsc -b',                           status: 'failed',  durationMs: 11_400 },
  { index: 4, name: '生成产物',       command: 'docker build -t web-api:${SHA}',   status: 'skipped', durationMs: null },
  { index: 5, name: '部署',           command: 'ssh deploy@10.0.0.8 docker-compose up -d', status: 'skipped', durationMs: null },
  { index: 6, name: '健康检查',       command: 'GET /healthz',                     status: 'skipped', durationMs: null },
]

/** 构建 #1092 运行中的阶段 */
export const stages1092: Stage[] = [
  { index: 1, name: '检出代码', command: 'git clone --depth=1',        status: 'passed',  durationMs: 4_200 },
  { index: 2, name: '安装依赖', command: 'npm ci',                     status: 'passed',  durationMs: 12_400 },
  { index: 3, name: '执行构建', command: 'npm run build',              status: 'running', durationMs: null },
  { index: 4, name: '生成产物', command: 'docker build -t web-api:$SHA', status: 'pending', durationMs: null },
  { index: 5, name: '部署',     command: 'SSH docker-compose up -d',   status: 'pending', durationMs: null },
  { index: 6, name: '健康检查', command: 'GET /healthz',               status: 'pending', durationMs: null },
]

/** 构建 #1091 的失败日志尾部 —— 13 行，顺序自洽：tsc 失败后直接 npm 退出，不会有 vite 的 banner */
export const failLog1091: LogLine[] = [
  { seq: 38, ts: '10:24:28', text: '$ npm run build', level: 'info' },
  { seq: 39, ts: '10:24:29', text: '> web-api@1.0.0 build', level: 'info' },
  { seq: 40, ts: '10:24:30', text: '> tsc -b', level: 'info' },
  { seq: 41, ts: '10:24:32', text: 'src/api/client.ts:42:18 - error TS2345: Argument of type \'string\' is not assignable to parameter of type \'number\'.', level: 'error' },
  { seq: 42, ts: '10:24:32', text: '42   const client = new ApiClient({ port: process.env.PORT, host: \'0.0.0.0\' });', level: 'error' },
  { seq: 43, ts: '10:24:32', text: '     ~~~~~~~~', level: 'error' },
  { seq: 44, ts: '10:24:33', text: 'npm ERR! code ELIFECYCLE', level: 'error' },
  { seq: 45, ts: '10:24:33', text: 'npm ERR! errno 2', level: 'error' },
  { seq: 46, ts: '10:24:33', text: 'npm ERR! web-api@1.0.0 build: `tsc -b`', level: 'error' },
  { seq: 47, ts: '10:24:33', text: 'npm ERR! Exit status 2', level: 'error' },
  { seq: 48, ts: '10:24:34', text: 'docker: 容器退出码 2', level: 'error' },
  { seq: 49, ts: '10:24:34', text: '[GoPulse CI] 阶段 [执行构建] 异常退出，耗时 28.14s', level: 'error' },
]

/** 构建 #1092（运行中）的日志 —— 进行中的流，结尾没有终态行，配合光标使用 */
export const runningLog1092: LogLine[] = [
  { seq: 1,  ts: '10:31:02', text: '$ git clone --depth=1 https://github.com/acme/web-api .', level: 'info' },
  { seq: 2,  ts: '10:31:06', text: 'Cloning into repository... done. (4.2s)', level: 'ok' },
  { seq: 3,  ts: '10:31:06', text: '$ npm ci', level: 'info' },
  { seq: 4,  ts: '10:31:08', text: '> web-api@1.0.0 prepare', level: 'info' },
  { seq: 5,  ts: '10:31:18', text: 'added 412 packages in 12.4s', level: 'ok' },
  { seq: 6,  ts: '10:31:19', text: '$ npm run build', level: 'info' },
  { seq: 7,  ts: '10:31:19', text: '> web-api@1.0.0 build', level: 'info' },
  { seq: 8,  ts: '10:31:19', text: '> tsc -b && vite build', level: 'info' },
  { seq: 9,  ts: '10:31:21', text: 'vite v5.2.0 building for production...', level: 'info' },
  { seq: 10, ts: '10:31:24', text: 'transforming (612) src/api/client.ts', level: 'info' },
  { seq: 11, ts: '10:31:27', text: 'transforming (1284) src/components/Dashboard.tsx', level: 'info' },
  { seq: 12, ts: '10:31:30', text: '✓ 1843 modules transformed.', level: 'ok' },
  { seq: 13, ts: '10:31:31', text: 'rendering chunks...', level: 'info' },
  { seq: 14, ts: '10:31:32', text: 'computing gzip size...', level: 'info' },
]

/** AI 诊断结果 —— 只展示真实能产出的内容：原因 + 建议 + 元信息 */
export const diagnosis1091 = {
  rootCause:
    'TypeScript 类型错误。src/api/client.ts 第 42 行把 string 类型的值传给了期望 number 的参数。该值来自环境变量 process.env.PORT，未做类型转换。',
  suggestion:
    '读取环境变量后显式转换：const port = Number(process.env.PORT ?? 3000)。或在该函数签名处将参数类型放宽为 string | number。',
  model: 'gpt-4o-mini',
  latencyMs: 3_800,
  inputTokens: 2_100,
  redactions: 3,
}

export const builds: Build[] = [
  // 缺陷 #1 决策后的真实数据形态：id 全局唯一连续；number 项目内自增（跨项目可重复）。
  // mock 不再 id===number，前端不得用 number 寻址 —— api 层按 id 取，UI 显示 #number。
  { id: 201, projectId: 1, number: 1092, state: 'running', trigger: 'push', ref: 'main',
    commitSha: 'c8f921d', commitMessage: '添加 JWT Token 刷新处理器', commitAuthor: 'Alex Mercer',
    baseImage: 'node:20-alpine', imageTag: null, exitCode: null,
    queuedAt: '52 秒前', startedAt: '52 秒前', finishedAt: null, durationMs: null, diagnosis: null },
  { id: 200, projectId: 1, number: 1091, state: 'failed', trigger: 'push', ref: 'main',
    commitSha: 'a3f9c21', commitMessage: '修复部署脚本的环境变量读取', commitAuthor: 'M. Alvarez',
    baseImage: 'node:20-alpine', imageTag: null, exitCode: 1,
    queuedAt: '10 分钟前', startedAt: '10 分钟前', finishedAt: '9 分钟前',
    durationMs: BUILD_1091_DURATION_MS, diagnosis: diagnosis1091 },
  { id: 199, projectId: 1, number: 1090, state: 'deployed', trigger: 'manual', ref: 'main',
    commitSha: '7b1e044', commitMessage: '优化数据库查询索引', commitAuthor: 'admin',
    baseImage: 'node:20-alpine', imageTag: 'web-api:7b1e044', exitCode: 0,
    queuedAt: '2 小时前', startedAt: '2 小时前', finishedAt: '2 小时前',
    durationMs: 134_000, diagnosis: null },
  { id: 187, projectId: 2, number: 1091, state: 'failed', trigger: 'push', ref: 'main',
    commitSha: 'f2e811b', commitMessage: '重构仪表盘图表组件', commitAuthor: 'M. Alvarez',
    baseImage: 'node:20-alpine', imageTag: null, exitCode: 1,
    queuedAt: '5 小时前', startedAt: '5 小时前', finishedAt: '5 小时前',
    durationMs: 21_000, diagnosis: null },
  { id: 172, projectId: 3, number: 1088, state: 'deployed', trigger: 'push', ref: 'main',
    commitSha: '91c4d2e', commitMessage: '更新 API 参考文档', commitAuthor: 'L. Chen',
    baseImage: 'node:20-alpine', imageTag: 'docs-site:91c4d2e', exitCode: 0,
    queuedAt: '昨天', startedAt: '昨天', finishedAt: '昨天',
    durationMs: 19_000, diagnosis: null },
]

export const deployments: Deployment[] = [
  {
    id: 1, buildId: 199, projectName: 'web-api', imageTag: 'web-api:a3f9c21',
    hostAddr: 'deploy@10.0.0.8', workDir: '/srv/web-api', state: 'deployed',
    startedAt: '10:25:04', durationMs: 19_500,
    steps: [
      { index: 1, name: '连接目标主机',  command: 'SSH deploy@10.0.0.8:22，主机密钥校验通过', status: 'passed', durationMs: 800 },
      { index: 2, name: '推送镜像 tag',  command: 'registry.local/web-api:a3f9c21',          status: 'passed', durationMs: 1_400 },
      { index: 3, name: '执行 compose',  command: 'docker-compose up -d',                    status: 'passed', durationMs: 6_200 },
      { index: 4, name: '容器启动',      command: 'Container web-api  Started',              status: 'passed', durationMs: 2_100 },
      { index: 5, name: '健康检查',      command: 'GET /healthz 连续 3 次返回 200',           status: 'passed', durationMs: 9_000 },
    ],
    versions: [
      { tag: 'web-api:a3f9c21', deployedAt: '10 分钟前',  state: '当前版本（构建失败未部署）' },
      { tag: 'web-api:7b1e044', deployedAt: '2 小时前',   state: '成功' },
      { tag: 'web-api:91c4d2e', deployedAt: '昨天',       state: '成功' },
    ],
  },
]

/** 项目类型检测规则 —— 后端 internal/build/detect.go 的规则镜像到前端，用于新建向导的即时提示 */
export const detectRules = [
  { file: 'Dockerfile',         type: 'Docker',  image: null },
  { file: 'package.json',       type: 'Node.js', image: 'node:20-alpine' },
  { file: 'go.mod',             type: 'Go',      image: 'golang:1.22-alpine' },
  { file: 'requirements.txt',   type: 'Python',  image: 'python:3.12-slim' },
  { file: 'pyproject.toml',     type: 'Python',  image: 'python:3.12-slim' },
  { file: 'pom.xml',            type: 'Java',    image: 'maven:3.9-eclipse-temurin-21' },
  { file: 'Cargo.toml',         type: 'Rust',    image: 'rust:1.78-alpine' },
]
