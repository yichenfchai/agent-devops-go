/**
 * 领域 API。每个方法都是「mock 分支 + 真实请求分支」二选一，
 * 后端起来后只需要把 USE_MOCK 设为 false，调用方一行都不用改。
 */
import { http, USE_MOCK } from './client'
import * as mock from './mock'
import type {
  Build, BuildStats, DeployHost, Deployment, Diagnosis, LogLine, Project, RunnerInfo, Secret, Stage,
} from '@/types'

/** mock 也走一点点延迟，好让骨架屏和 loading 态能被真正看到 */
const delay = (ms = 180) => new Promise<void>((r) => setTimeout(r, ms))

export const api = {
  async listProjects(): Promise<Project[]> {
    if (USE_MOCK) { await delay(); return structuredClone(mock.projects) }
    return http.get('/projects')
  },

  async getProject(id: number): Promise<Project> {
    if (USE_MOCK) {
      await delay()
      const p = mock.projects.find((x) => x.id === id)
      if (!p) throw new Error(`项目 ${id} 不存在`)
      return structuredClone(p)
    }
    return http.get(`/projects/${id}`)
  },

  async createProject(input: { repoFullName: string; branch: string; hostId: number; workDir: string }): Promise<Project> {
    if (USE_MOCK) { await delay(400); return structuredClone({ ...mock.projects[0], id: 99, ...input } as Project) }
    return http.post('/projects', input)
  },

  async listBuilds(projectId?: number): Promise<Build[]> {
    if (USE_MOCK) {
      await delay()
      return structuredClone(projectId ? mock.builds.filter((b) => b.projectId === projectId) : mock.builds)
    }
    return http.get(projectId ? `/projects/${projectId}/builds` : '/builds')
  },

  async getBuild(number: number): Promise<Build> {
    if (USE_MOCK) {
      await delay()
      const b = mock.builds.find((x) => x.number === number)
      if (!b) throw new Error(`构建 #${number} 不存在`)
      return structuredClone(b)
    }
    return http.get(`/builds/${number}`)
  },

  async getBuildStats(): Promise<BuildStats> {
    if (USE_MOCK) { await delay(); return structuredClone(mock.stats) }
    return http.get('/builds/stats')
  },

  async getStages(number: number): Promise<Stage[]> {
    if (USE_MOCK) {
      await delay()
      return structuredClone(number === 1092 ? mock.stages1092 : mock.stages1091)
    }
    return http.get(`/builds/${number}/stages`)
  },

  async getLogs(number: number): Promise<LogLine[]> {
    if (USE_MOCK) {
      await delay()
      // 不同构建号的日志各不相同 —— 运行中的构建不能显示上一次失败的日志
      return structuredClone(number === 1092 ? mock.runningLog1092 : mock.failLog1091)
    }
    return http.get(`/builds/${number}/logs`)
  },

  async triggerBuild(projectId: number): Promise<{ number: number }> {
    if (USE_MOCK) { await delay(300); return { number: 1093 } }
    return http.post(`/projects/${projectId}/builds`)
  },

  async rollbackTo(buildNumber: number): Promise<void> {
    if (USE_MOCK) { await delay(400); return }
    return http.post(`/builds/${buildNumber}/rollback`)
  },

  async listHosts(): Promise<DeployHost[]> {
    if (USE_MOCK) { await delay(); return structuredClone(mock.hosts) }
    return http.get('/hosts')
  },

  async testHost(id: number): Promise<{ ok: boolean; detail: string }> {
    if (USE_MOCK) { await delay(900); return { ok: id === 1, detail: id === 1 ? 'SSH-2.0-OpenSSH_8.9p1' : 'Connection refused' } }
    return http.post(`/hosts/${id}/test`)
  },

  async getDeployment(buildNumber: number): Promise<Deployment> {
    if (USE_MOCK) { await delay(); return structuredClone(mock.deployments[0]) }
    return http.get(`/deployments/${buildNumber}`)
  },

  async listSecrets(): Promise<Secret[]> {
    if (USE_MOCK) { await delay(); return structuredClone(mock.secrets) }
    return http.get('/secrets')
  },

  async addSecret(key: string, value: string): Promise<Secret> {
    if (USE_MOCK) { await delay(300); return { id: Date.now(), key, updatedAt: '刚刚', isSecret: true } }
    return http.post('/secrets', { key, value })
  },

  async getRunner(): Promise<RunnerInfo> {
    if (USE_MOCK) { await delay(80); return structuredClone(mock.RUNNER) }
    return http.get('/runner')
  },

  async getDiagnosis(buildNumber: number): Promise<Diagnosis> {
    if (USE_MOCK) { await delay(260); return structuredClone(mock.diagnosis1091) }
    return http.get(`/builds/${buildNumber}/diagnosis`)
  },
}

export { USE_MOCK }
