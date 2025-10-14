# Templates Advanced

**Maîtrisez les features avancées pour un contrôle total de vos générations.**

📚 **Prérequis** : [Template Basics](./3-templates-basics.md)

⏱️ **Durée de lecture** : 20 minutes

---

## Ce que vous allez apprendre

Vous maîtrisez les multi-variations et les modes de génération. Maintenant, découvrez comment :

- **Limiter et choisir** des variations spécifiques avec les sélecteurs
- **Réutiliser** des configurations avec l'héritage de templates
- **Composer** des prompts complexes avec les chunks
- **Combiner** plusieurs fichiers de variations automatiquement

---

## Sélecteurs : Choisir vos variations

Les sélecteurs permettent de **contrôler précisément quelles variations utiliser**, sans modifier les fichiers de variations.

### Pourquoi utiliser des sélecteurs ?

**Problème** :
```yaml
imports:
  Expression: ../variations/expressions.yaml  # 50 expressions
  Outfit: ../variations/outfits.yaml         # 30 outfits
  Angle: ../variations/angles.yaml            # 20 angles

# 50 × 30 × 20 = 30,000 images 🔥
```

**Solution avec sélecteurs** :
```yaml
template: |
  portrait, {Expression[5]}, {Outfit[3]}, {Angle[front,side,back]}

# 5 × 3 × 3 = 45 images ✅
```

---

## Types de sélecteurs

### 1. Sélecteur de limite `[N]`

**Syntaxe** : `{Placeholder[N]}`

**Effet** : Tire **N variations aléatoires** du fichier

```yaml
imports:
  Expression: ../variations/expressions.yaml  # 50 expressions

template: |
  portrait, {Expression[10]}, detailed

# Utilise seulement 10 expressions parmi les 50 disponibles
```

**Avantage** : Tester rapidement sans tout générer

---

### 2. Sélecteur par index `[#i,j,k]`

**Syntaxe** : `{Placeholder[#0,2,5]}`

**Effet** : Sélectionne les variations aux **indices spécifiques**

```yaml
# variations/expressions.yaml
# Index 0: happy
# Index 1: sad
# Index 2: angry
# Index 3: neutral
# Index 4: surprised

template: |
  portrait, {Expression[#0,2,4]}, detailed

# Utilise : happy, angry, surprised
```

**Usage** : Sélection précise d'éléments testés et approuvés

---

### 3. Sélecteur par clé `[key1,key2]`

**Syntaxe** : `{Placeholder[happy,sad,angry]}`

**Effet** : Sélectionne les variations **par leur nom de clé**

```yaml
imports:
  Expression: ../variations/expressions.yaml

template: |
  portrait, {Expression[happy,surprised,neutral]}, detailed

# Utilise exactement ces 3 expressions nommées
```

**Avantage** : Lisible et maintenable (pas de dépendance aux index)

---

### 4. Sélecteur de range `[#i-j]`

**Syntaxe** : `{Placeholder[#0-10]}`

**Effet** : Sélectionne un **intervalle d'indices**

```yaml
template: |
  portrait, {Expression[#0-5]}, detailed

# Utilise les 6 premières variations (index 0 à 5)
```

**Usage** : Grouper des variations similaires par range

---

## Exemples pratiques de sélecteurs

### Exemple 1 : Test rapide avant production

```yaml
version: '2.0'
name: 'Quick Test - 15 images'

imports:
  Expression: ../variations/expressions.yaml  # 50 disponibles
  Outfit: ../variations/outfits.yaml         # 30 disponibles
  Background: ../variations/backgrounds.yaml  # 20 disponibles

template: |
  masterpiece, portrait, {Expression[5]}, {Outfit[3]}, {Background[2]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 1000
  max_images: 30  # 5 × 3 × 2 = 30 images

# Test rapide, puis retirer les sélecteurs pour production complète
```

---

### Exemple 2 : Variations spécifiques approuvées

```yaml
version: '2.0'
name: 'Approved Expressions Only'

imports:
  Expression: ../variations/expressions.yaml
  Angle: ../variations/angles.yaml

template: |
  portrait, {Expression[happy,neutral,thoughtful]}, {Angle[front,side]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 2000
  max_images: 6  # 3 × 2 = 6 images
```

**Usage** : Génération finale avec variations validées uniquement

---

### Exemple 3 : Combinaison de sélecteurs

```yaml
template: |
  portrait,
  {Expression[10]},
  {Angle[front,side,three_quarter]},
  {Lighting[#0-5]},
  {Background[nature,studio]}

# 10 × 3 × 6 × 2 = 360 images
```

---

## Pondération : Contrôle de l'ordre des boucles

Par défaut, les placeholders sont combinés dans l'ordre où ils apparaissent. Vous pouvez contrôler cet ordre avec `weight:`.

### Syntaxe

```yaml
imports:
  Expression:
    source: ../variations/expressions.yaml
    weight: 1  # Boucle externe (change le moins souvent)

  Outfit:
    source: ../variations/outfits.yaml
    weight: 2  # Boucle intermédiaire

  Angle:
    source: ../variations/angles.yaml
    weight: 3  # Boucle interne (change le plus souvent)
```

