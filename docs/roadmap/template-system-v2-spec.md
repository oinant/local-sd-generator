# Template System V2.0 - Spécification Technique Formelle

**Version:** 2.0.0
**Date:** 2025-10-09
**Status:** Draft - Ready for Implementation

---

## 1. Vue d'ensemble

### 1.1 Objectifs du système V2.0

Le Template System V2.0 introduit un système de templates hiérarchique, modulaire et réutilisable pour la génération de prompts Stable Diffusion. Il permet :

- **Héritage de configurations** : Templates et chunks peuvent hériter (`implements:`) d'autres fichiers
- **Composition modulaire** : Chunks réutilisables pour personnages, styles, scènes
- **Import flexible** : Merge de variations depuis plusieurs sources (fichiers + inline)
- **Sélection avancée** : Contrôle fin sur les variations (limite, index, clés, poids combinatoire)
- **Validation stricte** : Détection de toutes les erreurs avant génération

### 1.2 Concepts clés

- **Template** (`.template.yaml`) : Configuration de base avec paramètres de génération et structure de prompt
- **Chunk** (`.chunk.yaml`) : Bloc réutilisable avec template et valeurs par défaut (ex: personnage, style)
- **Prompt** (`.prompt.yaml`) : Configuration finale avec imports de variations et template spécifique
- **Variations** (`.yaml`) : Dictionnaire de variations (ex: coiffures, poses, tenues)

### 1.3 Différences majeures avec V1.x

| Feature | V1.x | V2.0 |
|---------|------|------|
| Héritage | ❌ Non | ✅ `implements:` multi-niveaux |
| Chunks réutilisables | ❌ Non | ✅ Avec `@Chunk` syntax |
| Imports multi-sources | ❌ Non | ✅ Merge de fichiers + inline |
| Sélecteurs avancés | `:N`, `#\|N` | ✅ `[selectors;selectors]` |
| Validation | Partial | ✅ 5 phases, toutes erreurs collectées |
| Format variations | Liste `key→value` | ✅ Dict YAML simple |
| Injection de chunks | ❌ Non | ✅ `@{Chunk with Param:{Var}}` |

---

## 2. Grammaire formelle (EBNF)

### 2.1 Syntaxe des placeholders

```ebnf
(* Placeholder simple *)
placeholder = "{" identifier "}" ;

(* Placeholder avec sélecteurs *)
placeholder_with_selectors = "{" identifier "[" selector_list "]" "}" ;

(* Liste de sélecteurs séparés par point-virgule *)
selector_list = selector { ";" selector } ;

(* Sélecteur individuel *)
selector = limit_selector
         | index_selector
         | key_selector
         | weight_selector ;

(* Limite aléatoire : N variations random *)
limit_selector = integer ;

(* Sélection par index : #1,3,5 *)
index_selector = "#" index { "," index } ;
index = integer ;

(* Sélection par clé : BobCut,LongHair *)
key_selector = key { "," key } ;
key = identifier ;

(* Poids combinatoire : $N *)
weight_selector = "$" integer ;

(* Exemples valides *)
(* {Angle[15]}                  - 15 variations random *)
(* {Angle[#1,3,5]}              - Index 1, 3, 5 *)
(* {Angle[BobCut,LongHair]}     - Par clés *)
(* {Angle[$8]}                  - Poids 8 *)
(* {Angle[15;$8]}               - 15 random + poids 8 *)
(* {Angle[#1,3,5;$0]}           - Index 1,3,5 + hors combinatoire *)
(* {Angle[BobCut,LongHair;$5]}  - Par clés + poids 5 *)
```

### 2.2 Syntaxe des chunks

```ebnf
(* Référence simple à un chunk *)
chunk_ref = "@" identifier ;

(* Référence avec navigation (nested imports) *)
chunk_ref_nested = "@" identifier { "." identifier } ;

(* Injection de chunk avec paramètres *)
chunk_with_params = "@{" identifier "with" param_list "}" ;

(* Liste de paramètres *)
param_list = param_binding { "," param_binding } ;

(* Binding : PlaceholderName:{ImportName[selectors]} *)
param_binding = identifier ":" placeholder_with_selectors ;

(* Exemples valides *)
(* @Character                                           - Chunk simple *)
(* @chunks.positive                                     - Nested import *)
(* @{Character with Angles:{Angle[15]}}                - Avec param *)
(* @{Character with Angles:{Angle[15]}, Poses:{Pose}}  - Multi-params *)
```

