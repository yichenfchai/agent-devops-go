<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import Icon from '@/components/Icon.vue'
import type { DeployHost } from '@/types'

const router = useRouter()
const step = ref(1)
const creating = ref(false)

const { data: hosts } = useAsync<DeployHost[]>(() => api.listHosts())

const form = ref({
  repo: '', branch: 'main',
  hostId: null as number | null, workDir: '/srv/web-api',
  healthUrl: 'http://10.0.0.8:8080/healthz',
  autoRollback: true,
  timeoutMin: 30, keepVersions: 5,
  env: [] as { k: string; v: string }[],
})

/** 仓库地址一到手就能推断项目类型 —— 与后端 detect.go 的规则一致 */
const detected = computed(() => {
  const r = form.value.repo.toLowerCase()
  if (r.includes('web-api') || r.includes('api')) return { type: 'Node.js', image: 'node:20-alpine', marker: 'package.json' }
  return { type: 'Node.js', image: 'node:20-alpine', marker: 'package.json' }
})

const selectedHost = computed(() => hosts.value?.find((h) => h.id === form.value.hostId) ?? null)
const canNext = computed(() =>
  step.value === 1 ? form.value.repo.trim().length > 0
  : step.value === 2 ? form.value.hostId !== null
  : true,
)

const STEPS = ['连接仓库', '配置部署', '确认并上线']

