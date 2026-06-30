import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/HomeView.vue') },
  { path: '/game', name: 'Game', component: () => import('../views/GameView.vue') },
  { path: '/twenty-q', name: 'TwentyQ', component: () => import('../views/TwentyQView.vue') },
  { path: '/chain', name: 'Chain', component: () => import('../views/ChainView.vue') },
  { path: '/battle', name: 'Battle', component: () => import('../views/BattleView.vue') },
  { path: '/leaderboard', name: 'Leaderboard', component: () => import('../views/LeaderboardView.vue') },
  { path: '/profile', name: 'Profile', component: () => import('../views/ProfileView.vue') },
  { path: '/result', name: 'Result', component: () => import('../views/ResultView.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
