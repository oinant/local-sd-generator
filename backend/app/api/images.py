import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from PIL import Image

from app.auth import AuthService
from app.config import IMAGES_DIR, THUMBNAILS_DIR, METADATA_DIR
from app.models import ImageInfo, ImageListResponse

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
    image_files = []
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

    # Créer les infos d'images
    images = []
    for file_path in page_files:
        try:
            # Vérifier si le thumbnail existe
            relative_path = file_path.relative_to(IMAGES_DIR)
            thumbnail_path = THUMBNAILS_DIR / relative_path.with_suffix(".webp")

            # Obtenir les dimensions
            with Image.open(file_path) as img:
                dimensions = img.size

            # Charger les métadonnées si disponibles
            metadata = {}
            try:
                metadata_file = METADATA_DIR / f"{file_path.stem}.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
            except Exception:
                pass

            image_info = ImageInfo(
                filename=file_path.name,
                path=str(relative_path),
                thumbnail_path=str(thumbnail_path.relative_to(THUMBNAILS_DIR)) if thumbnail_path.exists() else None,
                metadata=metadata,
                created_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                file_size=file_path.stat().st_size,
                dimensions=dimensions
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


@router.get("/{filename:path}")
async def get_image(
    filename: str,
    thumbnail: bool = Query(False, description="Retourner la miniature"),
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère une image (haute résolution ou miniature)."""

    if thumbnail:
        file_path = THUMBNAILS_DIR / filename
        # Convertir l'extension en .webp pour les thumbnails
        if not file_path.suffix == ".webp":
            file_path = file_path.with_suffix(".webp")
    else:
        file_path = IMAGES_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image non trouvée")

    # Vérification de sécurité - s'assurer que le fichier est dans le bon répertoire
    try:
        if thumbnail:
            file_path.resolve().relative_to(THUMBNAILS_DIR.resolve())
        else:
            file_path.resolve().relative_to(IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès refusé")

    return FileResponse(
        path=file_path,
        media_type="image/webp" if thumbnail else None,
        filename=file_path.name
    )


@router.get("/{filename:path}/metadata")
async def get_image_metadata(
    filename: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère les métadonnées d'une image."""

    # Extraire le nom de base sans extension
    base_name = Path(filename).stem
    metadata_file = METADATA_DIR / f"{base_name}.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Métadonnées non trouvées")

    try:
        import json
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture des métadonnées: {str(e)}")