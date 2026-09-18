import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      // 后端起来后把 mock 关掉，请求直接转发给 Go 服务
      '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true },
    },
  },
})
