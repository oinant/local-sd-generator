# Prompting Standalone

**Générez vos premières images avec un prompt fixe et comprenez les paramètres de base.**

📚 **Prérequis** : [Getting Started](./getting-started.md) (installation + config)

⏱️ **Durée de lecture** : 10 minutes

---

## Objectif

Avant d'utiliser les variations et templates, commençons simple : **générer plusieurs images du même prompt** en faisant varier uniquement les paramètres de génération (seed, résolution, etc.).

---

## Votre premier prompt fixe

### Créer le fichier

**`prompts/landscape_test.prompt.yaml`**

```yaml
version: '2.0'
name: 'Landscape Test - Fixed Prompt'

# Pas de imports : pas de variations !
# Le prompt est fixe, seuls les paramètres varient

template: |
  masterpiece, beautiful sunset over mountains,
  lake reflecting golden light,
  dramatic clouds, nature photography,
  8K, ultra-HD, detailed

generation:
  mode: random              # Mode n'a pas d'importance sans variations
  seed_mode: progressive    # Seeds différentes pour chaque image
  seed: 1000
  max_images: 10            # Génère 10 images

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

### Générer

```bash
sdgen generate -t prompts/landscape_test.prompt.yaml
```

### Résultat

**10 images générées** avec le même prompt mais des seeds différentes :

```
Image 1: seed 1000
Image 2: seed 1001
Image 3: seed 1002
...
Image 10: seed 1009
```

**Constat** : Malgré le même prompt, chaque image est différente grâce aux seeds.

---

## Paramètres de base

### Section `parameters:`

```yaml
parameters:
  width: 512                # Largeur de l'image
  height: 768               # Hauteur de l'image
  steps: 20                 # Nombre de steps (qualité)
  cfg_scale: 7              # Guidance scale (fidélité au prompt)
  sampler: DPM++ 2M Karras  # Algorithme de sampling
```

### Paramètres essentiels

#### `width` et `height`

**Résolutions courantes** :

| Type | Résolution | Usage |
|------|-----------|-------|
| Portrait | 512×768 | Personnages, portraits |
| Portrait HD | 832×1216 | Haute définition |
| Paysage | 768×512 | Landscapes, scènes larges |
| Carré | 512×512 | Polyvalent |

**Conseil** : Augmenter la résolution = plus de temps de génération

#### `steps`

**Nombre d'itérations** de diffusion.

- **10-15 steps** : Rapide, qualité moyenne (tests)
- **20-25 steps** : Standard, bon compromis ⭐
- **30-40 steps** : Haute qualité, lent
- **50+ steps** : Diminishing returns (pas toujours mieux)

**Conseil** : Commencer à 20, ajuster selon résultats

#### `cfg_scale` (Classifier Free Guidance)

**Fidélité au prompt** (1-30).

- **1-5** : Créatif, liberté artistique
- **6-8** : Standard, équilibré ⭐
- **9-12** : Fidèle au prompt
- **13+** : Très fidèle, peut sur-saturer

**Conseil** : 7 est un bon point de départ

#### `sampler`

**Algorithme de génération**.

**Recommandés** :
- `DPM++ 2M Karras` ⭐ (bon équilibre qualité/vitesse)
- `DPM++ SDE Karras` (plus lent, très détaillé)
- `Euler a` (rapide, bon pour portraits)
- `DDIM` (reproductible, stable)

**Note** : Les samplers disponibles dépendent de votre SD WebUI.

**Voir tous les samplers disponibles** :
```bash
sdgen api samplers
```

---

## Section `generation:`

### `mode`

Sans variations (imports), le mode n'a **pas d'importance**.

```yaml
generation:
  mode: random  # ou combinatorial, même résultat sans variations
```

### `seed_mode` : Comment générer les seeds

#### Mode `fixed` : Même seed pour toutes les images

```yaml
generation:
  seed_mode: fixed
  seed: 1000
  max_images: 5
```

**Résultat** : **5 images identiques** (même seed 1000)

**Usage** :
- Tester l'impact de changements de paramètres
- Comparer deux prompts avec même seed
- Reproductibilité maximale

**Exemple d'usage** :
```yaml
# Test 1 : cfg_scale 5
parameters:
  cfg_scale: 5

generation:
  seed_mode: fixed
  seed: 1000
  max_images: 1

# Test 2 : cfg_scale 10 (avec même seed)
parameters:
  cfg_scale: 10

generation:
  seed_mode: fixed
  seed: 1000
  max_images: 1
```

Vous pouvez comparer les 2 images et voir l'effet de `cfg_scale`.

#### Mode `progressive` : Seeds incrémentées

```yaml
generation:
  seed_mode: progressive
  seed: 1000
  max_images: 10
```

**Résultat** : Seeds `1000`, `1001`, `1002`, ..., `1009`

**Usage** : Génération standard (recommandé) ⭐
- Diversité garantie
- Reproductible (même ordre si regénéré)
- Bon pour explorer les variations du modèle

#### Mode `random` : Seeds complètement aléatoires

```yaml
generation:
  seed_mode: random
  seed: 42  # Ignoré (seed = -1 pour chaque image)
  max_images: 10
