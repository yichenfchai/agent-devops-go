<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'

const route = useRoute()
/** 登录页是裸页，不套应用外壳 */
const bare = computed(() => route.meta.bare === true)
</script>

<template>
  <RouterView v-if="bare" />
  <AppShell v-else>
    <RouterView v-slot="{ Component }">
      <component :is="Component" />
    </RouterView>
  </AppShell>
</template>
