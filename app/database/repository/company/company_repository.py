from typing import List, Optional
from tortoise.transactions import in_transaction
from app.database.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from datetime import datetime, timezone

class CompanyRepository:

    @staticmethod
    async def create_company(company_data: CompanyCreate) -> Company:
        return await Company.create(**company_data.model_dump())

    @staticmethod
    async def get_companies() -> List[Company]:
        return await Company.all().prefetch_related('locals')

    @staticmethod
    async def get_company_by_id(company_id: int) -> Optional[Company]:
        return await Company.get_or_none(id=company_id).prefetch_related('locals')

    @staticmethod
    async def update_company(company_id: int, company_data: CompanyUpdate) -> Optional[Company]:
        company = await Company.get_or_none(id=company_id)
        if not company:
            return None
        
        update_data = company_data.model_dump(exclude_unset=True)
        if update_data:
            await company.update_from_dict(update_data)
            await company.save()
            
        return company

    @staticmethod
    async def delete_company(company_id: int) -> bool:
        company = await Company.get_or_none(id=company_id)
        if not company:
            return False
            
        company.deactivated_at = datetime.now(timezone.utc)
        await company.save()
        return True
