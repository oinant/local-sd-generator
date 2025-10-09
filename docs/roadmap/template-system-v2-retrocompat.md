# Template System V2.0 - Rétrocompatibilité V1.x ↔ V2.0

**Version:** 2.0.0
**Date:** 2025-10-09
**Status:** Draft - Ready for Implementation

---

## 1. Vue d'ensemble

### 1.1 Objectifs de la rétrocompatibilité

Le système doit permettre la **cohabitation** de fichiers V1.x et V2.0 dans le même projet sans :
- ❌ Régression sur les prompts existants V1.x
- ❌ Migration forcée des fichiers utilisateur
- ❌ Changement du comportement par défaut

**Principe :** Détection automatique de version → Routage vers le bon système

### 1.2 Stratégie

```
┌─────────────────────────────────────────────────────────┐
│  Projet utilisateur                                     │
│                                                         │
│  /prompts/                                              │
│    ├── old_prompt_v1.yaml  (version: 1.2.0) ──┐        │
│    ├── new_prompt_v2.yaml  (version: 2.0)   ──┼──┐     │
│    └── legacy_no_version.yaml (pas de version)┘  │     │
│                                                   │     │
└───────────────────────────────────────────────────┼─────┘
                                                    │
                    ┌───────────────────────────────┴──────────────────┐
                    │        Version Router                            │
                    │     (detect_version())                           │
                    └───────────────────┬──────────────────────────────┘
                                        │
                    ┌───────────────────┴──────────────────┐
                    │                                      │
         ┌──────────▼──────────┐              ┌───────────▼──────────┐
         │  V1.x System        │              │  V2.0 System         │
         │  (Legacy)           │              │  (New)               │
         │                     │              │                      │
         │  templating/v1/     │              │  templating/v2/      │
         │  - resolver.py      │              │  - loaders/          │
         │  - variation_loader │              │  - validators/       │
         │                     │              │  - resolvers/        │
         └─────────────────────┘              └──────────────────────┘
                    │                                      │
                    └──────────────┬───────────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  Generation Engine  │
                        │  (Unified)          │
                        └─────────────────────┘
```

---

## 2. Détection de version

### 2.1 Règles de détection

```python
def detect_version(config: dict) -> Version:
    """
    Détecte la version d'un fichier de configuration.

    Règles:
    1. Si version: '1.x.x' → V1 (Legacy)
    2. Si version: '2.x.x' → V2 (New)
    3. Si pas de version: → V1 (Legacy) + Warning

    Returns:
        Version enum (V1 | V2)

    Raises:
        ValueError: Si version non supportée (ex: 3.0.0)
    """
    version = config.get('version', '1.0.0')

    if version.startswith('1.'):
        return Version.V1
    elif version.startswith('2.'):
        return Version.V2
    else:
        raise ValueError(
            f"Unsupported version: {version}. "
            f"Supported versions: 1.x.x (legacy), 2.x.x (new)"
        )
```

### 2.2 Cas spéciaux

#### Fichier sans version

```yaml
# old_prompt.yaml (pas de champ version:)
name: 'OldPrompt'
template: 'masterpiece, 1girl, beautiful'
```

**Comportement :**
- Assume **V1.0.0** (legacy)
- ⚠️ **Warning** dans les logs :
  ```
  WARNING: old_prompt.yaml has no 'version' field, assuming v1.0.0 (legacy mode).
  Consider adding 'version: 1.0.0' to silence this warning.
  ```

#### Version invalide

```yaml
version: '3.0.0'
name: 'FuturePrompt'
```

**Comportement :**
- ❌ **Erreur** immédiate :
  ```
  ERROR: Unsupported version: 3.0.0
  Supported versions: 1.x.x (legacy), 2.x.x (new)
  ```

### 2.3 Code de détection

