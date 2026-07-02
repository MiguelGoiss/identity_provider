from app.database.repository.org_unit_type.org_unit_type_repository import OrgUnitTypeRepository
from app.schemas.org_unit_schemas import OrgUnitTypeCreate, OrgUnitTypeResponse, OrgUnitTypeListResponse
from app.utils.query_parser import QueryParser
import math


class OrgUnitTypeService:

    @staticmethod
    async def create(data: OrgUnitTypeCreate) -> OrgUnitTypeResponse:
        obj = await OrgUnitTypeRepository.create(data)
        return OrgUnitTypeResponse.model_validate(obj)

    @staticmethod
    async def get_all(
        page: int,
        size: int,
        filters: list[str] | None = None,
        order: str | None = None
    ) -> OrgUnitTypeListResponse:
        parsed_filters = QueryParser.parse_filters(filters)
        parsed_orders = QueryParser.parse_order(order)
        
        items, total = await OrgUnitTypeRepository.get_all(page, size, parsed_filters, parsed_orders)
        
        pages = math.ceil(total / size) if size > 0 else 0
        next_page = page + 1 if page < pages else None
        previous_page = page - 1 if page > 1 else None
        
        return OrgUnitTypeListResponse(
            items=[OrgUnitTypeResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
            next_page=next_page,
            previous_page=previous_page
        )

    @staticmethod
    async def delete(type_id: int) -> bool:
        return await OrgUnitTypeRepository.delete(type_id)
