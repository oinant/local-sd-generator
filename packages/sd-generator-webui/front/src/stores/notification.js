import { defineStore } from 'pinia'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    visible: false,
    message: '',
    color: 'info'
  }),

  actions: {
    show(payload) {
      this.visible = true
      this.message = payload.message
      this.color = payload.color || 'info'
    },

    hide() {
      this.visible = false
    }
  }
})
