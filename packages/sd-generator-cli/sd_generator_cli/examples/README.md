# Portrait Generation Examples

Ce dossier contient des exemples complets pour générer des portraits de femmes avec le système de templating Phase 2.

## 📁 Structure

```
examples/
├── base/                    # Templates de chunks
│   └── portrait_woman.char.template.yaml
├── characters/              # Instances de personnages
│   ├── portrait_base.char.yaml
│   ├── sophia.char.yaml
│   └── yuki.char.yaml
├── variations/              # Fichiers de variations
│   ├── ethnicities.yaml     (multi-field: skin + eyes)
│   ├── body_types.yaml      (multi-field: body + breast_size)
│   ├── hair_styles.yaml     (18 styles)
│   ├── expressions.yaml     (12 expressions)
│   ├── lighting.yaml        (14 setups)
│   └── framing.yaml         (14 angles/cadrages)
└── prompts/                 # Configurations de prompts
    ├── quick_test.prompt.yaml
    ├── sophia_expressions.prompt.yaml
    ├── portrait_selected.prompt.yaml
    └── portrait_variations_full.prompt.yaml
```

---

## 🎯 Fichiers de Variations

### Multi-Field (expansion automatique)

#### `ethnicities.yaml`
**8 variations** qui définissent automatiquement `skin` + `eyes` :
- `caucasian_fair` - Peau claire + yeux bleus
- `caucasian_tan` - Peau bronzée + yeux verts
- `african` - Peau foncée + yeux marron foncé
- `asian_east` - Peau claire + yeux en amande
- `asian_south` - Peau brune + yeux marron
- `latina` - Peau olive + yeux marron
- `middle_eastern` - Peau méditerranéenne + yeux noisette
- `mixed_asian_caucasian` - Peau métisse + yeux marron clair

#### `body_types.yaml`
**12 variations** qui définissent `body_type` + `breast_size` :
- `petite_small`, `petite_medium`
- `slim_small`, `slim_medium`
- `athletic_medium`, `athletic_large`
- `average_medium`, `average_large`
- `curvy_large`, `curvy_xlarge`
- `plus_large`, `plus_xlarge`

### Simple Variations

#### `hair_styles.yaml`
**18 styles** : long/medium/short × blonde/brunette/black/red/colors
- Long : straight, wavy, curly
- Medium : layered, bob
- Short : pixie, bob
- Updos : bun, ponytail, braided
- Colors : blonde, brunette, black, red, platinum, pink, silver

#### `expressions.yaml`
**12 expressions** :
- neutral, slight_smile, smiling, laughing
- seductive, confident, mysterious, serious
- contemplative, playful, shy, surprised

#### `lighting.yaml`
**14 setups** :
- Natural : soft, golden hour, backlit
- Studio : key, rembrandt, butterfly, split, loop
- Dramatic : low key, high key
- Special : cinematic, neon, candlelight, moonlight

#### `framing.yaml`
**14 angles/cadrages** :
- Headshots : front, 3/4, profile
- Body : shoulders up, bust, waist up, full body
- Close-ups : face, eyes
- Angles : over shoulder, from above/below, dutch angle

---

## 🚀 Utilisation

### Méthode Simple (Recommandée)

Utilisez le script `generate_from_template.py` qui génère du JSON compatible avec le système legacy :

```bash
cd /mnt/d/StableDiffusion/local-sd-generator/CLI

# Preview des variations
python3 generate_from_template.py examples/prompts/quick_test.prompt.yaml --preview

# Générer le JSON (16 variations)
python3 generate_from_template.py examples/prompts/quick_test.prompt.yaml

# Limiter le nombre de variations
python3 generate_from_template.py examples/prompts/portrait_full.prompt.yaml --count 50

# Spécifier le fichier de sortie
python3 generate_from_template.py examples/prompts/sophia_expressions.prompt.yaml -o sophia_batch.json
```

Le JSON généré peut ensuite être utilisé avec le système de génération d'images.

### Méthode Programmatique (Python)

```python
from templating import load_prompt_config, resolve_prompt
from pathlib import Path

config = load_prompt_config('examples/prompts/quick_test.prompt.yaml')
variations = resolve_prompt(config, base_path=Path('examples'))

print(f'Généré {len(variations)} variations')
for i, var in enumerate(variations[:3]):
    print(f'\n=== Variation {i} ===')
    print(var.final_prompt)
```

### Génération Sophia (60 images)

Étude d'expressions de Sophia avec 5 éclairages :

```yaml
# prompts/sophia_expressions.prompt.yaml
{SOPHIA with expression=EXPRESSIONS}
{LIGHTING[natural_soft,studio_rembrandt,studio_butterfly,cinematic,golden_hour]}
bust portrait, front view

# 12 expressions × 5 lighting = 60 images
```

### Génération sélective (50 images random)

