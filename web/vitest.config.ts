import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.spec.ts'],
      setupFiles: ['./src/test/setup.ts'],
      // 不开启 globals：每个测试文件显式 import，类型更明确
      globals: false,
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'json-summary'],
        include: ['src/**/*.{ts,vue}'],
        exclude: [
          'src/**/*.spec.ts',
          'src/test/**',
          'src/env.d.ts',
          'src/main.ts',      // 只有一行挂载，没有可测逻辑
          'src/router.ts',    // 路由表本身在 router.spec.ts 里以断言方式覆盖
        ],
      },
    },
  }),
)
