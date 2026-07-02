import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/ChatView.vue'),
    },
    {
      path: '/route-plan',
      name: 'RoutePlan',
      component: () => import('../views/RoutePlanView.vue'),
    },
  ],
})

export default router
