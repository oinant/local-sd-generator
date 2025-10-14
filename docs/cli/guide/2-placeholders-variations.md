# Placeholders & Variations

**Découvrez comment générer automatiquement des dizaines d'images avec des variations contrôlées.**

📚 **Prérequis** : [Prompting Standalone](./1-prompting-standalone.md)

⏱️ **Durée de lecture** : 10 minutes

---

## Le problème : Duplication de code

Dans le guide précédent, vous avez appris à générer des images avec un **prompt fixe**.

Mais que faire si vous voulez tester **5 expressions différentes** ?

### Approche naïve (à éviter)

Créer **5 fichiers** :

```yaml
# portrait_happy.prompt.yaml
template: |
  masterpiece, portrait, smiling, cheerful, detailed

# portrait_sad.prompt.yaml
template: |
  masterpiece, portrait, crying, melancholic, detailed

# portrait_angry.prompt.yaml
template: |
  masterpiece, portrait, frowning, angry, detailed

# portrait_neutral.prompt.yaml
template: |
  masterpiece, portrait, calm, neutral expression, detailed

# portrait_surprised.prompt.yaml
template: |
  masterpiece, portrait, surprised, wide eyes, detailed
```

**Problèmes** :
- ❌ **5 fichiers** à créer et maintenir
- ❌ Si vous changez "masterpiece, portrait" → modifier 5 fichiers
- ❌ Impossible de générer toutes les combinaisons automatiquement

---

## La solution : Placeholders & Variations

### Concept

**Placeholder** : Variable dans le prompt (`{Expression}`)
**Variations** : Fichier contenant les valeurs possibles

```yaml
# 1 seul fichier prompt
template: |
  masterpiece, portrait, {Expression}, detailed

# 1 fichier de variations
# expressions.yaml
happy: smiling, cheerful
sad: crying, melancholic
angry: frowning, angry
neutral: calm, neutral expression
surprised: surprised, wide eyes
```

**Résultat** : Le système génère automatiquement les 5 prompts !

---

## Votre premier placeholder

### Étape 1 : Créer le fichier de variations

**`variations/expressions.yaml`**

```yaml
happy: smiling, cheerful expression
sad: crying, tears, melancholic look
neutral: calm face, neutral expression
```

**Format** :
- `clé: valeur`
- La **clé** est un identifiant unique
- La **valeur** est le texte qui sera inséré dans le prompt

### Étape 2 : Créer le prompt avec placeholder

**`prompts/portrait_variations.prompt.yaml`**

```yaml
version: '2.0'
name: 'Portrait with Expressions'

# Importer le fichier de variations
imports:
  Expression: ../variations/expressions.yaml

# Utiliser le placeholder {Expression}
template: |
  masterpiece, beautiful portrait, {Expression}, detailed

generation:
  mode: combinatorial  # Génère toutes les combinaisons
  seed_mode: progressive
  seed: 1000
  max_images: 3  # 3 expressions

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

### Étape 3 : Générer

```bash
sdgen generate -t prompts/portrait_variations.prompt.yaml
```

### Résultat

**3 images générées automatiquement** :

```
Image 1 (seed 1000): masterpiece, beautiful portrait, smiling, cheerful expression, detailed
Image 2 (seed 1001): masterpiece, beautiful portrait, crying, tears, melancholic look, detailed
Image 3 (seed 1002): masterpiece, beautiful portrait, calm face, neutral expression, detailed
```

**Avantages** :
- ✅ 1 seul fichier prompt
- ✅ Facile à maintenir
- ✅ Ajout d'une variation = juste modifier expressions.yaml
- ✅ Génération automatique

---

## Comment ça marche ?

### 1. Détection du placeholder

Le système détecte `{Expression}` dans le template.

### 2. Chargement des variations

```yaml
imports:
  Expression: ../variations/expressions.yaml
```

Le système charge le fichier et lit les 3 variations.

### 3. Remplacement

Pour chaque variation, le placeholder est remplacé :

```
Template : masterpiece, portrait, {Expression}, detailed

Variation 1 : {Expression} → smiling, cheerful expression
Résultat   : masterpiece, portrait, smiling, cheerful expression, detailed

Variation 2 : {Expression} → crying, tears, melancholic look
Résultat   : masterpiece, portrait, crying, tears, melancholic look, detailed

...
```

### 4. Génération

Le système envoie chaque prompt à Stable Diffusion avec une seed différente.

---

## Ajouter des variations

### Éditer le fichier de variations

**`variations/expressions.yaml`**

```yaml
happy: smiling, cheerful expression
sad: crying, tears, melancholic look
neutral: calm face, neutral expression
angry: frowning, angry look, intense gaze  # ← Ajouté
surprised: surprised expression, wide eyes  # ← Ajouté
```

### Régénérer

```bash
sdgen generate -t prompts/portrait_variations.prompt.yaml
```

**Résultat** : **5 images** au lieu de 3 (sans modifier le fichier prompt !)

---

## Plusieurs placeholders

Vous pouvez utiliser **plusieurs placeholders** dans le même template.

### Fichiers de variations

**`variations/expressions.yaml`**
```yaml
happy: smiling, cheerful
sad: crying, melancholic
neutral: calm, neutral
```

**`variations/outfits.yaml`**
```yaml
casual: jeans and t-shirt
formal: elegant dress
```

### Template

**`prompts/portrait_multi.prompt.yaml`**

```yaml
version: '2.0'
name: 'Portrait Multi-Variations'

