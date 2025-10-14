# 📊 Audit Documentation CLI - Plan d'Action

**Date de l'audit :** 2025-10-14
**Status :** En cours
**Objectif :** Nettoyer la documentation avant traduction anglaise

---

## 🎯 Vue d'ensemble

### Statistiques
- **Total fichiers docs** : 69 fichiers Markdown
- **À supprimer/archiver** : 6-8 fichiers (specs redondantes + obsolètes V1)
- **À créer** : 4-5 nouveaux fichiers (architecture V2, guides utilisateur)
- **Gain estimé** : -11% de fichiers, clarification V1/V2

### État du système
- **CLI actif** : V2.0 uniquement (V1 legacy supprimé du code)
- **Tests** : 306 total (98% pass rate)
- **Template System** : V2.0 avec inheritance, imports, chunks, selectors

---

## 📁 INVENTAIRE DES FICHIERS

### Documentation CLI (10 fichiers)
```
docs/cli/
├── README.md
├── usage/
│   ├── getting-started.md
│   ├── variation-files.md
│   ├── negative-prompt-variations.md
│   ├── yaml-templating-guide.md
│   ├── examples.md
│   └── adetailer.md
└── technical/
    ├── architecture.md                    ⚠️  OBSOLETE - À archiver
    ├── design-decisions.md
    ├── yaml-templating-system.md          ✅  ACTUEL V2.0
    ├── v2-templating-engine.md            ❌  DEPRECATED - À archiver
    ├── output-system.md
    ├── config-system.md
    ├── error-handling-validation.md
    ├── adetailer.md
    └── manifest_v2_format.md
```

### Documentation Roadmap (47 fichiers)
```
docs/roadmap/
├── README.md
├── braindump.md
├── templateSpec.md                        ❌  Workshop - À archiver
├── template-system-v2-spec.md             ❌  Ancienne spec - À archiver
├── FIX_TEMPLATING_V2.0_SPEC.md           ✅  SPEC FINALE (à renommer)
├── FIX_TEMPLATING_V2.0_DELTA.md          ❌  Delta file - À supprimer
├── done/ (9 fichiers)                     ✅  Features terminées
├── next/ (3 fichiers)                     ✅  Prochaines features
├── future/ (14 fichiers)                  ✅  Backlog futur
└── archive/ (7 fichiers)                  ✅  Déjà archivé
```

### Documentation Tooling (6 fichiers)
```
docs/tooling/
├── README.md
├── CODE_REVIEW_GUIDELINES.md
├── CODE_REVIEW_ACTION_TEMPLATES.md
├── NEXT_SESSION_PROMPT.md
├── srp_analysis_2025-10-06.md
├── code_review_2025-10-06.md
└── automated_metrics_2025-10-06.md
```

---

## 🗑️ FICHIERS À SUPPRIMER/ARCHIVER

### Priorité 1 : CRITIQUE (specs redondantes)

#### ❌ `/docs/roadmap/templateSpec.md` (1275 lignes)
- **Raison** : Workshop/brainstorming session, pas une spec finale
- **Contenu** : Q&A sur la syntaxe, clarifications, 5 passes de discussion
- **Action** : Archiver dans `/docs/roadmap/archive/`
- **Status** : [ ] TODO

#### ✅ `/docs/roadmap/FIX_TEMPLATING_V2.0_SPEC.md` → RENOMMER (904 lignes)
- **Décision** : ✅ C'est LA SEULE spec à garder (version finale corrigée)
- **Action** :
  1. Renommer en `template-system-spec.md` (nom plus clair)
  2. Archiver l'ancien `template-system-v2-spec.md` (obsolète)
- **Raison** : Version finale avec Template Method Pattern, `prompt:` vs `template:`
- **Status** : [ ] TODO

