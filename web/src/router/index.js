import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/map', name: 'Map', component: () => import('../views/Map.vue') },
  { path: '/statistics', name: 'Statistics', component: () => import('../views/Statistics.vue') },
  { path: '/assistant', name: 'Assistant', component: () => import('../views/Assistant.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