imports:
  Expression: ../variations/expressions.yaml  # 3 variations
  Outfit: ../variations/outfits.yaml         # 2 variations

template: |
  masterpiece, portrait, {Expression}, {Outfit}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 2000
  max_images: 6  # 3 × 2 = 6 combinaisons
```

### Résultat

**6 images** (toutes les combinaisons) :

```
Image 1: ... smiling, cheerful, jeans and t-shirt ...
Image 2: ... smiling, cheerful, elegant dress ...
Image 3: ... crying, melancholic, jeans and t-shirt ...
Image 4: ... crying, melancholic, elegant dress ...
Image 5: ... calm, neutral, jeans and t-shirt ...
Image 6: ... calm, neutral, elegant dress ...
```

**Formule** : `3 expressions × 2 outfits = 6 images`

---

## Mode `combinatorial` vs `random`

### Mode `combinatorial`

```yaml
generation:
  mode: combinatorial
  max_images: 10  # Optionnel
```

**Génère** : **Toutes** les combinaisons possibles (ou jusqu'à `max_images`)

**Usage** :
- Dataset complet
- Garantir la couverture exhaustive
- Entraînement LoRA

### Mode `random`

```yaml
generation:
  mode: random
  max_images: 10  # Tire 10 combinaisons aléatoires
```

**Génère** : N combinaisons aléatoires uniques

**Usage** :
- Exploration rapide
- Tester sans tout générer
- Génération créative

### Comparaison

| Mode | Résultat | Exemple (3×2) |
|------|----------|---------------|
| `combinatorial` | Toutes les combinaisons | 6 images |
| `random` (max:4) | 4 combinaisons aléatoires | 4 images parmi 6 possibles |

---

## Statistiques de variations

Depuis 2025-10-13, le CLI affiche automatiquement les variations détectées avant génération :

```
╭─────────────────── Detected Variations ──────────────────╮
│   Expression: 5 variations                                │
│   Outfit: 3 variations                                    │
│   Background: 4 variations                                │
│                                                           │
│   Total combinations: 60                                  │
│   Generation mode: combinatorial                          │
│   Will generate: 60 images                                │
╰───────────────────────────────────────────────────────────╯
```

**Avantages** :
- ✅ Savoir combien d'images seront générées
- ✅ Vérifier que tous les placeholders ont des variations
- ✅ Détecter les erreurs avant génération

---

## Règles de nommage

### Placeholder

**Syntaxe** : `{NomDuPlaceholder}`

**Règles** :
- ✅ PascalCase recommandé : `{Expression}`, `{HairColor}`, `{Outfit}`
- ✅ Sensible à la casse : `{Expression}` ≠ `{expression}`
- ❌ Pas d'espaces : `{Hair Color}` invalide
- ❌ Pas de caractères spéciaux : `{Hair-Color}` invalide

### Fichier de variations

**Format** : `nom.yaml`

**Contenu** : Dictionnaire YAML
```yaml
cle1: valeur1
cle2: valeur2, avec plusieurs mots
cle3: valeur3
```

### Import

**Syntaxe** : Chemin relatif au fichier YAML

```yaml
imports:
  Expression: ../variations/expressions.yaml
  # ../ remonte d'un niveau
```

---

## Erreurs courantes

### Placeholder non défini

**Erreur** :
```
ValueError: Unresolved placeholders: Outfit
```

**Cause** : Vous utilisez `{Outfit}` dans le template mais pas d'import correspondant.

**Solution** :
```yaml
imports:
  Outfit: ../variations/outfits.yaml  # ← Ajouter
```

### Fichier de variations introuvable

**Erreur** :
```
FileNotFoundError: variations/expressions.yaml
```

**Cause** : Chemin incorrect

**Solution** : Vérifier le chemin relatif
```yaml
# Si le prompt est dans prompts/
imports:
  Expression: ../variations/expressions.yaml  # Correct

# PAS
imports:
  Expression: variations/expressions.yaml  # Incorrect
```

### Format de variation invalide

**Format YAML valide** :
```yaml
happy: smiling
sad: crying
```

**Format invalide** :
```yaml
- happy: smiling  # ← Liste au lieu de dict
- sad: crying
```

---

## Récapitulatif

✅ Vous maîtrisez maintenant :
- Le concept de placeholder (`{Nom}`)
- Créer des fichiers de variations
- Utiliser `imports:` pour charger les variations
- Générer automatiquement des combinaisons
- Mode `combinatorial` vs `random`
- Interpréter les statistiques de variations

### Limites actuelles

Pour l'instant, vous savez :
- ✅ 1 placeholder → N images
- ✅ M placeholders → M × N × ... images

**Mais** :
- ❌ Que faire si vous avez 50 expressions et vous voulez seulement en tester 5 ?
- ❌ Comment réutiliser un setup de base sans dupliquer ?
- ❌ Comment organiser des templates complexes ?

➡️ **Solutions** : Les features avancées !

---

## Prochaine étape

Passez à [Templates Basics →](./3-templates-basics.md) pour découvrir :
- Multi-variations complexes
- Organisation de projet
- Modes de seed détaillés
- Bonnes pratiques

Puis à [Templates Advanced →](./4-templates-advanced.md) pour :
- **Sélecteurs** : Limiter le nombre de variations
- **Héritage** : Réutiliser des templates de base
- **Chunks** : Blocs réutilisables

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~10 minutes
**Version du système** : V2.0
