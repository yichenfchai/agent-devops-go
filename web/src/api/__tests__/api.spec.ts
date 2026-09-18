import { describe, it, expect } from 'vitest'
import { api } from '@/api'
import * as mock from '@/api/mock'

describe('api 层（mock 模式）', () => {
  it('getLogs 按构建号返回不同日志', async () => {
    const failed = await api.getLogs(1091)
    const running = await api.getLogs(1092)
    expect(failed.some((l) => l.text.includes('TS2345'))).toBe(true)
    expect(running.some((l) => l.text.includes('TS2345'))).toBe(false)
  })

  it('getBuild 对不存在的构建号抛错', async () => {
    await expect(api.getBuild(99999)).rejects.toThrow(/不存在/)
  })

  it('getProject 对不存在的项目抛错', async () => {
    await expect(api.getProject(99999)).rejects.toThrow(/不存在/)
  })

  it('返回的是深拷贝，修改返回值不会污染源数据', async () => {
    const before = mock.projects[0].name
    const p = await api.listProjects()
    p[0].name = '被测试改坏了'
    expect(mock.projects[0].name).toBe(before)
  })

  it('阶段列表随构建号不同', async () => {
    const a = await api.getStages(1091)
    const b = await api.getStages(1092)
    expect(a.find((s) => s.status === 'failed')).toBeTruthy()
    expect(b.find((s) => s.status === 'running')).toBeTruthy()
  })

  it('listBuilds 支持按项目过滤', async () => {
    const only = await api.listBuilds(2)
    expect(only.every((b) => b.projectId === 2)).toBe(true)
    expect(only.length).toBeLessThan((await api.listBuilds()).length)
  })

  it('testHost 对不可达主机返回 ok=false', async () => {
    expect((await api.testHost(1)).ok).toBe(true)
    expect((await api.testHost(2)).ok).toBe(false)
  })
})
