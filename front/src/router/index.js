import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/images',
    name: 'Images',
    component: () => import('@/views/Images.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/generate',
    name: 'Generate',
    component: () => import('@/views/Generate.vue'),
    meta: { requiresAuth: true, requiresGenerate: true }
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: () => import('@/views/Jobs.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGenerate = to.matched.some(record => record.meta.requiresGenerate)
  const isAuthenticated = store.getters.isAuthenticated
  const canGenerate = store.getters.canGenerate

  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (requiresGenerate && !canGenerate) {
    store.dispatch('showSnackbar', {
      message: 'Vous n\'avez pas les permissions pour générer des images',
      color: 'error'
    })
    next('/')
  } else {
    next()
  }
})

export default router