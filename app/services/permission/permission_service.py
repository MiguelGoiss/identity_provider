from typing import List, Optional
from app.database.repository.permission.permission_repository import PermissionRepository, ADVANCED_SLUG
from app.database.models.permission import Permission
from app.schemas.permission_schemas import PermissionCreate, PermissionUpdate


class PermissionService:

    @staticmethod
    async def list_permissions(include_advanced: bool = False) -> List[Permission]:
        if include_advanced:
            return await PermissionRepository.list_all()
        return await PermissionRepository.list_ui_permissions()

    @staticmethod
    async def create_permission(data: PermissionCreate) -> Permission:
        return await PermissionRepository.create_permission(data)

    @staticmethod
    async def update_permission(permission_id: int, data: PermissionUpdate) -> Optional[Permission]:
        return await PermissionRepository.update_permission(permission_id, data)
