import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { router } from '@/router'
import StatesDemoView from '@/views/StatesDemoView.vue'

const opts = { global: { plugins: [router] } }

async function render() {
  await router.push('/states')
  return mount(StatesDemoView, opts)
}

describe('StatesDemoView（空态 / 排队 / 错误 / 加载）', () => {
  beforeEach(async () => {
    await router.push('/states')
  })

  it('四个场景卡齐全', async () => {
    const w = await render()
    for (const t of ['项目列表为空', '构建尚未开始', '请求守护进程失败', '数据加载中']) {
      expect(w.text()).toContain(t)
    }
  })

  it('空态场景提供新建项目与 CLI 导入两个入口', async () => {
    const w = await render()
    expect(w.text()).toContain('还没有项目')
    expect(w.text()).toContain('连接一个 GitHub 仓库，push 代码后自动构建部署')
    expect(w.text()).toContain('CLI 导入')
  })

  it('排队场景显示序号与预计等待，构建机名是唯一的 build-runner-01', async () => {
    const w = await render()
    expect(w.text()).toContain('排队中 · 序号 #1')
    expect(w.text()).toContain('预计等待 ~14s')
    expect(w.text()).toContain('build-runner-01')
    // 回归：设计稿曾出现 local-executor-0
    expect(w.text()).not.toContain('local-executor-0')
  })

  it('错误场景给出可执行的排查命令与重试', async () => {
    const w = await render()
    expect(w.text()).toContain('无法连接到构建守护进程')
    expect(w.text()).toContain('ECONNREFUSED')
    expect(w.text()).toContain('systemctl status devopsd')
    expect(w.text()).toContain('重试连接')
  })

  it('加载场景用骨架屏而不是转圈', async () => {
    const w = await render()
    expect(w.find('[aria-busy="true"]').exists()).toBe(true)
  })

  it('页脚写明退避策略', async () => {
    const w = await render()
    expect(w.text()).toContain('Backoff: 1s, 2s, 4s, 8s')
  })

  it('重试按钮点击后进入加载态', async () => {
    const w = await render()
    const btn = w.findAll('button').find((b) => b.text().includes('重试连接'))!
    expect(btn.attributes('disabled')).toBeUndefined()
    await btn.trigger('click')
    expect(btn.attributes('disabled')).toBeDefined()
  })
})