### 2.3 Identifiants

```ebnf
identifier = letter { letter | digit | "_" } ;
letter = "A".."Z" | "a".."z" ;
digit = "0".."9" ;
integer = digit { digit } ;
```

---

## 3. Structure des fichiers

### 3.1 Format `.template.yaml`

```yaml
version: '2.0'                  # OBLIGATOIRE - Version du format
name: 'TemplateName'            # OBLIGATOIRE - Nom du template

implements: '../parent.template.yaml'  # OPTIONNEL - Héritage

parameters:                     # OPTIONNEL - Paramètres SD WebUI
  width: 832
  height: 1216
  steps: 30
  cfg_scale: 6
  sampler: 'DPM++ 2M'
  scheduler: 'Karras'
  batch_size: 1
  batch_count: 1
  enable_hr: true              # Hires Fix
  hr_scale: 1.5
  hr_upscaler: '4x_foolhardy_Remacri'
  denoising_strength: 0.4
  hr_second_pass_steps: 15

imports:                        # OPTIONNEL - Imports de chunks/variations
  chunks:
    positive: ../chunks/positive.chunk.yaml
    negative: ../chunks/negative.chunk.yaml
  Character: ../chunks/character.chunk.yaml

template: |                     # OBLIGATOIRE - Template de prompt positif
  @chunks.positive,
  {prompt},
  detailed, masterpiece

negative_prompt: |              # OPTIONNEL - Template de prompt négatif
  @chunks.negative,
  {negprompt},
  low quality
```

**Champs obligatoires :** `version`, `name`, `template`

**Placeholders réservés dans `template:` et `negative_prompt:` :**
- `{prompt}` : Remplacé par le template du prompt final
- `{negprompt}` : Remplacé par le negative_prompt du prompt final
- `{loras}` : Réservé pour injection de LoRAs

### 3.2 Format `.chunk.yaml`

```yaml
version: '2.0'                  # OBLIGATOIRE - Version du format
type: 'character'               # OBLIGATOIRE - Type du chunk (character, scene, style, etc.)

implements: '../parent.chunk.yaml'  # OPTIONNEL - Héritage

imports:                        # OPTIONNEL - Imports de variations
  Haircuts: ../variations/haircuts.yaml
  HairColors: ../variations/haircolors.yaml
  Poses: ../variations/poses.yaml

template: |                     # OBLIGATOIRE - Template du chunk
  1girl, {Main},
  {Angle}, {Pose},
  {HairCut}, {HairColor} hair,
  detailed eyes, detailed skin

defaults:                       # OPTIONNEL - Valeurs par défaut
  Main: '30, slim build'
  HairCut: 'BobCut'
  HairColor: 'Brunette'
  Angle: 'Straight'

chunks:                         # OPTIONNEL - Valeurs spécifiques (override defaults)
  Main: '22, supermodel, slim curvy'
  HairCut: Haircuts.BobCut      # Référence par clé
  HairColor: HairColors.Ginger
  Angle: Angles.Straight
```

**Champs obligatoires :** `version`, `type`, `template`

**Placeholders interdits dans `template:` :**
- `{prompt}`, `{negprompt}`, `{loras}` → **Erreur de validation**

**Validation du type :**
- Si `implements:` défini, le parent doit avoir le même `type:`
- Si parent n'a pas de `type:`, **Warning** + assume le type de l'enfant

### 3.3 Format `.prompt.yaml`

```yaml
version: '2.0'                  # OBLIGATOIRE - Version du format
name: 'PromptName'              # OBLIGATOIRE - Nom du prompt

implements: '../template.yaml'  # OBLIGATOIRE - Template parent

generation:                     # OBLIGATOIRE - Config génération
  mode: 'random'                # 'random' | 'combinatorial'
  seed: 42
  seed_mode: 'random'           # 'fixed' | 'progressive' | 'random'
  max_images: 1000

imports:                        # OPTIONNEL - Imports de variations
  Character: ../chunks/character.chunk.yaml
  Outfit:
    - ../variations/outfit.urban.yaml
    - ../variations/outfit.chic.yaml
    - "custom red dress"        # Inline string
  Place:
    - "luxury living room"
    - "tropical jungle"
  Angle: ../variations/angles.yaml

template: |                     # OBLIGATOIRE - Template spécifique
  @{Character with Angles:{Angle}, Poses:{Pose}},
  detailed background, {Place},
  {Outfit},
  night scene, dramatic lighting

negative_prompt: |              # OPTIONNEL - Override du negative_prompt parent
  {negprompt},
  bad anatomy
```

