# [BUG] Output directory from .sdgen_config.json not used

**Status:** next
**Priority:** 2
**Component:** cli
**Created:** 2025-10-01

## Description

Le générateur JSON ne respecte pas le paramètre `output_dir` du fichier `.sdgen_config.json`. Il utilise toujours le dossier `apioutput/` par défaut au lieu du dossier configuré.

## Current Behavior

Config `.sdgen_config.json`:
```json
{
  "output_dir": "D:/StableDiffusion/private/results"
}
```

Mais la sortie va dans `apioutput/` au lieu de `D:/StableDiffusion/private/results/`.

## Expected Behavior

Le générateur devrait créer les sessions dans le dossier spécifié par `output_dir` dans `.sdgen_config.json`.

## Location

- `CLI/execution/json_generator.py`: create_generator_from_config()
- `CLI/image_variation_generator.py`: __init__() et run()
- Potentiellement besoin de lire `.sdgen_config.json` et passer output_dir au générateur

## Fix Approach

1. Lire `.sdgen_config.json` dans json_generator.py ou generator_cli.py
2. Extraire `output_dir` de la config
3. Passer ce paramètre à ImageVariationGenerator (ajouter param `output_dir` au constructeur)
4. Utiliser ce dossier au lieu de `apioutput/` hardcodé

## Tests

- Vérifier que les sessions sont créées dans le bon dossier
- Tester avec chemin relatif et absolu
- Tester avec chemin Windows (D:/) et WSL (/mnt/d/)
