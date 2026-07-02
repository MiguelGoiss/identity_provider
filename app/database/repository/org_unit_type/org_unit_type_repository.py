from typing import List
from app.database.models.org_unit_type import OrgUnitType
from app.schemas.org_unit_schemas import OrgUnitTypeCreate


class OrgUnitTypeRepository:

    @staticmethod
    async def create(data: OrgUnitTypeCreate) -> OrgUnitType:
        return await OrgUnitType.create(
            name=data.name,
            level=data.level
        )

    @staticmethod
    async def get_all(
        page: int = 1,
        size: int = 10,
        filters: dict = None,
        orders: list = None
    ) -> tuple[List[OrgUnitType], int]:
        qs = OrgUnitType.all()
        
        if filters:
            qs = qs.filter(**filters)
            
        if orders:
            qs = qs.order_by(*orders)
        else:
            qs = qs.order_by("level")
            
        qs = qs.distinct()
        
        total = await qs.count()
        items = await qs.offset((page - 1) * size).limit(size)
        
        return items, total

    @staticmethod
    async def delete(type_id: int) -> bool:
        obj = await OrgUnitType.get_or_none(id=type_id)
        if not obj:
            return False
        await obj.delete()
        return True