#### ❌ `/docs/roadmap/template-system-v2-spec.md` (1030 lignes)
- **Raison** : Ancienne version de la spec, remplacée par FIX_TEMPLATING_V2.0_SPEC.md
- **Action** : Archiver dans `/docs/roadmap/archive/template-system-v2-spec-OLD.md`
- **Status** : [ ] TODO

#### ❌ `/docs/roadmap/FIX_TEMPLATING_V2.0_DELTA.md`
- **Raison** : Delta file entre deux versions de spec (plus nécessaire)
- **Action** : Supprimer
- **Status** : [ ] TODO

### Priorité 2 : HAUTE (documentation obsolète V1)

#### ❌ `/docs/cli/technical/v2-templating-engine.md` (600 lignes)
- **Status dans le fichier** : Marqué **DEPRECATED** (ligne 3)
- **Contenu** : Documentation du système Phase 2 (ancien)
- **Remplacé par** : `/docs/cli/technical/yaml-templating-system.md`
- **Action** : Déplacer dans `/docs/roadmap/archive/v2-templating-engine-deprecated.md`
- **Status** : [ ] TODO

#### ❌ `/docs/cli/technical/architecture.md` (645 lignes)
- **Raison** : Décrit architecture obsolète (ImageVariationGenerator, config_schema.py, structure ancienne)
- **Problèmes** :
  - Parle de Phase 1, Phase 2, Phase 3 (obsolète)
  - Mentionne des modules qui n'existent plus
- **Action** : Renommer en `architecture-legacy.md` + archiver
- **Status** : [ ] TODO

#### ⚠️ `/docs/MIGRATION_PLAN.md`
- **Action** : Vérifier si migration V1→V2 terminée (98% tests OK)
- **Si terminée** : Archiver
- **Status** : [ ] TODO - Vérification requise

### Priorité 3 : MOYENNE (roadmap cleanup)

#### ✅ `/docs/roadmap/done/` (9 fichiers)
**Action** : Vérifier que toutes les features sont vraiment terminées

- [ ] `add-scheduler-parameter.md` - ✅ Terminé (scheduler dans CLI)
- [ ] `bug-output-dir-not-used.md` - ⚠️ Vérifier
- [ ] `bug-random-mode-no-randomness.md` - ⚠️ Vérifier
- [ ] `chore_refactor_sdapi_client_session_dir.md` - ⚠️ Vérifier
- [ ] `chore_refactor_sdapi_client_srp.md` - ⚠️ Vérifier
- [ ] `feature-negative-prompt-placeholders.md` - ⚠️ Vérifier
- [ ] `json-config-phase2.md` - ⚠️ Vérifier
- [ ] `json-config-phase3.md` - ⚠️ Vérifier
- [ ] `refactor-cli-with-typer.md` - ✅ Terminé (Typer actif)
- [ ] `templating-phase2-characters.md` - ⚠️ Vérifier
- [ ] `adetailer-integration.md` - ✅ Terminé (ADetailer fonctionnel)
- [ ] `manifest_v2_snapshot.md` - ✅ Terminé (Manifest V2 actif)

---

## 📝 FICHIERS À CRÉER

### Documentation manquante

#### 🆕 `/docs/cli/technical/architecture-v2.md`
**Contenu** :
- Structure de `CLI/src/templating/` (models, loaders, validators, resolvers, generators, normalizers, utils)
- `orchestrator.py` (V2Pipeline)
- Integration avec API client
- Flow de résolution (5 phases de validation)
- Diagrammes d'architecture V2.0

**Status** : [ ] TODO

#### 🆕 `/docs/INDEX.md`
**Contenu** :
- Liste complète des docs
- Status de chaque doc (active/deprecated/draft)
- Courte description
- Organisation par composant (CLI/WebApp/Tooling)

**Status** : [ ] TODO

#### 🆕 `/docs/cli/usage/quickstart.md`
**Contenu** :
- Installation
- Configuration initiale (`sdgen init`)
- Premier template
- Génération d'images
- Exemples concrets

**Status** : [ ] TODO