```yaml
# prompts/portrait_selected.prompt.yaml
{PORTRAIT with
  ethnicity=ETHNICITIES[caucasian_fair,asian_east],
  body=BODY_TYPES[slim_medium,athletic_medium,curvy_large],
  hair=HAIR[...6 styles...],
  expression=EXPRESSIONS[neutral,smiling,seductive,confident]
}
{LIGHTING[natural_soft,studio_rembrandt,cinematic]}
{FRAMING[bust_portrait,headshot_three_quarter]}

# Mode: random, max_images: 50
```

---

## 📊 Combinaisons possibles

### Quick Test
- 2 ethnies × 2 body types × 2 expressions × 2 lighting
- **= 16 images** (combinatorial)

### Sophia Expressions
- 1 personnage × 12 expressions × 5 lighting
- **= 60 images** (combinatorial)

### Portrait Selected
- 2 ethnies × 3 body × 6 hair × 4 expr × 3 light × 2 framing
- **= 864 combinaisons totales**
- Mode random → 50 images sélectionnées

### Portrait Full
- 8 ethnies × 12 body × 18 hair × 12 expr × 14 light × 14 framing
- **= 5,080,320 combinaisons totales !**
- Mode random → 100 images sélectionnées

---

## 🎨 Exemples de Prompts Générés

### Quick Test - Variation 0
```
beautiful woman, 25 years old
fair skin, caucasian features, athletic build, toned physique, fit body, medium breasts, firm chest
long blonde hair, straight hair, flowing hair, blue eyes
smiling, happy expression, cheerful
masterpiece, best quality, highly detailed, 8k uhd, professional photography
soft natural lighting, window light, diffused sunlight
headshot, front view
```

### Sophia - Confident + Rembrandt
```
Sophia, 28 years old
fair skin, caucasian features, athletic build, toned physique, fit body, medium breasts, firm chest
long blonde hair, ponytail, blue eyes, bright gaze
confident expression, strong gaze
masterpiece, best quality, highly detailed, professional photography
rembrandt lighting, dramatic shadows, classic portrait lighting
bust portrait, front view
```

---

## ⚙️ Personnalisation

### Créer un nouveau personnage

```yaml
# characters/my_character.char.yaml
type: character
name: "My Character"
implements: "base/portrait_woman.char.template.yaml"

fields:
  identity:
    name: "Luna"
    age: "26 years old"

  appearance:
    ethnicity: "olive skin, latina features"
    body_type: "curvy build, hourglass figure"
    breast_size: "large breasts"
    hair: "long black hair, wavy"
    eyes: "dark brown eyes"

  expression:
    current: "seductive expression"

  technical:
    quality: "masterpiece, best quality"
```

### Ajouter des variations de cheveux

```yaml
# variations/hair_styles.yaml
variations:
  - key: my_custom_style
    value: "braided mohawk, punk hairstyle, dyed tips"
    weight: 1.0
```

### Créer un prompt custom

```yaml
# prompts/my_prompt.prompt.yaml
name: "My Custom Prompt"

imports:
  PORTRAIT: characters/portrait_base.char.yaml
  ETHNICITIES: variations/ethnicities.yaml
  # ... autres imports

prompt: |
  {PORTRAIT with ethnicity=ETHNICITIES[african,latina]}
  {LIGHTING[cinematic,neon]}
  close-up portrait

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 5000
```

---

## 📝 Notes

### Multi-field expansion
Les variations multi-field (ethnicities, body_types) modifient **plusieurs champs simultanément** :

```yaml
ethnicity=ETHNICITIES[african]
# Devient automatiquement :
#   appearance.ethnicity: "dark skin, ebony complexion, african features"
#   appearance.eyes: "dark brown eyes"
```

### Priorité des valeurs
1. **Overrides inline** (dans le prompt)
2. **Chunk fields** (dans le .char.yaml)
3. **Template defaults** (dans le .char.template.yaml)

### Modes de génération
- **Combinatorial** : Toutes les combinaisons (exhaustif)
- **Random** : Sélection aléatoire (exploration)

### Seeds
- **Fixed** : Même seed partout (isolation prompt)
- **Progressive** : Seeds incrémentées (reproductible + diversité)
- **Random** : Seed -1 (max créativité)

---

## 🧪 Testing

Pour tester que tout fonctionne :

```bash
cd /mnt/d/StableDiffusion/local-sd-generator/CLI
../venv/bin/python3 -m pytest tests/templating/test_phase2_integration.py -v
```

27 tests doivent passer ✅

---

## 📚 Documentation

Pour plus d'infos sur le système de templating Phase 2 :
- `docs/roadmap/PHASE2_CONTINUATION_PART2.md` - Spécification complète
- `CLI/templating/` - Code source
- `CLI/tests/templating/fixtures/` - Autres exemples (Emma)

---

## 🎯 Prochaines étapes

1. **Tester** avec `quick_test.prompt.yaml`
2. **Personnaliser** les variations selon vos besoins
3. **Créer** vos propres personnages
4. **Générer** vos datasets !

Bon prompt engineering ! 🚀