```python
# CLI/src/templating/version_router.py

from enum import Enum
from pathlib import Path
import yaml


class Version(Enum):
    """Versions supportées du système de templates."""
    V1 = "1.x"
    V2 = "2.x"


class VersionRouter:
    """Routage vers V1 ou V2 selon version détectée."""

    def __init__(self):
        self._v1_system = None
        self._v2_system = None

    def load_prompt_config(self, path: Path):
        """
        Point d'entrée unifié.

        Args:
            path: Chemin vers le fichier .prompt.yaml

        Returns:
            PromptConfig (V1 ou V2)

        Raises:
            ValueError: Si version non supportée
            FileNotFoundError: Si fichier introuvable
        """
        # Load raw YAML
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Detect version
        version = self.detect_version(data, path)

        # Route to appropriate system
        if version == Version.V1:
            return self._load_v1(path, data)
        else:
            return self._load_v2(path, data)

    def detect_version(self, data: dict, path: Path) -> Version:
        """Détecte la version du fichier."""
        version_str = data.get('version', None)

        if version_str is None:
            # Pas de version → V1 + Warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"{path.name} has no 'version' field, assuming v1.0.0 (legacy mode). "
                f"Consider adding 'version: 1.0.0' to silence this warning."
            )
            return Version.V1

        # Parse version
        if version_str.startswith('1.'):
            return Version.V1
        elif version_str.startswith('2.'):
            return Version.V2
        else:
            raise ValueError(
                f"Unsupported version: {version_str} in {path}. "
                f"Supported versions: 1.x.x (legacy), 2.x.x (new)"
            )

    def _load_v1(self, path: Path, data: dict):
        """Charge avec système V1 (legacy)."""
        if self._v1_system is None:
            from .v1.resolver import LegacyPromptResolver
            self._v1_system = LegacyPromptResolver()

        return self._v1_system.load(path, data)

    def _load_v2(self, path: Path, data: dict):
        """Charge avec système V2 (new)."""
        if self._v2_system is None:
            from .v2 import V2System
            self._v2_system = V2System()

        return self._v2_system.load(path, data)
```

---

## 3. Cohabitation dans le codebase

### 3.1 Structure des dossiers (après migration)

```
CLI/src/templating/
├── __init__.py                   # Exports publics (VersionRouter)
├── version_router.py             # Point d'entrée unifié
│
├── v1/                           # Legacy system (V1.x)
│   ├── __init__.py
│   ├── resolver.py               # Ancien resolver.py (renommé)
│   ├── variation_loader.py       # Ancien variation_loader.py
│   ├── prompt_config.py          # Ancien prompt_config.py
│   └── README.md                 # "Legacy V1.x - Deprecated, use V2"
│
├── v2/                           # New system (V2.0)
│   ├── __init__.py               # Exports V2 (V2System)
│   │
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── yaml_loader.py
│   │   └── parser.py
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── validator.py
│   │   └── validation_error.py
│   │
│   ├── resolvers/
│   │   ├── __init__.py
│   │   ├── inheritance_resolver.py
│   │   ├── import_resolver.py
│   │   └── template_resolver.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config_models.py
│   │   └── context.py
│   │
│   ├── normalizers/
│   │   ├── __init__.py
│   │   └── prompt_normalizer.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── path_utils.py
│   │   ├── hash_utils.py
│   │   └── cache.py
│   │
│   └── system.py                 # V2System (orchestrator)
│
├── shared/                       # Code partagé (si nécessaire)
│   └── constants.py
│
└── tests/
    ├── v1/                       # Tests legacy (existants)
    │   ├── test_resolver.py
    │   └── test_variation_loader.py
    │
    └── v2/                       # Nouveaux tests V2
        ├── unit/
        └── integration/
```

### 3.2 Migration du code existant

