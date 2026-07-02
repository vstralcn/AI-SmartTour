import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('../layout/AdminLayout.vue'),
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

export default router
