# Template System V2.0 - Architecture & Plan d'Implémentation

**Version:** 2.0.0
**Date:** 2025-10-09
**Status:** Draft - Ready for Implementation

---

## 1. Vue d'ensemble de l'architecture

### 1.1 Principes de conception

- **Modularité** : Chaque composant a une responsabilité unique
- **Testabilité** : Injection de dépendances, interfaces claires
- **Performance** : Cache agressif, résolution lazy
- **Rétrocompatibilité** : Cohabitation V1/V2 sans régression
- **Validation stricte** : Fail-fast avec collecte complète des erreurs

### 1.2 Diagramme des modules

```
┌─────────────────────────────────────────────────────────────────┐
│                     Entry Point (CLI)                            │
│                  template_cli.py / sdgen                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Version Router                                │
│              templating/version_router.py                        │
│  ┌──────────────────────┐      ┌─────────────────────────────┐ │
│  │  V1.x (Legacy)       │      │  V2.0 (New)                 │ │
│  │  templating/v1/      │      │  templating/v2/             │ │
│  └──────────────────────┘      └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      V2.0 Architecture                           │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   Loaders      │  │   Validators   │  │   Resolvers      │  │
│  │                │  │                │  │                  │  │
│  │ • YamlLoader   │  │ • Validator    │  │ • Inheritance    │  │
│  │ • Parser       │  │ • ErrorCollect │  │ • Import         │  │
│  │                │  │                │  │ • Template       │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│           │                  │                     │             │
│           └──────────────────┴─────────────────────┘             │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Models                                │  │
│  │  • TemplateConfig  • ChunkConfig  • PromptConfig          │  │
│  │  • ValidationResult  • ResolvedContext                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Normalizer                               │  │
│  │                 PromptNormalizer                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Generation Engine                             │
│               prompt_config.py / executor.py                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SD WebUI API                                  │
│                   api/sdapi_client.py                            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Flux de données

```
User Input (path/to/prompt.yaml)
         │
         ▼
   Version Router
         │
         ├─► V1.x → Legacy System
         │
         └─► V2.0 ──────────────────────────────────────┐
                                                         │
    ┌────────────────────────────────────────────────────┘
    │
    ▼
YamlLoader.load_file(prompt.yaml)
    │
    ▼
Parser.parse_prompt(data) → PromptConfig (raw)
    │
    ▼
Validator.validate(config)
    │   ├─► Phase 1: Structure ──┐
    │   ├─► Phase 2: Paths ──────┤
    │   ├─► Phase 3: Inheritance ─┤
    │   ├─► Phase 4: Imports ─────┤
    │   └─► Phase 5: Templates ───┘
    │                              │
    │   ┌──────────────────────────┘
    │   ▼
    │  Errors? ─── YES ──► Log errors.json + Display + ABORT
    │   │
    │   NO
    ▼   ▼
InheritanceResolver.resolve_implements(config)
    │   (Load parent templates recursively)
    │   (Merge configs: parameters, imports, chunks, defaults)
    │
    ▼
ImportResolver.resolve_imports(config)
    │   (Load variation files)
    │   (Merge multi-sources: files + inline)
    │   (Detect key conflicts)
    │
    ▼
TemplateResolver.resolve_template(template, context)
    │   (Inject chunks with @)
    │   (Apply selectors [])
    │   (Resolve {placeholders})
    │
    ▼
PromptNormalizer.normalize(prompt)
    │   (Trim, collapse commas, remove orphan commas, etc.)
    │
    ▼
ResolvedPrompt (final string)
    │
    ▼
Generation Engine (combinatorial/random)
    │
    ▼
SD WebUI API (generate images)
```

---

## 2. Modules Python - Détails

### 2.1 Structure des dossiers

```
CLI/src/templating/
├── v1/                          # Legacy system (V1.x)
│   ├── resolver.py              # Ancien resolver
│   └── variation_loader.py      # Ancien loader
│
├── v2/                          # New system (V2.0)
│   ├── __init__.py
│   │
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── yaml_loader.py       # Chargement fichiers YAML
│   │   └── parser.py            # Parsing configs
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── validator.py         # Validation 5 phases
│   │   └── validation_error.py  # Modèle d'erreur
│   │
│   ├── resolvers/
│   │   ├── __init__.py
│   │   ├── inheritance_resolver.py  # Résolution implements:
│   │   ├── import_resolver.py       # Résolution imports:
│   │   └── template_resolver.py     # Résolution template strings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config_models.py     # TemplateConfig, ChunkConfig, etc.
│   │   └── context.py           # ResolvedContext
│   │
│   ├── normalizers/
│   │   ├── __init__.py
│   │   └── prompt_normalizer.py # Normalisation prompts
│   │
│   └── utils/
│       ├── __init__.py
│       ├── path_utils.py        # Résolution chemins
│       ├── hash_utils.py        # MD5 pour inline strings
│       └── cache.py             # Cache de résolution
│
├── version_router.py            # Point d'entrée unifié
└── __init__.py
```

---

### 2.2 Loaders & Parser

#### `loaders/yaml_loader.py`

```python
from pathlib import Path
from typing import Dict, Any
import yaml


