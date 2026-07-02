from typing import List
from app.database.models.user_application_access import UserApplicationAccess
from app.database.models.application import Application


class UserAppAccessRepository:

    @staticmethod
    async def grant_access(user_id: int, application_id: int, granted_by_id: int) -> UserApplicationAccess:
        """Concede acesso a uma app para um utilizador."""
        access, created = await UserApplicationAccess.get_or_create(
            user_id=user_id,
            application_id=application_id,
            defaults={"granted_by_id": granted_by_id}
        )
        return access

    @staticmethod
    async def revoke_access(user_id: int, app_id: int) -> bool:
        """Revoga o acesso de um utilizador a uma app."""
        deleted_count = await UserApplicationAccess.filter(
            user_id=user_id,
            application_id=app_id
        ).delete()
        return deleted_count > 0

    @staticmethod
    async def list_user_accesses(user_id: int) -> List[dict]:
        """Lista todas as apps a que um utilizador tem acesso."""
        accesses = await UserApplicationAccess.filter(
            user_id=user_id
        ).prefetch_related("application")

        return [
            {
                "id": a.id,
                "user_id": a.user_id,
                "application_id": a.application_id,
                "application_slug": a.application.slug,
                "application_name": a.application.name,
            }
            for a in accesses
        ]
