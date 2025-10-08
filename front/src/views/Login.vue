<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-card-title class="text-h4 text-center py-8">
            <div class="text-center">
              <div class="text-h3 mb-4">🎨</div>
              <div>SD Image Generator</div>
              <div class="text-subtitle-1 text-medium-emphasis">
                Authentification requise
              </div>
            </div>
          </v-card-title>

          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="token"
                label="Token d'authentification (GUID)"
                placeholder="550e8400-e29b-41d4-a716-446655440000"
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

            <v-divider class="my-6"></v-divider>

            <v-expansion-panels variant="accordion">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon class="mr-2">mdi-help-circle</v-icon>
                  Aide
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div class="text-body-2">
                    <p class="mb-2">
                      <strong>Tokens de démonstration :</strong>
                    </p>
                    <v-list density="compact">
                      <v-list-item>
                        <v-list-item-title class="font-monospace">
                          550e8400-e29b-41d4-a716-446655440000
                        </v-list-item-title>
                        <v-list-item-subtitle>Admin (toutes permissions)</v-list-item-subtitle>
                        <template v-slot:append>
                          <v-btn
                            size="small"
                            variant="outlined"
                            @click="token = '550e8400-e29b-41d4-a716-446655440000'"
                          >
                            Utiliser
                          </v-btn>
                        </template>
                      </v-list-item>

                      <v-list-item>
                        <v-list-item-title class="font-monospace">
                          6ba7b810-9dad-11d1-80b4-00c04fd430c8
                        </v-list-item-title>
                        <v-list-item-subtitle>Générateur</v-list-item-subtitle>
                        <template v-slot:append>
                          <v-btn
                            size="small"
                            variant="outlined"
                            @click="token = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'"
                          >
                            Utiliser
                          </v-btn>
                        </template>
                      </v-list-item>

                      <v-list-item>
                        <v-list-item-title class="font-monospace">
                          6ba7b812-9dad-11d1-80b4-00c04fd430c8
                        </v-list-item-title>
                        <v-list-item-subtitle>Lecture seule</v-list-item-subtitle>
                        <template v-slot:append>
                          <v-btn
                            size="small"
                            variant="outlined"
                            @click="token = '6ba7b812-9dad-11d1-80b4-00c04fd430c8'"
                          >
                            Utiliser
                          </v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'LoginView',

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

  computed: {
    ...mapGetters(['loading', 'isAuthenticated'])
  },

  methods: {
    ...mapActions(['login']),

    async handleLogin() {
      this.errorMessage = ''

      if (!this.token) {
        this.errorMessage = 'Token requis'
        return
      }

      const success = await this.login(this.token)
      if (success) {
        this.$router.push('/')
      } else {
        this.errorMessage = 'Token invalide'
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
  }
}
</script>

<style scoped>
.font-monospace {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}
</style>