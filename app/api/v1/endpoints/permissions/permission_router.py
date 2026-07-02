from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.schemas.permission_schemas import PermissionCreate, PermissionUpdate, PermissionResponse
from app.services.permission.permission_service import PermissionService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/permissions", tags=["Permissions"])

# ------------------------------------------------------------------ #
# UI Endpoints  (visible to normal role managers)
# ------------------------------------------------------------------ #

@router.get("", response_model=list[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(PermissionChecker("role:read")),
):
    """
    List all permissions suitable for UI role assignment.
    The special `permission:manage_advanced` slug is excluded from this list.
    """
    return await PermissionService.list_permissions(include_advanced=False)


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    data: PermissionCreate,
    current_user: User = Depends(PermissionChecker("permission:manage")),
):
    """
    Create a UI-level permission.
    Protected by `permission:manage`.
    """
    return await PermissionService.create_permission(data)


@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    data: PermissionUpdate,
    permission_id: int = Path(..., description="ID da permissão"),
    current_user: User = Depends(PermissionChecker("permission:manage")),
):
    """Update the description of a permission."""
    updated = await PermissionService.update_permission(permission_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return updated


# ------------------------------------------------------------------ #
# Advanced Endpoints  (protected by permission:manage_advanced)
# This permission is inserted manually in the DB and never shown in the
# normal UI permission list.
# ------------------------------------------------------------------ #

@router.get("/advanced", response_model=list[PermissionResponse])
async def list_all_permissions_advanced(
    current_user: User = Depends(PermissionChecker("permission:manage_advanced")),
):
    """
    List ALL permissions including system/admin ones.
    Requires `permission:manage_advanced` (assigned manually in DB).
    """
    return await PermissionService.list_permissions(include_advanced=True)


@router.post("/advanced", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_advanced_permission(
    data: PermissionCreate,
    current_user: User = Depends(PermissionChecker("permission:manage_advanced")),
):
    """
    Create any permission, including system/admin ones.
    Requires `permission:manage_advanced` (assigned manually in DB).
    """
    return await PermissionService.create_permission(data)
