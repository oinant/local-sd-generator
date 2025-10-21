# Selectors Reference

**Référence complète de tous les sélecteurs disponibles en V2.0**

---

## Vue d'ensemble

Les sélecteurs permettent de **contrôler quelles variations utiliser** sans modifier les fichiers de variations.

**Syntaxe générale** : `{PlaceholderName[selector]}`

---

## Tableau récapitulatif

| Sélecteur | Syntaxe | Effet | Exemple |
|-----------|---------|-------|---------|
| **Limite** | `[N]` | N variations aléatoires | `{Expression[5]}` |
| **Index** | `[#i,j,k]` | Indices spécifiques (0-based) | `{Expression[#0,2,4]}` |
| **Range** | `[#i-j]` | Intervalle d'indices (inclusif) | `{Expression[#0-10]}` |
| **Clés** | `[key1,key2]` | Clés nommées | `{Expression[happy,sad]}` |
| **Poids** | `[$W]` | Poids de boucle (combinatorial) | `{Expression[$10]}` |
| **Poids 0** | `[$0]` | Exclusion combinatoriale (random) | `{HairColor[$0]}` |
| **Combiné** | `[sel;$W]` | Sélection + poids | `{Expression[5;$10]}` |

---

## Sélecteurs de choix

### 1. Sélecteur de limite `[N]`

**Syntaxe** : `{Placeholder[N]}`

**Effet** : Tire **N variations aléatoires** parmi toutes les disponibles

**Exemples** :

```yaml
# 50 expressions disponibles
imports:
  Expression: ../variations/expressions.yaml

prompt: |
  portrait, {Expression[5]}, detailed

# Utilise seulement 5 expressions parmi les 50
```

**Notes** :
- Choix aléatoire à chaque exécution
- Garantit N variations uniques
- Si N > nombre de variations disponibles, utilise toutes les variations

---

### 2. Sélecteur par index `[#i,j,k]`

**Syntaxe** : `{Placeholder[#i,j,k]}`

**Effet** : Sélectionne les variations aux **indices spécifiques** (0-based, comma-separated)

**Exemples** :

```yaml
# variations/expressions.yaml
# Index 0: happy
# Index 1: sad
# Index 2: angry
# Index 3: neutral
# Index 4: surprised

prompt: |
  portrait, {Expression[#0,2,4]}, detailed

# Utilise : happy (0), angry (2), surprised (4)
```

