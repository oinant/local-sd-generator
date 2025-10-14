# YAML Schema Reference

**Schéma formel complet de tous les fichiers YAML V2.0**

---

## Types de fichiers

| Extension | Type | Usage |
|-----------|------|-------|
| `.prompt.yaml` | Prompt template | Template de génération principal |
| `.template.yaml` | Base template | Template réutilisable (héritage) |
| `.yaml` | Variation file | Fichier de variations |
| `.chunk.yaml` | Chunk | Fragment réutilisable |

---

## 1. Prompt Template (`.prompt.yaml`)

### Schema complet

```yaml
# OBLIGATOIRE
version: string                    # Toujours '2.0'
name: string                       # Nom du template

# CONTENU (au moins un obligatoire)
template: string                   # Contenu du prompt (V2)
prompt: string                     # Alias de template (legacy)

# OPTIONNEL
description: string                # Description du template
implements: string                 # Chemin vers template parent
imports: object | string           # Imports de variations
chunks: object                     # Chunks réutilisables
negative_prompt: string            # Prompt négatif

generation: object                 # Configuration de génération (voir section)
parameters: object                 # Paramètres SD (voir section)
output: object                     # Configuration de sortie (voir section)
```

### Champs détaillés

#### `version`

**Type** : `string`
**Obligatoire** : ✅
**Valeurs** : `'2.0'` uniquement

```yaml
version: '2.0'
```

---

#### `name`

**Type** : `string`
**Obligatoire** : ✅
**Contraintes** : Non vide

```yaml
name: 'My Template Name'
```

---

#### `template` / `prompt`

**Type** : `string`
**Obligatoire** : ✅ (au moins un des deux)
**Préférence** : `template` (V2), `prompt` (legacy)

```yaml
template: |
  masterpiece, {Expression}, beautiful portrait
```

**Placeholders** : `{PlaceholderName}` ou `{PlaceholderName[selector]}`

---

#### `description`

**Type** : `string`
**Obligatoire** : ❌
**Usage** : Documentation, liste des templates

```yaml
description: 'Generate character portraits with different expressions'
```

---

#### `implements`

**Type** : `string` (path)
**Obligatoire** : ❌
**Usage** : Héritage de template parent

```yaml
implements: ../templates/base_portrait.template.yaml
```

**Contraintes** :
- Fichier doit exister
- Pas de dépendances circulaires (A → B → A)
- Peut être multi-niveau (A → B → C)

---

#### `imports`

**Type** : `object` ou `string`
**Obligatoire** : ❌
**Usage** : Définir les variations pour les placeholders

**Format 1 : Fichier unique**
```yaml
imports:
  Expression: ../variations/expressions.yaml
```

**Format 2 : Fichiers multiples (merge)**
```yaml
imports:
  Outfit:
    - ../variations/outfits.casual.yaml
    - ../variations/outfits.formal.yaml
```

**Format 3 : Liste inline**
```yaml
imports:
  Expression:
    - happy, smiling
    - sad, crying
    - angry, frowning
```

**Format 4 : Dict inline**
```yaml
imports:
  Expression:
    happy: smiling, cheerful expression
    sad: crying, tears
    neutral: neutral expression
```

**Format 5 : Avec configuration**
```yaml
imports:
  Expression:
    source: ../variations/expressions.yaml
    weight: 10  # Poids de boucle
```

---

#### `chunks`

**Type** : `object`
**Obligatoire** : ❌
**Usage** : Définir des chunks réutilisables

```yaml
chunks:
  QUALITY: ../chunks/quality_tags.chunk.yaml
  STYLE: ../chunks/anime_style.chunk.yaml
```

**Utilisation dans template** : `@CHUNK_NAME`

---

#### `negative_prompt`

**Type** : `string`
**Obligatoire** : ❌
**Usage** : Prompt négatif

```yaml
negative_prompt: |
  low quality, blurry, bad anatomy
```

**Peut contenir des placeholders** :
```yaml
negative_prompt: |
  low quality, {NegativeExpression}, bad anatomy
```

---

#### `generation`

