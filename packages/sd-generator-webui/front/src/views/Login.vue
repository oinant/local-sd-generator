<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-card-title class="text-h4 text-center py-8">
            <div class="text-center">
              <div class="text-h3 mb-4">🎨</div>
              <div>SD Image Generator</div>
              <div class="text-subtitle-1 text-medium-emphasis">Authentification requise</div>
            </div>
          </v-card-title>

          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="token"
                label="Token d'authentification (GUID)"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                prepend-inner-icon="mdi-key"
                variant="outlined"
                :rules="[rules.required, rules.guid]"
                :error-messages="errorMessage"
                @keyup.enter="handleLogin"
              ></v-text-field>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                class="mt-4"
              >
                Se connecter
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

export default {
  name: 'LoginView',

  setup() {
    const authStore = useAuthStore()
    const { loading, isAuthenticated } = storeToRefs(authStore)

    return {
      authStore,
      loading,
      isAuthenticated
    }
  },

  data() {
    return {
      token: '',
      errorMessage: '',
      rules: {
        required: value => !!value || 'Token requis',
        guid: value => {
          const guidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
          return guidRegex.test(value) || 'Format GUID invalide'
        }
      }
    }
  },

  watch: {
    isAuthenticated(newVal) {
      if (newVal) {
        this.$router.push('/')
      }
    }
  },

  created() {
    // Rediriger si déjà authentifié
    if (this.isAuthenticated) {
      this.$router.push('/')
    }
  },

  methods: {
    async handleLogin() {
      this.errorMessage = ''

      if (!this.token) {
        this.errorMessage = 'Token requis'
        return
      }

      const success = await this.authStore.login(this.token)
      if (success) {
        this.$router.push('/')
      } else {
        this.errorMessage = 'Token invalide'
      }
    }
  }
}
</script>

<style scoped>
.font-monospace {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}
</style>
