import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { router } from '@/router'
import SecretsView from '@/views/SecretsView.vue'
import type { Secret } from '@/types'

const mocks = vi.hoisted(() => ({ listSecrets: vi.fn(), addSecret: vi.fn() }))

vi.mock('@/api', () => ({
  USE_MOCK: true,
  api: { listSecrets: mocks.listSecrets, addSecret: mocks.addSecret },
}))

const SECRETS: Secret[] = [
  { id: 1, key: 'DATABASE_URL', updatedAt: '3 天前', isSecret: true },
  { id: 2, key: 'JWT_SECRET', updatedAt: '1 周前', isSecret: true },
  { id: 3, key: 'NODE_ENV', updatedAt: '1 小时前', isSecret: false },
]

async function render() {
  const w = mount(SecretsView, { global: { plugins: [router] } })
  await flushPromises()
  return w
}

describe('SecretsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listSecrets.mockResolvedValue(SECRETS)
    return router.push('/projects/1/secrets')
  })

  it('安全说明与论文口径一致：环境变量主密钥，不提 KMS/HSM', async () => {
    const w = await render()
    expect(w.text()).toContain('AES-GCM')
    expect(w.text()).toContain('主密钥从环境变量注入，不写入数据库')
    expect(w.text()).not.toContain('KMS')
    expect(w.text()).not.toContain('硬件安全模块')
  })

  it('列出全部变量，敏感值默认掩码', async () => {
    const w = await render()
    expect(w.text()).toContain('DATABASE_URL')
    expect(w.text()).toContain('JWT_SECRET')
    expect(w.text()).toContain('NODE_ENV')
    expect(w.text()).toContain('••••••••')
  })

  it('非敏感明文变量不显示掩码（NODE_ENV=production 场景）', async () => {
    const w = await render()
    expect(w.text()).toContain('production')
  })

  it('新增表单默认收起，点开后有空值校验', async () => {
    const w = await render()
    expect(w.find('input[placeholder="DATABASE_URL"]').exists()).toBe(false)

    await w.findAll('button').find((b) => b.text().includes('添加变量'))!.trigger('click')
    expect(w.find('input[placeholder="DATABASE_URL"]').exists()).toBe(true)

    // 键名为空时保存按钮禁用
    const save = w.findAll('button').find((b) => b.text().includes('保存'))!
    expect(save.attributes('disabled')).toBeDefined()
  })

  it('填键值后保存会调用接口并刷新列表', async () => {
    mocks.addSecret.mockResolvedValue({ id: 99, key: 'API_KEY', updatedAt: '刚刚', isSecret: true })
    const w = await render()

    await w.findAll('button').find((b) => b.text().includes('添加变量'))!.trigger('click')
    await w.find('input[placeholder="DATABASE_URL"]').setValue('API_KEY')
    await w.find('input[type="password"]').setValue('super-secret')

    await w.findAll('button').find((b) => b.text().includes('保存'))!.trigger('click')
    await flushPromises()

    expect(mocks.addSecret).toHaveBeenCalledWith('API_KEY', 'super-secret')
    expect(mocks.listSecrets).toHaveBeenCalledTimes(2)   // 初始 + 保存后刷新
  })

  it('警告文案提醒不要把值打进日志', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text().includes('添加变量'))!.trigger('click')
    expect(w.text()).toContain('注意不要被构建脚本打印到日志')
  })
})
