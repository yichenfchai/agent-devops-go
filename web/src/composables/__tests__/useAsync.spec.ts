import { describe, it, expect } from 'vitest'
import { effectScope } from 'vue'
import { flushPromises } from '@vue/test-utils'
import { useAsync, type AsyncState } from '@/composables/useAsync'

/** 在独立的 effectScope 里跑 composable —— 这样 onScopeDispose 才有意义 */
function inScope<T>(fn: () => T) {
  const scope = effectScope()
  const value = scope.run(fn)!
  return { value, scope }
}

describe('useAsync', () => {
  it('初始即 loading，成功后填充 data 并清除 loading', async () => {
    const { value: st, scope } = inScope(() => useAsync(async () => 42))
    expect((st as AsyncState<number>).loading.value).toBe(true)

    await flushPromises()

    expect(st.data.value).toBe(42)
    expect(st.loading.value).toBe(false)
    expect(st.error.value).toBeNull()
    scope.stop()
  })

  it('失败时把错误消息写进 error，且不写 data', async () => {
    const { value: st, scope } = inScope(() =>
      useAsync(async () => { throw new Error('无法连接到构建守护进程') }),
    )
    await flushPromises()

    expect(st.error.value).toBe('无法连接到构建守护进程')
    expect(st.data.value).toBeNull()
    expect(st.loading.value).toBe(false)
    scope.stop()
  })

  it('非 Error 抛出物也能归一化成可读消息', async () => {
    const { value: st, scope } = inScope(() => useAsync(async () => { throw 'boom' }))
    await flushPromises()
    expect(st.error.value).toBe('未知错误')
    scope.stop()
  })

  it('reload 会重新执行并覆盖之前的结果', async () => {
    let n = 0
    const { value: st, scope } = inScope(() => useAsync(async () => ++n))
    await flushPromises()
    expect(st.data.value).toBe(1)

    await st.reload()
    expect(st.data.value).toBe(2)
    scope.stop()
  })

  it('重试时先清掉上一次的错误', async () => {
    let fail = true
    const { value: st, scope } = inScope(() =>
      useAsync(async () => { if (fail) throw new Error('第一次失败'); return 'ok' }),
    )
    await flushPromises()
    expect(st.error.value).toBe('第一次失败')

    fail = false
    await st.reload()
    expect(st.error.value).toBeNull()
    expect(st.data.value).toBe('ok')
    scope.stop()
  })

  /**
   * 关键安全属性：组件卸载后迟到的响应不能回写。
   * 否则会出现「切走页面后旧请求覆盖新页面数据」的竞态。
   */
  it('作用域销毁后，迟到的结果不会回写 data', async () => {
    let resolveIt!: (v: string) => void
    const pending = new Promise<string>((r) => { resolveIt = r })

    const { value: st, scope } = inScope(() => useAsync(() => pending))
    scope.stop()                 // 组件卸载

    resolveIt('迟到的结果')
    await flushPromises()

    expect(st.data.value).toBeNull()
  })
})
