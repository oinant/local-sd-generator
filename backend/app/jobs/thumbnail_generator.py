"""Job de génération automatique de miniatures pour les images."""

import os
from pathlib import Path
from PIL import Image
from typing import List
import logging

from app.config import IMAGE_FOLDERS

logger = logging.getLogger(__name__)

# Configuration des miniatures
THUMBNAIL_SIZE = (256, 256)  # Taille des miniatures
THUMBNAIL_FOLDER_NAME = ".thumbnails"  # Nom du dossier de miniatures
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def generate_thumbnail(image_path: Path, thumbnail_path: Path, size: tuple = THUMBNAIL_SIZE) -> bool:
    """
    Génère une miniature pour une image.

    Args:
        image_path: Chemin de l'image source
        thumbnail_path: Chemin où sauvegarder la miniature
        size: Taille de la miniature (largeur, hauteur)

    Returns:
        True si la miniature a été générée avec succès
    """
    try:
        # Ouvre l'image
        with Image.open(image_path) as img:
            # Convertit en RGB si nécessaire (pour les PNG avec transparence par exemple)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créé un fond blanc
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Créé la miniature en conservant le ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Sauvegarde la miniature
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

            logger.info(f"Miniature générée: {thumbnail_path}")
            return True

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la miniature pour {image_path}: {e}")
        return False


def get_thumbnail_path(image_path: Path, root_folder: Path) -> Path:
    """
    Retourne le chemin où devrait se trouver la miniature d'une image.
    La structure est répliquée dans un dossier .thumbnails à la racine.

    Args:
        image_path: Chemin de l'image source
        root_folder: Dossier racine configuré (ex: /path/to/outputs)

    Returns:
        Chemin vers la miniature
    """
    # Calcule le chemin relatif depuis la racine
    try:
        relative_path = image_path.relative_to(root_folder)
    except ValueError:
        # Si l'image n'est pas dans le dossier racine, utilise le nom du fichier
        relative_path = Path(image_path.name)

    # Créé le chemin de la miniature en répliquant la structure
    thumbnail_dir = root_folder / THUMBNAIL_FOLDER_NAME / relative_path.parent

    # Change l'extension en .jpg pour les miniatures
    thumbnail_filename = image_path.stem + '.jpg'

    return thumbnail_dir / thumbnail_filename


def thumbnail_exists(image_path: Path, root_folder: Path) -> bool:
    """
    Vérifie si une miniature existe pour une image.

    Args:
        image_path: Chemin de l'image source
        root_folder: Dossier racine configuré

    Returns:
        True si la miniature existe
    """
    thumbnail_path = get_thumbnail_path(image_path, root_folder)
    return thumbnail_path.exists()


def should_regenerate_thumbnail(image_path: Path, root_folder: Path) -> bool:
    """
    Détermine si une miniature doit être régénérée.

    Args:
        image_path: Chemin de l'image source
        root_folder: Dossier racine configuré

    Returns:
        True si la miniature doit être (re)générée
    """
    thumbnail_path = get_thumbnail_path(image_path, root_folder)

    # Si la miniature n'existe pas, il faut la générer
    if not thumbnail_path.exists():
        return True

    # Si l'image source est plus récente que la miniature, il faut la régénérer
    try:
        image_mtime = image_path.stat().st_mtime
        thumbnail_mtime = thumbnail_path.stat().st_mtime
        return image_mtime > thumbnail_mtime
    except OSError:
        return True


def process_directory(directory: Path, root_folder: Path, force_regenerate: bool = False) -> tuple[int, int]:
    """
    Traite un répertoire pour générer les miniatures manquantes.

    Args:
        directory: Répertoire à traiter
        root_folder: Dossier racine configuré
        force_regenerate: Si True, régénère toutes les miniatures même si elles existent

    Returns:
        Tuple (nombre de miniatures générées, nombre d'erreurs)
    """
    generated = 0
    errors = 0

    if not directory.exists():
        logger.warning(f"Répertoire inexistant: {directory}")
        return generated, errors

    logger.debug(f"Traitement du répertoire: {directory}")

    # Parcourt tous les fichiers du répertoire
    for item in directory.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
            # Vérifie si on doit générer la miniature
            if force_regenerate or should_regenerate_thumbnail(item, root_folder):
                thumbnail_path = get_thumbnail_path(item, root_folder)

                if generate_thumbnail(item, thumbnail_path):
                    generated += 1
                else:
                    errors += 1

        elif item.is_dir() and item.name != THUMBNAIL_FOLDER_NAME:
            # Traite récursivement les sous-dossiers (sauf le dossier de miniatures)
            sub_generated, sub_errors = process_directory(item, root_folder, force_regenerate)
            generated += sub_generated
            errors += sub_errors

    return generated, errors


def run_thumbnail_generation_job(force_regenerate: bool = False):
    """
    Lance le job de génération de miniatures pour tous les dossiers configurés.

    Args:
        force_regenerate: Si True, régénère toutes les miniatures même si elles existent
    """
    logger.info("=== Début du job de génération de miniatures ===")

    total_generated = 0
    total_errors = 0

    # Traite chaque dossier configuré
    for folder_config in IMAGE_FOLDERS:
        folder_path = Path(folder_config["path"])

        if not folder_path.exists():
            logger.warning(f"Dossier configuré inexistant: {folder_path}")
            continue

        logger.info(f"Traitement du dossier configuré: {folder_config['name']} ({folder_path})")
        generated, errors = process_directory(folder_path, folder_path, force_regenerate)

        total_generated += generated
        total_errors += errors

        if generated > 0 or errors > 0:
            logger.info(f"Dossier '{folder_config['name']}' : {generated} miniatures générées, {errors} erreurs")

    if total_generated > 0 or total_errors > 0:
        logger.info(f"=== Fin du job de génération de miniatures ===")
        logger.info(f"Total: {total_generated} miniatures générées, {total_errors} erreurs")
    else:
        logger.info("=== Toutes les miniatures sont à jour ===")

    return total_generated, total_errors


if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Lance le job
    run_thumbnail_generation_job()