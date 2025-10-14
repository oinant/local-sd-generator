# CLI Technical Documentation

**Documentation technique pour développeurs et contributeurs.**

---

## 📚 Documents disponibles

### 🏗️ [Architecture](architecture.md)
**Vue d'ensemble du système V2.0**

Comprendre l'architecture modulaire du Template System V2.0 :
- Structure des modules (models, loaders, validators, resolvers, generators)
- V2Pipeline orchestrator (5 phases : Load → Validate → Resolve → Generate → Normalize)
- Patterns architecturaux (Strategy, Pipeline, Dependency Injection)
- Integration avec l'API Stable Diffusion
- Performance et optimisations

**📖 Durée de lecture:** 20-30 minutes

**👥 Audience:** Développeurs, contributeurs, reviewers

---

### 📋 [Template System Spec](template-system-spec.md)
**Spécification complète du système de templating V2.0**

Documentation exhaustive de toutes les fonctionnalités :
- Format des fichiers `.prompt.yaml`
- Système d'imports (fichiers YAML, strings inline, multi-imports)
- Héritage avec `implements:` (multi-niveau)
- Chunks réutilisables avec `chunks:`
- Sélecteurs avancés (`[random:N]`, `[#i,j,k]`, `[keys:a,b]`, `[#i-j]`)
- Weight system pour contrôle de l'ordre des boucles
- Modes de génération (combinatorial, random)
- Modes de seed (fixed, progressive, random)
- Exemples complets et cas d'usage

**📖 Durée de lecture:** 45-60 minutes

**👥 Audience:** Développeurs, power users, intégrateurs

---

### ⚙️ [YAML Templating System](yaml-templating-system.md)
**Guide technique détaillé et référence d'implémentation**

Documentation du système en production :
- Historique (Phase 1 → Phase 2 → V2.0)
- Module structure détaillée
- Test coverage (306 tests, 98% pass rate)
- File formats (`.prompt.yaml`, `.yaml` variations)
- CLI usage et commandes
- Output structure (manifests, metadata)
- Resolution flow (6 SRP functions)
- Migration depuis legacy (Phase 1)
- Best practices et troubleshooting
- API introspection (samplers, schedulers, models)

**📖 Durée de lecture:** 30-40 minutes

**👥 Audience:** Développeurs, mainteneurs, DevOps

---

## 🗺️ Navigation rapide

### Par sujet

**Architecture et design :**
- [Architecture overview](architecture.md) - Structure modulaire et patterns
- [Template System Spec](template-system-spec.md) - Spec fonctionnelle complète

