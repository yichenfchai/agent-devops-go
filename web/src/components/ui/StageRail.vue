<script setup lang="ts">
import Icon from '@/components/Icon.vue'
import type { Stage } from '@/types'

defineProps<{ stages: Stage[] }>()

const fmt = (ms: number | null) => (ms === null ? '—' : `${(ms / 1000).toFixed(1)}s`)
</script>

<template>
  <ol class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
    <li
      v-for="s in stages" :key="s.index"
      class="panel p-2 flex flex-col gap-1 min-w-0"
      :class="s.status === 'failed' ? 'border-danger/50 bg-danger/5' : ''"
    >
      <div class="flex items-center gap-1.5">
        <span class="font-mono text-2xs text-dim">{{ String(s.index).padStart(2, '0') }}</span>
        <Icon
          v-if="s.status === 'passed'" name="check" :size="11" class="text-success ml-auto"
        />
        <Icon v-else-if="s.status === 'failed'" name="x" :size="11" class="text-danger ml-auto" />
        <Icon v-else-if="s.status === 'running'" name="spinner" :size="11" class="text-primary ml-auto" spin />
        <Icon v-else name="clock" :size="11" class="text-dim ml-auto" />
      </div>
      <div class="text-[11.5px] leading-tight truncate" :title="s.name">{{ s.name }}</div>
      <div class="font-mono text-2xs" :class="s.status === 'failed' ? 'text-danger' : 'text-dim'">
        {{ s.status === 'skipped' ? '已跳过' : fmt(s.durationMs) }}
      </div>
    </li>
  </ol>
</template>
