const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

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
  publicPath: process.env.NODE_ENV === 'production' ? '/webui/' : '/',

  chainWebpack: config => {
    // Inject build timestamp automatically (merge with existing defines)
    config.plugin('define').tap(args => {
      args[0].__BUILD_TIMESTAMP__ = JSON.stringify(new Date().toISOString())
      return args
    })
  }
})