**Champs obligatoires :** `version`, `name`, `implements`, `generation`, `template`

**Placeholders réservés :**
- `{prompt}`, `{negprompt}`, `{loras}` (utilisables uniquement dans templates parents)

### 3.4 Format `.yaml` (Variations)

**Format unique : Dictionnaire YAML simple**

```yaml
# haircuts.yaml
BobCut: "bob cut, chin-length hair"
LongHair: "long flowing hair, waist-length"
Pixie: "pixie cut, short spiky hair"
Ponytail: "high ponytail, sleek hair"
```

**Règles :**
- Clés : Identifiants uniques (PascalCase recommandé)
- Valeurs : Strings de prompt
- Pas de placeholders réservés

---

## 4. Placeholders réservés

### 4.1 Table par type de fichier

| Placeholder | `.template.yaml` | `.chunk.yaml` | `.prompt.yaml` | `.yaml` (variations) |
|-------------|------------------|---------------|----------------|---------------------|
| `{prompt}`     | ✅ Autorisé | ❌ **Erreur** | ✅ Autorisé | ❌ **Erreur** |
| `{negprompt}`  | ✅ Autorisé | ❌ **Erreur** | ✅ Autorisé | ❌ **Erreur** |
| `{loras}`      | ✅ Autorisé | ❌ **Erreur** | ✅ Autorisé | ❌ **Erreur** |

**Note :** Les placeholders réservés sont **case-sensitive** (`{Prompt}` ≠ `{prompt}`)

### 4.2 Validation contextuelle

**Dans un `.chunk.yaml` :**
```yaml
template: |
  1girl, {prompt}, beautiful  # ❌ ERREUR : "Reserved placeholder {prompt} not allowed in chunks"
```

**Dans un `.template.yaml` :**
```yaml
template: |
  masterpiece, {prompt}, detailed  # ✅ OK
```

---

## 5. Système d'héritage (`implements:`)

### 5.1 Résolution des chemins

**Règle :** Chemins relatifs au fichier YAML qui contient `implements:`

```yaml
# Fichier : /templates/prompts/emma.prompt.yaml
implements: '../template/base.template.yaml'
# Résolu comme : /templates/template/base.template.yaml
```

**Imports imbriqués :**
```yaml
# /templates/prompts/emma.prompt.yaml
implements: '../template/manga.template.yaml'

# /templates/template/manga.template.yaml
implements: './base.template.yaml'
# Résolu comme : /templates/template/base.template.yaml (relatif à manga.template.yaml)
```

**Chemins absolus :** ❌ Non supportés (pour portabilité Windows/Linux)

### 5.2 Merge des sections

**Règle générale :** Merge récursif, l'enfant override le parent

#### `parameters:` - MERGE

```yaml
# parent.template.yaml
parameters:
  width: 832
  height: 1216
  steps: 30

# child.template.yaml
implements: parent.template.yaml
parameters:
  steps: 40  # Override

# Résultat final :
# parameters:
#   width: 832      ← Hérité
#   height: 1216    ← Hérité
#   steps: 40       ← Overridé
```

#### `imports:` - MERGE

```yaml
# parent.template.yaml
imports:
  Character: ../chunks/char.chunk.yaml

# child.template.yaml
imports:
  Outfit: ../variations/outfit.yaml

# Résultat :
# imports:
#   Character: ../chunks/char.chunk.yaml  ← Hérité
#   Outfit: ../variations/outfit.yaml     ← Ajouté
```

#### `chunks:` (dans `.chunk.yaml`) - MERGE

```yaml
# parent.chunk.yaml
chunks:
  Angle: Angles.Straight
  Main: "30, slim"

# child.chunk.yaml
chunks:
  Main: "22, supermodel"  # Override

# Résultat :
# chunks:
#   Angle: Angles.Straight  ← Hérité
#   Main: "22, supermodel"  ← Overridé
```

#### `defaults:` (dans `.chunk.yaml`) - MERGE

Même comportement que `chunks:`

#### `template:` - REPLACE (avec Warning)