#### 🆕 `/docs/cli/usage/templates-guide.md`
**Contenu** :
- Guide complet des templates V2.0
- Syntaxe détaillée
- Exemples progressifs (simple → avancé)
- Best practices

**Status** : [ ] TODO

#### 🆕 `/docs/cli/usage/troubleshooting.md`
**Contenu** :
- FAQ
- Erreurs courantes + solutions
- Debugging tips

**Status** : [ ] TODO

#### 🆕 `/docs/cli/usage/api-commands.md`
**Contenu** :
- Documentation de toutes les commandes `sdgen api *`
- Exemples d'utilisation
- Options disponibles

**Status** : [ ] TODO

---

## 🚀 PLAN D'EXÉCUTION

### Phase 1 : Nettoyage critique (Session 1)

**Objectif** : Supprimer/archiver les docs redondantes et obsolètes

- [x] **Décision** : ✅ `FIX_TEMPLATING_V2.0_SPEC.md` est LA spec finale

- [x] **Renommage** : Spec finale ✅ **FAIT (2025-10-14)**
  ```bash
  # Renommer la spec finale avec un nom plus clair
  mv docs/roadmap/FIX_TEMPLATING_V2.0_SPEC.md \
     docs/roadmap/template-system-spec.md
  ```

- [x] **Archivage** : Anciennes specs ✅ **FAIT (2025-10-14)**
  ```bash
  # Archiver l'ancienne version
  mv docs/roadmap/template-system-v2-spec.md \
     docs/roadmap/archive/template-system-v2-spec-OLD.md

  # Supprimer le delta (plus nécessaire)
  rm docs/roadmap/FIX_TEMPLATING_V2.0_DELTA.md
  ```

- [x] **Archivage** : Workshop et brainstorm ✅ **FAIT (2025-10-14)**
  ```bash
  mv docs/roadmap/templateSpec.md \
     docs/roadmap/archive/templateSpec-workshop.md
  ```

- [x] **Archivage** : Docs obsolètes V1 ✅ **FAIT (2025-10-14)**
  ```bash
  mv docs/cli/technical/v2-templating-engine.md \
     docs/roadmap/archive/v2-templating-engine-deprecated.md

  mv docs/cli/technical/architecture.md \
     docs/roadmap/archive/architecture-legacy.md
  ```

- [ ] **Vérification** : roadmap/done/
  - Valider chaque feature terminée
  - Archiver si nécessaire

**Durée estimée** : 1-2h

### Phase 2 : Consolidation (Session 2)

**Objectif** : Créer les docs manquantes essentielles + préparer structure i18n

- [ ] Créer `docs/cli/technical/architecture-v2.md`
- [ ] Créer `docs/INDEX.md`
- [ ] Mettre à jour `README.md` principal (ajouter section CLI)

**Préparation VitePress (optionnel mais recommandé)** :
- [ ] Créer structure `docs/fr/` et déplacer docs actuelles dedans
- [ ] Créer squelette `docs/en/` pour traduction future
- [ ] Organiser par catégories VitePress-friendly :
  - `guide/` (getting-started, templates, etc.)
  - `reference/` (API, CLI commands)
  - `technical/` (architecture, design)

**Durée estimée** : 2-3h (+ 1h si structure i18n)

### Phase 3 : Guides utilisateur (Session 3)

**Objectif** : Améliorer la documentation utilisateur

- [ ] Créer `docs/cli/usage/quickstart.md`
- [ ] Créer `docs/cli/usage/templates-guide.md`
- [ ] Créer `docs/cli/usage/troubleshooting.md`
- [ ] Créer `docs/cli/usage/api-commands.md`

**Durée estimée** : 3-4h

### Phase 4 : Traduction anglaise (Session 4+)

**Objectif** : Traduire la documentation nettoyée

- [ ] Prioriser les docs à traduire
- [ ] Créer structure multilingue (`docs/en/`, `docs/fr/`)
- [ ] Traduire progressivement

