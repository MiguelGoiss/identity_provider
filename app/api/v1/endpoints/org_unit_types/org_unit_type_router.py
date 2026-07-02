from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query

from app.schemas.org_unit_schemas import OrgUnitTypeCreate, OrgUnitTypeResponse, OrgUnitTypeListResponse
from app.services.org_unit_type.org_unit_type_service import OrgUnitTypeService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/org-unit-types", tags=["Organizational Unit Types"])


@router.get("", response_model=OrgUnitTypeListResponse)
async def list_org_unit_types(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, description="Resultados por página"),
    filter: list[str] | None = Query(None, description="Filtros: campo:operador:valor"),
    order: str | None = Query(None, description="Ordenação (prefixo - para DESC)"),
    current_user: User = Depends(PermissionChecker("org_unit_type:read")),
):
    return await OrgUnitTypeService.get_all(page=page, size=size, filters=filter, order=order)


@router.post("", response_model=OrgUnitTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_org_unit_type(
    data: OrgUnitTypeCreate,
    current_user: User = Depends(PermissionChecker("org_unit_type:create")),
):
    return await OrgUnitTypeService.create(data)


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org_unit_type(
    type_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("org_unit_type:delete")),
):
    success = await OrgUnitTypeService.delete(type_id)
    if not success:
        raise HTTPException(status_code=404, detail="OrgUnitType not found")
    return None
