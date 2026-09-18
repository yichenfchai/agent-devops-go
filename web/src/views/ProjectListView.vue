<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Icon from '@/components/Icon.vue'
import type { Project } from '@/types'

const router = useRouter()
const { data: projects, loading, error, reload } = useAsync<Project[]>(() => api.listProjects())
const { data: runner } = useAsync(() => api.getRunner())

const triggering = ref<number | null>(null)

async function trigger(p: Project) {
  triggering.value = p.id
  try {
    const { number } = await api.triggerBuild(p.id)
    await router.push(`/builds/${number}`)
  } finally {
    triggering.value = null
  }
}

const fmtDuration = (ms: number) => (ms >= 1000 ? `${(ms / 1000).toFixed(0)}s` : `${ms}ms`)
</script>

<template>
  <div class="max-w-[1200px]">
    <PageHeader title="项目" :count="projects ? `共 ${projects.length} 个项目` : undefined">
      <template #actions>
        <RouterLink to="/projects/new" class="btn-primary">
          <Icon name="plus" :size="13" />新建项目
        </RouterLink>
      </template>
    </PageHeader>

    <SkeletonRows v-if="loading" :rows="4" height="118px" />

    <EmptyState
      v-else-if="error" icon="cloudOff" tone="danger"
      title="无法连接到构建守护进程" :detail="error"
    >
      <div class="flex items-center gap-2 text-2xs font-mono text-muted">
        <Icon name="terminal" :size="12" />
        <code>systemctl status devopsd</code>
      </div>
      <button class="btn-outline mt-1" @click="reload">
        <Icon name="refresh" :size="13" />重试连接
      </button>
    </EmptyState>

    <EmptyState
      v-else-if="!projects?.length" icon="inbox"
      title="还没有项目" detail="连接一个 GitHub 仓库，push 代码后自动构建部署"
    >
      <RouterLink to="/projects/new" class="btn-primary mt-1">
        <Icon name="plus" :size="13" />新建项目
      </RouterLink>
    </EmptyState>

    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <article
          v-for="p in projects" :key="p.id"
          class="panel p-3.5 flex flex-col gap-2.5 row-hover hover:border-primary/70"
        >
          <div class="flex items-center gap-2">
            <h2 class="text-[14px] font-semibold truncate">{{ p.name }}</h2>
            <div class="flex-1" />
            <StatusBadge :state="p.lastBuild?.state ?? 'idle'" />
          </div>

          <p class="font-mono text-2xs text-muted truncate">{{ p.repoFullName }}</p>

          <div class="flex flex-wrap items-center gap-1.5">
            <span class="chip bg-overlay border border-edge text-muted">
              类型: {{ p.detectedType ?? '未识别' }}
            </span>
            <span
              class="chip border"
              :class="p.deployHostId
                ? 'bg-overlay border-edge text-muted'
                : 'bg-warning/15 border-warning/35 text-warning'"
            >
              目标: {{ p.deployHostId ? 'prod-vps-01' : '未配置部署目标' }}
            </span>
            <span class="chip bg-overlay border border-edge text-muted">
              <Icon name="branch" :size="10" />{{ p.defaultBranch }}
            </span>
          </div>

          <div class="flex items-center gap-2 text-2xs text-dim font-mono min-h-[16px]">
            <template v-if="p.lastBuild">
              <Icon
                :name="p.lastBuild.state === 'failed' ? 'x' : 'check'"
                :size="11"
                :class="p.lastBuild.state === 'failed' ? 'text-danger' : 'text-success'"
              />
              <span>上次构建 #{{ p.lastBuild.number }} · {{ p.lastBuild.finishedAt }} ·
                {{ fmtDuration(p.lastBuild.durationMs) }}</span>
            </template>
            <template v-else>
              <Icon name="clock" :size="11" />
              <span>暂无部署记录 · 分支 {{ p.defaultBranch }}</span>
            </template>
          </div>

          <div class="flex items-center gap-2 pt-1">
            <RouterLink :to="`/projects/${p.id}/builds`" class="btn-outline">查看</RouterLink>
            <button class="btn-ghost" :disabled="triggering === p.id" @click="trigger(p)">
              <Icon name="play" :size="12" :spin="triggering === p.id" />运行流水线
            </button>
            <RouterLink v-if="!p.deployHostId" :to="`/projects/${p.id}/settings`" class="btn-ghost ml-auto">
              配置部署
            </RouterLink>
          </div>
        </article>
      </div>

      <!-- 构建机状态 —— 单机环境，只有一台 -->
      <section v-if="runner" class="panel mt-4 p-3.5 flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <Icon name="server" :size="15" class="text-muted" />
          <span class="text-[13px] font-medium">构建机状态</span>
        </div>
        <span class="font-mono text-2xs text-muted">{{ runner.name }} ({{ runner.os }} · {{ runner.version }})</span>
        <div class="flex-1" />
        <span class="chip border bg-success/15 border-success/35 text-[#64c284]">
          <span class="w-1.5 h-1.5 rounded-full bg-success" />就绪（空闲）
        </span>
        <span class="font-mono text-2xs text-dim">排队中: {{ runner.queued }}</span>
      </section>
    </template>
  </div>
</template>