**Durée estimée** : À définir selon volume

---

## 📊 MÉTRIQUES DE SUIVI

### Avant cleanup
- **Total docs** : 69 fichiers
- **Docs actives** : ~50 fichiers
- **Docs obsolètes/redondantes** : ~8-10 fichiers
- **Docs manquantes** : 4-6 fichiers

### Après cleanup (objectif)
- **Total docs** : ~60-65 fichiers
- **Docs actives** : 60-65 fichiers (100%)
- **Docs obsolètes** : 0
- **Docs manquantes** : 0

### Qualité
- **Clarté V1/V2** : 🔴 Confus → 🟢 Clair
- **Redondance** : 🔴 Haute → 🟢 Minimale
- **Couverture** : 🟡 Partielle → 🟢 Complète

---

## 📝 NOTES ET DÉCISIONS

### Session 2025-10-14 (Audit initial + Phase 1)

**Décisions prises** :
- ✅ Validation de la stratégie de nettoyage
- ✅ Identification des fichiers redondants
- ✅ Plan en 4 phases
- ✅ **DÉCISION CRITIQUE** : `FIX_TEMPLATING_V2.0_SPEC.md` est LA spec finale à garder
  - Renommer en `template-system-spec.md`
  - Archiver l'ancien `template-system-v2-spec.md`
  - Supprimer `FIX_TEMPLATING_V2.0_DELTA.md`
- ✅ Vision VitePress ajoutée (documentation future en ligne)

**Actions effectuées (Phase 1 - Nettoyage critique)** :
- ✅ Renommé `FIX_TEMPLATING_V2.0_SPEC.md` → `template-system-spec.md`
- ✅ Archivé `template-system-v2-spec.md` → `archive/template-system-v2-spec-OLD.md`
- ✅ Supprimé `FIX_TEMPLATING_V2.0_DELTA.md`
- ✅ Archivé `templateSpec.md` → `archive/templateSpec-workshop.md`
- ✅ Archivé `v2-templating-engine.md` → `archive/v2-templating-engine-deprecated.md`
- ✅ Archivé `architecture.md` → `archive/architecture-legacy.md`

**Résultat** :
- 6 fichiers nettoyés/archivés
- 1 fichier renommé (spec principale)
- Documentation plus claire (V1/V2 séparés)

**Questions en suspens** :
- [ ] Migration V1→V2 complète ? (vérifier `MIGRATION_PLAN.md`)
- [ ] Valider tous les roadmap/done/

**Prochaine session** :
- Continuer Phase 1 : Vérifier roadmap/done/
- Ou commencer Phase 2 : Consolidation (créer docs manquantes)

### Session 2025-10-14 (Phase 2 - Restructuration Guide)

**Objectif** : Créer structure de documentation didactique (guide/reference/technical)

**Actions effectuées (Phase 2 - Restructuration complète)** :
- ✅ Créé dossiers `docs/cli/guide/`, `reference/`, `technical/`
- ✅ Créé `guide/README.md` - Navigation et parcours d'apprentissage
- ✅ Créé `guide/getting-started.md` (366 lignes) - Installation et premier template
- ✅ Créé `guide/1-prompting-standalone.md` (459 lignes) - Prompts fixes et paramètres SD
- ✅ Créé `guide/2-placeholders-variations.md` (460 lignes) - Introduction aux variations
- ✅ Adapté `guide/3-templates-basics.md` (352 lignes) - Multi-variations et modes
- ✅ Créé `guide/4-templates-advanced.md` - Sélecteurs, héritage, chunks, listes
- ✅ Créé `guide/examples.md` - 6 cas d'usage complets (LoRA, exploration, variantes, etc.)
- ✅ Créé `guide/troubleshooting.md` - Problèmes courants et FAQ
- ✅ Mis à jour `docs/cli/README.md` - Landing page avec navigation guide/reference/technical

