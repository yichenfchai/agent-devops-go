/**
 * 轮询。用于「构建运行中」这种需要持续刷新的场景，
 * 页面切走时自动停，回来再启 —— 不占后台资源。
 *
 * 竞态说明（generation 修复）：
 * 旧实现里，tick() 挂在 await fn() 时若发生 pause()→resume()，
 * resume 会启动一条新轮询链，而旧 tick 的 finally 看到 active 又变回 true，
 * 也会续排 timer —— 两条链并行，请求频率翻倍。
 * 现在每条 tick 链持有自己的代数（generation），finally 里只有
 * 「自己仍是最新一代且 active」才续排；resume 使代数 +1，旧链自然作废。
 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue'

export function usePolling(fn: () => void | Promise<void>, intervalMs = 3000) {
  const active = ref(true)
  let timer: number | null = null
  let generation = 0 // 每次轮询链（重新）启动时 +1，用于让旧链的 finally 失效

  async function tick(gen: number) {
    if (!active.value || gen !== generation) return
    try {
      await fn()
    } finally {
      // 只有「仍然 active 且自己没被新链取代」才允许续排
      if (active.value && gen === generation) {
        timer = window.setTimeout(() => void tick(gen), intervalMs)
      }
    }
  }

  onMounted(() => {
    timer = window.setTimeout(() => void tick(generation), intervalMs)
  })
  onUnmounted(() => {
    active.value = false
    generation++ // 作废所有在飞的链
    if (timer !== null) clearTimeout(timer)
  })

  return {
    pause: () => {
      active.value = false
      generation++ // 在飞的旧 tick 回来后发现自己已过时，不再续排
      if (timer !== null) clearTimeout(timer)
    },
    resume: () => {
      if (!active.value) {
        active.value = true
        generation++ // 新链新代数；旧链即使还在 await 中也不会复活
        void tick(generation)
      }
    },
    active: active as Ref<boolean>,
  }
}
