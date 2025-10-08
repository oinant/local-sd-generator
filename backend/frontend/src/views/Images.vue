<template>
  <v-container fluid class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Panneau latéral avec treeview -->
      <v-col cols="3" class="border-r">
        <v-card flat height="100vh" class="overflow-auto">
          <v-card-title>
            <v-icon left>mdi-folder-outline</v-icon>
            Structure des fichiers
          </v-card-title>
          <v-card-text class="pa-2">
            <v-progress-linear v-if="loading" indeterminate class="mb-2" />
            <v-treeview
              :items="[fileTree]"
              v-model:opened="openNodes"
              item-key="id"
              item-title="name"
              item-children="children"
              density="compact"
              :load-children="loadTreeChildren"
            >
              <template v-slot:prepend="{ item }">
                <v-icon v-if="item.type === 'folder'">
                  {{ openNodes.includes(item.id) ? 'mdi-folder-open' : 'mdi-folder' }}
                </v-icon>
                <v-icon v-else-if="item.type === 'root'">
                  mdi-folder-multiple
                </v-icon>
              </template>
              <template v-slot:label="{ item }">
                <span
                  @click.stop="onLabelClick(item)"
                  style="cursor: pointer"
                >
                  {{ item.name }}
                </span>
                <v-chip
                  v-if="item.imageCount"
                  x-small
                  class="ml-2"
                  color="primary"
                >
                  {{ item.imageCount }}
                </v-chip>
                <v-chip
                  v-if="item.sessionCount"
                  x-small
                  class="ml-2"
                  color="info"
                >
                  {{ item.sessionCount }} sessions
                </v-chip>
              </template>
            </v-treeview>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Zone principale avec galerie -->
      <v-col cols="9">
        <v-card flat height="100vh" class="overflow-auto">
          <v-card-title>
            <v-icon left>mdi-image-multiple</v-icon>
            {{ selectedPath || 'Toutes les images' }}
            <v-spacer />
            <v-chip color="info" outlined>
              {{ filteredImages.length }} image{{ filteredImages.length > 1 ? 's' : '' }}
            </v-chip>
          </v-card-title>

          <v-card-text>
            <!-- Zone de galerie (placeholder pour l'instant) -->
            <div v-if="filteredImages.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey lighten-2">mdi-image-off-outline</v-icon>
              <p class="text-h6 grey--text mt-4">
                {{ selectedPath ? 'Aucune image dans ce dossier' : 'Aucune image générée' }}
              </p>
            </div>

            <v-container v-else fluid>
              <v-row>
                <v-col
                  v-for="image in filteredImages"
                  :key="image.id"
                  cols="12" sm="6" md="4" lg="3"
                >
                  <v-card outlined hover class="image-card">
                    <v-img
                      :src="image.thumbnail || image.url"
                      :aspect-ratio="1"
                      cover
                      @click="openImageDialog(image)"
                      class="cursor-pointer"
                    >
                      <template v-slot:placeholder>
                        <v-row class="fill-height ma-0" align="center" justify="center">
                          <v-progress-circular indeterminate color="grey lighten-5" />
                        </v-row>
                      </template>
                    </v-img>
                    <v-card-subtitle class="text-caption">
                      {{ image.name }}
                    </v-card-subtitle>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog pour agrandir l'image -->
    <v-dialog v-model="imageDialog" max-width="90vw">
      <v-card v-if="selectedImage">
        <v-card-title class="d-flex justify-space-between">
          {{ selectedImage.name }}
          <v-btn icon @click="imageDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <v-img :src="selectedImage.url" contain max-height="70vh" />
        </v-card-text>
        <v-card-actions>
          <v-chip small color="info">{{ selectedImage.session }}</v-chip>
          <v-chip small color="success">{{ formatDate(selectedImage.created) }}</v-chip>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import ApiService from '@/services/api'

export default {
  name: 'ImagesView',

  data() {
    return {
      openNodes: ['root'],
      selectedPath: null,
      imageDialog: false,
      selectedImage: null,
      loading: false,
      fileTree: {},
      allImages: []
    }
  },

  computed: {
    filteredImages() {
      if (!this.selectedPath) {
        return this.allImages
      }
      return this.allImages.filter(image => image.path === this.selectedPath)
    }
  },

  async mounted() {
    await this.loadFileTree()
    // Ne plus charger automatiquement les images - attendre la sélection d'un dossier
  },

  methods: {
    async loadFileTree() {
      try {
        this.loading = true
        this.fileTree = await ApiService.getFileTree()

        // Ouvre automatiquement la racine
        this.openNodes = ['root']
      } catch (error) {
        console.error('Erreur lors du chargement du treeview:', error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors du chargement de la structure de fichiers',
          color: 'error'
        })
      } finally {
        this.loading = false
      }
    },

    async loadTreeChildren(item) {
      // Ne charge que si le nœud a des enfants potentiels
      if (!item.hasChildren) {
        return
      }

      // Si déjà chargé, on ignore
      if (item.children && item.children.length > 0) {
        return
      }

      try {
        console.log('Fetching children from API for path:', item.path)
        // Charge les enfants du dossier
        const children = await ApiService.getFileTree(item.path)
        console.log('API response:', children)

        // Met à jour le nœud avec ses enfants
        // L'API retourne soit un tableau directement, soit un objet avec une propriété children
        const childrenArray = Array.isArray(children) ? children : (children.children || [])
        console.log('Setting children array:', childrenArray)

        // Important: retourner les enfants pour que Vuetify les gère
        return childrenArray

      } catch (error) {
        console.error('Erreur lors du chargement des sous-dossiers:', error)
        this.$store.dispatch('showSnackbar', {
          message: `Erreur lors du chargement du dossier ${item.name}`,
          color: 'error'
        })
        return []
      }
    },

    async loadImages(path = null) {
      try {
        this.loading = true
        const images = await ApiService.getFileImages(path)
        this.allImages = images.map(image => ({
          ...image,
          created: new Date(image.created * 1000), // Conversion timestamp
          modified: new Date(image.modified * 1000),
          // Utilise l'URL fournie par l'API
          thumbnail: image.url // Pas de thumbnail séparée pour l'instant
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des images:', error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors du chargement des images',
          color: 'error'
        })
      } finally {
        this.loading = false
      }
    },

    async onLabelClick(item) {
      console.log('Label clicked:', item.name, 'path:', item.path)

      // Charge les images pour ce dossier
      if (item.path) {
        console.log('Loading images for path:', item.path)
        this.selectedPath = item.path
        await this.loadImages(item.path)
      }
    },

    onNodeExpand(item) {
      console.log('Node expanded:', item.name, 'hasChildren:', item.hasChildren)
      // L'expansion est gérée automatiquement par load-children
    },

    findNodeById(id, nodes = [this.fileTree]) {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = this.findNodeById(id, node.children)
          if (found) return found
        }
      }
      return null
    },

    openImageDialog(image) {
      this.selectedImage = image
      this.imageDialog = true
    },

    formatDate(date) {
      return new Intl.DateTimeFormat('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      }).format(date)
    }
  }
}
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(0,0,0,0.12);
}

.cursor-pointer {
  cursor: pointer;
}

.image-card:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease-in-out;
}
</style>