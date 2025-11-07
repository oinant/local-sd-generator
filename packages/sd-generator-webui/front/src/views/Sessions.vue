<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-folder-multiple</v-icon>
            Sessions
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Session management dashboard - Coming soon!
              <br><br>
              Features:
              <ul class="mt-2">
                <li>Master/details layout</li>
                <li>Session statistics (model, images, placeholders)</li>
                <li>Editable tags and metadata</li>
                <li>Filters (seed-sweep, liked, complete)</li>
              </ul>
            </v-alert>

            <div class="mt-4">
              <v-btn color="primary" to="/gallery">
                View Legacy Gallery
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'SessionsView'
}
</script>