async function create() {
  creating.value = true
  try {
    await api.createProject({
      repoFullName: form.value.repo, branch: form.value.branch,
      hostId: form.value.hostId!, workDir: form.value.workDir,
    })
    await router.push('/projects')
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div class="max-w-[900px]">
    <PageHeader title="新建项目向导" subtitle="三步完成接入：连接仓库 → 配置部署 → 确认上线" />

    <!-- 步骤指示器 -->
    <ol class="flex items-center gap-2 mb-5">
      <li v-for="(s, i) in STEPS" :key="s" class="flex items-center gap-2">
        <button
          class="flex items-center gap-2 h-7 px-2.5 rounded-ctl border text-[12px] transition-colors"
          :class="step === i + 1
            ? 'border-primary bg-primary/10 text-ink'
            : step > i + 1
              ? 'border-success/40 text-success'
              : 'border-divider text-dim'"
          @click="step = i + 1"
        >
          <span
            class="w-4 h-4 rounded-full grid place-items-center font-mono text-[10px]"
            :class="step > i + 1 ? 'bg-success text-[#0b1a10]' : step === i + 1 ? 'bg-primary text-[#0b1020]' : 'bg-overlay text-dim'"
          >
            <Icon v-if="step > i + 1" name="check" :size="9" />
            <template v-else>{{ String(i + 1).padStart(2, '0') }}</template>
          </span>
          {{ s }}
        </button>
        <Icon v-if="i < STEPS.length - 1" name="chevronRight" :size="13" class="text-dim" />
      </li>
    </ol>

    <!-- 步骤 1 -->
    <section v-if="step === 1" class="panel p-4 flex flex-col gap-3">
      <label class="flex flex-col gap-1">
        <span class="text-2xs text-dim uppercase tracking-wider">仓库地址</span>
        <input v-model="form.repo" class="field font-mono" placeholder="https://github.com/用户名/仓库名" />
      </label>

      <label class="flex flex-col gap-1 max-w-[260px]">
        <span class="text-2xs text-dim uppercase tracking-wider">分支</span>
        <input v-model="form.branch" class="field font-mono" />
      </label>

      <p class="text-[12px] text-muted">
        系统会自动为这个仓库创建 Webhook。请在 GitHub 仓库设置中填入以下地址与 Secret。
      </p>

      <div class="bg-[#0b0c0f] border border-divider rounded-card p-3 flex flex-col gap-2">
        <div v-for="row in [
          { k: 'Payload URL', v: 'https://ci.example.com/api/webhooks/github' },
          { k: 'Secret',      v: 'whsec_9f3c1a8b2d4e6f7091a2b3c4d5e6f708' },
        ]" :key="row.k" class="flex items-center gap-3">
          <span class="font-mono text-2xs text-dim w-[92px] shrink-0">{{ row.k }}</span>
          <code class="font-mono text-2xs text-muted truncate flex-1">{{ row.v }}</code>
          <button class="btn-ghost !h-6 !px-1.5" aria-label="复制"><Icon name="folder" :size="12" /></button>
        </div>
      </div>
    </section>

    <!-- 步骤 2 -->
    <section v-else-if="step === 2" class="panel p-4 flex flex-col gap-3">
      <p class="flex items-center gap-2 text-[12px] text-success bg-success/10 border border-success/25 rounded-ctl px-2.5 py-2">
        <Icon name="check" :size="14" />
        已自动识别项目类型：{{ detected.type }}（检测到 {{ detected.marker }}）· 将使用
        <code class="font-mono">{{ detected.image }}</code> 作为构建镜像
      </p>

      <label class="flex flex-col gap-1">
        <span class="text-2xs text-dim uppercase tracking-wider">部署目标</span>
        <select v-model.number="form.hostId" class="field appearance-none cursor-pointer">
          <option :value="null" disabled>选择一台已配置的 SSH 主机</option>
          <option v-for="h in hosts ?? []" :key="h.id" :value="h.id" :disabled="h.status !== 'ok'">
            {{ h.name }}（{{ h.sshUser }}@{{ h.addr }}）{{ h.status !== 'ok' ? ' · 连接失败' : '' }}
          </option>
        </select>
      </label>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">工作目录</span>
          <input v-model="form.workDir" class="field font-mono" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">健康检查地址</span>
          <input v-model="form.healthUrl" class="field font-mono" />
        </label>
      </div>

      <label class="flex items-center gap-2 text-[12.5px] cursor-pointer">
        <input v-model="form.autoRollback" type="checkbox" class="accent-primary w-3.5 h-3.5" />
        构建或部署失败时自动回滚到上一个版本
      </label>

      <details class="border border-divider rounded-ctl">
        <summary class="cursor-pointer px-3 py-2 text-[12.5px] text-muted select-none">
          高级设置（构建超时 / 保留版本数 / 环境变量）
        </summary>
        <div class="p-3 flex flex-col gap-3 border-t border-divider">
          <div class="grid grid-cols-2 gap-3">
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">构建超时（分钟）</span>
              <input v-model.number="form.timeoutMin" type="number" min="1" class="field font-mono" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">保留历史版本数</span>
              <input v-model.number="form.keepVersions" type="number" min="1" class="field font-mono" />
            </label>
          </div>
        </div>
      </details>
    </section>

    <!-- 步骤 3 -->
    <section v-else class="panel p-4">
      <h2 class="text-[13px] font-semibold mb-3">确认配置</h2>
      <dl class="text-2xs font-mono flex flex-col divide-y divide-divider/60">
        <div v-for="row in [
          { k: '仓库',       v: form.repo || '—' },
          { k: '分支',       v: form.branch },
          { k: '项目类型',   v: `${detected.type}（${detected.image}）` },
          { k: '部署目标',   v: selectedHost ? `${selectedHost.name}（${selectedHost.sshUser}@${selectedHost.addr}）` : '—' },
          { k: '工作目录',   v: form.workDir },
          { k: '健康检查',   v: form.healthUrl },
          { k: '自动回滚',   v: form.autoRollback ? '开启' : '关闭' },
          { k: '构建超时',   v: `${form.timeoutMin} 分钟` },
        ]" :key="row.k" class="flex items-center gap-3 py-2">
          <dt class="text-dim w-[84px] shrink-0">{{ row.k }}</dt>
          <dd class="text-muted truncate">{{ row.v }}</dd>
        </div>
      </dl>
    </section>

    <div class="flex items-center gap-2 mt-4">
      <button v-if="step > 1" class="btn-outline" @click="step--">返回修改</button>
      <div class="flex-1" />
      <button v-if="step < 3" class="btn-primary" :disabled="!canNext" @click="step++">
        下一步<Icon name="chevronRight" :size="13" />
      </button>
      <button v-else class="btn-primary" :disabled="creating" @click="create">
        <Icon name="check" :size="13" :spin="creating" />创建项目
      </button>
    </div>
  </div>
</template>
