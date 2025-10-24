# Themable Templates with Rating System

**Status:** next
**Priority:** 7
**Component:** cli
**Created:** 2025-01-20
**Updated:** 2025-10-22

## Description

Permettre de créer des **templates réutilisables** avec deux dimensions orthogonales :
1. **Theme** (cyberpunk, rockstar, pirates, etc.) - Aspects visuels et thématiques
2. **Rating** (sfw, sexy, nsfw) - Niveau de contenu adulte

**Concept :** Un template définit la structure générique. Les thèmes fournissent les variations thématiques. Le rating filtre le niveau de contenu. Le système d'imports V2 existant est réutilisé.

**Avantage :** DRY (Don't Repeat Yourself) - une seule définition de template pour N thèmes × M ratings.

---

## Use Case

### Structure actuelle (duplication massive)
```
├── _tpl_teasing.template.yaml
├── cyberpunk-teasing-sfw.prompt.yaml        # Duplique structure
├── cyberpunk-teasing-sexy.prompt.yaml       # Duplique structure
├── cyberpunk-teasing-nsfw.prompt.yaml       # Duplique structure
├── rockstar-teasing-sfw.prompt.yaml         # Duplique structure
├── rockstar-teasing-sexy.prompt.yaml        # Duplique structure
├── rockstar-teasing-nsfw.prompt.yaml        # Duplique structure
├── pirates-teasing-sfw.prompt.yaml          # Duplique structure
├── pirates-teasing-sexy.prompt.yaml         # Duplique structure
└── pirates-teasing-nsfw.prompt.yaml         # Duplique structure
```

### Structure cible (themable + ratable)
```
├── _tpl_teasing.template.yaml               # Template unique
├── themes/
│   ├── cyberpunk/
│   │   ├── theme.yaml
│   │   ├── cyberpunk_ambiance.yaml
│   │   ├── cyberpunk_locations.yaml
│   │   ├── cyberpunk_haircut.yaml
│   │   ├── cyberpunk_outfit.sfw.yaml        # Rating variants
│   │   ├── cyberpunk_outfit.sexy.yaml
│   │   └── cyberpunk_outfit.nsfw.yaml
│   ├── rockstar/
│   │   └── rockstar_*.yaml
│   └── pirates/
│       └── pirates_*.yaml
└── common/
    ├── poses/
    │   ├── poses.classic.yaml               # SFW
    │   ├── poses.solo.sexy.yaml             # Sexy
    │   └── poses.solo.nsfw.yaml             # NSFW
    └── interactions/
        ├── teasing.sfw.yaml
        ├── teasing.sexy.yaml
        └── teasing.nsfw.yaml
```

### Usage CLI
```bash
# Template + theme + rating
sdgen generate --template _tpl_teasing --theme cyberpunk --rating sexy

# Raccourcis
sdgen generate -t _tpl_teasing --theme cyberpunk -r nsfw

# Rating par défaut (sfw)
sdgen generate -t _tpl_teasing --theme cyberpunk

# Sans thème (juste rating)
sdgen generate -t _tpl_teasing --rating nsfw
```

---

## Concepts clés

### 1. Theme vs Common Variations

#### Variations **THÉMATIQUES** (spécifiques au thème)
Ces variations changent radicalement selon le thème :

1. **Ambiance** - Palette couleurs, effets visuels, lighting, mood
2. **Locations** - Lieux thématiques (cyberpunk city vs pirate ship)
3. **HairCut** - Coupes de cheveux thématiques (mohawk vs tresses)
4. **HairColor** - Couleurs de cheveux (neon vs naturel vs fantastique)
5. **SkinType** - Type de peau (cyborg vs elf vs humain vs alien)
6. **Outfit** - Vêtements thématiques (leather jacket vs pirate coat)
7. **Underwear** - Sous-vêtements thématiques
8. **Accessories** - Accessoires thématiques (implants cyber vs sabre)
9. **TechAspect** - Aspects technologiques/fantastiques spécifiques

#### Variations **COMMUNES** (partagées entre thèmes)
Ces variations sont universelles et ne dépendent pas du thème :

1. **Poses** - Poses corporelles (standing, sitting, etc.)
2. **FacialExpressions** - Expressions faciales (happy, sad, angry, etc.)
3. **Interactions** - Gestes et interactions (winking, teasing, etc.)
4. **BodyTypes** - Types de corps (slim, curvy, athletic, etc.)
5. **Anatomie** - Détails anatomiques (tits, ass, etc.)
6. **EyeColor** - Couleurs des yeux (brown, blue, green, etc.)
7. **CameraAngles** - Angles de caméra (close-up, wide shot, etc.)

**Convention :** Les variations communes sont stockées dans `common/*` et ne sont jamais overridées par les thèmes.

### 2. Rating Dimension

Le **rating** est orthogonal au thème et filtre le niveau de contenu adulte.

#### Niveaux de rating

| Rating | Description | Use case |
|--------|-------------|----------|
| `sfw` | Safe For Work | Pas de nudité, pas de contenu sexuel |
| `sexy` | Sexy/Suggestif | Contenu suggestif, tenues sexy, poses sensuelles |
| `nsfw` | Not Safe For Work | Nudité, contenu sexuel explicite |

#### Placeholders rating-sensitive

Certains placeholders varient selon le rating :
- **Outfit** - Tenues : casual → sexy → nude
- **Underwear** - Sous-vêtements : conservateur → lingerie → absent
- **Pose** - Poses : classiques → sensuelles → explicites
- **Interaction** - Interactions : neutres → teasing → sexuelles

#### Convention de nommage (Option A)

**Format :** `{basename}.{rating}.yaml`

**Exemples :**
```
outfits.sfw.yaml         # Tenues SFW
outfits.sexy.yaml        # Tenues sexy
outfits.nsfw.yaml        # Tenues NSFW

poses.classic.yaml       # Poses SFW (pas de suffixe = sfw)
poses.solo.sexy.yaml     # Poses sexy
poses.solo.nsfw.yaml     # Poses NSFW
```

**Règle :** Pas de suffixe = SFW (défaut)

---

## Implementation

### 1. Template Principal

```yaml
# _tpl_teasing.template.yaml
version: '2.0'
name: 'Teasing Portrait Template'

themable: true   # 🆕 Template supporte les thèmes
ratable: true    # 🆕 Template supporte les ratings

implements: 'base-hassaku.template.yaml'

# 🆕 Déclaration des placeholders rating-sensitive
rating_sensitive_placeholders:
  - Outfit
  - Underwear
  - Pose
  - Interaction

imports:
  # THÉMATIQUES (overridables par thème)
  Ambiance:    defaults/ambiance.yaml
  Locations:   defaults/locations.yaml
  HairCut:     defaults/haircut.yaml
  HairColor:   defaults/haircolor.yaml
  SkinType:    defaults/skintypes.yaml
  Accessories: defaults/accessories.yaml

  # RATABLES (common, varient selon rating)
  Outfit:      common/outfits/outfits.sfw.yaml      # Default SFW
  Underwear:   common/underwear/underwear.sfw.yaml  # Default SFW
  Pose:        common/poses/poses.classic.yaml      # Default SFW
  Interaction: common/interactions/teasing.sfw.yaml # Default SFW

  # COMMUNS (non-overridables, non-ratables)
  Expression:  common/expressions/neutral.yaml
  BodyType:    common/body/bodytypes.yaml
  EyeColor:    common/body/eyecolors.realist.yaml

prompt: |
  {Ambiance}, {Locations},
  {SkinType} girl, {HairCut}, {HairColor}, {EyeColor},
  {BodyType}, {Expression},
  wearing {Outfit}, {Underwear}, {Accessories},
  {Pose}, {Interaction}

negative_prompt: "worst quality, low quality, text, watermark"

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 100

parameters:
  adetailer:
    - ../adetailer/faces/face_user_preferred.adetailer.yaml
    - ../adetailer/hands/hand_user_preferred.adetailer.yaml
```

### 2. Thème Explicite

```yaml
# themes/cyberpunk/theme.yaml
type: theme_config
version: "1.0"

imports:
  # THÉMATIQUES (override template)
  Ambiance:  cyberpunk/cyberpunk_ambiance.yaml
  Locations: cyberpunk/cyberpunk_locations.yaml
  HairCut:   cyberpunk/cyberpunk_haircut.yaml
  HairColor: cyberpunk/cyberpunk_haircolor.yaml
  SkinType:  cyberpunk/cyberpunk_skin.yaml      # Cyborg, augmented, etc.

  # RATABLES (override avec variants)
  Outfit.sfw:   cyberpunk/cyberpunk_outfit.sfw.yaml
  Outfit.sexy:  cyberpunk/cyberpunk_outfit.sexy.yaml
  Outfit.nsfw:  cyberpunk/cyberpunk_outfit.nsfw.yaml

  Underwear.sexy: cyberpunk/cyberpunk_underwear.sexy.yaml
  # Pas de Underwear.nsfw → fallback common

  # Accessories → pas défini → fallback template
  # Pose, Interaction → communs, pas overridés
```

### 3. Thème Implicite (inférence automatique)

Si `theme.yaml` n'existe pas, le système infère les imports depuis les fichiers `{theme}_*.yaml`.

**Exemple :**
```
themes/rockstar/
├── rockstar_ambiance.yaml
├── rockstar_locations.yaml
├── rockstar_haircut.yaml
├── rockstar_outfit.sfw.yaml
└── rockstar_outfit.sexy.yaml
```

**Inférence automatique :**
```yaml
imports:
  Ambiance:     rockstar/rockstar_ambiance.yaml
  Locations:    rockstar/rockstar_locations.yaml
  HairCut:      rockstar/rockstar_haircut.yaml
  Outfit.sfw:   rockstar/rockstar_outfit.sfw.yaml
  Outfit.sexy:  rockstar/rockstar_outfit.sexy.yaml
```

### 4. Résolution des Imports (Theme + Rating)

**Ordre de priorité :**
1. **Theme override** (selon rating si applicable)
2. **Template import** (selon rating si applicable)
3. **Common fallback** (selon rating si applicable)

**Algorithme :**

```python
def resolve_imports(template, theme, rating):
    resolved = {}

    for placeholder in template.imports:
        # 1. Check if placeholder is rating-sensitive
        is_rating_sensitive = placeholder in template.rating_sensitive_placeholders

        # 2. Build import key with rating if applicable
        if is_rating_sensitive:
            import_key = f"{placeholder}.{rating}"
        else:
            import_key = placeholder

        # 3. Try theme override first
        if theme and import_key in theme.imports:
            resolved[placeholder] = theme.imports[import_key]

        # 4. Fallback to template import
        elif import_key in template.imports:
            resolved[placeholder] = template.imports[import_key]

        # 5. Try to auto-resolve rating by replacing suffix
        elif is_rating_sensitive and placeholder in template.imports:
            base_import = template.imports[placeholder]
            resolved[placeholder] = replace_rating_suffix(base_import, rating)

        # 6. No import found → error or warning
        else:
            warn(f"No import found for {placeholder} (rating={rating})")

    return resolved
```

**Exemple concret :**

**CLI :** `sdgen generate -t _tpl_teasing --theme cyberpunk --rating sexy`

**Résolution :**

| Placeholder | Source | File | Raison |
|-------------|--------|------|--------|
| `Ambiance` | theme | `cyberpunk/cyberpunk_ambiance.yaml` | Theme override, pas de rating |
| `Locations` | theme | `cyberpunk/cyberpunk_locations.yaml` | Theme override |
| `HairCut` | theme | `cyberpunk/cyberpunk_haircut.yaml` | Theme override |
| `Outfit` | theme | `cyberpunk/cyberpunk_outfit.sexy.yaml` | Theme override, rating=sexy |
| `Underwear` | common | `common/underwear/underwear.sexy.yaml` | Theme ne fournit pas sexy → fallback common |
| `Pose` | common | `common/poses/poses.solo.sexy.yaml` | Commun, auto-résolu avec rating=sexy |
| `Interaction` | common | `common/interactions/teasing.sexy.yaml` | Commun, auto-résolu |
| `Expression` | common | `common/expressions/neutral.yaml` | Commun, pas de rating |
| `Accessories` | template | `defaults/accessories.yaml` | Theme ne fournit pas → fallback template |

---

## Data Models

### TemplateConfig (enrichi)

```python
@dataclass
class TemplateConfig:
    version: str
    name: str
    template: str
    source_file: Path
    themable: bool = False                # 🆕 Supporte les thèmes
    ratable: bool = False                 # 🆕 Supporte les ratings
    rating_sensitive_placeholders: List[str] = field(default_factory=list)  # 🆕
    implements: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    imports: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: str = ''
    output: Optional[OutputConfig] = None
```

### ThemeConfig (nouveau)

```python
@dataclass
class ThemeConfig:
    """Configuration for a theme."""
    name: str                            # Theme name (e.g., "cyberpunk")
    path: Path                           # Path to theme directory
    explicit: bool                       # True if theme.yaml exists
    imports: Dict[str, str]              # Import mappings (may include rating suffixes)
    variations: List[str]                # Available variation categories
```

### ResolvedContext (enrichi)

```python
@dataclass
class ImportResolution:
    """Metadata about how an import was resolved."""
    source: str                          # "theme" | "template" | "common"
    file: str                            # Path to resolved file
    type: str                            # "thematic" | "common"
    override: bool                       # True if theme overrode template
    rating_sensitive: bool = False       # 🆕 True if varies by rating
    resolved_rating: Optional[str] = None  # 🆕 Rating used for resolution
    note: Optional[str] = None           # Optional warning/info


@dataclass
class ResolvedContext:
    imports: Dict[str, Dict[str, str]]   # {import_name: {key: value}}
    chunks: Dict[str, ChunkConfig]       # {chunk_name: ChunkConfig}
    parameters: Dict[str, Any]
    variation_state: Dict[str, str] = field(default_factory=dict)
    import_resolution: Dict[str, ImportResolution] = field(default_factory=dict)  # 🆕
    rating: str = "sfw"                  # 🆕 Active rating
```

---

## Manifest Structure

### Manifest enrichi (theme + rating)

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-22T10:30:00",

    "theme": {
      "name": "cyberpunk",
      "path": "./themes/cyberpunk/",
      "explicit": true
    },

    "rating": "sexy",

    "runtime_info": {
      "sd_model_checkpoint": "model.safetensors"
    },

    "resolved_template": {
      "prompt": "...",
      "negative": "..."
    },

    "import_resolution": {
      "Ambiance": {
        "source": "theme",
        "file": "./cyberpunk/cyberpunk_ambiance.yaml",
        "type": "thematic",
        "override": true,
        "rating_sensitive": false
      },
      "Outfit": {
        "source": "theme",
        "file": "./cyberpunk/cyberpunk_outfit.sexy.yaml",
        "type": "thematic",
        "override": true,
        "rating_sensitive": true,
        "resolved_rating": "sexy"
      },
      "Pose": {
        "source": "common",
        "file": "common/poses/poses.solo.sexy.yaml",
        "type": "common",
        "override": false,
        "rating_sensitive": true,
        "resolved_rating": "sexy"
      },
      "Expression": {
        "source": "common",
        "file": "common/expressions/neutral.yaml",
        "type": "common",
        "override": false,
        "rating_sensitive": false
      }
    },

    "generation_params": {...},
    "api_params": {...},
    "variations": {...}
  },

  "images": [...]
}
```

---

## CLI Commands

### Generate with theme and rating

```bash
# Full syntax
sdgen generate --template _tpl_teasing --theme cyberpunk --rating sexy

