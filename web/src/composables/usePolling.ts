/**
 * 轮询。用于「构建运行中」这种需要持续刷新的场景，
 * 页面切走时自动停，回来再启 —— 不占后台资源。
 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue'

export function usePolling(fn: () => void | Promise<void>, intervalMs = 3000) {
  const active = ref(true)
  let timer: number | null = null

  async function tick() {
    if (!active.value) return
    try { await fn() } finally {
      if (active.value) timer = window.setTimeout(tick, intervalMs)
    }
  }

  onMounted(() => { timer = window.setTimeout(tick, intervalMs) })
  onUnmounted(() => { active.value = false; if (timer !== null) clearTimeout(timer) })

  return {
    pause: () => { active.value = false; if (timer !== null) clearTimeout(timer) },
    resume: () => { if (!active.value) { active.value = true; void tick() } },
    active: active as Ref<boolean>,
  }
}
