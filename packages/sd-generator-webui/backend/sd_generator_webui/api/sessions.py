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
from sd_generator_webui.services.session_stats import SessionStatsService
from sd_generator_webui.models import (
    SessionMetadata,
    SessionMetadataUpdate,
    SessionStatsResponse,
)


def parse_session_datetime(session_name: str) -> Optional[datetime]:
    """
    Parse datetime from session folder name.

    Supports two formats:
    - Old: 2025-10-14_173320_name.prompt (with dashes in date)
    - New: 20251014_173320-name (without dashes in date)

    Returns datetime or None if unable to parse.
    """
    # Try old format first: YYYY-MM-DD_HHMMSS
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass

    # Try new format: YYYYMMDD_HHMMSS
    match = re.match(r'^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
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
_stats_service: Optional[SessionStatsService] = None


def get_metadata_service() -> SessionMetadataService:
    """Get or create the metadata service instance."""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = SessionMetadataService()
    return _metadata_service


def get_stats_service() -> SessionStatsService:
    """Get or create the stats service instance."""
    global _stats_service
    if _stats_service is None:
        _stats_service = SessionStatsService(sessions_root=IMAGES_DIR)
    return _stats_service


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
    since: Optional[int] = None,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Liste les images d'une session spécifique.

    Args:
        session_name: Nom de la session
        since: Index de la dernière image connue par le client.
               Si fourni, ne retourne que les images APRÈS cet index (polling mode).
               Si None, retourne toutes les images (initial load).

    Utilisé pour:
    - Initial load: GET /sessions/{name}/images (retourne tout)
    - Polling: GET /sessions/{name}/images?since=42 (retourne images 43+)

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

    # Polling mode: skip images before 'since' index
    if since is not None:
        # since=42 means client has images 0-42, so return 43+
        image_files = image_files[since + 1:]

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


@router.get("/{session_name}/manifest")
async def get_session_manifest(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Get manifest.json for a specific session.

    Returns 404 if session doesn't exist or has no manifest.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session non trouvée")

    manifest_path = session_path / "manifest.json"

    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest non trouvé")

    # Read and return manifest as JSON
    import json
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        return manifest_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Manifest JSON invalide")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture manifest: {str(e)}")


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


# ==================== Session Statistics Endpoints ====================


def _stats_to_response(stats) -> SessionStatsResponse:
    """Convert SessionStats to SessionStatsResponse."""
    return SessionStatsResponse(
        session_name=stats.session_name,
        sd_model=stats.sd_model,
        sampler_name=stats.sampler_name,
        scheduler=stats.scheduler,
        cfg_scale=stats.cfg_scale,
        steps=stats.steps,
        width=stats.width,
        height=stats.height,
        images_requested=stats.images_requested,
        images_actual=stats.images_actual,
        completion_percent=stats.completion_percent,
        placeholders_count=stats.placeholders_count,
        placeholders=stats.placeholders,
        variations_theoretical=stats.variations_theoretical,
        variations_summary=stats.variations_summary,
        session_type=stats.session_type,
        is_seed_sweep=stats.is_seed_sweep,
        seed_min=stats.seed_min,
        seed_max=stats.seed_max,
        seed_mode=stats.seed_mode,
        session_created_at=stats.session_created_at,
        stats_computed_at=stats.stats_computed_at,
    )


@router.get("/{session_name}/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid),
):
    """
    Get detailed statistics for a specific session.

    Args:
        session_name: Session folder name
        user_guid: Authenticated user GUID

    Returns:
        SessionStatsResponse with all computed stats

    Raises:
        404: Session not found
    """
    stats_service = get_stats_service()

    # Try to get cached stats
    stats = stats_service.get_stats(session_name)

    if stats is None:
        # Stats not cached - compute on-demand
        session_path = IMAGES_DIR / session_name

        if not session_path.exists():
            raise HTTPException(status_code=404, detail=f"Session not found: {session_name}")

        # Compute and save
        stats = stats_service.compute_and_save(session_path)

    return _stats_to_response(stats)


@router.post("/{session_name}/stats/refresh", response_model=SessionStatsResponse)
async def refresh_session_stats(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid),
):
    """
    Force recalculation of statistics for a session.

    Args:
        session_name: Session folder name
        user_guid: Authenticated user GUID

    Returns:
        SessionStatsResponse with fresh stats

    Raises:
        404: Session not found
    """
    stats_service = get_stats_service()
    session_path = IMAGES_DIR / session_name

    if not session_path.exists():
        raise HTTPException(status_code=404, detail=f"Session not found: {session_name}")

    # Force recompute
    stats = stats_service.compute_and_save(session_path)

    return _stats_to_response(stats)


class BatchComputeRequest(BaseModel):
    """Request model for batch computing stats."""

    force_recompute: bool = False


@router.post("/batch-compute")
async def batch_compute_stats(
    request: BatchComputeRequest,
    user_guid: str = Depends(AuthService.validate_guid),
):
    """
    Batch compute stats for all sessions (admin only).

    Args:
        request: Batch compute options
        user_guid: Authenticated user GUID

    Returns:
        Count of sessions processed
    """
    stats_service = get_stats_service()

    count = stats_service.batch_compute_all(
        sessions_root=IMAGES_DIR, force_recompute=request.force_recompute
    )

    return {"success": True, "sessions_processed": count}