```yaml
# parent.chunk.yaml
template: |
  1girl, {Main}, {Angle}

# child.chunk.yaml
template: |
  beautiful woman, {Main}

# Résultat : template de child remplace complètement celui de parent
# ⚠️ WARNING : "Overriding parent template in child.chunk.yaml, consider creating a new base chunk"
```

### 5.3 Validation des types de chunks

**Règle :** Un chunk ne peut hériter que d'un chunk du même type

```yaml
# girl_solo.chunk.yaml
type: character

# emma.chunk.yaml
type: character
implements: girl_solo.chunk.yaml  # ✅ OK - Même type

# landscape.chunk.yaml
type: scene
implements: girl_solo.chunk.yaml  # ❌ ERREUR : "Type mismatch: landscape.chunk.yaml (scene) cannot implement girl_solo.chunk.yaml (character)"
```

**Cas spécial : Parent sans type**
```yaml
# base.chunk.yaml
# Pas de champ type:

# emma.chunk.yaml
type: character
implements: base.chunk.yaml  # ⚠️ WARNING : "base.chunk.yaml has no type, assuming 'character'"
```

---

## 6. Système d'imports

### 6.1 Fichiers vs Inline strings

**Import de fichier :**
```yaml
imports:
  Outfit: ../variations/outfit.yaml  # Fichier YAML dict
```

**Import inline (strings) :**
```yaml
imports:
  Place:
    - "luxury living room, glass table"
    - "tropical jungle, giant ferns"
```

**Mix fichiers + inline :**
```yaml
imports:
  Outfit:
    - ../variations/outfit.urban.yaml  # Fichier
    - ../variations/outfit.chic.yaml   # Fichier
    - "custom red dress, elegant"      # Inline
```

### 6.2 Merge multi-sources

**Ordre préservé :**
```yaml
imports:
  Outfit:
    - ../variations/outfit.urban.yaml   # 5 items : Urban1, Urban2, ..., Urban5
    - ../variations/outfit.chic.yaml    # 8 items : Chic1, Chic2, ..., Chic8
    - "red dress"                        # 1 item inline

# Résultat : 14 items dans l'ordre
# [Urban1, Urban2, ..., Urban5, Chic1, Chic2, ..., Chic8, "red dress"]
```

**Clés auto-générées pour inline :**
- Algorithme : MD5 court (`md5(value)[:8]`)
- Format : `{hash: value}`
- Exemple :
  ```python
  "red dress" → {"7d8e3a2f": "red dress"}
  ```
- **Pas de référence par clé auto-générée** (non recommandé)

### 6.3 Détection des conflits de clés

**Erreur si clés dupliquées entre fichiers :**

```yaml
# outfit.urban.yaml
Casual: "jeans and t-shirt"

# outfit.chic.yaml
Casual: "designer casual wear"

# Import
imports:
  Outfit:
    - ../variations/outfit.urban.yaml
    - ../variations/outfit.chic.yaml

# ❌ ERREUR : "Duplicate key 'Casual' in Outfit imports (found in outfit.urban.yaml and outfit.chic.yaml)"
```

**Inline n'entre pas en conflit** (clé auto-générée) :
```yaml
imports:
  Outfit:
    - ../variations/outfit.yaml    # {Casual: "jeans"}
    - "Casual: designer wear"       # Traité comme string → hash auto
# ✅ OK - Pas de conflit
```

### 6.4 Référence par clé

**Dans `chunks:` d'un `.chunk.yaml` :**
```yaml
imports:
  Haircuts: ../variations/haircuts.yaml  # {BobCut: "bob cut", LongHair: "long hair"}

chunks:
  HairCut: Haircuts.BobCut  # Référence à la clé BobCut
```

**Résolution :**
1. Parser `Haircuts.BobCut`
2. Vérifier que `Haircuts` existe dans `imports:`
3. Vérifier que `BobCut` existe dans le fichier chargé
4. Remplacer par la valeur : `"bob cut"`

---

## 7. Résolution des templates

### 7.1 Ordre de résolution (5 phases de validation)

**Phase 1 : Validation structurelle**
- YAML bien formé
- Champs requis présents (`version`, `name`, `template`, etc.)

**Phase 2 : Validation des chemins**
- Tous les fichiers `implements:` existent
- Tous les fichiers dans `imports:` existent

**Phase 3 : Validation de l'héritage**
- `implements:` corrects (pas de cycle)
- Types de chunks compatibles

**Phase 4 : Validation des imports**
- Pas de clés dupliquées dans les merges
- Imports référencés existent