**Implémentation et production :**
- [YAML Templating System](yaml-templating-system.md) - Guide technique détaillé
- [Test Coverage](yaml-templating-system.md#test-coverage) - 306 tests
- [CLI Commands](yaml-templating-system.md#cli-commands) - Toutes les commandes

**Performance et optimisation :**
- [Performance metrics](architecture.md#performance) - Temps d'exécution
- [Optimizations](architecture.md#optimisations) - Lazy loading, caching, streaming

**Évolution et roadmap :**
- [Roadmap technique](architecture.md#évolution-future) - Prochaines features
- [Migration guide](yaml-templating-system.md#migration-from-legacy-phase-1) - Legacy → V2.0

### Par rôle

**👨‍💻 Développeur qui rejoint le projet :**
1. [Architecture](architecture.md) - Comprendre la structure (20 min)
2. [YAML Templating System](yaml-templating-system.md) - Détails d'implémentation (30 min)
3. [Template System Spec](template-system-spec.md) - Features complètes (45 min)

**🔧 Mainteneur / DevOps :**
1. [YAML Templating System](yaml-templating-system.md) - Production guide (30 min)
2. [Architecture - Performance](architecture.md#performance) - Métriques (5 min)
3. [CLI Commands](yaml-templating-system.md#cli-commands) - Référence rapide (5 min)

**📝 Contributeur (nouvelle feature) :**
1. [Architecture - Patterns](architecture.md#patterns-architecturaux) - Principes de design (10 min)
2. [Template System Spec](template-system-spec.md) - Features existantes (45 min)
3. [Test Coverage](yaml-templating-system.md#test-coverage) - Stratégie de tests (5 min)

**🐛 Débugger un problème :**
1. [Architecture - Flux d'exécution](architecture.md#flux-dexécution-complet) - Comprendre le flow (10 min)
2. [YAML Templating System - Troubleshooting](yaml-templating-system.md#troubleshooting) - Problèmes courants (5 min)
3. [Test Coverage](yaml-templating-system.md#test-coverage) - Vérifier les tests (5 min)

---

## 📊 Statistiques du projet

**Version actuelle:** V2.0 (stable, production)

**Code :**
- Modules : 7 (models, loaders, validators, resolvers, generators, normalizers, utils)
- Fichiers Python : ~40
- Lignes de code : ~8000
- Complexité : Moyenne A-B (simple à modéré)

**Tests :**
- Total : 306 tests
- Pass rate : 98%
- Coverage : 96.5%
- Temps d'exécution : ~15s

**Documentation :**
- Guide utilisateur : 8 fichiers (~3500 lignes)
- Documentation technique : 3 fichiers (~1500 lignes)
- Exemples : 20+ templates complets

---

## 🛠️ Outils de développement

### Lancement des tests

```bash
# Activer le venv
source venv/bin/activate
cd CLI

# Tests V2 complets (227 tests)
python3 -m pytest tests/v2/ -v

# Tests API client (76 tests)
python3 -m pytest tests/api/ -v

# Tous les tests (sans legacy)
python3 -m pytest tests/ --ignore=tests/legacy -v

# Avec couverture
python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing -v
```

### Code quality

```bash
# Style checking (PEP 8)
python3 -m flake8 CLI/ --exclude=tests,private_generators --max-line-length=120

# Complexité cyclomatique
python3 -m radon cc CLI/ --exclude="tests,private_generators" -a -nb

# Code mort
python3 -m vulture CLI/ --min-confidence=80

# Sécurité
python3 -m bandit -r CLI/ -ll -f txt
```

### Analyse de performance

```bash
# Profiling d'un template
python3 -m cProfile -o profile.stats src/cli.py generate -t template.yaml
python3 -m pstats profile.stats

# Memory profiling
python3 -m memory_profiler src/cli.py generate -t template.yaml
```

---

## 🔗 Liens externes

**Repositories :**
- [GitHub Project](https://github.com/user/local-sd-generator) (si public)
- [Issues & Bugs](https://github.com/user/local-sd-generator/issues)

**Références SD :**
- [Stable Diffusion WebUI API](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)
- [SD Parameters Guide](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features)

**Python & Tools :**
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Pytest Documentation](https://docs.pytest.org/)
- [Typer CLI Framework](https://typer.tiangolo.com/)

---

## 🤝 Contribution

### Code review

Avant de contribuer, consulter :
- [Code Review Guidelines](../../tooling/CODE_REVIEW_GUIDELINES.md)
- [Code Review Action Templates](../../tooling/CODE_REVIEW_ACTION_TEMPLATES.md)

### Process de développement

1. **Créer une spec dans roadmap/wip/**
2. **Développer avec tests** (TDD recommandé)
3. **Code review** (guidelines + automated tools)
4. **Documenter** (usage + technical)
5. **Déplacer spec dans roadmap/done/**

---

## 📖 Autres documentations

### Documentation utilisateur
- **[User Guide](../guide/README.md)** - Apprentissage progressif (2h)
- **[Getting Started](../guide/getting-started.md)** - Première génération (10 min)
- **[Templates Advanced](../guide/4-templates-advanced.md)** - Features avancées (20 min)
- **[Examples](../guide/examples.md)** - Cas d'usage complets (15 min)
- **[Troubleshooting](../guide/troubleshooting.md)** - Problèmes courants (10 min)

### Documentation référence (usage/)
- **[Getting Started (Usage)](../usage/getting-started.md)** - Quick reference
- **[Examples (Usage)](../usage/examples.md)** - 10 patterns complets
- **[Variation Files](../usage/variation-files.md)** - Format des fichiers

### Roadmap
- **[Roadmap Overview](../../roadmap/README.md)** - État du projet
- **[Done Features](../../roadmap/done/)** - Terminé et déployé
- **[Next Sprint](../../roadmap/next/)** - Prochaines tâches
- **[Future Backlog](../../roadmap/future/)** - Long terme

---

**Dernière mise à jour:** 2025-10-14
**Mainteneur:** Active development
**Questions?** Ouvrir une issue sur GitHub
