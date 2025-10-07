# Advanced Features Brainstorm

**Status:** future
**Priority:** 8
**Component:** cli
**Created:** 2025-10-08

## Description

Collection d'idées pour fonctionnalités avancées à explorer dans le futur. Ces idées nécessitent plus de recherche et de validation avant implémentation.

---

## 1. Prévisualisation des Variations

Interface pour voir toutes les variations disponibles avant de lancer une génération.

**Concept :**
```bash
sdgen preview variations/expressions.txt variations/angles.txt
```

Affiche un tableau interactif avec :
- Liste des variations par fichier
- Nombre total de combinaisons
- Estimation du temps de génération
- Possibilité de sélectionner/désélectionner des variations

**Bénéfices :**
- Meilleure planification des générations
- Évite de lancer des générations trop longues par erreur
- Aide à découvrir toutes les variations disponibles

---

## 2. Variations Conditionnelles

Certaines variations ne s'appliquent que si d'autres sont présentes.

**Exemple :**
```yaml
variations:
  Expression: variations/expressions.txt
  OpenMouth:
    file: variations/open_mouth.txt
    conditions:
      - Expression: ["surprised", "laughing", "shouting"]
```

`{OpenMouth}` ne s'applique que si `{Expression}` = "surprised", "laughing" ou "shouting".

**Cas d'usage :**
- Cohérence anatomique (bouche ouverte avec certaines expressions)
- Accessoires contextuels (lunettes de soleil seulement en extérieur)
- Effets de lumière conditionnels

**Complexité :**
- Nécessite un système de dépendances
- Impact sur le calcul du nombre de combinaisons
- Interface de configuration à définir

---

## 3. Poids de Variations (Weighted Random)

En mode random, certaines variations apparaissent plus souvent que d'autres.

**Syntaxe possible :**
```yaml
# variations/expressions.txt
happy,smiling→3.0        # 3x plus probable
neutral→1.0              # Probabilité normale
sad,crying→0.5           # 2x moins probable
angry→0.1                # Rare
```

ou

```python
# Dans le prompt
prompt = "{Expression:weighted|happy:3.0|neutral:1.0|sad:0.5}"
```

**Bénéfices :**
- Contrôle de la distribution en mode random
- Évite de générer trop de variations rares/problématiques
- Focus sur les variations qui marchent bien

**Algorithme :**
Weighted random sampling avec normalisation des poids.

---

## 4. Historique et Favoris

Système de rating pour identifier et réutiliser les meilleures combinaisons.

**Features :**
- Marquer des images comme favorites
- Rating 1-5 étoiles
- Commentaires/notes sur les images
- Régénérer des variations similaires aux favoris

**Base de données :**
```sql
CREATE TABLE favorites (
    image_id INTEGER PRIMARY KEY,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    notes TEXT,
    favorited_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Workflows :**
```bash
# Voir les favoris
sdgen favorites list --min-rating=4

# Générer variations similaires
sdgen generate --similar-to=image_0042.png --count=20

# Export combinaisons favorites
sdgen favorites export > best_combinations.yaml
```

**Bénéfices :**
- Apprendre quelles combinaisons fonctionnent
- Itération progressive vers de meilleurs résultats
- Partage de combinaisons réussies

---

## 5. Templates de Configuration Réutilisables

Bibliothèque de configurations prêtes à l'emploi pour différents cas d'usage.

**Structure :**
```
templates/
├── portrait-standard.yaml
├── character-design.yaml
├── expression-sheet.yaml
├── angle-study.yaml
├── outfit-variations.yaml
└── lighting-test.yaml
```

**Utilisation :**
```bash
# Lister templates disponibles
sdgen templates list

# Utiliser un template
sdgen generate --template=character-design --model=my_lora.safetensors

# Créer template depuis session
sdgen template create my-workflow from-session session_2025-10-08/
```

**Contenu d'un template :**
```yaml
# templates/expression-sheet.yaml
name: Expression Sheet Generator
description: Generate a complete expression sheet for a character
author: community
version: 1.0

prompt_template: "1girl, {Expression:$10}, {Angle:$2}, portrait, detailed face"
negative_prompt: "bad anatomy, blurry"

variations:
  Expression: templates/data/common-expressions.txt
  Angle: templates/data/portrait-angles.txt

generation:
  mode: combinatorial
  seed_mode: progressive

parameters:
  steps: 30
  cfg_scale: 7
  width: 512
  height: 768
```

**Bénéfices :**
- Accélération pour utilisateurs novices
- Best practices partagées
- Cohérence entre projets
- Réutilisabilité

---

## 6. Batch Processing Multi-Prompts

Générer plusieurs sessions avec des prompts différents en une seule commande.

**Configuration :**
```yaml
# batch_job.yaml
batch:
  - name: character_happy
    prompt: "1girl, {Outfit}, happy, smiling"
    variations:
      Outfit: variations/outfits.txt
    count: 50

  - name: character_sad
    prompt: "1girl, {Outfit}, sad, crying"
    variations:
      Outfit: variations/outfits.txt
    count: 50

  - name: character_angry
    prompt: "1girl, {Outfit}, angry, frowning"
    variations:
      Outfit: variations/outfits.txt
    count: 50
```

**Exécution :**
```bash
sdgen batch run batch_job.yaml --parallel=3
```

**Bénéfices :**
- Automatisation de workflows complexes
- Génération nocturne de multiples datasets
- Comparaison A/B entre prompts

---

## 7. Variation Auto-Discovery

Scanner automatiquement des dossiers pour créer des fichiers de variations.

**Exemple :**
```bash
# Scanner un dossier d'images avec embeddings
sdgen discover-variations /path/to/embeddings/outfits/

# Génère variations/outfits.txt avec:
outfit_001→casual white shirt
outfit_002→red dress
outfit_003→school uniform
...
```

**Sources possibles :**
- Embeddings/TI (textual inversion)
- Tags dans metadata d'images
- Fichiers texte dans un dossier
- API externe (Civitai, etc.)

---

## 8. Interactive Prompt Builder

CLI interactive pour construire des prompts complexes step-by-step.

```bash
sdgen interactive

> What type of generation?
  1. Portrait
  2. Full body
  3. Landscape
  4. Custom
> 1

> Select variations to include:
  [x] Expression
  [x] Angle
  [ ] Lighting
  [ ] Background
> (space to toggle, enter to continue)

> Generation mode?
  1. Combinatorial (120 combinations)
  2. Random
> 2

> How many images? (max: 120)
> 50

> Preview prompt:
  "portrait, {Expression}, {Angle}, detailed face"

> Generate? [Y/n]
> Y
```

---

## 9. Variation Mixing Modes

Modes avancés pour combiner les variations.

**Modes possibles :**
- `orthogonal`: Combinaisons complètes (actuel)
- `paired`: Variations synchronisées par index
- `random-subset`: Random sur un sous-ensemble
- `grid`: Génération en grille 2D

**Example - Paired mode :**
```
# expressions.txt      # angles.txt
happy                  front
sad                    side
angry                  back

# Génère: (happy, front), (sad, side), (angry, back)
# Au lieu de: 3x3=9 combinaisons
```

---

## Notes

Ces idées sont en brainstorming et nécessitent :
- Validation de la pertinence
- Évaluation de la complexité
- Feedback utilisateurs
- Priorisation

Certaines peuvent être combinées ou simplifiées avant implémentation.