class YamlLoader:
    """Chargement de fichiers YAML avec gestion des chemins relatifs."""

    def __init__(self, cache: Optional[dict] = None):
        self.cache = cache or {}

    def load_file(self, path: Path, base_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Charge un fichier YAML.

        Args:
            path: Chemin vers le fichier (relatif ou absolu)
            base_path: Chemin de base pour résolution relative

        Returns:
            Dictionnaire contenu du fichier

        Raises:
            FileNotFoundError: Si fichier introuvable
            yaml.YAMLError: Si YAML mal formé
        """
        resolved_path = self.resolve_path(path, base_path)

        # Check cache
        if resolved_path in self.cache:
            return self.cache[resolved_path]

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        with open(resolved_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Cache result
        self.cache[resolved_path] = data
        return data

    def resolve_path(self, path: Path | str, base_path: Optional[Path] = None) -> Path:
        """
        Résout un chemin relatif par rapport à base_path.

        Args:
            path: Chemin à résoudre
            base_path: Répertoire de base (par défaut: parent du fichier courant)

        Returns:
            Chemin absolu résolu
        """
        path = Path(path)

        if path.is_absolute():
            # Chemins absolus non supportés (portabilité)
            raise ValueError(f"Absolute paths not supported: {path}")

        if base_path is None:
            base_path = Path.cwd()

        # Résolution relative au base_path
        resolved = (base_path / path).resolve()
        return resolved
```

#### `loaders/parser.py`

```python
from pathlib import Path
from typing import Dict, Any
from ..models.config_models import (
    TemplateConfig, ChunkConfig, PromptConfig, GenerationConfig
)


class ConfigParser:
    """Parsing des configurations YAML en modèles Python."""

    def parse_template(self, data: Dict[str, Any], source_file: Path) -> TemplateConfig:
        """Parse un fichier .template.yaml."""
        return TemplateConfig(
            version=data.get('version', '1.0.0'),
            name=data['name'],
            implements=data.get('implements'),
            parameters=data.get('parameters', {}),
            imports=data.get('imports', {}),
            template=data['template'],
            negative_prompt=data.get('negative_prompt', ''),
            source_file=source_file
        )

    def parse_chunk(self, data: Dict[str, Any], source_file: Path) -> ChunkConfig:
        """Parse un fichier .chunk.yaml."""
        return ChunkConfig(
            version=data.get('version', '1.0.0'),
            type=data['type'],
            implements=data.get('implements'),
            imports=data.get('imports', {}),
            template=data['template'],
            defaults=data.get('defaults', {}),
            chunks=data.get('chunks', {}),
            source_file=source_file
        )

    def parse_prompt(self, data: Dict[str, Any], source_file: Path) -> PromptConfig:
        """Parse un fichier .prompt.yaml."""
        gen_data = data['generation']
        generation = GenerationConfig(
            mode=gen_data['mode'],
            seed=gen_data['seed'],
            seed_mode=gen_data['seed_mode'],
            max_images=gen_data['max_images']
        )

        return PromptConfig(
            version=data.get('version', '1.0.0'),
            name=data['name'],
            implements=data['implements'],
            generation=generation,
            imports=data.get('imports', {}),
            template=data['template'],
            negative_prompt=data.get('negative_prompt'),
            source_file=source_file
        )

    def parse_variations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse un fichier de variations.

        Format attendu : dict YAML simple
        {
            "BobCut": "bob cut, chin-length hair",
            "LongHair": "long flowing hair"
        }
        """
        if not isinstance(data, dict):
            raise ValueError("Variations file must be a YAML dictionary")

        return data
```

---

### 2.3 Validators

#### `validators/validation_error.py`

```python
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class ValidationError:
    """Modèle d'erreur de validation."""
    type: str           # 'structure', 'path', 'inheritance', 'import', 'template'
    message: str
    file: Optional[Path] = None
    line: Optional[int] = None
    name: Optional[str] = None
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        """Conversion en dict pour JSON."""
        return {
            'type': self.type,
            'message': self.message,
            'file': str(self.file) if self.file else None,
            'line': self.line,
            'name': self.name,
            'details': self.details
        }


@dataclass
class ValidationResult:
    """Résultat de validation."""
    is_valid: bool
    errors: List[ValidationError]

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_json(self) -> dict:
        """Export JSON pour logging."""
        return {
            'errors': [e.to_dict() for e in self.errors],
            'count': self.error_count
        }
```

#### `validators/validator.py`

```python
from pathlib import Path
from typing import List
import re
from .validation_error import ValidationError, ValidationResult
from ..models.config_models import TemplateConfig, ChunkConfig, PromptConfig


class ConfigValidator:
    """
    Validation en 5 phases avec collecte complète des erreurs.

    Phases:
    1. Structure : YAML bien formé, champs requis
    2. Paths : Fichiers implements/imports existent
    3. Inheritance : Types compatibles, pas de cycles
    4. Imports : Pas de clés dupliquées
    5. Templates : Placeholders résolus, pas de réservés interdits
    """

    RESERVED_PLACEHOLDERS = {'prompt', 'negprompt', 'loras'}

    def __init__(self, loader):
        self.loader = loader
        self.errors: List[ValidationError] = []

    def validate(self, config: TemplateConfig | ChunkConfig | PromptConfig) -> ValidationResult:
        """Validation complète (5 phases)."""
        self.errors = []

        # Phase 1: Structure
        self._validate_structure(config)

        # Phase 2: Paths
        self._validate_paths(config)

        # Phase 3: Inheritance
        self._validate_inheritance(config)

        # Phase 4: Imports
        self._validate_imports(config)

        # Phase 5: Templates
        self._validate_templates(config)

        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors
        )

    def _validate_structure(self, config):
        """Phase 1: Validation structurelle."""
        # Version présente
        if not config.version:
            self.errors.append(ValidationError(
                type='structure',
                message='Missing required field: version',
                file=config.source_file
            ))

        # Champs obligatoires selon type
        if isinstance(config, TemplateConfig):
            if not config.name:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: name',
                    file=config.source_file
                ))
            if not config.template:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: template',
                    file=config.source_file
                ))

        elif isinstance(config, ChunkConfig):
            if not config.type:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: type',
                    file=config.source_file
                ))
            if not config.template:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: template',
                    file=config.source_file
                ))

        elif isinstance(config, PromptConfig):
            if not config.implements:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: implements',
                    file=config.source_file
                ))
            if not config.generation:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: generation',
                    file=config.source_file
                ))

    def _validate_paths(self, config):
        """Phase 2: Validation des chemins."""
        base_path = config.source_file.parent

        # Vérifier implements
        if config.implements:
            try:
                path = self.loader.resolve_path(config.implements, base_path)
                if not path.exists():
                    self.errors.append(ValidationError(
                        type='path',
                        message=f'File not found: {config.implements}',
                        file=config.source_file,
                        name='implements'
                    ))
            except ValueError as e:
                self.errors.append(ValidationError(
                    type='path',
                    message=str(e),
                    file=config.source_file,
                    name='implements'
                ))

        # Vérifier imports (fichiers)
        for import_name, import_value in config.imports.items():
            if isinstance(import_value, str):
                # Fichier simple
                try:
                    path = self.loader.resolve_path(import_value, base_path)
                    if not path.exists():
                        self.errors.append(ValidationError(
                            type='path',
                            message=f'File not found: {import_value}',
                            file=config.source_file,
                            name=f'imports.{import_name}'
                        ))
                except ValueError as e:
                    self.errors.append(ValidationError(
                        type='path',
                        message=str(e),
                        file=config.source_file,
                        name=f'imports.{import_name}'
                    ))

            elif isinstance(import_value, list):
                # Liste (fichiers + inline)
                for item in import_value:
                    if not isinstance(item, str) or not item.startswith('"'):
                        # Fichier (pas inline string)
                        try:
                            path = self.loader.resolve_path(item, base_path)
                            if not path.exists():
                                self.errors.append(ValidationError(
                                    type='path',
                                    message=f'File not found: {item}',
                                    file=config.source_file,
                                    name=f'imports.{import_name}'
                                ))
                        except ValueError as e:
                            self.errors.append(ValidationError(
                                type='path',
                                message=str(e),
                                file=config.source_file,
                                name=f'imports.{import_name}'
                            ))

    def _validate_inheritance(self, config):
        """Phase 3: Validation de l'héritage."""
        if not config.implements:
            return

        # Vérifier type compatibility (chunks uniquement)
        if isinstance(config, ChunkConfig):
            try:
                base_path = config.source_file.parent
                parent_path = self.loader.resolve_path(config.implements, base_path)
                parent_data = self.loader.load_file(parent_path)

                parent_type = parent_data.get('type')
                if parent_type and parent_type != config.type:
                    self.errors.append(ValidationError(
                        type='inheritance',
                        message=f'Type mismatch: {config.source_file.name} ({config.type}) '
                                f'cannot implement {parent_path.name} ({parent_type})',
                        file=config.source_file,
                        details={'parent_type': parent_type, 'child_type': config.type}
                    ))
                elif not parent_type:
                    # Warning: parent sans type
                    self.errors.append(ValidationError(
                        type='inheritance',
                        message=f'Warning: {parent_path.name} has no type, assuming {config.type}',
                        file=config.source_file,
                        details={'assumed_type': config.type}
                    ))
            except Exception as e:
                # Erreur déjà catchée en Phase 2 (path validation)
                pass

    def _validate_imports(self, config):
        """Phase 4: Validation des imports (conflits de clés)."""
        # TODO: Implémenter détection conflits de clés lors du merge
        pass

    def _validate_templates(self, config):
        """Phase 5: Validation des templates."""
        # Vérifier placeholders réservés
        if isinstance(config, ChunkConfig):
            # Dans chunks, interdire {prompt}, {negprompt}, {loras}
            for reserved in self.RESERVED_PLACEHOLDERS:
                pattern = r'\{' + reserved + r'\}'
                if re.search(pattern, config.template, re.IGNORECASE):
                    self.errors.append(ValidationError(
                        type='template',
                        message=f'Reserved placeholder {{{reserved}}} not allowed in chunks',
                        file=config.source_file,
                        name=reserved
                    ))