**Structure pédagogique** :
```
docs/cli/guide/
├── README.md                        # Parcours d'apprentissage
├── getting-started.md               # 10 min - Installation
├── 1-prompting-standalone.md        # 10 min - Prompts fixes
├── 2-placeholders-variations.md     # 10 min - Variations
├── 3-templates-basics.md            # 15 min - Multi-variations
├── 4-templates-advanced.md          # 20 min - Features avancées
├── examples.md                      # 15 min - Cas d'usage
└── troubleshooting.md               # 10 min - FAQ
```

**Statistiques** :
- **8 fichiers créés** (~3000+ lignes de documentation)
- **Durée totale parcours complet** : 2 heures
- **15+ exemples YAML complets**
- **6 cas d'usage détaillés**

**Résultat** :
- ✅ Documentation didactique complète en français
- ✅ Progression claire (Débutant → Avancé)
- ✅ Structure VitePress-ready
- ✅ Séparation guide/reference/technical
- ✅ Navigation intuitive avec parcours recommandés

**Prochaines étapes** :
- [ ] Phase 3 : Créer section `reference/` (syntaxe rapide)
- [x] Phase 5 : Archiver `yaml-templating-guide.md` (contenu dispersé dans guides)
- [ ] Phase 4 : Organiser `technical/` (déplacer template-system-spec.md)

### Session 2025-10-14 (Phase 5 - Nettoyage final)

**Objectif** : Archiver l'ancien guide monolithique et mettre à jour les liens

**Actions effectuées (Phase 5 - Nettoyage final)** :
- ✅ Créé `/docs/cli/usage/archive/` pour archivage
- ✅ Archivé `yaml-templating-guide.md` → `archive/yaml-templating-guide-monolithic.md` (1072 lignes)
- ✅ Recherché tous les liens vers l'ancien guide (4 fichiers trouvés)
- ✅ Mis à jour `/docs/cli/technical/yaml-templating-system.md` - Liens vers nouveaux guides
- ✅ Mis à jour `/docs/cli/usage/examples.md` - Liens vers structure guide/
- ✅ Mis à jour `/docs/cli/usage/getting-started.md` - Liens vers guides progressifs
- ✅ Mis à jour `/docs/roadmap/archive/README.md` - Documentation actuelle

**Liens mis à jour** :
- `../usage/yaml-templating-guide.md` → `../guide/README.md` (landing page)
- `yaml-templating-guide.md` → `../guide/3-templates-basics.md` (selon contexte)
- Ajouté références aux nouveaux guides : getting-started, templates-basics, templates-advanced

**Résultat** :
- ✅ Guide monolithique archivé (évite confusion)
- ✅ Tous les liens inter-docs mis à jour
- ✅ Navigation cohérente vers nouvelle structure
- ✅ Documentation clean sans fichiers obsolètes actifs

**Status Phase 5** : ✅ **TERMINÉE**

**Prochaines étapes disponibles** :
- [ ] Phase 3 : Créer section `reference/` (2-3h)
- [x] Phase 4 : Organiser `technical/` (1h) - **TERMINÉE**

### Session 2025-10-14 (Phase 4 - Organiser Technical)

**Objectif** : Déplacer la spec dans technical/ et créer navigation technique

**Actions effectuées (Phase 4 - Organisation technique)** :
- ✅ Déplacé `docs/roadmap/template-system-spec.md` → `docs/cli/technical/template-system-spec.md`
- ✅ Créé `docs/cli/technical/architecture.md` - Vue d'ensemble architecture V2.0
  - Structure modulaire (models, loaders, validators, resolvers, generators, normalizers, utils)
  - V2Pipeline orchestrator avec 5 phases (Load → Validate → Resolve → Generate → Normalize)
  - Patterns architecturaux (Strategy, Pipeline, Dependency Injection)
  - Integration avec API Stable Diffusion
  - Modèles de données (TemplateConfig, ResolvedVariation)
  - Performance metrics et optimisations
