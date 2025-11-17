# Session Module Refactoring Plan

**Created:** 2025-11-17
**Status:** Planning
**Priority:** P6 (Medium - Nice-to-have)
**Component:** webui-front
**Area:** architecture

## Context

Le module Sessions est actuellement composé de 3 vues principales qui sont devenues trop volumineuses et mélangent plusieurs responsabilités :

| Vue | Lignes | État |
|-----|--------|------|
| `Images.vue` | 1463 | 🔴 Trop volumineux |
| `SessionDetail.vue` | 575 | 🟠 Acceptable mais peut être amélioré |
| `Sessions.vue` | 259 | 🟢 Taille correcte |
| `FilterDrawer.vue` | 165 | 🟢 Déjà extrait (composant) |

**Problèmes identifiés :**
- `Images.vue` contient trop de responsabilités (1463 lignes)
- Difficile à maintenir et tester
- Réutilisabilité limitée
- Performance : re-render du composant entier même pour changements locaux
- Complexité cognitive élevée

## Objectifs du Refactoring

### Bénéfices attendus

✅ **Maintenabilité** - Chaque composant a une responsabilité claire (Single Responsibility Principle)
✅ **Réutilisabilité** - Composants réutilisables dans d'autres contextes
✅ **Testabilité** - Tests unitaires plus faciles et ciblés
✅ **Performance** - Optimisation des re-renders (composants indépendants)
✅ **Lisibilité** - Fichiers plus petits (~200-400 lignes vs 1463 lignes)
✅ **Maintenabilité future** - Facilite l'ajout de nouvelles fonctionnalités

### Contraintes

- ⚠️ **Ne PAS casser les fonctionnalités existantes** (filters, lazy loading, routing)
- ⚠️ **Garder la même UX** (pas de changements visuels)
- ⚠️ **Compatibilité stores Pinia** (filtersStore, authStore, etc.)
- ⚠️ **Tester chaque phase** avant de passer à la suivante

## Architecture Proposée

### Phase 1 : Découpage Principal de `Images.vue`

**Principe :** Extraire 4 composants principaux depuis `Images.vue` (1463 lignes → ~300 lignes orchestrateur)

#### 1. `SessionList.vue` (~200-300 lignes)

