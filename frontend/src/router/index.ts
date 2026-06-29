import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/game',
    name: 'Game',
    component: () => import('../views/GameView.vue'),
  },
  {
    path: '/twenty-q',
    name: 'TwentyQ',
    component: () => import('../views/TwentyQView.vue'),
  },
  {
    path: '/result',
    name: 'Result',
    component: () => import('../views/ResultView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
