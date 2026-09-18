import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StageList from '@/components/ui/StageList.vue'
import StageRail from '@/components/ui/StageRail.vue'
import { stages1091, stages1092 } from '@/api/mock'

describe('StageList', () => {
  it('渲染全部阶段并带序号', () => {
    const w = mount(StageList, { props: { stages: stages1091 } })
    const items = w.findAll('li')
    expect(items).toHaveLength(stages1091.length)
    expect(items[0].text()).toContain('01')
    expect(items[2].text()).toContain('03')
  })

  it('把毫秒格式化成秒', () => {
    const w = mount(StageList, { props: { stages: stages1091 } })
    expect(w.text()).toContain('4.2s')
    expect(w.text()).toContain('12.4s')
  })

  it('已跳过与未开始的阶段显示为占位符，而不是 0ms', () => {
    const w = mount(StageList, { props: { stages: stages1091 } })
    expect(w.text()).toContain('已跳过')
    expect(w.text()).not.toContain('0.0s')
  })

  it('失败阶段被标红，成功阶段被标绿', () => {
    const w = mount(StageList, { props: { stages: stages1091 } })
    const html = w.html()
    expect(html).toContain('border-danger/40')
    expect(html).toContain('border-success/25')
  })

  it('运行中的阶段显示进行中而不是时长（还没有最终耗时）', () => {
    const w = mount(StageList, { props: { stages: stages1092 } })
    expect(w.text()).toContain('进行中')
  })
})

describe('StageRail（六阶段横排）', () => {
  it('每个阶段渲染成一格', () => {
    const w = mount(StageRail, { props: { stages: stages1091 } })
    expect(w.findAll('li')).toHaveLength(6)
  })

  it('失败格有独立样式', () => {
    const w = mount(StageRail, { props: { stages: stages1091 } })
    expect(w.findAll('li')[2].classes()).toContain('border-danger/50')
  })
})
