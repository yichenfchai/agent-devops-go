import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import BuildDiagnosisView from '@/views/BuildDiagnosisView.vue'
import type { Build, Diagnosis, LogLine } from '@/types'

const mocks = vi.hoisted(() => ({
  getBuild: vi.fn(), getLogs: vi.fn(), getDiagnosis: vi.fn(),
}))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: {
    getBuild: mocks.getBuild,
    getLogs: mocks.getLogs,
    getDiagnosis: mocks.getDiagnosis,
  },
}))

const BUILD: Build = {
  id: 1091, projectId: 1, number: 1091, state: 'failed', trigger: 'push', ref: 'main',
  commitSha: 'a3f9c21', commitMessage: '修复部署脚本的环境变量读取', commitAuthor: 'M. Alvarez',
  baseImage: 'node:20-alpine', imageTag: null, exitCode: 1,
  queuedAt: '10 分钟前', startedAt: null, finishedAt: null,
  durationMs: 28_140, diagnosis: null,
}

const LOGS: LogLine[] = [
  { seq: 40, ts: '10:24:30', text: '> tsc -b', level: 'info' },
  { seq: 41, ts: '10:24:32', text: "error TS2345: Argument of type 'string'", level: 'error' },
]

const DIAG: Diagnosis = {
  rootCause: 'TypeScript 类型错误。src/api/client.ts 第 42 行把 string 类型的值传给了期望 number 的参数。',
  suggestion: '读取环境变量后显式转换：const port = Number(process.env.PORT ?? 3000)。',
  model: 'gpt-4o-mini', latencyMs: 3_800, inputTokens: 2_100, redactions: 3,
}

async function render() {
  const w = mount(BuildDiagnosisView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('BuildDiagnosisView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getBuild.mockResolvedValue(BUILD)
    mocks.getLogs.mockResolvedValue(LOGS)
    mocks.getDiagnosis.mockResolvedValue(DIAG)
    return router.push('/builds/1091/diagnosis')
  })

  it('顶部失败条给出退出码与提交信息', async () => {
    const w = await render()
    expect(w.text()).toContain('构建 #1091 失败')
    expect(w.text()).toContain('退出码 1')
    expect(w.text()).toContain('a3f9c21')
  })

  it('日志区渲染出错误行', async () => {
    const w = await render()
    expect(w.text()).toContain('tsc -b')
    expect(w.text()).toContain('error TS2345')
  })

  it('AI 面板展示原因、建议与元信息', async () => {
    const w = await render()
    expect(w.text()).toContain('AI 智能诊断')
    expect(w.text()).toContain('可能的原因')
    expect(w.text()).toContain('建议的修改')
    expect(w.text()).toContain('src/api/client.ts 第 42 行')
    expect(w.text()).toContain('Number(process.env.PORT')
  })

  it('元信息里没有置信度百分比 —— 那个数字论文里解释不了来源', async () => {
    const w = await render()
    expect(w.text()).toContain('分析耗时')
    expect(w.text()).toContain('2.1K tokens')
    expect(w.text()).toContain('日志已脱敏 3 处')
    expect(w.text()).not.toMatch(/置信度\s*\d/)
  })

  /**
   * 关键设计：诊断是异步的附加能力，失败不能影响构建结果。
   * 界面必须把这一点说清楚，而不是显示成一个致命错误。
   */
  it('诊断失败时只降级 AI 面板，并说明不影响构建结果', async () => {
    mocks.getDiagnosis.mockRejectedValue(new Error('LLM 接口超时'))
    const w = await render()

    expect(w.text()).toContain('智能诊断未完成')
    expect(w.text()).toContain('LLM 接口超时')
    expect(w.text()).toContain('诊断失败不影响构建结果')
    expect(w.text()).toContain('重新分析')

    // 构建本身的失败信息仍然完整
    expect(w.text()).toContain('构建 #1091 失败')
    expect(w.text()).toContain('error TS2345')
  })

  it('提供重新分析入口', async () => {
    mocks.getDiagnosis.mockRejectedValueOnce(new Error('超时'))
    const w = await render()
    expect(mocks.getDiagnosis).toHaveBeenCalledTimes(1)

    mocks.getDiagnosis.mockResolvedValue(DIAG)
    const retry = w.findAll('button').find((b) => b.text().includes('重新分析'))
    expect(retry, '未找到「重新分析」按钮').toBeTruthy()
    await retry!.trigger('click')
    await flushPromises()
    expect(mocks.getDiagnosis).toHaveBeenCalledTimes(2)
  })
})