**Phase 5 : Validation du template**
- Placeholders résolus
- Pas de placeholders réservés interdits
- Références `Import.Key` valides

**Règle :** Si erreur à une phase, continuer quand même les phases suivantes pour collecter toutes les erreurs

### 7.2 Injection de chunks avec `@`

**Syntaxe simple :**
```yaml
template: |
  @Character,
  detailed background
```

**Résolution :**
1. Chercher `Character` dans `imports:`
2. Charger le chunk (avec héritage récursif)
3. Résoudre le template du chunk
4. Injecter le résultat

**Syntaxe nested :**
```yaml
imports:
  chunks:
    positive: ../chunks/positive.chunk.yaml

template: |
  @chunks.positive,
  masterpiece
```

### 7.3 Passage de paramètres avec `with`

**Syntaxe :**
```yaml
template: |
  @{Character with Angles:{Angle[15]}, Poses:{Pose[$5]}}
```

**Résolution :**
1. Charger le chunk `Character`
2. Son template contient `{Angle}` et `{Pose}`
3. Remplacer `{Angle}` par une variation tirée de `{Angle[15]}`
4. Remplacer `{Pose}` par une variation tirée de `{Pose[$5]}`
5. Résoudre le template complet du chunk

**Exemple concret :**
```yaml
# character.chunk.yaml
template: |
  1girl, {Main}, {Angle}, {Pose}

# prompt.yaml
imports:
  Character: ../chunks/character.chunk.yaml
  Angle: ../variations/angles.yaml
  Pose: ../variations/poses.yaml

template: |
  @{Character with Angles:{Angle[15]}, Poses:{Pose[$0]}}

# Résolution :
# 1. {Angle[15]} → Tire 15 angles random
# 2. {Pose[$0]} → Tire des poses avec poids 0 (hors combinatoire)
# 3. Injecte dans le template de Character
# Résultat : "1girl, {Main}, [angle tiré], [pose tirée]"
```

### 7.4 Sélection de variations avec `[]`

**Sélecteurs supportés :**

| Syntaxe | Signification | Exemple |
|---------|---------------|---------|
| `[N]` | N variations random | `{Angle[15]}` |
| `[#i,j,k]` | Index i, j, k | `{Angle[#1,3,5]}` |
| `[Key1,Key2]` | Par clés | `{Haircut[BobCut,LongHair]}` |
| `[$W]` | Poids W | `{Angle[$8]}` |
| `[sel1;sel2]` | Combinaison (`;` séparateur) | `{Angle[15;$8]}` |

**Poids combinatoire (`$W`) :**
- Détermine l'ordre des boucles en mode `combinatorial`
- Poids par défaut : `$1`
- Poids `$0` : Hors combinatoire (variation random unique par image)
- Plus petit poids = boucle extérieure (change moins souvent)
- Plus grand poids = boucle intérieure (change plus souvent)

**Exemple :**
```yaml
template: |
  {Outfit[$2]}, {Angle[$10]}

# Mode combinatorial :
# Boucle extérieure : Outfit (poids 2)
# Boucle intérieure : Angle (poids 10)
# → Pour chaque Outfit, génère toutes les variations d'Angle
```

**Combinaisons complexes :**
```yaml
{Angle[#1,3,5;$8]}        # Index 1,3,5 + poids 8
{Angle[15;$0]}            # 15 random + hors combinatoire
{Angle[BobCut,LongHair;$5]} # Par clés + poids 5
```

---

## 8. Normalisation des prompts

**Appliquée après résolution complète du template**

### 8.1 Règles de normalisation

1. **Trim espaces début/fin de ligne**
   ```
   "  1girl, beautiful  " → "1girl, beautiful"
   ```

2. **Collapse virgules multiples**
   ```
   "1girl,, beautiful" → "1girl, beautiful"
   ```

3. **Suppression virgules orphelines début/fin**
   ```
   ", 1girl, beautiful," → "1girl, beautiful"
   ```

4. **Normalisation espaces autour virgules**
   ```
   "1girl,beautiful" → "1girl, beautiful"
   ```

5. **Préservation 1 ligne vide max**
   ```yaml
   # Avant
   template: |
     1girl,


     detailed background

   # Après
   "1girl,\n\ndetailed background"  # Max 1 ligne vide préservée
   ```

### 8.2 Gestion des placeholders vides

**Si un placeholder se résout en chaîne vide :**

