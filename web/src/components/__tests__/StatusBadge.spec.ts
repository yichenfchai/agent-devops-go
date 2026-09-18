import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import type { BuildState } from '@/types'

const ALL_STATES: BuildState[] = [
  'queued', 'running', 'succeeded', 'deploying',
  'deployed', 'failed', 'deploy_failed', 'rolled_back',
]

function textOf(state: unknown) {
  return mount(StatusBadge, { props: { state: state as never } }).text()
}

describe('StatusBadge', () => {
  it('每个构建状态都有对应文案，不会露出原始英文枚举', () => {
    for (const s of ALL_STATES) {
      const t = textOf(s)
      expect(t.length).toBeGreaterThan(0)
      expect(t).not.toBe(s)
    }
  })

  it('关键状态的文案正确', () => {
    expect(textOf('running')).toContain('运行中')
    expect(textOf('failed')).toContain('失败')
    expect(textOf('rolled_back')).toContain('已回滚')
    expect(textOf('queued')).toContain('排队中')
  })

  it('未知状态回退到原样显示，而不是空白', () => {
    expect(textOf('something_new')).toContain('something_new')
  })

  it('失败用红色系、成功用绿色系 —— 颜色语义不能串', () => {
    expect(mount(StatusBadge, { props: { state: 'failed' } }).html()).toContain('bg-danger')
    expect(mount(StatusBadge, { props: { state: 'succeeded' } }).html()).toContain('bg-success')
    expect(mount(StatusBadge, { props: { state: 'queued' } }).html()).toContain('bg-warning')
  })

  /**
   * deployed 在部署语境下的文案是「部署成功」。
   * 圆点而不是对勾：对勾留给 succeeded（构建成功），圆点表达「健康在跑」。
   */
  it('deployed 用圆点而不是对勾（对勾语义是成功）', () => {
    const html = mount(StatusBadge, { props: { state: 'deployed' } }).html()
    expect(html).toContain('rounded-full')
    expect(html).toContain('部署成功')
  })
})
