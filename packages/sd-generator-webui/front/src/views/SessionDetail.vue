<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-btn icon="mdi-arrow-left" variant="text" :to="{name: 'Sessions'}"></v-btn>
            <span class="ml-2">Session: {{ sessionName }}</span>
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Session details view - Coming soon!
              <br><br>
              Will display:
              <ul class="mt-2">
                <li>Detailed statistics</li>
                <li>Editable tags</li>
                <li>Flags (test, failed, complete, liked)</li>
                <li>Quick navigation to images/rating</li>
              </ul>
            </v-alert>

            <div class="mt-4">
              <v-btn color="primary" :to="`/sessions/${sessionName}/images`" class="mr-2">
                <v-icon left>mdi-image-multiple</v-icon>
                View Images
              </v-btn>
              <v-btn color="secondary" :to="`/sessions/${sessionName}/rating`">
                <v-icon left>mdi-star</v-icon>
                Rate Variations
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
  name: 'SessionDetailView',
  computed: {
    sessionName() {
      return this.$route.params.name
    }
  }
}
</script>
