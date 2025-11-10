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
from sd_generator_webui.storage.session_storage import SessionStorage, LocalSessionStorage
from sd_generator_webui.storage.local_storage import LocalStorage
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
    image_count: Optional[int] = None  # Deprecated - use images_actual instead

    # Stats from DB (loaded eagerly)
    images_requested: Optional[int] = None
    images_actual: Optional[int] = None
    completion_percent: Optional[float] = None
    is_finished: Optional[bool] = None  # True if session is completed (has at least one newer session)


class SessionListResponse(BaseModel):
    """Réponse pour la liste des sessions."""
    sessions: List[SessionInfo]
    total_count: int
    page: int
    page_size: int
    total_pages: int


router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Initialize services (singletons)
_metadata_service: Optional[SessionMetadataService] = None
_stats_service: Optional[SessionStatsService] = None
_storage: Optional[SessionStorage] = None


def get_storage() -> SessionStorage:
    """Get or create the storage instance."""
    global _storage
    if _storage is None:
        _storage = LocalSessionStorage()
    return _storage


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
        storage = get_storage()
        _stats_service = SessionStatsService(storage=storage, sessions_root=IMAGES_DIR)
    return _stats_service


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    page: int = 1,
    page_size: int = 50,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Liste tous les dossiers de sessions avec stats de base depuis la DB (paginé).

    Args:
        page: Page number (1-indexed)
        page_size: Number of sessions per page (default: 50)
        user_guid: Authenticated user GUID

    Stats chargées depuis session_stats (DB) :
    - images_requested, images_actual, completion_percent
    - is_finished (calculé : True si au moins une session plus récente existe)

    Metadata is loaded separately via /sessions/{name}/metadata endpoints.
    """
    sessions: List[SessionInfo] = []
    stats_service = get_stats_service()
    storage = get_storage()

    # Step 1: List all session folders (via storage)
    session_names = []
    session_info_map = {}  # Map session_name -> (created_at, path)

    for session_path in storage.list_sessions(IMAGES_DIR):
        # Parse date from folder name (format: 2025-10-14_173320_name.prompt)
        # Ignore folder if parsing fails (not a valid session)
        created_at = parse_session_datetime(session_path.name)
        if not created_at:
            continue  # Skip folders that don't match session format

        session_names.append(session_path.name)
        session_info_map[session_path.name] = (created_at, str(session_path.relative_to(IMAGES_DIR)))

    # Step 2: Batch load all stats from DB (single query)
    stats_map = stats_service.get_stats_batch(session_names)

    # Step 3: Build SessionInfo objects
    for session_name in session_names:
        created_at, path = session_info_map[session_name]
        stats = stats_map.get(session_name)

        # Calculate completion_percent dynamically
        completion_percent = None
        if stats and stats.images_requested and stats.images_requested > 0:
            completion_percent = stats.images_actual / stats.images_requested

        sessions.append(SessionInfo(
            name=session_name,
            path=path,
            created_at=created_at,
            image_count=stats.images_actual if stats else None,  # Deprecated field
            images_requested=stats.images_requested if stats else None,
            images_actual=stats.images_actual if stats else None,
            completion_percent=completion_percent,
            is_finished=None  # Will be computed after sorting
        ))

    # Trier par date décroissante (basé sur le nom de dossier)
    sessions.sort(key=lambda x: x.created_at, reverse=True)

    # Compute is_finished for each session (BEFORE pagination)
    # A session is finished if there's at least one newer session
    for i, session in enumerate(sessions):
        # If there's any session before this one in the sorted list (newer), mark as finished
        session.is_finished = i > 0

    # Pagination
    total_count = len(sessions)
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

    # Validate page number
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    # Slice sessions for current page
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_sessions = sessions[start_idx:end_idx]

    return SessionListResponse(
        sessions=paginated_sessions,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
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
    storage = get_storage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # Compter uniquement les fichiers images via storage
    count = storage.count_images(session_path)

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
    storage = get_storage()
    local_storage = LocalStorage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # List image files via storage (already sorted)
    image_files = storage.list_images(session_path)

    # Polling mode: skip images before 'since' index
    if since is not None:
        # since=42 means client has images 0-42, so return 43+
        image_files = image_files[since + 1:]

    # Créer les infos d'images (minimaliste)
    images = []
    for file_path in image_files:
        relative_path = file_path.relative_to(IMAGES_DIR)
        metadata = local_storage.get_metadata(file_path)
        images.append({
            "filename": file_path.name,
            "path": str(relative_path),
            "created_at": metadata.modified_at,
            "file_size": metadata.size,
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
    storage = get_storage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
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
    storage = get_storage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # Read manifest via storage
    manifest_data = storage.read_manifest(session_path)

    if manifest_data is None:
        raise HTTPException(status_code=404, detail="Manifest non trouvé")

    return manifest_data


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
    storage = get_storage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
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
    storage = get_storage()

    # Try to get cached stats
    stats = stats_service.get_stats(session_name)

    if stats is None:
        # Stats not cached - compute on-demand
        session_path = IMAGES_DIR / session_name

        if not storage.session_exists(session_path):
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
    storage = get_storage()
    session_path = IMAGES_DIR / session_name

    if not storage.session_exists(session_path):
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
