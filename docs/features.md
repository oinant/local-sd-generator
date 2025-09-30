# Guide des Fonctionnalités

Ce document décrit toutes les fonctionnalités disponibles dans le système de génération d'images avec variations.

---

## Table des matières

1. [CLI - Génération d'images](#cli---génération-dimages)
2. [Système de Placeholders](#système-de-placeholders)
3. [Modes de Génération](#modes-de-génération)
4. [Modes de Seed](#modes-de-seed)
5. [Webapp](#webapp)
6. [Fichiers de Variations](#fichiers-de-variations)

---

## CLI - Génération d'images

### Scripts principaux

#### `image_variation_generator.py`
**Classe générique pour créer des générateurs d'images avec variations**

```python
from image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Angle}, detailed",
    negative_prompt="low quality, blurry",
    variation_files={
        "Expression": "variations/expressions.txt",
        "Angle": "variations/angles.txt"
    },
    seed=42,
    max_images=50,
    generation_mode="random",  # ou "combinatorial", "ask"
    seed_mode="progressive",   # ou "fixed", "random", "ask"
    session_name="my_session"
)

success, total = generator.run()
```

#### Fonction utilitaire rapide

```python
from image_variation_generator import create_generator

generator = create_generator(
    "beautiful {Subject}, {Style}",
    "low quality",
    {"Subject": "subjects.txt", "Style": "styles.txt"}
)
generator.run()
```

### Configuration de génération

```python
from sdapi_client import GenerationConfig

config = GenerationConfig(
    steps=30,
    cfg_scale=7,
    width=512,
    height=768,
    sampler_name="DPM++ 2M Karras",
    batch_size=1,
    n_iter=1
)

generator.set_generation_config(config)
```

---

## Système de Placeholders

Les placeholders permettent de créer des variations dynamiques dans vos prompts.

### Format de base

```
{PlaceholderName}
```

**Exemple :**
```
"masterpiece, {Expression}, {Pose}, beautiful girl"
```

### Options avancées

#### 1. Toutes les variations (défaut)

```
{Hair}
```
Utilise toutes les variations disponibles dans le fichier.

#### 2. Limitation aléatoire

```
{Hair:5}
```
Sélectionne aléatoirement 5 variations parmi toutes celles disponibles.

**Cas d'usage :** Tester rapidement un sous-ensemble de variations.

#### 3. Suppression du placeholder

```
{Hair:0}
```
Supprime complètement ce placeholder du prompt final.

**Cas d'usage :**
- Tests A/B pour mesurer l'impact d'un élément
- Générer des versions avec et sans un attribut
- Prompts conditionnels

**Exemple :**
```python
# Avec cheveux
prompt = "portrait, {Hair}, {Expression}, beautiful"
# → "portrait, long blonde hair, smiling, beautiful"

# Sans cheveux (personnage chauve, avec casque, etc.)
prompt = "portrait, {Hair:0}, {Expression}, beautiful"
# → "portrait, smiling, beautiful"
```

#### 4. Sélection d'index spécifiques

```
{Hair:#|1|5|22}
```
Sélectionne uniquement les variations aux index 1, 5 et 22.

**Note :** Les index commencent à 0.

**Cas d'usage :**
- Tester des combinaisons spécifiques qui fonctionnent bien ensemble
- Reproduire des résultats avec des variations exactes
- Affiner progressivement les variations utilisées
- Créer des sets cohérents

**Exemple :**
```python
# Fichier hair.txt :
# 0: short blonde
# 1: long black
# 2: curly red
# 3: straight brown
# 4: wavy silver
# 5: pixie cut

prompt = "portrait, {Hair:#|1|4|5}, beautiful"
# Utilisera uniquement : long black, wavy silver, pixie cut
```

### Mix d'options

Vous pouvez combiner différentes options dans le même prompt :

```python
prompt = "anime girl, {Hair:#|1|5|22}, {Expression:10}, {Background:0}, detailed"
```
- `Hair` : Index spécifiques 1, 5, 22
- `Expression` : 10 variations aléatoires
- `Background` : Supprimé du prompt

---

## Modes de Génération

### Mode Combinatorial

Génère **toutes les combinaisons possibles** de variations.

```python
generation_mode="combinatorial"
```

**Caractéristiques :**
- Exhaustif : explore toutes les possibilités
- Nombre d'images = produit du nombre de variations
  - Exemple : 5 expressions × 3 angles = 15 images

**Quand l'utiliser :**
- Créer des sheets complètes de personnage
- Tests systématiques d'angles et expressions
- Datasets d'entraînement LoRA complets

**Exemple :**
```python
# 5 expressions × 3 angles = 15 images
generator = ImageVariationGenerator(
    prompt_template="{Expression}, {Angle}",
    variation_files={
        "Expression": "expressions.txt",  # 5 variations
        "Angle": "angles.txt"             # 3 variations
    },
    generation_mode="combinatorial"
)
```

### Mode Random

Génère des **combinaisons aléatoires uniques**.

```python
generation_mode="random"
```

**Caractéristiques :**
- Créativité : découverte de combinaisons inattendues
- Nombre d'images configurable librement
- Chaque combinaison est unique (pas de doublons)

**Quand l'utiliser :**
- Explorer rapidement de nombreuses possibilités
- Générer de la diversité
- Tests créatifs

**Exemple :**
```python
# 100 combinaisons aléatoires parmi 1000+ possibilités
generator = ImageVariationGenerator(
    prompt_template="{Expression}, {Angle}, {Lighting}",
    variation_files={
        "Expression": "expressions.txt",  # 20 variations
        "Angle": "angles.txt",            # 10 variations
        "Lighting": "lighting.txt"        # 5 variations
    },
    generation_mode="random",
    max_images=100  # Génère 100 images aléatoires
)
```

### Mode Ask (Interactif)

```python
generation_mode="ask"
```

Demande à l'utilisateur de choisir le mode au lancement du script.

---

## Modes de Seed

La seed contrôle la reproductibilité de la génération.

### Fixed (Seed fixe)

```python
seed_mode="fixed"
seed=42
```

**Comportement :** Toutes les images utilisent la même seed (42).

**Résultat :** Même composition, seules les variations du prompt changent l'image.

**Quand l'utiliser :**
- Isoler l'effet des variations de prompt
- Comparer précisément l'impact de différentes descriptions
- Maintenir une cohérence visuelle maximale

### Progressive (Seeds incrémentées)

```python
seed_mode="progressive"
seed=42
```

**Comportement :** Seeds incrémentées (42, 43, 44, 45...).

**Résultat :** Variations légères mais prévisibles entre images.

**Quand l'utiliser :**
- **Recommandé pour la plupart des cas**
- Équilibre entre cohérence et diversité
- Génération de datasets d'entraînement
- Reproductibilité (même suite de seeds)

### Random (Seed aléatoire)

```python
seed_mode="random"
```

**Comportement :** Seed aléatoire (-1) pour chaque image.

**Résultat :** Maximum de diversité, compositions très différentes.

**Quand l'utiliser :**
- Explorer un maximum de possibilités
- Génération créative
- Recherche d'inspiration

### Ask (Interactif)

```python
seed_mode="ask"
```

Demande à l'utilisateur de choisir le mode au lancement du script.

---

## Exemples de combinaisons classiques

### 1. Génération combinatoire systématique

```python
generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Angle}, beautiful girl",
    negative_prompt="low quality",
    variation_files={
        "Expression": "expressions.txt",
        "Angle": "angles.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42
)
```

**Résultat :** Toutes les combinaisons, seeds 42, 43, 44...

### 2. Exploration aléatoire

```python
generator = ImageVariationGenerator(
    prompt_template="concept art, {Style}, {Subject}, {Lighting}",
    negative_prompt="low quality",
    variation_files={
        "Style": "styles.txt",
        "Subject": "subjects.txt",
        "Lighting": "lighting.txt"
    },
    generation_mode="random",
    seed_mode="random",
    max_images=100
)
```

**Résultat :** 100 images totalement aléatoires.

### 3. Test de variations spécifiques

```python
generator = ImageVariationGenerator(
    prompt_template="portrait, {Expression:#|0|5|10}, {Angle:#|0|2}",
    negative_prompt="low quality",
    variation_files={
        "Expression": "expressions.txt",
        "Angle": "angles.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive"
)
```

**Résultat :** 3 expressions × 2 angles = 6 images précises.

### 4. Test A/B avec placeholder supprimé

```python
# Run 1 : Avec élément
generator1 = create_generator(
    "masterpiece, {Lighting}, {Pose}, beautiful",
    "low quality",
    {"Lighting": "lighting.txt", "Pose": "poses.txt"}
)

# Run 2 : Sans élément pour comparer
generator2 = create_generator(
    "masterpiece, {Lighting:0}, {Pose}, beautiful",
    "low quality",
    {"Lighting": "lighting.txt", "Pose": "poses.txt"}
)
```

---

## Fichiers de Variations

### Format supporté

Les fichiers de variations utilisent un format texte simple avec plusieurs syntaxes possibles.

#### Format 1 : Clé → Valeur

```
# expressions.txt
happy→smiling, cheerful expression
sad→sad, melancholic
angry→angry, frowning
surprised→surprised, wide eyes
```

#### Format 2 : Numéro → Valeur

```
# angles.txt
1→front view
2→side view, profile
3→3/4 view
4→back view
```

Le numéro est ignoré, la clé est générée depuis la valeur.

#### Format 3 : Valeur simple

```
# styles.txt
realistic
anime style
oil painting
watercolor
digital art
```

La clé est générée automatiquement depuis la valeur.

#### Commentaires

```
# Ceci est un commentaire (ligne ignorée)

# Expressions faciales
happy→smiling
sad→crying
```

### Encodage

Par défaut UTF-8, peut être changé :

```python
variations = load_variations_from_file("file.txt", encoding='latin1')
```

### Exemple de fichier complet

```
# facial_expressions.txt
# Collection d'expressions pour génération de personnages

# Expressions positives
1→smiling, happy
2→laughing, joyful
3→grinning, excited

# Expressions neutres
10→neutral expression
11→serious, focused
12→calm, peaceful

# Expressions négatives
20→sad, crying
21→angry, frowning
22→scared, worried

# Expressions spéciales
30→surprised, shocked
31→confused, puzzled
```

---

## Webapp

### Fonctionnalités actuelles

#### Navigation des images

- **Interface web** accessible via navigateur
- **Arborescence de dossiers** : Browse des sessions de génération
- **Galerie d'images** : Affichage des images par session
- **Métadonnées** : Consultation des paramètres de génération

### Démarrage

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Puis ouvrir `http://localhost:8000`

### Configuration

Le fichier `.env` dans `/backend/` configure :
- Chemins des dossiers d'images
- Port du serveur
- Options de sécurité

**Exemple `.env` :**
```
IMAGES_ROOT=/path/to/local-sd-generator/apioutput
UPLOAD_FOLDER=/path/to/backend/uploads
SECRET_KEY=your-secret-key-here
```

### Architecture

```
/CLI/apioutput/           # Source des images générées
/backend/app/             # API FastAPI
/backend/frontend/        # Interface Vue.js
/backend/uploads/         # Images uploadées via webapp
```

---

## Workflow complet

### 1. Préparer les fichiers de variations

```bash
mkdir -p variations
echo "smiling\nsad\nangry" > variations/expressions.txt
echo "front view\nside view" > variations/angles.txt
```

### 2. Créer un script de génération

```python
# my_generator.py
from image_variation_generator import create_generator

generator = create_generator(
    "masterpiece, {Expression}, {Angle}, beautiful anime girl",
    "low quality, blurry",
    {
        "Expression": "variations/expressions.txt",
        "Angle": "variations/angles.txt"
    },
    seed=42,
    generation_mode="combinatorial",
    seed_mode="progressive",
    session_name="anime_test"
)

generator.run()
```

### 3. Lancer la génération

```bash
python3 my_generator.py
```

### 4. Consulter les résultats

Images dans : `CLI/apioutput/anime_test_TIMESTAMP/`

Métadonnées dans : `CLI/apioutput/anime_test_TIMESTAMP/session_config.txt`

### 5. Visualiser via webapp

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Ouvrir `http://localhost:8000` et naviguer vers la session `anime_test_TIMESTAMP`.

---

## Scripts d'exemple

### `example_simple_generator.py`
Exemples d'utilisation basique de la classe.

### `demo_generators.py`
Démonstrations de différents types de générateurs :
- Générateur de paysages
- Générateur de portraits
- Générateur de personnages anime
- Générateur d'art conceptuel
- Générateur de test rapide

### `facial_expression_generator_refactored.py`
Version refactorisée utilisant `ImageVariationGenerator` avec configuration avancée.

---

## Astuces et bonnes pratiques

### 1. Commencer petit

Testez d'abord avec peu de variations :

```python
prompt = "portrait, {Expression:3}, {Angle:2}"
```

### 2. Utiliser des sessions nommées

```python
session_name="test_lighting_v2"
```

Facilite l'organisation et la traçabilité.

### 3. Documenter les fichiers de variations

Utilisez des commentaires dans vos fichiers :

```
# expressions.txt - Version 2.0
# Mis à jour le 2025-09-30
# Expressions testées et validées

happy→smiling, cheerful
```

### 4. Mode progressif recommandé

Pour la plupart des cas, utilisez :

```python
generation_mode="combinatorial"
seed_mode="progressive"
```

Balance entre reproductibilité et diversité.

### 5. Tester les index spécifiques

Identifiez d'abord les bonnes variations :

```python
# Run 1 : Toutes les variations
generator.run()

# Identifier manuellement les meilleures (ex: index 1, 5, 22)

# Run 2 : Seulement les bonnes
prompt = "{Hair:#|1|5|22}"
```

### 6. Tests A/B systématiques

```python
elements = ["Lighting", "Background", "Outfit"]

for element in elements:
    # Avec élément
    run_generation(f"{{Expression}}, {{{element}}}")

    # Sans élément
    run_generation(f"{{Expression}}, {{{element}:0}}")
```

---

## Troubleshooting

### Problème : Aucune image générée

**Solution :** Vérifiez que :
1. L'API Stable Diffusion est lancée (`http://127.0.0.1:7860`)
2. Les fichiers de variations existent et contiennent des données
3. Les placeholders dans le prompt correspondent aux fichiers configurés

### Problème : Trop de combinaisons

```
📊 Combinaisons possibles: 5000
```

**Solution :** Utilisez les limites :
- `{Expression:10}` au lieu de `{Expression}`
- Ou passez en mode `random` avec `max_images`

### Problème : Chemins de fichiers invalides

**Solution :** Utilisez des chemins absolus ou relatifs au script :

```python
import os

BASE_DIR = os.path.dirname(__file__)
variation_files = {
    "Expression": os.path.join(BASE_DIR, "variations/expressions.txt")
}
```

### Problème : Encodage de fichier

Si caractères mal affichés :

```python
variations = load_variations_from_file("file.txt", encoding='latin1')
# ou
variations = load_variations_from_file("file.txt", encoding='cp1252')
```

---

## Limites et contraintes

### Performance

- **Génération séquentielle** : Une image à la fois
- **Délai entre images** : 2 secondes par défaut (configurable)
- Pour de gros volumes, prévoir du temps

### Combinaisons

- Mode combinatorial limité par le nombre total de combinaisons
- Exemple : 100 expressions × 50 angles × 20 lightings = 100 000 images
- Utilisez les limites ou le mode random

### Fichiers de variations

- Pas de validation automatique des prompts SD
- Responsabilité de l'utilisateur de créer des prompts valides
- Testez avec peu de variations d'abord

---

## Ressources

### Documentation complémentaire

- `CLAUDE.md` : Instructions pour Claude Code
- `product_idea.md` : Roadmap des fonctionnalités futures
- `README.md` : Vue d'ensemble du projet

### Fichiers de variations d'exemple

Créez vos propres fichiers ou consultez les exemples dans les scripts de démo.

### Support

Pour rapporter des bugs ou suggérer des fonctionnalités, consultez le fichier `product_idea.md`.

---

## Changelog des fonctionnalités

### Version actuelle

- ✅ Placeholders avec variations dynamiques
- ✅ Modes de génération (combinatorial, random)
- ✅ Modes de seed (fixed, progressive, random)
- ✅ Limitation de variations (`{Placeholder:N}`)
- ✅ Suppression de placeholders (`{Placeholder:0}`)
- ✅ Sélection d'index spécifiques (`{Placeholder:#|1|5|22}`)
- ✅ Webapp de visualisation
- ✅ Export des métadonnées de session

### À venir (voir `product_idea.md`)

- 🔜 Format JSON pour session_config
- 🔜 Lancement depuis fichier de configuration
- 🔜 Génération de thumbnails WebP
- 🔜 Base de données SQLite pour métadonnées
- 🔜 Architecture webapp simplifiée