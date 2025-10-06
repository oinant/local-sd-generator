# 🔄 Prompt de Conversion - JSON Legacy → YAML Phase 2

## Contexte

J'ai des configurations existantes au format **JSON Legacy** (utilisées avec `image_variation_generator.py`) et je veux les convertir au nouveau format **YAML Phase 2** (système de templating avancé avec chunks et multi-field).

## Format Legacy (À CONVERTIR)

### Structure typique :
```
mon_setup/
├── config.json              # Configuration JSON
├── variations/
│   ├── expressions.txt      # Format: key→value ou simple list
│   ├── angles.txt
│   ├── lighting.txt
│   └── ...
```

### Exemple config.json legacy :
```json
{
  "version": "1.0",
  "name": "Ma Configuration",
  "description": "Description du setup",
  "prompt": {
    "template": "beautiful woman, {Expression}, {Angle}, {Lighting}",
    "negative": "low quality, blurry"
  },
  "variations": {
    "Expression": "variations/expressions.txt",
    "Angle": "variations/angles.txt",
    "Lighting": "variations/lighting.txt"
  },
  "generation": {
    "mode": "combinatorial",
    "seed": 42,
    "seed_mode": "progressive",
    "max_images": 100
  },
  "parameters": {
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras"
  }
}
```

### Exemple fichier variations.txt legacy :
```
# Format simple (liste)
happy
sad
angry

# OU format avec clés
1→happy, smiling
2→sad, crying
3→angry, frowning
```

## Format Cible (YAML Phase 2)

### Structure souhaitée :
```
examples/
├── prompts/
│   └── mon_setup.prompt.yaml        # Config principale
├── variations/
│   ├── expressions.yaml             # Variations converties
│   ├── angles.yaml
│   └── lighting.yaml
└── characters/ ou base/
    └── base_character.char.yaml     # Si applicable
```

### Format .prompt.yaml Phase 2 :
```yaml
version: "2.0"
name: "Ma Configuration"
description: "Description du setup"

base_path: ".."  # Relatif au fichier .prompt.yaml

# Template du prompt
template: |
  {CHARACTER}
  {POSES}
  {LIGHTING}
  masterpiece, best quality

negative_prompt: "low quality, blurry"

# Références aux variations
variations:
  CHARACTER: "characters/base_character.char.yaml"
  POSES: "variations/poses.yaml"
  LIGHTING: "variations/lighting.yaml"

# Configuration génération
generation:
  mode: "combinatorial"    # ou "random"
  seed: 42
  seed_mode: "progressive" # "fixed", "progressive", "random"
  max_images: 100

# Paramètres SD
parameters:
  width: 512
  height: 768
  steps: 30
  cfg_scale: 7.0
  sampler: "DPM++ 2M Karras"
  batch_size: 1
  batch_count: 1

# Nommage des fichiers
output:
  session_name: "mon_setup"
  filename_keys: ["CHARACTER", "POSES"]
```

### Format variations.yaml Phase 2 :
```yaml
type: variations
name: "Facial Expressions"
version: "1.0"

# Simple list format
variations:
  happy: "smiling, cheerful expression"
  sad: "crying, tears, melancholic"
  angry: "frowning, intense gaze"
  neutral: "calm, relaxed expression"
  surprised: "eyes wide, mouth open"
```

### Format character.char.yaml (optionnel) :
```yaml
type: chunk
name: "Base Female Character"
version: "1.0"

fields:
  age: "25 years old"
  ethnicity: "{ETHNICITY}"
  body: "{BODY_TYPE}"
  hair: "long brown hair"
  eyes: "blue eyes"
  quality: "masterpiece, best quality"

# Template de rendu
template: |
  beautiful woman, {age}
  {ethnicity}
  {body}
  {hair}, {eyes}
  {quality}
```

## Tâche : Convertir mes setups

**Ce que j'ai :**
- Plusieurs dossiers avec config.json + fichiers .txt
- Localisés dans : `/mnt/d/StableDiffusion/local-sd-generator/`

**Ce que je veux :**
1. Analyser mes configurations JSON legacy existantes
2. Convertir chaque setup en format YAML Phase 2
3. Organiser les fichiers selon la nouvelle structure :
   - Prompts principaux dans `examples/prompts/`
   - Variations dans `examples/variations/`
   - Chunks/characters dans `examples/characters/` ou `examples/base/`
4. Optimiser l'organisation :
   - Identifier les variations réutilisables (à partager entre setups)
   - Créer des chunks pour les éléments communs
   - Utiliser la syntaxe avancée (selectors, multi-field) si pertinent

**Options de conversion :**

### Option A : Conversion directe 1:1
- Chaque JSON → 1 fichier .prompt.yaml
- Chaque .txt → 1 fichier .yaml
- Structure minimale, pas d'optimisation

### Option B : Conversion optimisée (RECOMMANDÉ)
- Analyse des variations communes entre setups
- Factorisation en chunks réutilisables
- Utilisation de multi-field quand pertinent
- Organisation intelligente

### Option C : Conversion avec guidance
- Me poser des questions sur chaque setup
- Suggestions d'optimisations
- Explication des choix

## Questions pour Claude

1. **Peux-tu d'abord lister tous mes setups JSON legacy existants ?**
   - Localiser tous les fichiers config.json
   - Afficher leur structure
   - Identifier les patterns communs

2. **Quelle option de conversion me recommandes-tu ?**
   - Option A, B ou C ?
   - Pourquoi ?

3. **Procède à la conversion**
   - Créer les fichiers YAML
   - Organiser dans la bonne structure
   - Tester avec un preview

## Contraintes et Préférences

- ✅ Garder la compatibilité maximale
- ✅ Préserver tous les paramètres de génération
- ✅ Ne rien perdre lors de la conversion
- ✅ Utiliser les features Phase 2 quand c'est pertinent
- ✅ Documentation inline (commentaires YAML)
- ⚠️ Ne pas modifier mes fichiers legacy (créer de nouveaux fichiers)

## Validation Post-Conversion

Après conversion, je veux pouvoir :
```bash
# Preview du setup converti
python3 generate_from_template.py examples/prompts/mon_setup.prompt.yaml --preview

# Comparaison dry-run : ancien vs nouveau
python3 generator_cli.py --config ancien_setup.json --dry-run
python3 generate_from_template.py nouveau_setup.prompt.yaml --count 10 -o nouveau.json

# Comparer les JSONs générés
```

---

## 🚀 Action Demandée

**Claude, peux-tu :**
1. Analyser mes configurations legacy existantes
2. Me proposer un plan de conversion
3. Procéder à la conversion avec l'option recommandée
4. Me donner les commandes pour tester les conversions

Merci ! 🙏
