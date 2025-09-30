"""Scheduler pour les jobs périodiques."""

import asyncio
import logging
from datetime import datetime

from app.jobs.thumbnail_generator import run_thumbnail_generation_job

logger = logging.getLogger(__name__)

# Configuration
THUMBNAIL_JOB_INTERVAL = 300  # 5 minutes entre chaque scan


class JobScheduler:
    """Scheduler pour exécuter les jobs périodiques."""

    def __init__(self):
        self.running = False
        self.task = None

    async def start(self):
        """Démarre le scheduler."""
        if self.running:
            logger.warning("Scheduler déjà en cours d'exécution")
            return

        self.running = True
        logger.info("🚀 Démarrage du scheduler de jobs")

        # Lance le job initial immédiatement
        logger.info("Lancement du job initial de génération de miniatures...")
        try:
            generated, errors = run_thumbnail_generation_job()
            logger.info(f"Job initial terminé: {generated} miniatures générées, {errors} erreurs")
        except Exception as e:
            logger.error(f"Erreur lors du job initial: {e}")

        # Lance la boucle périodique
        self.task = asyncio.create_task(self._run_periodic_jobs())

    async def stop(self):
        """Arrête le scheduler."""
        if not self.running:
            return

        self.running = False
        logger.info("Arrêt du scheduler de jobs...")

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("✅ Scheduler arrêté")

    async def _run_periodic_jobs(self):
        """Boucle principale du scheduler."""
        while self.running:
            try:
                # Attend l'intervalle configuré
                await asyncio.sleep(THUMBNAIL_JOB_INTERVAL)

                if not self.running:
                    break

                logger.info(f"🔄 Lancement périodique du job de miniatures ({datetime.now()})")

                # Exécute le job
                generated, errors = run_thumbnail_generation_job()

                if generated > 0:
                    logger.info(f"✅ Job périodique terminé: {generated} miniatures générées, {errors} erreurs")

            except asyncio.CancelledError:
                logger.info("Job périodique annulé")
                break
            except Exception as e:
                logger.error(f"❌ Erreur lors du job périodique: {e}")
                # Continue malgré l'erreur


# Instance globale du scheduler
scheduler = JobScheduler()