# Template Syntax Reference

**Référence rapide de la syntaxe YAML pour templates V2.0**

---

## Structure minimale

```yaml
version: '2.0'
name: 'Template Name'

template: |
  your prompt here

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 10
```

---

## Champs disponibles

### Champs obligatoires

| Champ | Type | Description |
|-------|------|-------------|
| `version` | string | Version du template (toujours `'2.0'`) |
| `name` | string | Nom du template |
| `template` ou `prompt` | string | Contenu du prompt |
| `generation` | object | Configuration de génération |

### Champs optionnels

| Champ | Type | Description |
|-------|------|-------------|
| `description` | string | Description du template |
| `implements` | string | Chemin vers template parent |
| `imports` | object | Imports de variations |
| `chunks` | object | Chunks réutilisables |
| `negative_prompt` | string | Prompt négatif |
| `parameters` | object | Paramètres SD |
| `output` | object | Configuration de sortie |

---

## Placeholders

### Syntaxe de base

```yaml
template: |
  masterpiece, {Expression}, {Pose}, beautiful
```

### Avec sélecteurs

```yaml
template: |
  {Expression[5]}                    # 5 random variations
  {Expression[#0,2,4]}               # Indices spécifiques
  {Expression[happy,sad,angry]}      # Clés nommées
  {Expression[#0-10]}                # Range d'indices
  {Expression[random:5]}             # Syntaxe alternative
  {Expression[weight:10]}            # Poids de boucle
```

**Voir** : [Selectors Reference](selectors-reference.md) pour détails complets

---

## Imports

### Import simple (fichier YAML)

```yaml
imports:
  Expression: ../variations/expressions.yaml
```

### Import multiple (merge automatique)

```yaml
imports:
  Outfit:
    - ../variations/outfits.casual.yaml
    - ../variations/outfits.formal.yaml
    - ../variations/outfits.fantasy.yaml
```

### Import inline (liste)

```yaml
imports:
  Expression:
    - happy, smiling, cheerful
    - sad, crying, melancholic
    - angry, frowning
```

### Import inline (dict)

```yaml
imports:
  Expression:
    happy: smiling, cheerful expression
    sad: crying, tears, melancholic
    neutral: neutral expression
```

### Import avec configuration

```yaml
imports:
  Expression:
    source: ../variations/expressions.yaml
    weight: 10  # Poids de boucle
```

---

## Inheritance

### Template parent

**`templates/base.template.yaml`**
```yaml
version: '2.0'
name: 'Base Template'

parameters:
  width: 512
  height: 768
  steps: 20

template: |
  masterpiece, {prompt}, high quality
```

### Template enfant

**`prompts/child.prompt.yaml`**
```yaml
version: '2.0'
name: 'Child Template'
implements: ../templates/base.template.yaml

template: |
  portrait of a woman, smiling
```

**Résultat** : `masterpiece, portrait of a woman, smiling, high quality` avec paramètres hérités.

### Override de paramètres

```yaml
implements: ../templates/base.template.yaml

parameters:
  steps: 30  # Override seulement steps
```

---

## Generation

### Champs

| Champ | Type | Valeurs | Défaut | Description |
|-------|------|---------|--------|-------------|
| `mode` | string | `combinatorial`, `random` | `combinatorial` | Mode de génération |
| `seed_mode` | string | `fixed`, `progressive`, `random` | `progressive` | Mode de seed |
| `seed` | int | `>= -1` | `42` | Seed de base |
| `max_images` | int | `>= -1` | `-1` | Nombre d'images (-1 = toutes) |

### Modes de génération

**`combinatorial`** : Génère toutes les combinaisons possibles
```yaml
generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1  # Toutes les combinaisons
```

**`random`** : Génère N combinaisons aléatoires uniques
```yaml
generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 100  # 100 combinaisons aléatoires
```

### Seed modes

| Mode | Comportement | Usage |
|------|--------------|-------|
| `fixed` | Même seed pour toutes les images | A/B testing, comparaisons |
| `progressive` | Seeds 42, 43, 44, ... | Reproductible mais varié |
| `random` | Seed -1 (aléatoire) | Maximum de diversité |

---

## Parameters

