import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { router } from '@/router'
import BuildRunningView from '@/views/BuildRunningView.vue'

const mocks = vi.hoisted(() => ({
  getBuild: vi.fn(), getStages: vi.fn(), getLogs: vi.fn(),
}))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: {
    getBuild: mocks.getBuild,
    getStages: mocks.getStages,
    getLogs: mocks.getLogs,
  },
}))

const BUILD = {
  id: 1092, projectId: 1, number: 1092, state: 'running' as const, trigger: 'push' as const,
  ref: 'main', commitSha: 'c8f921d', commitMessage: '添加 JWT Token 刷新处理器',
  commitAuthor: 'Alex Mercer', baseImage: 'node:20-alpine', imageTag: null, exitCode: null,
  queuedAt: '52 秒前', startedAt: '52 秒前', finishedAt: null, durationMs: null, diagnosis: null,
}

const STAGES = [
  { index: 1, name: '检出代码', command: 'git clone --depth=1', status: 'passed' as const, durationMs: 4200 },
  { index: 2, name: '安装依赖', command: 'npm ci', status: 'passed' as const, durationMs: 12400 },
  { index: 3, name: '执行构建', command: 'npm run build', status: 'running' as const, durationMs: null },
  { index: 4, name: '生成产物', command: 'docker build', status: 'pending' as const, durationMs: null },
  { index: 5, name: '部署', command: 'ssh', status: 'pending' as const, durationMs: null },
  { index: 6, name: '健康检查', command: 'GET /healthz', status: 'pending' as const, durationMs: null },
]

const LOGS = Array.from({ length: 14 }, (_, i) => ({
  seq: i + 1, ts: '10:31:02', text: `transforming (${i + 1})`, level: 'info' as const,
}))

describe('BuildRunningView（轮询 + 实时日志）', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    mocks.getBuild.mockResolvedValue(BUILD)
    mocks.getStages.mockResolvedValue(STAGES)
    mocks.getLogs.mockResolvedValue(LOGS)
    return router.push('/builds/1092')
  })
  afterEach(() => vi.useRealTimers())

  async function mountView() {
    const w = mount(BuildRunningView, { global: { plugins: [router] } })
    // 初始请求立即 resolve；日志回放的 14 个 setTimeout（最后一个在 13*90=1170ms）
    await vi.advanceTimersByTimeAsync(1600)
    return w
  }

  it('显示运行中状态、构建号与提交元信息', async () => {
    const w = await mountView()
    expect(w.text()).toContain('运行中')
    expect(w.text()).toContain('#1092')
    expect(w.text()).toContain('c8f921d')
    expect(w.text()).toContain('添加 JWT Token 刷新处理器')
    expect(w.text()).toContain('Alex Mercer')
    expect(w.text()).toContain('LIVE STREAM')
  })

  it('阶段进度：2/6 已完成，构建中的阶段标记为进行中', async () => {
    const w = await mountView()
    expect(w.text()).toContain('2/6 已完成')
    expect(w.text()).toContain('进行中')
  })

  it('实时日志全部回放后显示行数统计', async () => {
    const w = await mountView()
    expect(w.text()).toContain('transforming (14)')
    expect(w.text()).toContain('LINES: 14')
    expect(w.text()).toContain('BUFFER: 8192B')
  })

  it('日志连接后显示已连接状态', async () => {
    const w = await mountView()
    expect(w.text()).toContain('日志已连接')
  })

  it('轮询随时间推进：执行时长累加并刷新阶段数据', async () => {
    const w = await mountView()
    expect(w.text()).toContain('52.1s')

    const before = mocks.getStages.mock.calls.length
    await vi.advanceTimersByTimeAsync(3500)      // 越过第一个 3s 轮询点

    expect(mocks.getStages.mock.calls.length).toBeGreaterThan(before)
    expect(w.text()).toContain('55.1s')
  })

  it('中止运行后轮询停止，不再刷阶段接口', async () => {
    const w = await mountView()
    const stop = w.findAll('button').find((b) => b.text().includes('中止运行'))!
    expect(stop).toBeTruthy()

    await stop.trigger('click')
    const n = mocks.getStages.mock.calls.length
    await vi.advanceTimersByTimeAsync(9000)
    expect(mocks.getStages.mock.calls.length).toBe(n)
  })

  it('展示 Pipeline 快照与项目类型识别结果', async () => {
    const w = await mountView()
    expect(w.text()).toContain('本次构建使用的 Pipeline 快照')
    expect(w.text()).toContain('npm ci → npm run build → docker build -t web-api:${SHA} → docker push')
    expect(w.text()).toContain('检测到 package.json，自动识别为 Node.js 项目')
  })
})
