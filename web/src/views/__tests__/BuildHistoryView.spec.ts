import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import BuildHistoryView from '@/views/BuildHistoryView.vue'
import type { Build } from '@/types'

const mocks = vi.hoisted(() => ({
  listBuilds: vi.fn(), getBuildStats: vi.fn(), rollbackTo: vi.fn(),
}))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: {
    listBuilds: mocks.listBuilds,
    getBuildStats: mocks.getBuildStats,
    rollbackTo: mocks.rollbackTo,
  },
}))

const B = (over: Partial<Build>): Build => ({
  id: 1091, projectId: 1, number: 1091, state: 'failed', trigger: 'push', ref: 'main',
  commitSha: 'a3f9c21', commitMessage: '修复部署脚本的环境变量读取', commitAuthor: 'M. Alvarez',
  baseImage: 'node:20-alpine', imageTag: null, exitCode: 1,
  queuedAt: '10 分钟前', startedAt: null, finishedAt: null,
  durationMs: 28_140, diagnosis: null, ...over,
})

const BUILDS = [
  B({}),
  B({ id: 1090, number: 1090, state: 'deployed', trigger: 'manual', commitSha: '7b1e044',
      commitMessage: '优化数据库查询索引', exitCode: 0, durationMs: 134_000 }),
  B({ id: 1088, number: 1088, state: 'deployed', commitSha: '91c4d2e',
      commitMessage: '更新 API 参考文档', exitCode: 0, durationMs: 19_000 }),
]

async function render() {
  const w = mount(BuildHistoryView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('BuildHistoryView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listBuilds.mockResolvedValue(BUILDS)
    mocks.getBuildStats.mockResolvedValue({
      total: 128, successRate: 92.2, avgDurationMs: 41_000, monthlyDeploys: 37,
    })
    return router.push('/projects/1/builds')
  })

  it('渲染统计卡', async () => {
    const w = await render()
    expect(w.text()).toContain('总构建数')
    expect(w.text()).toContain('128')
    expect(w.text()).toContain('92.2%')
  })

  /**
   * 回归测试：设计稿里构建历史表格给 #1091 写的是 48s，
   * 而其它 5 个页面都是 28s —— 同一个构建两个耗时。
   */
  it('构建 #1091 的耗时与其它页面一致（不是设计稿里的 48s）', async () => {
    const w = await render()
    const row1091 = w.findAll('tbody tr').find((r) => r.text().includes('#1091'))
    expect(row1091).toBeTruthy()
    expect(row1091!.text()).toContain('28s')
    expect(row1091!.text()).not.toContain('48s')
  })

  it('每一行都有 commit sha 与触发源', async () => {
    const w = await render()
    const rows = w.findAll('tbody tr')
    expect(rows).toHaveLength(3)
    expect(rows[0].text()).toContain('a3f9c21')
    expect(rows[0].text()).toContain('Git Hook (push)')
  })

  it('进行中的构建用左侧高亮条标出', async () => {
    mocks.listBuilds.mockResolvedValue([B({ state: 'running', exitCode: null, durationMs: null })])
    const w = await render()
    expect(w.find('tbody tr').classes()).toContain('border-l-primary')
  })

  it('按状态过滤只保留匹配的行', async () => {
    const w = await render()
    expect(w.findAll('tbody tr')).toHaveLength(3)

    await w.find('select').setValue('failed')
    expect(w.findAll('tbody tr')).toHaveLength(1)
    expect(w.text()).toContain('#1091')
  })

  it('过滤后无结果时显示空状态，而不是空表格', async () => {
    const w = await render()
    await w.find('select').setValue('rolled_back')
    expect(w.find('tbody').exists()).toBe(false)
    expect(w.text()).toContain('没有匹配的构建记录')
  })

  it('只有已部署的构建才提供回滚入口', async () => {
    const w = await render()
    // 3 行里 2 行是 deployed
    expect(w.findAll('[title="回滚到此版本"]')).toHaveLength(2)
  })

  it('点回滚弹出确认框，且不会直接执行', async () => {
    const w = await render()
    await w.find('[title="回滚到此版本"]').trigger('click')

    expect(w.find('[role="dialog"]').exists()).toBe(true)
    expect(w.text()).toContain('回滚到上一个版本')
    expect(w.text()).toContain('5–10 秒服务不可用')
    expect(mocks.rollbackTo).not.toHaveBeenCalled()   // 必须显式确认
  })
})
