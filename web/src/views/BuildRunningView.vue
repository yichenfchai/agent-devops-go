<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import { useLogStream } from '@/composables/useLogStream'
import { usePolling } from '@/composables/usePolling'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import StageList from '@/components/ui/StageList.vue'
import LogTerminal from '@/components/ui/LogTerminal.vue'
import Icon from '@/components/Icon.vue'
import type { Build } from '@/types'

const route = useRoute()
const number = computed(() => Number(route.params.number))

const { data: build } = useAsync<Build>(() => api.getBuild(number.value), number)
const { data: stages, reload: reloadStages } = useAsync(() => api.getStages(number.value), number)

const elapsed = ref(52.1)
const live = ref(true)

// 实时日志：真实模式走 SSE，mock 模式逐行回放
const { lines, connected, start } = useLogStream(number.value)
onMounted(start)

// 运行中每 3 秒刷新阶段与耗时
const { pause } = usePolling(async () => {
  elapsed.value += 3
  await reloadStages()
}, 3000)

const done = computed(() => (stages.value ?? []).filter((s) => s.status === 'passed').length)
const total = computed(() => (stages.value ?? []).length)
const pipeline = 'npm ci → npm run build → docker build -t web-api:${SHA} → docker push'
</script>

<template>
  <div class="max-w-[1300px]">
    <!-- 运行中状态条 -->
    <div class="panel p-3.5 mb-4 flex flex-wrap items-center gap-4">
      <div class="flex items-center gap-2">
        <StatusBadge :state="build?.state ?? 'running'" />
        <span class="text-[15px] font-semibold">#{{ number }}</span>
      </div>
      <div class="flex flex-col">
        <span class="text-2xs text-dim uppercase tracking-wider">执行时长</span>
        <span class="font-mono text-[15px]">{{ elapsed.toFixed(1) }}s</span>
      </div>
      <div class="flex-1" />
      <span class="chip border bg-primary/15 border-primary/35 text-primary">
        <Icon name="spinner" :size="10" spin />LIVE STREAM
      </span>
      <span
        class="chip border"
        :class="connected ? 'bg-success/15 border-success/35 text-[#64c284]'
                          : 'bg-overlay border-edge text-dim'"
      >
        {{ connected ? '日志已连接' : '连接中…' }}
      </span>
      <button class="btn-ghost">原始配置</button>
      <button class="btn-danger" @click="pause(); live = false">
        <Icon name="stop" :size="12" />中止运行
      </button>
    </div>

    <!-- 元信息 -->
    <div class="flex flex-wrap items-center gap-4 mb-4 font-mono text-2xs text-muted">
      <span class="flex items-center gap-1.5"><Icon name="branch" :size="12" />分支: {{ build?.ref ?? 'main' }}</span>
      <span class="flex items-center gap-1.5"><Icon name="commit" :size="12" />Commit: {{ build?.commitSha }}</span>
      <span class="truncate">{{ build?.commitMessage }}</span>
      <span class="text-dim">{{ build?.commitAuthor }}</span>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[1fr_1fr] gap-4">
      <!-- 左：阶段 -->
      <section>
        <div class="flex items-center gap-2 mb-2">
          <Icon name="code" :size="14" class="text-muted" />
          <h2 class="text-[13px] font-semibold">流水线阶段</h2>
          <span class="text-2xs text-dim font-mono">{{ done }}/{{ total }} 已完成</span>
        </div>
        <StageList v-if="stages" :stages="stages" />

        <div class="panel mt-3 p-3">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-2xs uppercase tracking-wider text-dim">本次构建使用的 Pipeline 快照</span>
            <div class="flex-1" />
            <button class="btn-ghost !h-6 !px-1.5 text-2xs">覆盖配置</button>
          </div>
          <code class="block font-mono text-2xs text-muted break-all">{{ pipeline }}</code>
          <p class="text-2xs text-dim mt-1.5">
            检测到 package.json，自动识别为 Node.js 项目 · 使用 node:20-alpine（{{ build?.baseImage ?? 'node:20-alpine' }}）
          </p>
        </div>
      </section>

      <!-- 右：实时日志 -->
      <section>
        <div class="flex items-center gap-2 mb-2">
          <Icon name="terminal" :size="14" class="text-muted" />
          <h2 class="text-[13px] font-semibold">实时日志</h2>
          <div class="flex-1" />
          <button class="btn-ghost !h-6 !px-1.5" aria-label="下载原始日志">
            <Icon name="download" :size="12" />
          </button>
        </div>
        <LogTerminal
          :lines="lines" :caret="connected" height="480px"
          empty-text="等待容器输出…"
        />
        <p v-if="lines.length" class="text-2xs text-dim mt-1.5 font-mono">
          LINES: {{ lines.length }} · BUFFER: 8192B（超出丢弃最旧的）
        </p>
      </section>
    </div>
  </div>
</template>
