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
| **Index** | `[#i,j,k]` | Indices spécifiques | `{Expression[#0,2,4]}` |
| **Clés** | `[key1,key2]` | Clés nommées | `{Expression[happy,sad]}` |
| **Range** | `[#i-j]` | Intervalle d'indices | `{Expression[#0-10]}` |
| **Random** | `[random:N]` | N variations aléatoires | `{Expression[random:5]}` |
| **Weight** | `[weight:W]` | Poids de boucle | `{Expression[weight:10]}` |

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

template: |
  portrait, {Expression[5]}, detailed

# Utilise seulement 5 expressions parmi les 50
```

**Notes** :
- Choix aléatoire à chaque exécution
- Garantit N variations uniques
- Erreur si N > nombre de variations disponibles

---

### 2. Sélecteur par index `[#i,j,k]`

**Syntaxe** : `{Placeholder[#i,j,k]}`

**Effet** : Sélectionne les variations aux **indices spécifiques** (0-based)

**Exemples** :

```yaml
# variations/expressions.yaml
# Index 0: happy
# Index 1: sad
# Index 2: angry
# Index 3: neutral
# Index 4: surprised

template: |
  portrait, {Expression[#0,2,4]}, detailed

# Utilise : happy (0), angry (2), surprised (4)
```

**Notes** :
- Index commence à 0
- Ordre préservé (0, 2, 4 génère dans cet ordre)
- Erreur si index >= nombre de variations
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

template: |
  portrait, {Expression[happy,neutral]}, detailed

# Utilise : happy et neutral seulement
```

**Notes** :
- Clés sensibles à la casse
- Ordre préservé
- Erreur si clé n'existe pas
- Plus lisible que les index
- Recommandé pour maintenance long-terme

---

### 4. Sélecteur de range `[#i-j]`

**Syntaxe** : `{Placeholder[#i-j]}`

**Effet** : Sélectionne un **intervalle d'indices** (inclusif)

**Exemples** :

```yaml
template: |
  portrait, {Expression[#0-5]}, detailed

# Utilise les indices 0, 1, 2, 3, 4, 5 (6 variations)
```

```yaml
template: |
  portrait, {Expression[#10-19]}, detailed

# Utilise les indices 10 à 19 (10 variations)
```

**Notes** :
- Intervalle inclusif (début et fin inclus)
- Erreur si `j` >= nombre de variations
- Erreur si `i` > `j`
- **Préfixe `#` obligatoire** : `[#0-10]` pas `[0-10]`

---

### 5. Sélecteur random `[random:N]`

**Syntaxe** : `{Placeholder[random:N]}`

**Effet** : Tire **N variations aléatoires** (syntaxe alternative à `[N]`)

**Exemples** :

```yaml
template: |
  portrait, {Expression[random:10]}, detailed

# Équivalent à {Expression[10]}
```

**Notes** :
- Identique à `[N]`
- Syntaxe plus explicite
- Utile pour combiner avec d'autres sélecteurs

---

## Sélecteur de contrôle

### 6. Sélecteur de poids `[weight:W]`

**Syntaxe** : `{Placeholder[weight:W]}`

**Effet** : Contrôle l'**ordre des boucles** en mode combinatorial

**Comportement** :
- **Poids faible** = boucle externe (change moins souvent)
- **Poids élevé** = boucle interne (change plus souvent)

**Exemples** :

```yaml
imports:
  Outfit:
    source: ../variations/outfits.yaml
    weight: 1   # Boucle externe
  Angle:
    source: ../variations/angles.yaml
    weight: 10  # Boucle intermédiaire
  Expression:
    source: ../variations/expressions.yaml
    weight: 20  # Boucle interne
```

**Résultat** :
```
Image 1:  Outfit=casual, Angle=front, Expression=happy
Image 2:  Outfit=casual, Angle=front, Expression=sad
Image 3:  Outfit=casual, Angle=front, Expression=angry
Image 4:  Outfit=casual, Angle=side,  Expression=happy
Image 5:  Outfit=casual, Angle=side,  Expression=sad
...
```

**Notes** :
- Seulement en mode `combinatorial`
- Ignoré en mode `random`
- Défaut : ordre d'apparition dans le template

---

## Combinaison de sélecteurs

**Note** : Actuellement, les sélecteurs ne peuvent **pas** être combinés dans la même déclaration.

**❌ Non supporté** :
```yaml
# Ceci ne fonctionne pas
template: |
  {Expression[random:10;weight:5]}
```

**✅ Supporté** :
```yaml
# Utiliser imports avec config
imports:
  Expression:
    source: ../variations/expressions.yaml
    weight: 5

template: |
  {Expression[random:10]}
```

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

template: |
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

template: |
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
  Outfit:
    source: ../variations/outfits.yaml
    weight: 1   # Change le moins souvent
  Angle:
    source: ../variations/angles.yaml
    weight: 10
  Expression:
    source: ../variations/expressions.yaml
    weight: 20  # Change le plus souvent

template: |
  1girl, {Outfit}, {Angle}, {Expression}

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
```

### Range pour groupes logiques

```yaml
version: '2.0'
name: 'Positive Expressions Only'

# variations/expressions.yaml
# Index 0-20: Positive expressions (happy, smiling, cheerful, etc.)
# Index 21-40: Negative expressions (sad, angry, crying, etc.)
# Index 41-50: Neutral expressions

imports:
  Expression: ../variations/expressions.yaml

template: |
  portrait, {Expression[#0-20]}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

# Génère seulement avec les expressions positives
```

---

## Règles de syntaxe

### ✅ Syntaxe correcte

```yaml
{Expression}                    # Toutes les variations
{Expression[5]}                 # 5 random
{Expression[random:5]}          # 5 random (syntaxe alternative)
{Expression[#0,2,4]}            # Indices 0, 2, 4
{Expression[happy,sad,angry]}   # Clés nommées
{Expression[#0-10]}             # Range 0 à 10
{Expression[weight:10]}         # Poids 10
```

### ❌ Syntaxe incorrecte

```yaml
{Expression:5}                  # ❌ Utiliser [5] pas :5
{Expression[1,5,8]}             # ❌ Manque # pour indices
{Expression[$5]}                # ❌ Pas de $ pour weight
{Expression[0-10]}              # ❌ Manque # pour range
{Expression[random:10,weight:5]} # ❌ Combinaison non supportée
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

**Avec sélecteurs** :
```yaml
# 5 × 3 × 2 = 30 images
template: |
  {Expression[5]}, {Outfit[3]}, {Background[2]}
```

**Réduction** : 99.9% (30,000 → 30)

---

## Cas d'usage par sélecteur

| Sélecteur | Cas d'usage principal |
|-----------|----------------------|
| `[N]` | Test rapide, échantillonnage |
| `[#i,j,k]` | Variations testées et approuvées |
| `[key1,key2]` | Variations nommées, maintenabilité |
| `[#i-j]` | Groupes logiques, catégories |
| `[random:N]` | Échantillonnage explicite |
| `[weight:W]` | Character sheets, datasets organisés |

---

## Voir aussi

- **[Template Syntax](template-syntax.md)** - Syntaxe complète des templates
- **[CLI Commands](cli-commands.md)** - Génération et validation
- **[Templates Advanced Guide](../guide/4-templates-advanced.md)** - Explications détaillées
- **[Examples](../guide/examples.md)** - Cas d'usage complets

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
