# CLI Architecture - Template System V2.0

**Version:** 2.0 (stable)
**Last Updated:** 2025-10-14
**Status:** ✅ Production

---

## Vue d'ensemble

Le système de templating V2.0 est construit sur une architecture modulaire et extensible avec une séparation claire des responsabilités. L'ensemble du système suit les principes SOLID et est entièrement testé (306 tests, 98% de réussite).

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Entry                            │
│                    (src/cli.py - Typer)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    V2Pipeline Orchestrator                   │
│                  (templating/orchestrator.py)                │
│                                                               │
│  Coordinate: Load → Validate → Resolve → Generate → Execute │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────┐     ┌──────────┐    ┌──────────┐
    │ Loaders│     │Validators│    │Resolvers │
    └────────┘     └──────────┘    └──────────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
                  ┌──────────────┐
                  │  Generators  │
                  └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ API Executor │
                  └──────────────┘
```

---

## Structure des modules

### CLI/src/templating/

Module principal du système de templating avec 7 sous-modules :

```
templating/
├── models/              # Data structures (TemplateConfig, ResolvedVariation)
│   ├── template_config.py
│   ├── resolved_variation.py
│   └── variation_data.py
│
├── loaders/             # YAML parsing and file loading
│   ├── yaml_loader.py           # Load and parse YAML files
│   ├── variation_loader.py      # Load variation files
│   └── import_loader.py         # Handle imports (files + inline)
│
├── validators/          # Template validation
│   ├── schema_validator.py      # YAML schema compliance
│   ├── reference_validator.py   # File existence and refs
│   ├── inheritance_validator.py # Circular dependency detection
│   └── placeholder_validator.py # Placeholder consistency
│
├── resolvers/           # Template resolution
│   ├── inheritance_resolver.py  # implements: multi-level resolution
│   ├── import_resolver.py       # imports: merging and dedup
│   ├── chunk_resolver.py        # chunks: substitution
│   └── placeholder_resolver.py  # Final prompt generation
│
├── generators/          # Variation generation strategies
│   ├── combinatorial_generator.py  # All combinations
│   ├── random_generator.py         # Random sampling
│   └── seed_manager.py             # Seed modes (fixed/progressive/random)
│
├── normalizers/         # Prompt normalization
│   └── prompt_normalizer.py     # Whitespace, line breaks, cleanup
│
├── utils/               # Utilities
│   ├── hash_utils.py            # Template hashing for caching
│   └── path_utils.py            # Path resolution (base_path)
│
└── orchestrator.py      # V2Pipeline - Main entry point
```

---

## V2Pipeline - Orchestrateur principal

**Fichier:** `templating/orchestrator.py`

### Responsabilités

Le V2Pipeline coordonne l'ensemble du processus de génération en 5 phases :

```python
class V2Pipeline:
    def execute(self, template_path: Path) -> List[ResolvedVariation]:
        # Phase 1: Load
        config = self._load_template(template_path)

        # Phase 2: Validate
        self._validate_template(config)

        # Phase 3: Resolve
        resolved_config = self._resolve_template(config)

        # Phase 4: Generate
        variations = self._generate_variations(resolved_config)

        # Phase 5: Normalize
        return self._normalize_prompts(variations)