# Short syntax
sdgen generate -t _tpl_teasing --theme cyberpunk -r sexy

# Default rating (sfw)
sdgen generate -t _tpl_teasing --theme cyberpunk

# No theme (just rating)
sdgen generate -t _tpl_teasing --rating nsfw

# Interactive mode (selects template + theme + rating)
sdgen generate
```

### List themes

```bash
# List all available themes
sdgen list-themes

# Output:
Available Themes (3 found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Theme         Type       Variations
───────────────────────────────────────────
cyberpunk     explicit   ambiance, locations, haircut, outfit (3 ratings)
rockstar      explicit   ambiance, locations, outfit (2 ratings)
pirates       implicit   ambiance, locations, haircut
```

### Validate theme compatibility

```bash
# Check if theme is compatible with template
sdgen validate-theme --template _tpl_teasing --theme cyberpunk

# Output:
✓ Theme 'cyberpunk' is compatible with template '_tpl_teasing'

Theme provides:
  ✓ Ambiance       (cyberpunk/cyberpunk_ambiance.yaml)
  ✓ Locations      (cyberpunk/cyberpunk_locations.yaml)
  ✓ HairCut        (cyberpunk/cyberpunk_haircut.yaml)
  ✓ Outfit (sfw)   (cyberpunk/cyberpunk_outfit.sfw.yaml)
  ✓ Outfit (sexy)  (cyberpunk/cyberpunk_outfit.sexy.yaml)
  ✓ Outfit (nsfw)  (cyberpunk/cyberpunk_outfit.nsfw.yaml)
  ⚠ Accessories    (missing, will use template fallback)
  ⚠ Underwear (nsfw) (missing, will use common fallback)

Common variations (not overridden by theme):
  - Pose
  - Interaction
  - Expression
  - BodyType
  - EyeColor
```

### Show resolution

```bash
# Display import resolution from manifest
sdgen show-resolution --manifest session_001/manifest.json

# Output:
Import Resolution for 'Hassaku_PortraitTeasing_cyberpunk_sexy'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Placeholder  Source   Type       Rating  Override  File
────────────────────────────────────────────────────────────────
Ambiance     theme    thematic   -       ✓         cyberpunk/ambiance.yaml
Locations    theme    thematic   -       ✓         cyberpunk/locations.yaml
Outfit       theme    thematic   sexy    ✓         cyberpunk/outfit.sexy.yaml
Underwear    common   common     sexy    ✗         common/underwear.sexy.yaml
Pose         common   common     sexy    ✗         common/poses.sexy.yaml
Expression   common   common     -       ✗         common/expressions.yaml

Theme: cyberpunk (explicit)
Rating: sexy
Theme overrides: 3/8 placeholders
```

---

## Tasks

### Phase 1: Core Infrastructure

- [ ] **Data Models**
  - [ ] Add `themable`, `ratable`, `rating_sensitive_placeholders` to `TemplateConfig`
  - [ ] Create `ThemeConfig` model
  - [ ] Extend `ResolvedContext` with `rating`, `import_resolution`
  - [ ] Create `ImportResolution` model

- [ ] **Theme Discovery**
  - [ ] `ThemeLoader.discover_themes(configs_dir)` → List[ThemeConfig]
  - [ ] `ThemeLoader.load_theme(theme_path)` → ThemeConfig
  - [ ] Infer imports from `{theme}_*.yaml` files (implicit themes)
  - [ ] Parse `theme.yaml` for explicit themes

- [ ] **Rating Resolution**
  - [ ] `RatingResolver.resolve_with_rating(imports, rating, sensitive_placeholders)`
  - [ ] Rating suffix replacement logic (`.sfw.yaml` → `.sexy.yaml`)
  - [ ] Fallback chain (theme → template → common)

- [ ] **Theme Resolution**
  - [ ] `ThemeResolver.merge_imports(template, theme, rating)`
  - [ ] Build `import_resolution` map for manifest
  - [ ] Validation and warnings (missing files, etc.)

### Phase 2: Pipeline Integration

- [ ] **V2Pipeline**
  - [ ] Add `rating` parameter to `resolve()` method
  - [ ] Integrate `ThemeResolver` and `RatingResolver`
  - [ ] Build `import_resolution` metadata

- [ ] **CLI Commands**
  - [ ] Add `--theme` option to `generate` command
  - [ ] Add `--rating` option to `generate` command
  - [ ] Interactive mode with theme + rating selection
  - [ ] `sdgen list-themes` command
  - [ ] `sdgen validate-theme` command
  - [ ] `sdgen show-resolution` command

- [ ] **Manifest Generation**
  - [ ] Add `theme` field to snapshot
  - [ ] Add `rating` field to snapshot
  - [ ] Add `import_resolution` field to snapshot
  - [ ] Serialize `ImportResolution` objects

### Phase 3: Testing

- [ ] **Unit Tests**
  - [ ] `test_theme_loader.py` (discovery, explicit, implicit)
  - [ ] `test_rating_resolver.py` (suffix replacement, fallbacks)
  - [ ] `test_theme_resolver.py` (merge strategy, priorities)

- [ ] **Integration Tests**
  - [ ] Template + theme resolution
  - [ ] Template + theme + rating resolution
  - [ ] Fallback scenarios (missing files)
  - [ ] Manifest generation with theme + rating

### Phase 4: Documentation

- [ ] **Usage Guide** (`docs/cli/usage/themable-templates.md`)
  - [ ] Creating themable templates
  - [ ] Creating themes (explicit vs implicit)
  - [ ] Using ratings
  - [ ] Examples (cyberpunk, rockstar, pirates)

- [ ] **Technical Doc** (`docs/cli/technical/themable-templates.md`)
  - [ ] Architecture (loaders, resolvers)
  - [ ] Resolution algorithm
  - [ ] Manifest structure

- [ ] **Reference** (`docs/cli/reference/themable-templates.md`)
  - [ ] CLI commands reference
  - [ ] File formats (theme.yaml)
  - [ ] Naming conventions

---

## Success Criteria

- ✅ Un template themable peut être utilisé avec N thèmes × M ratings
- ✅ Découverte automatique des thèmes dans `configs_dir/`
- ✅ Résolution correcte : theme override → template → common fallback
- ✅ Ratings résolus automatiquement (suffix replacement)
- ✅ Manifest contient tracabilité complète (theme + rating + resolution)
- ✅ CLI `sdgen generate --template X --theme Y --rating Z` fonctionne
- ✅ CLI `sdgen list-themes` affiche thèmes disponibles
- ✅ CLI `sdgen validate-theme` vérifie compatibilité
- ✅ Warnings affichés si variations manquantes (non-bloquant)
- ✅ Compatible avec toutes les features V2 (imports, chunks, inheritance)

---

## Examples

### Example 1: Cyberpunk Sexy Portrait

**Command:**
```bash
sdgen generate -t _tpl_teasing --theme cyberpunk --rating sexy -n 50
```

**Resolution:**
- Theme: cyberpunk
- Rating: sexy
- Output: `YYYYMMDD_HHMMSS_Hassaku_PortraitTeasing_cyberpunk_sexy/`

**Variations used:**
- `Ambiance` → cyberpunk neon lighting
- `Outfit` → cyberpunk sexy outfits (leather, mesh, etc.)
- `Pose` → sexy poses (common)
- `Interaction` → sexy teasing gestures (common)

### Example 2: Rockstar NSFW with Fallback

**Command:**
```bash
sdgen generate -t _tpl_teasing --theme rockstar --rating nsfw -n 100
```

**Resolution:**
- Theme: rockstar
- Rating: nsfw
- Theme ne fournit pas `Outfit.nsfw` → fallback `common/outfits/outfits.nsfw.yaml`

**Warnings:**
```
⚠ Warning: Theme 'rockstar' does not provide Outfit.nsfw, using common fallback
```

### Example 3: No Theme, Just Rating

**Command:**
```bash
sdgen generate -t _tpl_teasing --rating nsfw
```

**Resolution:**
- Pas de theme → tous les imports du template
- Rating nsfw → résolution automatique des suffixes

### Example 4: Multi-Theme Batch

**Script:**
```bash
for theme in cyberpunk rockstar pirates; do
  for rating in sfw sexy nsfw; do
    sdgen generate -t _tpl_teasing --theme $theme --rating $rating -n 20
  done
done
```

**Output:** 9 sessions (3 thèmes × 3 ratings × 20 images = 180 images total)

---

## Edge Cases

### Missing theme file
**Scenario:** `cyberpunk/cyberpunk_outfit.nsfw.yaml` n'existe pas

**Behavior:** Warning + fallback `common/outfits/outfits.nsfw.yaml`

```
⚠ Warning: Theme 'cyberpunk' missing Outfit.nsfw, using common fallback
```

### Missing common fallback
**Scenario:** `common/poses/poses.solo.nsfw.yaml` n'existe pas

**Behavior:** Error (bloquant)

```
❌ Error: No import found for Pose with rating=nsfw
   Tried:
   - Theme: rockstar/rockstar_pose.nsfw.yaml (not found)
   - Template: defaults/pose.yaml (not rating-compatible)
   - Common: common/poses/poses.solo.nsfw.yaml (not found)
```

### Non-rating-sensitive override
**Scenario:** Theme override un placeholder non-rating-sensitive

**Behavior:** Fonctionne normalement (theme override prioritaire)

### Invalid rating
**Scenario:** `--rating invalid`

**Behavior:** Error immédiat

```
❌ Error: Invalid rating 'invalid'
   Valid ratings: sfw, sexy, nsfw
```

---

## Future Enhancements

- **Multi-themes**: `--themes cyberpunk,rockstar` (générer plusieurs thèmes en une commande)
- **Theme inheritance**: `theme.yaml` avec `extends: base_theme`
- **Theme marketplace**: Partager/télécharger des thèmes
- **Theme validation**: `sdgen validate-theme --strict` (vérifier complétude)
- **Custom ratings**: Permettre ratings personnalisés (e.g., `r15`, `r18`)
- **Rating auto-detection**: Analyser le contenu des variations pour suggérer le rating
- **Theme mixing**: Combiner plusieurs thèmes (e.g., `--theme cyberpunk:0.7,rockstar:0.3`)
