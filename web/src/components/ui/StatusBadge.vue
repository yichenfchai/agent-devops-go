<script setup lang="ts">
import { computed } from 'vue'
import Icon from '@/components/Icon.vue'
import type { IconName } from '@/components/icons'
import type { BuildState } from '@/types'

const props = defineProps<{ state: BuildState | 'ok' | 'unreachable' | 'idle' | 'passed' | 'failed' | 'skipped' | 'running' }>()

interface Meta { label: string; cls: string; icon?: IconName; spin?: boolean; dot?: boolean }

const MAP: Record<string, Meta> = {
  // 构建 / 部署状态
  queued:        { label: '排队中',   cls: 'bg-warning/15 border-warning/35 text-warning', icon: 'clock' },
  running:       { label: '运行中',   cls: 'bg-primary/15 border-primary/35 text-primary', icon: 'spinner', spin: true },
  succeeded:     { label: '构建成功', cls: 'bg-success/15 border-success/35 text-[#64c284]', icon: 'check' },
  deploying:     { label: '部署中',   cls: 'bg-primary/15 border-primary/35 text-primary', icon: 'spinner', spin: true },
  deployed:      { label: '部署成功', cls: 'bg-success/15 border-success/35 text-[#64c284]', dot: true },
  failed:        { label: '失败',     cls: 'bg-danger/15 border-danger/35 text-[#e55353]',  icon: 'x' },
  deploy_failed: { label: '部署失败', cls: 'bg-danger/15 border-danger/35 text-[#e55353]',  icon: 'x' },
  rolled_back:   { label: '已回滚',   cls: 'bg-warning/15 border-warning/35 text-warning', icon: 'undo' },
  // 阶段 / 主机
  passed:        { label: '已通过',   cls: 'bg-success/15 border-success/35 text-[#64c284]', icon: 'check' },
  skipped:       { label: '已跳过',   cls: 'bg-overlay border-edge text-dim', icon: 'skip' },
  ok:            { label: '连接正常', cls: 'bg-success/15 border-success/35 text-[#64c284]', icon: 'check' },
  unreachable:   { label: '连接失败', cls: 'bg-danger/15 border-danger/35 text-[#e55353]',  icon: 'x' },
  idle:          { label: '未部署',   cls: 'bg-overlay border-edge text-muted' },
}

const m = computed<Meta>(() => MAP[props.state] ?? { label: props.state, cls: 'bg-overlay border-edge text-muted' })
</script>

<template>
  <span class="chip border" :class="m.cls">
    <span v-if="m.dot" class="w-1.5 h-1.5 rounded-full bg-current" />
    <Icon v-else-if="m.icon" :name="m.icon" :size="10" :spin="m.spin" />
    {{ m.label }}
  </span>
</template>
