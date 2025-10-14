# Examples & Use Cases

**Cas d'usage réels et exemples complets pour différents scénarios.**

📚 **Prérequis** : [Templates Advanced](./4-templates-advanced.md)

⏱️ **Durée de lecture** : 15 minutes

---

## Vue d'ensemble

Ce guide présente des **configurations complètes** pour différents cas d'usage :

1. **Entraînement de LoRA** - Dataset exhaustif avec variations maximales
2. **Exploration créative** - Génération aléatoire pour découvrir des idées
3. **Production de variantes** - Variations contrôlées d'un concept approuvé
4. **Test rapide** - Validation avant génération massive
5. **Character consistency** - Maintenir un personnage cohérent

---

## Cas 1 : Entraînement de LoRA

**Objectif** : Générer 500 images d'un personnage avec variations maximales pour entraîner un LoRA.

**Stratégie** :
- Mode `combinatorial` pour couvrir toutes les combinaisons
- Seeds progressives pour diversité garantie
- Multi-variations (expressions, angles, tenues, backgrounds)

### Configuration complète

**`prompts/lora_training_alice.prompt.yaml`**

```yaml
version: '2.0'
name: 'LoRA Training Dataset - Alice'

imports:
  Expression:
    - ../variations/expressions.positive.yaml    # 15 variations
    - ../variations/expressions.neutral.yaml     # 10 variations
    - ../variations/expressions.negative.yaml    # 8 variations

  Angle:
    - ../variations/angles.portrait.yaml         # 12 variations
    - ../variations/angles.fullbody.yaml         # 8 variations

  Outfit:
    - ../variations/outfits.casual.yaml          # 15 variations
    - ../variations/outfits.formal.yaml          # 12 variations
    - ../variations/outfits.fantasy.yaml         # 8 variations

  Background:
    - ../variations/backgrounds.indoor.yaml      # 10 variations
    - ../variations/backgrounds.outdoor.yaml     # 10 variations

template: |
  masterpiece, 1girl, alice_character,
  25 years old, blonde hair, blue eyes,
  {Expression}, {Angle}, {Outfit}, {Background},
  detailed face, detailed skin, high quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 10000
  max_images: 500

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

### Calcul des images

```
Expressions : 33 (15+10+8)
Angles      : 20 (12+8)
Outfits     : 35 (15+12+8)
Backgrounds : 20 (10+10)

Total théorique : 33 × 20 × 35 × 20 = 462,000 combinaisons

Avec max_images: 500 → 500 premières combinaisons
```

### Workflow

1. **Générer le dataset**
   ```bash
   sdgen generate -t prompts/lora_training_alice.prompt.yaml
   ```

2. **Vérifier les résultats**
   - Parcourir les 500 images
   - Supprimer les images avec artefacts
   - Garder ~450-480 images de qualité

3. **Entraîner le LoRA**
   - Utiliser les images validées
   - Captionner si nécessaire

---

## Cas 2 : Exploration créative

**Objectif** : Explorer rapidement des idées artistiques sans plan prédéfini.

**Stratégie** :
- Mode `random` pour résultats imprévisibles
- Seeds aléatoires pour variété maximale
- Sélecteurs pour limiter à un nombre raisonnable

### Configuration complète

**`prompts/creative_exploration.prompt.yaml`**

```yaml
version: '2.0'
name: 'Creative Exploration - Abstract Art'

imports:
  Style:
    - ../variations/styles.artistic.yaml         # 30 styles
    - ../variations/styles.photographic.yaml     # 20 styles

  Mood:
    - ../variations/moods.positive.yaml          # 15 moods
    - ../variations/moods.negative.yaml          # 12 moods
    - ../variations/moods.abstract.yaml          # 8 moods

  ColorPalette:
    - ../variations/colors.warm.yaml             # 10 palettes
    - ../variations/colors.cold.yaml             # 10 palettes
    - ../variations/colors.vibrant.yaml          # 8 palettes

  Subject:
    - ../variations/subjects.nature.yaml         # 15 sujets
    - ../variations/subjects.urban.yaml          # 12 sujets
    - ../variations/subjects.abstract.yaml       # 10 sujets

