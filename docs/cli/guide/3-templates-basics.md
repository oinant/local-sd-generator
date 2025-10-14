# Template Basics

**Maîtrisez les multi-variations et l'organisation de projets complexes.**

📚 **Prérequis** : [Placeholders & Variations](./2-placeholders-variations.md)

⏱️ **Durée de lecture** : 15 minutes

---

## Ce que vous allez apprendre

Dans le guide précédent, vous avez découvert les placeholders et les fichiers de variations. Maintenant, vous allez apprendre à :

- Combiner **plusieurs placeholders** dans un même template
- Calculer et gérer le nombre de combinaisons
- Choisir le bon mode de génération (`combinatorial` vs `random`)
- Maîtriser les modes de seed pour contrôler la reproductibilité
- Organiser vos projets de manière professionnelle

---

## Multi-variations

### Objectif

Utiliser **plusieurs placeholders** pour créer des combinaisons complexes.

### Fichiers de variations

**`variations/expressions.yaml`** (5 variations)
```yaml
happy: smiling, cheerful
sad: crying, melancholic
neutral: calm face
angry: frowning
surprised: wide eyes
```

**`variations/outfits.yaml`** (4 variations)
```yaml
casual: jeans and t-shirt
formal: elegant dress
sporty: athletic wear
fantasy: magical robes
```

**`variations/backgrounds.yaml`** (3 variations)
```yaml
studio: plain studio background
nature: forest background
urban: city street background
```

### Template

**`prompts/portrait_multi.prompt.yaml`**

```yaml
version: '2.0'
name: 'Portrait Multi-Variations'

imports:
  Expression: ../variations/expressions.yaml    # 5 variations
  Outfit: ../variations/outfits.yaml           # 4 variations
  Background: ../variations/backgrounds.yaml    # 3 variations

template: |
  masterpiece, beautiful woman, {Expression}, {Outfit}, {Background}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 2000
  max_images: 60  # 5 × 4 × 3 = 60 combinaisons
```

### Résultat

**60 images** générées (toutes les combinaisons possibles) :

```
Image 1:  Expression=happy,     Outfit=casual,  Background=studio
Image 2:  Expression=happy,     Outfit=casual,  Background=nature
Image 3:  Expression=happy,     Outfit=casual,  Background=urban
Image 4:  Expression=happy,     Outfit=formal,  Background=studio
...
Image 60: Expression=surprised, Outfit=fantasy, Background=urban
```

### Calcul des combinaisons

**Formule** : `Variations_1 × Variations_2 × ... × Variations_N`

```
5 expressions × 4 outfits × 3 backgrounds = 60 images
```

**Attention** : Le nombre de combinaisons explose rapidement !

```
10 expressions × 20 outfits × 15 backgrounds = 3000 images 🔥
```

➡️ Utilisez des **sélecteurs** (voir [Templates Advanced](./4-templates-advanced.md)) pour limiter.

---

## Modes de génération

### Mode `combinatorial` : Toutes les combinaisons

```yaml
generation:
  mode: combinatorial
  max_images: 100  # Optionnel : limite le nombre d'images
```

