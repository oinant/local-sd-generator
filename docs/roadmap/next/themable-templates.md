# Themable Templates

**Status:** next
**Priority:** 7
**Component:** cli
**Created:** 2025-01-20

## Description

Permettre de créer des **templates réutilables** avec différents **thèmes** (cyberpunk, rockstar, pirates, etc.) sans dupliquer la structure pour chaque thème.

**Concept :** Un template définit la structure générique, les thèmes fournissent les variations spécifiques. Le système d'imports V2 existant est réutilisé pour résoudre les variations themables.

**Avantage :** DRY (Don't Repeat Yourself) - une seule définition de template pour N thèmes.

## Use Case

```
Structure actuelle (duplication):
├── _tpl_teasing.template.yaml
├── cyberpunk-teasing.prompt.yaml       # Duplique structure
├── rockstar-teasing.prompt.yaml        # Duplique structure
├── pirates-teasing.prompt.yaml         # Duplique structure
└── ...

Structure cible (themable):
├── _tpl_teasing.template.yaml          # Template unique
├── cyberpunk/
│   ├── theme.yaml (optionnel)
│   ├── cyberpunk_girl.yaml
│   ├── cyberpunk_location.yaml
│   └── ...
├── rockstar/
│   └── rockstar_*.yaml
└── ...

Usage:
$ sdgen generate --template _tpl_teasing --theme cyberpunk
```

## Implementation

### 1. Template Principal

```yaml
# _tpl_teasing.template.yaml
template: "teasing"
themable: true  # Flag pour CLI (optionnel, inféré si --theme utilisé)

# Imports par défaut (fallbacks)
imports:
  default_girl.yaml:
    - Girl
  default_location.yaml:
    - Location
  accessories.yaml:
    - Accessories
  teasing-gestures.yaml:
    - TeasingGesture

prompt: "beautiful {Girl} in {Location}, wearing {Accessories}, {TeasingGesture}"

generation:
  mode: random
  max_images: 50
```

### 2. Thème Explicite (optionnel)

```yaml
# cyberpunk/theme.yaml
imports:
  cyberpunk_girl.yaml:
    - Girl
  cyberpunk_location.yaml:
    - Location
  cyberpunk_accessories.yaml:
    - Accessories
  # TeasingGesture non défini → fallback sur template
```

### 3. Thème Implicite (inférence automatique)

Si `theme.yaml` n'existe pas dans le dossier du thème :
- Scanner tous les fichiers `{theme}_*.yaml`
- Mapper automatiquement les placeholders :
  ```
  cyberpunk_girl.yaml → Girl
  cyberpunk_location.yaml → Location
  ```
- Fallback sur imports du template pour les placeholders manquants

### 4. Résolution des Imports (Theme Override)

**Merge Strategy :**
1. Charger imports du **template** (baseline)
2. Charger imports du **thème** (explicite ou inféré)
3. **Theme wins** : Les imports du thème overrident ceux du template
4. **Fallback** : Les placeholders non définis dans le thème utilisent les imports du template

**Exemple :**
```
Template imports:
  Girl → default_girl.yaml
  Location → default_location.yaml
  Accessories → accessories.yaml

Theme imports (cyberpunk):
  Girl → cyberpunk_girl.yaml
  Location → cyberpunk_location.yaml

Merged imports:
  Girl → cyberpunk_girl.yaml       (override)
  Location → cyberpunk_location.yaml (override)
  Accessories → accessories.yaml    (fallback)
```

### 5. Découverte Automatique des Thèmes

**Scanner le `configs_dir/` :**
- Lister tous les sous-dossiers
- Pour chaque dossier, vérifier :
  - Présence de `theme.yaml` (thème explicite)
  - OU présence de fichiers `{theme}_*.yaml` (thème implicite)
- Extraire le nom du thème :
  - Nom du dossier (ex: `cyberpunk/` → thème "cyberpunk")

**Output :**
```python
{
  "cyberpunk": {
    "path": "./cyberpunk/",
    "explicit": True,  # theme.yaml existe
    "variations": ["girl", "location", "accessories"]
  },
  "rockstar": {
    "path": "./rockstar/",
    "explicit": False,  # Inféré
    "variations": ["girl", "boy", "location", "outfit"]
  }
}
```

### 6. Validation

**Warnings (non-bloquants) :**
- Placeholder utilisé dans template mais non défini dans thème ET template
- Fichier de variation manquant

**Comportement :**
- Afficher warning
- Continuer avec placeholder vide ou valeur par défaut

## Tasks

- [ ] Design data models
  - [ ] `ThemeConfig` (path, explicit, variations)
  - [ ] Ajouter `themable: bool` dans `TemplateConfig`
- [ ] Implement theme discovery
  - [ ] `ThemeLoader.discover_themes(configs_dir)` → dict
  - [ ] `ThemeLoader.load_theme(theme_path)` → ThemeConfig
  - [ ] Inférence automatique si pas de `theme.yaml`
- [ ] Implement theme resolution
  - [ ] `ThemeResolver.resolve_imports(template, theme)` → merged imports
  - [ ] Merge strategy (theme wins, fallback template)
  - [ ] Validation + warnings
- [ ] CLI integration
  - [ ] Ajouter option `--theme` à `generate` command
  - [ ] `sdgen list --themable` (liste templates + thèmes disponibles)
  - [ ] Mode interactif : sélection template + thème
- [ ] Pipeline V2 integration
  - [ ] Inject merged imports dans `V2Pipeline.orchestrate()`
  - [ ] S'assurer compatibilité avec imports/chunks/inheritance existants
- [ ] Tests
  - [ ] Tests unitaires `ThemeLoader`
  - [ ] Tests unitaires `ThemeResolver`
  - [ ] Tests d'intégration template + thème
  - [ ] Tests fallback (variation manquante)
  - [ ] Tests inférence automatique
- [ ] Documentation
  - [ ] Usage guide (`docs/cli/usage/themable-templates.md`)
  - [ ] Technical architecture (`docs/cli/technical/themable-templates.md`)
  - [ ] Examples (cyberpunk, rockstar, pirates)

## Success Criteria

- ✅ Un template themable peut être utilisé avec N thèmes différents
- ✅ Découverte automatique des thèmes dans `configs_dir/`
- ✅ Merge strategy (theme override + fallback) fonctionne
- ✅ Warnings affichés si variations manquantes, mais génération continue
- ✅ CLI `sdgen generate --template _tpl_teasing --theme cyberpunk` fonctionne
- ✅ CLI `sdgen list --themable` affiche templates + thèmes disponibles
- ✅ Mode interactif permet de sélectionner template + thème
- ✅ Compatible avec toutes les features V2 (imports, chunks, inheritance)

## Tests

### Tests unitaires
- `test_theme_loader.py`
  - Test découverte thèmes explicites (avec `theme.yaml`)
  - Test découverte thèmes implicites (inférence `{theme}_*.yaml`)
  - Test parsing `theme.yaml`
  - Test validation dossier thème
- `test_theme_resolver.py`
  - Test merge imports (theme override)
  - Test fallback (placeholder manquant dans thème)
  - Test warnings (variation manquante)
  - Test résolution avec chunks themables

### Tests d'intégration
- `test_themable_templates_integration.py`
  - Test génération complète template + thème
  - Test mode combinatorial avec thème
  - Test mode random avec thème
  - Test avec chunks themables
  - Test fallback sur imports template
  - Test multi-thèmes (générer plusieurs thèmes successivement)

## Architecture

### Nouveaux modules

```
sd_generator_cli/templating/
├── loaders/
│   └── theme_loader.py          # Découverte et chargement thèmes
├── resolvers/
│   └── theme_resolver.py        # Résolution theme + merge imports
└── models/
    ├── template_config.py       # Ajouter themable: bool
    └── theme_config.py          # NEW: ThemeConfig model
```

### Data Models

```python
# models/theme_config.py
@dataclass
class ThemeConfig:
    name: str
    path: str
    explicit: bool  # True si theme.yaml existe
    imports: Dict[str, List[str]]  # Merged imports
    variations: List[str]  # Liste des variations disponibles
```

### API publique

```python
# loaders/theme_loader.py
class ThemeLoader:
    @staticmethod
    def discover_themes(configs_dir: str) -> Dict[str, ThemeConfig]:
        """Découvre tous les thèmes dans configs_dir."""
        pass

    @staticmethod
    def load_theme(theme_path: str, theme_name: str) -> ThemeConfig:
        """Charge un thème (explicite ou inféré)."""
        pass

    @staticmethod
    def infer_theme_imports(theme_path: str, theme_name: str) -> Dict[str, List[str]]:
        """Infère les imports depuis {theme}_*.yaml."""
        pass

# resolvers/theme_resolver.py
class ThemeResolver:
    @staticmethod
    def resolve_imports(
        template: TemplateConfig,
        theme: ThemeConfig
    ) -> Dict[str, List[str]]:
        """Merge imports (theme wins, fallback template)."""
        pass

    @staticmethod
    def validate_theme(
        template: TemplateConfig,
        theme: ThemeConfig
    ) -> List[str]:
        """Valide thème vs template, retourne warnings."""
        pass
```

### CLI Flow

```
1. User: sdgen generate --template _tpl_teasing --theme cyberpunk

2. CLI:
   - Load template: _tpl_teasing.template.yaml
   - Discover themes: ThemeLoader.discover_themes()
   - Load theme: ThemeLoader.load_theme("cyberpunk")
   - Resolve imports: ThemeResolver.resolve_imports(template, theme)
   - Validate: ThemeResolver.validate_theme() → warnings

3. Pipeline V2:
   - Inject merged imports dans orchestrator
   - Continue processing normal (chunks, inheritance, generation)

4. Output:
   - Session cyberpunk-teasing-{timestamp}/
   - Images générées avec variations du thème
```

## Edge Cases

### Placeholder dans prompt mais aucun import (template ET thème)
**Behavior:** Warning + placeholder vide
```
⚠️ Warning: Placeholder {Girl} used in prompt but no import found in template or theme 'cyberpunk'
```

### Fichier de variation manquant
**Behavior:** Warning + skip variation
```
⚠️ Warning: Variation file cyberpunk_girl.yaml not found, skipping
```

### Thème sans aucune variation
**Behavior:** Erreur bloquante
```
❌ Error: Theme 'empty_theme' has no variations (no theme.yaml and no {theme}_*.yaml files)
```

### Placeholder défini dans thème mais pas utilisé dans template
**Behavior:** Ignoré silencieusement (pas de warning)

### Conflits de noms (chunk vs import themable)
**Behavior:** Import wins (chunks résolus après imports)

## Examples

### Exemple 1 : Teasing Simple

**Template:**
```yaml
# _tpl_teasing.template.yaml
template: "teasing"
themable: true

imports:
  default_girl.yaml: [Girl]
  default_location.yaml: [Location]

prompt: "{Girl} in {Location}, teasing pose"
```

**Thème Cyberpunk (explicite):**
```yaml
# cyberpunk/theme.yaml
imports:
  cyberpunk_girl.yaml: [Girl]
  cyberpunk_location.yaml: [Location]
```

**Usage:**
```bash
sdgen generate --template _tpl_teasing --theme cyberpunk
```

### Exemple 2 : Customisation par Override

**Template:**
```yaml
# _tpl_advanced.template.yaml
imports:
  default_girl.yaml: [Girl]
  default_accessories.yaml: [Accessories]
  default_lighting.yaml: [Lighting]

prompt: "{Girl}, wearing {Accessories}, {Lighting}"
```

**Thème Rockstar (inféré + fallback):**
```
rockstar/
├── rockstar_girl.yaml         # Override Girl
├── rockstar_accessories.yaml  # Override Accessories
# Pas de rockstar_lighting.yaml → fallback sur default_lighting.yaml
```

**Résultat merged:**
- Girl → rockstar_girl.yaml
- Accessories → rockstar_accessories.yaml
- Lighting → default_lighting.yaml (fallback)

### Exemple 3 : Multi-thèmes

```bash
# Générer plusieurs thèmes successivement
for theme in cyberpunk rockstar pirates; do
  sdgen generate --template _tpl_teasing --theme $theme -n 20
done
```

## Documentation

### Usage Guide
`docs/cli/usage/themable-templates.md`
- Introduction et motivation
- Créer un template themable
- Créer un thème (explicite vs inféré)
- Exemples pratiques
- Troubleshooting

### Technical Documentation
`docs/cli/technical/themable-templates.md`
- Architecture (ThemeLoader, ThemeResolver)
- Merge strategy détaillée
- Pipeline V2 integration
- Edge cases handling

## Future Enhancements

- **Multi-themes** : `--themes cyberpunk,rockstar` (générer plusieurs thèmes en une commande)
- **Theme inheritance** : `theme.yaml` avec `extends: base_theme`
- **Theme marketplace** : Partager/télécharger des thèmes
- **Theme validation** : `sdgen validate-theme cyberpunk` (check complétude)
- **Theme snippets** : Chunks réutilisables cross-thèmes
