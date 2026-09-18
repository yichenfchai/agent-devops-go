import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import ProjectListView from '@/views/ProjectListView.vue'
import type { Project } from '@/types'

const mocks = vi.hoisted(() => ({
  listProjects: vi.fn(),
  getRunner: vi.fn(),
  triggerBuild: vi.fn(),
}))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: {
    listProjects: mocks.listProjects,
    getRunner: mocks.getRunner,
    triggerBuild: mocks.triggerBuild,
  },
}))

const P = (over: Partial<Project>): Project => ({
  id: 1, name: 'web-api', repoProvider: 'github', repoFullName: 'acme/web-api',
  defaultBranch: 'main', detectedType: 'Node.js', deployHostId: 1,
  lastBuild: { number: 1091, state: 'failed', finishedAt: '3 分钟前', durationMs: 28_140 },
  deployed: true, created_at: '2026-06-02', ...over,
})

async function render() {
  const w = mount(ProjectListView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('ProjectListView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getRunner.mockResolvedValue({
      name: 'build-runner-01', os: 'Ubuntu 22.04 LTS', version: 'v1.4.2', state: 'idle', queued: 0,
    })
    return router.push('/projects')
  })

  it('加载中先渲染骨架屏，不是空白', async () => {
    mocks.listProjects.mockReturnValue(new Promise(() => {}))   // 永不 resolve
    const w = mount(ProjectListView, { global: { plugins: [router] } })
    expect(w.find('[aria-busy="true"]').exists()).toBe(true)
    expect(w.text()).not.toContain('还没有项目')
  })

  it('渲染每个项目的名称、仓库与最后构建信息', async () => {
    mocks.listProjects.mockResolvedValue([P({}), P({ id: 2, name: 'docs-site', repoFullName: 'acme/docs-site' })])
    const w = await render()

    expect(w.text()).toContain('web-api')
    expect(w.text()).toContain('acme/docs-site')
    expect(w.text()).toContain('共 2 个项目')
    expect(w.text()).toContain('上次构建 #1091')
    expect(w.text()).toContain('28s')
  })

  it('没有项目时显示引导式空状态，而不是空表格', async () => {
    mocks.listProjects.mockResolvedValue([])
    const w = await render()

    expect(w.text()).toContain('还没有项目')
    expect(w.text()).toContain('连接一个 GitHub 仓库')
    expect(w.text()).toContain('新建项目')
  })

  it('请求失败时显示守护进程引导，而不是干瘪的错误码', async () => {
    mocks.listProjects.mockRejectedValue(new Error('无法连接到构建守护进程'))
    const w = await render()

    expect(w.text()).toContain('无法连接到构建守护进程')
    expect(w.text()).toContain('systemctl status devopsd')   // 给出可执行的排查命令
    expect(w.text()).toContain('重试连接')
  })

  it('点重试会重新请求', async () => {
    mocks.listProjects.mockRejectedValueOnce(new Error('网络错误'))
    const w = await render()
    expect(mocks.listProjects).toHaveBeenCalledTimes(1)

    mocks.listProjects.mockResolvedValue([P({})])
    await w.find('button').trigger('click')      // 空状态里的「重试连接」
    await flushPromises()
    expect(mocks.listProjects).toHaveBeenCalledTimes(2)
  })

  it('未配置部署目标的项目给出显式提示和配置入口', async () => {
    mocks.listProjects.mockResolvedValue([P({ id: 4, name: 'payment-service', deployHostId: null, lastBuild: null })])
    const w = await render()

    expect(w.text()).toContain('未配置部署目标')
    expect(w.text()).toContain('暂无部署记录')
    expect(w.text()).toContain('配置部署')
  })

  it('构建机信息来自接口，而不是写死在模板里', async () => {
    mocks.listProjects.mockResolvedValue([P({})])
    const w = await render()
    expect(w.text()).toContain('build-runner-01')
    expect(w.text()).toContain('构建机状态')
  })
})
