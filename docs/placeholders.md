# Système de Placeholders - Guide Complet

Le système de placeholders est au cœur du générateur d'images avec variations. Il permet de créer des prompts dynamiques et de générer automatiquement toutes les combinaisons ou variations aléatoires.

---

## Table des matières

1. [Concepts de base](#concepts-de-base)
2. [Format des placeholders](#format-des-placeholders)
3. [Fichiers de variations](#fichiers-de-variations)
4. [Options avancées](#options-avancées)
5. [Système de priorité des boucles](#système-de-priorité-des-boucles)
6. [Negative Prompt Placeholders](#negative-prompt-placeholders)
7. [Variations imbriquées](#variations-imbriquées)
8. [Fichiers multiples](#fichiers-multiples)
9. [Exemples pratiques](#exemples-pratiques)
10. [Bonnes pratiques](#bonnes-pratiques)

---

## Concepts de base

### Qu'est-ce qu'un placeholder ?

Un **placeholder** est une balise dans votre prompt qui sera remplacée par différentes valeurs lors de la génération.

**Format de base :**
```
{NomDuPlaceholder}
```

**Exemple simple :**
```python
prompt_template = "masterpiece, {Expression}, beautiful girl"
```

Si le fichier `expressions.txt` contient :
```
smiling
sad
angry
```

Le générateur créera automatiquement 3 prompts :
- `"masterpiece, smiling, beautiful girl"`
- `"masterpiece, sad, beautiful girl"`
- `"masterpiece, angry, beautiful girl"`

### Placeholders multiples

Vous pouvez utiliser plusieurs placeholders dans un même prompt :

```python
prompt_template = "masterpiece, {Expression}, {Angle}, {Lighting}, beautiful girl"
```

Avec 3 expressions × 5 angles × 4 lightings = **60 combinaisons possibles** !

---

## Format des placeholders

### Tableau récapitulatif

| Syntaxe | Effet | Exemple |
|---------|-------|---------|
| `{Name}` | Toutes les variations | `{Hair}` |
| `{Name:N}` | N variations aléatoires | `{Hair:5}` |
| `{Name:0}` | Supprime le placeholder | `{Hair:0}` |
| `{Name:#\|1\|5}` | Index spécifiques | `{Hair:#\|1\|5\|22}` |
| `{Name:$P}` | Priorité P (ordre boucles) | `{Outfit:$2}` |
| `{Name:N$P}` | Limite + priorité | `{Hair:10$5}` |
| `{Name:#\|1\|5$P}` | Index + priorité | `{Hair:#\|1\|5$8}` |

### 1. Toutes les variations (défaut)

```
{PlaceholderName}
```

Utilise **toutes** les variations disponibles dans le fichier.

**Exemple :**
```python
prompt = "portrait, {Hair}, beautiful"
```

### 2. Limitation aléatoire

```
{PlaceholderName:N}
```

Sélectionne aléatoirement **N variations** parmi toutes celles disponibles.

**Exemple :**
```python
prompt = "portrait, {Hair:5}, beautiful"
# Utilise 5 coiffures aléatoires parmi toutes celles disponibles
```

**Cas d'usage :**
- Tester rapidement un sous-ensemble
- Réduire le nombre de combinaisons
- Explorer sans tout générer

### 3. Suppression du placeholder

```
{PlaceholderName:0}
```

**Supprime complètement** ce placeholder du prompt final.

**Exemple :**
```python
# Avec background
prompt1 = "portrait, {Hair}, {Background}, beautiful"
# → "portrait, long blonde hair, sunset sky, beautiful"

# Sans background
prompt2 = "portrait, {Hair}, {Background:0}, beautiful"
# → "portrait, long blonde hair, beautiful"
```

**Cas d'usage :**
- Tests A/B pour mesurer l'impact d'un élément
- Générer des versions avec et sans un attribut
- Prompts conditionnels

### 4. Sélection d'index spécifiques

```
{PlaceholderName:#|index1|index2|index3}
```

Sélectionne uniquement les variations aux **index spécifiques** (commence à 0).

**Exemple :**
```python
prompt = "portrait, {Hair:#|1|5|22}, beautiful"
# Utilise seulement les variations aux index 1, 5 et 22
```

**Cas d'usage :**
- Tester des combinaisons spécifiques qui fonctionnent bien
- Reproduire des résultats avec des variations exactes
- Affiner progressivement les variations utilisées
- Créer des sets cohérents

**Workflow typique :**
```python
# 1. Génération exploratoire avec toutes les variations
prompt = "{Hair}, {Expression}"

# 2. Identifier les meilleures (ex: index 1, 5, 8 pour Hair et 2, 7 pour Expression)

# 3. Régénérer seulement les bonnes combinaisons
prompt = "{Hair:#|1|5|8}, {Expression:#|2|7}"
```

---

## Système de priorité des boucles

### Concept

En mode **combinatorial**, le système génère des boucles imbriquées. Le **poids de priorité** contrôle l'ordre d'imbrication des boucles.

### Format

```
{PlaceholderName:$poids}
{PlaceholderName:N$poids}
{PlaceholderName:#|1|5$poids}
```

**Règle importante :**
- **Plus petit poids** = boucle **extérieure** (change moins souvent)
- **Plus grand poids** = boucle **intérieure** (change plus souvent)

### Exemple sans priorité

```python
prompt = "{Outfit}, {Angle}"
```

**Ordre par défaut** (alphabétique) :
```
Angle=front, Outfit=dress
Angle=front, Outfit=shirt
Angle=side, Outfit=dress
Angle=side, Outfit=shirt
```

### Exemple avec priorité

```python
prompt = "{Outfit:$2}, {Angle:$10}"
```

**Ordre contrôlé** (Outfit en boucle extérieure) :
```
Outfit=dress, Angle=front
Outfit=dress, Angle=side
Outfit=shirt, Angle=front
Outfit=shirt, Angle=side
```

### Cas d'usage

**Génération de character sheets :**
```python
prompt = "{Outfit:$1}, {Angle:$10}, {Expression:$20}"
```

Génère :
1. Toutes les expressions et angles pour **Outfit 1**
2. Puis toutes les expressions et angles pour **Outfit 2**
3. Etc.

**Organisation logique** : 1 bloc par outfit contenant toutes les variations d'angles et d'expressions.

### Combinaisons possibles

Vous pouvez combiner priorité avec d'autres options :

```python
# Limite + priorité
"{Expression:10$5}"  # 10 variations aléatoires, poids 5

# Index + priorité
"{Angle:#|0|2|4$8}"  # Index 0,2,4 avec poids 8

# Priorité seule
"{Lighting:$3}"  # Toutes les variations, poids 3
```

---

## Fichiers de variations

### Formats supportés

#### Format 1 : Clé → Valeur

```
# expressions.txt
happy→smiling, cheerful expression
sad→sad, melancholic look
angry→angry, frowning
surprised→surprised, wide eyes
```

La clé (`happy`) est utilisée en interne, la valeur est insérée dans le prompt.

#### Format 2 : Numéro → Valeur

```
# angles.txt
1→front view
2→side view, profile
3→3/4 view
4→back view
```

Le numéro est ignoré, une clé est générée automatiquement depuis la valeur.

#### Format 3 : Valeur simple

```
# styles.txt
realistic
anime style
oil painting
watercolor
digital art
```

La clé est générée automatiquement depuis la valeur (`realistic` → clé `realistic`).

### Commentaires et lignes vides

```
# Ceci est un commentaire

# Expressions faciales
happy→smiling
sad→crying

# Ligne vide ci-dessus ignorée
```

- Lignes commençant par `#` : ignorées
- Lignes vides : ignorées

### Encodage

Par défaut **UTF-8**. Si vous avez des problèmes d'encodage :

```python
from variation_loader import load_variations_from_file

variations = load_variations_from_file("file.txt", encoding='latin1')
# ou
variations = load_variations_from_file("file.txt", encoding='cp1252')
```

---

## Negative Prompt Placeholders

### Concept

Vous pouvez maintenant utiliser des **placeholders dans le negative prompt** pour varier facilement les negative prompts selon les modèles (SDXL, Illustrious, Pony, etc.).

### Utilisation de base

```python
generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Subject}, highly detailed",
    negative_prompt="{NegStyle}",
    variation_files={
        "Subject": "subjects.txt",
        "NegStyle": "negative_styles.txt"
    }
)
```

**Fichier `negative_styles.txt` :**
```
sdxl→low quality, bad anatomy, blurry, watermark
illustrious→worst quality, low quality, displeasing, very displeasing
pony→3d, worst quality, low quality, bad anatomy, text
none→
```

**Résultat :** Chaque sujet sera généré avec chaque style de negative prompt.

### Placeholders partagés

Vous pouvez utiliser le **même placeholder** dans le prompt et le negative :

```python
prompt_template = "{Style} artwork, beautiful landscape"
negative_prompt = "bad {Style}, low quality"
```

**Exemple :**
- Quand `Style = "anime"` → Prompt: `"anime artwork..."`, Negative: `"bad anime, low quality"`
- Quand `Style = "realistic"` → Prompt: `"realistic artwork..."`, Negative: `"bad realistic, low quality"`

### Tous les sélecteurs fonctionnent

```python
# Limite à 2 negative styles
negative_prompt = "{NegStyle:2}"

# Sélection d'index spécifiques
negative_prompt = "{NegStyle:#|0|2}"

# Avec priorité
negative_prompt = "{NegStyle:$5}"
```

### Cas d'usage

**1. Comparaison de modèles :**
```python
# Teste le même prompt avec différents negatives spécifiques aux modèles
negative_prompt = "{ModelNegative}"
```

**2. Tests de filtres de qualité :**
```python
negative_prompt = "{QualityFilter}"
# Fichier: "low quality", "worst quality, low quality", "worst quality, bad anatomy", etc.
```

**3. Combinaison prompt + negative :**
```python
prompt_template = "{Character}, {Pose}"
negative_prompt = "{NegStyle}, {Defect}"
# Génère toutes les combinaisons : character × pose × negstyle × defect
```

### Documentation complète

Pour plus de détails et d'exemples, consultez : `docs/cli/usage/negative-prompt-variations.md`

---

## Variations imbriquées

### Concept

Les **variations imbriquées** permettent de définir des sous-variations **à l'intérieur** des fichiers de variations.

### Format

```
{|option1|option2|option3}
```

**Important :** L'option vide est **toujours incluse** (permet "avec" ou "sans").

### Exemple simple

**Fichier `poses.txt` :**
```
standing
sitting
lying down
kneeling,{|hands on ground|arms up}
```

**Résultat chargé :**
```
standing
sitting
lying down
kneeling                    ← option vide
kneeling,hands on ground    ← option 1
kneeling,arms up            ← option 2
```

**3 variations deviennent 6 variations** automatiquement !

### Exemple complexe

**Fichier :**
```
dynamic pose,{|jumping},{|motion blur|motion blur,speed lines}
```

**Résultat expansé (6 variations) :**
```
dynamic pose
dynamic pose,jumping
dynamic pose,motion blur
dynamic pose,jumping,motion blur
dynamic pose,motion blur,speed lines
dynamic pose,jumping,motion blur,speed lines
```

**Explication :**
- Premier `{|}` : 2 options (vide, "jumping")
- Second `{|}` : 3 options (vide, "motion blur", "motion blur,speed lines")
- Total : 2 × 3 = **6 combinaisons**

### Plusieurs placeholders imbriqués

```
base pose,{|modifier1},{|modifier2},{|modifier3}
```

Génère : 2 × 2 × 2 = **8 variations** (toutes les combinaisons possibles)

### Cas d'usage

**Variations optionnelles :**
```
standing,{|arms crossed|hands in pockets}
# Génère : "standing", "standing,arms crossed", "standing,hands in pockets"
```

**Variations graduelles :**
```
blushing,{|light blush|heavy blush|blush,embarrassed}
```

**Combinaisons d'attributs :**
```
rainy scene,{|umbrella},{|wet ground|puddles}
# 4 variations : base, avec umbrella, avec wet ground/puddles, combinaisons
```

---

## Fichiers multiples

### Concept

Vous pouvez maintenant charger **plusieurs fichiers** pour un même placeholder. Toutes les variations sont **fusionnées**.

### Syntaxe

```python
VARIATION_FILES = {
    # Un seul fichier (syntaxe classique)
    "Expression": "expressions.txt",

    # Plusieurs fichiers (nouvelle syntaxe)
    "Pose": ["poses_basic.txt", "poses_advanced.txt", "poses_sitting.txt"]
}
```

### Exemple

**Fichier `poses_basic.txt` :**
```
standing
sitting
lying down
```

**Fichier `poses_advanced.txt` :**
```
handstand
splits
backbend,{|arms extended|hands on ground}
```

**Résultat fusionné pour le placeholder `{Pose}` :**
```
standing
sitting
lying down
handstand
splits
backbend
backbend,arms extended
backbend,hands on ground
```

**Total : 8 variations** (3 du basic + 5 du advanced dont 3 expansées)

### Organisation recommandée

```python
VARIATION_FILES = {
    "Pose": [
        "variations/poses/standing.txt",
        "variations/poses/sitting.txt",
        "variations/poses/action.txt",
        "variations/poses/special.txt"
    ],
    "Expression": [
        "variations/expressions/positive.txt",
        "variations/expressions/negative.txt",
        "variations/expressions/neutral.txt"
    ]
}
```

### Avantages

- **Modularité** : Organiser les variations par catégories
- **Maintenance** : Facile d'ajouter/retirer des catégories
- **Réutilisation** : Partager des fichiers entre projets
- **Collaboration** : Plusieurs personnes travaillent sur différents fichiers

### Interaction avec les options

Les options de placeholder s'appliquent **après** la fusion :

```python
prompt = "{Pose:10}"  # Sélectionne 10 variations aléatoires parmi TOUTES celles fusionnées

prompt = "{Pose:#|1|5|22}"  # Sélectionne index 1, 5, 22 du résultat fusionné
```

---

## Options avancées combinées

Vous pouvez **combiner plusieurs options** :

### Tableau récapitulatif

| Format | Description | Exemple |
|--------|-------------|---------|
| `{Name}` | Toutes les variations | `{Hair}` |
| `{Name:N}` | N variations aléatoires | `{Hair:5}` |
| `{Name:0}` | Supprime le placeholder | `{Hair:0}` |
| `{Name:#\|1\|5}` | Index spécifiques | `{Hair:#\|1\|5\|22}` |
| `{Name:$P}` | Priorité P | `{Hair:$3}` |
| `{Name:N$P}` | Limite + priorité | `{Hair:10$5}` |
| `{Name:#\|1\|5$P}` | Index + priorité | `{Hair:#\|1\|5$8}` |

### Exemples de combinaisons

```python
# Limite + priorité
prompt = "{Outfit:8$2}, {Angle:$10}, {Expression:15$20}"
# 8 outfits (poids 2), tous les angles (poids 10), 15 expressions (poids 20)

# Index spécifiques + priorité
prompt = "{Outfit:#|0|3|5$1}, {Angle:#|1|4$10}"
# Outfits 0,3,5 en boucle extérieure, Angles 1,4 en boucle intérieure

# Mix de tout
prompt = "{A:5$1}, {B:#|0|2$5}, {C:$10}, {D:0}"
# A: 5 aléatoires poids 1
# B: index 0,2 poids 5
# C: toutes variations poids 10
# D: supprimé
```

---

## Exemples pratiques

### 1. Character sheet complet

```python
from image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="1girl, emma watson, {Outfit:$1}, {Angle:$10}, {Expression:$20}, high quality",
    negative_prompt="low quality, blurry",
    variation_files={
        "Outfit": ["outfits_casual.txt", "outfits_formal.txt"],
        "Angle": "angles.txt",
        "Expression": "expressions.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="emma_charactersheet"
)

generator.run()
```

**Résultat :** Un bloc complet par outfit, avec toutes les expressions et angles.

### 2. Exploration créative

```python
generator = ImageVariationGenerator(
    prompt_template="concept art, {Style}, {Subject:20}, {Lighting:8}, {Mood:0}",
    negative_prompt="low quality",
    variation_files={
        "Style": "styles.txt",
        "Subject": "subjects_fantasy.txt",
        "Lighting": "lighting.txt",
        "Mood": "moods.txt"  # Sera ignoré (:0)
    },
    generation_mode="random",
    seed_mode="random",
    max_images=100,
    session_name="concept_exploration"
)
```

**Résultat :** 100 concepts aléatoires, 20 sujets max, 8 lighting max, sans mood.

### 3. Tests A/B structurés

```python
# Configuration commune
base_config = {
    "prompt_template": "portrait, {Hair:#|1|5|8}, {Expression:#|2|7}, {Lighting}, beautiful",
    "negative_prompt": "low quality",
    "generation_mode": "combinatorial",
    "seed_mode": "fixed",
    "seed": 42
}

# Test AVEC background
generator_with = ImageVariationGenerator(
    **base_config,
    variation_files={
        "Hair": "hair.txt",
        "Expression": "expressions.txt",
        "Lighting": "lighting.txt"
    },
    session_name="test_with_lighting"
)

# Test SANS background (lighting supprimé)
generator_without = ImageVariationGenerator(
    **base_config,
    variation_files={
        "Hair": "hair.txt",
        "Expression": "expressions.txt",
        "Lighting": "lighting.txt"  # Sera ignoré car :0 dans prompt
    },
    session_name="test_without_lighting"
)

# Même seed = compositions identiques, seul le lighting change
```

### 4. Génération progressive

```python
# Étape 1 : Explorer largement
generator = ImageVariationGenerator(
    prompt_template="{Hair}, {Expression}, {Pose}",
    variation_files={
        "Hair": "hair.txt",
        "Expression": "expressions.txt",
        "Pose": "poses.txt"
    },
    generation_mode="random",
    max_images=50,
    session_name="exploration_v1"
)
generator.run()

# → Identifier les meilleures combinaisons visuellement

# Étape 2 : Affiner avec index spécifiques
generator = ImageVariationGenerator(
    prompt_template="{Hair:#|1|5|8}, {Expression:#|2|7|15}, {Pose:#|0|3}",
    variation_files={
        "Hair": "hair.txt",
        "Expression": "expressions.txt",
        "Pose": "poses.txt"
    },
    generation_mode="combinatorial",  # Toutes les combinaisons des sélectionnés
    seed_mode="progressive",
    session_name="refined_v2"
)
generator.run()

# → 3 hair × 3 expressions × 2 poses = 18 images précises
```

### 5. Variations conditionnelles avec fichiers imbriqués

**Fichier `action_poses.txt` :**
```
running,{|looking back|arms pumping}
jumping,{|legs bent},{|arms up|reaching}
fighting stance,{|fists raised},{|defensive|aggressive}
dancing,{|spinning},{|arms extended|graceful pose}
```

**Script :**
```python
generator = ImageVariationGenerator(
    prompt_template="1girl, {Pose}, outdoor scene, dynamic",
    negative_prompt="low quality",
    variation_files={
        "Pose": "action_poses.txt"
    },
    generation_mode="combinatorial",
    session_name="action_variations"
)
```

**Résultat :**
- `running` → génère 3 variations (base, +looking back, +arms pumping)
- `jumping` → génère 6 variations (2×3)
- `fighting stance` → génère 6 variations (2×3)
- `dancing` → génère 6 variations (2×3)

**Total automatique : 21 variations** à partir de 4 lignes !

---

## Bonnes pratiques

### 1. Commencer petit

Testez toujours avec peu de variations d'abord :

```python
prompt = "{Expression:3}, {Angle:2}"  # 6 images max
```

Une fois validé, augmentez progressivement.

### 2. Nommer clairement les placeholders

**Bon :**
```python
prompt = "{FacialExpression}, {CameraAngle}, {LightingSetup}"
```

**Moins bon :**
```python
prompt = "{Expr}, {Ang}, {Light}"
```

### 3. Utiliser des commentaires dans les fichiers

```
# expressions.txt
# Version 3.0 - Validé le 2025-10-01
# 50 expressions testées et approuvées

# Expressions positives
happy→smiling, cheerful
joyful→laughing, happy

# Expressions négatives
sad→sad, crying
```

### 4. Organiser par dossiers

```
variations/
├── expressions/
│   ├── positive.txt
│   ├── negative.txt
│   └── neutral.txt
├── poses/
│   ├── standing.txt
│   ├── sitting.txt
│   └── action.txt
└── styles/
    ├── anime.txt
    ├── realistic.txt
    └── artistic.txt
```

### 5. Tester les index avant production

```python
# Phase 1 : Exploration
generator.run()  # Toutes les variations

# Phase 2 : Analyse manuelle des résultats
# Identifier index des meilleures : 1, 5, 8, 22, 45

# Phase 3 : Production ciblée
prompt = "{Hair:#|1|5|8|22|45}"
generator.run()
```

### 6. Documenter les sessions

```python
session_name = "emma_outfit_test_v3_progressive_seed42"
# Nom explicite : personnage, test, version, seed mode, seed
```

### 7. Utiliser les priorités pour la cohérence

Pour des character sheets cohérents :

```python
# Poids faibles pour éléments fixes (outfit)
# Poids élevés pour éléments variables (expression)
prompt = "{Outfit:$1}, {Angle:$10}, {Expression:$20}"
```

**Organisation** : Toutes les expressions/angles par outfit = cohérence visuelle.

### 8. Sauvegarder les configurations réussies

```python
# Créer des présets réutilisables
PRESET_CHARACTER_SHEET = {
    "generation_mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42
}

PRESET_CREATIVE_EXPLORATION = {
    "generation_mode": "random",
    "seed_mode": "random",
    "max_images": 100
}

# Utiliser
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...},
    **PRESET_CHARACTER_SHEET,
    session_name="..."
)
```

### 9. Tester les variations imbriquées progressivement

```
# v1 : Simple
standing

# v2 : Ajouter une option
standing,{|arms crossed}

# v3 : Ajouter plus d'options
standing,{|arms crossed|hands in pockets|arms up}

# v4 : Ajouter un deuxième niveau
standing,{|arms crossed|hands in pockets|arms up},{|looking away}
```

Testez chaque étape avant d'ajouter la suivante.

### 10. Utiliser le mode ask pour l'exploration

```python
generation_mode = "ask"  # Demande au lancement
seed_mode = "ask"        # Demande au lancement
```

Permet de changer de stratégie sans modifier le code.

---

## Résumé des fonctionnalités

### Formats de placeholders

| Syntaxe | Effet |
|---------|-------|
| `{Name}` | Toutes les variations |
| `{Name:N}` | N variations aléatoires |
| `{Name:0}` | Supprime le placeholder |
| `{Name:#\|1\|5}` | Sélectionne index 1 et 5 |
| `{Name:$5}` | Poids 5 pour ordre des boucles |
| `{Name:10$5}` | 10 variations aléatoires, poids 5 |
| `{Name:#\|1\|5$8}` | Index 1,5 avec poids 8 |

### Fichiers de variations

- **3 formats** : `clé→valeur`, `numéro→valeur`, `valeur seule`
- **Commentaires** : lignes commençant par `#`
- **Variations imbriquées** : `{|option1|option2}` dans les valeurs
- **Fichiers multiples** : `{"Pose": ["file1.txt", "file2.txt"]}`

### Cas d'usage principaux

- **Character sheets** : Mode combinatorial + priorités
- **Exploration créative** : Mode random + seed random
- **Tests A/B** : Placeholder :0 pour supprimer des éléments
- **Affinage progressif** : Index spécifiques après exploration
- **Variations conditionnelles** : Variations imbriquées dans fichiers

---

## Références

### Fichiers liés

- `variation_loader.py` : Module de chargement des variations
- `image_variation_generator.py` : Classe générique de génération
- `features.md` : Guide complet des fonctionnalités

### Exemples de scripts

- `example_simple_generator.py` : Exemples basiques
- `demo_generators.py` : Démonstrations variées
- `facial_expression_generator_refactored.py` : Exemple avancé

---

**Dernière mise à jour** : 2025-10-01