**Étape 1 : Créer structure v1/**
```bash
cd CLI/src/templating
mkdir v1
git mv resolver.py v1/resolver.py
git mv variation_loader.py v1/variation_loader.py
# Créer v1/__init__.py avec exports
```

**Étape 2 : Créer structure v2/**
```bash
mkdir -p v2/{loaders,validators,resolvers,models,normalizers,utils}
# Créer tous les __init__.py
```

**Étape 3 : Créer version_router.py**
```bash
# Créer le router (code ci-dessus)
```

**Étape 4 : Mettre à jour les imports**
```python
# Avant (ancien code)
from templating.resolver import resolve_prompt

# Après (nouveau code)
from templating import VersionRouter
router = VersionRouter()
config = router.load_prompt_config(path)
```

### 3.3 Points d'entrée

#### CLI (template_cli.py)

```python
# CLI/template_cli.py (ou sdgen command)

from templating import VersionRouter

def generate_command(prompt_file: str, ...):
    """Commande generate (unifiée V1/V2)."""
    router = VersionRouter()

    # Chargement automatique V1 ou V2
    config = router.load_prompt_config(Path(prompt_file))

    # Le reste du code reste identique
    # (config est compatible V1/V2)
    ...
```

#### prompt_config.py

**Option A : Refactoring (recommandé)**
```python
# CLI/src/templating/prompt_config.py

from .version_router import VersionRouter

def load_prompt_config(path: Path):
    """Point d'entrée unifié."""
    router = VersionRouter()
    return router.load_prompt_config(path)
```

**Option B : Wrapper (temporaire)**
```python
# Garder ancien code pour V1
# Ajouter nouveau code pour V2
# Router selon version
```

---

## 4. Interface commune (abstraction)

### 4.1 Problème

V1 et V2 retournent des structures différentes :
- V1 : `dict` ou objet custom
- V2 : `PromptConfig` (dataclass)

**Solution :** Adaptateur pour uniformiser

### 4.2 Adaptateur V1 → Interface commune

```python
# CLI/src/templating/v1/adapter.py

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class V1PromptConfig:
    """Adaptateur pour V1 → interface commune."""
    version: str = "1.0.0"
    name: str = ""
    template: str = ""
    variations: Dict[str, list] = None
    parameters: Dict[str, Any] = None
    generation: Dict[str, Any] = None

    @classmethod
    def from_v1_dict(cls, data: dict):
        """Convertit dict V1 → V1PromptConfig."""
        return cls(
            name=data.get('name', 'Unnamed'),
            template=data.get('prompt_template', ''),
            variations=data.get('variations', {}),
            parameters=data.get('parameters', {}),
            generation=data.get('generation', {})
        )
```

### 4.3 Interface unifiée

```python
# CLI/src/templating/interfaces.py

from typing import Protocol, Dict, Any

class PromptConfigProtocol(Protocol):
    """Interface commune V1/V2."""
    version: str
    name: str
    template: str
    parameters: Dict[str, Any]
    generation: Dict[str, Any]

# V1PromptConfig et V2PromptConfig implémentent ce protocol
```

---

## 5. Tests de non-régression

### 5.1 Stratégie

**Objectif :** Garantir que TOUS les tests V1 existants passent toujours

**Approche :**
1. Copier tous les tests V1 actuels dans `tests/v1/`
2. Les exécuter avec le nouveau router
3. Vérifier : **0 régression**

### 5.2 Tests de compatibilité

```python
# CLI/tests/integration/test_v1_compatibility.py

import pytest
from pathlib import Path
from templating import VersionRouter


class TestV1Compatibility:
    """Tests de non-régression V1."""

    @pytest.fixture
    def router(self):
        return VersionRouter()

    def test_v1_prompt_without_version_loads(self, router, tmp_path):
        """Fichier V1 sans version doit charger en mode legacy."""
        prompt_file = tmp_path / "old_prompt.yaml"
        prompt_file.write_text("""
name: 'OldPrompt'
prompt_template: 'masterpiece, 1girl'
variations:
  Angle: angles.txt
""")

        # Doit charger sans erreur
        config = router.load_prompt_config(prompt_file)
        assert config is not None
        assert config.version.startswith('1.')

    def test_v1_with_explicit_version_loads(self, router, tmp_path):
        """Fichier V1 avec version explicite."""
        prompt_file = tmp_path / "v1_prompt.yaml"
        prompt_file.write_text("""
version: '1.2.0'
name: 'V1Prompt'
prompt_template: 'masterpiece, 1girl'
""")

        config = router.load_prompt_config(prompt_file)
        assert config.version == '1.2.0'

    def test_all_existing_v1_prompts_still_work(self, router):
        """Tous les prompts V1 existants doivent toujours fonctionner."""
        # Charger tous les fichiers .yaml de test V1
        v1_test_dir = Path(__file__).parent.parent / 'v1' / 'fixtures'

        if not v1_test_dir.exists():
            pytest.skip("No V1 fixtures found")

        for prompt_file in v1_test_dir.glob('**/*.yaml'):
            # Doit charger sans erreur
            config = router.load_prompt_config(prompt_file)
            assert config is not None
