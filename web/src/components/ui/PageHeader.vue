<script setup lang="ts">
defineProps<{ title: string; count?: string; subtitle?: string }>()
</script>

<template>
  <div class="flex items-start gap-3 mb-4">
    <div class="min-w-0">
      <div class="flex items-center gap-2">
        <h1 class="text-[16px] font-semibold tracking-tight">{{ title }}</h1>
        <span v-if="count" class="text-2xs text-dim font-mono">{{ count }}</span>
      </div>
      <p v-if="subtitle" class="text-[12px] text-muted mt-0.5">{{ subtitle }}</p>
    </div>
    <div class="flex-1" />
    <slot name="actions" />
  </div>
</template>
