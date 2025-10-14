# CLI Reference Documentation

**Quick reference pour utilisateurs expérimentés.**

---

## 📚 Documents de référence

### 🔧 [Template Syntax](template-syntax.md)
**Référence complète de la syntaxe YAML**

Syntaxe rapide pour créer des templates :
- Structure des fichiers `.prompt.yaml`
- Tous les champs disponibles
- Valeurs par défaut
- Exemples minimaux

**⏱️ Consultation rapide** : 5-10 minutes

---

### 🎯 [Selectors Reference](selectors-reference.md)
**Tous les sélecteurs en un coup d'œil**

Tableau complet des sélecteurs avec syntaxe et exemples :
- `[N]` - Limite
- `[#i,j,k]` - Index
- `[key1,key2]` - Clés
- `[#i-j]` - Range
- `[random:N]` - Random N
- `[weight:W]` - Poids de boucle

**⏱️ Consultation rapide** : 2-3 minutes

---

### 💻 [CLI Commands](cli-commands.md)
**Toutes les commandes disponibles**

Référence complète des commandes CLI :
- `sdgen generate` - Génération
- `sdgen list` - Liste templates
- `sdgen validate` - Validation
- `sdgen init` - Configuration
- `sdgen api` - API introspection
- Options et flags

**⏱️ Consultation rapide** : 5 minutes

---

### 📋 [YAML Schema](yaml-schema.md)
**Schéma complet des fichiers YAML**

Structure formelle de tous les types de fichiers :
- `.prompt.yaml` - Templates de prompts
- `.template.yaml` - Templates réutilisables
- `.yaml` - Fichiers de variations
- Validation schema (types, required, optional)

**⏱️ Consultation rapide** : 10 minutes

---

## 🗺️ Navigation rapide

### Par besoin

**Je cherche une syntaxe spécifique :**
- Placeholder → [Template Syntax](template-syntax.md#placeholders)
- Sélecteur → [Selectors Reference](selectors-reference.md)
- Héritage → [Template Syntax](template-syntax.md#inheritance)
- Import → [Template Syntax](template-syntax.md#imports)

**Je cherche une commande CLI :**
- Générer → [CLI Commands](cli-commands.md#generate)
- Lister → [CLI Commands](cli-commands.md#list)
- Valider → [CLI Commands](cli-commands.md#validate)
- API → [CLI Commands](cli-commands.md#api)

**Je cherche un champ YAML :**
- Paramètres SD → [YAML Schema](yaml-schema.md#parameters)
- Génération → [YAML Schema](yaml-schema.md#generation)
- Output → [YAML Schema](yaml-schema.md#output)
- Imports → [YAML Schema](yaml-schema.md#imports)

**Je cherche des valeurs valides :**
- Modes → [YAML Schema](yaml-schema.md#generation-modes)
- Seed modes → [YAML Schema](yaml-schema.md#seed-modes)
- Samplers → [CLI Commands](cli-commands.md#api-samplers)
- Schedulers → [CLI Commands](cli-commands.md#api-schedulers)

---

## 📖 Autres documentations

### Documentation d'apprentissage
- **[User Guide](../guide/README.md)** - Apprentissage progressif (2h)
- **[Getting Started](../guide/getting-started.md)** - Première génération (10 min)
- **[Templates Advanced](../guide/4-templates-advanced.md)** - Features avancées (20 min)

### Documentation technique
- **[Architecture](../technical/architecture.md)** - Architecture V2.0
- **[Template System Spec](../technical/template-system-spec.md)** - Spécification complète
- **[YAML Templating System](../technical/yaml-templating-system.md)** - Guide technique

---

## 🔍 Format de cette section

Les documents de référence suivent ces principes :

**✅ Concis** - Tableaux, listes, exemples minimaux
**✅ Scannable** - Titres clairs, structure prévisible
**✅ Complet** - Toutes les options, tous les cas
**✅ À jour** - V2.0 uniquement

**❌ Pas d'explication détaillée** - Voir guide/
**❌ Pas de tutoriel** - Voir guide/
**❌ Pas de design rationale** - Voir technical/

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