```yaml
template: |
  @chunks.positive,
  {Outfit},
  detailed background

# Si {Outfit} est vide :
# Avant normalisation : "@chunks.positive,\n,\ndetailed background"
# Après normalisation : "@chunks.positive, detailed background"
```

---

## 9. Gestion d'erreurs

### 9.1 Stratégie de validation

**Fail-fast avec collecte complète :**
1. Collecter **toutes** les erreurs (5 phases de validation)
2. Afficher toutes les erreurs ensemble
3. **Arrêter avant génération** si erreurs présentes

### 9.2 Format JSON des erreurs

```json
{
  "errors": [
    {
      "type": "import",
      "name": "Outfit",
      "file": "../variations/outfit.yaml",
      "message": "File not found"
    },
    {
      "type": "import",
      "name": "Pose",
      "file": "../variations/missing.yaml",
      "message": "File not found"
    },
    {
      "type": "template",
      "line": 1,
      "message": "Import 'NonExistent' not defined in imports"
    },
    {
      "type": "chunk_type",
      "file": "landscape.chunk.yaml",
      "message": "Type mismatch: cannot implement girl_solo.chunk.yaml (character) with type 'scene'"
    },
    {
      "type": "duplicate_key",
      "import": "Outfit",
      "key": "Casual",
      "files": ["outfit.urban.yaml", "outfit.chic.yaml"],
      "message": "Duplicate key 'Casual' found in multiple files"
    }
  ],
  "count": 5
}
```

### 9.3 Logging

**Fichier de log :**
- Emplacement : `{output_dir}/{session_name}/errors.json`
- Format : JSON (comme ci-dessus)

**Affichage console :**
```
=== Validation Errors ===

File Imports (2 errors):
  - Outfit: ../variations/outfit.yaml (not found)
  - Pose: ../variations/missing.yaml (not found)

Template Resolution (1 error):
  - Line 1: import 'NonExistent' not defined

Chunk Type Validation (1 error):
  - landscape.chunk.yaml: Type mismatch (cannot implement character with scene)

Import Conflicts (1 error):
  - Outfit: Duplicate key 'Casual' in outfit.urban.yaml and outfit.chic.yaml

Total: 5 errors. Generation aborted.
```

---

## 10. Tables de référence

### 10.1 Champs par type de fichier

#### `.template.yaml`

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `version` | string | ✅ | Version du format (`2.0`) |
| `name` | string | ✅ | Nom du template |
| `implements` | string | ❌ | Chemin vers template parent |
| `parameters` | dict | ❌ | Paramètres SD WebUI |
| `imports` | dict | ❌ | Imports de chunks/variations |
| `template` | string | ✅ | Template de prompt positif |
| `negative_prompt` | string | ❌ | Template de prompt négatif |

#### `.chunk.yaml`

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `version` | string | ✅ | Version du format (`2.0`) |
| `type` | string | ✅ | Type du chunk (`character`, `scene`, etc.) |
| `implements` | string | ❌ | Chemin vers chunk parent |
| `imports` | dict | ❌ | Imports de variations |
| `template` | string | ✅ | Template du chunk |
| `defaults` | dict | ❌ | Valeurs par défaut |
| `chunks` | dict | ❌ | Valeurs spécifiques (override defaults) |

#### `.prompt.yaml`

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `version` | string | ✅ | Version du format (`2.0`) |
| `name` | string | ✅ | Nom du prompt |
| `implements` | string | ✅ | Chemin vers template parent |
| `generation` | dict | ✅ | Config génération (mode, seed, etc.) |
| `imports` | dict | ❌ | Imports de variations |
| `template` | string | ✅ | Template spécifique |
| `negative_prompt` | string | ❌ | Override negative_prompt parent |

#### `.yaml` (Variations)

| Structure | Format | Description |
|-----------|--------|-------------|
| Dict YAML | `Key: "value"` | Dictionnaire simple clé-valeur |

### 10.2 Sélecteurs supportés

| Syntaxe | Type | Description | Exemple |
|---------|------|-------------|---------|
| `[N]` | Limite | N variations random | `{Angle[15]}` |
| `[#i,j,k]` | Index | Sélection par index (0-based) | `{Angle[#1,3,5]}` |
| `[Key1,Key2]` | Clés | Sélection par clés | `{Haircut[BobCut,LongHair]}` |
| `[$W]` | Poids | Poids combinatoire (défaut: 1) | `{Angle[$8]}` |
| `[sel1;sel2;...]` | Combinaison | Multiple sélecteurs (`;` séparateur) | `{Angle[15;$8]}` |

