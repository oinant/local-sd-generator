from fastapi import APIRouter, Depends

from app.auth import AuthService
from app.models import UserInfo

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    user_guid: str = Depends(AuthService.validate_guid)
):
    """Récupère les informations de l'utilisateur actuel."""
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