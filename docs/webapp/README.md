# WebUI Documentation

Documentation complète du frontend Vue3/Vuetify de la WebUI SD Generator.

---

## 📚 Documents Disponibles

### 1. [Frontend Architecture Audit](./frontend-architecture-audit.md)

**Audit complet de l'architecture actuelle**

- État actuel (forces/faiblesses)
- Problèmes identifiés par priorité (P1-P3)
- Métriques détaillées
- Patterns & anti-patterns
- Vue3 & Composition API analysis
- Vuetify best practices
- Performance analysis
- Architecture cible proposée
- Plan de refactoring (5 phases)
- Métriques de succès
- Risques & mitigations

**Qui devrait lire :** Toute l'équipe dev frontend, lead dev, product owner

**Quand :** Avant de commencer le refactoring

---

### 2. [Refactoring Plan](./refactoring-plan.md)

**Guide pratique avec exemples de code pour chaque phase**

- Phase 1: Quick Wins (1-2 jours)
  - Extraire formatters
  - Migrer Vuex → Pinia
  - Ajouter virtual scrolling
  - Setup ESLint + Prettier
  - Setup Vitest

- Phase 2: Composables Extraction (3-5 jours)
  - `useSessionPolling()`
  - `useImagePolling()`
  - `useImageLazyLoad()`
  - `useSessionFilters()`
  - `useKeyboardNav()`
  - `useImageDialog()`

- Phase 3: Component Splitting (5-7 jours)
  - `SessionList.vue`
  - `ImageGrid.vue`
  - `ImageDialog.vue`
  - `ImageFullscreen.vue`
  - `ImageMetadata.vue`

- Phase 4: Store Refactoring (2-3 jours)
  - `stores/sessions.js`
  - `stores/images.js`

- Phase 5: Tests & Optimization (3-5 jours)
  - Tests E2E Playwright
  - Performance audit
  - Accessibilité

**Qui devrait lire :** Devs qui implémentent le refactoring

**Quand :** Pendant l'implémentation (référence)

---

### 3. [Architecture Diagrams](./architecture-diagrams.md)

**Visualisations de l'architecture avant/après**

- Component Tree (avant/après)
- Data Flow diagrams
- Responsabilités par layer
- Composables dependency graph
- Component communication patterns
- State management (Pinia stores)
- Lazy loading strategy
- Polling architecture
- Testing pyramid
- Performance metrics
- Migration path

**Qui devrait lire :** Toute l'équipe (visualisations)

**Quand :** Pour comprendre la vision globale

---

### 4. [Quick Wins Implementation](./quick-wins-implementation.md)

**Guide pas-à-pas pour démarrer immédiatement**

- Quick Win 1: Extraire formatters (~30 min)
- Quick Win 2: Setup Vitest (~2h)
- Quick Win 3: Migrer Vuex → Pinia (~2h)
- Quick Win 4: Virtual Scrolling (~3h)
- Quick Win 5: ESLint + Prettier (~1h)

**Total:** ~8-10h, risque faible, gains immédiats

**Qui devrait lire :** Dev qui commence le refactoring

**Quand :** Maintenant ! (première étape)

---

## 🎯 Par Où Commencer ?

### Si vous êtes...

**Lead Dev / Architecte**
1. Lire [Architecture Audit](./frontend-architecture-audit.md) (30 min)
2. Lire [Architecture Diagrams](./architecture-diagrams.md) (15 min)
3. Valider l'approche avec l'équipe

**Dev Frontend (implémentation)**
1. Lire [Quick Wins](./quick-wins-implementation.md) (10 min)
2. Appliquer Phase 1 Quick Wins (8-10h)
3. Référer à [Refactoring Plan](./refactoring-plan.md) pour Phases 2-5

**Product Owner**
1. Lire Executive Summary de [Architecture Audit](./frontend-architecture-audit.md) (5 min)
2. Lire section "Métriques de Succès" (5 min)
3. Lire section "ROI Estimé" (5 min)

**QA / Testeur**
1. Lire section "Tests Strategy" de [Architecture Audit](./frontend-architecture-audit.md)
2. Lire Phase 5 de [Refactoring Plan](./refactoring-plan.md)
3. Préparer les tests E2E Playwright

---

## 📊 Résumé Exécutif

### Problèmes Critiques

🔴 **God Component** - `Images.vue` (1366 lignes) avec 13+ responsabilités
🔴 **Logique métier dans UI** - Business logic mélangée avec présentation
🔴 **État local massif** - 20+ data properties, state anarchique

### Solution Proposée

✅ **Composables** - Extraire business logic (6 composables)
✅ **Component Splitting** - Diviser en composants atomiques (8 composants)
✅ **Pinia Stores** - État global modulaire (4 stores)
✅ **Tests** - 50+ tests unitaires + intégration + E2E
✅ **Performance** - Virtual scroll, lazy load, memoization

### Timeline & Effort

