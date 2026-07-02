from typing import Any
from fastapi import APIRouter, status, Query, HTTPException, Path, Body, Depends, UploadFile, File
from app.schemas.user import UserCreate, UserResponse, UserListResponse, UserUpdate, BatchUserResponse, UserBatchDetail, UserBatchDetailsOut, UserDetailsOut
from app.services import UserService
from app.dependencies import verify_internal_access
from app.core.permissions import PermissionChecker
from app.services.user.photo_service import PhotoService

router = APIRouter(
  prefix="/users",
  tags=["Users"]
)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionChecker("user:create"))])
async def create_user(user_data: UserCreate):
  """
  Create a new user.
  """
  return await UserService.create_user(user_data)

@router.get("", response_model=UserListResponse, dependencies=[Depends(PermissionChecker("user:read"))])
async def get_users(
  page: int = Query(1, ge=1, description="Número da página"),
  size: int = Query(10, ge=1, description="Resultados por página"),
  filter: list[str] | None = Query(None, description="Lista de filtros no formato campo:operador:valor"),
  order: str | None = Query(None, description="Order by pelo campo (separado pela vírgula, prefixo com - para desc)")
):
  """
  Obtém uma lista de users com paginação, pesquisa avançada (filtros), e ordenação.
  
  Filtros: campo:operador:valor 
  (ex: first_name:eq:Johnny no uri deve ser algo do género "/users?page=1&size=10&filter=first_name:eq:Johnny"
  para vários filtros deve ser algo do tipo "/users?page=1&size=10&filter=first_name:eq:Johnny&filter=last_name:ilike:Depp")
  
  Operadores: eq(=), neq(!=), gt(>), gte(>=), lt(<), lte(<=), like, ilike, in, not_in, isnull
  """
  return await UserService.get_users(page, size, filter, order)

@router.post("/batch", dependencies=[Depends(verify_internal_access)], response_model=dict[str, UserBatchDetailsOut])
async def get_users_batch(
  user_ids: list[str] = Body(..., embed=True)
):
  """
  Aceita lista de UUIDs. Devolve dict {uuid: UserBatchDetail} incluindo contactos.
  """
  if not user_ids:
    return {}
  
  users_list = await UserService.fetch_batch_users(user_ids)
  if not users_list:
    return {}
  
  return {
    str(u['uuid']): UserBatchDetailsOut(**u) 
    for u in users_list
  }
  
@router.post("/batch-list", dependencies=[Depends(verify_internal_access)], response_model=list[UserBatchDetailsOut])
async def get_users_batch_list(
  user_ids: list[str] = Body(..., embed=True)
):

  if not user_ids:
    return []
  
  users_list = await UserService.fetch_batch_users(user_ids)
  if not users_list:
    return []
  
  return users_list 


@router.get("/details/{user_id}", response_model=UserDetailsOut, dependencies=[Depends(PermissionChecker("user:read"))])
async def get_user(
  user_id: int = Path(..., description="O ID do user a obter")
):
  """
  Obtém os detalhes de um user específico pelo ID.
  """
  user = await UserService.get_user_by_id(user_id)
  if not user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
  return user

@router.patch("/details/{user_id}", response_model=UserResponse, dependencies=[Depends(PermissionChecker("user:edit"))])
async def update_user(
  user_id: int = Path(..., description="O ID do user a dar update"),
  user_data: UserUpdate = ...
):
  """
  Update a user.
  """
  updated_user = await UserService.update_user(user_id, user_data)
  if not updated_user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
  return updated_user

@router.put("/details/{user_id}/photo", response_model=UserResponse, dependencies=[Depends(PermissionChecker("user:edit"))])
async def update_user_photo(
  user_id: int = Path(..., description="O ID do user para atualizar a foto"),
  file: UploadFile = File(...)
):
  """
  Atualiza a foto de perfil do utilizador. O ficheiro não deve exceder 5MB.
  """
  photo_uri = await PhotoService.save_profile_photo(user_id, file)
  success = await UserService.update_photo(user_id, photo_uri)
  if not success:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
  
  updated_user = await UserService.get_user_by_id(user_id)
  return UserResponse.model_validate(updated_user)

@router.delete("/details/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(PermissionChecker("user:delete"))])
async def deactivate_user(
  user_id: int = Path(..., description="The ID of the user to deactivate")
):
  """
  Deactivate a user (soft delete).
  """
  success = await UserService.deactivate_user(user_id)
  if not success:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
  return None

@router.get("/details/{user_id}/login-attempts", dependencies=[Depends(PermissionChecker("user:read"))])
async def get_user_login_attempts(
  user_id: int = Path(..., description="O ID do user a consultar histórico")
):
  """
  Obtém o histórico de tentativas de login do utilizador.
  """
  return await UserService.get_user_login_attempts(user_id)

@router.post("/details/{user_id}/revoke-all-sessions", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(PermissionChecker("user:edit"))])
async def revoke_all_sessions(
  user_id: int = Path(..., description="O ID do user para revogar sessões")
):
  """
  Revoga todas as sessões ativas do utilizador.
  """
  await UserService.revoke_all_sessions(user_id)
  return None

@router.post("/details/{user_id}/companies", response_model=Any, status_code=status.HTTP_201_CREATED, dependencies=[Depends(PermissionChecker("user_company:create"))])
async def add_user_company(
  user_id: int = Path(..., description="O ID do user"),
  company_data: Any = Body(...)
):
  """
  Adiciona uma empresa a um utilizador com detalhes laborais.
  """
  from app.schemas.user import UserCompanyInput
  company = await UserService.add_user_company(user_id, UserCompanyInput(**company_data))
  if not company:
    raise HTTPException(status_code=404, detail="User not found")
  # Return updated user to show new company relation
  return await UserService.get_user_by_id(user_id)

@router.patch("/details/{user_id}/companies/{company_id}", response_model=Any, dependencies=[Depends(PermissionChecker("user_company:edit"))])
async def update_user_company(
  user_id: int = Path(..., description="O ID do user"),
  company_id: int = Path(..., description="O ID da empresa"),
  company_data: Any = Body(...)
):
  """
  Atualiza os dados laborais de um utilizador numa empresa.
  """
  from app.schemas.user import UserCompanyUpdateInput
  company = await UserService.update_user_company(user_id, company_id, UserCompanyUpdateInput(**company_data))
  if not company:
    raise HTTPException(status_code=404, detail="User or Company not found")
  return await UserService.get_user_by_id(user_id)

@router.delete("/details/{user_id}/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(PermissionChecker("user_company:delete"))])
async def remove_user_company(
  user_id: int = Path(..., description="O ID do user"),
  company_id: int = Path(..., description="O ID da empresa")
):
  """
  Remove um utilizador de uma empresa.
  """
  success = await UserService.remove_user_company(user_id, company_id)
  if not success:
    raise HTTPException(status_code=404, detail="User or Company not found")
  return None