```

---

### 2.4 Resolvers

#### `resolvers/inheritance_resolver.py`

```python
from pathlib import Path
from typing import Dict, Any
from ..models.config_models import TemplateConfig, ChunkConfig, PromptConfig


class InheritanceResolver:
    """Résolution de l'héritage avec implements:"""

    def __init__(self, loader, parser):
        self.loader = loader
        self.parser = parser
        self.resolution_cache = {}

    def resolve_implements(
        self,
        config: TemplateConfig | ChunkConfig | PromptConfig
    ) -> TemplateConfig | ChunkConfig | PromptConfig:
        """
        Résout l'héritage récursif.

        Returns:
            Config avec tous les champs mergés depuis les parents
        """
        if not config.implements:
            return config

        # Check cache
        cache_key = str(config.source_file)
        if cache_key in self.resolution_cache:
            return self.resolution_cache[cache_key]

        # Load parent
        base_path = config.source_file.parent
        parent_path = self.loader.resolve_path(config.implements, base_path)
        parent_data = self.loader.load_file(parent_path)

        # Parse parent
        parent_config = self._parse_config(parent_data, parent_path)

        # Resolve parent's implements (recursive)
        parent_resolved = self.resolve_implements(parent_config)

        # Merge
        merged = self.merge_configs(parent_resolved, config)

        # Cache
        self.resolution_cache[cache_key] = merged
        return merged

    def merge_configs(self, parent, child):
        """
        Merge parent et child configs.

        Règles:
        - parameters: MERGE (child override parent)
        - imports: MERGE (child override parent)
        - chunks: MERGE (child override parent)
        - defaults: MERGE (child override parent)
        - template: REPLACE (child remplace parent, avec warning)
        """
        # Clone child
        merged = child

        # Merge parameters
        if hasattr(parent, 'parameters') and hasattr(child, 'parameters'):
            merged_params = {**parent.parameters, **child.parameters}
            merged.parameters = merged_params

        # Merge imports
        merged_imports = {**parent.imports, **child.imports}
        merged.imports = merged_imports

        # Merge chunks (ChunkConfig uniquement)
        if isinstance(child, ChunkConfig):
            merged_chunks = {**parent.chunks, **child.chunks}
            merged_defaults = {**parent.defaults, **child.defaults}
            merged.chunks = merged_chunks
            merged.defaults = merged_defaults

        return merged

    def _parse_config(self, data: dict, source_file: Path):
        """Parse config selon type (auto-detect)."""
        if 'generation' in data:
            return self.parser.parse_prompt(data, source_file)
        elif 'type' in data:
            return self.parser.parse_chunk(data, source_file)
        else:
            return self.parser.parse_template(data, source_file)
