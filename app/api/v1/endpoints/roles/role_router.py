from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.schemas.role_schemas import RoleCreate, RoleUpdate, RoleResponse, RoleDetailResponse, RoleListItem
from app.services.role.role_service import RoleService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleListItem])
async def list_roles(
    company_id: Optional[int] = None,
    current_user: User = Depends(PermissionChecker("role:read")),
):
    """
    List all roles.
    Pass `?company_id=<id>` to filter by company. Omit for global roles too.
    """
    return await RoleService.get_all_roles(company_id=company_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(PermissionChecker("role:create")),
):
    """
    Create a new role.
    Accepts `permission_ids` and `app_window_ids` to assign immediately.
    Set `company_id = null` for a global role.
    """
    role = await RoleService.create_role(data)
    await role.fetch_related("permissions")
    return {
        "id": role.id,
        "name": role.name,
        "company_id": role.company_id,
        "permissions": [
            {"id": p.id, "slug": p.slug, "description": p.description}
            for p in role.permissions
        ],
    }


@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role_detail(
    role_id: int = Path(..., description="ID do role"),
    current_user: User = Depends(PermissionChecker("role:read")),
):
    """
    Role detail view.
    Returns ALL permissions with `assigned: true|false` and ALL app_windows
    with `accessible: true|false` – designed for the UI multiselect flow.
    """
    detail = await RoleService.get_role_detail(role_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return detail


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    data: RoleUpdate,
    role_id: int = Path(..., description="ID do role"),
    current_user: User = Depends(PermissionChecker("role:edit")),
):
    """
    Update a role.
    `permission_ids` and `app_window_ids` are **replace** operations –
    the new list becomes the complete set.
    """
    role = await RoleService.update_role(role_id, data)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return {
        "id": role.id,
        "name": role.name,
        "company_id": role.company_id,
        "permissions": [
            {"id": p.id, "slug": p.slug, "description": p.description}
            for p in role.permissions
        ],
    }


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int = Path(..., description="ID do role"),
    current_user: User = Depends(PermissionChecker("role:delete")),
):
    """Delete a role (hard delete)."""
    success = await RoleService.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return None

@router.post("/{role_id}/users/{user_id}")
async def assign_role_to_user(
    role_id: int,
    user_id: int,
    current_user: User = Depends(PermissionChecker("user:edit")),
):
    """
    Assign a role to a specific user.
    """
    from app.database.repository.role.role_repository import RoleRepository
    success = await RoleRepository.add_role_to_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or Role not found")
    return {"msg": "Role added to user"}

