from fastapi import APIRouter, Depends, BackgroundTasks

from auth import AuthService
from models import UserInfo

router = APIRouter(prefix="/api/auth", tags=["authentication"])


async def _warm_file_tree_cache():
    """Précharge le file tree en arrière-plan pour accélérer l'affichage."""
    from api.files import _get_directory_children
    from config import IMAGE_FOLDERS

    try:
        # Précharge l'arbre de chaque dossier racine
        for folder_config in IMAGE_FOLDERS:
            _get_directory_children(folder_config["path"])
    except Exception:
        # Ignore silencieusement les erreurs de warming
        pass


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    background_tasks: BackgroundTasks,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère les informations de l'utilisateur actuel."""
    # Lance le warming du cache en arrière-plan
    background_tasks.add_task(_warm_file_tree_cache)
    return AuthService.get_user_info(user_guid)


@router.get("/validate")
async def validate_token(
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Valide un token d'authentification."""
    return {
        "valid": True,
        "guid": user_guid,
        "message": "Token valide"
    }