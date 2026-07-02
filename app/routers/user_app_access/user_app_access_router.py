from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.schemas.application_schemas import UserAppAccessGrant, UserAppAccessResponse
from app.services.user_app_access.user_app_access_service import UserAppAccessService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/users/{user_id}/app-access", tags=["User App Access"])


@router.get("", response_model=list[UserAppAccessResponse])
async def list_user_app_access(
    user_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("user:read")),
):
    return await UserAppAccessService.list_user_accesses(user_id)


@router.post("", response_model=UserAppAccessResponse, status_code=status.HTTP_201_CREATED)
async def grant_app_access(
    data: UserAppAccessGrant,
    user_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("user:edit")),
):
    return await UserAppAccessService.grant_access(
        user_id=user_id,
        application_id=data.application_id,
        granted_by_id=current_user.id
    )


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_app_access(
    user_id: int = Path(...),
    app_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("user:edit")),
):
    success = await UserAppAccessService.revoke_access(user_id, app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access grant not found")
    return None
