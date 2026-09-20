<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import LogTerminal from '@/components/ui/LogTerminal.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const buildId = computed(() => Number(route.params.id))

const { data: build } = useAsync(() => api.getBuild(buildId.value), buildId)
const { data: logs } = useAsync(() => api.getLogs(buildId.value), buildId)
const { data: diag, loading: diagLoading, error: diagError, reload } =
  useAsync(() => api.getDiagnosis(buildId.value), buildId)

const helpful = ref(false)
</script>

<template>
  <div class="max-w-[1300px] flex flex-col gap-4">
    <!-- 失败条 -->
    <div class="panel border-danger/45 bg-danger/5 p-3.5 flex flex-wrap items-center gap-3">
      <span class="flex items-center gap-2 text-danger">
        <Icon name="x" :size="16" />
        <span class="text-[15px] font-semibold">构建 #{{ build?.number ?? buildId }} 失败 · 退出码 {{ build?.exitCode ?? 1 }}</span>
      </span>
      <span class="text-[12px] text-muted">执行阶段发生类型检查异常，作业管道已终止。</span>
      <div class="flex-1" />
      <template v-if="build">
        <span class="font-mono text-2xs text-muted">Commit {{ build.commitSha }}</span>
        <span class="text-dim">•</span>
        <span class="font-mono text-2xs text-muted">分支 {{ build.ref }}</span>
        <span class="text-dim">•</span>
        <span class="font-mono text-2xs text-muted">阶段 执行构建</span>
        <span class="text-dim">•</span>
        <span class="font-mono text-2xs text-muted">耗时 {{ ((build.durationMs ?? 0) / 1000).toFixed(2) }}s</span>
      </template>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[3fr_2fr] gap-4 items-start">
      <!-- 左：日志尾部 -->
      <section>
        <div class="flex items-center gap-2 mb-2">
          <span class="chip bg-overlay border border-edge text-dim">
            <Icon name="filter" :size="10" />正则过滤
          </span>
          <div class="flex-1" />
          <button class="btn-ghost">跳转至错误行</button>
          <button class="btn-ghost"><Icon name="download" :size="12" />下载原始日志</button>
          <button class="btn-outline"><Icon name="refresh" :size="12" />重新构建</button>
        </div>
        <LogTerminal
          :lines="logs ?? []" :auto-scroll="false" auto-height height="430px"
          empty-text="没有日志"
        />
        <p class="text-2xs text-dim mt-1.5 font-mono">
          容器最后 8KB 脱敏日志（ANSI 格式化输出） · BUFFER: 8192B
        </p>
      </section>

      <!-- 右：AI 诊断 -->
      <section class="panel border-ai/35 bg-ai/[0.04]">
        <header class="flex items-center gap-2 h-9 px-3 border-b border-ai/25">
          <Icon name="sparkle" :size="15" class="text-ai" />
          <h2 class="text-[13.5px] font-semibold text-ai">AI 智能诊断</h2>
          <div class="flex-1" />
          <span v-if="diag" class="font-mono text-2xs text-dim">
            分析耗时 {{ (diag.latencyMs / 1000).toFixed(1) }}s · 输入 {{ (diag.inputTokens / 1000).toFixed(1) }}K tokens
            · 日志已脱敏 {{ diag.redactions }} 处
          </span>
        </header>

        <div class="p-3.5 flex flex-col gap-4">
          <SkeletonRows v-if="diagLoading" :rows="2" height="60px" />

          <!-- 诊断失败 —— 不影响构建结果，只是这块没有内容 -->
          <div v-else-if="diagError" class="text-[12px] text-warning flex items-start gap-2">
            <Icon name="alert" :size="14" class="mt-0.5 shrink-0" />
            <div>
              <p>智能诊断未完成：{{ diagError }}</p>
              <p class="text-dim text-2xs mt-1">诊断失败不影响构建结果，构建已按正常流程结束。</p>
              <button class="btn-outline mt-2" @click="reload">
                <Icon name="refresh" :size="12" />重新分析
              </button>
            </div>
          </div>

          <template v-else-if="diag">
            <div>
              <h3 class="text-2xs uppercase tracking-wider text-dim mb-1.5">可能的原因</h3>
              <p class="text-[12.5px] leading-relaxed text-ink">{{ diag.rootCause }}</p>
            </div>

            <div>
              <h3 class="text-2xs uppercase tracking-wider text-dim mb-1.5">建议的修改</h3>
              <p class="text-[12.5px] leading-relaxed text-ink">{{ diag.suggestion }}</p>
            </div>

            <div class="border-t border-ai/20 pt-3 flex items-center gap-2">
              <span class="font-mono text-2xs text-dim">分析模型 {{ diag.model }}</span>
              <div class="flex-1" />
              <button class="btn-ghost" :class="helpful && 'text-success'" @click="helpful = !helpful">
                <Icon :name="helpful ? 'check' : 'info'" :size="12" />{{ helpful ? '已标记有用' : '有帮助' }}
              </button>
              <button class="btn-ghost"><Icon name="refresh" :size="12" />重新构建</button>
            </div>
          </template>
        </div>

        <p class="px-3.5 pb-3 text-2xs text-dim flex items-start gap-1.5">
          <Icon name="info" :size="11" class="mt-0.5 shrink-0" />
          诊断在独立协程中异步执行，不阻塞构建状态流转；诊断失败不影响构建结果。
        </p>
      </section>
    </div>
  </div>
</template>