### Comportement

**Sans weight** : Ordre d'apparition dans le template
**Avec weight** : Plus le weight est bas, plus la variation change lentement

**Exemple** :
```
Image 1:  Expression=happy,    Outfit=casual,  Angle=front
Image 2:  Expression=happy,    Outfit=casual,  Angle=side
Image 3:  Expression=happy,    Outfit=casual,  Angle=back
Image 4:  Expression=happy,    Outfit=formal,  Angle=front
Image 5:  Expression=happy,    Outfit=formal,  Angle=side
...
Image 19: Expression=sad,      Outfit=casual,  Angle=front
```

**Usage** : Organiser vos datasets LoRA par groupes logiques

---

## Héritage de templates

L'héritage permet de **réutiliser** des configurations de base sans dupliquer le code.

### Concept

```
base_template.template.yaml  (paramètres + structure commune)
    ↓ implements
portrait_happy.prompt.yaml  (prompt spécifique)
```

### Cas d'usage typique

Vous avez des **paramètres SD** optimaux (résolution, steps, sampler, hires fix) que vous voulez réutiliser pour plusieurs prompts.

---

### Template de base

**`templates/base_portrait_hq.template.yaml`**

```yaml
version: '2.0'
name: 'Base Portrait High Quality'

# Paramètres optimisés pour portraits haute qualité
parameters:
  width: 832
  height: 1216
  steps: 30
  cfg_scale: 6
  sampler: DPM++ 2M
  scheduler: Karras

  # Hires fix pour améliorer les détails
  enable_hr: true
  hr_scale: 1.5                      # 832×1216 → 1248×1824
  hr_upscaler: 4x_foolhardy_Remacri
  denoising_strength: 0.4
  hr_second_pass_steps: 15

# Imports communs
imports:
  HairColor: ../variations/shared/haircolors.yaml
  Outfit: ../variations/shared/outfits.yaml

# Structure de base
template: |
  masterpiece, ultra-HD, high detail, depth of field,
  beautiful woman, {HairColor} hair, {Outfit},
  cinematic lighting, HDR,
  {prompt}
```

**Note** : Le placeholder `{prompt}` est le **point d'injection** où le contenu des prompts enfants sera inséré.

---

### Prompts utilisant le template

**`prompts/portrait_happy.prompt.yaml`**

```yaml
version: '2.0'
name: 'Portrait Happy Expressions'
implements: ../templates/base_portrait_hq.template.yaml

# Contenu spécifique injecté dans {prompt}
template: |
  smiling, happy, cheerful expression, looking at viewer

generation:
  mode: random
  seed_mode: progressive
  seed: 1000
  max_images: 50
```

**`prompts/portrait_action.prompt.yaml`**

```yaml
version: '2.0'
name: 'Portrait Action Shots'
implements: ../templates/base_portrait_hq.template.yaml

# Import supplémentaire
imports:
  Action: ../variations/actions.yaml

# Contenu spécifique
template: |
  {Action}, dynamic pose, motion blur

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 2000
  max_images: 100
```

---

### Résultat de l'héritage

**Pour `portrait_happy.prompt.yaml`**, le prompt final sera :

```
masterpiece, ultra-HD, high detail, depth of field,
beautiful woman, {HairColor} hair, {Outfit},
cinematic lighting, HDR,
smiling, happy, cheerful expression, looking at viewer
```

**Avantages** :
- ✅ Un seul endroit pour modifier les paramètres techniques
- ✅ Pas de duplication de code
- ✅ Cohérence entre tous les prompts utilisant la même base
- ✅ Facile de créer 10+ variations sans répéter le setup

---

### Override de paramètres

L'enfant peut **overrider** n'importe quel paramètre du parent :

```yaml
version: '2.0'
name: 'Portrait Night - Lower CFG'
implements: ../templates/base_portrait_hq.template.yaml

# Override du cfg_scale seulement
parameters:
  cfg_scale: 4  # Plus bas pour scènes de nuit

template: |
  night scene, stars, moonlight, mysterious atmosphere
```

**Résultat** :
- Tous les paramètres hérités de `base_portrait_hq.template.yaml`
- Sauf `cfg_scale` qui passe à 4

---

## Listes d'imports : Combiner plusieurs fichiers

Vous pouvez **merger automatiquement** plusieurs fichiers de variations dans un seul placeholder.

### Syntaxe

```yaml
imports:
  HairColor:
    - ../variations/haircolors.realistic.yaml
    - ../variations/haircolors.fantasy.yaml
    - ../variations/haircolors.gradient.yaml
```

### Fichiers sources

**`haircolors.realistic.yaml`**
```yaml
brown: brown hair, chestnut tones
blonde: blonde hair, golden highlights
black: black hair, raven dark
red: auburn hair, copper tones
```

