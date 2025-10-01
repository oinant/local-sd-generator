# All: Génération automatique de thumbnails WebP

**Priorité** : P1 (Haute)
**Cible** : All (CLI + WebApp)
**Statut** : 🔜 À venir

---

## Objectif

Créer automatiquement des thumbnails WebP optimisés lors de la génération d'images PNG.

---

## Workflow proposé

1. Image PNG générée dans `/CLI/apioutput/session_xxx/`
2. **En background** : génération d'un thumbnail WebP
3. Thumbnail placé dans `/backend/static/thumbnails/session_xxx/`
4. Métadonnées enregistrées dans SQLite

---

## Configuration suggérée

```python
THUMBNAIL_CONFIG = {
    "format": "webp",
    "quality": 85,
    "max_width": 512,
    "max_height": 512,
    "maintain_aspect_ratio": True
}
```

---

## Bénéfices

- ✅ **Performance webapp** : Chargement rapide avec WebP optimisés
- ✅ **Économie de bande passante** : WebP ~30% plus léger que JPEG
- ✅ **Préservation des originaux** : PNG haute qualité intacts
- ✅ **Génération asynchrone** : Pas de ralentissement du workflow principal
- ✅ **Structure miroir** : Facile de retrouver l'original

---

## Implémentation

### Utilisation de Pillow

```python
from PIL import Image

def generate_thumbnail(png_path, webp_path, config):
    """Génère un thumbnail WebP depuis un PNG."""
    with Image.open(png_path) as img:
        # Redimensionner en conservant le ratio
        img.thumbnail(
            (config["max_width"], config["max_height"]),
            Image.Resampling.LANCZOS
        )

        # Sauvegarder en WebP
        img.save(
            webp_path,
            "WEBP",
            quality=config["quality"]
        )
```

### Hook dans le générateur

```python
class ImageVariationGenerator:
    def _save_image(self, image_data, filepath):
        # Sauvegarder PNG original
        save_png(image_data, filepath)

        # Générer thumbnail WebP en arrière-plan
        if self.generate_thumbnails:
            thumbnail_path = get_thumbnail_path(filepath)
            generate_thumbnail(filepath, thumbnail_path, THUMBNAIL_CONFIG)
```

---

## Structure des dossiers

```
CLI/apioutput/session_xxx/
├── image_0001.png    (1920×1080, 3.5 MB)
└── image_0002.png    (1920×1080, 3.2 MB)

backend/static/thumbnails/session_xxx/
├── image_0001.webp   (512×288, 45 KB)
└── image_0002.webp   (512×288, 42 KB)
```

---

## Impact

Fondation pour l'architecture webapp simplifiée et amélioration majeure des performances de navigation.
