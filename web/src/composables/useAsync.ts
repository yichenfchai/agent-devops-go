/**
 * 统一的异步数据获取：loading / error / retry / 卸载即取消。
 * 所有页面都用它，避免每个页面各写一套 ref 状态机。
 */
import { ref, shallowRef, watch, onScopeDispose, type Ref, type WatchSource } from 'vue'
import { ApiError } from '@/api/client'

export interface AsyncState<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  reload: () => Promise<void>
}

export function useAsync<T>(fn: () => Promise<T>, deps?: WatchSource | WatchSource[]): AsyncState<T> {
  const data = shallowRef<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let ctrl: AbortController | null = null

  async function run() {
    ctrl?.abort()
    ctrl = new AbortController()
    const mine = ctrl
    loading.value = true
    error.value = null
    try {
      const res = await fn()
      if (mine.signal.aborted) return
      data.value = res
    } catch (e) {
      if (mine.signal.aborted) return
      if (e instanceof DOMException && e.name === 'AbortError') return
      error.value = e instanceof ApiError ? e.message : e instanceof Error ? e.message : '未知错误'
    } finally {
      if (!mine.signal.aborted) loading.value = false
    }
  }

  if (deps) watch(deps, run, { immediate: true })
  else void run()

  onScopeDispose(() => ctrl?.abort())

  return { data, loading, error, reload: run }
}