```

### 5.3 Tests mixtes (V1 + V2)

```python
# CLI/tests/integration/test_mixed_versions.py

def test_project_with_v1_and_v2_prompts(router):
    """Projet avec prompts V1 et V2 dans le même dossier."""
    # Créer structure
    # /prompts/
    #   ├── old_v1.yaml (version: 1.0)
    #   └── new_v2.yaml (version: 2.0)

    # Les deux doivent charger correctement
    v1_config = router.load_prompt_config(Path('prompts/old_v1.yaml'))
    v2_config = router.load_prompt_config(Path('prompts/new_v2.yaml'))

    assert v1_config.version.startswith('1.')
    assert v2_config.version.startswith('2.')
```

---

## 6. Migration utilisateur (optionnel)

### 6.1 Guide de migration

**Pour les utilisateurs qui VEULENT migrer V1 → V2**

#### Étape 1 : Identifier les fichiers V1

```bash
# Lister tous les prompts sans version ou avec version: 1.x
grep -L "version:" prompts/*.yaml
grep "version: 1\." prompts/*.yaml
```

#### Étape 2 : Ajouter `version: 1.0.0` (silence warnings)

```yaml
# Avant
name: 'OldPrompt'
prompt_template: 'masterpiece'

# Après
version: '1.0.0'  # Ajout
name: 'OldPrompt'
prompt_template: 'masterpiece'
```

#### Étape 3 : Migration manuelle V1 → V2 (si souhaité)

**Mapping des concepts :**

| V1 | V2 |
|----|-----|
| `prompt_template` | `template` |
| `variations:` (fichiers txt) | `imports:` (fichiers .yaml dict) |
| Pas d'héritage | `implements:` |
| Placeholders `{Name:N}` | `{Name[N]}` |
| Pas de chunks | `@Chunk` syntax |

**Exemple de conversion :**

```yaml
# V1
version: '1.0.0'
name: 'Portrait'
prompt_template: 'masterpiece, 1girl, {Angle}, {Expression:15}'
variations:
  Angle: variations/angles.txt
  Expression: variations/expressions.txt
parameters:
  width: 832
  height: 1216
```

```yaml
# V2 (équivalent)
version: '2.0'
name: 'Portrait'
implements: '../templates/base.template.yaml'

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 100

imports:
  Angle: ../variations/angles.yaml      # Convertir .txt → .yaml dict
  Expression: ../variations/expressions.yaml

template: |
  masterpiece, 1girl,
  {Angle},
  {Expression[15]}
```

### 6.2 Outil de migration (optionnel, futur)

```bash
# Commande future (V2.1+)
sdgen migrate prompt.v1.yaml --to=2.0 --output=prompt.v2.yaml
```

**Fonctionnalités :**
- Convertir `prompt_template` → `template`
- Convertir variations `.txt` → `.yaml` dict
- Ajouter structure `generation:`
- Créer template parent si paramètres communs

---

## 7. Workflow de développement

### 7.1 Développement V2 (nouveau code)

```bash
# Créer une nouvelle feature V2
cd CLI/src/templating/v2

# Créer module
touch resolvers/my_new_feature.py

# Tests
cd ../../../../tests/v2/unit
touch test_my_new_feature.py

# Run tests V2 seulement
pytest tests/v2/
```

### 7.2 Bugfix V1 (legacy)

```bash
# Si bug trouvé dans V1
cd CLI/src/templating/v1

# Fix dans resolver.py ou variation_loader.py

# Tests
pytest tests/v1/

# Vérifier non-régression
pytest tests/integration/test_v1_compatibility.py
```

### 7.3 CI/CD

```yaml
# .github/workflows/test.yml

jobs:
  test-v1-legacy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run V1 legacy tests
        run: pytest CLI/tests/v1/

  test-v2-new:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run V2 tests
        run: pytest CLI/tests/v2/

  test-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests (V1 + V2)
        run: pytest CLI/tests/integration/
```

---

## 8. Dépréciation V1 (timeline)

### 8.1 Phases de dépréciation

**Phase 1 : V2.0 Release (Maintenant)**
- ✅ V1 totalement supporté (mode legacy)
- ✅ V2 disponible pour early adopters
- ℹ️ Documentation encourage V2 pour nouveaux projets

**Phase 2 : V2.1 - V2.5 (6-12 mois)**
- ⚠️ Warning si utilisation V1 :
  ```
  WARNING: You are using V1 (legacy) format. Consider migrating to V2.
  V1 will be deprecated in version 3.0.
  See: https://docs.sdgen.com/migration-v1-v2
  ```
- ✅ V1 toujours fonctionnel
- 📚 Guide de migration publié

**Phase 3 : V3.0 (12-18 mois)**
- ❌ V1 supprimé du code
- 🚫 Fichiers V1 rejettent avec erreur :
  ```
  ERROR: V1 format is no longer supported as of v3.0.
  Please migrate to V2 format.
  Migration guide: https://docs.sdgen.com/migration-v1-v2
  ```
- 🛠️ Outil de migration automatique fourni

### 8.2 Metrics pour décision

**Avant dépréciation V1, vérifier :**
- Adoption V2 : > 80% des nouveaux fichiers utilisent V2
- Migration : > 50% des fichiers existants migrés
- Feedback : Pas de blockers majeurs rapportés

---

## 9. Documentation utilisateur

### 9.1 README principal

```markdown
# Template System

## Versions

Le système de templates supporte 2 versions :

### V1.x (Legacy)
Format historique. **Toujours supporté** mais déprécié.
- Simple, basique
- Pas d'héritage, pas de chunks
- Voir `/docs/v1/` pour documentation

### V2.0+ (Recommended)
Nouveau format avec features avancées.
- Héritage (`implements:`)
- Chunks réutilisables (`@Chunk`)
- Sélecteurs avancés (`[selectors]`)
- Validation stricte
- Voir `/docs/v2/` pour documentation

## Quelle version utiliser ?

**Nouveaux projets** : Utilisez V2.0
**Projets existants** : Pas besoin de migrer (V1 reste supporté)
**Migration** : Optionnelle, voir guide de migration
```

### 9.2 Message de bienvenue (CLI)

```
$ sdgen --version
sdgen 2.0.0

Template System:
  - V1.x (legacy): Supported
  - V2.0 (new): Recommended for new projects

For migration guide: sdgen docs --migration
```

---

## 10. Checklist de validation

### 10.1 Avant merge V2

- [ ] ✅ Tous les tests V1 passent (100% sans régression)
- [ ] ✅ Tests de compatibilité V1/V2 passent
- [ ] ✅ VersionRouter détecte correctement versions
- [ ] ✅ Warning si pas de version (legacy assume)
- [ ] ✅ Erreur si version non supportée
- [ ] ✅ Documentation mise à jour (README, guides)
- [ ] ✅ CI/CD configure pour tester V1 + V2

### 10.2 Post-release V2.0

- [ ] Monitoring adoption V2 (metrics)
- [ ] Feedback utilisateurs (GitHub issues)
- [ ] Bugfixes V1 si nécessaire (legacy support)
- [ ] Amélioration continue V2

---

## 11. Résolution de problèmes

### 11.1 "Mon ancien prompt ne marche plus"

**Diagnostic :**
1. Vérifier que le fichier a `version: 1.x.x` ou pas de version
2. Vérifier que `v1/resolver.py` existe bien
3. Vérifier logs : doit afficher "Loading with V1 (legacy)"

**Solution :**
- Si version manquante : Ajouter `version: 1.0.0` pour silence warning
- Si erreur : Vérifier que migration V1 → v1/ a été faite correctement

### 11.2 "Je veux tester V2 sans casser mes prompts V1"

**Solution :**
1. Créer nouveau fichier `test_v2.prompt.yaml` avec `version: 2.0`
2. Tester avec `sdgen generate test_v2.prompt.yaml`
3. Les anciens prompts V1 continuent de fonctionner normalement

### 11.3 "Comment migrer progressivement ?"

**Approche recommandée :**
1. **Phase 1** : Ajouter `version: 1.0.0` à tous les fichiers existants
2. **Phase 2** : Créer templates V2 pour nouveaux prompts
3. **Phase 3** : Migrer fichiers V1 un par un (optionnel)

---

## 12. Code example complet

### 12.1 Version Router (complet)

```python
# CLI/src/templating/version_router.py

from enum import Enum
from pathlib import Path
from typing import Union
import yaml
import logging

logger = logging.getLogger(__name__)


class Version(Enum):
    V1 = "1.x"
    V2 = "2.x"


class VersionRouter:
    """Routage automatique V1/V2 selon version détectée."""

    def __init__(self):
        self._v1_system = None
        self._v2_system = None

    def load_prompt_config(self, path: Path):
        """Point d'entrée unifié."""
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        version = self.detect_version(data, path)

        logger.info(f"Loading {path.name} with {version.value} system")

        if version == Version.V1:
            return self._load_v1(path, data)
        else:
            return self._load_v2(path, data)

    def detect_version(self, data: dict, path: Path) -> Version:
        """Détecte version du fichier."""
        version_str = data.get('version', None)

        if version_str is None:
            logger.warning(
                f"{path.name} has no 'version' field, "
                f"assuming v1.0.0 (legacy mode). "
                f"Add 'version: 1.0.0' to silence this warning."
            )
            return Version.V1

        if version_str.startswith('1.'):
            return Version.V1
        elif version_str.startswith('2.'):
            return Version.V2
        else:
            raise ValueError(
                f"Unsupported version: {version_str} in {path}. "
                f"Supported: 1.x.x (legacy), 2.x.x (new)"
            )

    def _load_v1(self, path: Path, data: dict):
        """Charge avec V1 (lazy loading)."""
        if self._v1_system is None:
            from .v1.resolver import LegacyPromptResolver
            self._v1_system = LegacyPromptResolver()

        return self._v1_system.load(path, data)

    def _load_v2(self, path: Path, data: dict):
        """Charge avec V2 (lazy loading)."""
        if self._v2_system is None:
            from .v2.system import V2System
            self._v2_system = V2System()

        return self._v2_system.load(path, data)
```

### 12.2 Utilisation dans CLI

```python
# CLI/template_cli.py

from templating import VersionRouter
from pathlib import Path

def generate(prompt_file: str, **kwargs):
    """Commande generate (V1/V2 unifié)."""
    router = VersionRouter()

    # Chargement automatique
    config = router.load_prompt_config(Path(prompt_file))

    # Le reste est identique (V1/V2 compatible)
    # ...
```

---

**Fin du document de rétrocompatibilité**

**Documentation complète terminée ! 🎉**

**3 documents créés :**
1. ✅ `template-system-v2-spec.md` (860 lignes) - Spec technique formelle
2. ✅ `template-system-v2-architecture.md` (1000+ lignes) - Architecture & implémentation
3. ✅ `template-system-v2-retrocompat.md` (600+ lignes) - Rétrocompatibilité V1/V2

**Prêt pour l'implémentation ! 🚀**
