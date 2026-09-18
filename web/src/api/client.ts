/**
 * 极简 API 客户端：统一前缀、JSON、超时、错误归一化。
 * 窗口关闭 / 组件卸载时通过 AbortSignal 取消下游请求。
 */

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly url: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  timeoutMs?: number
}

const BASE = '/api'
/** 是否走 mock。后端起来后把 .env 里的 VITE_USE_MOCK 改成 false 即可切换。 */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal, timeoutMs = 15_000 } = opts

  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(new DOMException('timeout', 'TimeoutError')), timeoutMs)
  // 转发上层取消：组件卸载 / 路由切换时取消下游请求
  const forwardAbort = () => ctrl.abort(signal?.reason)
  signal?.addEventListener('abort', forwardAbort, { once: true })

  try {
    const res = await fetch(BASE + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    })
    if (!res.ok) {
      throw new ApiError(`请求失败：${res.status} ${res.statusText}`, res.status, path)
    }
    if (res.status === 204) return undefined as T
    return (await res.json()) as T
  } catch (e) {
    if (e instanceof ApiError) throw e
    if (e instanceof DOMException && e.name === 'AbortError') throw e
    throw new ApiError(e instanceof Error ? e.message : '网络错误', 0, path)
  } finally {
    clearTimeout(timer)
    // 无论成功失败都摘掉监听 —— 不复用的 signal 还好，复用同一个 signal 发多次
    // 请求时，否则会累积出 N 个永不触发的监听
    signal?.removeEventListener('abort', forwardAbort)
  }
}

export const http = {
  get:  <T>(p: string, o?: RequestOptions) => request<T>(p, { ...o, method: 'GET' }),
  post: <T>(p: string, body?: unknown, o?: RequestOptions) => request<T>(p, { ...o, method: 'POST', body }),
  patch:<T>(p: string, body?: unknown, o?: RequestOptions) => request<T>(p, { ...o, method: 'PATCH', body }),
  del:  <T>(p: string, o?: RequestOptions) => request<T>(p, { ...o, method: 'DELETE' }),
}
