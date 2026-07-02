import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status

from app.database.models.user import User
from app.routers.auth.auth_router import get_current_active_user
from app.core.permissions import PermissionChecker
from app.services.service_api_key.service_api_key_service import ServiceApiKeyService
from app.schemas.service_api_key_schemas import (
    ServiceApiKeyCreate,
    ServiceApiKeyCreatedResponse,
    ServiceApiKeyResponse,
    PaginatedServiceApiKeyResponse,
    RevokeRequest,
    PaginatedApiKeyAuditLogResponse
)

router = APIRouter(
    prefix="/service-api-keys",
    tags=["Service API Keys"],
    dependencies=[Depends(get_current_active_user), Depends(PermissionChecker("api_key:manage"))]
)

@router.post("", response_model=ServiceApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ServiceApiKeyCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Creates a new Service API Key.
    Returns the raw key only once.
    """
    return await ServiceApiKeyService.create_api_key(data, current_user.id)

@router.get("", response_model=PaginatedServiceApiKeyResponse)
async def list_api_keys(
    environment: Optional[str] = Query(None, description="Filter by environment"),
    key_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """
    Lists API Keys (without the raw key value).
    """
    return await ServiceApiKeyService.list_keys(environment, key_status, page, size)

@router.post("/{key_uuid}/revoke", response_model=ServiceApiKeyResponse)
async def revoke_api_key(
    key_uuid: uuid.UUID = Path(...),
    data: RevokeRequest = RevokeRequest(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Revokes an active API Key.
    """
    result = await ServiceApiKeyService.revoke_key(key_uuid, current_user.id, data.reason)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found or already revoked")
    return result

@router.post("/{key_uuid}/rotate", response_model=ServiceApiKeyCreatedResponse)
async def rotate_api_key(
    key_uuid: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Rotates an API Key: creates a new one with same properties and revokes the old one.
    """
    result = await ServiceApiKeyService.rotate_key(key_uuid, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
    return result

@router.get("/{key_uuid}/audit", response_model=PaginatedApiKeyAuditLogResponse)
async def get_audit_logs(
    key_uuid: uuid.UUID = Path(...),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100)
):
    """
    Gets the audit trail for a specific API Key.
    """
    return await ServiceApiKeyService.get_audit_logs(key_uuid, page, size)