**Génère** : Toutes les combinaisons possibles (ou jusqu'à `max_images`)

**Usage typique** :
- Dataset complet pour entraînement LoRA
- Création de référence exhaustive
- Garantir la couverture de toutes les variations

**Exemple** :
```
3 expressions × 2 outfits = 6 images
- Expression1 + Outfit1
- Expression1 + Outfit2
- Expression2 + Outfit1
- Expression2 + Outfit2
- Expression3 + Outfit1
- Expression3 + Outfit2
```


### Mode `random` : Échantillonnage aléatoire

```yaml
generation:
  mode: random
  max_images: 20  # Tire 20 combinaisons aléatoires parmi toutes les possibles
```

**Génère** : N combinaisons aléatoires uniques (pas de doublons)

**Usage typique** :
- Exploration rapide sans tout générer
- Tests avant production
- Génération créative sans pattern prévisible

**Exemple** :
```
3 expressions × 2 outfits = 6 combinaisons possibles
Mode random avec max_images: 4

Résultat (tirage aléatoire) :
- Expression2 + Outfit1
- Expression1 + Outfit2
- Expression3 + Outfit2
- Expression1 + Outfit1
```

### Comparaison

| Aspect | Combinatorial | Random |
|--------|--------------|--------|
| **Génère** | Toutes les combinaisons | N combinaisons aléatoires |
| **Ordre** | Prévisible (systématique) | Imprévisible |
| **Couverture** | Exhaustive | Partielle |
| **Performance** | Peut être très long | Rapide (limite fixe) |
| **Usage** | Dataset, LoRA | Exploration, tests |

---

## Modes de seed

Le mode de seed détermine **comment les seeds sont générées** pour chaque image.

### Mode `fixed` : Même seed partout

```yaml
generation:
  seed_mode: fixed
  seed: 1000
```

**Toutes les images** avec seed `1000`

**Usage** :
- Tester l'impact des variations de prompt uniquement
- Comparer des prompts avec même seed
- Reproductibilité maximale

**Résultat** :
```
Image 1: seed 1000 (Expression1 + Outfit1)
Image 2: seed 1000 (Expression1 + Outfit2)
Image 3: seed 1000 (Expression2 + Outfit1)
...
```

### Mode `progressive` : Seeds incrémentées

```yaml
generation:
  seed_mode: progressive
  seed: 1000
```

**Seeds** : `1000`, `1001`, `1002`, `1003`, ...

**Usage** :
- Génération standard (recommandé)
- Garantit diversité entre les images
- Reproductible (même ordre)

**Résultat** :
```
Image 1: seed 1000 (Expression1 + Outfit1)
Image 2: seed 1001 (Expression1 + Outfit2)
Image 3: seed 1002 (Expression2 + Outfit1)
...
```

### Mode `random` : Seeds aléatoires

```yaml
generation:
  seed_mode: random
  seed: 42  # Non utilisé (seed aléatoire = -1)
```

**Seeds** : Aléatoires (`-1` pour chaque image)

**Usage** :
- Exploration créative
- Maximum de variété
- Non reproductible

**Résultat** :
```
Image 1: seed -1 (aléatoire, par ex. 842345)
Image 2: seed -1 (aléatoire, par ex. 123987)
Image 3: seed -1 (aléatoire, par ex. 954321)
...
```

### Comparaison

| Mode | Seeds | Reproductible | Usage |
|------|-------|---------------|-------|
| `fixed` | Toutes identiques | ✅ Maximum | Tests de prompts |
| `progressive` | Incrémentées | ✅ Oui | Génération standard ⭐ |
| `random` | Aléatoires | ❌ Non | Exploration |

---

## Organisation de projet

### Structure recommandée

```
my-project/
├── templates/              # Templates de base réutilisables (Niveau 4)
│   └── base_portrait.template.yaml
│
├── prompts/               # Prompts spécifiques
│   ├── portrait_happy.prompt.yaml
│   ├── portrait_action.prompt.yaml
│   └── landscape.prompt.yaml
│
├── variations/            # Fichiers de variations réutilisables
│   ├── shared/            # Variations communes
│   │   ├── expressions.yaml
│   │   ├── outfits.yaml
│   │   └── backgrounds.yaml
│   │
│   └── custom/            # Variations spécifiques
│       ├── character_poses.yaml
│       └── fantasy_items.yaml
│
└── results/               # Images générées (configuré dans .sdgen_config.json)
    ├── 20251014_portrait_happy/
    └── 20251014_landscape/
```

### Bonnes pratiques

#### 1. Nommer clairement

```yaml
# ❌ Mauvais
name: 'test1'

# ✅ Bon
name: 'Portrait Emma - Expression Tests'
```

#### 2. Commenter vos templates

```yaml
version: '2.0'
name: 'Portrait High Quality'

# Ce template génère des portraits haute résolution
# avec hires fix pour améliorer les détails

imports:
  Expression: ../variations/expressions.yaml  # 50 expressions variées
  Outfit: ../variations/outfits.yaml         # 30 tenues casual et formal
```

#### 3. Tester avant production

```yaml
# Version test (rapide)
generation:
  mode: random
  max_images: 5  # Test rapide

# Version production (après validation)
generation:
  mode: combinatorial
  max_images: 500
```

#### 4. Utiliser des chemins relatifs

```yaml
# ✅ Bon : chemins relatifs au fichier YAML
imports:
  Expression: ../variations/expressions.yaml

# ❌ Mauvais : chemins absolus (non portables)
imports:
  Expression: /home/user/project/variations/expressions.yaml
```

---

## Récapitulatif

✅ Vous maîtrisez maintenant :
- Multi-variations (plusieurs placeholders)
- Calcul des combinaisons
- Modes `combinatorial` vs `random`
- Modes de seed (`fixed`, `progressive`, `random`)
- Organisation de projet
- Bonnes pratiques de structuration

### Prochaine étape

Passez aux [Templates Advanced →](./4-templates-advanced.md) pour découvrir :
- **Sélecteurs** : Limiter/choisir des variations spécifiques
- **Héritage** : Réutiliser des templates de base
- **Chunks** : Blocs réutilisables complexes
- **Listes d'imports** : Combiner plusieurs fichiers

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~15 minutes
**Version du système** : V2.0
