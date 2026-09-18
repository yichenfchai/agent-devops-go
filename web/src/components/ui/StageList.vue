<script setup lang="ts">
import Icon from '@/components/Icon.vue'
import type { Stage } from '@/types'

defineProps<{ stages: Stage[]; compact?: boolean }>()

const fmt = (ms: number | null) =>
  ms === null ? '—' : ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`

const ring: Record<Stage['status'], string> = {
  passed:  'text-success',
  failed:  'text-danger',
  running: 'text-primary',
  skipped: 'text-dim',
  pending: 'text-dim',
}
</script>

<template>
  <ol class="flex flex-col">
    <li
      v-for="s in stages" :key="s.index"
      class="flex items-center gap-3 rounded-ctl border px-3 transition-colors"
      :class="[
        compact ? 'h-9' : 'h-11',
        s.status === 'failed'  ? 'border-danger/40 bg-danger/5'
        : s.status === 'running' ? 'border-primary/45 bg-primary/5'
        : s.status === 'passed'  ? 'border-success/25'
        : 'border-divider',
      ]"
    >
      <span
        class="w-5 h-5 rounded-full grid place-items-center font-mono text-[10px] shrink-0"
        :class="[
          s.status === 'passed'  ? 'bg-success text-[#0b1a10]'
          : s.status === 'failed'  ? 'bg-danger text-[#2b0707]'
          : s.status === 'running' ? 'bg-primary text-[#0b1020]'
          : 'bg-overlay text-dim',
        ]"
      >{{ String(s.index).padStart(2, '0') }}</span>

      <span class="text-[12.5px] font-medium shrink-0">{{ s.name }}</span>

      <code class="font-mono text-2xs text-dim truncate flex-1 min-w-0">{{ s.command }}</code>

      <span v-if="s.status === 'running'" class="chip border border-primary/35 bg-primary/15 text-primary">
        <Icon name="spinner" :size="10" spin />
        {{ fmt(s.durationMs) === '—' ? '进行中' : fmt(s.durationMs) }}
      </span>
      <span v-else class="font-mono text-2xs shrink-0" :class="ring[s.status]">
        {{ s.status === 'skipped' ? '已跳过' : fmt(s.durationMs) }}
      </span>

      <Icon
        v-if="s.status === 'passed'" name="check" :size="13" class="text-success shrink-0"
      />
      <Icon v-else-if="s.status === 'failed'" name="x" :size="13" class="text-danger shrink-0" />
    </li>
  </ol>
</template>