**`haircolors.fantasy.yaml`**
```yaml
pink: pink hair, pastel rose
blue: blue hair, cerulean
purple: purple hair, violet
silver: silver hair, metallic sheen
```

**`haircolors.gradient.yaml`**
```yaml
ombre: ombre hair, gradient effect
highlights: highlighted hair, sun-kissed
```

### Résultat

Le placeholder `{HairColor}` aura **10 variations** (4 + 4 + 2) sans créer de fichier intermédiaire.

```yaml
template: |
  portrait, {HairColor} hair, detailed

# Génère 10 images avec toutes les couleurs disponibles
```

---

### Usage pratique

**Cas 1 : Organisation par catégorie**

```yaml
imports:
  Outfit:
    - ../variations/outfits.casual.yaml     # 15 variations
    - ../variations/outfits.formal.yaml     # 12 variations
    - ../variations/outfits.fantasy.yaml    # 8 variations
    - ../variations/outfits.sport.yaml      # 10 variations
  # Total : 45 variations dans {Outfit}
```

**Cas 2 : Réutilisation avec sélecteurs**

```yaml
imports:
  Expression:
    - ../variations/expressions.positive.yaml  # 20 variations
    - ../variations/expressions.negative.yaml  # 15 variations

template: |
  portrait, {Expression[10]}, detailed

# Tire 10 expressions parmi les 35 disponibles (20+15)
```

---

## Chunks : Composition avancée (Aperçu)

Les chunks permettent de créer des **blocs réutilisables** pour composer des prompts complexes.

**Note** : Les chunks sont une feature avancée détaillée dans la documentation technique. Voici un aperçu.

### Concept

Au lieu de répéter la description d'un personnage, créez un chunk réutilisable :

```yaml
# chunks/character_alice.chunk.yaml
version: '2.0'
type: 'character'

template: |
  1girl, 25 years old, blonde hair, blue eyes,
  alice_lora, detailed face, detailed skin

# Utilisation dans prompt
imports:
  Alice: ../chunks/character_alice.chunk.yaml

template: |
  @Alice, in a forest, sunlight filtering through trees
```

**Le `@Alice` sera remplacé** par le contenu du chunk.

### Avantages

- ✅ Réutiliser des descriptions de personnages complexes
- ✅ Composition modulaire de prompts
- ✅ Un seul endroit pour modifier un personnage

---

## Bonnes pratiques avancées

### 1. Tester avec sélecteurs avant production

```yaml
# Version test (rapide)
template: |
  {Expression[5]}, {Outfit[3]}, {Background[2]}
  # = 30 images

# Version production (après validation)
template: |
  {Expression}, {Outfit}, {Background}
  # = Toutes les combinaisons
```

### 2. Nommer clairement les templates de base

```yaml
# ❌ Mauvais
base.template.yaml

# ✅ Bon
base_portrait_hq_hiresfix.template.yaml
```

### 3. Documenter les templates réutilisables

```yaml
version: '2.0'
name: 'Base Portrait High Quality'

# Description du template
# --------------------------------------------------
# Template optimisé pour portraits haute qualité
# Résolution : 832×1216 upscalée à 1248×1824
# Hires Fix : 4x_foolhardy_Remacri, denoising 0.4
#
# Utilisation :
#   implements: ../templates/base_portrait_hq.template.yaml
#   template: |
#     [votre contenu spécifique]
# --------------------------------------------------

parameters:
  # ...
```

### 4. Organiser vos fichiers

```
project/
├── templates/                    # Templates réutilisables
│   ├── base_portrait_hq.template.yaml
│   ├── base_landscape.template.yaml
│   └── base_fantasy.template.yaml
│
├── prompts/                      # Prompts spécifiques
│   ├── portraits/
│   │   ├── happy.prompt.yaml
│   │   ├── action.prompt.yaml
│   │   └── night.prompt.yaml
│   │
│   └── scenes/
│       ├── forest.prompt.yaml
│       └── city.prompt.yaml
│
└── variations/
    ├── shared/                   # Variations communes
    │   ├── expressions.yaml
    │   └── outfits.yaml
    │
    └── specific/                 # Variations spécifiques
        └── fantasy_items.yaml
```

---

## Récapitulatif

✅ Vous maîtrisez maintenant :
- Les **sélecteurs** pour contrôler les variations (`[N]`, `[#i,j]`, `[key1,key2]`, `[#i-j]`)
- Le **weight** pour ordonner les boucles de génération
- L'**héritage de templates** pour réutiliser des configurations
- Les **listes d'imports** pour combiner plusieurs fichiers
- L'**organisation** de projets complexes
- Les **bonnes pratiques** avancées

### Pour aller plus loin

➡️ Consultez la [documentation technique](../../roadmap/template-system-spec.md) pour :
- Chunks et composition avancée
- Multi-field variations
- Architecture du système V2.0

➡️ Explorez les [exemples](./examples.md) pour des cas d'usage réels

➡️ Consultez le [troubleshooting](./troubleshooting.md) en cas de problème

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~20 minutes
**Version du système** : V2.0
