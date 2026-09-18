import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { effectScope } from 'vue'
import { MAX_LINES, useLogStream } from '@/composables/useLogStream'

/** 把 USE_MOCK 设为 false，强制走真实 SSE 分支，便于注入假的 EventSource */
vi.mock('@/api', () => ({
  USE_MOCK: false,
  api: { getLogs: vi.fn() },
}))

class FakeEventSource {
  static instances: FakeEventSource[] = []
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  closed = false
  constructor(readonly url: string) { FakeEventSource.instances.push(this) }
  close() { this.closed = true }
}

function makeLine(seq: number) {
  return { seq, ts: '00:00:00', text: `line ${seq}`, level: 'info' as const }
}

describe('useLogStream', () => {
  beforeEach(() => {
    FakeEventSource.instances = []
    vi.stubGlobal('EventSource', FakeEventSource)
  })
  afterEach(() => vi.unstubAllGlobals())

  function start() {
    const scope = effectScope()
    const st = scope.run(() => useLogStream(1091))!
    st.start()
    const es = FakeEventSource.instances.at(-1)!
    return { st, es, scope }
  }

  it('start 会按构建号订阅 SSE 端点', () => {
    const { es, scope } = start()
    expect(es.url).toBe('/api/builds/1091/logs/stream')
    scope.stop()
  })

  it('open 后 connected 为 true', () => {
    const { st, es, scope } = start()
    expect(st.connected.value).toBe(false)
    es.onopen?.()
    expect(st.connected.value).toBe(true)
    scope.stop()
  })

  it('逐条推入日志', () => {
    const { st, es, scope } = start()
    es.onopen?.()
    for (let i = 1; i <= 5; i++) es.onmessage?.({ data: JSON.stringify(makeLine(i)) })
    expect(st.lines.value.map((l) => l.seq)).toEqual([1, 2, 3, 4, 5])
    expect(st.dropped.value).toBe(0)
    scope.stop()
  })

  /**
   * 环形缓冲：前端也要防止无限增长 —— 和后端 LogPipe 的策略一致。
   * 超过上限时丢最旧的，并把丢弃条数记在 dropped 里。
   */
  it('超过上限时丢弃最旧的日志并计数', () => {
    const { st, es, scope } = start()
    es.onopen?.()

    const total = MAX_LINES + 5
    for (let i = 1; i <= total; i++) es.onmessage?.({ data: JSON.stringify(makeLine(i)) })

    expect(st.lines.value).toHaveLength(MAX_LINES)
    expect(st.dropped.value).toBe(5)
    expect(st.lines.value[0].seq).toBe(6)               // 前 5 条被丢掉
    expect(st.lines.value.at(-1)!.seq).toBe(total)      // 最新的始终保留
    scope.stop()
  })

  it('坏帧被忽略，不影响后续日志', () => {
    const { st, es, scope } = start()
    es.onopen?.()
    es.onmessage?.({ data: '{ 这不是合法 JSON' })
    es.onmessage?.({ data: JSON.stringify(makeLine(1)) })

    expect(st.lines.value).toHaveLength(1)
    expect(st.lines.value[0].seq).toBe(1)
    scope.stop()
  })

  it('onerror 把 connected 置回 false，但不丢失已收到的日志', () => {
    const { st, es, scope } = start()
    es.onopen?.()
    es.onmessage?.({ data: JSON.stringify(makeLine(1)) })
    es.onerror?.()

    expect(st.connected.value).toBe(false)
    expect(st.lines.value).toHaveLength(1)
    scope.stop()
  })

  it('stop 关闭连接；作用域销毁时自动 stop（不泄漏订阅）', () => {
    const { st, es, scope } = start()
    scope.stop()
    expect(es.closed).toBe(true)
    expect(st.connected.value).toBe(false)
  })

  it('重复 start 不会叠加多个连接', () => {
    const { st, es, scope } = start()
    st.start()
    expect(FakeEventSource.instances).toHaveLength(2)
    expect(es.closed).toBe(true)      // 旧连接已被关掉
    scope.stop()
  })
})
