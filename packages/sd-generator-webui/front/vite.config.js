import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  // Resolve aliases
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  // Dev server configuration
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },

  // Build configuration
  build: {
    outDir: '../backend/static/dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'vuetify': ['vuetify']
        }
      }
    }
  },

  // Base URL (public path)
  base: process.env.NODE_ENV === 'production' ? '/webui/' : '/',

  // Define global constants
  define: {
    __BUILD_TIMESTAMP__: JSON.stringify(new Date().toISOString())
  },

  // Vitest configuration
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/tests/setup.js'],
    pool: 'vmThreads',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.spec.js'
      ]
    }
  }
})
