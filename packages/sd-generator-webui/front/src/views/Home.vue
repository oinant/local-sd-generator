<template>
  <v-container fluid>
    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 mb-2">🎨 SD Image Generator</h1>
        <p class="text-subtitle-1 text-medium-emphasis">
          Bienvenue dans l'interface de génération d'images Stable Diffusion
        </p>
      </v-col>
    </v-row>

    <!-- Global Stats (Placeholder) -->
    <v-row class="mt-4">
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">Total Sessions</div>
            <div class="text-h4">-</div>
            <div class="text-caption text-medium-emphasis">Coming soon</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">Total Images</div>
            <div class="text-h4">-</div>
            <div class="text-caption text-medium-emphasis">Coming soon</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">Storage Used</div>
            <div class="text-h4">-</div>
            <div class="text-caption text-medium-emphasis">Coming soon</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-overline mb-1">Liked Sessions</div>
            <div class="text-h4">-</div>
            <div class="text-caption text-medium-emphasis">Coming soon</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="mt-6">
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Quick Actions</h2>
      </v-col>
      <v-col cols="12" md="4">
        <v-card :to="{name: 'Sessions'}" hover>
          <v-card-title>
            <v-icon class="mr-2">mdi-folder-multiple</v-icon>
            Browse Sessions
          </v-card-title>
          <v-card-text>
            View and manage all your generation sessions with detailed statistics
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card :to="{name: 'Generate'}" hover>
          <v-card-title>
            <v-icon class="mr-2">mdi-creation</v-icon>
            New Generation
          </v-card-title>
          <v-card-text>
            Start a new image generation session
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card :to="{name: 'Gallery'}" hover>
          <v-card-title>
            <v-icon class="mr-2">mdi-image-multiple</v-icon>
            Gallery
          </v-card-title>
          <v-card-text>
            Browse images from all sessions
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Liked (Placeholder) -->
    <v-row class="mt-6">
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Recently Liked</h2>
        <v-alert type="info" variant="tonal">
          Recently liked sessions and images will appear here (coming soon with Session Stats Dashboard feature)
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'HomeView'
}
</script>