```

#### `resolvers/import_resolver.py`

```python
from pathlib import Path
from typing import Dict, List
from ..utils.hash_utils import md5_short


class ImportResolver:
    """Résolution des imports avec merge multi-sources."""

    def __init__(self, loader, parser):
        self.loader = loader
        self.parser = parser

    def resolve_imports(self, config, base_path: Path) -> Dict[str, Dict[str, str]]:
        """
        Résout tous les imports.

        Returns:
            Dict[import_name, Dict[key, value]]
            Ex: {"Outfit": {"Urban1": "jeans", "Chic1": "dress", "7d8e3a2f": "red dress"}}
        """
        resolved = {}

        for import_name, import_value in config.imports.items():
            if isinstance(import_value, str):
                # Fichier simple
                variations = self._load_variation_file(import_value, base_path)
                resolved[import_name] = variations

            elif isinstance(import_value, list):
                # Multi-sources (merge)
                merged = self._merge_multi_sources(import_value, base_path, import_name)
                resolved[import_name] = merged

            elif isinstance(import_value, dict):
                # Nested imports (ex: chunks: {positive: ..., negative: ...})
                nested = {}
                for nested_name, nested_path in import_value.items():
                    variations = self._load_variation_file(nested_path, base_path)
                    nested[nested_name] = variations
                resolved[import_name] = nested

        return resolved

    def _load_variation_file(self, path: str, base_path: Path) -> Dict[str, str]:
        """Charge un fichier de variations."""
        resolved_path = self.loader.resolve_path(path, base_path)
        data = self.loader.load_file(resolved_path)
        return self.parser.parse_variations(data)

    def _merge_multi_sources(
        self,
        sources: List[str],
        base_path: Path,
        import_name: str
    ) -> Dict[str, str]:
        """
        Merge variations depuis plusieurs sources.

        Détecte conflits de clés.
        """
        merged = {}
        key_sources = {}  # Tracking pour erreurs de conflit

        for source in sources:
            if source.startswith('"') or not source.endswith('.yaml'):
                # Inline string
                inline_key = md5_short(source)
                merged[inline_key] = source
            else:
                # Fichier
                variations = self._load_variation_file(source, base_path)

                # Détection conflits
                for key, value in variations.items():
                    if key in merged:
                        raise ValueError(
                            f"Duplicate key '{key}' in {import_name} imports "
                            f"(found in {key_sources[key]} and {source})"
                        )
                    merged[key] = value
                    key_sources[key] = source

        return merged
```

#### `resolvers/template_resolver.py`

```python
import re
from typing import Dict, Any


