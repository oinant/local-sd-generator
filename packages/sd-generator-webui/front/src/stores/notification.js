import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    show: false,
    message: '',
    color: 'info'
  }),

  actions: {
    show(payload) {
      this.show = true
      this.message = payload.message
      this.color = payload.color || 'info'
    },

    hide() {
      this.show = false
    }
  }
})
