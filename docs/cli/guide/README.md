# Guide Utilisateur CLI

Bienvenue dans le guide d'utilisation du **CLI de génération d'images Stable Diffusion** !

Ce guide vous accompagne de vos premières générations jusqu'à la maîtrise complète du système de templating V2.0.

---

## 📚 Parcours d'apprentissage

### 🆕 Débutant

**Objectif** : Générer vos premières images et comprendre les bases

1. **[Getting Started](./getting-started.md)** ⏱️ 10 min
   - Installation et configuration
   - Votre premier template
   - Comprendre les résultats

2. **[Prompting Standalone](./1-prompting-standalone.md)** ⏱️ 10 min
   - Générer avec un prompt fixe
   - Paramètres Stable Diffusion (résolution, steps, cfg_scale, sampler)
   - Modes de seed (fixed, progressive, random)
   - Manifest.json et reproductibilité

3. **[Placeholders & Variations](./2-placeholders-variations.md)** ⏱️ 10 min
   - Concept de placeholder (`{Expression}`)
   - Fichiers de variations
   - Génération automatique de combinaisons
   - Éviter la duplication de code

**Durée totale : 30 minutes**
**Résultat : Vous savez générer des images avec variations**

---

### 🔄 Intermédiaire

**Objectif** : Maîtriser les multi-variations et l'organisation

4. **[Template Basics](./3-templates-basics.md)** ⏱️ 15 min
   - Multi-variations (plusieurs placeholders)
   - Calcul des combinaisons
   - Modes combinatorial vs random
   - Organisation de projet
   - Bonnes pratiques

**Durée : 15 minutes**
**Résultat : Vous gérez des projets complexes avec des centaines d'images**

---

### 🚀 Avancé

**Objectif** : Contrôle total avec les features avancées

5. **[Templates Advanced](./4-templates-advanced.md)** ⏱️ 20 min
   - **Sélecteurs** : Limiter et choisir des variations (`[N]`, `[#i,j]`, `[key1,key2]`)
   - **Héritage** : Réutiliser des configurations (`implements:`)
   - **Chunks** : Composition de prompts complexes
   - **Listes d'imports** : Combiner plusieurs fichiers

**Durée : 20 minutes**
**Résultat : Vous maîtrisez toutes les fonctionnalités du système**

---

### 💡 Pratique

**Objectif** : Appliquer vos connaissances à des cas réels

6. **[Examples & Use Cases](./examples.md)** ⏱️ 15 min
   - Entraînement de LoRA (500 images)
   - Exploration créative (génération aléatoire)
   - Production de variantes (contrôle précis)
   - Tests rapides
   - Character consistency
   - A/B Testing

**Durée : 15 minutes**
**Résultat : Exemples complets prêts à utiliser**

---

### 🔧 Dépannage

**Objectif** : Résoudre les problèmes courants

7. **[Troubleshooting](./troubleshooting.md)** ⏱️ 10 min
   - Problèmes de génération
   - Erreurs de validation
   - Problèmes de configuration
   - FAQ

**Durée : 10 minutes**
**Résultat : Solutions aux erreurs courantes**

---

## 🎯 Progression recommandée

### Parcours rapide (1 heure)

Pour une prise en main rapide :

1. [Getting Started](./getting-started.md) - 10 min
2. [Placeholders & Variations](./2-placeholders-variations.md) - 10 min
3. [Examples](./examples.md) - 15 min (copier un exemple)
4. Générer vos premières images ! 🎉

### Parcours complet (2 heures)

Pour une maîtrise complète :

1. [Getting Started](./getting-started.md)
2. [Prompting Standalone](./1-prompting-standalone.md)
3. [Placeholders & Variations](./2-placeholders-variations.md)
4. [Template Basics](./3-templates-basics.md)
5. [Templates Advanced](./4-templates-advanced.md)
6. [Examples](./examples.md)
7. [Troubleshooting](./troubleshooting.md) (référence)

---

## 📖 Guides par thème

### Concepts fondamentaux
- [Prompting Standalone](./1-prompting-standalone.md) - Prompts fixes et paramètres SD
- [Placeholders & Variations](./2-placeholders-variations.md) - Variations automatiques
- [Template Basics](./3-templates-basics.md) - Multi-variations

### Features avancées
- [Templates Advanced - Sélecteurs](./4-templates-advanced.md#sélecteurs--choisir-vos-variations) - Contrôle des variations
- [Templates Advanced - Héritage](./4-templates-advanced.md#héritage-de-templates) - Réutilisation
- [Templates Advanced - Listes d'imports](./4-templates-advanced.md#listes-dimports--combiner-plusieurs-fichiers) - Merge de fichiers

### Cas d'usage
- [LoRA Training](./examples.md#cas-1--entraînement-de-lora) - Dataset exhaustif
- [Creative Exploration](./examples.md#cas-2--exploration-créative) - Génération aléatoire
- [Variants Production](./examples.md#cas-3--production-de-variantes) - Contrôle précis

### Résolution de problèmes
- [Une seule image générée](./troubleshooting.md#-une-seule-image-générée-au-lieu-de-plusieurs)
- [Trop d'images](./troubleshooting.md#-trop-dimages-générées-explosion-combinatoire)
- [Erreurs de validation](./troubleshooting.md#erreurs-de-validation)

---

## 🔗 Ressources complémentaires

### Documentation technique
- **[Architecture V2.0](../../roadmap/template-system-spec.md)** - Spécification technique complète
- **[Error Handling](../technical/error-handling-validation.md)** - Système de validation

### Documentation avancée
- **[Reference](../reference/)** - Référence rapide (à venir)
- **[Technical](../technical/)** - Documentation technique (à venir)

---

## 💬 Besoin d'aide ?

- **Problème technique ?** → [Troubleshooting](./troubleshooting.md)
- **Question sur une fonctionnalité ?** → Cherchez dans les guides ci-dessus
- **Bug ou suggestion ?** → Créer une issue GitHub

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
**Statut** : Documentation complète et à jour

**Bon apprentissage ! 🚀**
