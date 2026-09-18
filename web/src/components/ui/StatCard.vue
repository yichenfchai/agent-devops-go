<script setup lang="ts">
import Icon from '@/components/Icon.vue'
import type { IconName } from '@/components/icons'

withDefaults(defineProps<{
  label: string
  value: string
  icon?: IconName
  hint?: string
  tone?: 'default' | 'success' | 'danger' | 'primary' | 'warning'
}>(), { tone: 'default' })

const TONE: Record<string, string> = {
  default: 'text-ink',
  success: 'text-success',
  danger:  'text-danger',
  primary: 'text-primary',
  warning: 'text-warning',
}
</script>

<template>
  <div class="panel p-3 flex flex-col gap-1">
    <div class="flex items-center gap-1.5 text-2xs uppercase tracking-wider text-dim">
      <Icon v-if="icon" :name="icon" :size="12" />
      {{ label }}
    </div>
    <div class="font-mono text-[19px] font-semibold leading-tight" :class="TONE[tone]">{{ value }}</div>
    <div v-if="hint" class="text-2xs text-dim">{{ hint }}</div>
  </div>
</template>
