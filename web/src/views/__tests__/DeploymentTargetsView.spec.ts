import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import DeploymentTargetsView from '@/views/DeploymentTargetsView.vue'
import type { DeployHost } from '@/types'

const mocks = vi.hoisted(() => ({ listHosts: vi.fn(), testHost: vi.fn() }))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { listHosts: mocks.listHosts, testHost: mocks.testHost },
}))

const H = (over: Partial<DeployHost>): DeployHost => ({
  id: 1, name: 'prod-vps-01', addr: '10.0.0.8:22', sshUser: 'deploy',
  workDir: '/srv/web-api', composeFile: 'docker-compose.yml',
  healthCheckUrl: 'http://10.0.0.8:8080/healthz', healthRetries: 5, keepVersions: 5,
  status: 'ok', statusDetail: 'SSH-2.0-OpenSSH_8.9p1',
  usedBy: ['web-api', 'admin-dashboard', 'payment-service'], ...over,
})

const HOSTS = [
  H({}),
  H({ id: 2, name: 'docs-vps', addr: '10.0.0.12:22', workDir: '/srv/docs-site',
      keepVersions: 3, status: 'unreachable',
      statusDetail: '上次校验失败：ssh: connect to host 10.0.0.12 port 22: Connection refused',
      usedBy: ['docs-site'] }),
]

async function render() {
  const w = mount(DeploymentTargetsView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('DeploymentTargetsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listHosts.mockResolvedValue(HOSTS)
    return router.push('/hosts')
  })

  it('显示主机数与前置校验说明', async () => {
    const w = await render()
    expect(w.text()).toContain('共 2 台主机')
    expect(w.text()).toContain('校验目标机是否已安装 Docker 与 docker-compose')
  })

  it('每台主机一张卡：地址、目录、保留版本、被哪些项目使用', async () => {
    const w = await render()
    expect(w.text()).toContain('prod-vps-01')
    expect(w.text()).toContain('deploy@10.0.0.8:22')
    expect(w.text()).toContain('/srv/web-api')
    expect(w.text()).toContain('web-api、admin-dashboard、payment-service')
    expect(w.text()).toContain('保留 3 个历史版本')
  })

  it('不可达主机显示连接失败徽章与原始错误', async () => {
    const w = await render()
    expect(w.text()).toContain('连接失败')
    expect(w.text()).toContain('Connection refused')
  })

  it('测试连接调用接口并回显结果', async () => {
    mocks.testHost.mockResolvedValue({ ok: true, detail: 'SSH-2.0-OpenSSH_8.9p1' })
    const w = await render()

    const btn = w.findAll('button').find((b) => b.text().includes('测试连接'))!
    await btn.trigger('click')
    await flushPromises()

    expect(mocks.testHost).toHaveBeenCalledWith(1)
    expect(w.text()).toContain('SSH-2.0-OpenSSH_8.9p1')
  })

  it('添加主机抽屉：默认收起，点开显示全部表单字段', async () => {
    const w = await render()
    expect(w.find('[role="dialog"]').exists()).toBe(false)

    await w.findAll('button').find((b) => b.text().includes('添加主机'))!.trigger('click')
    const drawer = w.find('[role="dialog"]')
    expect(drawer.exists()).toBe(true)

    const txt = drawer.text()
    for (const label of ['主机名', '地址 (host:port)', '登录用户', 'SSH 私钥',
                         '目标机公钥指纹', '工作目录', '健康检查地址', '保留历史版本数']) {
      expect(txt).toContain(label)
    }
  })

  it('抽屉里的安全说明与论文口径一致（不提 KMS/HSM）', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text().includes('添加主机'))!.trigger('click')
    const txt = w.find('[role="dialog"]').text()

    expect(txt).toContain('AES-GCM')
    expect(txt).toContain('主密钥从环境变量注入，不写入数据库')
    expect(txt).not.toContain('KMS')
    expect(txt).not.toContain('硬件安全模块')
  })

  it('公钥指纹字段附防中间人说明', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text().includes('添加主机'))!.trigger('click')
    expect(w.find('[role="dialog"]').text()).toContain('ssh-keyscan')
  })
})
