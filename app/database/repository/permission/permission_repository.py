from typing import List, Optional
from app.database.models.permission import Permission
from app.schemas.permission_schemas import PermissionCreate, PermissionUpdate

ADVANCED_SLUG = "permission:manage_advanced"


class PermissionRepository:

    @staticmethod
    async def create_permission(permission_data: PermissionCreate) -> Permission:
        permission, created = await Permission.get_or_create(
            slug=permission_data.slug,
            defaults={
                "description": permission_data.description,
                "app_window_id": permission_data.app_window_id
            }
        )
        if not created:
            changed = False
            if permission.description != permission_data.description:
                permission.description = permission_data.description
                changed = True
            if permission.app_window_id != permission_data.app_window_id:
                permission.app_window_id = permission_data.app_window_id
                changed = True
            if changed:
                await permission.save()
        return permission

    @staticmethod
    async def get_permission_by_slug(slug: str) -> Optional[Permission]:
        return await Permission.get_or_none(slug=slug)

    @staticmethod
    async def get_by_id(permission_id: int) -> Optional[Permission]:
        return await Permission.get_or_none(id=permission_id)

    @staticmethod
    async def list_all() -> List[Permission]:
        """Return all permissions (including advanced/system ones)."""
        return await Permission.all().order_by("slug")

    @staticmethod
    async def list_ui_permissions() -> List[Permission]:
        """
        Return permissions suitable for UI assignment.
        Excludes the special permission:manage_advanced slug so it doesn't
        appear in role-edit multiselects.
        """
        return await Permission.filter(slug__not=ADVANCED_SLUG).order_by("slug")

    @staticmethod
    async def update_permission(permission_id: int, data: PermissionUpdate) -> Optional[Permission]:
        permission = await Permission.get_or_none(id=permission_id)
        if not permission:
            return None
        permission.description = data.description
        permission.app_window_id = data.app_window_id
        await permission.save()
        return permission
