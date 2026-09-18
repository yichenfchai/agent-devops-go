<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import Icon from '@/components/Icon.vue'
import type { DeployHost } from '@/types'

const { data: hosts, loading, reload } = useAsync<DeployHost[]>(() => api.listHosts())
const drawer = ref(false)
const testing = ref<number | null>(null)
const testResult = ref<Record<number, string>>({})

async function test(h: DeployHost) {
  testing.value = h.id
  try {
    const r = await api.testHost(h.id)
    testResult.value = { ...testResult.value, [h.id]: r.detail }
  } finally {
    testing.value = null
  }
}

const form = ref({
  name: '', addr: '', user: 'deploy', key: '', fingerprint: '',
  workDir: '', composeFile: 'docker-compose.yml',
  healthUrl: '', healthRetries: 5, keepVersions: 5,
})
</script>

<template>
  <div class="max-w-[1100px]">
    <PageHeader
      title="部署目标"
      :count="hosts ? `共 ${hosts.length} 台主机` : undefined"
    >
      <template #actions>
        <button class="btn-primary" @click="drawer = true">
          <Icon name="plus" :size="13" />添加主机
        </button>
      </template>
    </PageHeader>

    <p class="flex items-center gap-2 text-[12px] text-muted border border-divider rounded-card
              bg-overlay/40 px-3 py-2.5 mb-4">
      <Icon name="shield" :size="14" class="text-primary" />
      连接前系统会校验目标机是否已安装 Docker 与 docker-compose，校验失败会阻止部署。
    </p>

    <SkeletonRows v-if="loading" :rows="2" height="150px" />

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <article v-for="h in hosts ?? []" :key="h.id" class="panel p-3.5 flex flex-col gap-2.5">
        <div class="flex items-center gap-2">
          <h2 class="text-[14px] font-semibold">{{ h.name }}</h2>
          <div class="flex-1" />
          <StatusBadge :state="h.status" />
          <button class="btn-ghost !h-6 !px-1.5" aria-label="更多操作">
            <Icon name="more" :size="14" />
          </button>
        </div>

        <div class="font-mono text-2xs text-muted">
          {{ h.sshUser }}@{{ h.addr }}
          <span class="text-dim ml-2">{{ h.statusDetail }}</span>
        </div>

        <p class="text-2xs text-dim">
          工作目录 {{ h.workDir }} · 健康检查{{ h.healthCheckUrl ? '已配置' : '未配置' }} ·
          保留 {{ h.keepVersions }} 个历史版本
        </p>

        <p class="text-2xs text-dim">
          已被 {{ h.usedBy.length }} 个项目使用：{{ h.usedBy.join('、') }}
        </p>

        <p v-if="h.status === 'unreachable'" class="text-2xs text-danger font-mono">{{ h.statusDetail }}</p>
        <p v-else-if="testResult[h.id]" class="text-2xs text-success font-mono">{{ testResult[h.id] }}</p>

        <div class="flex items-center gap-2 pt-0.5">
          <button class="btn-outline" :disabled="testing === h.id" @click="test(h)">
            <Icon name="refresh" :size="12" :spin="testing === h.id" />测试连接
          </button>
          <button class="btn-ghost">编辑</button>
        </div>
      </article>
    </div>

    <!-- 添加主机抽屉 -->
    <div v-if="drawer" class="fixed inset-0 z-50 flex justify-end bg-black/50" @click.self="drawer = false">
      <aside
        class="w-[420px] max-w-full h-full bg-overlay border-l border-edge flex flex-col shadow-float"
        role="dialog" aria-modal="true" aria-labelledby="add-host-title"
      >
        <header class="flex items-center gap-2 h-10 px-3 border-b border-divider shrink-0">
          <h2 id="add-host-title" class="text-[13.5px] font-semibold">添加部署主机</h2>
          <div class="flex-1" />
          <button class="btn-ghost !h-6 !px-1.5" aria-label="关闭" @click="drawer = false">
            <Icon name="close" :size="14" />
          </button>
        </header>

        <div class="flex-1 overflow-y-auto p-3.5 flex flex-col gap-3">
          <p class="flex items-start gap-2 text-2xs text-primary border border-primary/30
                    bg-primary/10 rounded-ctl px-2 py-1.5">
            <Icon name="lock" :size="12" class="mt-0.5 shrink-0" />
            私钥将使用 AES-GCM 加密后存储，主密钥从环境变量注入，不写入数据库。
          </p>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">主机名</span>
            <input v-model="form.name" class="field" placeholder="prod-vps-02" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">地址 (host:port)</span>
            <input v-model="form.addr" class="field font-mono" placeholder="10.0.0.20:22" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">登录用户</span>
            <input v-model="form.user" class="field font-mono" placeholder="deploy" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">SSH 私钥</span>
            <textarea
              v-model="form.key" rows="4" class="field !h-auto py-1.5 font-mono text-2xs resize-y"
              placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
            />
            <span class="text-2xs text-dim">支持 OpenSSH 格式私钥，粘贴后不可再查看明文。</span>
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">目标机公钥指纹</span>
            <input v-model="form.fingerprint" class="field font-mono" placeholder="SHA256:..." />
            <span class="text-2xs text-dim">用于防止中间人攻击，可在目标机执行 ssh-keyscan 获取。</span>
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">工作目录</span>
            <input v-model="form.workDir" class="field font-mono" placeholder="/srv/我的项目" />
          </label>

          <div class="grid grid-cols-2 gap-2.5">
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">compose 文件名</span>
              <input v-model="form.composeFile" class="field font-mono" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">健康检查重试</span>
              <input v-model.number="form.healthRetries" type="number" min="1" class="field font-mono" />
            </label>
          </div>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">健康检查地址</span>
            <input v-model="form.healthUrl" class="field font-mono" placeholder="http://10.0.0.20:8080/healthz" />
          </label>

          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">保留历史版本数</span>
            <input v-model.number="form.keepVersions" type="number" min="1" class="field font-mono" />
          </label>
        </div>

        <footer class="flex items-center justify-end gap-2 px-3 py-2.5 border-t border-divider shrink-0">
          <button class="btn-outline" @click="drawer = false">取消</button>
          <button class="btn-primary" @click="drawer = false; reload()">
            <Icon name="plus" :size="13" />添加主机
          </button>
        </footer>
      </aside>
    </div>
  </div>
</template>
