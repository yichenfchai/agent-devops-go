import { describe, it, expect } from 'vitest'
import * as mock from '@/api/mock'

/**
 * mock 数据是全站唯一事实来源，这些断言把设计稿里出现过的
 * 「同一构建号两个耗时」「构建机三个名字」这类跨页矛盾钉死在测试里。
 */
describe('mock 数据跨页一致性', () => {
  it('构建 #1091 的耗时在全站只有一个值', () => {
    expect(mock.BUILD_1091_DURATION_MS).toBe(28_140)
    const b = mock.builds.find((x) => x.number === 1091)
    expect(b?.durationMs).toBe(mock.BUILD_1091_DURATION_MS)
  })

  it('构建机只有一个名字，不存在已废弃的旧名字', () => {
    expect(mock.RUNNER.name).toBe('build-runner-01')
    const dumped = JSON.stringify(mock)
    // 这三个名字是设计稿里出现过的历史遗留，任何页面都不该再引用
    expect(dumped).not.toContain('local-agent-01')
    expect(dumped).not.toContain('runner-primary.internal')
    expect(dumped).not.toContain('local-executor-0')
  })

  it('构建号唯一', () => {
    const nums = mock.builds.map((b) => b.number)
    expect(new Set(nums).size).toBe(nums.length)
  })

  it('项目引用的部署目标真实存在', () => {
    const hostIds = new Set(mock.hosts.map((h) => h.id))
    for (const p of mock.projects) {
      if (p.deployHostId !== null) expect(hostIds.has(p.deployHostId)).toBe(true)
    }
  })

  it('失败构建有非零退出码，成功构建退出码为 0', () => {
    for (const b of mock.builds) {
      if (b.exitCode === null) continue
      if (b.state === 'failed' || b.state === 'deploy_failed') expect(b.exitCode).not.toBe(0)
      if (b.state === 'deployed' || b.state === 'succeeded') expect(b.exitCode).toBe(0)
    }
  })

  it('项目地址与主机地址的格式始终是合法的', () => {
    for (const h of mock.hosts) {
      expect(h.addr).toMatch(/^\d+\.\d+\.\d+\.\d+:\d+$/)
      expect(h.workDir.startsWith('/')).toBe(true)
    }
  })
})

/**
 * AI 诊断页的日志顺序曾经在技术上讲不通：命令是 `tsc -b && vite build`，
 * 但日志先输出了 vite 的构建 banner 再报 TS 错误 —— && 是短路执行，
 * tsc 失败后 vite 根本不会跑。这些断言防止它被改回去。
 */
describe('失败日志的技术自洽性', () => {
  const idx = (needle: string) => mock.failLog1091.findIndex((l) => l.text.includes(needle))

  it('顺序正确：tsc -b → TS 错误 → npm 生命周期错误', () => {
    const tsc = idx('tsc -b')
    const err = idx('error TS2345')
    const lifecycle = idx('npm ERR! code ELIFECYCLE')
    expect(tsc).toBeGreaterThanOrEqual(0)
    expect(err).toBeGreaterThan(tsc)
    expect(lifecycle).toBeGreaterThan(err)
  })

  it('tsc 失败后不再出现 vite 的构建输出', () => {
    expect(mock.failLog1091.some((l) => l.text.includes('vite v5.2.0 building'))).toBe(false)
    expect(mock.failLog1091.some((l) => l.text.includes('modules transformed'))).toBe(false)
  })

  it('时间戳单调不减', () => {
    for (let i = 1; i < mock.failLog1091.length; i++) {
      expect(mock.failLog1091[i].ts >= mock.failLog1091[i - 1].ts).toBe(true)
    }
  })

  it('时间戳都是 HH:MM:SS 格式', () => {
    for (const l of mock.failLog1091) expect(l.ts).toMatch(/^\d{2}:\d{2}:\d{2}$/)
  })

  it('日志里出现的文件名与行号，与 AI 诊断的原因描述对得上', () => {
    const joined = mock.failLog1091.map((l) => l.text).join('\n')
    expect(joined).toContain('src/api/client.ts:42')
    expect(mock.diagnosis1091.rootCause).toContain('src/api/client.ts 第 42 行')
  })
})

/**
 * 运行中的构建不能显示上一次失败的日志 —— 这是实现过程中真实出现过的 bug。
 */
describe('运行中构建的日志', () => {
  it('与失败构建的日志不同', () => {
    expect(mock.runningLog1092).not.toEqual(mock.failLog1091)
  })

  it('不包含任何失败信号', () => {
    const joined = mock.runningLog1092.map((l) => l.text).join('\n')
    expect(joined).not.toContain('TS2345')
    expect(joined).not.toContain('npm ERR!')
    expect(joined).not.toContain('退出码')
  })

  it('有 level 为 error 的行则视为回归', () => {
    expect(mock.runningLog1092.filter((l) => l.level === 'error')).toHaveLength(0)
  })
})
