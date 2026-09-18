import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LogTerminal from '@/components/ui/LogTerminal.vue'
import type { LogLine } from '@/types'

const lines: LogLine[] = [
  { seq: 1, ts: '10:24:28', text: '$ npm run build', level: 'info' },
  { seq: 2, ts: '10:24:32', text: 'error TS2345', level: 'error' },
  { seq: 3, ts: '10:24:33', text: 'added 412 packages', level: 'ok' },
]

describe('LogTerminal', () => {
  it('空日志时显示占位文案，不渲染日志行', () => {
    const w = mount(LogTerminal, { props: { lines: [], emptyText: '等待容器输出…' } })
    expect(w.text()).toContain('等待容器输出…')
    expect(w.findAll('.logline')).toHaveLength(0)
  })

  it('按顺序渲染每一行，含行号与时间戳', () => {
    const w = mount(LogTerminal, { props: { lines } })
    const rows = w.findAll('.logline')
    expect(rows).toHaveLength(3)
    expect(rows[0].text()).toContain('001')
    expect(rows[0].text()).toContain('[10:24:28]')
    expect(rows[0].text()).toContain('$ npm run build')
  })

  it('可以关掉行号', () => {
    const w = mount(LogTerminal, { props: { lines, showLineNo: false } })
    expect(w.findAll('.logline')[0].text()).not.toContain('001')
  })

  it('错误行有单独的高亮样式，且与其它级别不同', () => {
    const w = mount(LogTerminal, { props: { lines } })
    const rows = w.findAll('.logline')
    expect(rows[1].classes()).toContain('bg-danger/10')
    expect(rows[0].classes()).not.toContain('bg-danger/10')
  })

  it('caret 只在需要时渲染（表示日志流仍在播）', () => {
    expect(mount(LogTerminal, { props: { lines, caret: true } }).find('.caret').exists()).toBe(true)
    expect(mount(LogTerminal, { props: { lines, caret: false } }).find('.caret').exists()).toBe(false)
  })

  it('autoHeight 用 max-height 而不是固定 height（避免大片空白）', () => {
    const fixed = mount(LogTerminal, { props: { lines, height: '400px' } })
    expect(fixed.attributes('style')).toContain('height: 400px')
    expect(fixed.attributes('style')).not.toContain('max-height')

    const auto = mount(LogTerminal, { props: { lines, height: '400px', autoHeight: true } })
    expect(auto.attributes('style')).toContain('max-height: 400px')
  })

  it('日志区域带等价于 aria-live 的无障碍标记', () => {
    const w = mount(LogTerminal, { props: { lines } })
    expect(w.attributes('role')).toBe('log')
    expect(w.attributes('aria-live')).toBe('polite')
  })
})
