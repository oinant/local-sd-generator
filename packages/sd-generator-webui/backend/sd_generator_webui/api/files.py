"""API endpoints pour la gestion des fichiers et structure de dossiers."""

import os
from pathlib import Path
from typing import List, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from sd_generator_webui.auth import AuthService
from sd_generator_webui.config import IMAGE_FOLDERS

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/tree")
async def get_file_tree(
    path: str = None,
    user_guid: str = Depends(AuthService.validate_guid)
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Retourne la structure de fichiers pour le treeview avec lazy loading optimisé.
    """
    try:
        if path is None:
            # Structure racine - rapide, pas de récursivité
            tree = {
                "id": "root",
                "name": "Images générées",
                "type": "root",
                "children": []
            }

            # Ajoute chaque dossier configuré (niveau racine seulement)
            for idx, folder_config in enumerate(IMAGE_FOLDERS):
                folder_path = Path(folder_config["path"])

                # Crée le dossier s'il n'existe pas
                folder_path.mkdir(parents=True, exist_ok=True)

                has_children = _has_subdirectories(folder_path) or folder_config["type"] == "sessions"
                folder_item = {
                    "id": f"root-{idx}",
                    "name": folder_config["name"],
                    "type": folder_config["type"],
                    "path": str(folder_path),
                    "hasChildren": has_children
                }

                # Initialise children comme tableau vide si le nœud a des enfants
                # Cela permet à Vuetify d'afficher le bouton d'expansion
                if has_children:
                    folder_item["children"] = []

                # Comptage uniforme : toujours imageCount
                if folder_config["type"] == "sessions":
                    folder_item["sessionCount"] = _count_subdirectories(folder_path)
                    # Pas de comptage récursif d'images ici - trop lent
                else:
                    folder_item["imageCount"] = _count_images_in_directory(folder_path)

                tree["children"].append(folder_item)

            return tree
        else:
            # Chargement lazy des enfants d'un dossier spécifique
            return _get_directory_children(path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture de la structure: {str(e)}")


def _get_directory_children(directory_path: str) -> List[Dict[str, Any]]:
    """Retourne les enfants d'un répertoire pour le lazy loading optimisé."""
    path = Path(directory_path)
    children = []

    if not path.exists():
        return children

    # Parcourt tous les éléments du dossier
    for item in path.iterdir():
        if item.is_dir():
            # Ignore le dossier de miniatures
            if item.name == ".thumbnails":
                continue

            has_subdirs = _has_subdirectories(item)
            has_images = _has_images_quick_check(item)

            # Tous les dossiers sont de type "folder" maintenant
            # On ne fait plus la distinction session/folder dans le tree
            item_type = "folder"

            # Génère un ID safe en remplaçant les caractères problématiques
            safe_path = str(item).replace('/', '_').replace('\\', '_').replace(':', '_')
            child_item = {
                "id": f"dir-{safe_path}",
                "name": item.name,
                "type": item_type,
                "path": str(item),
                "hasChildren": has_subdirs
            }

            # Initialise children comme tableau vide si le nœud a des sous-dossiers
            if has_subdirs:
                child_item["children"] = []

            # Ne compte pas les images pour éviter les ralentissements
            # Le comptage sera fait à la demande quand l'utilisateur ouvre le dossier

            children.append(child_item)

    # Trie par nom
    children.sort(key=lambda x: x["name"].lower())
    return children


def _has_images_quick_check(directory: Path) -> bool:
    """Vérification rapide s'il y a des images (arrête dès la première trouvée)."""
    if not directory.exists():
        return False

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    try:
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                return True  # Arrête dès qu'on trouve une image
        return False
    except (PermissionError, OSError):
        return False


def _has_subdirectories(directory: Path) -> bool:
    """Vérifie si un répertoire contient des sous-dossiers."""
    if not directory.exists():
        return False

    try:
        return any(item.is_dir() for item in directory.iterdir())
    except (PermissionError, OSError):
        return False


def _count_subdirectories(directory: Path) -> int:
    """Compte le nombre de sous-dossiers."""
    if not directory.exists():
        return 0

    try:
        return sum(1 for item in directory.iterdir() if item.is_dir())
    except (PermissionError, OSError):
        return 0




def _count_images_in_directory(directory: Path) -> int:
    """Compte les fichiers image dans un répertoire (non-récursif)."""
    if not directory.exists():
        return 0

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    count = 0
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            count += 1

    return count


def _count_images_recursive(directory: Path) -> int:
    """Compte les fichiers image dans un répertoire et ses sous-dossiers récursivement."""
    if not directory.exists():
        return 0

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    count = 0

    try:
        for item in directory.rglob('*'):
            if item.is_file() and item.suffix.lower() in image_extensions:
                count += 1
    except (PermissionError, OSError):
        # Fallback : comptage non-récursif si problème de permissions
        count = _count_images_in_directory(directory)

    return count


def _get_directory_tree_recursive(directory: Path, parent_type: str = "folder") -> List[Dict[str, Any]]:
    """
    Construit récursivement l'arbre des dossiers avec comptage d'images.

    Args:
        directory: Répertoire à explorer
        parent_type: Type du dossier parent ('sessions', 'folder', etc.)
    """
    if not directory.exists():
        return []

    children = []

    try:
        # Parcourt tous les éléments du dossier
        for item in directory.iterdir():
            if item.is_dir():
                # Compte les images dans ce dossier (directement et récursivement)
                images_direct = _count_images_in_directory(item)
                images_recursive = _count_images_recursive(item)
                has_subdirs = _has_subdirectories(item)

                # Détermine le type de dossier
                if parent_type == "sessions" and images_direct > 0:
                    item_type = "session"
                else:
                    item_type = "folder"

                # Génère un ID unique et safe
                safe_path = str(item).replace('/', '_').replace('\\', '_').replace(':', '_')
                child_item = {
                    "id": f"dir-{safe_path}",
                    "name": item.name,
                    "type": item_type,
                    "path": str(item),
                    "imageCount": images_recursive,  # Toujours le compte récursif
                    "children": []
                }

                # Ajoute les métadonnées spécifiques
                if item_type == "session":
                    child_item["directImageCount"] = images_direct  # Images directes dans la session
                elif has_subdirs:
                    child_item["folderCount"] = _count_subdirectories(item)

                # Charge récursivement les enfants si nécessaire
                if has_subdirs:
                    child_item["children"] = _get_directory_tree_recursive(item, item_type)

                children.append(child_item)

    except (PermissionError, OSError):
        pass  # Ignore les dossiers inaccessibles

    # Trie par nom
    children.sort(key=lambda x: x["name"].lower())
    return children


@router.get("/images")
async def get_images(
    path: str = None,
    user_guid: str = Depends(AuthService.validate_guid)
) -> List[Dict[str, Any]]:
    """
    Retourne la liste des images dans un dossier donné.

    Args:
        path: Chemin du dossier à scanner (optionnel, défaut = tous)
    """
    try:
        images = []

        if path:
            # Scan du dossier spécifique
            folder_path = Path(path)
            if folder_path.exists():
                images = _scan_images_in_directory(folder_path)
        else:
            # Quand aucun path n'est spécifié, on ne retourne aucune image
            # L'utilisateur doit sélectionner un dossier spécifique pour voir les images
            images = []

        # Trie par date de modification (plus récent en premier)
        images.sort(key=lambda x: x.get("modified", 0), reverse=True)

        return images

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture des images: {str(e)}")


def _scan_images_in_directory(directory: Path) -> List[Dict[str, Any]]:
    """Scanne un répertoire et retourne la liste des images avec métadonnées."""
    if not directory.exists():
        return []

    images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            # Statistiques du fichier
            stat = file_path.stat()

            # Détermine le dossier parent (session)
            session_name = directory.name if directory.parent.name != "apioutput" else "default"

            # Calcule le chemin relatif pour l'URL de service
            try:
                # Essaie de calculer le chemin relatif par rapport aux dossiers configurés
                relative_path = None
                for folder_config in IMAGE_FOLDERS:
                    folder_root = Path(folder_config["path"]).resolve()
                    try:
                        relative_path = file_path.resolve().relative_to(folder_root)
                        break
                    except ValueError:
                        continue

                # Fallback si aucun dossier racine ne correspond
                if relative_path is None:
                    relative_path = file_path.name

            except Exception:
                relative_path = file_path.name

            # Cherche le dossier racine pour cette image
            root_folder = None
            for folder_config in IMAGE_FOLDERS:
                folder_root = Path(folder_config["path"]).resolve()
                try:
                    file_path.resolve().relative_to(folder_root)
                    root_folder = folder_root
                    break
                except ValueError:
                    continue

            image_info = {
                "id": str(hash(str(file_path))),  # ID unique basé sur le chemin
                "name": file_path.name,
                "url": f"/api/files/serve/{relative_path}",
                "path": str(relative_path),
                "session": session_name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                # Les images dans .thumbnails sont déjà des miniatures
                "thumbnail": f"/api/files/serve/{relative_path}"
            }

            images.append(image_info)

    return images


@router.get("/serve/{file_path:path}")
async def serve_image(file_path: str):
    """
    Sert un fichier image.

    Args:
        file_path: Chemin relatif vers le fichier
    """
    from fastapi.responses import FileResponse

    # Sécurité : vérification du chemin
    full_path = Path(file_path).resolve()

    # Vérifie que le fichier est dans un des dossiers autorisés
    allowed = False
    for folder_config in IMAGE_FOLDERS:
        folder_path = Path(folder_config["path"]).resolve()
        try:
            full_path.relative_to(folder_path)
            allowed = True
            break
        except ValueError:
            continue

    if not allowed:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce fichier")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    return FileResponse(full_path)