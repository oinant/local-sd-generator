# Thumbnail Generator

Convertit automatiquement les images PNG de `CLI/apioutput` en thumbnails WebP dans `api/static/thumbnails/`.

## Installation

Les dépendances sont incluses dans le `pyproject.toml` de l'API :
```bash
cd api
pip install -e .
```

## Utilisation

**Important :** Lancer depuis la racine du projet

### Mode Initial
Traite toutes les images existantes :
```bash
python api/services/watchdogs/thumbnail_generator.py initial
```

### Mode Diff
Traite seulement les nouveaux dossiers depuis la dernière exécution :
```bash
python api/services/watchdogs/thumbnail_generator.py diff
```

### Mode Watch
Surveille en temps réel et traite automatiquement les nouvelles images :
```bash
python api/services/watchdogs/thumbnail_generator.py watch
```

## Configuration

Paramètres par défaut (modifiables dans le script) :
- **Source :** `CLI/apioutput`
- **Destination :** `api/static/thumbnails`
- **Hauteur thumbnail :** 240px (ratio conservé)
- **Qualité WebP :** 85
- **État :** `api/services/watchdogs/.thumbnail_state.json` (pour mode diff)

## Format des dossiers

Les dossiers doivent suivre le format : `YYYY-MM-DD_HHMMSS_nom`

Exemple : `2025-09-30_223814_facial_expressions`

## Structure générée

```
CLI/apioutput/2025-09-30_223814_test/image1.png
                                      /image2.png
                                      /subfolder/image3.png

→

api/static/thumbnails/2025-09-30_223814_test/image1.webp
                                              /image2.webp
                                              /subfolder/image3.webp
```

## Gestion des erreurs

- Images corrompues ou illisibles : skip avec log
- Thumbnails existants : skip automatiquement
- Dossiers sans timestamp : skip avec warning
