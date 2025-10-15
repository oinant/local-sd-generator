from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from sd_generator_webui.config import VALID_GUIDS, READ_ONLY_GUIDS

security = HTTPBearer()


class AuthService:
    @staticmethod
    def validate_guid(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
        """Valide le GUID d'authentification."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification requis",
                headers={"WWW-Authenticate": "Bearer"},
            )

        guid = credentials.credentials
        if guid not in VALID_GUIDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GUID d'authentification invalide",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return guid

    @staticmethod
    def check_write_permission(guid: str) -> None:
        """Vérifie si le GUID a les permissions d'écriture (génération)."""
        if guid in READ_ONLY_GUIDS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions insuffisantes pour générer des images"
            )

    @staticmethod
    def get_user_info(guid: str) -> dict:
        """Retourne les informations de l'utilisateur basées sur le GUID."""
        if guid not in VALID_GUIDS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GUID invalide"
            )

        is_read_only = guid in READ_ONLY_GUIDS
        is_admin = guid == VALID_GUIDS[0]  # Premier GUID = admin

        return {
            "guid": guid,
            "is_admin": is_admin,
            "is_read_only": is_read_only,
            "can_generate": not is_read_only,
            "can_view": True
        }