# Thumbnail Generator

Convertit automatiquement les images PNG de `CLI/apioutput` en thumbnails WebP dans `backend/static/thumbnails/`.

## Installation

Les dépendances sont incluses dans le `pyproject.toml` du backend :
```bash
cd backend
hatch env create
```

## Utilisation

**Important :** Lancer depuis le répertoire `backend/`

### Mode Initial
Traite toutes les images existantes :
```bash
cd backend
hatch run python watchdogs/thumbnail_generator.py initial --source ../CLI/apioutput --target static/thumbnails
```

### Mode Diff
Traite seulement les nouveaux dossiers depuis la dernière exécution :
```bash
hatch run python watchdogs/thumbnail_generator.py diff --source ../CLI/apioutput --target static/thumbnails
```

### Mode Watch
Surveille en temps réel et traite automatiquement les nouvelles images :
```bash
hatch run python watchdogs/thumbnail_generator.py watch --source ../CLI/apioutput --target static/thumbnails
```

## Configuration

Paramètres par défaut (modifiables dans le script) :
- **Source :** `CLI/apioutput`
- **Destination :** `backend/static/thumbnails`
- **Hauteur thumbnail :** 240px (ratio conservé)
- **Qualité WebP :** 85
- **État :** `.thumbnail_state.json` (pour mode diff)

## Format des dossiers

Les dossiers doivent suivre le format : `YYYY-MM-DD_HHMMSS_nom`

Exemple : `2025-09-30_223814_facial_expressions`

## Structure générée

```
CLI/apioutput/2025-09-30_223814_test/image1.png
                                      /image2.png
                                      /subfolder/image3.png

→

backend/static/thumbnails/2025-09-30_223814_test/image1.webp
                                                  /image2.webp
                                                  /subfolder/image3.webp
```

## Gestion des erreurs

- Images corrompues ou illisibles : skip avec log
- Thumbnails existants : skip automatiquement
- Dossiers sans timestamp : skip avec warning
