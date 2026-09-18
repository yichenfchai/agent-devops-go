import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import ProjectWizardView from '@/views/ProjectWizardView.vue'
import { hosts as HOSTS } from '@/api/mock'

const mocks = vi.hoisted(() => ({ listHosts: vi.fn(), createProject: vi.fn() }))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { listHosts: mocks.listHosts, createProject: mocks.createProject },
}))

async function render() {
  const w = mount(ProjectWizardView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

function next(w: ReturnType<typeof mount>) {
  return w.findAll('button').find((b) => b.text().includes('下一步'))!
}

describe('ProjectWizardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listHosts.mockResolvedValue(HOSTS)
    mocks.createProject.mockResolvedValue({})
    return router.push('/projects/new')
  })

  it('三步指示器齐全', async () => {
    const w = await render()
    expect(w.text()).toContain('连接仓库')
    expect(w.text()).toContain('配置部署')
    expect(w.text()).toContain('确认并上线')
  })

  it('第一步显示 Webhook 配置代码块', async () => {
    const w = await render()
    expect(w.text()).toContain('Payload URL')
    expect(w.text()).toContain('Secret')
    expect(w.text()).toContain('https://ci.example.com/api/webhooks/github')
  })

  it('仓库地址没填时不能进下一步', async () => {
    const w = await render()
    const btn = w.findAll('button').find((b) => b.text().includes('下一步'))!
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('填了仓库地址后可以进第二步并看到类型识别', async () => {
    const w = await render()
    await w.find('input').setValue('https://github.com/acme/web-api')
    await next(w).trigger('click')
    await flushPromises()

    expect(w.text()).toContain('已自动识别项目类型：Node.js')
    expect(w.text()).toContain('package.json')
    expect(w.text()).toContain('node:20-alpine')
  })

  it('第二步：不可达的主机不可选', async () => {
    const w = await render()
    await w.find('input').setValue('https://github.com/acme/web-api')
    await next(w).trigger('click')
    await flushPromises()

    const opt = w.findAll('option').find((o) => o.text().includes('docs-vps'))
    expect(opt!.element as HTMLOptionElement && (opt!.element as HTMLOptionElement).disabled).toBe(true)
  })

  it('自动回滚开关默认开启', async () => {
    const w = await render()
    await w.find('input').setValue('https://github.com/acme/web-api')
    await next(w).trigger('click')
    await flushPromises()

    const cb = w.findAll('input[type="checkbox"]').at(0)
    expect((cb!.element as HTMLInputElement).checked).toBe(true)
  })

  it('走完三步在确认页汇总配置，然后创建', async () => {
    const w = await render()
    await w.find('input').setValue('https://github.com/acme/web-api')
    await next(w).trigger('click')
    await flushPromises()

    // 选部署目标
    const select = w.find('select')
    await select.setValue('1')
    await next(w).trigger('click')
    await flushPromises()

    expect(w.text()).toContain('确认配置')
    expect(w.text()).toContain('https://github.com/acme/web-api')
    expect(w.text()).toContain('prod-vps-01')
    expect(w.text()).toContain('开启')        // 自动回滚

    await w.findAll('button').find((b) => b.text().includes('创建项目'))!.trigger('click')
    await flushPromises()
    expect(mocks.createProject).toHaveBeenCalledTimes(1)
  })
})
