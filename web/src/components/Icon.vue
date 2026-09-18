<script setup lang="ts">
import { computed } from 'vue'
import { PATHS, type IconName } from './icons'

const props = withDefaults(defineProps<{ name: IconName; size?: number | string; spin?: boolean }>(), {
  size: 16,
  spin: false,
})

const d = computed(() => PATHS[props.name])
const px = computed(() => (typeof props.size === 'number' ? `${props.size}px` : props.size))
</script>

<template>
  <svg
    :width="px" :height="px" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true" class="shrink-0" :class="spin && 'animate-spin'"
  >
    <path :d="d" />
  </svg>
</template>
