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
            <span class="ml-2">Variation Rating: {{ sessionName }}</span>
          </v-card-title>

          <v-card-text>
            <v-alert type="info" variant="tonal">
              Variation Impact Rating - Coming soon!
              <br /><br />
              For seed-sweep sessions, will allow:
              <ul class="mt-2">
                <li>Rate each variation: "As Intended" / "No Effect" / "Unintended Effect"</li>
                <li>Add notes for unintended effects</li>
                <li>Bulk action: "Mark all as intended"</li>
              </ul>
            </v-alert>

            <v-alert type="warning" variant="tonal" class="mt-4">
              <strong>Note:</strong> This feature requires the session to be a seed-sweep session.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'SessionRatingView',
  computed: {
    sessionName() {
      return this.$route.params.name
    }
  }
}
</script>
