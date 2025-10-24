# Themable Templates - Usage Guide

Guide utilisateur pour les templates thématiques avec support de styles.

## Table des matières

- [Concepts](#concepts)
- [Quick Start](#quick-start)
- [Creating Themable Templates](#creating-themable-templates)
- [Creating Themes](#creating-themes)
- [Using Themes](#using-themes)
- [CLI Commands](#cli-commands)
- [Examples](#examples)

---

## Concepts

### Qu'est-ce qu'un Themable Template ?

Un **themable template** est un template réutilisable qui peut être combiné avec différents **themes** pour générer des variations thématiques sans dupliquer le code.

**Avantage principal :** DRY (Don't Repeat Yourself)
- 1 template × N themes = N variations sans duplication

### Dimensions orthogonales

1. **Theme** - Aspects visuels et thématiques (cyberpunk, rockstar, pirates, etc.)
2. **Style** - Style artistique freeform (cartoon, realistic, photorealistic, etc.)

### Exemple concret

**Sans themable templates** (duplication) :
```
├── cyberpunk-teasing.prompt.yaml        # Duplique structure + imports
├── rockstar-teasing.prompt.yaml         # Duplique structure + imports
└── pirates-teasing.prompt.yaml          # Duplique structure + imports
```

**Avec themable templates** (DRY) :
```
├── _tpl_teasing.template.yaml           # Template unique
├── themes/
│   ├── cyberpunk/theme.yaml
│   ├── rockstar/theme.yaml
│   └── pirates/theme.yaml
└── teasing.prompt.yaml                  # Prompt simple (pas d'imports)
```

---

## Quick Start

### 1. Utiliser un template themable existant

```bash
# Lister les themes disponibles
sdgen theme list

# Générer avec un theme
sdgen generate -t _tpl_teasing.template.yaml --theme pirates

# Générer avec un theme + style
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style cartoon
```

### 2. Voir les détails d'un theme

```bash
# Afficher les informations du theme
sdgen theme show cyberpunk

# Valider compatibilité theme/template
sdgen theme validate _tpl_teasing.template.yaml cyberpunk
```

---

## Creating Themable Templates

### Structure d'un template themable

```yaml
# _tpl_character.template.yaml
version: "2.0"
name: "Character Portrait Template"

# 🆕 Activer le support des themes
themable: true

# 🆕 (Optionnel) Support des styles
style_sensitive: true
style_sensitive_placeholders:
  - Rendering
  - Outfit

# Template avec placeholders
template: |
  masterpiece, {Rendering},
  {Ambiance}, {Location},
  girl, {HairCut}, {HairColor},
  wearing {Outfit}, {Accessories}

prompts:
  default: "high quality"

# Imports par défaut (overridables par themes)
imports:
  # Variations communes (partagées)
  EyeColor: common/body/eyecolors.yaml

  # Variations thématiques (avec defaults)
  Ambiance:    defaults/ambiance.yaml
  Location:    defaults/locations.yaml
  HairCut:     defaults/haircut.yaml
  HairColor:   defaults/haircolor.yaml
  Outfit:      defaults/outfit.yaml
  Accessories: defaults/accessories.yaml
  Rendering:   common/rendering.default.yaml

negative_prompt: "low quality, blurry"

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 100
```

### Placeholders thématiques vs communs

**Thématiques** (varient selon le theme) :
- `Ambiance` - Palette couleurs, mood, lighting
- `Location` - Lieux spécifiques au theme
- `HairCut` - Coupes de cheveux thématiques
- `HairColor` - Couleurs de cheveux
- `Outfit` - Vêtements thématiques
- `Accessories` - Accessoires du theme
- `TechAspect` - Éléments technologiques/fantastiques

**Communs** (universels, non-overridés) :
- `Poses` - Poses corporelles
- `Expression` - Expressions faciales
- `BodyType` - Types de corps
- `EyeColor` - Couleurs des yeux
- `CameraAngle` - Angles de caméra

---

## Creating Themes

### Theme explicite (recommandé)

Créer un fichier `theme.yaml` dans le dossier du theme :

```yaml
# themes/cyberpunk/theme.yaml
version: "1.0"
name: cyberpunk

imports:
  # Variations thématiques
  Ambiance:    cyberpunk/cyberpunk_ambiance.yaml
  Location:    cyberpunk/cyberpunk_location.yaml
  HairCut:     cyberpunk/cyberpunk_haircut.yaml
  HairColor:   cyberpunk/cyberpunk_haircolor.yaml
  Outfit:      cyberpunk/cyberpunk_outfit.yaml
  Accessories: cyberpunk/cyberpunk_accessories.yaml

  # Style-sensitive (variants)
  Rendering.default:   cyberpunk/cyberpunk_rendering.default.yaml
  Rendering.cartoon:   cyberpunk/cyberpunk_rendering.cartoon.yaml
  Rendering.realistic: cyberpunk/cyberpunk_rendering.realistic.yaml

variations:
  - Ambiance
  - Location
  - HairCut
  - HairColor
  - Outfit
  - Accessories
  - Rendering
```

### Theme implicite (auto-découverte)

Si `theme.yaml` n'existe pas, le système infère les imports depuis les fichiers `{theme}_*.yaml` :

```
themes/pirates/
├── pirates_ambiance.yaml
├── pirates_location.yaml
├── pirates_haircut.yaml
└── pirates_outfit.yaml
```

→ Auto-détection :
```yaml
imports:
  Ambiance: pirates/pirates_ambiance.yaml
  Location: pirates/pirates_location.yaml
  HairCut:  pirates/pirates_haircut.yaml
  Outfit:   pirates/pirates_outfit.yaml
```

### Convention de nommage

**Format :** `{theme}_{placeholder}.yaml`

**Exemples :**
- `cyberpunk_ambiance.yaml`
- `rockstar_haircut.yaml`
- `pirates_location.yaml`

**Avec styles :**
- `cyberpunk_outfit.default.yaml`
- `cyberpunk_outfit.cartoon.yaml`
- `rockstar_rendering.realistic.yaml`

---

## Using Themes

### Générer avec un theme

```bash
# Theme seul (style par défaut)
sdgen generate -t _tpl_character.template.yaml --theme cyberpunk

# Theme + style
sdgen generate -t _tpl_character.template.yaml --theme cyberpunk --style cartoon

# Sans theme (utilise les imports du template)
sdgen generate -t _tpl_character.template.yaml
```

### Ordre de résolution des imports

**Priorité :** theme → template → common fallback

**Exemple :**

| Placeholder | Theme fourni ? | Résolution |
|-------------|----------------|------------|
| `Ambiance` | ✓ | `themes/cyberpunk/cyberpunk_ambiance.yaml` |
| `Outfit` | ✓ (style=cartoon) | `themes/cyberpunk/cyberpunk_outfit.cartoon.yaml` |
| `Rendering` | ✗ | `common/rendering/rendering.cartoon.yaml` (fallback) |
| `EyeColor` | ✗ | `common/body/eyecolors.yaml` (commun) |

### Styles freeform

Les styles sont **définis par l'utilisateur**, pas hardcodés.

**Styles courants :**
- `default` - Style par défaut
- `cartoon` - Style cartoon/animation
- `realistic` - Style réaliste
- `photorealistic` - Photo-réaliste
- `minimalist` - Minimaliste
- `watercolor` - Aquarelle
- `sketch` - Esquisse

**Créer un style personnalisé :**
```bash
# Créer des fichiers avec le suffix du style
common/rendering/rendering.cyberpunk-noir.yaml
common/lighting/lighting.cyberpunk-noir.yaml

# Utiliser
sdgen generate -t template.yaml --style cyberpunk-noir
```

---

## CLI Commands

### `sdgen generate` avec themes

```bash
# Syntaxe complète
sdgen generate --template <path> --theme <name> --style <style>

# Exemples
sdgen generate -t _tpl_teasing.template.yaml --theme pirates
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style cartoon
sdgen generate -t _tpl_teasing.template.yaml --theme rockstar --style realistic -n 50
```

### `sdgen theme list`

Liste tous les themes disponibles :

```bash
sdgen theme list

# Output:
Available Themes (6 found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Theme          Type       Variations
───────────────────────────────────
cyberpunk      explicit   8 variations
rockstar       explicit   12 variations
pirates        explicit   8 variations
mafia_1920     explicit   8 variations
annees_folles  explicit   8 variations
fantasy        explicit   6 variations
```

### `sdgen theme show <name>`

Affiche les détails d'un theme :

```bash
sdgen theme show cyberpunk

# Output:
Theme: cyberpunk
Type: Explicit
Path: ./themes/cyberpunk/

Imports:
  HairCut          → cyberpunk/cyberpunk_haircut.yaml
  HairColor        → cyberpunk/cyberpunk_haircolor.yaml
  TechAspect       → cyberpunk/cyberpunk_tech-aspect.yaml
  FemaleCharacter  → cyberpunk/cyberpunk_girl.yaml
  ...

Variations: 8
Styles detected: default
```

### `sdgen theme validate <template> <theme>`

Valide la compatibilité theme/template :

```bash
sdgen theme validate _tpl_teasing.template.yaml cyberpunk

# Output:
✓ Theme 'cyberpunk' is compatible with template

Theme provides:
  ✓ HairCut
  ✓ HairColor
  ✓ TechAspect
  ✓ FemaleCharacter
  ✓ TeasingOutfits
  ✓ TeasingLocations
  ✓ TeasingGestures
  ⚠ Accessories (missing, will use template fallback)
```

---

## Examples

### Example 1: Simple theme usage

```bash
# Generate 50 cyberpunk portraits
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk -n 50
```

**Output:** `YYYYMMDD_HHMMSS_Teasing_cyberpunk/`

### Example 2: Theme + Style

```bash
# Cartoon style with pirates theme
sdgen generate -t _tpl_teasing.template.yaml --theme pirates --style cartoon -n 100
```

**Output:** `YYYYMMDD_HHMMSS_Teasing_pirates_cartoon/`

### Example 3: Batch generation (multiple themes)

```bash
# Generate for all themes
for theme in cyberpunk rockstar pirates mafia_1920; do
  sdgen generate -t _tpl_teasing.template.yaml --theme $theme -n 20
done
```

**Output:** 4 sessions × 20 images = 80 images total

### Example 4: Multi-style batch

```bash
# Generate cyberpunk in multiple styles
for style in default cartoon realistic; do
  sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style $style -n 25
done
```

**Output:** 3 sessions × 25 images = 75 images total

### Example 5: Prompt using themable template

```yaml
# teasing-pirates.prompt.yaml
version: "2.0"
name: "Teasing Pirates (Themable)"

implements: "./_tpl_teasing_themable.template.yaml"

# Only common imports (theme provides the rest)
imports:
  EyeColor: ../variations/body/eyecolors.yaml
  Tits:     ../variations/body/tits.yaml

generation:
  mode: random
  seed: 42
  max_images: 100
```

**Usage:**
```bash
# Use with pirates theme
sdgen generate -t teasing-pirates.prompt.yaml --theme pirates

# Switch to another theme without changing the file!
sdgen generate -t teasing-pirates.prompt.yaml --theme cyberpunk
sdgen generate -t teasing-pirates.prompt.yaml --theme rockstar
```

---

## Troubleshooting

### "Theme not found"

```
❌ Error: Theme 'unknown' not found
```

**Solution :** Vérifier les themes disponibles avec `sdgen theme list`

### "Missing import for placeholder"

```
⚠ Warning: Theme 'cyberpunk' missing Outfit.realistic, using fallback
```

**Solution :** Normal si le theme ne fournit pas tous les styles. Le système utilise le fallback automatiquement.

### "File not found"

```
❌ Error: File not found: themes/cyberpunk/cyberpunk_outfit.yaml
```

**Solution :** Vérifier que le fichier existe et que le chemin dans `theme.yaml` est correct.

---

## Best Practices

### 1. Structure des dossiers

```
configs/
├── templates/
│   └── _tpl_character.template.yaml
├── themes/
│   ├── cyberpunk/
│   │   ├── theme.yaml
│   │   └── cyberpunk_*.yaml
│   ├── rockstar/
│   │   ├── theme.yaml
│   │   └── rockstar_*.yaml
│   └── pirates/
│       ├── theme.yaml
│       └── pirates_*.yaml
└── common/
    ├── body/
    ├── poses/
    └── rendering/
```

### 2. Naming conventions

- **Templates :** `_tpl_{name}.template.yaml`
- **Themes :** `themes/{name}/theme.yaml`
- **Variations :** `{theme}_{placeholder}.yaml`
- **Styles :** `{basename}.{style}.yaml`

### 3. Séparation thématique vs commun

**Thématiques** (dans themes/) :
- Changent radicalement selon le theme
- Exemple : cyberpunk vs pirates hair colors

**Communs** (dans common/) :
- Universels, partagés entre themes
- Exemple : body types, facial expressions

### 4. Documentation des themes

Ajouter des commentaires dans `theme.yaml` :

```yaml
# Cyberpunk Theme
# Neon-lit dystopian future aesthetic
# Supports styles: default, cartoon, realistic
version: "1.0"
name: cyberpunk
# ...
```

---

## See Also

- [Technical Documentation](../technical/themable-templates.md) - Architecture interne
- [CLI Reference](../reference/themable-templates.md) - Référence complète des commandes
- [Template System V2](./template-system-v2.md) - Système de templates V2
