import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { router } from '@/router'
import LoginView from '@/views/LoginView.vue'

const opts = { global: { plugins: [router] } }

async function render() {
  await router.push('/login')
  return mount(LoginView, opts)
}

function fill(w: ReturnType<typeof mount>, email = 'dev@acme.io', pwd = 'correct-horse') {
  const [emailInput, pwdInput] = w.findAll('input')
  return emailInput.setValue(email).then(() => pwdInput.setValue(pwd))
}

describe('LoginView', () => {
  beforeEach(async () => {
    await router.push('/login')
  })

  it('品牌信息与产品定位文案', async () => {
    const w = await render()
    expect(w.text()).toContain('GoPulse CI')
    expect(w.text()).toContain('轻量 CI/CD · 面向小型团队')
  })

  it('页脚展示单二进制形态 —— 与产品定位一致', async () => {
    const w = await render()
    expect(w.text()).toContain('单二进制部署')
    expect(w.text()).toContain('SQLite 嵌入式存储')
    expect(w.text()).toContain('v0.1.0')
  })

  it('必填字段为空时表单不可提交（原生校验拦截）', async () => {
    const w = await render()
    const form = w.find('form')
    // jsdom 不跑原生校验，但 required 属性必须在 —— 断言它在
    // 只有邮箱与密码是必填；「记住此会话」的 checkbox 不算
    const required = w.findAll('input').filter(
      (i) => (i.element as HTMLInputElement).required,
    )
    expect(required).toHaveLength(2)
    expect(form.exists()).toBe(true)
  })

  it('提交后跳转到项目列表（暂为模拟登录）', async () => {
    const w = await render()
    await fill(w)

    await w.find('form').trigger('submit')
    // 模拟登录内部是 400ms setTimeout；不用 fake timer，
    // 真实等 600ms 让登录完成 + 路由跳转落地（jsdom 下两者对 fake timer 都不友好）
    await new Promise((r) => setTimeout(r, 600))

    expect(router.currentRoute.value.path).toBe('/projects')
  })
})