class TemplateResolver:
    """Résolution de templates avec injection de chunks et sélecteurs."""

    def __init__(self, import_resolver, chunk_cache):
        self.import_resolver = import_resolver
        self.chunk_cache = chunk_cache

    def resolve_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Résout un template complet.

        Args:
            template: Template string
            context: {
                'imports': Dict[import_name, variations],
                'chunks': Dict[chunk_name, ChunkConfig],
                'variation_state': Current variation values
            }

        Returns:
            Template résolu
        """
        # 1. Inject chunks (@Chunk, @{Chunk with ...})
        template = self._inject_chunks(template, context)

        # 2. Resolve placeholders ({Placeholder[selectors]})
        template = self._resolve_placeholders(template, context)

        return template

    def _inject_chunks(self, template: str, context: Dict) -> str:
        """Injecte les chunks (@)."""
        # Pattern: @ChunkName ou @{ChunkName with ...}

        # Simple chunk ref: @ChunkName
        pattern_simple = r'@([\w.]+)'
        template = re.sub(
            pattern_simple,
            lambda m: self._resolve_chunk_ref(m.group(1), context),
            template
        )

        # Chunk with params: @{ChunkName with Param1:{Import1}, Param2:{Import2}}
        pattern_with = r'@\{(\w+)\s+with\s+([^}]+)\}'
        template = re.sub(
            pattern_with,
            lambda m: self._resolve_chunk_with_params(m.group(1), m.group(2), context),
            template
        )

        return template

    def _resolve_chunk_ref(self, ref: str, context: Dict) -> str:
        """Résout une référence simple @ChunkName."""
        # Navigation nested: @chunks.positive
        parts = ref.split('.')

        if len(parts) == 1:
            # Simple ref
            chunk = context['chunks'].get(ref)
            if not chunk:
                raise ValueError(f"Chunk '{ref}' not found in imports")
            return chunk.template
        else:
            # Nested ref (ex: chunks.positive)
            # TODO: Implémenter navigation
            return ""

    def _resolve_chunk_with_params(
        self,
        chunk_name: str,
        params_str: str,
        context: Dict
    ) -> str:
        """
        Résout @{ChunkName with Param1:{Import1[sel]}, ...}

        Exemple:
        @{Character with Angles:{Angle[15]}, Poses:{Pose[$5]}}
        """
        chunk = context['chunks'].get(chunk_name)
        if not chunk:
            raise ValueError(f"Chunk '{chunk_name}' not found")

        # Parse params: "Angles:{Angle[15]}, Poses:{Pose[$5]}"
        params = self._parse_with_params(params_str)

        # Create new context for chunk resolution
        chunk_context = {**context}

        # Resolve chunk template with params
        chunk_template = chunk.template
        for param_name, import_ref in params.items():
            # import_ref = "{Angle[15]}"
            # Extract import name and selectors
            # TODO: Parser selector et appliquer variations
            pass

        return chunk_template

    def _parse_with_params(self, params_str: str) -> Dict[str, str]:
        """
        Parse 'Angles:{Angle[15]}, Poses:{Pose}'

        Returns:
            {"Angles": "{Angle[15]}", "Poses": "{Pose}"}
        """
        # Simple split sur ','
        params = {}
        for part in params_str.split(','):
            part = part.strip()
            if ':' in part:
                key, value = part.split(':', 1)
                params[key.strip()] = value.strip()
        return params

    def _resolve_placeholders(self, template: str, context: Dict) -> str:
        """Résout {Placeholder[selectors]}."""
        # Pattern: {Name} ou {Name[selectors]}
        pattern = r'\{(\w+)(?:\[([^\]]+)\])?\}'

        def replacer(match):
            name = match.group(1)
            selectors = match.group(2)  # Peut être None

            # Get variation value from context
            if name in context.get('variation_state', {}):
                return context['variation_state'][name]

            # Placeholder non résolu (sera résolu plus tard par generation engine)
            return match.group(0)

        return re.sub(pattern, replacer, template)
```

---

### 2.5 Models

#### `models/config_models.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class TemplateConfig:
    """Configuration d'un .template.yaml"""
    version: str
    name: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    imports: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: str = ''


@dataclass
class ChunkConfig:
    """Configuration d'un .chunk.yaml"""
    version: str
    type: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    imports: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)


@dataclass
class GenerationConfig:
    """Configuration de génération"""
    mode: str  # 'random' | 'combinatorial'
    seed: int
    seed_mode: str  # 'fixed' | 'progressive' | 'random'
    max_images: int


@dataclass
class PromptConfig:
    """Configuration d'un .prompt.yaml"""
    version: str
    name: str
    implements: str
    generation: GenerationConfig
    template: str
    source_file: Path
    imports: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: Optional[str] = None


@dataclass
class ResolvedContext:
    """Context de résolution avec toutes les variations chargées"""
    imports: Dict[str, Dict[str, str]]  # {import_name: {key: value}}
    chunks: Dict[str, ChunkConfig]      # {chunk_name: ChunkConfig}
    parameters: Dict[str, Any]
    variation_state: Dict[str, str] = field(default_factory=dict)
```

---

### 2.6 Normalizers

#### `normalizers/prompt_normalizer.py`

```python
import re


