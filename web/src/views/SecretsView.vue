<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import { useAsync } from '@/composables/useAsync'
import PageHeader from '@/components/ui/PageHeader.vue'
import SkeletonRows from '@/components/ui/SkeletonRows.vue'
import Icon from '@/components/Icon.vue'
import type { Secret } from '@/types'

const { data: secrets, loading, reload } = useAsync<Secret[]>(() => api.listSecrets())
const revealed = ref<Set<number>>(new Set())
const showAdd = ref(false)
const newKey = ref('')
const newValue = ref('')
const saving = ref(false)

function toggle(id: number) {
  const s = new Set(revealed.value)
  s.has(id) ? s.delete(id) : s.add(id)
  revealed.value = s
}

async function save() {
  if (!newKey.value.trim()) return
  saving.value = true
  try {
    await api.addSecret(newKey.value.trim(), newValue.value)
    newKey.value = ''
    newValue.value = ''
    showAdd.value = false
    await reload()
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-[960px]">
    <PageHeader title="环境变量与密钥" :count="secrets ? `变量总数 ${secrets.length} · 上限 50` : undefined">
      <template #actions>
        <button class="btn-primary" @click="showAdd = !showAdd">
          <Icon name="plus" :size="13" />添加变量
        </button>
      </template>
    </PageHeader>

    <!-- 安全说明：与论文里的设计描述保持一致，不提 KMS / HSM -->
    <p class="flex items-start gap-2 text-[12px] text-muted border border-divider rounded-card
              bg-overlay/40 px-3 py-2.5 mb-4">
      <Icon name="lock" :size="14" class="text-success mt-0.5" />
      <span>
        所有值使用 <span class="font-mono text-ink">AES-GCM</span> 加密后存储，
        主密钥从环境变量注入，不写入数据库。构建时仅注入该项目声明过的变量。
      </span>
    </p>

    <!-- 新增表单 -->
    <div v-if="showAdd" class="panel p-3.5 mb-4 flex flex-col gap-2.5">
      <div class="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-2.5">
        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">键名</span>
          <input v-model="newKey" class="field font-mono" placeholder="DATABASE_URL" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">值</span>
          <input v-model="newValue" type="password" class="field font-mono" placeholder="••••••••" />
        </label>
      </div>
      <p class="text-2xs text-warning flex items-center gap-1.5">
        <Icon name="alert" :size="11" />
        请勿在值中使用换行符。该值会注入到所有构建步骤，注意不要被构建脚本打印到日志。
      </p>
      <div class="flex gap-2">
        <button class="btn-primary" :disabled="saving || !newKey.trim()" @click="save">
          <Icon name="save" :size="13" :spin="saving" />保存
        </button>
        <button class="btn-outline" @click="showAdd = false">取消</button>
      </div>
    </div>

    <SkeletonRows v-if="loading" :rows="3" height="36px" />

    <div v-else class="panel overflow-hidden">
      <table class="w-full text-[12.5px]">
        <thead>
          <tr class="text-2xs uppercase tracking-wider text-dim border-b border-divider">
            <th class="text-left font-medium px-3 h-8">键名</th>
            <th class="text-left font-medium px-3 h-8 w-[240px]">值</th>
            <th class="text-left font-medium px-3 h-8 w-[110px]">更新时间</th>
            <th class="text-left font-medium px-3 h-8 w-[100px]">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in secrets ?? []" :key="s.id" class="border-b border-divider/60 row-hover">
            <td class="px-3 h-9 font-mono">{{ s.key }}</td>
            <td class="px-3 h-9">
              <span class="flex items-center gap-2">
                <code class="font-mono text-muted">
                  {{ s.isSecret && !revealed.has(s.id) ? '••••••••' : (s.isSecret ? '已解密（仅本次会话可见）' : 'production') }}
                </code>
                <button
                  v-if="s.isSecret" class="btn-ghost !h-5 !px-1"
                  :aria-label="revealed.has(s.id) ? '隐藏值' : '显示值'"
                  @click="toggle(s.id)"
                >
                  <Icon name="eye" :size="12" />
                </button>
              </span>
            </td>
            <td class="px-3 h-9 text-dim text-2xs">{{ s.updatedAt }}</td>
            <td class="px-3 h-9">
              <div class="flex gap-1">
                <button class="btn-ghost !h-6 !px-1.5" aria-label="编辑"><Icon name="sliders" :size="12" /></button>
                <button class="btn-ghost !h-6 !px-1.5" aria-label="删除"><Icon name="x" :size="12" /></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
