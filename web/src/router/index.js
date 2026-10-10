import { createRouter, createWebHistory } from 'vue-router'
import { watch } from 'vue'
import Home from '../views/Home.vue'
import { t, lang } from '../i18n'
import { scrollToTop } from '../motion'

const routes = [
  { path: '/', name: 'Home', component: Home, meta: { title: 'meta.home' } },
  { path: '/map', name: 'Map', component: () => import('../views/Map.vue'), meta: { title: 'meta.map', fullBleed: true } },
  { path: '/statistics', name: 'Statistics', component: () => import('../views/Statistics.vue'), meta: { title: 'meta.figures' } },
  { path: '/assistant', name: 'Assistant', component: () => import('../views/Assistant.vue'), meta: { title: 'meta.ask', fullBleed: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue'), meta: { title: 'meta.notFound' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Lenis owns window scrolling; reset it ourselves after each navigation
  scrollBehavior: () => false,
})

const setTitle = () => {
  const key = router.currentRoute.value.meta.title
  document.title = `${key ? t(key) : 'MeghBhed'} · ${lang.value === 'bn' ? 'মেঘভেদ' : 'MeghBhed'}`
}

router.afterEach((to, from) => {
  if (to.path !== from.path) scrollToTop()
  setTitle()
})
watch(lang, setTitle)

export default router
