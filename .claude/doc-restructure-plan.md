# 📚 Plan de Restructuration Documentation CLI

**Date:** 2025-10-14
**Objectif:** Créer une documentation didactique avec progression claire

---

## 🎯 PROBLÈME IDENTIFIÉ

### Redondance actuelle

**Fichiers en conflit:**
- `docs/roadmap/template-system-spec.md` (903 lignes) - Spec technique formelle
- `docs/cli/usage/yaml-templating-guide.md` (1072 lignes) - Guide utilisateur didactique

**Contenu redondant:**
- ✅ Syntaxe des templates (les deux)
- ✅ Sélecteurs (les deux)
- ✅ Héritage/implements (les deux)
- ✅ Exemples YAML (les deux)

### Publics différents non servis optimalement

**3 types d'utilisateurs:**

1. **Nouveaux utilisateurs** 🆕
   - Besoin: Tutoriel progressif, exemples simples
   - Actuellement: Guide OK mais mélangé avec référence

2. **Utilisateurs habitués** 🔄
   - Besoin: Référence rapide, syntaxe complète
   - Actuellement: Doivent chercher dans 1000+ lignes

3. **Développeurs/Mainteneurs** 🔧
   - Besoin: Spec technique, architecture
   - Actuellement: Spec dans /roadmap/ (mauvais emplacement)

---

## ✨ NOUVELLE STRUCTURE PROPOSÉE

### Organisation type VitePress/Docusaurus

```
docs/cli/
│
├── guide/                          # 🆕 NOUVEAUX UTILISATEURS
│   ├── README.md                   # Landing page du guide
│   ├── getting-started.md          # Installation + premier template
│   ├── templates-basics.md         # Concepts de base (progressif)
│   ├── templates-advanced.md       # Features avancées
│   ├── examples.md                 # Exemples concrets par cas d'usage
│   └── troubleshooting.md          # FAQ + dépannage
│
├── reference/                      # 🔄 UTILISATEURS HABITUÉS
│   ├── README.md                   # Landing page référence
│   ├── template-syntax.md          # Syntaxe complète (reference card)
│   ├── selectors-reference.md      # Tous les sélecteurs avec exemples
│   ├── cli-commands.md             # Toutes les commandes CLI
│   ├── yaml-schema.md              # Schéma YAML complet
│   └── api-reference.md            # API commands (samplers, models, etc.)
│
└── technical/                      # 🔧 DÉVELOPPEURS/MAINTENEURS
    ├── README.md                   # Vue d'ensemble architecture
    ├── architecture.md             # Architecture V2.0 (à créer)
    ├── template-system-spec.md     # Spec technique formelle (déplacé)
    ├── design-decisions.md         # Rationales et trade-offs
    ├── adetailer.md                # Intégration ADetailer
    ├── manifest_v2_format.md       # Format manifest
    ├── error-handling-validation.md # Validation système
    ├── output-system.md            # Système output
    └── config-system.md            # Système config
```

---

## 📋 CONTENU PAR SECTION

### guide/ (Nouveaux utilisateurs)

#### getting-started.md (NOUVEAU - à créer)
**Contenu:**
- Installation et setup (`sdgen init`)
- Votre premier template (minimal example)
- Générer vos premières images
- Comprendre les résultats
- Next steps

**Durée de lecture:** 5-10 min

#### templates-basics.md (EXTRAIT de yaml-templating-guide.md)
**Contenu:**
- Concepts de base (placeholders, variations)
- Niveau 1: Template simple
- Niveau 2: Multi-variations
- Modes combinatorial vs random
- Modes de seed

**Durée de lecture:** 15 min

#### templates-advanced.md (EXTRAIT de yaml-templating-guide.md)
**Contenu:**
- Niveau 3: Sélecteurs
- Niveau 4: Héritage de templates
- Niveau 5: Chunks (si applicable)
- Listes d'imports multi-fichiers
- Organisation de projet

**Durée de lecture:** 20 min

#### examples.md (EXTRAIT de yaml-templating-guide.md)
**Contenu:**
- Cas d'usage réels
- Entraînement de LoRA
- Exploration créative
- Production de variantes
- Workflows complets

**Durée de lecture:** 10 min

#### troubleshooting.md (EXTRAIT de yaml-templating-guide.md + compléments)
**Contenu:**
- Problèmes courants + solutions
- Erreurs de validation
- Performance tips
- Bonnes pratiques

---

### reference/ (Utilisateurs habitués)

#### template-syntax.md (NOUVEAU - synthèse)
**Contenu:**
- Reference card complète
- Tous les champs YAML
- Syntaxe des placeholders
- Tableau récapitulatif

