# Getting Started

**Bienvenue ! Ce guide vous permettra de générer vos premières images avec le CLI en moins de 10 minutes.**

---

## Installation

### Prérequis

- Python 3.8+
- Stable Diffusion WebUI lancé et accessible (par défaut : `http://127.0.0.1:7860`)

### Installation du CLI

```bash
# Depuis la racine du projet
cd /mnt/d/StableDiffusion/local-sd-generator/CLI
pip install -e .
```

**Vérification :**
```bash
sdgen --help
```

Vous devriez voir la liste des commandes disponibles.

---

## Configuration initiale

### Créer la configuration globale

```bash
sdgen init
```

Cette commande crée le fichier `~/.sdgen_config.json` avec :

```json
{
  "configs_dir": "/path/to/your/templates",
  "output_dir": "/path/to/output",
  "api_url": "http://127.0.0.1:7860"
}
```

**Modifiez les chemins** pour pointer vers :
- `configs_dir` : Où vous stockerez vos templates
- `output_dir` : Où les images seront sauvegardées

---

## Votre premier template

### Créer la structure

```bash
# Dans votre configs_dir
mkdir -p my-first-project/prompts
mkdir -p my-first-project/variations
```

### Créer un fichier de variations

**`my-first-project/variations/expressions.yaml`**

```yaml
happy: smiling, cheerful expression
sad: crying, melancholic look
neutral: calm, neutral expression
```

### Créer votre premier template

**`my-first-project/prompts/portrait.prompt.yaml`**

```yaml
version: '2.0'
name: 'My First Portrait'

# Importez le fichier de variations
imports:
  Expression: ../variations/expressions.yaml

# Template avec un placeholder {Expression}
template: |
  masterpiece, beautiful portrait, {Expression}, detailed

# Configuration de génération
generation:
  mode: combinatorial        # Génère toutes les combinaisons
  seed_mode: progressive     # Seeds incrémentées (42, 43, 44...)
  seed: 42
  max_images: 3              # 3 expressions = 3 images

# Paramètres Stable Diffusion
parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras
```

---

## Générer vos premières images

```bash
sdgen generate -t my-first-project/prompts/portrait.prompt.yaml
```

### Ce qui se passe

1. **Le CLI lit votre template**
   - Charge `expressions.yaml` (3 variations)
   - Détecte le placeholder `{Expression}`

2. **Affiche les statistiques**
   ```
   ╭─────────────────── Detected Variations ───────────────────╮
   │   Expression: 3 variations                                │
   │   Total combinations: 3                                   │
   │   Generation mode: combinatorial                          │
   │   Will generate: 3 images                                 │
   ╰───────────────────────────────────────────────────────────╯
   ```

3. **Génère les 3 images**
   ```
   Image 1: masterpiece, beautiful portrait, smiling, cheerful expression, detailed
   Image 2: masterpiece, beautiful portrait, crying, melancholic look, detailed
   Image 3: masterpiece, beautiful portrait, calm, neutral expression, detailed
   ```

4. **Sauvegarde dans `output_dir`**
   ```
   output_dir/20251014_150423_MyFirstPortrait/
   ├── 001.png
   ├── 002.png
   ├── 003.png
   └── manifest.json
   ```

---

## Comprendre les résultats

### Structure du dossier de session

```
20251014_150423_MyFirstPortrait/
├── 001.png                    # Image générée
├── 002.png
├── 003.png
└── manifest.json              # Métadonnées complètes
```

### Le fichier `manifest.json`

Contient **tout** pour reproduire la génération :

```json
{
  "version": "2.0",
  "timestamp": "2025-10-14T15:04:23",
  "template_used": "portrait.prompt.yaml",
  "images": [
    {
      "filename": "001.png",
      "seed": 42,
      "prompt": "masterpiece, beautiful portrait, smiling, cheerful expression, detailed",
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

**Avantage** : Vous pouvez reproduire exactement la même génération plus tard.

---

## Modifier votre template

### Ajouter des variations

**`variations/outfits.yaml`**

```yaml
casual: jeans and t-shirt
formal: elegant dress
```

**Mettez à jour `portrait.prompt.yaml`** :

```yaml
imports:
  Expression: ../variations/expressions.yaml
  Outfit: ../variations/outfits.yaml  # ← Nouveau

template: |
  masterpiece, beautiful portrait, {Expression}, {Outfit}, detailed

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 6  # 3 expressions × 2 outfits = 6 images
```

**Régénérez** :

```bash
sdgen generate -t my-first-project/prompts/portrait.prompt.yaml
```

Vous obtenez maintenant **6 images** (toutes les combinaisons).

---

## Modes de génération

### Mode `combinatorial` (toutes les combinaisons)

```yaml
generation:
  mode: combinatorial
  # Génère : Expression1 + Outfit1, Expression1 + Outfit2, Expression2 + Outfit1, ...
```

**Utilisation** : Créer un dataset complet, entraînement LoRA

### Mode `random` (échantillonnage aléatoire)

```yaml
generation:
  mode: random
  max_images: 10  # Tire 10 combinaisons aléatoires parmi toutes les possibles
```

**Utilisation** : Exploration rapide, génération créative

---

## Commandes utiles

### Lister les templates disponibles

```bash
sdgen list
```

Affiche tous les templates dans `configs_dir`.

### Valider un template avant génération

```bash
sdgen validate my-first-project/prompts/portrait.prompt.yaml
```

Vérifie que :
- Le YAML est bien formé
- Tous les imports existent
- Tous les placeholders ont des variations

### Générer avec limite

```bash
sdgen generate -t portrait.prompt.yaml -n 5
```

Limite à 5 images maximum (utile pour tester).

### Dry-run (sans générer)

```bash
sdgen generate -t portrait.prompt.yaml --dry-run
```

Sauvegarde les payloads API en JSON sans générer les images (pour debug).

---

## Prochaines étapes

Maintenant que vous avez généré vos premières images, explorez :

### 📖 [Templates Basics](./templates-basics.md)
Apprenez les concepts fondamentaux :
- Multi-variations
- Modes de seed
- Organisation de projet

### 🚀 [Templates Advanced](./templates-advanced.md)
Fonctionnalités avancées :
- Sélecteurs (limiter les variations)
- Héritage de templates
- Chunks réutilisables

### 💡 [Examples](./examples.md)
Cas d'usage réels :
- Entraînement LoRA
- Exploration créative
- Production de variantes

### 🔧 [Troubleshooting](./troubleshooting.md)
Solutions aux problèmes courants

---

## Aide rapide

### Problème : Aucune image générée

**Vérifiez** :
1. Stable Diffusion WebUI est lancé (`http://127.0.0.1:7860`)
2. Votre template est valide (`sdgen validate`)
3. Les fichiers de variations existent

### Problème : Une seule image au lieu de plusieurs

**Cause probable** : Placeholder sans variations

**Solution** : Vérifiez que tous les `{Placeholders}` ont un import correspondant.

### Problème : Erreur "File not found"

**Cause** : Chemin relatif incorrect

**Solution** : Les chemins dans `imports:` sont relatifs au fichier YAML :
```yaml
# Si portrait.prompt.yaml est dans prompts/
imports:
  Expression: ../variations/expressions.yaml  # Remonte d'un niveau
```

---

## Récapitulatif

✅ Vous savez maintenant :
- Installer et configurer le CLI
- Créer un template simple
- Définir des variations
- Générer des images
- Comprendre les résultats

**Temps total** : ~10 minutes

**Images générées** : 3-6 selon vos variations

**Next step** : [Templates Basics →](./templates-basics.md)

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
