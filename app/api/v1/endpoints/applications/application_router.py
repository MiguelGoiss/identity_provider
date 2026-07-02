from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.schemas.application_schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.services.application.application_service import ApplicationService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(PermissionChecker("application:read")),
):
    return await ApplicationService.get_all()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(PermissionChecker("application:create")),
):
    return await ApplicationService.create(data)


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    data: ApplicationUpdate,
    app_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("application:edit")),
):
    obj = await ApplicationService.update(app_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return obj
