const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  lintOnSave: false, // Désactive ESLint pendant le dev pour éviter les blocages
  devServer: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  outputDir: '../static/dist',
  publicPath: process.env.NODE_ENV === 'production' ? '/static/dist/' : '/'
})