### Paramètres SD de base

```yaml
parameters:
  width: 512                    # Largeur (multiples de 64)
  height: 768                   # Hauteur (multiples de 64)
  steps: 20                     # Nombre de steps
  cfg_scale: 7                  # CFG scale
  sampler: DPM++ 2M Karras      # Sampler
  scheduler: Karras             # Scheduler (optionnel, SD 1.9+)
  batch_size: 1                 # Batch size
  batch_count: 1                # Batch count
```

### Hires Fix

```yaml
parameters:
  enable_hr: true
  hr_scale: 1.5                      # Facteur d'upscale
  hr_upscaler: 4x_foolhardy_Remacri  # Upscaler
  denoising_strength: 0.4            # Denoising strength
  hr_second_pass_steps: 15           # Steps du second pass
```

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

### Liste complète des samplers

```bash
# Lister les samplers disponibles
sdgen api samplers
```

Samplers courants :
- `DPM++ 2M Karras`
- `DPM++ SDE Karras`
- `Euler a`
- `DDIM`
- `UniPC`

---

## Output

### Configuration de sortie

```yaml
output:
  session_name: my_generation       # Nom de la session (défaut: template name)
  filename_keys:                    # Clés pour noms de fichiers (optionnel)
    - Expression
    - Outfit
    - Angle
```

### Résultat

**Sans `filename_keys`** :
```
apioutput/20251014_143052_my_generation/
├── my_generation_0001.png
├── my_generation_0002.png
└── ...
```

**Avec `filename_keys`** :
```
apioutput/20251014_143052_my_generation/
├── my_generation_0001_Expression-Happy_Outfit-Casual.png
├── my_generation_0002_Expression-Happy_Outfit-Formal.png
└── ...
```

---

## Chunks

### Définition de chunk

**`chunks/quality.chunk.yaml`**
```yaml
version: '2.0'
type: chunk
name: Quality Tags

template: |
  masterpiece, best quality, high detail, HDR
```

### Utilisation

```yaml
chunks:
  QUALITY: ../chunks/quality.chunk.yaml

template: |
  @QUALITY, portrait of a woman, {Expression}
```

**Résultat** : `masterpiece, best quality, high detail, HDR, portrait of a woman, smiling`

---

## Negative Prompt

### Simple

```yaml
negative_prompt: |
  low quality, blurry, bad anatomy
```

### Avec placeholders

```yaml
negative_prompt: |
  low quality, {NegativeExpression}, bad anatomy

imports:
  Expression: ../variations/expressions.yaml
  NegativeExpression: ../variations/negative_expressions.yaml
```

---

## Exemples complets

### Template minimal

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

### Template avec variations

```yaml
version: '2.0'
name: 'With Variations'

imports:
  Expression: ../variations/expressions.yaml
  Outfit: ../variations/outfits.yaml

template: |
  portrait, {Expression}, {Outfit}, detailed

negative_prompt: |
  low quality, blurry

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

output:
  session_name: portraits
  filename_keys:
    - Expression
    - Outfit
```

### Template avec héritage

```yaml
version: '2.0'
name: 'With Inheritance'
implements: ../templates/base_portrait.template.yaml

imports:
  Expression: ../variations/expressions.yaml

template: |
  {Expression}, looking at viewer

generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 50
```

---

## Validation

### Règles de validation

**Champs obligatoires** :
- `version` doit être `'2.0'`
- `name` ne peut pas être vide
- `template` ou `prompt` doit être présent
- `generation` doit contenir `mode`, `seed_mode`, `seed`, `max_images`

**Références** :
- Tous les fichiers `implements` doivent exister
- Tous les fichiers `imports` doivent exister
- Tous les placeholders dans `template` doivent avoir un import correspondant

**Héritage** :
- Pas de dépendances circulaires (A → B → A)

---

## Voir aussi

- **[Selectors Reference](selectors-reference.md)** - Tous les sélecteurs
- **[CLI Commands](cli-commands.md)** - Commandes de génération
- **[YAML Schema](yaml-schema.md)** - Schéma formel complet
- **[Templates Advanced Guide](../guide/4-templates-advanced.md)** - Explications détaillées

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