**Poids spéciaux :**
- `$0` : Hors combinatoire (variation random unique par image)
- `$1` : Poids par défaut

### 10.3 Placeholders réservés (par contexte)

| Context | `{prompt}` | `{negprompt}` | `{loras}` |
|---------|-----------|---------------|----------|
| `.template.yaml` (template) | ✅ | ✅ | ✅ |
| `.template.yaml` (negative_prompt) | ✅ | ✅ | ✅ |
| `.chunk.yaml` (template) | ❌ | ❌ | ❌ |
| `.prompt.yaml` (template) | ✅ | ✅ | ✅ |
| `.prompt.yaml` (negative_prompt) | ✅ | ✅ | ✅ |
| `.yaml` (variations) | ❌ | ❌ | ❌ |

---

## 11. Exemples complets

### 11.1 Exemple minimal

**base.template.yaml**
```yaml
version: '2.0'
name: 'BaseTemplate'

parameters:
  width: 832
  height: 1216
  steps: 30

template: |
  masterpiece, {prompt}, detailed
```

**prompt.yaml**
```yaml
version: '2.0'
name: 'MyPrompt'
implements: '../base.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 10

template: |
  1girl, beautiful, smiling
```

### 11.2 Exemple avec chunks

**girl_solo.chunk.yaml**
```yaml
version: '2.0'
type: character

template: |
  1girl, {Main}, {Angle}, {Pose}

defaults:
  Main: '30, slim'
  Angle: 'Straight'
  Pose: 'Standing'
```

**emma.chunk.yaml**
```yaml
version: '2.0'
type: character
implements: '../girl_solo.chunk.yaml'

imports:
  Haircuts: ../variations/haircuts.yaml
  Poses: ../variations/poses.yaml

chunks:
  Main: '22, supermodel, slim curvy'
  HairCut: Haircuts.BobCut
```

**prompt.yaml**
```yaml
version: '2.0'
name: 'EmmaPortrait'
implements: '../base.template.yaml'

generation:
  mode: combinatorial
  seed: 42
  seed_mode: progressive
  max_images: 100

imports:
  Character: ../chunks/emma.chunk.yaml
  Angle: ../variations/angles.yaml
  Pose: ../variations/poses.yaml

template: |
  @{Character with Angles:{Angle[15]}, Poses:{Pose[$8]}},
  detailed background, bokeh
```

### 11.3 Exemple avec variations inline

```yaml
version: '2.0'
name: 'QuickTest'
implements: '../base.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: random
  max_images: 5

imports:
  Place:
    - "luxury living room, glass table"
    - "tropical jungle, giant ferns"
    - "desert landscape, sand dunes"
  Outfit:
    - ../variations/outfit.yaml
    - "red dress, elegant"

template: |
  1girl, beautiful,
  {Place},
  {Outfit},
  detailed
```

---

## 12. Rétrocompatibilité

### 12.1 Détection de version

**Règle :**
- Si `version:` commence par `1.` → Système V1.x (legacy)
- Si `version:` commence par `2.` → Système V2.0 (nouveau)
- Si pas de `version:` → **Assume V1.0** + Warning

### 12.2 Cohabitation V1/V2

Les deux systèmes coexistent dans le codebase :
- `CLI/src/templating/v1/` : Ancien système (resolver.py actuel)
- `CLI/src/templating/v2/` : Nouveau système
- `CLI/src/templating/version_router.py` : Point d'entrée unifié

**Voir `template-system-v2-retrocompat.md` pour détails**

---

## 13. Notes d'implémentation

### 13.1 Ordre de priorité (resolution)

1. `chunks:` (valeurs spécifiques)
2. `defaults:` (valeurs par défaut)
3. Héritage parent (récursif)

### 13.2 Cache de résolution

Pour éviter de recharger les mêmes fichiers :
- Cache des fichiers YAML chargés (par chemin absolu)
- Cache des chunks résolus (avec héritage)
- Invalidation si fichier modifié

### 13.3 Performance

- Validation en parallèle (phases indépendantes)
- Résolution lazy (charger seulement ce qui est utilisé)
- Cache agressif

---

**Fin de la spécification technique V2.0**

**Prochaine étape :** Voir `template-system-v2-architecture.md` pour le plan d'implémentation détaillé
