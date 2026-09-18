import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import BuildFailedView from '@/views/BuildFailedView.vue'

const mocks = vi.hoisted(() => ({
  getBuild: vi.fn(), getStages: vi.fn(), getLogs: vi.fn(),
}))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { getBuild: mocks.getBuild, getStages: mocks.getStages, getLogs: mocks.getLogs },
}))

const BUILD = {
  id: 1091, projectId: 1, number: 1091, state: 'failed' as const, trigger: 'push' as const,
  ref: 'main', commitSha: 'a3f9c21', commitMessage: '修复部署脚本的环境变量读取',
  commitAuthor: 'M. Alvarez', baseImage: 'node:20-alpine', imageTag: null, exitCode: 1,
  queuedAt: '10 分钟前', startedAt: null, finishedAt: null,
  durationMs: 28_140, diagnosis: null,
}

const STAGES = [
  { index: 1, name: '检出代码', command: 'git clone', status: 'passed' as const, durationMs: 4200 },
  { index: 2, name: '安装依赖', command: 'npm ci', status: 'passed' as const, durationMs: 12400 },
  { index: 3, name: '执行构建', command: 'tsc -b', status: 'failed' as const, durationMs: 11400 },
  { index: 4, name: '生成产物', command: 'docker build', status: 'skipped' as const, durationMs: null },
  { index: 5, name: '部署', command: 'ssh', status: 'skipped' as const, durationMs: null },
  { index: 6, name: '健康检查', command: 'GET /healthz', status: 'skipped' as const, durationMs: null },
]

const LOGS = [
  { seq: 40, ts: '10:24:30', text: '> tsc -b', level: 'info' as const },
  { seq: 41, ts: '10:24:32', text: 'error TS2345', level: 'error' as const },
]

async function render() {
  const w = mount(BuildFailedView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('BuildFailedView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getBuild.mockResolvedValue(BUILD)
    mocks.getStages.mockResolvedValue(STAGES)
    mocks.getLogs.mockResolvedValue(LOGS)
    return router.push('/builds/1091/failed')
  })

  it('失败条显示构建号、退出码与耗时', async () => {
    const w = await render()
    expect(w.text()).toContain('构建 #1091 失败')
    expect(w.text()).toContain('exit code 1')
    expect(w.text()).toContain('28.1s')
  })

  it('六阶段横排：失败格标红、后续阶段显示已跳过', async () => {
    const w = await render()
    expect(w.text()).toContain('检出代码')
    expect(w.text()).toContain('已跳过')
    const cells = w.findAll('li')
    expect(cells).toHaveLength(6)
    expect(cells[2].classes()).toContain('border-danger/50')
  })

  it('日志区渲染错误行并提供工具条', async () => {
    const w = await render()
    expect(w.text()).toContain('tsc -b')
    expect(w.text()).toContain('error TS2345')
    expect(w.text()).toContain('跳转至错误行')
    expect(w.text()).toContain('下载原始日志')
  })

  it('提供到 AI 诊断页的入口', async () => {
    const w = await render()
    const link = w.findAll('a').find((a) => a.text().includes('查看 AI 诊断'))
    expect(link).toBeTruthy()
    expect(link!.attributes('href')).toBe('/builds/1091/diagnosis')
  })

  it('页脚标注运行时环境与基础镜像', async () => {
    const w = await render()
    expect(w.text()).toContain('Docker 运行时隔离环境')
    expect(w.text()).toContain('node:20-alpine')
  })
})
