const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // Désactive ESLint pendant le dev pour éviter les blocages
  devServer: {
    port: 3000,
    allowedHosts: [
      'localhost',
      '.trycloudflare.com' // Allow Cloudflare Tunnel subdomains
    ],
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws' // Auto-detect protocol (wss:// for HTTPS)
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  outputDir: '../backend/static/dist',
  publicPath: process.env.NODE_ENV === 'production' ? '/webui/' : '/'
})