**Type** : `object`
**Obligatoire** : ✅
**Schema** : Voir section [Generation Config](#generation-config)

---

#### `parameters`

**Type** : `object`
**Obligatoire** : ❌
**Schema** : Voir section [Parameters Config](#parameters-config)

---

#### `output`

**Type** : `object`
**Obligatoire** : ❌
**Schema** : Voir section [Output Config](#output-config)

---

## 2. Generation Config

### Schema

```yaml
generation:
  mode: string                     # Mode de génération
  seed_mode: string                # Mode de seed
  seed: int                        # Seed de base
  max_images: int                  # Nombre d'images
```

### Champs

#### `mode`

**Type** : `string`
**Obligatoire** : ✅
**Valeurs** : `combinatorial`, `random`
**Défaut** : `combinatorial`

```yaml
generation:
  mode: combinatorial  # Toutes les combinaisons
  # ou
  mode: random         # Combinaisons aléatoires
```

---

#### `seed_mode`

**Type** : `string`
**Obligatoire** : ✅
**Valeurs** : `fixed`, `progressive`, `random`
**Défaut** : `progressive`

```yaml
generation:
  seed_mode: fixed        # Même seed pour toutes les images
  # ou
  seed_mode: progressive  # Seeds 42, 43, 44, ...
  # ou
  seed_mode: random       # Seed -1 (aléatoire)
```

---

#### `seed`

**Type** : `int`
**Obligatoire** : ✅
**Valeurs** : `>= -1`
**Défaut** : `42`

```yaml
generation:
  seed: 42     # Seed de base
  # ou
  seed: -1     # Random seed
```

---

#### `max_images`

**Type** : `int`
**Obligatoire** : ✅
**Valeurs** : `>= -1`
**Défaut** : `-1` (toutes les combinaisons)

```yaml
generation:
  max_images: -1   # Toutes les combinaisons
  # ou
  max_images: 50   # Limite à 50 images
```

**Note** : En mode `combinatorial`, si `max_images` > combinaisons totales, génère toutes les combinaisons.

---

## 3. Parameters Config

### Schema

```yaml
parameters:
  # Dimensions
  width: int                       # Largeur
  height: int                      # Hauteur

  # Génération
  steps: int                       # Nombre de steps
  cfg_scale: float                 # CFG scale
  sampler: string                  # Sampler
  scheduler: string                # Scheduler (optionnel)

  # Batch
  batch_size: int                  # Batch size
  batch_count: int                 # Batch count

  # Hires Fix
  enable_hr: bool                  # Activer hires fix
  hr_scale: float                  # Facteur d'upscale
  hr_upscaler: string              # Upscaler
  denoising_strength: float        # Denoising strength
  hr_second_pass_steps: int        # Steps du second pass

  # ADetailer
  alwayson_scripts: object         # Scripts always-on
```

### Champs de base

#### `width` / `height`

**Type** : `int`
**Obligatoire** : ❌
**Défaut** : `512` / `512`
**Contraintes** : Multiples de 64 recommandés

```yaml
parameters:
  width: 512
  height: 768
```

**Résolutions courantes** :
- SD 1.5 : 512×512, 512×768, 768×512
- SDXL : 1024×1024, 832×1216, 1216×832

---

#### `steps`

**Type** : `int`
**Obligatoire** : ❌
**Défaut** : `20`
**Valeurs** : 1-150 (pratique : 20-30)

```yaml
parameters:
  steps: 20
```

---

#### `cfg_scale`

**Type** : `float`
**Obligatoire** : ❌
**Défaut** : `7.0`
**Valeurs** : 1-30 (pratique : 5-10)

```yaml
parameters:
  cfg_scale: 7.0
```

---

#### `sampler`

**Type** : `string`
**Obligatoire** : ❌
**Défaut** : Selon SD WebUI
**Valeurs** : Voir `sdgen api samplers`

```yaml
parameters:
  sampler: DPM++ 2M Karras
```

**Samplers courants** :
- `DPM++ 2M Karras`
- `DPM++ SDE Karras`
- `Euler a`
- `DDIM`
- `UniPC`

---

#### `scheduler`

**Type** : `string`
**Obligatoire** : ❌
**Défaut** : `Automatic`
**Valeurs** : Voir `sdgen api schedulers`
**Note** : SD WebUI 1.9+ uniquement

```yaml
parameters:
  scheduler: Karras
```

**Schedulers courants** :
- `Karras`
- `Exponential`
- `SGM Uniform` (SDXL)
- `Polyexponential`

---

#### `batch_size` / `batch_count`

**Type** : `int`
**Obligatoire** : ❌
**Défaut** : `1` / `1`

```yaml
parameters:
  batch_size: 1    # Générer 1 image à la fois
  batch_count: 1   # Répéter 1 fois
```

---

### Hires Fix

#### `enable_hr`

**Type** : `bool`
**Obligatoire** : ❌
**Défaut** : `false`

```yaml
parameters:
  enable_hr: true
```

---

#### `hr_scale`

**Type** : `float`
**Obligatoire** : Si `enable_hr: true`
**Valeurs** : 1.0-4.0 (pratique : 1.5-2.0)

```yaml
parameters:
  hr_scale: 1.5  # 512×768 → 768×1152
```

---

#### `hr_upscaler`

**Type** : `string`
**Obligatoire** : Si `enable_hr: true`
**Valeurs** : Voir `sdgen api upscalers`

```yaml
parameters:
  hr_upscaler: 4x_foolhardy_Remacri
```

**Upscalers courants** :
- `4x_foolhardy_Remacri`
- `4x-UltraSharp`
- `R-ESRGAN 4x+`
- `R-ESRGAN 4x+ Anime6B`

---

#### `denoising_strength`

**Type** : `float`
**Obligatoire** : Si `enable_hr: true`
**Valeurs** : 0.0-1.0 (pratique : 0.3-0.5)

```yaml
parameters:
  denoising_strength: 0.4
```

---

#### `hr_second_pass_steps`

**Type** : `int`
**Obligatoire** : ❌
**Défaut** : 0 (utilise `steps`)
**Valeurs** : 0-150

```yaml
parameters:
  hr_second_pass_steps: 15
```

---

### ADetailer

```yaml
parameters:
  alwayson_scripts:
    ADetailer:
      args:
        - ad_model: face_yolov8n.pt
          ad_prompt: "detailed face, high quality"
          ad_negative_prompt: "low quality"
          ad_confidence: 0.3
          ad_dilate_erode: 4
```

**Voir** : [ADetailer Documentation](../technical/adetailer.md)

---

## 4. Output Config

### Schema

```yaml
output:
  session_name: string             # Nom de la session
  filename_keys: array             # Clés pour noms de fichiers
```

### Champs

#### `session_name`

**Type** : `string`
**Obligatoire** : ❌
**Défaut** : Nom du template

```yaml
output:
  session_name: my_generation
```

**Résultat** :
```
apioutput/20251014_143052_my_generation/
```

---

#### `filename_keys`

**Type** : `array[string]`
**Obligatoire** : ❌
**Défaut** : Aucun (numérotation simple)

```yaml
output:
  filename_keys:
    - Expression
    - Outfit
    - Angle
```

**Résultat** :
```
my_generation_0001_Expression-Happy_Outfit-Casual_Angle-Front.png
```

---

## 5. Variation File (`.yaml`)

### Schema

```yaml
type: string                       # Type de variation (optionnel)
version: string                    # Version (optionnel)
name: string                       # Nom (optionnel)
description: string                # Description (optionnel)

variations: object | array         # Variations (obligatoire)
```

### Format simple (array)

```yaml
variations:
  - happy, smiling
  - sad, crying
  - angry, frowning
  - neutral
```

### Format avec clés (object)

```yaml
variations:
  happy: smiling, cheerful expression
  sad: crying, tears, melancholic
  angry: frowning, furious look
  neutral: neutral expression
```

### Format avec métadonnées

```yaml
type: variations
version: '1.0'
name: Facial Expressions
description: Common facial expressions

variations:
  happy: smiling, cheerful expression
  sad: crying, tears
  angry: frowning, furious
```

---

## 6. Base Template (`.template.yaml`)

### Schema

Identique à `.prompt.yaml` mais généralement **sans** :
- Champ `generation` (défini par l'enfant)
- Champ `output` (défini par l'enfant)

**Usage typique** :
```yaml
version: '2.0'
name: 'Base Portrait Template'

imports:
  HairColor: ../variations/haircolors.yaml
  Outfit: ../variations/outfits.yaml

template: |
  masterpiece, {HairColor} hair, {Outfit}, {prompt}

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

**Placeholder `{prompt}`** : Point d'injection du contenu enfant.

---

## 7. Chunk File (`.chunk.yaml`)

### Schema

```yaml
version: string                    # Toujours '2.0'
type: string                       # Toujours 'chunk'
name: string                       # Nom du chunk

template: string                   # Contenu du chunk
```

### Exemple

```yaml
version: '2.0'
type: chunk
name: Quality Tags

template: |
  masterpiece, best quality, high detail, HDR, 8K
```

**Utilisation** :
```yaml
chunks:
  QUALITY: ../chunks/quality.chunk.yaml

template: |
  @QUALITY, portrait of a woman
```

---

## Règles de validation

### Validations globales

| Règle | Erreur |
|-------|--------|
| `version` doit être `'2.0'` | ❌ Invalid version |
| `name` ne peut pas être vide | ❌ Missing name |
| `template` ou `prompt` obligatoire | ❌ Missing template/prompt |
| Fichiers `implements` doivent exister | ❌ File not found |
| Fichiers `imports` doivent exister | ❌ File not found |
| Pas de dépendances circulaires | ❌ Circular dependency |
| Placeholders doivent avoir import | ❌ Missing import for placeholder |

### Validations generation

| Règle | Erreur |
|-------|--------|
| `mode` doit être `combinatorial` ou `random` | ❌ Invalid mode |
| `seed_mode` doit être `fixed`, `progressive` ou `random` | ❌ Invalid seed_mode |
| `seed` doit être `>= -1` | ❌ Invalid seed |
| `max_images` doit être `>= -1` | ❌ Invalid max_images |

### Validations parameters

| Règle | Erreur |
|-------|--------|
| `width` / `height` doivent être `> 0` | ❌ Invalid dimensions |
| `steps` doit être `> 0` | ❌ Invalid steps |
| `cfg_scale` doit être `> 0` | ❌ Invalid cfg_scale |
| Si `enable_hr: true`, `hr_scale` obligatoire | ❌ Missing hr_scale |
| Si `enable_hr: true`, `hr_upscaler` obligatoire | ❌ Missing hr_upscaler |

---

## Exemples complets

### Exemple 1 : Template minimal

```yaml
version: '2.0'
name: 'Minimal Template'

template: |
  masterpiece, beautiful portrait

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 1
```

### Exemple 2 : Template complet

```yaml
version: '2.0'
name: 'Complete Template'
description: 'Portrait generation with variations'

implements: ../templates/base_portrait.template.yaml

imports:
  Expression: ../variations/expressions.yaml
  Outfit:
    - ../variations/outfits.casual.yaml
    - ../variations/outfits.formal.yaml

chunks:
  QUALITY: ../chunks/quality.chunk.yaml

template: |
  @QUALITY, portrait, {Expression}, {Outfit}, detailed

negative_prompt: |
  low quality, blurry, bad anatomy

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
  scheduler: Karras
  enable_hr: true
  hr_scale: 1.5
  hr_upscaler: 4x_foolhardy_Remacri
  denoising_strength: 0.4
  hr_second_pass_steps: 15

output:
  session_name: portraits
  filename_keys:
    - Expression
    - Outfit
```

---

## Voir aussi

- **[Template Syntax](template-syntax.md)** - Syntaxe détaillée
- **[Selectors Reference](selectors-reference.md)** - Sélecteurs
- **[CLI Commands](cli-commands.md)** - Validation
- **[Technical Spec](../technical/template-system-spec.md)** - Spécification complète

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
