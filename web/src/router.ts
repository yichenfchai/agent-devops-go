import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/**
 * 13 个页面与 stitch 设计稿一一对应。
 * meta.title 同时用于顶栏面包屑与 document.title —— 顺手解决了
 * 设计稿里「所有页面面包屑都写死成 构建 #1091」和「页面没有 title」两个问题。
 */
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/projects' },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('@/views/ProjectListView.vue'),
    meta: { title: '项目', crumb: ['项目'] },
  },
  {
    path: '/projects/new',
    name: 'project-new',
    component: () => import('@/views/ProjectWizardView.vue'),
    meta: { title: '新建项目', crumb: ['项目', '新建'] },
  },
  {
    path: '/projects/:id/builds',
    name: 'builds',
    component: () => import('@/views/BuildHistoryView.vue'),
    meta: { title: '构建历史', crumb: ['项目', 'web-api', '构建历史'] },
  },
  {
    path: '/projects/:id/settings',
    name: 'project-settings',
    component: () => import('@/views/ProjectSettingsView.vue'),
    meta: { title: '项目设置', crumb: ['项目', 'web-api', '设置'] },
  },
  {
    path: '/projects/:id/secrets',
    name: 'secrets',
    component: () => import('@/views/SecretsView.vue'),
    meta: { title: '密钥管理', crumb: ['项目', 'web-api', '密钥管理'] },
  },
  {
    path: '/builds/:number',
    name: 'build-detail',
    component: () => import('@/views/BuildRunningView.vue'),
    meta: { title: '构建详情', crumb: ['项目', 'web-api', '构建'] },
  },
  {
    path: '/builds/:number/failed',
    name: 'build-failed',
    component: () => import('@/views/BuildFailedView.vue'),
    meta: { title: '构建失败', crumb: ['项目', 'web-api', '构建'] },
  },
  {
    path: '/builds/:number/diagnosis',
    name: 'build-diagnosis',
    component: () => import('@/views/BuildDiagnosisView.vue'),
    meta: { title: 'AI 智能诊断', crumb: ['项目', 'web-api', '构建'] },
  },
  {
    path: '/builds/:number/deployment',
    name: 'deployment',
    component: () => import('@/views/DeploymentDetailView.vue'),
    meta: { title: '部署详情', crumb: ['项目', 'web-api', '部署'] },
  },
  {
    path: '/hosts',
    name: 'hosts',
    component: () => import('@/views/DeploymentTargetsView.vue'),
    meta: { title: '部署目标', crumb: ['项目', '部署目标'] },
  },
  {
    path: '/states',
    name: 'states',
    component: () => import('@/views/StatesDemoView.vue'),
    meta: { title: '状态规范', crumb: ['项目', 'web-api', '状态规范'] },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', bare: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/projects' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  const t = to.meta.title as string | undefined
  document.title = t ? `${t} · GoPulse CI` : 'GoPulse CI'
})
