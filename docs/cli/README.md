# Documentation CLI

Documentation complète du **CLI de génération d'images Stable Diffusion** avec système de templating V2.0.

---

## 🎯 Quelle documentation pour vous ?

### 🆕 **Vous débutez ?** → [Guide Utilisateur](./guide/)

Guides progressifs pour apprendre le CLI étape par étape.

- ✅ Installation et configuration
- ✅ Premiers templates et générations
- ✅ Placeholders et variations
- ✅ Multi-variations et organisation
- ✅ Features avancées (sélecteurs, héritage)
- ✅ Exemples complets et cas d'usage
- ✅ Troubleshooting

**Parcours complet : 2 heures**

➡️ **[Commencer le guide →](./guide/README.md)**

---

### 🔄 **Vous cherchez une référence rapide ?** → Reference

Syntaxe complète et référence condensée.

- **[Template Syntax](./reference/template-syntax.md)** - Structure YAML et placeholders
- **[Selectors Reference](./reference/selectors-reference.md)** - Tous les sélecteurs en un coup d'œil
- **[CLI Commands](./reference/cli-commands.md)** - Toutes les commandes disponibles
- **[YAML Schema](./reference/yaml-schema.md)** - Schéma formel complet

**Pour recherche rapide (5-10 min par doc)**

➡️ **[Documentation de référence →](./reference/README.md)**

---

### 🔧 **Vous voulez comprendre l'architecture ?** → Technical

Documentation technique et spécifications.

- **[Template System V2.0 Spec](./technical/template-system-spec.md)** - Spécification formelle complète
- **[Error Handling & Validation](./technical/error-handling-validation.md)** - Système de validation
- **[Manifest V2 Format](./technical/manifest_v2_format.md)** - Format manifest.json
- **[Config System](./technical/config-system.md)** - Système de configuration
- **[Output System](./technical/output-system.md)** - Système de sortie
- **[ADetailer Integration](./technical/adetailer.md)** - Intégration ADetailer

**Pour développeurs et mainteneurs**

➡️ **[Documentation technique →](./technical/)**

---

## 📚 Structure de la documentation

```
docs/cli/
│
├── guide/                      # 🆕 APPRENDRE
│   ├── README.md              # Navigation du guide
│   ├── getting-started.md     # Installation (10 min)
│   ├── 1-prompting-standalone.md    # Prompts fixes (10 min)
│   ├── 2-placeholders-variations.md # Variations (10 min)
│   ├── 3-templates-basics.md        # Multi-variations (15 min)
│   ├── 4-templates-advanced.md      # Features avancées (20 min)
│   ├── examples.md            # Cas d'usage (15 min)
│   └── troubleshooting.md     # FAQ & dépannage (10 min)
│
├── reference/                  # 🔄 CHERCHER
│   ├── README.md              # Navigation référence
│   ├── template-syntax.md     # Référence syntaxe
│   ├── selectors-reference.md # Tous les sélecteurs
│   ├── cli-commands.md        # Commandes CLI
│   └── yaml-schema.md         # Schéma YAML
│
└── technical/                  # 🔧 COMPRENDRE
    ├── template-system-spec.md      # Spec V2.0 (roadmap/)
    ├── error-handling-validation.md # Validation
    ├── manifest_v2_format.md        # Format manifest
    ├── config-system.md             # Config
    ├── output-system.md             # Output
    └── adetailer.md                 # ADetailer
```

---

## 🚀 Quick Start

### Installation

```bash
# Depuis la racine du projet
cd /path/to/local-sd-generator/CLI
pip install -e .

# Initialiser la configuration
sdgen init
```

### Premier template

```yaml
# prompts/test.prompt.yaml
version: '2.0'
name: 'Premier Test'

imports:
  Expression: ../variations/expressions.yaml

template: |
  masterpiece, portrait, {Expression}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 5

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

```bash
# Générer
sdgen generate -t prompts/test.prompt.yaml
```

➡️ **[Guide complet →](./guide/getting-started.md)**

---

## 📖 Parcours recommandés

### Parcours débutant (1h)

Pour démarrer rapidement :

1. [Getting Started](./guide/getting-started.md) - 10 min
2. [Placeholders & Variations](./guide/2-placeholders-variations.md) - 10 min
3. [Examples](./guide/examples.md) - Copier un exemple
4. Générer vos premières images ! 🎉

### Parcours complet (2h)

Pour une maîtrise totale :

1. [Getting Started](./guide/getting-started.md)
2. [Prompting Standalone](./guide/1-prompting-standalone.md)
3. [Placeholders & Variations](./guide/2-placeholders-variations.md)
4. [Template Basics](./guide/3-templates-basics.md)
5. [Templates Advanced](./guide/4-templates-advanced.md)
6. [Examples](./guide/examples.md)

### Parcours développeur (3h)

Pour comprendre l'architecture :

1. Parcours complet (2h)
2. [Template System Spec](./technical/template-system-spec.md) - 1h
3. [Architecture technique](./technical/)

---

## 🔗 Liens utiles

### Commandes CLI

```bash
# Générer des images
sdgen generate -t template.yaml

# Lister les templates
sdgen list

# Valider un template
sdgen validate template.yaml

# API introspection
sdgen api samplers
sdgen api models
sdgen api upscalers
```

### Ressources externes

- **[Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)** - Backend API
- **[Stable Diffusion Models](https://civitai.com/)** - Modèles et LoRAs

---

## 💡 Fonctionnalités clés

### Système de templating V2.0

- ✅ **Placeholders** : `{Expression}`, `{Outfit}`, etc.
- ✅ **Sélecteurs** : `[N]`, `[#i,j]`, `[key1,key2]`, `[#i-j]`
- ✅ **Héritage** : `implements:` pour réutiliser des configurations
- ✅ **Chunks** : Composition de prompts complexes
- ✅ **Multi-imports** : Listes de fichiers mergés automatiquement
- ✅ **Modes** : Combinatorial (toutes combinaisons) ou Random (échantillonnage)
- ✅ **Seed modes** : Fixed, Progressive, Random
- ✅ **Validation** : Erreurs claires et détection précoce

### Génération d'images

- ✅ **Manifest V2** : Métadonnées complètes pour reproductibilité
- ✅ **ADetailer** : Amélioration automatique des visages
- ✅ **Hires Fix** : Upscaling haute qualité
- ✅ **Dry-run** : Preview sans générer

---

## 📊 Statistiques

**Version du système** : V2.0
**Tests** : 306 tests (98% pass rate)
**Documentation** : 100% à jour (2025-10-14)
**Guides** : 8 guides progressifs (2h de lecture)

---

## 💬 Support

### Problèmes techniques

➡️ **[Troubleshooting](./guide/troubleshooting.md)**

### Questions sur les fonctionnalités

➡️ Parcourir les [guides](./guide/)

### Bugs et suggestions

➡️ Créer une issue GitHub

---

**Dernière mise à jour** : 2025-10-14
**Version** : V2.0
**Status** : Stable ✅

**Bonne génération ! 🎨**
