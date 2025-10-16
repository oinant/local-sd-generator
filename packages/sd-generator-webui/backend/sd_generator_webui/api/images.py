import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from PIL import Image

from sd_generator_webui.auth import AuthService
from sd_generator_webui.config import IMAGES_DIR, THUMBNAILS_DIR, METADATA_DIR
from sd_generator_webui.models import ImageInfo, ImageListResponse
from sd_generator_webui.services.image_metadata import extract_png_metadata

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    session: Optional[str] = Query(None, description="Filtrer par session"),
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Liste les images générées avec pagination."""

    # Collecter tous les fichiers images
    image_files: list[Path] = []
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        image_files.extend(IMAGES_DIR.glob(f"**/*{ext}"))

    # Filtrer par session si spécifié
    if session:
        image_files = [f for f in image_files if session in str(f)]

    # Trier par date de modification (plus récent en premier)
    image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Pagination
    total_count = len(image_files)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_files = image_files[start_idx:end_idx]

    # Créer les infos d'images (sans ouvrir les fichiers pour performance)
    images = []
    for file_path in page_files:
        try:
            # Vérifier si le thumbnail existe
            relative_path = file_path.relative_to(IMAGES_DIR)
            thumbnail_path = THUMBNAILS_DIR / relative_path.with_suffix(".webp")

            # NE PAS ouvrir l'image - dimensions chargées à la demande
            # NE PAS charger les métadonnées - chargées via endpoint dédié

            image_info = ImageInfo(
                filename=file_path.name,
                path=str(relative_path),
                thumbnail_path=str(thumbnail_path.relative_to(THUMBNAILS_DIR)) if thumbnail_path.exists() else None,
                metadata=None,  # Pas de metadata dans la liste
                created_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                file_size=file_path.stat().st_size,
                dimensions=None  # Pas de dimensions dans la liste
            )
            images.append(image_info)

        except Exception as e:
            # Ignorer les fichiers problématiques
            continue

    return ImageListResponse(
        images=images,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


# IMPORTANT: Route spécifique /metadata AVANT la route générique /{filename:path}
@router.get("/{filename:path}/metadata")
async def get_image_metadata(
    filename: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Récupère les métadonnées d'une image depuis le PNG.

    Extrait directement les metadata du chunk 'parameters' du PNG
    (format standard Stable Diffusion WebUI).
    """
    # Construire le chemin vers l'image
    image_path = IMAGES_DIR / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")

    # Vérification de sécurité - s'assurer que le fichier est dans IMAGES_DIR
    try:
        image_path.resolve().relative_to(IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Extraire metadata depuis PNG
    try:
        metadata = extract_png_metadata(image_path)
        return metadata
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image non trouvée")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Metadata invalide ou manquante: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture des métadonnées: {str(e)}")


@router.get("/{filename:path}")
async def get_image(
    filename: str,
    thumbnail: bool = Query(False, description="Retourner la miniature"),
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère une image (haute résolution ou miniature)."""

    # Chemin de l'image source
    source_path = IMAGES_DIR / filename

    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")

    # Vérification de sécurité
    try:
        source_path.resolve().relative_to(IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès refusé")

    if thumbnail:
        # Chemin du thumbnail (même structure que source, en .webp)
        thumbnail_path = THUMBNAILS_DIR / Path(filename).parent / (Path(filename).stem + ".webp")

        # Générer le thumbnail s'il n'existe pas
        if not thumbnail_path.exists():
            try:
                # Créer le dossier parent si nécessaire
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

                # Générer le thumbnail avec PIL
                with Image.open(source_path) as img:
                    # Convertir en RGB si nécessaire (pour RGBA)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background

                    # Resize avec thumbnail (garde le ratio)
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)

                    # Sauvegarder en WebP
                    img.save(thumbnail_path, 'WEBP', quality=85, method=6)

            except Exception as e:
                # Si échec, fallback sur l'image originale
                return FileResponse(
                    path=source_path,
                    media_type=None,
                    filename=source_path.name
                )

        return FileResponse(
            path=thumbnail_path,
            media_type="image/webp",
            filename=thumbnail_path.name
        )
    else:
        # Image full-size
        return FileResponse(
            path=source_path,
            media_type=None,
            filename=source_path.name
        )