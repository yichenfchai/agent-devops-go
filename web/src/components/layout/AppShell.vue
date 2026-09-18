<script setup lang="ts">
import AppTopbar from './AppTopbar.vue'
import AppSidebar from './AppSidebar.vue'
import AppStatusBar from './AppStatusBar.vue'
</script>

<template>
  <div class="h-full flex flex-col bg-canvas">
    <AppTopbar />
    <div class="flex-1 flex min-h-0">
      <AppSidebar />
      <main class="flex-1 min-w-0 overflow-y-auto p-4">
        <slot />
      </main>
    </div>
    <AppStatusBar />
  </div>
</template>
