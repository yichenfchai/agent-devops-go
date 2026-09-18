<script setup lang="ts">
withDefaults(defineProps<{ rows?: number; height?: string }>(), { rows: 3, height: '44px' })
</script>

<template>
  <div class="flex flex-col gap-2" aria-busy="true" aria-label="加载中">
    <div
      v-for="i in rows" :key="i"
      class="animate-pulse rounded-card bg-overlay/70 border border-divider"
      :style="{ height }"
    />
  </div>
</template>
