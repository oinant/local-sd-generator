<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-btn
              icon="mdi-arrow-left"
              variant="text"
              :to="{ name: 'SessionDetail', params: { name: sessionName } }"
            ></v-btn>
            <span class="ml-2">Images: {{ sessionName }}</span>
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Session images grid - Coming soon!
              <br /><br />
              Will display:
              <ul class="mt-2">
                <li>Image grid with thumbnails</li>
                <li>Bulk actions</li>
                <li>Filter/sort options</li>
                <li>Click to view image detail</li>
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
  name: 'SessionImagesView',
  computed: {
    sessionName() {
      return this.$route.params.name
    }
  }
}
</script>
