/**
 * usePolling 的竞态回归测试：审查发现旧 tick 在 await 挂起期间发生
 * pause→resume 会造成双链轮询（频率翻倍）。本文件钉住该缺陷。
 *
 * 要点：usePolling 内部用 onMounted 排首个定时器，必须在组件 setup() 内
 * 调用 —— 测试用宿主组件在 setup 里调用并透出 API；fake timer 用
 * advanceTimersByTimeAsync（虚拟时间推进间自动冲刷微任务，适配 async tick）。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { usePolling } from '../usePolling'

type PollApi = ReturnType<typeof usePolling>

function mountHost(fn: () => void | Promise<void>, intervalMs: number): PollApi {
  let api!: PollApi
  const Host = defineComponent({
    setup() {
      api = usePolling(fn, intervalMs)
      return () => h('div')
    },
  })
  mount(Host)   // 挂载时 onMounted 执行，首个 setTimeout 进入 fake timeline
  return api
}

describe('usePolling', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('正常节奏轮询，pause 停止、resume 重启', async () => {
    let calls = 0
    const fn = vi.fn(async () => { calls++ })
    const { pause, resume, active } = mountHost(fn, 500)

    await vi.advanceTimersByTimeAsync(500)
    expect(calls).toBe(1)
    await vi.advanceTimersByTimeAsync(1000)
    expect(calls).toBe(3)

    pause()
    expect(active.value).toBe(false)
    await vi.advanceTimersByTimeAsync(2000)
    expect(calls).toBe(3)          // 暂停后不再增加

    resume()
    expect(active.value).toBe(true)
    await vi.advanceTimersByTimeAsync(0)   // resume 的立即 tick
    expect(calls).toBe(4)
    await vi.advanceTimersByTimeAsync(500)
    expect(calls).toBe(5)          // 恢复后按节奏继续
  })

  it('竞态：await 挂起中 pause→resume 不产生双链（频率不翻倍）', async () => {
    let calls = 0
    // fn 挂起一个手工控制的 promise，模拟慢请求恰好卡在 pause/resume 交错点
    let release!: () => void
    const gate = new Promise<void>((r) => { release = r })
    const fn = vi.fn(async () => { calls++; await gate })

    const { pause, resume } = mountHost(fn, 1000)

    // 第 1 次 tick 触发，fn 挂起中（这条旧链卡在 await gate）
    await vi.advanceTimersByTimeAsync(1000)
    expect(calls).toBe(1)

    // 挂起期间 pause → resume：active 被置回 true，resume 另起新 tick（calls=2）
    pause()
    resume()
    await vi.advanceTimersByTimeAsync(0)
    expect(calls).toBe(2)

    // 释放旧 tick 的 await —— 旧 tick 进入 finally
    release()
    await vi.advanceTimersByTimeAsync(0)

    // 未修复时：旧 tick 看到 active===true 会续排 timer，与新链并行 → 频率翻倍
    // 修复后：旧 tick 的 gen 已过期，只有 resume 起的新链在跑
    await vi.advanceTimersByTimeAsync(3000)
    expect(calls).toBe(2 + 3)      // 新链 1000ms 一跳，3 秒 +3；若双链会是 +6
  })
})
