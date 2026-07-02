from typing import Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query

from app.schemas.org_unit_schemas import OrgUnitCreate, OrgUnitUpdate, OrgUnitResponse, OrgUnitTreeNode, OrgUnitListResponse
from app.services.org_unit.org_unit_service import OrgUnitService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/org-units", tags=["Organizational Units"])

@router.get("", response_model=OrgUnitListResponse)
async def list_org_units(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, description="Resultados por página"),
    filter: list[str] | None = Query(None, description="Filtros: campo:operador:valor"),
    order: str | None = Query(None, description="Ordenação (prefixo - para DESC)"),
    # _: User = Depends() #"org_unit:read")),
):
    return await OrgUnitService.get_all(page=page, size=size, filters=filter, order=order)


@router.get("/{org_unit_id}", response_model=OrgUnitResponse)
async def get_org_unit(
    org_unit_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("org_unit:read")),
):
    obj = await OrgUnitService.get_by_id(org_unit_id)
    if not obj:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return obj


@router.post("", response_model=OrgUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_org_unit(
    data: OrgUnitCreate,
    current_user: User = Depends(PermissionChecker("org_unit:create")),
):
    return await OrgUnitService.create(data)


@router.patch("/{org_unit_id}", response_model=OrgUnitResponse)
async def update_org_unit(
    data: OrgUnitUpdate,
    org_unit_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("org_unit:edit")),
):
    obj = await OrgUnitService.update(org_unit_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return obj


@router.delete("/{org_unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org_unit(
    org_unit_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("org_unit:delete")),
):
    success = await OrgUnitService.soft_delete(org_unit_id)
    if not success:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return None


@router.get("/{org_unit_id}/tree", response_model=list[OrgUnitTreeNode])
async def get_org_unit_tree(
    org_unit_id: int = Path(...),
    current_user: User = Depends(PermissionChecker("org_unit:read")),
):
    """
    Retorna a sub-árvore hierárquica a partir da OrgUnit indicada.
    Usado para visualização em org charts.
    """
    return await OrgUnitService.get_tree(org_unit_id)
