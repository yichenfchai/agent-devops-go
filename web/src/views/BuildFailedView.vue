<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import StageRail from '@/components/ui/StageRail.vue'
import LogTerminal from '@/components/ui/LogTerminal.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const buildId = computed(() => Number(route.params.id))

const { data: build, loading } = useAsync(() => api.getBuild(buildId.value), buildId)
const { data: stages } = useAsync(() => api.getStages(buildId.value), buildId)
const { data: logs } = useAsync(() => api.getLogs(buildId.value), buildId)

const fmt = (ms: number | null) => (ms === null ? '—' : `${(ms / 1000).toFixed(1)}s`)
</script>

<template>
  <div class="max-w-[1300px] flex flex-col gap-4">
    <!-- 失败条 -->
    <div class="panel border-danger/45 bg-danger/5 p-3.5 flex flex-wrap items-center gap-4">
      <span class="flex items-center gap-2 text-danger">
        <Icon name="x" :size="16" />
        <span class="text-[15px] font-semibold">构建 #{{ build?.number ?? buildId }} 失败</span>
      </span>
      <span class="chip border bg-danger/15 border-danger/35 text-[#e55353]">
        exit code {{ build?.exitCode ?? 1 }}
      </span>
      <div class="flex-1" />
      <template v-if="build">
        <span class="font-mono text-2xs text-muted">Commit {{ build.commitSha }}</span>
        <span class="text-dim">·</span>
        <span class="font-mono text-2xs text-muted">分支 {{ build.ref }}</span>
        <span class="text-dim">·</span>
        <span class="font-mono text-2xs text-muted">耗时 {{ fmt(build.durationMs) }}</span>
      </template>
    </div>

    <SkeletonRows v-if="loading" :rows="2" height="80px" />

    <template v-else>
      <!-- 六阶段横排 -->
      <section>
        <h2 class="text-2xs uppercase tracking-wider text-dim mb-2">执行阶段</h2>
        <StageRail v-if="stages" :stages="stages" />
      </section>

      <!-- 日志 -->
      <section>
        <div class="flex items-center gap-2 mb-2">
          <Icon name="terminal" :size="14" class="text-muted" />
          <h2 class="text-[13px] font-semibold">容器最后 8KB 脱敏日志</h2>
          <span class="chip bg-overlay border border-edge text-dim">
            LINES: {{ logs?.length ?? 0 }}
          </span>
          <div class="flex-1" />
          <div class="flex items-center gap-1.5">
            <label class="relative">
              <Icon name="search" :size="12" class="absolute left-2 top-1/2 -translate-y-1/2 text-dim" />
              <input class="field w-[180px] pl-6 font-mono text-2xs" placeholder="正则过滤" />
            </label>
            <button class="btn-ghost">跳转至错误行</button>
            <button class="btn-ghost">
              <Icon name="download" :size="12" />下载原始日志
            </button>
          </div>
        </div>

        <LogTerminal
          :lines="logs ?? []" :auto-scroll="false" auto-height height="460px"
          empty-text="该构建没有日志输出"
        />

        <div class="flex items-center gap-4 mt-2 font-mono text-2xs text-dim">
          <span>Docker 运行时隔离环境 · 基础镜像 node:20-alpine</span>
          <span>exit: {{ build?.exitCode ?? 1 }} (ELIFECYCLE)</span>
          <div class="flex-1" />
          <RouterLink :to="`/builds/${buildId}/diagnosis`" class="btn-ghost text-ai">
            <Icon name="sparkle" :size="12" />查看 AI 诊断
          </RouterLink>
        </div>
      </section>
    </template>
  </div>
</template>