class PromptNormalizer:
    """Normalisation des prompts finaux."""

    @staticmethod
    def normalize(prompt: str) -> str:
        """
        Applique toutes les règles de normalisation.

        1. Trim espaces début/fin
        2. Collapse virgules multiples
        3. Suppression virgules orphelines
        4. Normalisation espaces autour virgules
        5. Préservation 1 ligne vide max
        """
        # 1. Trim par ligne
        lines = [line.strip() for line in prompt.split('\n')]

        # 2. Collapse virgules multiples
        prompt = '\n'.join(lines)
        prompt = re.sub(r',\s*,+', ',', prompt)

        # 3. Suppression virgules orphelines début/fin
        prompt = prompt.strip(',').strip()

        # 4. Normalisation espaces autour virgules
        prompt = re.sub(r'\s*,\s*', ', ', prompt)

        # 5. Collapse lignes vides (max 1)
        prompt = re.sub(r'\n\n\n+', '\n\n', prompt)

        return prompt
```

---

## 3. Flux de résolution détaillé

### 3.1 Diagramme de séquence

```
User                CLI             Router          Loader          Parser          Validator
 │                   │                │               │               │                │
 │ sdgen generate    │                │               │               │                │
 │  prompt.yaml      │                │               │               │                │
 ├──────────────────>│                │               │               │                │
 │                   │ detect_version │               │               │                │
 │                   ├───────────────>│               │               │                │
 │                   │      v2.0      │               │               │                │
 │                   │<───────────────┤               │               │                │
 │                   │                │ load_file     │               │                │
 │                   │                ├──────────────>│               │                │
 │                   │                │    (data)     │               │                │
 │                   │                │<──────────────┤               │                │
 │                   │                │               │ parse_prompt  │                │
 │                   │                │               ├──────────────>│                │
 │                   │                │               │ PromptConfig  │                │
 │                   │                │               │<──────────────┤                │
 │                   │                │               │               │   validate     │
 │                   │                │               │               ├───────────────>│
 │                   │                │               │               │ (5 phases)     │
 │                   │                │               │               │                │
 │                   │                │               │               │ ValidationOK   │
 │                   │                │               │               │<───────────────┤
 │                   │                │               │               │                │

InheritanceResolver    ImportResolver    TemplateResolver    Normalizer    Generator
       │                      │                  │                │            │
       │  resolve_implements  │                  │                │            │
       │<─────────────────────┤                  │                │            │
       │  (recursive load     │                  │                │            │
       │   & merge parents)   │                  │                │            │
       ├─────────────────────>│                  │                │            │
       │                      │ resolve_imports  │                │            │
       │                      ├─────────────────>│                │            │
       │                      │  (load files +   │                │            │
       │                      │   merge sources) │                │            │
       │                      │<─────────────────┤                │            │
       │                      │                  │ resolve_template│           │
       │                      │                  ├────────────────>│           │
       │                      │                  │ (inject chunks, │           │
       │                      │                  │  apply selectors)│          │
       │                      │                  │<────────────────┤           │
       │                      │                  │                 │ normalize │
       │                      │                  │                 ├──────────>│
       │                      │                  │                 │  (final)  │
       │                      │                  │                 │<──────────┤
       │                      │                  │                 │           │
       │                      │                  │                 │  generate │
       │                      │                  │                 │  (combos) │
       │                      │                  │                 ├──────────>│
       │                      │                  │                 │           │
       │                      │                  │                 │  SD API   │
       │                      │                  │                 │  calls    │
       │                      │                  │                 │           │
```

---

### 3.2 Validation : 5 phases

```
Phase 1: Structure
├─ Version présente ?
├─ Champs requis (name, template, type, etc.) ?
└─ Format YAML valide ?

Phase 2: Paths
├─ implements: fichier existe ?
├─ imports: fichiers existent ?
└─ Chemins relatifs valides ?

Phase 3: Inheritance
├─ Types compatibles (chunks) ?
├─ Pas de cycles ?
└─ Parent sans type → Warning

Phase 4: Imports
├─ Pas de clés dupliquées dans merge ?
└─ Imports référencés existent ?