```

**Résultat** : Seeds aléatoires (ex: `842345`, `123987`, `954321`, ...)

**Usage** : Exploration créative
- Maximum de variété
- Non reproductible
- Bon pour découvrir des résultats inattendus

### Comparaison

| Mode | Seeds | Reproductible | Usage |
|------|-------|---------------|-------|
| `fixed` | Toutes identiques | ✅ Maximum | Tests, comparaisons |
| `progressive` | Incrémentées | ✅ Oui | Standard ⭐ |
| `random` | Aléatoires | ❌ Non | Exploration |

---

## Paramètres avancés (optionnels)

### Hires Fix : Améliorer la résolution

```yaml
parameters:
  # Paramètres de base
  width: 832
  height: 1216
  steps: 30

  # Hires Fix (upscaling)
  enable_hr: true
  hr_scale: 1.5                # Facteur d'upscale (1.5× = 1248×1824)
  hr_upscaler: 4x_foolhardy_Remacri  # Modèle d'upscale
  denoising_strength: 0.4      # Force du denoising (0.3-0.5)
  hr_second_pass_steps: 15     # Steps du second pass
```

**Avantages** :
- ✅ Images plus grandes et détaillées
- ✅ Meilleure qualité visuelle
- ✅ Réduit les artefacts

**Inconvénients** :
- ⏱️ ~2× plus lent
- 💾 Plus de VRAM nécessaire

**Usage** : Génération finale haute qualité

### Schedulers (SD 1.9+)

```yaml
parameters:
  sampler: DPM++ 2M
  scheduler: Karras  # Karras, Exponential, etc.
```

**Voir tous les schedulers** :
```bash
sdgen api schedulers
```

---

## Comprendre le manifest.json

Après génération, chaque session contient un `manifest.json` avec **toutes les métadonnées**.

### Structure

```json
{
  "version": "2.0",
  "timestamp": "2025-10-14T16:23:45",
  "template_name": "Landscape Test - Fixed Prompt",
  "template_file": "landscape_test.prompt.yaml",

  "generation_config": {
    "mode": "random",
    "seed_mode": "progressive",
    "seed": 1000,
    "max_images": 10
  },

  "images": [
    {
      "filename": "001.png",
      "seed": 1000,
      "prompt": "masterpiece, beautiful sunset over mountains, lake reflecting golden light, dramatic clouds, nature photography, 8K, ultra-HD, detailed",
      "negative_prompt": "",
      "parameters": {
        "width": 512,
        "height": 768,
        "steps": 20,
        "cfg_scale": 7,
        "sampler": "DPM++ 2M Karras"
      }
    }
    // ... autres images
  ]
}
```

### Utilité

✅ **Reproductibilité** : Vous pouvez régénérer exactement la même image
✅ **Traçabilité** : Savoir quel prompt/paramètres ont donné quel résultat
✅ **Comparaison** : Comparer plusieurs générations

---

## Cas d'usage pratiques

### Cas 1 : Tester un prompt

```yaml
version: '2.0'
name: 'Prompt Test'

template: |
  masterpiece, young woman, smiling, detailed face

generation:
  seed_mode: progressive
  seed: 42
  max_images: 5  # Tester avec 5 seeds

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

**Générez et observez** : Le prompt donne-t-il de bons résultats ? Ajustez si nécessaire.

### Cas 2 : Comparer des samplers

**Test 1 : Sampler A**
```yaml
parameters:
  sampler: DPM++ 2M Karras

generation:
  seed_mode: fixed
  seed: 1000
  max_images: 1
```

**Test 2 : Sampler B**
```yaml
parameters:
  sampler: Euler a

generation:
  seed_mode: fixed
  seed: 1000  # Même seed !
  max_images: 1
```

Comparez les résultats avec **exactement le même seed**.

### Cas 3 : Générer un batch pour sélection

```yaml
generation:
  seed_mode: random
  max_images: 50  # Générer 50 variations

parameters:
  steps: 15  # Rapide pour tests
```

Parcourez les 50 images, sélectionnez les meilleures, notez les seeds des images que vous aimez.

---

## Commandes utiles

### Générer avec limite custom

```bash
sdgen generate -t landscape_test.prompt.yaml -n 5
```

Génère seulement 5 images (ignore `max_images` du fichier).

### Dry-run (sans générer)

```bash
sdgen generate -t landscape_test.prompt.yaml --dry-run
```

Crée les payloads JSON sans appeler l'API (debug).

### Voir les modèles disponibles

```bash
sdgen api models
```

### Voir les options du modèle actuel

```bash
sdgen api model-info
```

---

## Récapitulatif

✅ Vous savez maintenant :
- Créer un prompt fixe (sans variations)
- Configurer les paramètres de base (résolution, steps, cfg_scale, sampler)
- Utiliser les seed modes (fixed, progressive, random)
- Générer plusieurs images du même prompt
- Interpréter le manifest.json
- Tester et comparer des paramètres

### Limites du prompting standalone

❌ **Répétitif** : Pour tester 5 expressions × 3 outfits = écrire 15 fichiers
❌ **Pas de combinaisons** : Impossible de générer toutes les variantes automatiquement
❌ **Maintenance** : Changer le prompt de base = modifier tous les fichiers

➡️ **Solution** : Les placeholders et variations ! [Prochaine étape →](./2-placeholders-variations.md)

---

## Prochaine étape

Passez à [Placeholders & Variations →](./2-placeholders-variations.md) pour découvrir :
- Le concept de placeholder (`{Expression}`)
- Créer des fichiers de variations
- Générer automatiquement des combinaisons
- Éviter la duplication de code

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~10 minutes
**Version du système** : V2.0