**Format:** Dense, cherchable, organisé par catégorie

#### selectors-reference.md (NOUVEAU - extrait de spec + guide)
**Contenu:**
```
# Sélecteurs - Référence Complète

## Syntaxe générale
{Placeholder[selector1;selector2;...]}

## Types de sélecteurs

### 1. Limite aléatoire [N]
Syntaxe: {Angle[15]}
Usage: Tire N variations aléatoires
Exemples:
  - {Expression[5]} → 5 expressions random
  - {Outfit[10;$2]} → 10 outfits random, poids 2

### 2. Sélection par index [#i,j,k]
Syntaxe: {Angle[#1,3,5]}
...

## Combinaisons complexes
{Angle[#1,3,5;$8]} → Index 1,3,5 + poids 8
{Angle[15;$0]} → 15 random + hors combinatoire
```

#### cli-commands.md (NOUVEAU - depuis cli.py)
**Contenu:**
- `sdgen generate` (toutes les options)
- `sdgen list`
- `sdgen validate`
- `sdgen init`
- `sdgen api *` (toutes les sous-commandes)

#### yaml-schema.md (NOUVEAU - référence formelle)
**Contenu:**
- Schéma complet des fichiers YAML
- `.template.yaml` schema
- `.chunk.yaml` schema
- `.prompt.yaml` schema
- `.yaml` (variations) schema
- Champs obligatoires vs optionnels

---

### technical/ (Développeurs)

#### architecture.md (NOUVEAU - à créer)
**Contenu:**
- Structure de `CLI/src/templating/`
- V2Pipeline (orchestrator)
- Flow de résolution (5 phases)
- Modules (models, loaders, validators, resolvers, generators)
- Diagrammes d'architecture

#### template-system-spec.md (DÉPLACÉ depuis roadmap/)
**Contenu actuel:**
- Spec technique formelle (EBNF)
- Règles de validation
- Template Method Pattern
- Merge rules
- Injection mechanics

---

## 🔄 MIGRATION DES CONTENUS

### yaml-templating-guide.md → Découpé en plusieurs fichiers

| Section actuelle | Destination | Notes |
|-----------------|-------------|-------|
| Vue d'ensemble | `guide/templates-basics.md` | Introduction |
| Concepts de base | `guide/templates-basics.md` | Avec diagrammes |
| Niveau 1 & 2 | `guide/templates-basics.md` | Progression simple |
| Niveau 3 & 4 | `guide/templates-advanced.md` | Features avancées |
| Cas d'usage réels | `guide/examples.md` | Exemples concrets |
| Dépannage | `guide/troubleshooting.md` | FAQ |
| Référence rapide (tableau fin) | `reference/template-syntax.md` | Tableau synthétique |
| Syntaxe sélecteurs | `reference/selectors-reference.md` | Référence complète |

### template-system-spec.md → Déplacé + complété

| Section | Action |
|---------|--------|
| Glossaire | Garder dans spec |
| Architecture conceptuelle | **Extraire** → `architecture.md` (nouveau) |
| Structure fichiers | Garder dans spec |
| EBNF grammar | Garder dans spec |
| Résolution/injection | Garder dans spec |
| Règles de merge | Garder dans spec |
| Validation | Garder dans spec |
| Exemples complets | **Copier aussi** dans `guide/examples.md` |

---

## 📊 COMPARAISON AVANT/APRÈS

### Avant (état actuel)

**Utilisateur nouveau:**
1. Lit 1072 lignes de `yaml-templating-guide.md`
2. Cherche dans les diagrammes
3. Trouve pas toujours la réponse rapide

**Utilisateur habitué:**
1. Cherche syntaxe d'un sélecteur
2. Scroll 1072 lignes pour trouver la bonne section
3. Ou va dans la spec de 903 lignes

**Développeur:**
1. Cherche la spec dans `/roadmap/` (?)
2. Pas de doc architecture V2.0

### Après (nouvelle structure)

**Utilisateur nouveau:**
1. `guide/getting-started.md` (5 min)
2. `guide/templates-basics.md` (15 min)
3. Premier template fonctionnel en 20 min ✅

**Utilisateur habitué:**
1. Va directement dans `reference/selectors-reference.md`
2. Trouve la syntaxe en 30 secondes ✅
3. Copie-colle l'exemple

**Développeur:**
1. `technical/architecture.md` pour vue d'ensemble
2. `technical/template-system-spec.md` pour détails
3. Comprend le système en 30 min ✅

---

## 🎯 AVANTAGES DE LA NOUVELLE STRUCTURE

