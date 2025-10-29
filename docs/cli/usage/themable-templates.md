# Themable Templates - Usage Guide

Guide utilisateur complet pour les templates thématiques avec découverte automatique des themes.

## Table des matières

- [Concepts](#concepts)
- [Quick Start](#quick-start)
- [Creating Themable Templates](#creating-themable-templates)
- [Creating Themes](#creating-themes)
- [Using Themes](#using-themes)
- [CLI Commands](#cli-commands)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Concepts

### 🎯 Qu'est-ce qu'un Themable Template ?

Un **themable template** est un template réutilisable qui peut être combiné avec différents **themes** pour générer des variations thématiques sans dupliquer le code.

**Avantage principal :** DRY (Don't Repeat Yourself)
- 1 template × N themes = N variations sans duplication

### 📐 Architecture

**Template + Theme = Variations**

```
Template (structure)   +   Theme (variations)   =   Generated Prompts
    ↓                           ↓                         ↓
{HairCut}, {Outfit}      cyberpunk_haircut.yaml    neon mohawk, cybersuit
                         cyberpunk_outfit.yaml

{HairCut}, {Outfit}   +  pirates_haircut.yaml  =  bandana, pirate coat
                         pirates_outfit.yaml
```

### 🎨 Dimensions orthogonales

1. **Theme** - Aspects visuels et thématiques (cyberpunk, rockstar, pirates, etc.)
2. **Style** - Style artistique freeform (cartoon, realistic, photorealistic, etc.)

### 💡 Exemple concret

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
│   ├── cyberpunk/
│   │   ├── theme.yaml
│   │   └── cyberpunk-*.yaml
│   ├── rockstar/
│   │   ├── theme.yaml
│   │   └── rockstar-*.yaml
│   └── pirates/
│       ├── theme.yaml
│       └── pirates-*.yaml
└── teasing.prompt.yaml                  # Prompt simple (implements template)
```

---

## Quick Start

### 1. Découvrir les themes disponibles

```bash
# Lister tous les themes disponibles pour un template
sdgen list-themes -t _tpl_teasing.template.yaml

# Lister tous les themes du système
sdgen theme list
```

### 2. Générer avec un theme

```bash
# Theme seul (style default)
sdgen generate -t _tpl_teasing.template.yaml --theme pirates

# Theme + style
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style cartoon
```

### 3. Valider compatibilité

```bash
# Voir les détails d'un theme
sdgen theme show cyberpunk

# Valider qu'un theme est compatible avec un template
sdgen theme validate _tpl_teasing.template.yaml cyberpunk
```

---

## Creating Themable Templates

### Structure d'un template themable

```yaml
# _tpl_character.template.yaml
version: "2.0"
name: "Character Portrait Template"

# 🆕 Phase 2: Theme configuration block
themes:
  enable_autodiscovery: true                 # Enable theme autodiscovery
  search_paths: [./themes/, ../shared/]     # Where to look for themes
  explicit:                                  # Manual theme declarations (optional)
    custom: ../custom/theme.yaml

# Template avec placeholders thématiques
template: |
  masterpiece, {Rendering},
  {Ambiance}, {Location},
  girl, {HairCut}, {HairColor},
  wearing {Outfit}, {Accessories}

prompts:
  default: "high quality"

# Imports par défaut (peuvent être remplacés par themes)
imports:
  # Variations communes (ne changent pas par theme)
  EyeColor: common/body/eyecolors.yaml

  # Variations thématiques (avec defaults utilisés si theme ne les fournit pas)
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

### 🔧 Configuration du bloc `themes:`

Le bloc `themes:` définit comment découvrir et charger les themes. Il existe 3 modes :

#### Mode 1 : Explicit only (défaut)

Déclarer uniquement les themes manuellement :

```yaml
themes:
  explicit:
    pirates: ./pirates/theme.yaml
    cyberpunk: ./cyberpunk/theme.yaml
```

#### Mode 2 : Autodiscovery only

Découvrir automatiquement tous les themes dans un dossier :

```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/]    # Optionnel, défaut: ['.']
```

#### Mode 3 : Hybrid (recommandé)

Combiner découverte automatique + déclarations manuelles :

```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/, ../shared/]
  explicit:
    custom: ../custom/my_theme.yaml
```

**💡 Priorité :** Les themes `explicit` ont priorité sur les themes autodiscovered.

### 📝 Placeholders thématiques vs communs

**Thématiques** (varient selon le theme) :
- `Ambiance` - Palette couleurs, mood, lighting
- `Location` - Lieux spécifiques au theme
- `HairCut` - Coupes de cheveux thématiques
- `HairColor` - Couleurs de cheveux
- `Outfit` - Vêtements thématiques
- `Accessories` - Accessoires du theme
- `TechAspect` - Éléments technologiques/fantastiques

**Communs** (universels, partagés entre themes) :
- `Poses` - Poses corporelles
- `Expression` - Expressions faciales
- `BodyType` - Types de corps
- `EyeColor` - Couleurs des yeux
- `CameraAngle` - Angles de caméra

---

## Creating Themes

### 📁 Structure d'un theme

```
themes/pirates/
├── theme.yaml                      # Theme configuration (explicit)
├── pirates-haircut.yaml            # Hair variations
├── pirates-outfit.yaml             # Default outfit style
├── pirates-outfit.cartoon.yaml     # Cartoon outfit style
├── pirates-outfit.realistic.yaml   # Realistic outfit style
└── pirates-location.yaml           # Pirate locations
```

### 📐 Convention de nommage des fichiers

**IMPORTANT** : Les fichiers de variations suivent cette convention stricte :

**Format base :** `{theme_name}-{placeholder_name}.yaml` (avec **tiret**)

**Format avec style :** `{theme_name}-{placeholder_name}.{style_name}.yaml`

**Exemples corrects :**
```
pirates-haircut.yaml                # ✅ Base placeholder
pirates-outfit.yaml                 # ✅ Default style
pirates-outfit.cartoon.yaml         # ✅ Cartoon style
pirates-outfit.realistic.yaml       # ✅ Realistic style
cyberpunk-tech-aspect.yaml          # ✅ Multi-word placeholder
```

**Exemples incorrects :**
```
pirates_haircut.yaml                # ❌ Underscore au lieu de tiret
pirateshaircut.yaml                 # ❌ Pas de séparateur
haircut-pirates.yaml                # ❌ Ordre inversé
pirates-haircut-cartoon.yaml        # ❌ Style avec tiret au lieu de point
```

### 🎨 Theme explicite (recommandé)

Créer un fichier `theme.yaml` dans le dossier du theme :

```yaml
# themes/cyberpunk/theme.yaml
type: theme_config
version: "1.0"

imports:
  # Variations thématiques de base
  Ambiance:    cyberpunk/cyberpunk-ambiance.yaml
  Location:    cyberpunk/cyberpunk-location.yaml
  HairCut:     cyberpunk/cyberpunk-haircut.yaml
  HairColor:   cyberpunk/cyberpunk-haircolor.yaml
  Outfit:      cyberpunk/cyberpunk-outfit.yaml
  Accessories: cyberpunk/cyberpunk-accessories.yaml

  # Style-sensitive variants (optional)
  Rendering.default:   cyberpunk/cyberpunk-rendering.yaml
  Rendering.cartoon:   cyberpunk/cyberpunk-rendering.cartoon.yaml
  Rendering.realistic: cyberpunk/cyberpunk-rendering.realistic.yaml
```

**💡 Avantages du theme explicite :**
- Contrôle total sur les imports
- Support des styles explicite
- Documentation claire
- Validation plus stricte

### 🤖 Theme implicite (auto-découverte)

Si `theme.yaml` n'existe pas, le système infère automatiquement les imports depuis les fichiers :

```
themes/pirates/
├── pirates-haircut.yaml
├── pirates-location.yaml
├── pirates-outfit.yaml
└── pirates-outfit.cartoon.yaml
```

→ **Auto-détection** :
```yaml
imports:
  HairCut:         pirates/pirates-haircut.yaml
  Location:        pirates/pirates-location.yaml
  Outfit:          pirates/pirates-outfit.yaml
  Outfit.cartoon:  pirates/pirates-outfit.cartoon.yaml
```

**💡 Avantages du theme implicite :**
- Moins de configuration
- Idéal pour prototypage rapide
- Convention over configuration

### ⚠️ Validation de la convention

Le système valide automatiquement les noms de fichiers :

```bash
# Lister les themes et voir leurs imports découverts
sdgen list-themes -t template.yaml
```

**Erreurs courantes détectées :**
- Fichiers avec underscore au lieu de tiret
- Format de style incorrect
- Fichiers manquants déclarés dans theme.yaml

---

## Using Themes

### 🚀 Générer avec un theme

```bash
# Theme seul (style default)
sdgen generate -t _tpl_character.template.yaml --theme cyberpunk

# Theme + style
sdgen generate -t _tpl_character.template.yaml --theme cyberpunk --style cartoon

# Sans theme (utilise les imports du template)
sdgen generate -t _tpl_character.template.yaml
```

### 🔄 Ordre de résolution des imports

**Priorité :** prompt > theme > template

| Source | Description | Exemple |
|--------|-------------|---------|
| **Prompt** | Imports explicites dans le fichier .prompt.yaml | `imports: {Ambiance: custom/my_ambiance.yaml}` |
| **Theme** | Variations fournies par le theme | `cyberpunk/cyberpunk-ambiance.yaml` |
| **Template** | Defaults déclarés dans le template | `defaults/ambiance.yaml` |

**Exemple complet :**

| Placeholder | Prompt override? | Theme fourni? | Résolution finale |
|-------------|------------------|---------------|-------------------|
| `Ambiance` | ❌ | ✅ | `themes/cyberpunk/cyberpunk-ambiance.yaml` |
| `Outfit` | ❌ | ✅ (style=cartoon) | `themes/cyberpunk/cyberpunk-outfit.cartoon.yaml` |
| `Rendering` | ✅ | ❌ | `custom/my_rendering.yaml` (prompt override) |
| `EyeColor` | ❌ | ❌ | `common/body/eyecolors.yaml` (template default) |

### 🎨 Styles freeform

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
# 1. Créer des fichiers avec le suffix du style
# Format: {theme}-{placeholder}.{style}.yaml
cyberpunk-outfit.neon-noir.yaml
cyberpunk-rendering.neon-noir.yaml

# 2. Utiliser le style
sdgen generate -t template.yaml --theme cyberpunk --style neon-noir
```

---

## CLI Commands

### `sdgen list-themes`

Liste les themes disponibles pour un template spécifique :

```bash
# Syntaxe
sdgen list-themes -t <template_path>

# Exemples
sdgen list-themes -t ./prompts/template.yaml
sdgen list-themes -t template.yaml --configs-dir /path/to/configs
```

**Output :**
```
📋 Theme Configuration
├─ Autodiscovery: ✓ Enabled
├─ Search paths:
│  ├─ • ./themes/
│  └─ • ../shared/
└─ Explicit themes: 1
   └─ • custom

🎨 pirates (autodiscovered)
├─ Path: ./themes/pirates/theme.yaml
└─ Imports: 8
   ├─ ✓ HairCut → pirates/pirates-haircut.yaml
   ├─ ✓ Outfit → pirates/pirates-outfit.yaml
   └─ ✓ Location → pirates/pirates-location.yaml

🎨 cyberpunk (explicit)
├─ Path: ../custom/cyberpunk.yaml
└─ Imports: 12
   ├─ ✓ Ambiance → cyberpunk/cyberpunk-ambiance.yaml
   ├─ ✗ TechAspect → cyberpunk/tech.yaml (missing)
   └─ ...

Summary: 2 theme(s) found
  • 1 explicit
  • 1 autodiscovered
```

### `sdgen generate` avec themes

```bash
# Syntaxe complète
sdgen generate --template <path> --theme <name> [--theme-file <path>] [--style <style>]

# Exemples
sdgen generate -t _tpl_teasing.template.yaml --theme pirates
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style cartoon
sdgen generate -t _tpl_teasing.template.yaml --theme-file ../custom/my_theme.yaml
sdgen generate -t _tpl_teasing.template.yaml --theme rockstar --style realistic -n 50
```

**Options :**
- `--theme <name>` : Nom du theme (défini dans le bloc themes:)
- `--theme-file <path>` : Chemin direct vers un theme.yaml (bypass le bloc themes:)
- `--style <style>` : Style artistique (default, cartoon, realistic, etc.)

**⚠️ Important :** `--theme` et `--theme-file` sont mutuellement exclusifs.

### `sdgen theme list`

Liste tous les themes du système :

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
  HairCut          → cyberpunk/cyberpunk-haircut.yaml
  HairColor        → cyberpunk/cyberpunk-haircolor.yaml
  TechAspect       → cyberpunk/cyberpunk-tech-aspect.yaml
  FemaleCharacter  → cyberpunk/cyberpunk-girl.yaml
  ...

Variations: 8
Styles detected: default, cartoon, realistic
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

**Output:** `YYYYMMDD_HHMMSS_Teasing_cyberpunk_default/`

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

### Example 6: Custom theme file

```bash
# Use a theme file outside the standard discovery paths
sdgen generate -t template.yaml --theme-file ~/my-themes/custom/theme.yaml
```

### Example 7: Discover themes for a template

```bash
# See all available themes before generating
sdgen list-themes -t _tpl_teasing.template.yaml

# Then generate with one of them
sdgen generate -t _tpl_teasing.template.yaml --theme pirates
```

---

## Troubleshooting

### ❌ "No 'themes:' block found"

```
❌ No 'themes:' block found in TemplateName
💡 Use --theme-file to specify theme path directly, or add a themes: block to your template
```

**Solution 1 :** Ajouter un bloc `themes:` au template :
```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/]
```

**Solution 2 :** Utiliser `--theme-file` pour bypass le bloc themes:
```bash
sdgen generate -t template.yaml --theme-file ./themes/pirates/theme.yaml
```

### ❌ "Theme not found"

```
❌ Theme 'unknown' not found
💡 Available themes: pirates, cyberpunk, rockstar
   Or use --theme-file to load a custom theme
```

**Solution :**
```bash
# Lister les themes disponibles
sdgen list-themes -t template.yaml

# Utiliser un theme existant
sdgen generate -t template.yaml --theme pirates
```

### ⚠️ "Missing import for placeholder"

```
⚠ Warning: Theme 'cyberpunk' missing Outfit.realistic, using fallback
```

**Explication :** Normal si le theme ne fournit pas tous les styles. Le système utilise automatiquement le fallback (template default ou common).

**Fix (optionnel) :** Créer le fichier manquant :
```bash
# Créer cyberpunk-outfit.realistic.yaml
cp themes/cyberpunk/cyberpunk-outfit.yaml \
   themes/cyberpunk/cyberpunk-outfit.realistic.yaml
```

### ❌ "File not found"

```
❌ Error: File not found: themes/cyberpunk/cyberpunk-outfit.yaml
```

**Solution :** Vérifier que :
1. Le fichier existe : `ls themes/cyberpunk/`
2. Le chemin dans `theme.yaml` est correct (relatif à `configs_dir`)
3. La convention de nommage est respectée (tiret, pas underscore)

### ⚠️ "Cannot use both --theme and --theme-file"

```
✗ Cannot use both --theme and --theme-file

Use --theme for themes defined in the template, or --theme-file for custom theme files
```

**Solution :** Choisir une seule option :
```bash
# Option A: Use theme name (from template's themes: block)
sdgen generate -t template.yaml --theme pirates

# Option B: Use direct theme file path
sdgen generate -t template.yaml --theme-file ./my_theme.yaml
```

---

## Best Practices

### 1. 📁 Structure des dossiers

```
configs/
├── templates/
│   └── _tpl_character.template.yaml
├── themes/
│   ├── cyberpunk/
│   │   ├── theme.yaml
│   │   ├── cyberpunk-haircut.yaml
│   │   ├── cyberpunk-outfit.yaml
│   │   └── cyberpunk-outfit.cartoon.yaml
│   ├── rockstar/
│   │   ├── theme.yaml
│   │   └── rockstar-*.yaml
│   └── pirates/
│       ├── theme.yaml
│       └── pirates-*.yaml
└── common/
    ├── body/
    ├── poses/
    └── rendering/
```

### 2. 📝 Naming conventions

**CRUCIAL** : Respecter la convention de nommage avec **tirets** :

- **Templates :** `_tpl_{name}.template.yaml`
- **Themes :** `themes/{name}/theme.yaml`
- **Variations :** `{theme}-{placeholder}.yaml` (**tiret**, pas underscore)
- **Styles :** `{basename}.{style}.yaml` (**point** pour le style)

**✅ Correct :**
```
pirates-haircut.yaml
cyberpunk-outfit.cartoon.yaml
fantasy-tech-aspect.yaml
```

**❌ Incorrect :**
```
pirates_haircut.yaml          # Underscore au lieu de tiret
piratesHaircut.yaml           # PascalCase
haircut-pirates.yaml          # Ordre inversé
pirates-haircut-cartoon.yaml  # Style avec tiret
```

### 3. 🎯 Séparation thématique vs commun

**Thématiques** (dans themes/) :
- Changent radicalement selon le theme
- Exemple : cyberpunk vs pirates hair colors

**Communs** (dans common/) :
- Universels, partagés entre themes
- Exemple : body types, facial expressions

### 4. 📖 Documentation des themes

Ajouter des commentaires dans `theme.yaml` :

```yaml
# Cyberpunk Theme
# Neon-lit dystopian future aesthetic
# Supports styles: default, cartoon, realistic
type: theme_config
version: "1.0"
imports:
  # Core variations
  Ambiance: cyberpunk/cyberpunk-ambiance.yaml
  # ...
```

### 5. ✅ Validation avant génération

```bash
# 1. Lister les themes disponibles
sdgen list-themes -t template.yaml

# 2. Valider compatibilité
sdgen theme validate template.yaml cyberpunk

# 3. Dry-run pour vérifier
sdgen generate -t template.yaml --theme cyberpunk --dry-run

# 4. Générer
sdgen generate -t template.yaml --theme cyberpunk -n 100
```

### 6. 🔄 Mode hybride recommandé

Pour les gros projets, utiliser le mode hybride :

```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/, ../shared-themes/]
  explicit:
    # Themes custom ou avec path spécial
    custom: ../custom/my_theme.yaml
    experimental: ./experimental/test_theme.yaml
```

**Avantages :**
- Autodiscovery pour themes standards
- Explicit pour themes custom/experimentaux
- Flexibilité maximale

---

## See Also

- [Technical Documentation](../technical/themable-templates.md) - Architecture interne et algorithmes
- [CLI Reference](../reference/themable-templates.md) - Référence complète des commandes
- [Template System V2](../guide/4-templates-advanced.md) - Système de templates V2
- [Variation Files](./variation-files.md) - Format des fichiers de variations
