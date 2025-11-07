<template>
  <v-app>
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="drawer"
      app
      :permanent="$vuetify.display.mdAndUp"
      :temporary="!$vuetify.display.mdAndUp"
      width="260"
    >
      <!-- Header compact avec titre et infos -->
      <v-list-item class="pa-3">
        <v-list-item-title class="text-h6">
          🎨 SD Generator
        </v-list-item-title>
        <v-list-item-subtitle class="mt-1">
          <v-chip
            v-if="user"
            color="secondary"
            size="x-small"
            class="mr-1"
          >
            <v-icon size="x-small" class="mr-1">
              {{ user.is_admin ? 'mdi-crown' : user.can_generate ? 'mdi-account' : 'mdi-eye' }}
            </v-icon>
            {{ user.is_admin ? 'Admin' : user.can_generate ? 'Gen' : 'RO' }}
          </v-chip>
          <v-chip
            size="x-small"
            variant="outlined"
            :title="'Build: ' + buildTimestamp"
          >
            <v-icon size="x-small" class="mr-1">mdi-clock-outline</v-icon>
            {{ buildInfo }}
          </v-chip>
        </v-list-item-subtitle>
      </v-list-item>

      <v-divider />

      <v-list density="compact">
        <v-list-item
          v-for="item in menuItems"
          :key="item.title"
          :to="item.route"
          :disabled="item.disabled"
        >
          <template v-slot:prepend>
            <v-icon>{{ item.icon }}</v-icon>
          </template>
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>

      <template v-slot:append>
        <div class="pa-2">
          <v-btn
            block
            color="error"
            @click="logout"
          >
            <v-icon left>mdi-logout</v-icon>
            Déconnexion
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar
      v-if="isAuthenticated && !$vuetify.display.mdAndUp"
      app
      color="primary"
      dark
      density="compact"
    >
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title class="text-subtitle-1">🎨 SD Generator</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>

    <!-- Snackbar global -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      top
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="hideSnackbar"
        >
          Fermer
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Loading overlay -->
    <v-overlay v-model="loading" class="align-center justify-center">
      <v-progress-circular
        color="primary"
        indeterminate
        size="64"
      ></v-progress-circular>
    </v-overlay>
  </v-app>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'App',

  data() {
    return {
      drawer: true,
    }
  },

  computed: {
    ...mapGetters(['isAuthenticated', 'user', 'loading', 'snackbar', 'canGenerate']),

    buildTimestamp() {
      return __BUILD_TIMESTAMP__
    },

    buildInfo() {
      // Format: "2 nov. 13:05"
      const date = new Date(__BUILD_TIMESTAMP__)
      return new Intl.DateTimeFormat('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    },

    menuItems() {
      const items = [
        {
          title: 'Accueil',
          icon: 'mdi-home',
          route: '/',
          disabled: false
        },
        {
          title: 'Galerie',
          icon: 'mdi-image-multiple',
          route: '/images',
          disabled: false
        },
        {
          title: 'Générer',
          icon: 'mdi-creation',
          route: '/generate',
          disabled: !this.canGenerate
        },
        {
          title: 'Jobs',
          icon: 'mdi-cog',
          route: '/jobs',
          disabled: false
        }
      ]

      return items
    }
  },

  methods: {
    ...mapActions(['logout', 'hideSnackbar']),

    async logout() {
      await this.$store.dispatch('logout')
      this.$router.push('/login')
    }
  },

  async created() {
    // Vérifier si un token existe au démarrage
    const token = localStorage.getItem('authToken')
    if (token && !this.isAuthenticated) {
      await this.$store.dispatch('login', token)
      if (!this.isAuthenticated) {
        this.$router.push('/login')
      }
    } else if (!this.isAuthenticated) {
      this.$router.push('/login')
    }
  }
}
</script>

<style>
.v-application {
  font-family: 'Roboto', sans-serif !important;
}
</style>