### 1. Séparation des préoccupations
- ✅ Guide = apprentissage progressif
- ✅ Reference = recherche rapide
- ✅ Technical = compréhension profonde

### 2. Compatible VitePress
```javascript
// .vitepress/config.js
sidebar: {
  '/cli/guide/': [
    { text: 'Getting Started', link: '/cli/guide/getting-started' },
    { text: 'Template Basics', link: '/cli/guide/templates-basics' },
    // ...
  ],
  '/cli/reference/': [
    { text: 'Template Syntax', link: '/cli/reference/template-syntax' },
    // ...
  ]
}
```

### 3. Navigation claire
```
Guide           →  Apprendre progressivement
  ├─ Getting Started
  ├─ Basics
  ├─ Advanced
  └─ Examples

Reference       →  Chercher rapidement
  ├─ Syntax
  ├─ Selectors
  └─ CLI Commands

Technical       →  Comprendre en profondeur
  ├─ Architecture
  └─ Spec
```

### 4. Meilleure découverte
- Nouveaux users trouvent immédiatement `guide/`
- Habitués sautent directement à `reference/`
- Développeurs plongent dans `technical/`

### 5. Maintenance facilitée
- Chaque fichier a un rôle clair
- Pas de duplication inutile
- Updates ciblées

---

## 📅 PLAN D'EXÉCUTION

### Phase 1 : Préparation (30 min)
- [x] Analyser redondance actuelle
- [ ] Valider nouvelle structure avec utilisateur
- [ ] Créer dossiers `guide/`, `reference/`, `technical/`

### Phase 2 : Création des guides (2-3h)
- [ ] Créer `guide/getting-started.md`
- [ ] Découper `yaml-templating-guide.md` → `templates-basics.md`
- [ ] Découper → `templates-advanced.md`
- [ ] Extraire cas d'usage → `examples.md`
- [ ] Extraire dépannage → `troubleshooting.md`

### Phase 3 : Création des références (1-2h)
- [ ] Créer `reference/template-syntax.md` (synthèse)
- [ ] Créer `reference/selectors-reference.md` (depuis spec + guide)
- [ ] Créer `reference/cli-commands.md` (depuis cli.py)
- [ ] Créer `reference/yaml-schema.md` (schéma formel)

### Phase 4 : Organisation technical (1h)
- [ ] Déplacer `template-system-spec.md` → `technical/`
- [ ] Créer `technical/architecture.md` (Vue d'ensemble V2.0)
- [ ] Organiser docs existantes dans `technical/`

### Phase 5 : Nettoyage (30 min)
- [ ] Archiver `yaml-templating-guide.md` original
- [ ] Supprimer redondances
- [ ] Mettre à jour liens inter-docs

### Phase 6 : Index et navigation (1h)
- [ ] Créer `docs/cli/README.md` (landing page)
- [ ] Créer `guide/README.md`, `reference/README.md`, `technical/README.md`
- [ ] Créer `docs/INDEX.md` global

**Durée totale estimée:** 6-8 heures

---

## ✅ VALIDATION AVEC L'UTILISATEUR

### Questions à valider

1. **Structure OK ?**
   - [ ] `guide/` pour nouveaux utilisateurs
   - [ ] `reference/` pour habitués
   - [ ] `technical/` pour développeurs

2. **Contenu des guides OK ?**
   - [ ] getting-started.md (5-10 min de lecture)
   - [ ] templates-basics.md (concepts + niveaux 1-2)
   - [ ] templates-advanced.md (niveaux 3-4)

3. **Références utiles ?**
   - [ ] template-syntax.md (reference card)
   - [ ] selectors-reference.md (tous les sélecteurs)
   - [ ] cli-commands.md (toutes les commandes)

4. **Organisation technical OK ?**
   - [ ] Déplacer spec dans technical/
   - [ ] Créer architecture.md

5. **Autres besoins ?**
   - [ ] Autres sections manquantes ?
   - [ ] Autre organisation préférée ?

---

## 📝 NOTES

**Préparation VitePress:**
Cette structure est **100% compatible** avec VitePress/Docusaurus :
- Dossiers clairs (guide/reference/technical)
- Un fichier = une page
- Navigation intuitive
- Supporte i18n (`docs/en/cli/guide/`, `docs/fr/cli/guide/`)

**Migration anglaise facilitée:**
Avec cette structure, la traduction sera plus simple :
- Fichiers plus petits (300-500 lignes vs 1000+)
- Contenu bien délimité
- Peut traduire progressivement (guide d'abord, puis reference)

---

**Dernière mise à jour:** 2025-10-14
**Status:** Proposition en attente de validation
**Prochaine action:** Validation de la structure avec l'utilisateur
