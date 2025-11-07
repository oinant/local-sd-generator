<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-btn icon="mdi-arrow-left" variant="text" :to="{name: 'SessionImages', params: {name: sessionName}}"></v-btn>
            <span class="ml-2">Image: {{ imageId }}</span>
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Image detail view - Coming soon!
              <br><br>
              Will display:
              <ul class="mt-2">
                <li>Full resolution image</li>
                <li>Metadata (seed, prompt, params)</li>
                <li>Actions (like, download, annotate)</li>
              </ul>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'ImageDetailView',
  computed: {
    sessionName() {
      return this.$route.params.name
    },
    imageId() {
      return this.$route.params.imageId
    }
  }
}
</script>
