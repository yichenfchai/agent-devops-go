import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import DeploymentDetailView from '@/views/DeploymentDetailView.vue'

const mocks = vi.hoisted(() => ({ getDeployment: vi.fn() }))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { getDeployment: mocks.getDeployment },
}))

const DEP = {
  id: 1, buildId: 1090, projectName: 'web-api', imageTag: 'web-api:a3f9c21',
  hostAddr: 'deploy@10.0.0.8', workDir: '/srv/web-api', state: 'deployed' as const,
  startedAt: '10:25:04', durationMs: 19_500,
  steps: [
    { index: 1, name: '连接目标主机', command: 'SSH deploy@10.0.0.8:22，主机密钥校验通过', status: 'passed' as const, durationMs: 800 },
    { index: 2, name: '推送镜像 tag', command: 'registry.local/web-api:a3f9c21', status: 'passed' as const, durationMs: 1400 },
    { index: 3, name: '健康检查', command: 'GET /healthz 连续 3 次返回 200', status: 'passed' as const, durationMs: 9000 },
  ],
  versions: [
    { tag: 'web-api:a3f9c21', deployedAt: '10 分钟前', state: '当前版本' },
    { tag: 'web-api:7b1e044', deployedAt: '2 小时前', state: '成功' },
    { tag: 'web-api:91c4d2e', deployedAt: '昨天', state: '成功' },
  ],
}

async function render() {
  const w = mount(DeploymentDetailView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('DeploymentDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getDeployment.mockResolvedValue(DEP)
    return router.push('/builds/1090/deployment')
  })

  it('摘要条显示成功状态、镜像与目标主机', async () => {
    const w = await render()
    expect(w.text()).toContain('部署成功')
    expect(w.text()).toContain('web-api:a3f9c21')
    expect(w.text()).toContain('deploy@10.0.0.8')
    expect(w.text()).toContain('19.5s')
  })

  it('部署步骤时间线渲染每一步与命令', async () => {
    const w = await render()
    expect(w.text()).toContain('连接目标主机')
    expect(w.text()).toContain('主机密钥校验通过')
    expect(w.text()).toContain('GET /healthz 连续 3 次返回 200')
  })

  it('右侧信息卡列出主机与目录配置', async () => {
    const w = await render()
    expect(w.text()).toContain('部署信息')
    expect(w.text()).toContain('/srv/web-api')
    expect(w.text()).toContain('docker-compose.yml')
  })

  it('版本历史展示全部版本', async () => {
    const w = await render()
    expect(w.text()).toContain('版本历史')
    expect(w.text()).toContain('web-api:7b1e044')
    expect(w.text()).toContain('web-api:91c4d2e')
  })

  it('每个历史版本都有回滚入口，点开弹确认框', async () => {
    const w = await render()
    const btns = w.findAll('button').filter((b) => b.text().includes('回滚到此版本'))
    expect(btns.length).toBeGreaterThanOrEqual(2)

    await btns[0].trigger('click')
    expect(w.find('[role="dialog"]').exists()).toBe(true)
    expect(w.text()).toContain('回滚到上一个版本')
  })
})
