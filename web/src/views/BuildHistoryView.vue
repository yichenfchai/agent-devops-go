<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import StatCard from '@/components/ui/StatCard.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import RollbackDialog from '@/components/RollbackDialog.vue'
import Icon from '@/components/Icon.vue'
import type { Build } from '@/types'

const { data: builds, loading, error, reload } = useAsync<Build[]>(() => api.listBuilds(1))
const { data: stats } = useAsync(() => api.getBuildStats())

const stateFilter = ref<string>('all')
const branchFilter = ref('main')
const rollbackTarget = ref<Build | null>(null)

const filtered = computed(() => {
  let list = builds.value ?? []
  if (stateFilter.value !== 'all') list = list.filter((b) => b.state === stateFilter.value)
  return list
})

const fmtMs = (ms: number | null) => {
  if (ms === null) return '—'
  return ms >= 60_000 ? `${Math.floor(ms / 60_000)}m ${Math.round((ms % 60_000) / 1000)}s` : `${(ms / 1000).toFixed(0)}s`
}

const TRIGGER_LABEL: Record<string, string> = {
  push: 'Git Hook (push)', pr: 'Pull Request', manual: '手动触发', rollback: '回滚',
}
</script>

<template>
  <div class="max-w-[1200px]">
    <PageHeader title="构建历史记录" subtitle="流水线执行日志与版本变更索引，当前追踪分支 main">
      <template #actions>
        <div class="flex items-center gap-2">
          <label class="relative">
            <Icon name="filter" :size="12" class="absolute left-2 top-1/2 -translate-y-1/2 text-dim" />
            <select v-model="stateFilter" class="field pl-6 pr-6 appearance-none cursor-pointer">
              <option value="all">按状态过滤</option>
              <option value="deployed">成功</option>
              <option value="failed">失败</option>
              <option value="rolled_back">已回滚</option>
              <option value="running">进行中</option>
            </select>
          </label>
          <select v-model="branchFilter" class="field appearance-none cursor-pointer pr-6">
            <option value="main">main</option>
            <option value="develop">develop</option>
          </select>
        </div>
      </template>
    </PageHeader>

    <!-- 统计卡 -->
    <div v-if="stats" class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
      <StatCard label="总构建数" :value="String(stats.total)" icon="chip" hint="+14% 环比" />
      <StatCard label="成功率" :value="`${stats.successRate}%`" icon="check" tone="success" hint="目标 ≥ 90%" />
      <StatCard label="平均耗时" :value="`${Math.round(stats.avgDurationMs / 1000)}s`" icon="clock" hint="-6s 加速" />
      <StatCard label="本月部署" :value="`${stats.monthlyDeploys} 次`" icon="rocket" tone="primary" />
    </div>

    <SkeletonRows v-if="loading" :rows="6" height="36px" />

    <EmptyState
      v-else-if="error" icon="cloudOff" tone="danger"
      title="无法连接到构建守护进程" :detail="error"
    >
      <button class="btn-outline" @click="reload"><Icon name="refresh" :size="13" />重试</button>
    </EmptyState>

    <EmptyState
      v-else-if="!filtered.length" icon="history"
      title="没有匹配的构建记录" detail="换个筛选条件试试"
    />

    <!-- 表格 -->
    <div v-else class="panel overflow-hidden">
      <table class="w-full text-[12.5px]">
        <thead>
          <tr class="text-2xs uppercase tracking-wider text-dim border-b border-divider">
            <th class="text-left font-medium px-3 h-8 w-[92px]">构建编号 / 提交</th>
            <th class="text-left font-medium px-3 h-8">提交信息</th>
            <th class="text-left font-medium px-3 h-8 w-[130px]">触发源</th>
            <th class="text-right font-medium px-3 h-8 w-[80px]">耗时</th>
            <th class="text-left font-medium px-3 h-8 w-[110px]">状态 / 操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="b in filtered" :key="b.id"
            class="border-b border-divider/60 row-hover"
            :class="b.state === 'running' && 'border-l-2 border-l-primary'"
          >
            <td class="px-3 h-9">
              <RouterLink
                :to="b.state === 'failed' ? `/builds/${b.number}/failed` : `/builds/${b.number}`"
                class="font-mono hover:text-primary"
              >#{{ b.number }}</RouterLink>
              <div class="font-mono text-2xs text-dim">{{ b.commitSha }}</div>
            </td>
            <td class="px-3 h-9 truncate max-w-[320px]" :title="b.commitMessage">{{ b.commitMessage }}</td>
            <td class="px-3 h-9 text-muted text-2xs font-mono">{{ TRIGGER_LABEL[b.trigger] ?? b.trigger }}</td>
            <td class="px-3 h-9 text-right font-mono text-muted">{{ fmtMs(b.durationMs) }}</td>
            <td class="px-3 h-9">
              <div class="flex items-center gap-2">
                <StatusBadge :state="b.state" />
                <button
                  v-if="b.state === 'deployed'"
                  class="btn-ghost !h-6 !px-1.5" title="回滚到此版本"
                  @click="rollbackTarget = b"
                >
                  <Icon name="undo" :size="12" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="flex items-center gap-3 px-3 h-9 text-2xs text-dim border-t border-divider">
        <span>共 {{ filtered.length }} 条</span>
        <div class="flex-1" />
        <button class="btn-ghost !h-6" disabled>上一页</button>
        <span class="font-mono">1 / 1</span>
        <button class="btn-ghost !h-6" disabled>下一页</button>
      </div>
    </div>

    <RollbackDialog
      v-if="rollbackTarget"
      :build="rollbackTarget"
      :previous="{ sha: '7b1e044', message: '优化数据库查询索引', time: '2 小时前' }"
      @close="rollbackTarget = null"
    />
  </div>
</template>
