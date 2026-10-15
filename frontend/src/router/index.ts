import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatView.vue'),
    meta: { title: '我的对话' },
  },
  {
    path: '/services',
    name: 'services',
    component: () => import('../views/ServicesView.vue'),
    meta: { title: '支持事项' },
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../views/HistoryView.vue'),
    meta: { title: '最近记录' },
  },
  {
    path: '/help',
    name: 'help',
    component: () => import('../views/HelpView.vue'),
    meta: { title: '使用帮助' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '设置' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router