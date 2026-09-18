<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Icon from '@/components/Icon.vue'
import type { IconName } from '@/components/icons'

/** 固定 5 项，与设计稿一致，不多不少 */
const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: '/projects',            label: '项目列表', icon: 'grid' },
  { to: '/projects/1/builds',   label: '构建历史', icon: 'history' },
  { to: '/hosts',               label: '部署目标', icon: 'server' },
  { to: '/projects/1/secrets',  label: '密钥管理', icon: 'key' },
  { to: '/projects/1/settings', label: '设置',     icon: 'sliders' },
]

const route = useRoute()
const current = computed(() => {
  const p = route.path
  // 构建详情归到「构建历史」下，避免这些页面没有高亮项
  if (p.startsWith('/builds')) return '/projects/1/builds'
  // 取最长匹配，而不是第一个命中 —— 否则 /projects/1/secrets
  // 会先被 '/projects' 吃掉，高亮成「项目列表」
  let best = ''
  for (const item of NAV) {
    if ((p === item.to || p.startsWith(item.to + '/')) && item.to.length > best.length) {
      best = item.to
    }
  }
  return best
})
</script>

<template>
  <nav class="w-[200px] shrink-0 border-r border-divider bg-canvas py-2" aria-label="主导航">
    <RouterLink
      v-for="item in NAV" :key="item.to" :to="item.to"
      class="flex items-center gap-2 h-8 px-3 text-[12.5px] border-l-2 transition-colors"
      :class="current === item.to
        ? 'border-l-primary bg-primary/10 text-ink'
        : 'border-l-transparent text-muted hover:bg-hover hover:text-ink'"
    >
      <Icon :name="item.icon" :size="15" />
      <span>{{ item.label }}</span>
    </RouterLink>
  </nav>
</template>
