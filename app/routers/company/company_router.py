from typing import List
from fastapi import APIRouter, status, HTTPException, Path, Depends
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyOut
from app.services import CompanyService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(PermissionChecker("company:create"))
):
  return await CompanyService.create_company(company_data)

@router.get("", response_model=List[CompanyOut])
async def get_companies():
  return await CompanyService.get_companies()

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int = Path(..., description="The ID of the company")):
  company = await CompanyService.get_company_by_id(company_id)
  if not company:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
  return company

@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_data: CompanyUpdate,
    company_id: int = Path(..., description="The ID of the company"),
    current_user: User = Depends(PermissionChecker("company:edit"))
):
  company = await CompanyService.update_company(company_id, company_data)
  if not company:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
  return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int = Path(..., description="The ID of the company"),
    current_user: User = Depends(PermissionChecker("company:delete"))
):
  success = await CompanyService.delete_company(company_id)
  if not success:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
  return None

