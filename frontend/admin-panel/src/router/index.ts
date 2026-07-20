import { createRouter, createWebHistory } from 'vue-router'
import { isAdminAuthenticated } from '../services/api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/',
      component: () => import('../layout/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('../views/Dashboard/DashboardView.vue'),
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('../views/KnowledgeBase/KnowledgeView.vue'),
        },
        {
          path: 'avatar',
          name: 'Avatar',
          component: () => import('../views/AvatarConfig/AvatarView.vue'),
        },
        {
          path: 'analytics',
          name: 'Analytics',
          component: () => import('../views/Analytics/AnalyticsView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const authenticated = isAdminAuthenticated()
  if (to.meta.requiresAuth && !authenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && authenticated) return { name: 'Dashboard' }
})

export default router