template: |
  {Style[10]}, {Mood[8]}, {ColorPalette[6]} color scheme,
  {Subject[12]}, artistic composition, creative lighting

generation:
  mode: random
  seed_mode: random
  max_images: 100

parameters:
  width: 768
  height: 512
  steps: 25
  cfg_scale: 8
  sampler: DPM++ SDE Karras
```

### Combinaisons possibles

```
Avec sélecteurs :
10 × 8 × 6 × 12 = 5,760 combinaisons possibles

Mode random génère 100 images parmi ces 5,760
```

### Workflow

1. **Générer le batch**
   ```bash
   sdgen generate -t prompts/creative_exploration.prompt.yaml
   ```

2. **Sélectionner les meilleures**
   - Parcourir les 100 images
   - Noter les seeds des images intéressantes
   - Identifier les patterns qui fonctionnent

3. **Affiner avec les résultats**
   - Créer un nouveau prompt avec les éléments retenus
   - Régénérer avec plus de contrôle

---

## Cas 3 : Production de variantes

**Objectif** : Générer des variantes d'un concept déjà approuvé par un client.

**Stratégie** :
- Template de base hérité
- Variations limitées et contrôlées
- Seeds progressives pour reproductibilité

### Template de base (approuvé)

**`templates/approved_concept.template.yaml`**

```yaml
version: '2.0'
name: 'Approved Concept - Product Shot'

# Setup technique approuvé
parameters:
  width: 832
  height: 1216
  steps: 30
  cfg_scale: 6
  sampler: DPM++ 2M
  scheduler: Karras
  enable_hr: true
  hr_scale: 1.5
  hr_upscaler: 4x_foolhardy_Remacri
  denoising_strength: 0.4

# Éléments de base approuvés
template: |
  product photography, luxury watch, professional lighting,
  white background, studio setup, high-end marketing,
  {prompt}
```

### Variantes avec héritage

**`prompts/variants_approved_concept.prompt.yaml`**

```yaml
version: '2.0'
name: 'Approved Concept Variants'
implements: ../templates/approved_concept.template.yaml

imports:
  Lighting:
    - ../variations/lighting.subtle.yaml         # 8 variations

  Angle:
    - ../variations/angles.product.yaml          # 6 variations

template: |
  {Lighting[3]}, {Angle[front,three_quarter,side]},
  dramatic shadows, depth of field

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 5000
  max_images: 9  # 3 × 3 = 9 images

output:
  session_name: approved_variants
```

### Résultat

**9 images** avec :
- Setup technique identique (approuvé)
- Lighting limité à 3 variations subtiles
- Angles limités à 3 vues principales
- Seeds reproductibles (5000-5008)

**Usage** : Présenter les variantes au client pour sélection finale

---

## Cas 4 : Test rapide

**Objectif** : Tester un nouveau prompt avant génération massive.

**Stratégie** :
- Sélecteurs très limités
- Mode random pour aperçu rapide
- Steps réduits pour vitesse

### Configuration de test

**`prompts/quick_test.prompt.yaml`**

```yaml
version: '2.0'
name: 'Quick Test - New Character'

imports:
  Expression:
    - ../variations/expressions.yaml  # 50 variations
  Outfit:
    - ../variations/outfits.yaml     # 30 variations
  Background:
    - ../variations/backgrounds.yaml  # 20 variations

template: |
  masterpiece, portrait, new_character_lora,
  {Expression[3]}, {Outfit[2]}, {Background[2]},
  detailed

generation:
  mode: random
  seed_mode: progressive
  seed: 42
  max_images: 12  # Test rapide : 3×2×2 = 12 images

parameters:
  width: 512
  height: 768
  steps: 15  # Steps réduits pour vitesse
  cfg_scale: 7
  sampler: Euler a  # Sampler rapide
