# Claude Code Configuration

## Workspace Analysis Guidelines

### Excluded Directories
- `stable-diffusion-webui/` - Repository trop volumineux, ne pas analyser

## Project Focus
Ce workspace est dédié à la création de scripts pour générer des variations d'images avec différents angles et expressions faciales pour l'entraînement de LoRA et la création de sets de personnages cohérents.

## Scripts Principaux

### `emma-batch-generator.py`
Script original de génération de variations d'images pour un personnage spécifique (Emma).

### `image_variation_generator.py`
**Classe générique réutilisable pour créer des générateurs d'images avec variations**

Cette classe permet de créer facilement des générateurs personnalisés en spécifiant seulement :
- Template de prompt avec placeholders `{PlaceholderName}`
- Prompt négatif
- Dictionnaire de fichiers de variations

### `facial-expression-generator.py` (original)
Générateur avancé avec toute la logique intégrée (version monolithique).

### `facial_expression_generator_refactored.py`
**Version refactorisée utilisant ImageVariationGenerator**

Même fonctionnalité que l'original mais avec une configuration plus claire et modulaire.

#### Fonctionnalités principales :

1. **Système de placeholders dynamiques**
   - Format de base : `{PlaceholderName}` dans le prompt
   - Limitation : `{PlaceholderName:N}` pour limiter à N variations aléatoires
   - Sélection d'index : `{PlaceholderName:#|1|5|22}` sélectionne les index 1, 5 et 22
   - Poids de priorité : `{PlaceholderName:$N}` définit le poids N pour l'ordre des boucles
   - Combinaison : `{PlaceholderName:#|6|4|2$8}` sélectionne index 6,4,2 avec poids 8
   - Exemple : `{FacialExpression:15$5}` utilise 15 expressions avec poids 5

   **Système de poids pour l'ordre des boucles** :
   - Le poids détermine l'ordre d'imbrication des boucles en mode combinatorial
   - Plus petit poids = boucle extérieure (change moins souvent)
   - Plus grand poids = boucle intérieure (change plus souvent)
   - Exemple : `{Outfit:$2}` et `{Angle:$10}` → boucle sur Outfit d'abord, puis Angle pour chaque Outfit

2. **Chargement intelligent des variations**
   - Analyse automatique du prompt pour détecter les placeholders
   - Charge uniquement les fichiers de variations nécessaires
   - Support format `clé→valeur` dans les fichiers texte

3. **Modes de génération orthogonaux**

   **Mode génération des variations :**
   - `combinatorial` : Génère toutes les combinaisons possibles
   - `random` : Crée des combinaisons aléatoires uniques

   **Mode gestion des seeds :**
   - `fixed` : Même seed pour toutes les images
   - `progressive` : Seeds incrémentées (SEED, SEED+1, SEED+2...)
   - `random` : Seed aléatoire (-1) pour chaque image

4. **Interface interactive**
   - Choix du mode de génération
   - Choix du mode de seed
   - Sélection du nombre d'images après calcul des combinaisons
   - Validation des paramètres

5. **Configuration flexible**
   ```python
   # Fichiers de variations mappés aux placeholders
   VARIATION_FILES = {
       "FacialExpression": "chemin/vers/expressions.txt",
       "Angle": "chemin/vers/angles.txt",
       "Lighting": "chemin/vers/lighting.txt"
   }

   # Modes configurables
   GENERATION_MODE = "random"        # ou "combinatorial"
   SEED_MODE = "progressive"         # ou "fixed", "random"
   SEED = 42                         # Seed de base
   ```

### `variation_loader.py`
**Module utilitaire pour le chargement de variations**

#### Fonctions principales :
- `load_variations_from_file()` : Charge un fichier de variations
- `load_variations_for_placeholders()` : Charge selon les placeholders du prompt
- `create_random_combinations()` : Génère des combinaisons aléatoires
- `extract_placeholders_with_limits()` : Parse les placeholders avec limites
- `limit_variations()` : Limite aléatoirement le nombre de variations

#### Format des fichiers de variations :
```
# Commentaires supportés
1→angry
2→happy,smiling
surprised→very surprised
just_a_value
```

## Utilisation de ImageVariationGenerator

### Création d'un générateur simple
```python
from image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Pose}, detailed",
    negative_prompt="low quality, blurry",
    variation_files={
        "Expression": "path/to/expressions.txt",
        "Pose": "path/to/poses.txt"
    }
)
generator.run()
```

### Avec configuration avancée
```python
generator = ImageVariationGenerator(
    prompt_template="anime girl, {Expression:10}, {Style}, beautiful",
    negative_prompt="low quality",
    variation_files={
        "Expression": "expressions.txt",
        "Style": "styles.txt"
    },
    seed=42,
    max_images=25,
    generation_mode="random",
    seed_mode="progressive",
    session_name="anime_test"
)
```

### Fonction utilitaire
```python
from image_variation_generator import create_generator

# Version ultra-simple
generator = create_generator(
    "beautiful {Subject}, {Style}",
    "low quality",
    {"Subject": "subjects.txt", "Style": "styles.txt"}
)
generator.run()
```

## Scripts d'exemple disponibles

### `example_simple_generator.py`
Exemples d'utilisation basique de la classe.

### `demo_generators.py`
Démonstration de différents types de générateurs :
- Paysages
- Portraits
- Personnages anime
- Art conceptuel
- Tests rapides

### `facial_expression_generator_refactored.py`
Version refactorisée du générateur original.

## Exemples d'utilisation classiques

### Génération combinatoire classique
```python
generation_mode="combinatorial"
seed_mode="progressive"
# Génère toutes les combinaisons avec seeds 42, 43, 44...
```

### Exploration aléatoire
```python
generation_mode="random"
seed_mode="random"
# 100 images avec combinaisons et seeds totalement aléatoires
```

### Test de variations spécifiques
```python
prompt_template="masterpiece, {FacialExpression:5}, {Angle:3}, beautiful girl"
# Teste 5 expressions × 3 angles = 15 combinaisons maximum
```

### Génération avec ordre des boucles contrôlé
```python
prompt_template="1girl, {Outfit:$2}, {Angle:$10}, beautiful"
# Boucle extérieure : Outfit (poids 2)
# Boucle intérieure : Angle (poids 10)
# Résultat : Pour chaque Outfit, génère toutes les variations d'Angle
```

## Commands
- Lint: À déterminer
- Test: À déterminer
- Build: À déterminer