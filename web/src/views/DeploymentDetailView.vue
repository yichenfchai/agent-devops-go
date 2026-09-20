<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import RollbackDialog from '@/components/RollbackDialog.vue'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const number = computed(() => Number(route.params.number))
const { data: dep, loading } = useAsync(() => api.getDeployment(number.value), number)
const rollback = ref(false)

const fmt = (ms: number | null) => (ms === null ? '—' : ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`)
</script>

<template>
  <div class="max-w-[1200px]">
    <PageHeader :title="`部署 #${number}`">
      <template #actions>
        <button class="btn-outline"><Icon name="refresh" :size="13" />重新部署</button>
      </template>
    </PageHeader>

    <SkeletonRows v-if="loading" :rows="3" height="80px" />

    <template v-else-if="dep">
      <!-- 摘要条 -->
      <div class="panel p-3.5 mb-4 flex flex-wrap items-center gap-4">
        <StatusBadge :state="dep.state" />
        <span class="chip border bg-primary/15 border-primary/35 text-primary">PRODUCTION</span>
        <div class="flex-1" />
        <span class="font-mono text-2xs text-muted">镜像: {{ dep.imageTag }}</span>
        <span class="text-dim">·</span>
        <span class="font-mono text-2xs text-muted">目标主机: {{ dep.hostAddr }}</span>
        <span class="text-dim">·</span>
        <span class="font-mono text-2xs text-muted">开始: {{ dep.startedAt }}</span>
        <span class="text-dim">·</span>
        <span class="font-mono text-2xs text-muted">耗时 {{ fmt(dep.durationMs) }}</span>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-4 items-start">
        <!-- 部署步骤时间线 -->
        <section>
          <h2 class="text-2xs uppercase tracking-wider text-dim mb-2">部署步骤</h2>
          <ol class="relative pl-4">
            <span class="absolute left-[5px] top-2 bottom-2 w-px bg-divider" aria-hidden="true" />
            <li v-for="s in dep.steps" :key="s.index" class="relative mb-2.5">
              <span class="absolute -left-4 top-2.5 w-2.5 h-2.5 rounded-full bg-success" aria-hidden="true" />
              <div class="panel px-3 py-2">
                <div class="flex items-center gap-2">
                  <span class="font-mono text-2xs text-dim">{{ String(s.index).padStart(2, '0') }}</span>
                  <span class="text-[12.5px] font-medium">{{ s.name }}</span>
                  <div class="flex-1" />
                  <Icon name="check" :size="12" class="text-success" />
                  <span class="font-mono text-2xs text-muted">{{ fmt(s.durationMs) }}</span>
                </div>
                <code class="block font-mono text-2xs text-dim mt-1">{{ s.command }}</code>
              </div>
            </li>
          </ol>
        </section>

        <!-- 右侧：部署信息 + 版本历史 -->
        <div class="flex flex-col gap-3">
          <section class="panel p-3.5">
            <h2 class="text-2xs uppercase tracking-wider text-dim mb-2">部署信息</h2>
            <dl class="text-2xs font-mono flex flex-col gap-1.5 text-muted">
              <div class="flex justify-between"><dt class="text-dim">目标主机</dt><dd>{{ dep.hostAddr }}</dd></div>
              <div class="flex justify-between"><dt class="text-dim">工作目录</dt><dd>{{ dep.workDir }}</dd></div>
              <div class="flex justify-between"><dt class="text-dim">compose 文件</dt><dd>docker-compose.yml</dd></div>
              <div class="flex justify-between"><dt class="text-dim">健康检查</dt><dd>已配置 · 重试 5 次</dd></div>
              <div class="flex justify-between"><dt class="text-dim">保留版本</dt><dd>5 个</dd></div>
            </dl>
          </section>

          <section class="panel p-3.5">
            <h2 class="text-2xs uppercase tracking-wider text-dim mb-2">版本历史</h2>
            <ul class="flex flex-col divide-y divide-divider/60">
              <li v-for="v in dep.versions" :key="v.tag" class="flex items-center gap-2 py-2">
                <div class="min-w-0">
                  <div class="font-mono text-2xs truncate">{{ v.tag }}</div>
                  <div class="text-2xs text-dim">{{ v.deployedAt }} · {{ v.state }}</div>
                </div>
                <div class="flex-1" />
                <button class="btn-ghost !h-6 !px-1.5 text-2xs" @click="rollback = true">回滚到此版本</button>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </template>

    <RollbackDialog
      v-if="rollback && dep"
      :build="{ id: 1, number: number, commitSha: 'a3f9c21', commitMessage: '修复部署脚本的环境变量读取', exitCode: 1 } as never"
      :previous="(() => {
        const v = dep?.versions.find((x) => !x.tag.includes('a3f9c21'))
        const tag = v?.tag ?? ''
        const [, sha = ''] = tag.split(':')
        return { sha, message: v?.state ?? '', time: v?.deployedAt ?? '' }
      })()"
      @close="rollback = false"
    />
  </div>
</template>
