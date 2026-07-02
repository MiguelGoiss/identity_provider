from typing import List
from fastapi import APIRouter, status, HTTPException, Path, Depends
from app.schemas.local import LocalCreate, LocalUpdate, LocalResponse
from app.services import LocalService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(
    prefix="/locals",
    tags=["Locals"]
)

@router.post("", response_model=LocalResponse, status_code=status.HTTP_201_CREATED)
async def create_local(
    local_data: LocalCreate,
    current_user: User = Depends(PermissionChecker("local:create"))
):
    return await LocalService.create_local(local_data)

@router.get("", response_model=List[LocalResponse])
async def get_locals():
    return await LocalService.get_locals()

@router.get("/{local_id}", response_model=LocalResponse)
async def get_local(local_id: int = Path(..., description="The ID of the local")):
    local = await LocalService.get_local_by_id(local_id)
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local not found")
    return local

@router.patch("/{local_id}", response_model=LocalResponse)
async def update_local(
    local_data: LocalUpdate,
    local_id: int = Path(..., description="The ID of the local"),
    current_user: User = Depends(PermissionChecker("local:edit"))
):
    local = await LocalService.update_local(local_id, local_data)
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local not found")
    return local

@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_local(
    local_id: int = Path(..., description="The ID of the local"),
    current_user: User = Depends(PermissionChecker("local:delete"))
):
    success = await LocalService.delete_local(local_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local not found")
    return None
