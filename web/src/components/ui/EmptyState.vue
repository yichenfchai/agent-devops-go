<script setup lang="ts">
import Icon from '@/components/Icon.vue'
import type { IconName } from '@/components/icons'

withDefaults(defineProps<{
  icon?: IconName
  title: string
  detail?: string
  tone?: 'neutral' | 'danger' | 'warning'
}>(), { icon: 'inbox', tone: 'neutral' })

const TONE = {
  neutral: 'text-muted bg-overlay',
  danger:  'text-danger bg-danger/15',
  warning: 'text-warning bg-warning/15',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center text-center gap-3 py-10 px-4">
    <div class="w-11 h-11 rounded-card grid place-items-center" :class="TONE[tone]">
      <Icon :name="icon" :size="22" />
    </div>
    <div>
      <p class="text-[13.5px] font-medium text-ink">{{ title }}</p>
      <p v-if="detail" class="text-[12px] text-muted mt-1">{{ detail }}</p>
    </div>
    <slot />
  </div>
</template>
