<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const email = ref('')
const password = ref('')
const remember = ref(true)
const busy = ref(false)

async function submit() {
  busy.value = true
  // 后端接入后换成真实的 /api/auth/login
  await new Promise((r) => setTimeout(r, 400))
  busy.value = false
  await router.push('/projects')
}
</script>

<template>
  <div class="min-h-full grid place-items-center bg-canvas p-6">
    <div class="w-[360px] max-w-full flex flex-col gap-4">
      <form class="panel bg-overlay p-5 flex flex-col gap-3.5" @submit.prevent="submit">
        <header class="text-center flex flex-col gap-1">
          <h1 class="text-[18px] font-semibold tracking-tight">GoPulse CI</h1>
          <p class="text-[12px] text-muted">轻量 CI/CD · 面向小型团队</p>
        </header>

        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">工作邮箱</span>
          <input
            v-model="email" type="email" required autocomplete="username"
            class="field w-full" placeholder="you@example.com"
          />
        </label>

        <label class="flex flex-col gap-1">
          <span class="text-2xs text-dim uppercase tracking-wider">访问密码</span>
          <input
            v-model="password" type="password" required autocomplete="current-password"
            class="field w-full" placeholder="••••••••"
          />
        </label>

        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2 text-[12px] text-muted cursor-pointer">
            <input v-model="remember" type="checkbox" class="accent-primary w-3.5 h-3.5" />
            记住此会话
          </label>
          <a href="#" class="text-[12px] text-muted hover:text-primary">忘记密码？</a>
        </div>

        <button type="submit" class="btn-primary w-full justify-center !h-8" :disabled="busy">
          <Icon name="lock" :size="13" :spin="busy" />登录进入控制台
        </button>
      </form>

      <p class="text-center font-mono text-2xs text-dim flex items-center justify-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-success" />本地构建机在线 · PID 4192
      </p>
      <p class="text-center font-mono text-2xs text-dim">
        GoPulse CI v0.1.0 · 单二进制部署 · SQLite 嵌入式存储
      </p>
      <p class="text-center font-mono text-2xs text-dim/70">
        Listening on 127.0.0.1:8080 (Unix Socket Ready)
      </p>
    </div>
  </div>
</template>
