<script setup lang="ts">
import { ref } from 'vue'
import Icon from '@/components/Icon.vue'
import { api } from '@/api'
import type { Build } from '@/types'

const props = defineProps<{
  build: Build
  previous: { sha: string; message: string; time: string }
}>()
const emit = defineEmits<{ close: [] }>()

const busy = ref(false)
const done = ref(false)

async function confirm() {
  busy.value = true
  try {
    await api.rollbackTo(props.build.number)
    done.value = true
    setTimeout(() => emit('close'), 900)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4"
    role="dialog" aria-modal="true" aria-labelledby="rb-title"
    @click.self="emit('close')"
  >
    <div class="panel bg-overlay border-edge w-full max-w-[520px] shadow-float">
      <header class="flex items-center gap-2 h-9 px-3 border-b border-divider">
        <h2 id="rb-title" class="text-[13.5px] font-semibold">回滚到上一个版本</h2>
        <div class="flex-1" />
        <button class="btn-ghost !h-6 !px-1.5" aria-label="关闭" @click="emit('close')">
          <Icon name="close" :size="14" />
        </button>
      </header>

      <div class="p-3.5 flex flex-col gap-3">
        <p class="text-[12.5px] text-muted leading-relaxed">
          将把 <span class="font-mono text-ink">web-api</span> 从当前版本
          <span class="font-mono text-danger">{{ build.commitSha }}</span> 回滚到
          <span class="font-mono text-success">{{ previous.sha }}</span>。
          系统会重新部署该版本的镜像，并在部署后执行健康检查。
        </p>

        <table class="w-full text-2xs font-mono border border-divider rounded-ctl overflow-hidden">
          <thead class="bg-overlay/60 text-dim">
            <tr><th class="text-left px-2 h-6 font-medium"></th>
                <th class="text-left px-2 h-6 font-medium">当前版本（异常）</th>
                <th class="text-left px-2 h-6 font-medium">将回滚到（健康）</th></tr>
          </thead>
          <tbody class="text-muted">
            <tr class="border-t border-divider"><td class="px-2 h-6 text-dim">COMMIT</td>
              <td class="px-2 h-6 text-danger">{{ build.commitSha }}</td>
              <td class="px-2 h-6 text-success">{{ previous.sha }}</td></tr>
            <tr class="border-t border-divider"><td class="px-2 h-6 text-dim">提交标题</td>
              <td class="px-2 h-6 truncate max-w-[150px]">{{ build.commitMessage }}</td>
              <td class="px-2 h-6 truncate max-w-[150px]">{{ previous.message }}</td></tr>
            <tr class="border-t border-divider"><td class="px-2 h-6 text-dim">状态</td>
              <td class="px-2 h-6">退出码 {{ build.exitCode }} (失败)</td>
              <td class="px-2 h-6">健康检查 200 OK</td></tr>
          </tbody>
        </table>

        <p class="flex items-center gap-2 text-2xs text-warning bg-warning/10 border border-warning/30 rounded-ctl px-2 py-1.5">
          <Icon name="alert" :size="12" />回滚过程约有 5–10 秒服务不可用。
        </p>
      </div>

      <footer class="flex items-center justify-end gap-2 px-3 py-2.5 border-t border-divider">
        <button class="btn-outline" @click="emit('close')">取消</button>
        <button class="btn-danger" :disabled="busy || done" @click="confirm">
          <Icon :name="done ? 'check' : 'undo'" :size="13" :spin="busy" />
          {{ done ? '已回滚' : '确认回滚' }}
        </button>
      </footer>
    </div>
  </div>
</template>