- ✅ Créé `docs/cli/technical/README.md` - Navigation complète section technique
  - Vue d'ensemble des 3 docs techniques principales
  - Parcours par rôle (développeur, mainteneur, contributeur, debugger)
  - Statistiques du projet (tests, coverage, complexité)
  - Commandes de dev (tests, quality tools, profiling)
  - Liens externes et ressources
- ✅ Mis à jour 5 fichiers avec liens vers nouveau chemin de spec :
  - `/docs/cli/guide/4-templates-advanced.md`
  - `/docs/cli/guide/examples.md`
  - `/docs/cli/guide/README.md`
  - `/docs/cli/README.md` (2 références)

**Structure technique finale** :
```
docs/cli/technical/
├── README.md                    # Navigation et parcours
├── architecture.md              # Architecture V2.0 (nouveau)
├── template-system-spec.md      # Spec complète (déplacé)
├── yaml-templating-system.md    # Guide technique détaillé
├── error-handling-validation.md # Système de validation
├── manifest_v2_format.md        # Format manifest.json
├── config-system.md             # Configuration
├── output-system.md             # Système de sortie
└── adetailer.md                 # ADetailer integration
```

**Résultat** :
- ✅ Triangle guide/reference/technical complet
- ✅ Documentation technique organisée dans un seul dossier
- ✅ Navigation claire pour développeurs
- ✅ Tous les liens inter-docs mis à jour
- ✅ Architecture V2.0 documentée en détail

**Status Phase 4** : ✅ **TERMINÉE**

**Prochaines étapes disponibles** :
- [ ] Phase 3 : Créer section `reference/` (2-3h) - Syntaxe rapide et commandes CLI

---

## 🔗 RÉFÉRENCES

### Fichiers clés à consulter
- `/docs/cli/technical/yaml-templating-system.md` - Doc V2.0 actuelle
- `/docs/roadmap/template-system-v2-spec.md` - Spec V2.0 technique
- `/CLI/src/cli.py` - Commandes CLI réelles
- `/CLI/src/templating/orchestrator.py` - V2Pipeline
- `/CLAUDE.md` - Configuration projet

### Commandes utiles
```bash
# Lister toutes les docs
find docs -name "*.md" | sort

# Compter les fichiers par dossier
find docs -type f -name "*.md" | cut -d/ -f1-3 | sort | uniq -c

# Rechercher mentions de "V1" ou "legacy"
grep -r "V1\|legacy\|deprecated" docs/ --include="*.md"
```

---

**Dernière mise à jour** : 2025-10-14
**Prochaine action** : Phase 1 - Nettoyage critique

---

## 🌐 VISION FUTURE : VITEPRESS

**Note importante** : La documentation pourrait migrer vers VitePress (site statique en ligne) à terme.

### Implications pour l'organisation
- ✅ Structure actuelle compatible (`docs/` avec sous-dossiers)
- ✅ Fichiers Markdown standards (pas de migration nécessaire)
- 🎯 Prévoir structure i18n (`docs/en/`, `docs/fr/`)
- 🎯 Penser navigation (sidebar, catégories claires)

### Avantages VitePress
- 🚀 Recherche full-text intégrée
- 🎨 UI moderne et responsive
- 🌍 Support multilingue natif
- 📱 Navigation mobile optimisée
- ⚡ Performances excellentes (Vite)

### Structure recommandée pour VitePress
```
docs/
├── .vitepress/
│   └── config.js         # Configuration VitePress
├── en/                   # English docs
│   ├── cli/
│   ├── api/
│   └── guide/
├── fr/                   # French docs (actuel)
│   ├── cli/
│   ├── api/
│   └── guide/
└── public/               # Assets statiques
```

### À prévoir
- [ ] Créer structure i18n dès maintenant (facilite migration)
- [ ] Organiser par "guide" (getting-started, advanced, etc.)
- [ ] Maintenir cohérence navigation entre langues
