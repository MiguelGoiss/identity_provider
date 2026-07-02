from typing import Optional
from app.database.repository.org_unit.org_unit_repository import OrgUnitRepository
from app.schemas.org_unit_schemas import OrgUnitCreate, OrgUnitUpdate, OrgUnitResponse, OrgUnitTreeNode, OrgUnitListResponse
from app.utils.query_parser import QueryParser
import math


class OrgUnitService:

    @staticmethod
    async def create(data: OrgUnitCreate) -> OrgUnitResponse:
        obj = await OrgUnitRepository.create(data)
        await obj.fetch_related("type")
        return OrgUnitResponse.model_validate(obj)

    @staticmethod
    async def get_all(
        page: int,
        size: int,
        filters: list[str] | None = None,
        order: str | None = None
    ) -> OrgUnitListResponse:
        parsed_filters = QueryParser.parse_filters(filters)
        parsed_orders = QueryParser.parse_order(order)
        
        items, total = await OrgUnitRepository.get_all(page, size, parsed_filters, parsed_orders)
        
        pages = math.ceil(total / size) if size > 0 else 0
        next_page = page + 1 if page < pages else None
        previous_page = page - 1 if page > 1 else None
        
        return OrgUnitListResponse(
            items=[OrgUnitResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
            next_page=next_page,
            previous_page=previous_page
        )

    @staticmethod
    async def get_by_id(org_unit_id: int) -> Optional[OrgUnitResponse]:
        obj = await OrgUnitRepository.get_by_id(org_unit_id)
        if not obj:
            return None
        return OrgUnitResponse.model_validate(obj)

    @staticmethod
    async def update(org_unit_id: int, data: OrgUnitUpdate) -> Optional[OrgUnitResponse]:
        obj = await OrgUnitRepository.update(org_unit_id, data)
        if not obj:
            return None
        return OrgUnitResponse.model_validate(obj)

    @staticmethod
    async def soft_delete(org_unit_id: int) -> bool:
        return await OrgUnitRepository.soft_delete(org_unit_id)

    @staticmethod
    async def get_tree(root_id: int) -> list[OrgUnitTreeNode]:
        rows = await OrgUnitRepository.get_tree(root_id)
        return [OrgUnitTreeNode(**r) for r in rows]
