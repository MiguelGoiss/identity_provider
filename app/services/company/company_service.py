from typing import List, Optional
from app.database.repository.company.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyOut

class CompanyService:

    @staticmethod
    async def create_company(company_data: CompanyCreate) -> CompanyResponse:
        company = await CompanyRepository.create_company(company_data)
        return CompanyResponse.model_validate(company)

    @staticmethod
    async def get_companies() -> List[CompanyOut]:
        companies = await CompanyRepository.get_companies()
        return [CompanyOut.model_validate(comp) for comp in companies]

    @staticmethod
    async def get_company_by_id(company_id: int) -> Optional[CompanyResponse]:
        company = await CompanyRepository.get_company_by_id(company_id)
        if not company:
            return None
        return CompanyResponse.model_validate(company)

    @staticmethod
    async def update_company(company_id: int, company_data: CompanyUpdate) -> Optional[CompanyResponse]:
        company = await CompanyRepository.update_company(company_id, company_data)
        if not company:
            return None
        return CompanyResponse.model_validate(company)

    @staticmethod
    async def delete_company(company_id: int) -> bool:
        return await CompanyRepository.delete_company(company_id)


