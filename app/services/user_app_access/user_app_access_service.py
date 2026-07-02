from app.database.repository.user_app_access.user_app_access_repository import UserAppAccessRepository
from app.schemas.application_schemas import UserAppAccessResponse


class UserAppAccessService:

    @staticmethod
    async def grant_access(user_id: int, application_id: int, granted_by_id: int) -> UserAppAccessResponse:
        access = await UserAppAccessRepository.grant_access(user_id, application_id, granted_by_id)
        await access.fetch_related("application")
        return UserAppAccessResponse(
            id=access.id,
            user_id=access.user_id,
            application_id=access.application_id,
            application_slug=access.application.slug,
            application_name=access.application.name,
        )

    @staticmethod
    async def revoke_access(user_id: int, application_id: int) -> bool:
        return await UserAppAccessRepository.revoke_access(user_id, application_id)

    @staticmethod
    async def list_user_accesses(user_id: int) -> list[UserAppAccessResponse]:
        rows = await UserAppAccessRepository.list_user_accesses(user_id)
        return [UserAppAccessResponse(**r) for r in rows]
