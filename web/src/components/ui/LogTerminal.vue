<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { LogLine } from '@/types'

const props = withDefaults(defineProps<{
  lines: LogLine[]
  autoScroll?: boolean
  showLineNo?: boolean
  height?: string
  emptyText?: string
  caret?: boolean
  /** 高度自适应内容（最多不超过 height），用于日志行数少的场景 */
  autoHeight?: boolean
}>(), {
  autoScroll: true,
  showLineNo: true,
  height: '420px',
  emptyText: '等待日志输出…',
  caret: false,
  autoHeight: false,
})

const box = ref<HTMLElement | null>(null)

watch(
  () => props.lines.length,
  async () => {
    if (!props.autoScroll) return
    await nextTick()
    if (box.value) box.value.scrollTop = box.value.scrollHeight
  },
)

const tone: Record<LogLine['level'], string> = {
  info:  'text-[#9fb8da]',
  ok:    'text-[#7fd79e]',
  warn:  'text-warning',
  error: 'text-danger',
}
</script>

<template>
  <div
    ref="box"
    class="overflow-y-auto bg-[#0b0c0f] border border-divider rounded-card p-2"
    :style="autoHeight ? { maxHeight: height } : { height }"
    role="log"
    aria-live="polite"
  >
    <p v-if="!lines.length" class="text-dim text-[12px] p-2">{{ emptyText }}</p>

    <div
      v-for="l in lines" :key="l.seq"
      class="logline flex gap-3 px-1"
      :class="[tone[l.level], l.level === 'error' && 'bg-danger/10']"
    >
      <span v-if="showLineNo" class="text-dim select-none w-8 text-right shrink-0">{{ String(l.seq).padStart(3, '0') }}</span>
      <span class="text-dim shrink-0">[{{ l.ts }}]</span>
      <span class="flex-1 min-w-0">{{ l.text }}</span>
    </div>

    <div v-if="caret" class="logline px-1"><span class="caret" /></div>
  </div>
</template>
