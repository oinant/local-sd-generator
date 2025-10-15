import sys
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Ajouter le répertoire CLI au path pour importer les services existants
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "CLI"))

from image_variation_generator import ImageVariationGenerator
from variation_loader import load_variations_for_placeholders
from config import IMAGES_DIR, METADATA_DIR, VARIATIONS_DIR
from models import GenerationRequest, GenerationJob, GenerationStatus, SeedMode, GenerationMode


class GenerationService:
    def __init__(self):
        self.active_jobs: Dict[str, GenerationJob] = {}

    def create_job(self, request: GenerationRequest, user_guid: str) -> GenerationJob:
        """Crée un nouveau job de génération."""
        job_id = str(uuid.uuid4())

        # Calculer le nombre total d'images basé sur les variations
        total_images = self._calculate_total_images(request)
        if request.generation_mode == GenerationMode.RANDOM:
            total_images = min(total_images, request.num_images)

        job = GenerationJob(
            job_id=job_id,
            status=GenerationStatus.PENDING,
            request=request,
            created_at=datetime.now(),
            total_images=total_images
        )

        self.active_jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[GenerationJob]:
        """Récupère un job par son ID."""
        return self.active_jobs.get(job_id)

    def start_generation(self, job_id: str) -> bool:
        """Lance la génération pour un job."""
        job = self.active_jobs.get(job_id)
        if not job or job.status != GenerationStatus.PENDING:
            return False

        try:
            job.status = GenerationStatus.RUNNING
            job.started_at = datetime.now()

            # Créer le générateur en utilisant les services CLI existants
            generator = self._create_generator(job.request)

            # Lancer la génération
            self._run_generation(generator, job)

            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 1.0

            return True

        except Exception as e:
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            return False

    def _create_generator(self, request: GenerationRequest) -> ImageVariationGenerator:
        """Crée un ImageVariationGenerator basé sur la requête."""

        # Convertir les chemins de fichiers de variations en chemins absolus
        variation_files = {}
        for placeholder, filename in request.variation_files.items():
            variation_files[placeholder] = str(VARIATIONS_DIR / filename)

        # Déterminer le seed
        seed = None
        if request.seed_mode == SeedMode.FIXED and request.seed is not None:
            seed = request.seed
        elif request.seed_mode == SeedMode.PROGRESSIVE and request.seed is not None:
            seed = request.seed
        # Pour RANDOM, on laisse seed=None

        # Créer le générateur
        generator = ImageVariationGenerator(
            prompt_template=request.prompt_template,
            negative_prompt=request.negative_prompt,
            variation_files=variation_files,
            seed=seed,
            max_images=request.num_images,
            generation_mode=request.generation_mode.value,
            seed_mode=request.seed_mode.value,
            session_name=request.session_name or f"api_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",

            # Paramètres SD WebUI
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            width=request.width,
            height=request.height,
            sampler_name=request.sampler_name,

            # Configuration pour l'API
            interactive=False  # Pas d'interface interactive
        )

        return generator

    def _run_generation(self, generator: ImageVariationGenerator, job: GenerationJob):
        """Lance la génération et met à jour le job."""

        # Hook de progression
        def progress_callback(current: int, total: int, filename: str = None):
            job.current_image = current
            job.total_images = total
            job.progress = current / total if total > 0 else 0
            if filename:
                job.generated_images.append(filename)

        # Modifier le générateur pour utiliser notre callback
        generator.progress_callback = progress_callback

        # Lancer la génération
        results = generator.run()

        # Sauvegarder les métadonnées
        self._save_metadata(job, results)

    def _calculate_total_images(self, request: GenerationRequest) -> int:
        """Calcule le nombre total d'images possibles."""
        try:
            # Charger les variations pour calculer les combinaisons
            variations = load_variations_for_placeholders(
                request.prompt_template,
                request.variation_files
            )

            total_combinations = 1
            for variations_list in variations.values():
                total_combinations *= len(variations_list)

            return total_combinations

        except Exception:
            # En cas d'erreur, retourner le nombre demandé
            return request.num_images

    def _save_metadata(self, job: GenerationJob, results: Dict):
        """Sauvegarde les métadonnées du job."""
        metadata = {
            "job_id": job.job_id,
            "request": job.request.model_dump(),
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "generated_images": job.generated_images,
            "results": results
        }

        metadata_file = METADATA_DIR / f"{job.job_id}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)