```

### Phase 1 : Load (Chargement)

**Modules impliqués:** `loaders/`

1. **yaml_loader.py** - Parse le fichier `.prompt.yaml` principal
2. **import_loader.py** - Charge les imports (fichiers YAML ou strings inline)
3. **variation_loader.py** - Charge les fichiers de variations référencés

**Résultat:** Objet `TemplateConfig` avec toutes les données brutes.

### Phase 2 : Validate (Validation)

**Modules impliqués:** `validators/`

Validation en 4 étapes :

1. **schema_validator.py** - Vérifie la conformité du schéma YAML
   - Champs obligatoires présents (version, template/prompt)
   - Types corrects (strings, dicts, lists)
   - Valeurs valides (modes, seed_mode, etc.)

2. **reference_validator.py** - Vérifie les références de fichiers
   - Fichiers `implements:` existent
   - Fichiers `imports:` existent
   - Fichiers `chunks:` existent

3. **inheritance_validator.py** - Détecte les dépendances circulaires
   - A implements B, B implements A → ❌ Erreur
   - Construit le graphe de dépendances

4. **placeholder_validator.py** - Vérifie la cohérence des placeholders
   - Tous les `{Placeholder}` dans le template ont un import correspondant
   - Tous les imports sont utilisés (warning si non-utilisé)

**Résultat:** Template validé ou erreurs détaillées.

### Phase 3 : Resolve (Résolution)

**Modules impliqués:** `resolvers/`

Résolution en 4 étapes (ordre important) :

1. **inheritance_resolver.py** - Résout `implements:` (multi-niveau)
   ```yaml
   # child.yaml implements parent.yaml implements grandparent.yaml
   # → Merge en profondeur (grandparent → parent → child)
   ```
   - Stratégie de merge : deep merge pour parameters/generation/output
   - Override pour template/prompt (enfant remplace parent)

2. **import_resolver.py** - Résout `imports:`
   - Fichiers multiples : merge des variations
   - Strings inline : conversion en variations
   - Déduplication par clé

3. **chunk_resolver.py** - Résout `chunks:`
   - Substitution des `{CHUNK_NAME}` dans le template
   - Support des chunks imbriqués

4. **placeholder_resolver.py** - Application des sélecteurs
   - `[random:N]` - N variations aléatoires
   - `[limit:N]` - Limite à N premières variations
   - `[indexes:1,5,8]` ou `[#1,5,8]` - Indices spécifiques
   - `[keys:foo,bar]` - Clés nommées
   - `[#0-10]` - Range d'indices

**Résultat:** `ResolvedTemplateConfig` avec tous les placeholders prêts.

### Phase 4 : Generate (Génération)

**Modules impliqués:** `generators/`

Génération des variations selon le mode :

**Mode combinatorial:**
```python
# combinatorial_generator.py
for outfit in Outfits:
    for angle in Angles:
        for expression in Expressions:
            generate_variation(outfit, angle, expression)
```

**Contrôle de l'ordre avec weights:**
```yaml
template: |
  {Outfit[weight:1]}, {Angle[weight:10]}, {Expression[weight:20]}
# → Outfit change le moins souvent (outer loop)
# → Expression change le plus souvent (inner loop)
```

**Mode random:**
```python
# random_generator.py
variations = []
for _ in range(max_images):
    combo = select_random_unique_combination()
    variations.append(combo)
```

**Seed modes (seed_manager.py):**
- `fixed`: Même seed pour toutes les images
- `progressive`: Seeds 42, 43, 44, ... (incrémentées)
- `random`: Seed -1 (unpredictable)

**Résultat:** Liste de `ResolvedVariation` avec prompts et seeds.

### Phase 5 : Normalize (Normalisation)

**Modules impliqués:** `normalizers/`

**prompt_normalizer.py** - Nettoie les prompts :
- Trim whitespace en début/fin
- Supprime les lignes vides multiples
- Normalise les virgules (`, ,` → `,`)
- Collapse les espaces multiples

**Résultat:** Prompts prêts pour l'API SD.

---

## Integration avec l'API

### CLI/src/api/

Module SRP-compliant pour l'interaction avec Stable Diffusion WebUI :

```
api/
├── sdapi_client.py       # HTTP client pur (POST /sdapi/v1/txt2img)
├── session_manager.py    # Gestion des dossiers de session
├── image_writer.py       # Écriture des fichiers PNG
├── progress_reporter.py  # Affichage console (progress bar)
└── batch_generator.py    # Orchestration de génération
```

### Flux d'exécution complet

```python
# cli.py (simplifié)

# 1. Template resolution
pipeline = V2Pipeline()
variations = pipeline.execute(template_path)

# 2. API components
api_client = SDAPIClient(api_url="http://127.0.0.1:7860")
session_manager = SessionManager(output_dir, session_name, dry_run=False)
image_writer = ImageWriter(session_manager.output_dir)
progress = ProgressReporter(total_images=len(variations))
generator = BatchGenerator(api_client, session_manager, image_writer, progress)

# 3. Generate images
for variation in variations:
    payload = {
        "prompt": variation.final_prompt,
        "negative_prompt": variation.negative_prompt,
        "seed": variation.seed,
        **parameters
    }
    generator.generate_single(payload, filename)

# 4. Save manifest
manifest = ManifestGenerator.create_manifest(variations, template_path)
manifest.save(session_manager.output_dir)
```

---

## Modèles de données

### TemplateConfig

**Fichier:** `templating/models/template_config.py`

```python
@dataclass
class TemplateConfig:
    version: str                    # "2.0"
    name: str                       # Template name
    description: Optional[str]

    # Inheritance
    implements: Optional[str]       # Path to parent template

    # Imports (variations)
    imports: Dict[str, Any]         # {PlaceholderName: file|list|dict}

    # Chunks (reusable fragments)
    chunks: Optional[Dict[str, str]]

    # Template/Prompt
    template: Optional[str]         # V1 compat
    prompt: Optional[str]           # V2 preferred
    negative_prompt: Optional[str]

    # Generation config
    generation: GenerationConfig    # mode, seed_mode, seed, max_images

    # SD parameters
    parameters: Dict[str, Any]      # width, height, steps, cfg_scale, etc.

    # Output config
    output: OutputConfig            # session_name, filename_keys

    # Metadata
    base_path: Optional[Path]       # For relative path resolution
```

### ResolvedVariation

**Fichier:** `templating/models/resolved_variation.py`

```python
@dataclass
class ResolvedVariation:
    index: int                      # Variation number (1-based)
    final_prompt: str               # Complete prompt with substitutions
    negative_prompt: str
    seed: int
    placeholders: Dict[str, str]    # {PlaceholderName: chosen_value}
    metadata: Optional[Dict[str, Any]]
```

---

## Patterns architecturaux

### 1. Strategy Pattern (Generators)

Les générateurs implémentent une stratégie commune :

```python
class GeneratorStrategy(ABC):
    @abstractmethod
    def generate(self, variations: Dict[str, List], max_images: int) -> List[Dict]:
        pass

class CombinatorialGenerator(GeneratorStrategy):
    def generate(self, variations, max_images):
        return list(itertools.product(*variations.values()))

class RandomGenerator(GeneratorStrategy):
    def generate(self, variations, max_images):
        return random.sample(combinations, max_images)
```

### 2. Pipeline Pattern (V2Pipeline)

Chaque phase transforme les données pour la phase suivante :

```
YAML file → TemplateConfig → ValidatedConfig → ResolvedConfig → Variations → Normalized Prompts
```

### 3. Dependency Injection

Les modules ne créent pas leurs dépendances, elles sont injectées :

```python
class V2Pipeline:
    def __init__(
        self,
        loader: YAMLLoader,
        validator: TemplateValidator,
        resolver: TemplateResolver,
        generator: VariationGenerator
    ):
        self.loader = loader
        self.validator = validator
        self.resolver = resolver
        self.generator = generator
```

### 4. Single Responsibility Principle

Chaque module a une seule raison de changer :

- **Loaders** : Format des fichiers YAML change
- **Validators** : Règles de validation changent
- **Resolvers** : Logique de résolution change
- **Generators** : Algorithmes de génération changent
- **Normalizers** : Règles de nettoyage changent

---

## Tests

### Structure de tests

```
CLI/tests/
├── api/                 # 76 tests - HTTP client, batch generator
├── templating/          # 3 tests - Parsing YAML V2
├── v2/                  # 227 tests - Système V2 complet
│   ├── unit/            # Tests unitaires (loaders, validators, resolvers, generators)
│   └── integration/     # Tests d'intégration (pipeline complet)
└── legacy/              # Anciens tests (Phase 1)
```

**Total : 306 tests (98% de réussite)**

### Stratégie de tests

**Tests unitaires (v2/unit/):**
- Mock des dépendances
- Test d'un seul module à la fois
- Cas normaux + cas d'erreur

**Tests d'intégration (v2/integration/):**
- Tests end-to-end du pipeline
- Templates YAML réels
- Validation des outputs (prompts, seeds, placeholders)

**Couverture de code:**
```bash
pytest tests/v2/ --cov=templating --cov-report=term-missing
# → 96.5% de couverture
```

---

## Performance

### Métriques

| Opération | Temps | Notes |
|-----------|-------|-------|
| Load YAML template | <10ms | Parse + imports |
| Validate template | <20ms | 4 validators |
| Resolve inheritance | <50ms | Multi-level |
| Generate 100 variations | <200ms | Combinatorial |
| Generate 1000 variations | <2s | Avec normalization |

### Optimisations

1. **Lazy loading** - Les variations ne sont chargées qu'au besoin
2. **Caching** - Templates hashés pour éviter re-parsing
3. **Streaming** - Génération d'images en batch avec progress
4. **Memory-efficient** - Générateurs Python (yield) pour grandes séries

---

## Évolution future

### Roadmap technique

**Voir:** `docs/roadmap/next/` et `docs/roadmap/future/`

**Priorité 1-3 (Sprint actuel):**
- ✅ V2.0 stable (terminé)

**Priorité 4-6 (Prochain sprint):**
- 🔄 Reference documentation
- 🔄 English translation
- 📋 Character templates (`.char.yaml`)
- 📋 Numeric slider placeholders (LoRA weights)

**Priorité 7-10 (Futur):**
- Web UI (FastAPI + React)
- Real-time generation preview
- Template marketplace

---

## Voir aussi

- **[Template System Spec](template-system-spec.md)** - Spécification complète V2.0
- **[YAML Templating System](yaml-templating-system.md)** - Guide technique détaillé
- **[User Guide](../guide/README.md)** - Documentation utilisateur progressive
- **[Roadmap](../../roadmap/README.md)** - Planning des features

---

**Dernière mise à jour:** 2025-10-14
**Mainteneur:** Active development
**Status:** Production ✅
