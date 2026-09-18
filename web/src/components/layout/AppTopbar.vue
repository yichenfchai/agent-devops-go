<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import Icon from '@/components/Icon.vue'
import { api } from '@/api'

const route = useRoute()

/** 面包屑来自路由 meta —— 每个页面自动正确，
 *  根治了设计稿里「13 个页面面包屑都写死成 构建 #1091」的问题 */
const crumb = computed<string[]>(() => (route.meta.crumb as string[] | undefined) ?? [])

const search = ref('')
const busy = ref(false)

async function runPipeline() {
  busy.value = true
  try { await api.triggerBuild(1) } finally { busy.value = false }
}
</script>

<template>
  <header class="h-12 shrink-0 flex items-center gap-3 px-3 border-b border-divider bg-canvas">
    <RouterLink to="/projects" class="font-semibold text-[13.5px] tracking-tight hover:text-primary">
      GoPulse CI
    </RouterLink>

    <nav class="flex items-center gap-1.5 text-[12px] text-muted min-w-0" aria-label="面包屑">
      <template v-for="(c, i) in crumb" :key="i">
        <Icon v-if="i > 0" name="chevronRight" :size="12" class="text-dim" />
        <span :class="i === crumb.length - 1 ? 'text-ink' : ''" class="truncate">{{ c }}</span>
      </template>
    </nav>

    <div class="flex-1" />

    <label class="relative hidden md:block">
      <Icon name="search" :size="14" class="absolute left-2 top-1/2 -translate-y-1/2 text-dim" />
      <input
        v-model="search" type="search" placeholder="搜索项目、构建记录…"
        class="field w-[240px] pl-7" aria-label="搜索"
      />
      <kbd class="absolute right-1.5 top-1/2 -translate-y-1/2 font-mono text-2xs text-dim
                  border border-edge rounded-badge px-1">⌘K</kbd>
    </label>

    <button class="btn-primary" :disabled="busy" @click="runPipeline">
      <Icon name="play" :size="13" :spin="busy" />
      运行流水线
    </button>

    <div class="w-6 h-6 rounded-full bg-overlay border border-edge grid place-items-center text-dim" title="Alex Mercer">
      <Icon name="user" :size="13" />
    </div>
  </header>
</template>
