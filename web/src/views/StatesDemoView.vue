<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import Icon from '@/components/Icon.vue'

const SCENES = [
  { id: 1, title: '场景 1：项目列表为空', meta: 'HTTP 200 · 0 结果' },
  { id: 2, title: '场景 2：构建尚未开始', meta: '单机 Worker 独占调度' },
  { id: 3, title: '场景 3：请求守护进程失败', meta: 'ECONNREFUSED' },
  { id: 4, title: '场景 4：数据加载中', meta: '轮询中…' },
]

const retrying = ref(false)
</script>

<template>
  <div class="max-w-[1200px]">
    <PageHeader
      title="系统状态与反馈规范"
      subtitle="针对单机环境的高频瞬态交互与空值模式"
    >
      <template #actions>
        <span class="chip border bg-success/15 border-success/35 text-[#64c284]">
          <span class="w-1.5 h-1.5 rounded-full bg-success" />
          本地 UNIX 套接字: /run/devopsd.sock
        </span>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <!-- 场景 1 -->
      <section class="panel flex flex-col">
        <header class="flex items-center gap-2 h-8 px-3 border-b border-divider shrink-0">
          <span class="text-2xs text-muted">{{ SCENES[0].title }}</span>
          <div class="flex-1" />
          <span class="font-mono text-2xs text-dim">{{ SCENES[0].meta }}</span>
        </header>
        <div class="flex-1 grid place-items-center">
          <EmptyState icon="inbox" title="还没有项目" detail="连接一个 GitHub 仓库，push 代码后自动构建部署">
            <div class="flex gap-2 mt-1">
              <RouterLink to="/projects/new" class="btn-primary"><Icon name="plus" :size="13" />新建项目</RouterLink>
              <button class="btn-outline font-mono text-2xs">CLI 导入</button>
            </div>
          </EmptyState>
        </div>
      </section>

      <!-- 场景 2 -->
      <section class="panel flex flex-col">
        <header class="flex items-center gap-2 h-8 px-3 border-b border-divider shrink-0">
          <span class="text-2xs text-muted">{{ SCENES[1].title }}</span>
          <div class="flex-1" />
          <span class="font-mono text-2xs text-dim">{{ SCENES[1].meta }}</span>
        </header>
        <div class="flex-1 grid place-items-center">
          <EmptyState icon="hourglass" tone="warning" title="构建尚未开始" detail="任务已入队，等待可用 worker 释放执行槽位">
            <div class="flex flex-col items-center gap-1.5 mt-1">
              <StatusBadge state="queued" />
              <span class="font-mono text-2xs text-dim">
                排队中 · 序号 #1 · 预计等待 ~14s · 构建机 build-runner-01
              </span>
            </div>
          </EmptyState>
        </div>
      </section>

      <!-- 场景 3 -->
      <section class="panel flex flex-col">
        <header class="flex items-center gap-2 h-8 px-3 border-b border-divider shrink-0">
          <span class="text-2xs text-muted">{{ SCENES[2].title }}</span>
          <div class="flex-1" />
          <span class="font-mono text-2xs text-danger">{{ SCENES[2].meta }}</span>
        </header>
        <div class="flex-1 grid place-items-center">
          <EmptyState icon="cloudOff" tone="danger" title="无法连接到构建守护进程" detail="请确认 devopsd 服务正在运行">
            <code class="font-mono text-2xs text-muted border border-divider rounded-badge px-2 py-1">
              systemctl status devopsd
            </code>
            <div class="flex gap-2 mt-1">
              <button class="btn-outline" :disabled="retrying" @click="retrying = true">
                <Icon name="refresh" :size="13" :spin="retrying" />重试连接
              </button>
              <button class="btn-ghost">查看日志</button>
            </div>
          </EmptyState>
        </div>
      </section>

      <!-- 场景 4 -->
      <section class="panel flex flex-col">
        <header class="flex items-center gap-2 h-8 px-3 border-b border-divider shrink-0">
          <span class="text-2xs text-muted">{{ SCENES[3].title }}</span>
          <div class="flex-1" />
          <span class="flex items-center gap-1.5 font-mono text-2xs text-dim">
            <Icon name="spinner" :size="11" spin />轮询中…
          </span>
        </header>
        <div class="flex-1 p-4 flex flex-col gap-2.5">
          <SkeletonRows :rows="3" height="46px" />
          <p class="text-2xs text-dim text-center mt-1">获取本地执行器队列状态…</p>
        </div>
      </section>
    </div>

    <p class="mt-4 text-2xs text-dim font-mono">
      状态渲染策略：本地守护进程 IPC 断联时采用平滑重试退避（Backoff: 1s, 2s, 4s, 8s）
    </p>
  </div>
</template>