**Responsabilités :**
- Liste des sessions avec `v-virtual-scroll`
- Sélection de session active
- Affichage métadonnées (date, nombre d'images, statut)
- Observer pour détecter nouvelles sessions

**Props :**
```typescript
{
  sessions: Array<Session>,           // Liste des sessions
  selectedSession: String | null,     // Session sélectionnée
  sessionMetadata: Object,            // Métadonnées { [sessionName]: { ... } }
  loading: Boolean                    // État de chargement
}
```

**Events :**
```typescript
@select-session(sessionName: string)  // Sélection d'une session
@refresh-sessions()                   // Demande de refresh
```

**Extrait de :**
- Template : Lignes ~40-100 (v-virtual-scroll + session items)
- Script : `selectSession()`, `loadSessions()`, `setupSessionObserver()`

---

#### 2. `ImageGallery.vue` (~400-500 lignes)

**Responsabilités :**
- Grille d'images avec lazy loading
- Intersection Observer pour thumbnails
- Gestion du clic sur image (ouverture dialog)
- Compteur d'images filtrées
- Toolbar avec actions (refresh, filter toggle)

**Props :**
```typescript
{
  images: Array<Image>,               // Images à afficher (filteredImages)
  sessionName: String,                // Nom de la session
  loading: Boolean,                   // État de chargement
  hasActiveFilters: Boolean           // Indicateur filtres actifs
}
```

**Events :**
```typescript
@open-image(image: Image)             // Ouverture du dialog image
@refresh-images()                     // Demande de refresh des images
@toggle-filters()                     // Toggle du drawer de filtres
```

**Extrait de :**
- Template : Lignes ~150-350 (v-container avec grille d'images)
- Script : `setupLazyLoading()`, `loadThumbnail()`, `openImageDialog()`

---

#### 3. `ImageDialog.vue` (~200-300 lignes)

**Responsabilités :**
- Dialog plein écran pour affichage image
- Navigation prev/next dans le subset filtré
- Affichage métadonnées (seed, variations, generation params)
- Actions (download, delete, close)
- Compteur de position (X / Y)

**Props :**
```typescript
{
  image: Image | null,                // Image courante
  images: Array<Image>,               // Toutes les images (pour navigation)
  visible: Boolean                    // Visibilité du dialog
}
```

**Events :**
```typescript
@close()                              // Fermeture du dialog
@navigate-next()                      // Navigation image suivante
@navigate-prev()                      // Navigation image précédente
@delete(image: Image)                 // Suppression d'une image
```

**Extrait de :**
- Template : Lignes ~400-700 (v-dialog avec contenu image)
- Script : `showNextImage()`, `showPreviousImage()`, `closeImageDialog()`

---

#### 4. `FilterDrawer.vue` (déjà extrait ✅)

**Responsabilités :**
- Drawer de filtres sur applied_variations
- Multi-sélection avec chips
- Intégration avec `filtersStore` (Pinia)

**État :** ✅ Déjà extrait (165 lignes)

**Location :** `src/components/FilterDrawer.vue`

---

#### 5. `Images.vue` (orchestrateur, ~300-400 lignes)

**Nouvelles responsabilités :**
- Orchestration des 4 composants enfants
- Gestion état global (`selectedSession`, `selectedImage`, `imageDialog`)
- Appels API (loadSessionImages, loadManifestForFilters)
- Gestion routing (lecture `$route.params.sessionName`)
- Computed properties (`filteredImages` depuis filtersStore)

**Structure template :**
```vue
<template>
  <v-container fluid>
    <!-- Session List (left sidebar) -->
    <SessionList
      :sessions="sessions"
      :selected-session="selectedSession"
      :session-metadata="sessionMetadata"
      :loading="loadingSessions"
      @select-session="selectSession"
      @refresh-sessions="loadSessions"
    />

    <!-- Image Gallery (main content) -->
    <ImageGallery
      v-if="selectedSession"
      :images="filteredImages"
      :session-name="selectedSession"
      :loading="loadingImages"
      :has-active-filters="filtersStore.hasActiveFilters"
      @open-image="openImageDialog"
      @refresh-images="refreshImages"
      @toggle-filters="toggleFilterDrawer"
    />

    <!-- Filter Drawer (right sidebar) -->
    <FilterDrawer
      v-if="selectedSession"
    />

    <!-- Image Dialog (fullscreen overlay) -->
    <ImageDialog
      :image="selectedImage"
      :images="filteredImages"
      :visible="imageDialog"
      @close="closeImageDialog"
      @navigate-next="showNextImage"
      @navigate-prev="showPreviousImage"
      @delete="deleteImage"
    />
  </v-container>
</template>
```

---

### Phase 2 : Sous-composants (optionnel, après Phase 1)

**Principe :** Extraire des sous-composants UNIQUEMENT si >50 lignes de logique dédiée

#### 2.1. `ImageDialogToolbar.vue` (~50-100 lignes)

**Responsabilités :**
- Barre d'actions du dialog (close, prev/next, download, delete)
- Affichage compteur position (X / Y)

**Condition d'extraction :** Si la toolbar fait >50 lignes

**Props :**
```typescript
{
  image: Image,
  currentIndex: number,
  totalImages: number,
  hasNext: boolean,
  hasPrev: boolean
}
```

**Events :**
```typescript
@close()
@navigate-next()
@navigate-prev()
@download()
@delete()
```

---

#### 2.2. `ImageMetadata.vue` (~80-150 lignes)

**Responsabilités :**
- Affichage structuré des métadonnées
- Seed, variations, generation params
- Formatage et présentation (chips, badges)

**Condition d'extraction :** Si l'affichage métadonnées fait >50 lignes

**Props :**
```typescript
{
  image: Image,
  metadata: Object  // Métadonnées complètes
}
```

---

#### 2.3. `GalleryToolbar.vue` (~50-80 lignes)

**Responsabilités :**
- Barre d'actions de la gallery (refresh, filter toggle)
- Compteur d'images (X images, Y filtrées)
- Actions bulk (select all, etc.)

**Condition d'extraction :** Si la toolbar fait >50 lignes

**Props :**
```typescript
{
  totalImages: number,
  filteredCount: number,
  hasActiveFilters: boolean,
  loading: boolean
}
```

**Events :**
```typescript
@refresh()
@toggle-filters()
```

---

#### 2.4. `SessionListItem.vue` (~30-50 lignes) [OPTIONNEL]

**Responsabilités :**
- Rendu d'un item de session
- Affichage métadonnées (date, images, statut)

**Condition d'extraction :** UNIQUEMENT si logique >50 lignes ou réutilisé ailleurs

**Props :**
```typescript
{
  session: Session,
  selected: boolean,
  metadata: Object
}
```

**Events :**
```typescript
@select()
```

---

### Phase 3 : Refactoring de `SessionDetail.vue` (optionnel)

**État actuel :** 575 lignes (🟠 acceptable mais peut être amélioré)

**Candidats d'extraction :**

#### 3.1. `SessionStatsCard.vue` (~150-200 lignes)

**Responsabilités :**
- Affichage statistiques de session
- Graphiques (completion, variations, etc.)
- Badges (seed sweep, model, etc.)

**Extrait de :** Template lignes ~45-200

---

#### 3.2. `SessionVariationsCard.vue` (~100-150 lignes)

**Responsabilités :**
- Tableau des variations utilisées
- Compteurs par placeholder
- Valeurs utilisées

**Extrait de :** Template lignes ~200-350

---

#### 3.3. `SessionToolbar.vue` (~50-80 lignes)

**Responsabilités :**
- Back button
- Titre session formaté
- Actions (refresh, view images, rate variations)

**Extrait de :** Template lignes ~4-42

---

## Règles de Découpage

### Créer un sous-composant SI :

1. **>50 lignes** de template/logique dédiée
2. **Réutilisable** dans 2+ endroits
3. **Testabilité** - Logique métier à isoler
4. **Clarté** - Améliore significativement la lisibilité

### NE PAS créer de sous-composant SI :

1. **<30 lignes** et logique triviale
2. **Fortement couplé** au parent (nécessite 5+ props)
3. **Une seule utilisation** et logique simple
4. **Overhead inutile** - Pas de bénéfice réel

---

## Plan d'Exécution

### Étape 1 : Phase 1 - Découpage Principal `Images.vue`

**Durée estimée :** 4-6h

**Ordre d'extraction :**

1. **ImageDialog.vue** (le plus isolé, facile à extraire)
   - Extraire template dialog (lignes ~400-700)
   - Extraire méthodes navigation (`showNextImage`, `showPreviousImage`, etc.)
   - Tester en isolation

2. **SessionList.vue** (bien délimité dans le template)
   - Extraire template liste sessions (lignes ~40-100)
   - Extraire `selectSession()`, `loadSessions()`, observer
   - Tester sélection + refresh

3. **ImageGallery.vue** (nécessite attention pour lazy loading)
   - Extraire grille d'images (lignes ~150-350)
   - Extraire `setupLazyLoading()`, `loadThumbnail()`, `openImageDialog()`
   - **CRITIQUE :** Tester Intersection Observer

4. **Nettoyage Images.vue** (devient l'orchestrateur)
   - Supprimer code extrait
   - Garder uniquement orchestration + API calls
   - Vérifier computed `filteredImages`
   - Tester routing + F5 refresh

**Critères de validation :**
- ✅ Toutes les fonctionnalités existantes marchent
- ✅ Filters fonctionnent (blonde hair → 6/73 images)
- ✅ Navigation prev/next respecte les filtres
- ✅ Lazy loading des thumbnails fonctionne
- ✅ Session dans l'URL (`/gallery/:sessionName`)
- ✅ F5 conserve la session sélectionnée
- ✅ Scrollbar de la liste de sessions visible

---

### Étape 2 : Phase 2 - Sous-composants (si nécessaire)

**Durée estimée :** 2-3h

**Déclencheurs :**
- Si `ImageDialog.vue` fait >300 lignes après extraction → Extraire `ImageDialogToolbar` + `ImageMetadata`
- Si `ImageGallery.vue` fait >500 lignes → Extraire `GalleryToolbar`
- Si `SessionList.vue` fait >300 lignes → Extraire `SessionListItem` (peu probable)

**Principe :** Attendre d'avoir fait Phase 1 et évaluer les besoins réels

---

### Étape 3 : Phase 3 - `SessionDetail.vue` (optionnel)

**Durée estimée :** 3-4h

**Condition :** Si Phase 1 + Phase 2 validées ET SessionDetail devient un problème de maintenance

**Ordre d'extraction :**
1. `SessionToolbar.vue` (facile, indépendant)
2. `SessionStatsCard.vue` (bien délimité)
3. `SessionVariationsCard.vue` (tableau variations)

---

## Priorisation

### P6 (Medium - Nice-to-have) : Phase 1 - `Images.vue`

**Justification :** 1463 lignes, complexité élevée, difficile à maintenir

**ROI :** Élevé (maintenabilité ++) / Effort moyen (4-6h)

### P8 (Low - Future) : Phase 2 - Sous-composants

**Justification :** Dépend des besoins réels après Phase 1

**ROI :** Moyen / Effort faible (2-3h)

### P9 (Low - Future) : Phase 3 - `SessionDetail.vue`

**Justification :** 575 lignes (acceptable), pas de problème urgent

**ROI :** Faible / Effort moyen (3-4h)

---

## Risques et Mitigation

### Risque 1 : Casser le lazy loading des thumbnails

**Probabilité :** Moyenne
**Impact :** Élevé (performance)

**Mitigation :**
- ✅ Tester Intersection Observer après extraction `ImageGallery.vue`
- ✅ Conserver exactement la même structure DOM (`data-src` attribute)
- ✅ Vérifier que `setupLazyLoading()` s'exécute au bon moment

---

### Risque 2 : Props drilling excessif

**Probabilité :** Moyenne
**Impact :** Moyen (lisibilité)

**Mitigation :**
- ✅ Utiliser Pinia stores pour état partagé (filtersStore déjà en place)
- ✅ Limiter props à 3-5 par composant
- ✅ Utiliser `provide/inject` si nécessaire pour éviter props drilling

---

### Risque 3 : Régression des filtres

**Probabilité :** Faible (FilterDrawer déjà extrait)
**Impact :** Élevé (fonctionnalité clé)

**Mitigation :**
- ✅ `filteredImages` reste computed dans `Images.vue` (orchestrateur)
- ✅ Passer `filteredImages` en prop à `ImageGallery` et `ImageDialog`
- ✅ Tester "blonde hair" → 6/73 images après refactoring

---

### Risque 4 : F5 casse la session sélectionnée

**Probabilité :** Faible (déjà fixé dans commit récent)
**Impact :** Moyen (UX)

**Mitigation :**
- ✅ Garder routing dans `Images.vue` (orchestrateur)
- ✅ `mounted()` lit `$route.params.sessionName`
- ✅ `selectSession()` utilise `this.$router.push()`
- ✅ Tester F5 après chaque phase

---

## Success Criteria

### Phase 1 (Must Have)

- ✅ `Images.vue` réduit à ~300-400 lignes (vs 1463)
- ✅ 4 composants créés (`SessionList`, `ImageGallery`, `ImageDialog`, `FilterDrawer` ✅)
- ✅ Tous les tests de non-régression passent :
  - Sélection session
  - Affichage images + lazy loading
  - Filtres (blonde hair → 6/73)
  - Navigation prev/next respecte filtres
  - Session dans URL (`/gallery/:sessionName`)
  - F5 conserve session
  - Scrollbar liste sessions
- ✅ Aucune régression visuelle (même UX)

### Phase 2 (Should Have)

- ✅ Sous-composants extraits UNIQUEMENT si >50 lignes
- ✅ Pas de props drilling excessif (<5 props par composant)

### Phase 3 (Nice to Have)

- ✅ `SessionDetail.vue` réduit à ~200-300 lignes (vs 575)
- ✅ 3 composants créés (`SessionToolbar`, `SessionStatsCard`, `SessionVariationsCard`)

---

## Tests à Effectuer

### Tests de Non-Régression (Phase 1)

**1. Session Selection**
- [ ] Cliquer sur session → charge les images
- [ ] URL change → `/gallery/:sessionName`
- [ ] F5 → session reste sélectionnée

**2. Image Display**
- [ ] Images s'affichent avec thumbnails
- [ ] Lazy loading fonctionne (scroll → charge thumbnails)
- [ ] Placeholders gris avant chargement

**3. Filters**
- [ ] Ouvrir drawer filtres → liste des variations
- [ ] Sélectionner "blonde hair" → 6/73 images
- [ ] Compteur "6 / 73" affiché
- [ ] Clear filters → retour 73/73 images

**4. Image Dialog**
- [ ] Cliquer image → ouvre dialog
- [ ] Navigation prev/next fonctionne
- [ ] Compteur "X / Y" correct (Y = filtered count)
- [ ] ESC ferme le dialog

**5. Navigation with Filters**
- [ ] Avec filtre actif (6 images) :
  - [ ] Prev/next navigue dans les 6 images filtrées
  - [ ] Compteur "1 / 6", "2 / 6", etc.
  - [ ] Pas d'images non-filtrées affichées

**6. Scrollbar**
- [ ] Liste sessions a scrollbar visible
- [ ] Scroll fonctionne (`v-virtual-scroll`)

---

## Documentation

### À Créer

- [ ] `docs/webapp/architecture/components-hierarchy.md` - Hiérarchie des composants
- [ ] `docs/webapp/technical/lazy-loading-strategy.md` - Stratégie lazy loading
- [ ] `docs/webapp/usage/session-module-guide.md` - Guide utilisateur module Sessions

### À Mettre à Jour

- [ ] `CLAUDE.md` - Ajouter section sur architecture composants
- [ ] `README.md` (webui) - Mettre à jour structure projet

---

## Commits Recommandés

**Phase 1 :**
```bash
git commit -m "refactor(webui): Extract ImageDialog component from Images.vue"
git commit -m "refactor(webui): Extract SessionList component from Images.vue"
git commit -m "refactor(webui): Extract ImageGallery component from Images.vue"
git commit -m "refactor(webui): Clean up Images.vue orchestrator"
```

**Phase 2 :**
```bash
git commit -m "refactor(webui): Extract ImageDialogToolbar sub-component"
git commit -m "refactor(webui): Extract ImageMetadata sub-component"
git commit -m "refactor(webui): Extract GalleryToolbar sub-component"
```

**Phase 3 :**
```bash
git commit -m "refactor(webui): Extract SessionToolbar component"
git commit -m "refactor(webui): Extract SessionStatsCard component"
git commit -m "refactor(webui): Extract SessionVariationsCard component"
```

---

## Notes Additionnelles

### Avantages Mesurables

| Métrique | Avant | Après (Phase 1) | Gain |
|----------|-------|----------------|------|
| Lignes `Images.vue` | 1463 | ~300-400 | -72% |
| Composants réutilisables | 1 | 4 | +300% |
| Complexité cognitive | Élevée | Faible | ++ |
| Temps ajout feature | ~2h | ~30min | -75% |
| Tests unitaires possibles | Difficile | Facile | ++ |

### Principe Général : KISS (Keep It Simple, Stupid)

**Règle d'or :** Ne pas sur-découper. Mieux vaut **4 composants bien pensés** que **10 composants micro** qui ajoutent de la complexité sans bénéfice.

**Décision :** Attendre Phase 1 complète avant de décider Phase 2/Phase 3.

---

## Changelog

**2025-11-17 13:42:50**
- Création du document de planning
- Définition architecture 3 phases
- Priorisation P6 (Phase 1), P8 (Phase 2), P9 (Phase 3)
- Success criteria et tests définis
