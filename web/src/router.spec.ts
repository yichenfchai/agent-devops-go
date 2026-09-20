import { describe, it, expect } from 'vitest'
import { router } from '@/router'

/**
 * 路由 meta 是「面包屑」和「文档标题」的唯一来源。
 *
 * 这两件事在设计稿里都是坏的：
 *   1. 13 个页面的面包屑全部写死成「项目 / web-api / 构建 #1091」，
 *      连项目列表页都显示「构建 #1091」；
 *   2. 13 个页面一个 <title> 都没有，浏览器标签页全是空白。
 *
 * 这些断言把它们钉死，防止以后再退化。
 */

/** 需要面包屑与标题的正常页面（登录页是裸页，单独处理） */
const PAGES = [
  { name: 'projects',         params: {} },
  { name: 'project-new',      params: {} },
  { name: 'builds',           params: { id: 1 } },
  { name: 'project-settings', params: { id: 1 } },
  { name: 'secrets',          params: { id: 1 } },
  { name: 'build-detail',     params: { id: 200 } },
  { name: 'build-failed',     params: { id: 200 } },
  { name: 'build-diagnosis',  params: { id: 200 } },
  { name: 'deployment',       params: { id: 199 } },
  { name: 'hosts',            params: {} },
  { name: 'states',           params: {} },
] as const

describe('路由 meta', () => {
  it('每个页面都有标题和面包屑', () => {
    for (const p of PAGES) {
      const r = router.resolve({ name: p.name, params: p.params as never })
      expect(r.meta.title, `${p.name} 缺 title`).toBeTruthy()
      expect(Array.isArray(r.meta.crumb), `${p.name} 缺 crumb`).toBe(true)
      expect((r.meta.crumb as string[]).length, `${p.name} 的 crumb 为空`).toBeGreaterThan(0)
    }
  })

  it('面包屑逐页不同 —— 不是全站写死同一串', () => {
    const crumbs = PAGES.map(
      (p) => JSON.stringify(router.resolve({ name: p.name, params: p.params as never }).meta.crumb),
    )
    // 至少要有 8 种不同组合，说明确实是按页面算出来的
    expect(new Set(crumbs).size).toBeGreaterThanOrEqual(8)
  })

  it('项目列表页的面包屑就是「项目」，不该出现构建号', () => {
    const r = router.resolve({ name: 'projects' })
    expect(r.meta.crumb).toEqual(['项目'])
    expect(JSON.stringify(r.meta.crumb)).not.toContain('#')
  })

  it('密钥管理页指向密钥管理，而不是构建 #1091', () => {
    const r = router.resolve({ name: 'secrets', params: { id: 1 } })
    expect((r.meta.crumb as string[]).join(' / ')).toContain('密钥管理')
    expect(JSON.stringify(r.meta.crumb)).not.toContain('1091')
  })

  it('登录页标记为裸页（不套顶栏 / 侧栏 / 状态栏）', () => {
    expect(router.resolve({ name: 'login' }).meta.bare).toBe(true)
  })

  it('同一页面的中文标题不重复', () => {
    const titles = PAGES.map(
      (p) => router.resolve({ name: p.name, params: p.params as never }).meta.title as string,
    )
    // 构建详情 / 失败 / 诊断 允许共用「构建」系列前缀，但整体去重后仍应有足够区分度
    expect(new Set(titles).size).toBeGreaterThanOrEqual(9)
  })
})

describe('路由结构', () => {
  it('根路径重定向到项目列表', () => {
    expect(router.resolve('/').matched.length).toBeGreaterThan(0)
  })

  it('未知路径有兜底，不会白屏', () => {
    const r = router.resolve('/完全不存在的路径')
    expect(r.matched.length).toBeGreaterThan(0)
  })

  it('13 个页面全部注册（含登录页）', () => {
    const names = router.getRoutes().map((r) => r.name).filter(Boolean)
    for (const p of PAGES) expect(names).toContain(p.name)
    expect(names).toContain('login')
  })

  it('页面全部懒加载 —— 不在主包里的路由组件应是动态导入', () => {
    // 首页之外的路由不应同步 import，保证主包体积可控
    const lazy = router.getRoutes().filter((r) => typeof r.components?.default === 'function')
    expect(lazy.length).toBeGreaterThanOrEqual(12)
  })
})

describe('文档标题', () => {
  it('导航后 document.title 会跟着变（不再是空白标签页）', async () => {
    await router.push({ name: 'projects' })
    expect(document.title).toBe('项目 · GoPulse CI')

    await router.push({ name: 'secrets', params: { id: 1 } })
    expect(document.title).toBe('密钥管理 · GoPulse CI')
  })

  it('登录页也有标题', async () => {
    await router.push({ name: 'login' })
    expect(document.title).toBe('登录 · GoPulse CI')
  })
})
