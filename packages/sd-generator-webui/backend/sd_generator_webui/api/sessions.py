"""
API endpoints pour la gestion des sessions d'images.

Une session = un dossier de génération contenant plusieurs images.
Approche progressive pour gérer 12k+ images efficacement.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sd_generator_webui.auth import AuthService
from sd_generator_webui.config import IMAGES_DIR
from sd_generator_webui.services.session_metadata import SessionMetadataService
from sd_generator_webui.models import (
    SessionMetadata,
    SessionMetadataUpdate
)


def parse_session_datetime(session_name: str) -> Optional[datetime]:
    """
    Parse datetime from session folder name.

    Format: 2025-10-14_173320_name.prompt
    Returns datetime or None if unable to parse.
    """
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass
    return None


class SessionInfo(BaseModel):
    """Information sur une session (dossier d'images)."""
    name: str
    path: str
    created_at: datetime
    image_count: Optional[int] = None  # Chargé à la demande


class SessionListResponse(BaseModel):
    """Réponse pour la liste des sessions."""
    sessions: List[SessionInfo]
    total_count: int


router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Initialize metadata service (singleton)
_metadata_service: Optional[SessionMetadataService] = None


def get_metadata_service() -> SessionMetadataService:
    """Get or create the metadata service instance."""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = SessionMetadataService()
    return _metadata_service


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Liste tous les dossiers de sessions (rapide).

    Ne compte PAS les images par session - utilisez l'endpoint /count pour ça.
    Metadata is loaded separately via /sessions/{name}/metadata endpoints.
    """
    sessions: List[SessionInfo] = []

    # Lister uniquement les dossiers de premier niveau
    for item in IMAGES_DIR.iterdir():
        if item.is_dir():
            # Parse date from folder name (format: 2025-10-14_173320_name.prompt)
            # Ignore folder if parsing fails (not a valid session)
            created_at = parse_session_datetime(item.name)
            if not created_at:
                continue  # Skip folders that don't match session format

            # Always return SessionInfo (not SessionWithMetadata to keep types simple)
            # Frontend will fetch metadata separately if needed
            sessions.append(SessionInfo(
                name=item.name,
                path=str(item.relative_to(IMAGES_DIR)),
                created_at=created_at,
                image_count=None  # Pas de comptage ici
            ))

    # Trier par date décroissante (basé sur le nom de dossier)
    sessions.sort(key=lambda x: x.created_at, reverse=True)

    return SessionListResponse(
        sessions=sessions,
        total_count=len(sessions)
    )


@router.get("/{session_name}/count")
async def get_session_count(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Compte le nombre d'images dans une session spécifique.

    Utilisé pour afficher le badge de count à la demande (lazy).
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # Compter uniquement les fichiers images
    count = 0
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        count += len(list(session_path.glob(f"*{ext}")))

    return {"session": session_name, "count": count}


@router.get("/{session_name}/images")
async def list_session_images(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Liste toutes les images d'une session spécifique.

    Utilisé quand l'utilisateur clique sur une session.
    Ne charge PAS les thumbnails - ils seront lazy-loadés par le frontend.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # Collecter les fichiers images de ce dossier uniquement (pas récursif)
    image_files: list[Path] = []
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        image_files.extend(session_path.glob(f"*{ext}"))

    # Trier par nom de fichier
    image_files.sort()

    # Créer les infos d'images (minimaliste)
    images = []
    for file_path in image_files:
        relative_path = file_path.relative_to(IMAGES_DIR)
        images.append({
            "filename": file_path.name,
            "path": str(relative_path),
            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime),
            "file_size": file_path.stat().st_size,
        })

    return {
        "session": session_name,
        "images": images,
        "total_count": len(images)
    }


@router.get("/{session_name}/metadata", response_model=SessionMetadata)
async def get_session_metadata(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Get metadata for a specific session.

    Returns 404 if session doesn't exist or has no metadata.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session non trouvée")

    metadata_service = get_metadata_service()
    metadata = metadata_service.get_metadata(session_name)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Metadata non trouvée")

    return metadata


@router.patch("/{session_name}/metadata", response_model=SessionMetadata)
async def update_session_metadata(
    session_name: str,
    update: SessionMetadataUpdate,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Create or update metadata for a session.

    If metadata doesn't exist, it will be created.
    Only provided fields will be updated.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session non trouvée")

    metadata_service = get_metadata_service()
    metadata = metadata_service.upsert_metadata(
        session_id=session_name,
        session_path=str(session_path),
        update=update
    )

    return metadata


@router.delete("/{session_name}/metadata")
async def delete_session_metadata(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Delete metadata for a session.

    Returns 404 if metadata doesn't exist.
    """
    metadata_service = get_metadata_service()
    deleted = metadata_service.delete_metadata(session_name)

    if not deleted:
        raise HTTPException(status_code=404, detail="Metadata non trouvée")

    return {"success": True, "message": f"Metadata deleted for {session_name}"}
