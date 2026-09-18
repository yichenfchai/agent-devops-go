import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { usePolling } from '@/composables/usePolling'

/** usePolling 依赖 onMounted / onUnmounted，必须挂在组件里测 */
const Harness = defineComponent({
  props: { fn: { type: Function, required: true }, interval: { type: Number, default: 1000 } },
  setup(props) {
    const ctl = usePolling(() => props.fn(), props.interval)
    return () => h('div', { class: ctl.active.value ? 'active' : 'idle' })
  },
})

describe('usePolling', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('挂载后按间隔重复调用', async () => {
    const fn = vi.fn()
    mount(Harness, { props: { fn, interval: 1000 } })

    expect(fn).not.toHaveBeenCalled()       // 首次调用在第一个间隔之后
    await vi.advanceTimersByTimeAsync(1000)
    expect(fn).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(2000)
    expect(fn).toHaveBeenCalledTimes(3)
  })

  it('卸载后停止轮询（页面切走不再占后台资源）', async () => {
    const fn = vi.fn()
    const w = mount(Harness, { props: { fn, interval: 1000 } })
    await vi.advanceTimersByTimeAsync(1000)
    expect(fn).toHaveBeenCalledTimes(1)

    w.unmount()
    await vi.advanceTimersByTimeAsync(5000)
    expect(fn).toHaveBeenCalledTimes(1)     // 没有再增加
  })

  it('上一次还没跑完时不会并发叠加', async () => {
    let resolveIt!: () => void
    const fn = vi.fn(() => new Promise<void>((r) => { resolveIt = r }))
    mount(Harness, { props: { fn, interval: 1000 } })

    await vi.advanceTimersByTimeAsync(1000)
    expect(fn).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(3000)   // 上一次未 resolve
    expect(fn).toHaveBeenCalledTimes(1)

    resolveIt()
    await vi.advanceTimersByTimeAsync(1000)
    expect(fn).toHaveBeenCalledTimes(2)
  })
})