**Notes** :
- Index commence à **0** (zero-based)
- Ordre préservé (0, 2, 4 génère dans cet ordre)
- Index hors limites sont **ignorés** (pas d'erreur)
- **Préfixe `#` obligatoire** : `[#1,5,8]` pas `[1,5,8]`

---

### 3. Sélecteur par clé `[key1,key2]`

**Syntaxe** : `{Placeholder[key1,key2,key3]}`

**Effet** : Sélectionne les variations **par leur nom de clé**

**Exemples** :

```yaml
# variations/expressions.yaml
# happy: smiling, cheerful expression
# sad: crying, tears
# angry: frowning, furious
# neutral: neutral expression

prompt: |
  portrait, {Expression[happy,neutral]}, detailed

# Utilise : happy et neutral seulement
```

**Notes** :
- Clés sensibles à la casse
- Ordre préservé
- Clés non existantes sont **ignorées** (pas d'erreur)
- Plus lisible que les index
- **Recommandé pour maintenance long-terme**
- ✅ Sélecteur le plus utilisé dans les exemples

**Détection automatique** :
Le parser détecte un key selector si :
- Contient une virgule : `happy,sad`
- OU commence par une majuscule : `BobCut`

---

### 2.5. Sélecteur de range `[#i-j]`

**Syntaxe** : `{Placeholder[#start-end]}`

**Effet** : Sélectionne un **intervalle d'indices** (inclusif, 0-based)

**Exemples** :

```yaml
# variations/expressions.yaml
# Index 0: happy
# Index 1: smiling
# Index 2: cheerful
# Index 3: joyful
# Index 4: excited
# Index 5: laughing
# ...

prompt: |
  portrait, {Expression[#0-5]}, detailed

# Utilise : indices 0, 1, 2, 3, 4, 5 (6 variations)
```

**Use case - Groupes logiques** :

```yaml
# variations/expressions.yaml organisé par catégories :
# Index 0-20: Positive expressions (happy, smiling, cheerful, etc.)
# Index 21-40: Negative expressions (sad, angry, crying, etc.)
# Index 41-50: Neutral expressions

# Générer seulement avec expressions positives
prompt: "{Expression[#0-20]}"

# Générer seulement avec expressions négatives
prompt: "{Expression[#21-40]}"

# Un seul index (équivalent à [#5])
prompt: "{Expression[#5-5]}"
```

**Notes** :
- Intervalle **inclusif** (start et end inclus)
- Index commence à **0** (zero-based)
- `start` doit être `<= end` (sinon ignoré)
- Si `end` dépasse le nombre de variations, utilise le maximum disponible
- **Préfixe `#` obligatoire** : `[#0-10]` pas `[0-10]`
- Plus lisible que `[#0,1,2,3,4,5,6,7,8,9,10]` pour les intervalles

**Comparaison avec index** :

```yaml
# Équivalents :
{Expression[#0-5]}              # Range (concis)
{Expression[#0,1,2,3,4,5]}      # Index (verbose)

# Range est préférable pour intervalles continus
# Index est préférable pour sélections spécifiques
{Expression[#0,5,10,15]}        # Index non consécutifs
```

---

## Sélecteur de contrôle

### 4. Sélecteur de poids `[$W]`

**Syntaxe** : `{Placeholder[$W]}`

**Effet** : Contrôle l'**ordre des boucles** en mode combinatorial

**Comportement** :
- **Poids faible** = boucle externe (change **moins** souvent)
- **Poids élevé** = boucle interne (change **plus** souvent)
- **Poids par défaut** = 1 (si pas de sélecteur)

**Exemples** :

```yaml
# Exemple avec poids explicites
prompt: "{Outfit[$2]}, {Angle[$10]}, {Expression[$20]}"

# Résultat (ordre des boucles) :
# Outfit (outer) → Angle (middle) → Expression (inner)
```

**Ordre de génération** :
```
Image 1:  Outfit=casual,  Angle=front, Expression=happy
Image 2:  Outfit=casual,  Angle=front, Expression=sad
Image 3:  Outfit=casual,  Angle=front, Expression=angry
Image 4:  Outfit=casual,  Angle=side,  Expression=happy
Image 5:  Outfit=casual,  Angle=side,  Expression=sad
Image 6:  Outfit=casual,  Angle=side,  Expression=angry
Image 7:  Outfit=formal,  Angle=front, Expression=happy
...
```

**Notes** :
- Seulement en mode `combinatorial`
- Ignoré en mode `random`
- Valeurs usuelles : 1, 5, 10, 20 (pas de limite)

---

### 5. Poids zéro `[$0]` - Exclusion combinatoriale

**Syntaxe** : `{Placeholder[$0]}`

**Effet** : **Exclut la variable des boucles combinatoriales**. La valeur est sélectionnée **aléatoirement** à chaque image.

**🔥 Use case critique** : Éviter l'explosion combinatoriale

**Problème** :
```yaml
# 5 Outfits × 3 Angles × 100 HairColors = 1500 images ❌
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$15]}"
```

**Solution** :
```yaml
# 5 Outfits × 3 Angles = 15 images ✅
# HairColor random à chaque image (pas de multiplication)
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"
```

**Résultat** :
```
Image 1:  Outfit=casual,  Angle=front, HairColor=blonde (random)
Image 2:  Outfit=casual,  Angle=side,  HairColor=red (random)
Image 3:  Outfit=casual,  Angle=back,  HairColor=black (random)
Image 4:  Outfit=formal,  Angle=front, HairColor=brown (random)
...
```

**Exemples pratiques** :

```yaml
# Character sheet avec détails cosmétiques aléatoires
version: '2.0'
name: 'Character Sheet with Random Details'

imports:
  Outfit: ../variations/outfits.yaml       # 5 variations
  Angle: ../variations/angles.yaml         # 4 variations
  Expression: ../variations/expressions.yaml # 10 variations
  HairColor: ../variations/haircolors.yaml  # 50 variations
  EyeColor: ../variations/eyecolors.yaml    # 30 variations

# Sans [$0] : 5 × 4 × 10 × 50 × 30 = 300,000 images ❌
# Avec [$0] : 5 × 4 × 10 = 200 images ✅

prompt: |
  1girl, {Outfit[$1]}, {Angle[$5]}, {Expression[$10]},
  {HairColor[$0]}, {EyeColor[$0]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Résultat : 200 images avec couleurs aléatoires
```

**Notes** :
- ✅ Variable présente dans chaque prompt
- ✅ Valeur change à chaque image
- ❌ Pas de garantie de voir toutes les valeurs
- ❌ Combinaison de couleurs non reproductible
- **Cas d'usage** : Détails cosmétiques, accessoires, effets

---

## Combinaison de sélecteurs

**Syntaxe** : `[selector1;selector2]`
**Séparateur** : `;` (point-virgule)

**Sélecteurs combinables** :
- Limite `[N]` + Poids `[$W]` ✅
- Index `[#i,j,k]` + Poids `[$W]` ✅
- Clés `[key1,key2]` + Poids `[$W]` ✅

**Exemples** :

```yaml
# Limite + poids
{Expression[5;$10]}
# → 5 random expressions, poids 10 (inner loop)

# Index + poids 0
{Angle[#0,2,4;$0]}
# → Seulement angles 0, 2, 4, mais random à chaque image

# Clés + poids
{Haircut[BobCut,Pixie,Long;$5]}
# → Seulement ces 3 coupes, poids 5
```

**Ordre des sélecteurs** :
```yaml
# Ces deux sont équivalents :
{Expression[5;$10]}
{Expression[$10;5]}
```

**Limitations** :
- ❌ Ne peut pas combiner Limite + Index + Clés ensemble
- ✅ Peut combiner n'importe quel choix (Limite/Index/Clés) avec Poids

---

## Exemples d'utilisation

### Test rapide avant production

```yaml
version: '2.0'
name: 'Quick Test'

imports:
  Expression: ../variations/expressions.yaml  # 50 disponibles
  Outfit: ../variations/outfits.yaml         # 30 disponibles
  Background: ../variations/backgrounds.yaml  # 20 disponibles

prompt: |
  portrait, {Expression[5]}, {Outfit[3]}, {Background[2]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 30  # 5 × 3 × 2 = 30 images
```

### Variations approuvées seulement

```yaml
version: '2.0'
name: 'Approved Only'

imports:
  Expression: ../variations/expressions.yaml
  Angle: ../variations/angles.yaml

prompt: |
  portrait, {Expression[happy,neutral,thoughtful]}, {Angle[front,side]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 6  # 3 × 2 = 6 images
```

### Character sheet avec poids

```yaml
version: '2.0'
name: 'Character Sheet'

imports:
  Outfit: ../variations/outfits.yaml
  Angle: ../variations/angles.yaml
  Expression: ../variations/expressions.yaml

prompt: |
  1girl, {Outfit[$1]}, {Angle[$5]}, {Expression[$10]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  filename_keys:
    - Outfit
    - Angle
    - Expression

# Outfit change le moins souvent (outer loop)
# Expression change le plus souvent (inner loop)
```

### Éviter l'explosion combinatoriale

```yaml
version: '2.0'
name: 'Character Dataset with Random Colors'

imports:
  Outfit: ../variations/outfits.yaml       # 8 variations
  Pose: ../variations/poses.yaml           # 12 variations
  Expression: ../variations/expressions.yaml # 15 variations
  HairColor: ../variations/haircolors.yaml  # 100 variations
  Accessories: ../variations/accessories.yaml # 50 variations

# Sans [$0] : 8 × 12 × 15 × 100 × 50 = 7,200,000 images ❌
# Avec [$0] : 8 × 12 × 15 = 1,440 images ✅

prompt: |
  1girl, {Outfit[$1]}, {Pose[$5]}, {Expression[$10]},
  {HairColor[$0]}, {Accessories[$0]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Résultat : 1,440 images avec couleurs/accessoires aléatoires
```

### Sélection d'index spécifiques

```yaml
version: '2.0'
name: 'Tested Variations Only'

imports:
  Expression: ../variations/expressions.yaml  # 50 total

# Après tests, on garde seulement certaines expressions
prompt: |
  portrait, {Expression[#0,5,12,18,25,33]}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Génère seulement avec les 6 expressions testées
```

### Groupes logiques avec range

```yaml
version: '2.0'
name: 'Positive Expressions Only'

imports:
  Expression: ../variations/expressions.yaml  # 50 total

# Fichier organisé :
# Index 0-20: Positive expressions (happy, smiling, cheerful, etc.)
# Index 21-40: Negative expressions (sad, angry, crying, etc.)
# Index 41-50: Neutral expressions

# Générer seulement avec expressions positives
prompt: |
  portrait, {Expression[#0-20]}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Génère 21 images (indices 0 à 20 inclus)
```

### Character sheet par catégories

```yaml
version: '2.0'
name: 'Standing Poses Only'

imports:
  Outfit: ../variations/outfits.yaml
  Pose: ../variations/poses.yaml       # 30 total
  Expression: ../variations/expressions.yaml

# Fichier poses.yaml organisé :
# Index 0-9: Standing poses
# Index 10-19: Sitting poses
# Index 20-29: Action poses

# Character sheet avec seulement standing poses
prompt: |
  1girl, {Outfit[$1]}, {Pose[#0-9;$5]}, {Expression[$10]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Génère avec seulement les 10 standing poses (range + poids)
```

---

## Règles de syntaxe

### ✅ Syntaxe correcte

```yaml
{Expression}                    # Toutes les variations
{Expression[5]}                 # 5 random
{Expression[#0,2,4]}            # Indices 0, 2, 4
{Expression[#0-10]}             # Range 0 à 10 (inclusif)
{Expression[happy,sad,angry]}   # Clés nommées
{Expression[$10]}               # Poids 10
{Expression[$0]}                # Poids 0 (random)
{Expression[5;$10]}             # 5 random + poids 10
{Expression[#0,2;$0]}           # Index 0,2 + random
{Expression[#0-10;$5]}          # Range 0-10 + poids 5
{Expression[happy,sad;$5]}      # Clés + poids 5
```

### ❌ Syntaxe incorrecte

```yaml
{Expression:5}                  # ❌ Utiliser [5] pas :5
{Expression[1,5,8]}             # ❌ Manque # pour indices ([#1,5,8])
{Expression[0-10]}              # ❌ Manque # pour range ([#0-10])
{Expression[#10-5]}             # ❌ start > end (invalide)
{Expression[weight:5]}          # ❌ Utiliser [$5] pas [weight:5]
{Expression[random:10]}         # ❌ Utiliser [10] pas [random:10]
{Expression[5,#0,2]}            # ❌ Ne peut combiner limit + index
{Expression[#0-5,10-15]}        # ❌ Multiple ranges non supporté
```

---

## Performance

### Impact sur le nombre de combinaisons

**Sans sélecteurs** :
```yaml
# 50 expressions × 30 outfits × 20 backgrounds = 30,000 images
imports:
  Expression: ../variations/expressions.yaml   # 50
  Outfit: ../variations/outfits.yaml          # 30
  Background: ../variations/backgrounds.yaml   # 20
```

**Avec sélecteurs de limite** :
```yaml
# 5 × 3 × 2 = 30 images
prompt: |
  {Expression[5]}, {Outfit[3]}, {Background[2]}
```

**Réduction** : 99.9% (30,000 → 30)

**Avec poids 0** :
```yaml
# 5 Outfits × 3 Angles = 15 images
# HairColor random (pas de multiplication)
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"

imports:
  Outfit: outfits.yaml      # 5
  Angle: angles.yaml        # 3
  HairColor: colors.yaml    # 100
```

**Sans [$0]** : 5 × 3 × 100 = **1,500 images**
**Avec [$0]** : 5 × 3 = **15 images**
**Réduction** : 99% (1,500 → 15)

---

## Cas d'usage par sélecteur

| Sélecteur | Cas d'usage principal | Fréquence d'utilisation |
|-----------|----------------------|------------------------|
| `[N]` | Test rapide, échantillonnage | Moyen |
| `[#i,j,k]` | Variations testées et approuvées | Faible |
| `[#i-j]` | Groupes logiques, catégories | Moyen |
| `[key1,key2]` | Variations nommées, maintenabilité | ✅ **Élevé** |
| `[$W]` | Character sheets, contrôle ordre | Moyen |
| `[$0]` | Éviter explosion combinatoriale | 🔥 **Critique** |
| `[sel;$W]` | Combinaison sélection + poids | Faible |

---

## Comparaison des modes de génération

### Mode Combinatorial

**Sans poids** :
```yaml
prompt: "{Outfit}, {Angle}, {Expression}"
# Ordre : apparition dans le template (gauche → droite)
```

**Avec poids** :
```yaml
prompt: "{Outfit[$1]}, {Angle[$5]}, {Expression[$10]}"
# Ordre : poids croissant (1 → 5 → 10)
```

**Avec poids 0** :
```yaml
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"
# Outfit × Angle = combinaisons
# HairColor = random (pas de multiplication)
```

### Mode Random

**Tous les sélecteurs de poids sont ignorés** :
```yaml
prompt: "{Outfit[$1]}, {Angle[$5]}, {Expression[$10]}"
# Poids ignorés, ordre totalement random
```

**Poids 0 n'a pas d'effet** :
```yaml
prompt: "{Outfit}, {Angle}, {HairColor[$0]}"
# Tout est déjà random, [$0] n'a pas d'effet
```

---

## Voir aussi

- **[Template Syntax](template-syntax.md)** - Syntaxe complète des templates
- **[CLI Commands](cli-commands.md)** - Génération et validation
- **[Selector Audit Report](../../tooling/selector-audit-2025-01-20.md)** - Analyse doc vs implémentation
- **[Examples](../usage/examples.md)** - Cas d'usage complets

---

**Dernière mise à jour** : 2025-01-20
**Version du système** : V2.0
**Status** : ✅ Documentation corrigée (audit 2025-01-20) + Range selector implémenté
