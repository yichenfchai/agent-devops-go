/**
 * 构建日志流。
 *
 * 真实模式走 SSE（EventSource，浏览器自带断线重连），
 * mock 模式用一个定时器逐行回放，方便没有后端时演示 UI。
 *
 * 关键设计：慢消费者不阻塞生产者 —— 前端这里用固定长度环形缓冲，
 * 超过上限就丢最旧的，和后端 LogPipe 的策略一致。
 */
import { ref, shallowRef, onScopeDispose, type Ref } from 'vue'
import type { LogLine } from '@/types'
import { USE_MOCK } from '@/api'
import { api } from '@/api'

export interface LogStreamState {
  lines: Ref<LogLine[]>
  connected: Ref<boolean>
  dropped: Ref<number>
  start: () => void
  stop: () => void
}

export const MAX_LINES = 2000

export function useLogStream(buildNumber: number): LogStreamState {
  const lines = ref<LogLine[]>([]) as Ref<LogLine[]>
  const connected = ref(false)
  const dropped = ref(0)
  const es = shallowRef<EventSource | null>(null)
  const timers: number[] = []

  function push(line: LogLine) {
    lines.value.push(line)
    if (lines.value.length > MAX_LINES) {
      dropped.value += lines.value.length - MAX_LINES
      lines.value.splice(0, lines.value.length - MAX_LINES)
    }
  }

  function startMock() {
    api.getLogs(buildNumber)
      .then((all) => {
        connected.value = true
        all.forEach((line, i) => {
          const t = window.setTimeout(() => push(line), i * 90)
          timers.push(t)
        })
      })
      // 拉日志失败不能让 Promise 悬空 —— 与真实模式下 onerror 的行为保持一致
      .catch(() => { connected.value = false })
  }

  function start() {
    stop()
    if (USE_MOCK) { startMock(); return }

    const source = new EventSource(`/api/builds/${buildNumber}/logs/stream`)
    source.onopen = () => { connected.value = true }
    source.onmessage = (ev) => {
      try { push(JSON.parse(ev.data) as LogLine) } catch { /* 忽略坏帧 */ }
    }
    source.onerror = () => { connected.value = false }
    es.value = source
  }

  function stop() {
    es.value?.close()
    es.value = null
    connected.value = false
    timers.splice(0).forEach(clearTimeout)
  }

  onScopeDispose(stop)

  return { lines, connected, dropped, start, stop }
}