Phase 5: Templates
├─ Placeholders réservés corrects ?
├─ Références Import.Key valides ?
└─ Pas de placeholders non résolus ?
```

**Si erreurs :** Log JSON + Display + ABORT
**Sinon :** Continue resolution

---

## 4. Plan d'implémentation (8 phases)

### Phase 1 : Fondations (Semaine 1)
**Objectif :** Structures de données + Parsing basique

**Tâches :**
1. Créer `models/config_models.py`
   - `TemplateConfig`, `ChunkConfig`, `PromptConfig`
   - `ValidationError`, `ValidationResult`
2. Créer `loaders/yaml_loader.py`
   - `YamlLoader.load_file()`
   - `YamlLoader.resolve_path()`
3. Créer `loaders/parser.py`
   - `ConfigParser.parse_template()`
   - `ConfigParser.parse_chunk()`
   - `ConfigParser.parse_prompt()`
   - `ConfigParser.parse_variations()`
4. Créer `utils/path_utils.py` et `utils/hash_utils.py`

**Tests :**
- `tests/v2/test_models.py` : Validation des dataclasses
- `tests/v2/test_yaml_loader.py` : Chargement fichiers
- `tests/v2/test_parser.py` : Parsing configs

**Critères de succès :**
- ✅ Tous les modèles instanciables
- ✅ YamlLoader charge fichiers YAML valides
- ✅ Parser convertit dict → Config objects

---

### Phase 2 : Validation (Semaine 2)
**Objectif :** Validator avec 5 phases + Erreurs JSON

**Tâches :**
1. Créer `validators/validation_error.py`
2. Créer `validators/validator.py`
   - Implémenter 5 phases
   - Collecte toutes erreurs
3. Créer système de logging JSON

**Tests :**
- `tests/v2/test_validator.py` : Chaque phase séparément
- `tests/v2/test_validation_errors.py` : Format JSON

**Critères de succès :**
- ✅ Toutes les 5 phases implémentées
- ✅ Erreurs collectées (pas de throw immédiat)
- ✅ JSON valide exporté

---

### Phase 3 : Héritage (Semaine 3) - ✅ **COMPLETED** (2025-10-09)
**Objectif :** Résolution `implements:` avec merge

**Tâches :**
1. ✅ Créer `resolvers/inheritance_resolver.py`
   - ✅ `resolve_implements()` récursif
   - ✅ `merge_configs()` avec règles spécifiques
2. ✅ Implémenter cache de résolution

**Tests :** ✅ 17 tests (tests/v2/unit/test_inheritance_resolver.py)
- ✅ Héritage simple (template, chunk, prompt)
- ✅ Multi-niveaux (3 niveaux grandparent → parent → child)
- ✅ Merge rules (parameters, imports, chunks, defaults, template, negative_prompt)
- ✅ Cache behavior (hits, clear, invalidate)
- ✅ Type validation (chunks: same type, mismatch error, no-type warning)
- ✅ Error handling (missing files, absolute paths)

**Critères de succès :**
- ✅ Héritage multi-niveaux fonctionne
- ✅ Merge respecte les règles (parameters: MERGE, template: REPLACE avec WARNING)
- ✅ Cache évite rechargements

**Métriques :**
- Tests: 17 nouveaux tests Phase 3
- Total V2: 100 tests (Phase 1+2: 83, Phase 3: 17)
- Total projet: 324 tests (V1: 224, V2: 100)
- Régression V1: ✅ Aucune
- Fichiers créés:
  - `CLI/src/templating/v2/resolvers/inheritance_resolver.py` (262 lignes)
  - `CLI/tests/v2/unit/test_inheritance_resolver.py` (441 lignes)

---

### Phase 4 : Imports & Variations (Semaine 4)
**Objectif :** Chargement variations + Merge multi-sources

**Tâches :**
1. Créer `resolvers/import_resolver.py`
   - `resolve_imports()`
   - `_merge_multi_sources()` avec détection conflits
2. Implémenter MD5 hash pour inline strings

**Tests :**
- `tests/v2/test_imports.py` : Import fichiers, inline, mix
- `tests/v2/test_merge_variations.py` : Conflits de clés

**Critères de succès :**
- ✅ Import fichiers YAML fonctionne
- ✅ Inline strings avec clés auto-générées (MD5)
- ✅ Conflits de clés détectés et loggés

---

### Phase 5 : Résolution Templates (Semaine 5)
**Objectif :** Injection chunks + Sélecteurs

**Tâches :**
1. Créer `resolvers/template_resolver.py`
   - `_inject_chunks()` : `@Chunk`, `@{Chunk with ...}`
   - `_resolve_placeholders()` : `{Placeholder[selectors]}`
   - Parser sélecteurs : `[15]`, `[#1,3,5]`, `[$8]`, combinaisons
2. Implémenter syntaxe `with`

**Tests :**
- `tests/v2/test_chunk_injection.py` : `@Chunk` résolution
- `tests/v2/test_selectors.py` : Tous les types de sélecteurs
- `tests/v2/test_chunk_with.py` : Syntaxe `@{Chunk with ...}`

**Critères de succès :**
- ✅ `@Chunk` injecte template résolu
- ✅ Sélecteurs `[]` appliqués correctement
- ✅ `with` passe paramètres aux chunks

---

### Phase 6 : Normalisation (Semaine 6)
**Objectif :** Normalisation prompts finaux

**Tâches :**
1. Créer `normalizers/prompt_normalizer.py`
   - Implémenter 5 règles de normalisation

**Tests :**
- `tests/v2/test_normalizer.py` : Chaque règle séparément

**Critères de succès :**
- ✅ Toutes les règles appliquées
- ✅ Placeholders vides gérés correctement

---

### Phase 7 : Intégration & Rétrocompat (Semaine 7)
**Objectif :** Cohabitation V1/V2 + Routage

**Tâches :**
1. Créer `version_router.py`
   - `detect_version()`
   - Routage V1 vs V2
2. Restructurer `templating/` en `v1/` et `v2/`
3. Intégrer avec `prompt_config.py` et `executor.py`

**Tests :**
- `tests/v2/test_version_detection.py` : Détection correcte
- `tests/integration/test_v1_compatibility.py` : Tous les anciens tests passent

**Critères de succès :**
- ✅ V1.x toujours fonctionnel
- ✅ V2.0 routé correctement
- ✅ Pas de régression sur V1

---

### Phase 8 : Tests End-to-End (Semaine 8)
**Objectif :** Tests complets + Exemples réels

**Tâches :**
1. Créer exemples réels (templates, chunks, prompts)
2. Tests end-to-end complets
3. Documentation utilisateur

**Tests :**
- `tests/integration/test_e2e_simple.py`
- `tests/integration/test_e2e_chunks.py`
- `tests/integration/test_e2e_complex.py`

**Critères de succès :**
- ✅ Exemples génèrent images correctement
- ✅ Tous les tests passent (141 existants + nouveaux V2)
- ✅ Documentation complète

---

## 5. Points d'intégration avec code existant

### 5.1 Refactoring vs Nouveau module

**Décision :** Nouveau module `v2/` plutôt que refactoring de `resolver.py`

**Raisons :**
- Éviter régression sur V1.x
- Cohabitation claire
- Refactoring futur possible après validation V2

### 5.2 Fichiers à modifier

```
CLI/src/config/config_manager.py
  └─ Ajouter détection version dans load_config()

CLI/src/templating/prompt_config.py
  └─ Router vers V1 ou V2 selon version

CLI/template_cli.py
  └─ Passer version au système de génération
```

### 5.3 Backward compatibility hooks

```python
# CLI/src/templating/version_router.py

def load_prompt_config(path: Path):
    """Point d'entrée unifié."""
    data = yaml.safe_load(path.read_text())
    version = data.get('version', '1.0.0')

    if version.startswith('1.'):
        # Legacy V1.x
        from .v1.resolver import resolve_prompt
        return resolve_prompt(path)
    elif version.startswith('2.'):
        # New V2.0
        from .v2 import V2System
        return V2System().process(path)
    else:
        raise ValueError(f"Unsupported version: {version}")
```

---

## 6. Tests Strategy

### 6.1 Structure des tests

```
CLI/tests/v2/
├── unit/
│   ├── test_models.py
│   ├── test_yaml_loader.py
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_inheritance_resolver.py
│   ├── test_import_resolver.py
│   ├── test_template_resolver.py
│   └── test_normalizer.py
│
├── integration/
│   ├── test_full_resolution.py
│   ├── test_v1_compatibility.py
│   └── test_error_handling.py
│
└── fixtures/
    ├── templates/
    ├── chunks/
    ├── prompts/
    └── variations/
```

### 6.2 Coverage objectives

- **Unit tests :** 90%+ coverage
- **Integration tests :** Tous les flows principaux
- **Rétrocompat :** 100% des anciens tests V1 passent

---

## 7. Performance & Optimisations

### 7.1 Cache strategy

**Cache multi-niveaux :**

1. **File cache** : Éviter rechargements YAML
   ```python
   cache[absolute_path] = parsed_data
   ```

2. **Resolution cache** : Éviter re-résolution héritage
   ```python
   cache[config_path] = resolved_config_with_inheritance
   ```

3. **Import cache** : Éviter re-merge variations
   ```python
   cache[import_signature] = merged_variations
   ```

### 7.2 Lazy loading

- Ne charger que les imports utilisés
- Résolution chunks à la demande
- Parser sélecteurs uniquement si présents

### 7.3 Parallel validation

- Phases 1-2 peuvent s'exécuter en parallèle
- Phases 3-5 dépendent de phases précédentes

---

## 8. Logging & Debugging

### 8.1 Niveaux de log

```python
# DEBUG : Détails résolution (cache hits, etc.)
logger.debug("Cache hit for %s", path)

# INFO : Étapes principales
logger.info("Resolving inheritance for %s", config.name)

# WARNING : Problèmes non bloquants
logger.warning("Parent chunk has no type, assuming %s", child_type)

# ERROR : Erreurs de validation
logger.error("Validation failed: %s", error.message)
```

### 8.2 Fichiers de log

```
output_dir/
└── session_name/
    ├── errors.json       # Erreurs de validation
    ├── resolution.log    # Log résolution (DEBUG)
    └── generation.log    # Log génération
```

---

## 9. Métriques de succès

### 9.1 Critères techniques

- ✅ Tous les tests passent (V1 + V2)
- ✅ Coverage > 90%
- ✅ Aucune régression V1
- ✅ Validation collecte toutes erreurs
- ✅ Performance acceptable (<100ms pour résolution)

### 9.2 Critères fonctionnels

- ✅ Héritage multi-niveaux fonctionne
- ✅ Chunks réutilisables
- ✅ Sélecteurs avancés opérationnels
- ✅ Validation stricte détecte erreurs
- ✅ Exemples réels génèrent images

---

## 10. Next steps

### 10.1 Après V2.0

**Features futures :**
- Scénarios (type `story` avec orchestration multi-prompts)
- Conditions (`if:` dans templates)
- Variables utilisateur (`{user.favorite_color}`)
- Templates de templates (meta-templates)

### 10.2 Maintenance

**Dépréciation V1.x :**
- V2.0 Release : V1 toujours supporté (mode legacy)
- V2.1+ : Warning si utilisation V1
- V3.0 : Suppression V1 (migration obligatoire)

---

**Fin du document d'architecture**

**Prochaine étape :** Voir `template-system-v2-retrocompat.md` pour détails rétrocompatibilité
