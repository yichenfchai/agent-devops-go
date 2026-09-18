import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { http, ApiError } from '@/api/client'

/**
 * client.ts 是真实环境里最容易出问题的层：它管重试、超时、
 * AbortSignal、错误归一化。mock 模式根本走不到这里，
 * 所以必须桩掉 globalThis.fetch 来测。
 */

function jsonResponse(status: number, body: unknown, statusText = 'OK') {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: () => Promise.resolve(body),
    // fetch Response 的其它字段不需要
  } as unknown as Response
}

describe('api client（真实 fetch 分支）', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn())
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('GET 请求走 /api 前缀并返回解析后的 JSON', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { id: 1, name: 'web-api' }))
    const data = await http.get('/projects')
    expect(data).toEqual({ id: 1, name: 'web-api' })
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe('/api/projects')
  })

  it('POST 自动加 Content-Type 和 JSON 序列化 body', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(201, { id: 7 }))
    await http.post('/projects', { name: 'docs-site' })
    const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(JSON.parse(init.body as string)).toEqual({ name: 'docs-site' })
  })

  it('204 No Content 返回 undefined，不去解析 body', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(204, null))
    const res = await http.del('/projects/9')
    expect(res).toBeUndefined()
  })

  it('非 2xx 归一化为 ApiError，带状态码与 URL', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(503, {}, 'Service Unavailable'))
    try {
      await http.get('/builds')
      expect.unreachable('不该走到这里')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      expect((e as ApiError).status).toBe(503)
      expect((e as ApiError).url).toBe('/builds')
      expect((e as ApiError).message).toContain('503')
      expect((e as ApiError).message).toContain('Service Unavailable')
    }
  })

  it('网络层 reject（不是 4xx/5xx）也归一化为 ApiError', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('ECONNREFUSED'))
    await expect(http.get('/projects')).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: 'ECONNREFUSED',
    })
  })

  it('超时触发 AbortSignal 取消 fetch', async () => {
    let capturedSignal: AbortSignal | undefined
    // 关键：真实的 fetch 会在 signal abort 时 reject 一个 AbortError，
    // 测试桩必须模拟这个行为，否则测不出代码是否真的把 signal 传下去了
    vi.mocked(fetch).mockImplementation((_u, init) => {
      const sig = ((init as RequestInit).signal ?? undefined) as AbortSignal
      capturedSignal = sig
      return new Promise<Response>((_res, rej) => {
        sig.addEventListener('abort', () =>
          rej(new DOMException('Aborted', 'AbortError')),
        )
      })
    })

    const p = http.get('/slow', { timeoutMs: 5000 })
    const assertion = expect(p).rejects.toMatchObject({ name: 'AbortError' })
    await vi.advanceTimersByTimeAsync(5000)
    await assertion
    expect(capturedSignal?.aborted).toBe(true)
  })

  it('上层 signal abort 会取消下游 fetch（页面卸载不泄漏请求）', async () => {
    const outer = new AbortController()
    vi.mocked(fetch).mockImplementation((_u, init) => {
      const sig = (init as RequestInit).signal as AbortSignal
      return new Promise<Response>((_res, rej) => {
        sig.addEventListener('abort', () => rej(new DOMException('Aborted', 'AbortError')))
      })
    })

    const p = http.get('/builds/1/logs', { signal: outer.signal })
    const assertion = expect(p).rejects.toMatchObject({ name: 'AbortError' })
    outer.abort()
    await assertion
  })

  it('PATCH 与 DELETE 也走同一套归一化', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { ok: true }))
    await http.patch('/projects/1', { name: 'x' })
    await http.del('/projects/1')
    expect(vi.mocked(fetch).mock.calls.map((c) => (c[1] as RequestInit).method)).toEqual(['PATCH', 'DELETE'])
  })

  it('传 body 但没有 JSON 序列化时不会破坏请求', async () => {
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, {}))
    // body 为 undefined：不该出现 Content-Type
    await http.post('/builds/1/rollback')
    const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit]
    expect(init.headers).toBeUndefined()
    expect(init.body).toBeUndefined()
  })

  it('非 Error 抛出物也能归一化成可读消息', async () => {
    vi.mocked(fetch).mockRejectedValue('something_went_wrong')
    await expect(http.get('/projects')).rejects.toMatchObject({ name: 'ApiError', message: '网络错误' })
  })

  /**
   * 监听器泄漏：request() 会在上层 signal 上挂一个 abort 转发监听。
   * 如果请求正常结束（signal 从未 abort），那个监听必须被摘掉 ——
   * 否则复用同一个 signal 发 N 个请求就会留下 N 个永不触发的监听。
   */
  it('请求结束后摘掉挂在信号上的 abort 监听，不累积', async () => {
    const outer = new AbortController()
    vi.mocked(fetch).mockResolvedValue(jsonResponse(200, { ok: true }))
    const removed = vi.fn()
    const spy = vi.spyOn(outer.signal, 'removeEventListener').mockImplementation((type, fn, opt) => {
      if (type === 'abort') removed()
      return EventTarget.prototype.removeEventListener.call(outer.signal, type, fn, opt)
    })
    await http.get('/projects', { signal: outer.signal })
    expect(removed).toHaveBeenCalledTimes(1)
    spy.mockRestore()
  })

  it('请求失败时同样摘掉监听', async () => {
    const outer = new AbortController()
    const removed = vi.fn()
    const spy = vi.spyOn(outer.signal, 'removeEventListener').mockImplementation((type, fn, opt) => {
      if (type === 'abort') removed()
      return EventTarget.prototype.removeEventListener.call(outer.signal, type, fn, opt)
    })

    vi.mocked(fetch).mockRejectedValue(new Error('boom'))
    await expect(http.get('/projects', { signal: outer.signal })).rejects.toThrow()
    expect(removed).toHaveBeenCalledTimes(1)
    spy.mockRestore()
  })
})
