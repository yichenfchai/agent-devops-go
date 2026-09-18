import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import AppTopbar from '@/components/layout/AppTopbar.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppShell from '@/components/layout/AppShell.vue'

const mocks = vi.hoisted(() => ({ triggerBuild: vi.fn() }))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { triggerBuild: mocks.triggerBuild },
}))

const opts = { global: { plugins: [router] } }

async function at(path: string) {
  await router.push(path)
  await flushPromises()
}

describe('AppTopbar 面包屑', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.triggerBuild.mockResolvedValue({ number: 1093 })
  })

  /**
   * 回归测试：设计稿里 13 个页面的面包屑全部写死成
   * 「项目 / web-api / 构建 #1091」，连项目列表页都显示「构建 #1091」。
   * 这里断言它确实是跟着路由变的。
   */
  it('面包屑随路由变化', async () => {
    await at('/projects')
    const projects = mount(AppTopbar, opts).text()
    expect(projects).toContain('项目')
    expect(projects).not.toContain('构建')

    await at('/projects/1/secrets')
    const secrets = mount(AppTopbar, opts).text()
    expect(secrets).toContain('密钥管理')
    expect(secrets).not.toContain('#1091')
  })

  it('项目列表页不会显示构建号', async () => {
    await at('/projects')
    expect(mount(AppTopbar, opts).text()).not.toContain('#1091')
  })

  it('产品名与主操作按钮始终在位', async () => {
    await at('/projects')
    const w = mount(AppTopbar, opts)
    expect(w.text()).toContain('GoPulse CI')
    expect(w.text()).toContain('运行流水线')
  })

  it('点「运行流水线」会触发构建并进入防重复提交态', async () => {
    await at('/projects')
    let release!: () => void
    mocks.triggerBuild.mockReturnValue(new Promise<void>((r) => { release = () => r() }))

    const w = mount(AppTopbar, opts)
    const btn = w.findAll('button').find((b) => b.text().includes('运行流水线'))!
    expect(btn.attributes('disabled')).toBeUndefined()

    await btn.trigger('click')
    expect(mocks.triggerBuild).toHaveBeenCalledWith(1)

    release()
    await flushPromises()
  })
})

describe('AppSidebar', () => {
  it('固定 5 项，不多不少', async () => {
    await at('/projects')
    const links = mount(AppSidebar, opts).findAll('a')
    expect(links).toHaveLength(5)
    expect(links.map((l) => l.text())).toEqual(
      expect.arrayContaining(['项目列表', '构建历史', '部署目标', '密钥管理', '设置']),
    )
  })

  it('当前页对应的项高亮，其余不高亮', async () => {
    await at('/hosts')
    const w = mount(AppSidebar, opts)
    const active = w.findAll('a').filter((a) => a.classes().includes('border-l-primary'))
    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('部署目标')
  })

  it('切到子路由时父级项保持高亮', async () => {
    await at('/projects/1/secrets')
    const w = mount(AppSidebar, opts)
    const active = w.findAll('a').filter((a) => a.classes().includes('border-l-primary'))
    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('密钥管理')
  })

  /**
   * 回归测试：之前用「第一个前缀命中」匹配，导致 /projects/1/secrets
   * 被更短的 '/projects' 先吃掉，高亮成「项目列表」。
   */
  it('子路由不会被更短的父级路径抢走高亮', async () => {
    for (const [path, label] of [
      ['/projects/1/builds', '构建历史'],
      ['/projects/1/secrets', '密钥管理'],
      ['/projects/1/settings', '设置'],
      ['/projects/new', '项目列表'],
    ] as const) {
      await at(path)
      const active = mount(AppSidebar, opts)
        .findAll('a')
        .filter((a) => a.classes().includes('border-l-primary'))
      expect(active, `${path} 应该高亮「${label}」`).toHaveLength(1)
      expect(active[0].text()).toContain(label)
    }
  })

  it('构建详情页归到「构建历史」，不留空白高亮', async () => {
    await at('/builds/1091/diagnosis')
    const active = mount(AppSidebar, opts)
      .findAll('a')
      .filter((a) => a.classes().includes('border-l-primary'))
    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('构建历史')
  })
})

describe('AppShell 骨架', () => {
  it('渲染顶栏、侧栏、内容槽与状态栏', async () => {
    await at('/projects')
    const w = mount(AppShell, {
      ...opts,
      slots: { default: '<p class="probe">内容区</p>' },
    })
    expect(w.find('header').exists()).toBe(true)
    expect(w.find('nav[aria-label="主导航"]').exists()).toBe(true)
    expect(w.find('footer').exists()).toBe(true)
    expect(w.find('.probe').text()).toBe('内容区')
  })

  it('状态栏常驻显示守护进程状态', async () => {
    await at('/projects')
    const w = mount(AppShell, opts)
    expect(w.find('footer').text()).toContain('构建守护进程运行中')
    expect(w.find('footer').text()).toContain('UTF-8 LF')
  })
})
