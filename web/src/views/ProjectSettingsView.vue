<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import Icon from '@/components/Icon.vue'

const TABS = [
  { id: 'basic',   label: '基本信息', icon: 'info' },
  { id: 'build',   label: '构建配置', icon: 'code' },
  { id: 'notify',  label: '通知',     icon: 'bell' },
] as const

const tab = ref<(typeof TABS)[number]['id']>('build')
const mode = ref<'auto' | 'manual'>('auto')

const form = ref({
  name: 'web-api', branch: 'main',
  timeoutMin: 30, artifactPath: 'dist/', logLines: 5000,
  notifyOnFail: true, notifyOnDeploy: true, notifyOnRollback: true,
  channel: 'webhook', webhookUrl: '',
})

const PIPELINE = 'npm ci → npm run build → docker build -t web-api:${SHA} → docker push'
</script>

<template>
  <div class="max-w-[1000px]">
    <PageHeader title="项目设置" subtitle="配置与交付策略">
      <template #actions>
        <div class="flex items-center gap-2">
          <button class="btn-ghost"><Icon name="undo" :size="13" />放弃更改</button>
          <button class="btn-primary"><Icon name="save" :size="13" />保存所有设置</button>
        </div>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-4 items-start">
      <!-- 设置子导航 -->
      <nav class="flex md:flex-col gap-1" aria-label="设置分类">
        <button
          v-for="t in TABS" :key="t.id"
          class="flex items-center gap-2 h-8 px-2.5 rounded-ctl text-[12.5px] text-left transition-colors"
          :class="tab === t.id ? 'bg-hover text-ink' : 'text-muted hover:bg-hover hover:text-ink'"
          @click="tab = t.id"
        >
          <Icon :name="t.icon" :size="14" />{{ t.label }}
        </button>
      </nav>

      <div class="flex flex-col gap-4">
        <!-- 基本信息 -->
        <section v-if="tab === 'basic'" class="panel p-4 flex flex-col gap-3">
          <label class="flex flex-col gap-1 max-w-[320px]">
            <span class="text-2xs text-dim uppercase tracking-wider">项目名</span>
            <input v-model="form.name" class="field" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-2xs text-dim uppercase tracking-wider">仓库地址</span>
            <input value="github.com/acme/web-api" readonly class="field font-mono text-muted cursor-not-allowed" />
          </label>
          <label class="flex flex-col gap-1 max-w-[240px]">
            <span class="text-2xs text-dim uppercase tracking-wider">默认分支</span>
            <input v-model="form.branch" class="field font-mono" />
          </label>
          <hr class="border-divider my-1" />
          <div>
            <button class="btn-danger"><Icon name="x" :size="13" />删除项目</button>
            <p class="text-2xs text-dim mt-1.5">删除后构建历史与部署记录会一并移除，目标机上的应用不会被卸载。</p>
          </div>
        </section>

        <!-- 构建配置 -->
        <section v-else-if="tab === 'build'" class="panel p-4 flex flex-col gap-3">
          <div class="flex items-center gap-1 border border-divider rounded-ctl p-0.5 w-fit">
            <button
              v-for="m in [{ id: 'auto', l: '自动识别' }, { id: 'manual', l: '手动配置' }]" :key="m.id"
              class="h-6 px-3 rounded-badge text-[12px] transition-colors"
              :class="mode === m.id ? 'bg-primary text-[#0b1020] font-medium' : 'text-muted hover:text-ink'"
              @click="mode = m.id as 'auto' | 'manual'"
            >{{ m.l }}</button>
          </div>

          <template v-if="mode === 'auto'">
            <div class="bg-[#0b0c0f] border border-divider rounded-card p-3">
              <div class="flex items-center gap-2 mb-2">
                <span class="font-mono text-2xs text-dim">检测到 package.json · 构建镜像 node:20-alpine</span>
                <div class="flex-1" />
                <button class="btn-ghost !h-6 text-2xs"><Icon name="refresh" :size="11" />重新检测</button>
              </div>
              <code class="font-mono text-2xs text-muted break-all">{{ PIPELINE }}</code>
            </div>
          </template>
          <template v-else>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">Pipeline YAML</span>
              <textarea
                rows="8" class="field !h-auto py-1.5 font-mono text-2xs resize-y"
                :value="`stages:\n  - name: 安装依赖\n    run: npm ci\n  - name: 执行构建\n    run: npm run build\n  - name: 生成产物\n    run: docker build -t web-api:$SHA .`"
              />
            </label>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">构建超时（分钟）</span>
              <input v-model.number="form.timeoutMin" type="number" min="1" class="field font-mono" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">构建产物路径</span>
              <input v-model="form.artifactPath" class="field font-mono" />
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">日志保留行数</span>
              <input v-model.number="form.logLines" type="number" min="100" class="field font-mono" />
            </label>
          </div>
        </section>

        <!-- 通知 -->
        <section v-else class="panel p-4 flex flex-col gap-1">
          <label
            v-for="n in [
              { k: 'notifyOnFail',     t: '构建失败时通知',     d: '当任意阶段退出码不为 0 时发送通知' },
              { k: 'notifyOnDeploy',   t: '部署成功时通知',     d: '部署完成且健康检查通过后发送通知' },
              { k: 'notifyOnRollback', t: '自动回滚发生时通知', d: '健康检查失败触发自动回滚时发送通知' },
            ]" :key="n.k"
            class="flex items-center gap-3 py-2.5 border-b border-divider/60 last:border-0 cursor-pointer"
          >
            <input
              v-model="form[n.k as 'notifyOnFail' | 'notifyOnDeploy' | 'notifyOnRollback']"
              type="checkbox" class="accent-primary w-3.5 h-3.5"
            />
            <div class="min-w-0">
              <div class="text-[12.5px]">{{ n.t }}</div>
              <div class="text-2xs text-dim">{{ n.d }}</div>
            </div>
          </label>

          <div class="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-3 pt-2">
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">通知渠道</span>
              <select v-model="form.channel" class="field appearance-none cursor-pointer">
                <option value="webhook">Webhook</option>
                <option value="email">邮件</option>
              </select>
            </label>
            <label class="flex flex-col gap-1">
              <span class="text-2xs text-dim uppercase tracking-wider">Webhook 地址</span>
              <input v-model="form.webhookUrl" class="field font-mono" placeholder="https://hooks.example.com/..." />
            </label>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
