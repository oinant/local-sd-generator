import os
from pathlib import Path
from celery import Celery
from PIL import Image
import logging

from sd_generator_webui.config import REDIS_URL, IMAGES_DIR, THUMBNAILS_DIR, THUMBNAIL_SIZE, THUMBNAIL_QUALITY

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'instance Celery
celery_app = Celery(
    "sd_image_generator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.worker"]
)

# Configuration Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max par tâche
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True)
def generate_thumbnail(self, image_path: str, force_regenerate: bool = False):
    """
    Génère une miniature WebP pour une image.

    Args:
        image_path: Chemin relatif de l'image depuis IMAGES_DIR
        force_regenerate: Force la régénération même si la miniature existe
    """
    try:
        # Construire les chemins complets
        full_image_path = IMAGES_DIR / image_path
        relative_path = Path(image_path)
        thumbnail_path = THUMBNAILS_DIR / relative_path.with_suffix(".webp")

        # Vérifier que l'image source existe
        if not full_image_path.exists():
            logger.error(f"Image source non trouvée: {full_image_path}")
            return {"success": False, "error": "Image source non trouvée"}

        # Vérifier si la miniature existe déjà et est plus récente
        if thumbnail_path.exists() and not force_regenerate:
            image_mtime = full_image_path.stat().st_mtime
            thumbnail_mtime = thumbnail_path.stat().st_mtime
            if thumbnail_mtime >= image_mtime:
                logger.info(f"Miniature déjà à jour: {thumbnail_path}")
                return {"success": True, "thumbnail_path": str(thumbnail_path), "status": "already_exists"}

        # Créer le répertoire de destination si nécessaire
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

        # Générer la miniature
        with Image.open(full_image_path) as img:
            # Convertir en RGB si nécessaire (pour les images RGBA)
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = rgb_img

            # Redimensionner en gardant les proportions
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Sauvegarder en WebP
            img.save(
                thumbnail_path,
                "WebP",
                quality=THUMBNAIL_QUALITY,
                optimize=True
            )

        logger.info(f"Miniature générée: {thumbnail_path}")
        return {
            "success": True,
            "thumbnail_path": str(thumbnail_path),
            "original_size": os.path.getsize(full_image_path),
            "thumbnail_size": os.path.getsize(thumbnail_path),
            "status": "generated"
        }

    except Exception as e:
        logger.error(f"Erreur lors de la génération de miniature pour {image_path}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def generate_thumbnails_batch(self, image_paths: list, force_regenerate: bool = False):
    """
    Génère des miniatures pour un lot d'images.

    Args:
        image_paths: Liste des chemins d'images
        force_regenerate: Force la régénération
    """
    results = []
    total = len(image_paths)

    for i, image_path in enumerate(image_paths):
        # Mettre à jour le progrès
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": total, "processing": image_path}
        )

        # Générer la miniature
        result = generate_thumbnail.apply_async(args=[image_path, force_regenerate]).get()
        results.append({
            "image_path": image_path,
            "result": result
        })

    return {
        "success": True,
        "total_processed": total,
        "results": results
    }


@celery_app.task(bind=True)
def scan_and_generate_missing_thumbnails(self):
    """
    Scanne le répertoire d'images et génère les miniatures manquantes.
    """
    try:
        # Trouver toutes les images
        image_extensions = [".png", ".jpg", ".jpeg", ".webp"]
        all_images = []

        for ext in image_extensions:
            all_images.extend(IMAGES_DIR.glob(f"**/*{ext}"))

        # Filtrer les images qui n'ont pas de miniature
        missing_thumbnails = []
        for image_path in all_images:
            relative_path = image_path.relative_to(IMAGES_DIR)
            thumbnail_path = THUMBNAILS_DIR / relative_path.with_suffix(".webp")

            if not thumbnail_path.exists():
                missing_thumbnails.append(str(relative_path))

        logger.info(f"Trouvé {len(missing_thumbnails)} miniatures manquantes sur {len(all_images)} images")

        # Générer les miniatures manquantes
        if missing_thumbnails:
            return generate_thumbnails_batch.apply_async(args=[missing_thumbnails, False]).get()
        else:
            return {
                "success": True,
                "message": "Aucune miniature manquante",
                "total_images": len(all_images)
            }

    except Exception as e:
        logger.error(f"Erreur lors du scan des miniatures: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task
def cleanup_orphaned_thumbnails():
    """
    Supprime les miniatures orphelines (sans image source correspondante).
    """
    try:
        orphaned_count = 0

        # Parcourir toutes les miniatures
        for thumbnail_path in THUMBNAILS_DIR.glob("**/*.webp"):
            relative_path = thumbnail_path.relative_to(THUMBNAILS_DIR)

            # Chercher l'image source correspondante
            source_found = False
            for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                source_path = IMAGES_DIR / relative_path.with_suffix(ext)
                if source_path.exists():
                    source_found = True
                    break

            # Supprimer la miniature orpheline
            if not source_found:
                thumbnail_path.unlink()
                orphaned_count += 1
                logger.info(f"Miniature orpheline supprimée: {thumbnail_path}")

        return {
            "success": True,
            "orphaned_thumbnails_removed": orphaned_count
        }

    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        return {"success": False, "error": str(e)}


# Tâches périodiques
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "scan-missing-thumbnails": {
        "task": "app.services.worker.scan_and_generate_missing_thumbnails",
        "schedule": crontab(minute=0, hour="*/2"),  # Toutes les 2 heures
    },
    "cleanup-orphaned-thumbnails": {
        "task": "app.services.worker.cleanup_orphaned_thumbnails",
        "schedule": crontab(minute=30, hour=3),  # Tous les jours à 3h30
    },
}