```

### Workflow

1. **Test rapide (2-3 minutes)**
   ```bash
   sdgen generate -t prompts/quick_test.prompt.yaml
   ```

2. **Analyse des résultats**
   - Le personnage est-il correct ?
   - Les variations fonctionnent-elles ?
   - Ajustements nécessaires ?

3. **Production** (si test OK)
   ```yaml
   # Retirer les sélecteurs
   template: |
     {Expression}, {Outfit}, {Background}

   # Augmenter qualité
   parameters:
     steps: 25
     sampler: DPM++ 2M Karras

   generation:
     max_images: 500
   ```

---

## Cas 5 : Character consistency

**Objectif** : Maintenir un personnage cohérent à travers différentes scènes.

**Stratégie** :
- Utiliser héritage de template avec description fixe
- Varier uniquement l'action/scène
- Seeds progressives

### Template personnage (base)

**`templates/character_emma.template.yaml`**

```yaml
version: '2.0'
name: 'Character Emma - Base Template'

# Description fixe du personnage
template: |
  masterpiece, 1girl, emma_lora,
  28 years old, long brown hair with highlights,
  green eyes, oval face, subtle smile,
  athletic build, 170cm tall,
  {prompt},
  detailed face, detailed skin, consistent character

parameters:
  width: 512
  height: 768
  steps: 25
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

### Scènes variées

**`prompts/emma_scenes.prompt.yaml`**

```yaml
version: '2.0'
name: 'Emma in Various Scenes'
implements: ../templates/character_emma.template.yaml

imports:
  Scene:
    - ../variations/scenes.indoor.yaml   # 15 scènes
    - ../variations/scenes.outdoor.yaml  # 15 scènes

  Action:
    - ../variations/actions.daily.yaml   # 20 actions

  Lighting:
    - ../variations/lighting.natural.yaml  # 10 variations

template: |
  {Scene[5]}, {Action[4]}, {Lighting[3]},
  dynamic composition, cinematic angle

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 3000
  max_images: 60  # 5 × 4 × 3 = 60 images
```

### Résultat

**60 images** du même personnage (Emma) dans :
- 5 scènes différentes
- 4 actions différentes
- 3 lightings différents

**Le personnage reste cohérent** grâce au template de base fixe.

---

## Cas 6 : A/B Testing

**Objectif** : Comparer deux configurations avec même seed pour évaluer l'impact.

**Stratégie** :
- Seed mode `fixed` pour comparaison directe
- 2 fichiers de prompt identiques sauf la variable testée

### Test A : CFG 7

**`prompts/test_cfg7.prompt.yaml`**

```yaml
version: '2.0'
name: 'Test CFG Scale 7'

imports:
  Expression: ../variations/expressions.yaml

template: |
  masterpiece, portrait, {Expression[5]}, detailed

generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 1000
  max_images: 5

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7  # ← Variable testée
  sampler: DPM++ 2M Karras
```

### Test B : CFG 10

**`prompts/test_cfg10.prompt.yaml`**

```yaml
version: '2.0'
name: 'Test CFG Scale 10'

imports:
  Expression: ../variations/expressions.yaml

template: |
  masterpiece, portrait, {Expression[5]}, detailed

generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 1000  # ← Même seed !
  max_images: 5

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 10  # ← Variable testée
  sampler: DPM++ 2M Karras
```

### Résultat

**10 images** (5 pour chaque config) :
- Chaque paire partage la même seed
- Permet comparaison directe de l'impact du CFG

---

## Récapitulatif

✅ Vous avez maintenant des **exemples complets** pour :
- Entraînement de LoRA (500 images, combinatorial)
- Exploration créative (100 images random)
- Production de variantes contrôlées
- Tests rapides avant production
- Character consistency
- A/B Testing de paramètres

### Bonnes pratiques tirées des exemples

1. **Toujours tester** avec `max_images` réduit avant production
2. **Utiliser des sélecteurs** pour limiter les combinaisons explosives
3. **Héritage de templates** pour réutiliser les setups approuvés
4. **Seeds fixes** pour A/B testing
5. **Seeds progressives** pour datasets LoRA
6. **Seeds aléatoires** pour exploration créative

---

## Prochaines étapes

➡️ Consultez le [Troubleshooting](./troubleshooting.md) pour résoudre les problèmes courants

➡️ Explorez la [documentation technique](../../roadmap/template-system-spec.md) pour comprendre l'architecture

➡️ Créez votre propre workflow en combinant ces exemples

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~15 minutes
**Version du système** : V2.0
