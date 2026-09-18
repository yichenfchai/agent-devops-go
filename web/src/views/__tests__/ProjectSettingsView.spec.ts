import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { router } from '@/router'
import ProjectSettingsView from '@/views/ProjectSettingsView.vue'

const opts = { global: { plugins: [router] } }

async function render() {
  await router.push('/projects/1/settings')
  const w = mount(ProjectSettingsView, opts)
  return w
}

describe('ProjectSettingsView', () => {
  beforeEach(async () => {
    await router.push('/projects/1/settings')
  })

  it('三个设置分类齐全', async () => {
    const w = await render()
    for (const t of ['基本信息', '构建配置', '通知']) expect(w.text()).toContain(t)
  })

  it('默认落在构建配置：自动识别模式展示 Pipeline 与检测说明', async () => {
    const w = await render()
    expect(w.text()).toContain('自动识别')
    expect(w.text()).toContain('手动配置')
    expect(w.text()).toContain('npm ci → npm run build → docker build -t web-api:${SHA} → docker push')
    expect(w.text()).toContain('检测到 package.json · 构建镜像 node:20-alpine')
  })

  it('切到手动配置显示 YAML 编辑区', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text() === '手动配置')!.trigger('click')
    expect(w.text()).toContain('Pipeline YAML')
    expect(w.find('textarea').exists()).toBe(true)
    expect(w.find('textarea').element.value).toContain('npm ci')
  })

  it('切到基本信息显示只读仓库地址与删除项目（带警告文案）', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text().includes('基本信息'))!.trigger('click')
    const repo = w.findAll('input').find((i) => (i.element as HTMLInputElement).value.includes('github.com'))
    expect(repo).toBeTruthy()
    expect(w.text()).toContain('删除项目')
    expect(w.text()).toContain('目标机上的应用不会被卸载')
  })

  it('切到通知显示三个开关与渠道选择', async () => {
    const w = await render()
    await w.findAll('button').find((b) => b.text().includes('通知'))!.trigger('click')
    for (const t of ['构建失败时通知', '部署成功时通知', '自动回滚发生时通知']) {
      expect(w.text()).toContain(t)
    }
    expect(w.text()).toContain('Webhook')
    expect(w.text()).toContain('邮件')
  })

  it('日志保留行数是普通数字输入（不是环形缓冲区之类的设计稿遗留）', async () => {
    const w = await render()
    expect(w.text()).toContain('日志保留行数')
    expect(w.text()).not.toContain('环形缓冲')
  })
})
