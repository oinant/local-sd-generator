import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true, title: 'Home' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },

  // New session management routes
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('@/views/Sessions.vue'),
    meta: { requiresAuth: true, title: 'Sessions' }
  },
  {
    path: '/sessions/:name',
    name: 'SessionDetail',
    component: () => import('@/views/SessionDetail.vue'),
    meta: { requiresAuth: true, title: 'Session Details' }
  },
  {
    path: '/sessions/:name/images',
    name: 'SessionImages',
    component: () => import('@/views/SessionImages.vue'),
    meta: { requiresAuth: true, title: 'Session Images' }
  },
  {
    path: '/sessions/:name/images/:imageId',
    name: 'ImageDetail',
    component: () => import('@/views/ImageDetail.vue'),
    meta: { requiresAuth: true, title: 'Image' }
  },
  {
    path: '/sessions/:name/rating',
    name: 'SessionRating',
    component: () => import('@/views/SessionRating.vue'),
    meta: { requiresAuth: true, title: 'Variation Rating' }
  },

  // Legacy gallery route (keep /images for backward compatibility)
  {
    path: '/gallery',
    name: 'Gallery',
    component: () => import('@/views/Images.vue'),
    meta: { requiresAuth: true, title: 'Gallery' }
  },
  {
    path: '/images',
    redirect: '/gallery'
  },

  {
    path: '/generate',
    name: 'Generate',
    component: () => import('@/views/Generate.vue'),
    meta: { requiresAuth: true, requiresGenerate: true, title: 'Generate' }
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: () => import('@/views/Jobs.vue'),
    meta: { requiresAuth: true, title: 'Jobs' }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const notificationStore = useNotificationStore()

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGenerate = to.matched.some(record => record.meta.requiresGenerate)
  const isAuthenticated = authStore.isAuthenticated
  const canGenerate = authStore.canGenerate

  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (requiresGenerate && !canGenerate) {
    notificationStore.show({
      message: "Vous n'avez pas les permissions pour générer des images",
      color: 'error'
    })
    next('/')
  } else {
    next()
  }
})

export default router
