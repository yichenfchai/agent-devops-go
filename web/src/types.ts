/**
 * 与后端类型定义一一对应的类型定义（单一事实来源）。
 * 后端布局为 cmd/devopsd + internal/store（sqlc 生成），字段改动须双侧同步。
 */

export type BuildState =
  | 'queued' | 'running' | 'succeeded'
  | 'deploying' | 'deployed'
  | 'failed' | 'deploy_failed' | 'rolled_back'

export type Trigger = 'push' | 'pr' | 'manual' | 'rollback'

export interface Project {
  id: number
  name: string
  repoProvider: 'github' | 'gitlab'
  repoFullName: string
  defaultBranch: string
  detectedType: string | null
  deployHostId: number | null
  lastBuild: { number: number; state: BuildState; finishedAt: string; durationMs: number } | null
  deployed: boolean
  created_at: string
}

export interface Build {
  id: number
  projectId: number
  number: number
  state: BuildState
  trigger: Trigger
  ref: string
  commitSha: string
  commitMessage: string
  commitAuthor: string
  baseImage: string | null
  imageTag: string | null
  exitCode: number | null
  queuedAt: string
  startedAt: string | null
  finishedAt: string | null
  durationMs: number | null
  diagnosis: Diagnosis | null
}

export interface Diagnosis {
  rootCause: string
  suggestion: string
  model: string
  latencyMs: number
  inputTokens: number
  redactions: number
}

export interface Stage {
  index: number
  name: string
  command: string
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped'
  durationMs: number | null
}

export interface LogLine {
  seq: number
  ts: string
  text: string
  level: 'info' | 'ok' | 'warn' | 'error'
}

export interface DeployHost {
  id: number
  name: string
  addr: string
  sshUser: string
  workDir: string
  composeFile: string
  healthCheckUrl: string | null
  healthRetries: number
  keepVersions: number
  status: 'ok' | 'unreachable'
  statusDetail: string
  usedBy: string[]
}

export interface Deployment {
  id: number
  buildId: number
  projectName: string
  imageTag: string
  hostAddr: string
  workDir: string
  state: 'deploying' | 'deployed' | 'failed' | 'rolled_back'
  steps: Stage[]
  startedAt: string
  durationMs: number
  versions: { tag: string; deployedAt: string; state: string }[]
}

export interface Secret {
  id: number
  key: string
  updatedAt: string
  isSecret: boolean
}

export interface BuildStats {
  total: number
  successRate: number
  avgDurationMs: number
  monthlyDeploys: number
}

export interface RunnerInfo {
  name: string
  os: string
  version: string
  state: 'idle' | 'busy'
  queued: number
}
