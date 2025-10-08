from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional

from app.auth import AuthService
from app.models import GenerationRequest, GenerationResponse, GenerationJob
from app.services.generation_service import GenerationService

router = APIRouter(prefix="/api/generation", tags=["generation"])

# Instance globale du service de génération
generation_service = GenerationService()


@router.post("/", response_model=GenerationResponse)
async def create_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Lance une nouvelle génération d'images."""

    # Vérifier les permissions de génération
    AuthService.check_write_permission(user_guid)

    # Créer le job
    job = generation_service.create_job(request, user_guid)

    # Lancer la génération en arrière-plan
    background_tasks.add_task(generation_service.start_generation, job.job_id)

    return GenerationResponse(
        job_id=job.job_id,
        status=job.status,
        message="Génération créée et lancée en arrière-plan"
    )


@router.get("/{job_id}", response_model=GenerationJob)
async def get_generation_status(
    job_id: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère le statut d'une génération."""

    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de génération non trouvé")

    return job


@router.get("/")
async def list_generations(
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Liste tous les jobs de génération actifs."""

    return {
        "active_jobs": list(generation_service.active_jobs.keys()),
        "total_count": len(generation_service.active_jobs)
    }