| Phase | Durée | Effort | Risque |
|-------|-------|--------|--------|
| Phase 1: Quick Wins | 1-2 jours | ~10h | 🟢 Faible |
| Phase 2: Composables | 3-5 jours | ~17h | 🟡 Moyen |
| Phase 3: Components | 5-7 jours | ~21h | 🟠 Moyen-Haut |
| Phase 4: Stores | 2-3 jours | ~9h | 🟡 Moyen |
| Phase 5: Tests | 3-5 jours | ~28h | 🟢 Faible |
| **TOTAL** | **~3-4 semaines** | **~85h** | 🟡 Gérable |

### ROI Estimé

**Investissement:** ~85h (3-4 semaines)

**Gains:**
- 🟢 **Maintenabilité:** +300% (1366 lignes → 150 lignes par composant)
- 🟢 **Testabilité:** +∞% (0 tests → 50+ tests)
- 🟢 **Vélocité:** +50% (ajout features 2× plus rapide)
- 🟢 **Bugs:** -70% (détection précoce par tests)
- 🟢 **Performance:** +40% (virtual scroll + optimisations)

---

## 📁 Structure des Documents

```
docs/webapp/
├── README.md                              (ce fichier)
├── frontend-architecture-audit.md         (audit complet)
├── refactoring-plan.md                    (plan détaillé)
├── architecture-diagrams.md               (visualisations)
└── quick-wins-implementation.md           (guide de démarrage)
```

---

## 🔗 Liens Utiles

### Documentation Externe

- [Vue 3 Documentation](https://vuejs.org/)
- [Vuetify 3 Documentation](https://vuetifyjs.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Vue Virtual Scroller](https://github.com/Akryum/vue-virtual-scroller)

### Documentation Interne

- [CLI Documentation](../cli/) - Documentation du CLI Python
- [API Documentation](../backend/) - Documentation de l'API FastAPI
- [Roadmap](../roadmap/) - Planning des features

---

## 📝 Conventions de Code

### Vue Components

```vue
<!-- ✅ BON : Composition API avec <script setup> -->
<script setup>
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>

<!-- ❌ MAUVAIS : Options API (ancien style) -->
<script>
export default {
  data() {
    return { count: 0 }
  },
  computed: {
    doubled() {
      return this.count * 2
    }
  }
}
</script>
```

### Composables

```javascript
// ✅ BON : Préfixe "use", retourne état + actions
export function useSessionPolling(options) {
  const sessions = ref([])
  const loading = ref(false)

  async function loadSessions() {
    // ...
  }

  return {
    sessions,
    loading,
    loadSessions
  }
}
```

### Stores Pinia

```javascript
// ✅ BON : defineStore avec actions asynchrones
export const useSessionStore = defineStore('sessions', {
  state: () => ({
    sessions: []
  }),

  actions: {
    async loadSessions() {
      this.sessions = await ApiService.getSessions()
    }
  }
})
```

### Tests

```javascript
// ✅ BON : Tests descriptifs avec AAA pattern
describe('useSessionPolling', () => {
  test('loads and formats sessions correctly', async () => {
    // Arrange
    ApiService.getSessions.mockResolvedValue({ sessions: [...] })

    // Act
    const { sessions, loadSessions } = useSessionPolling()
    await loadSessions()

    // Assert
    expect(sessions.value).toHaveLength(10)
    expect(sessions.value[0]).toMatchObject({ name: '...', displayName: '...' })
  })
})
```

---

## 🤝 Contribution

### Workflow de Développement

1. **Créer une branche feature**
   ```bash
   git checkout -b feature/extract-composables
   ```

2. **Développer avec TDD**
   - Écrire le test d'abord
   - Implémenter la feature
   - Refactor si nécessaire

3. **Valider avant commit**
   ```bash
   npm run lint:fix
   npm run test
   npm run format
   ```

4. **Commit avec message conventionnel**
   ```bash
   git commit -m "feat(composables): extract useSessionPolling composable

   - Extract session polling logic from Images.vue
   - Add unit tests (100% coverage)
   - Update Images.vue to use composable

   Closes #123"
   ```

5. **Push et créer PR**
   ```bash
   git push origin feature/extract-composables
   ```

### Code Review Checklist

- [ ] Tests ajoutés/modifiés et passent
- [ ] Lint passe (0 erreurs/warnings)
- [ ] Coverage maintenue (>80%)
- [ ] Documentation mise à jour (JSDoc)
- [ ] Pas de régression fonctionnelle
- [ ] Performance non dégradée

---

## 📞 Support

### Questions ?

- **Architecture** → Voir [Architecture Audit](./frontend-architecture-audit.md)
- **Implémentation** → Voir [Refactoring Plan](./refactoring-plan.md)
- **Quick Start** → Voir [Quick Wins](./quick-wins-implementation.md)

### Issues

Pour reporter un bug ou proposer une feature :
- GitHub Issues : https://github.com/oinant/local-sd-generator/issues

---

**Dernière mise à jour:** 2025-11-07
**Version:** 1.0
**Auteur:** Claude Code
