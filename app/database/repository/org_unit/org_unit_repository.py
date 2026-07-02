from typing import List, Optional
from tortoise import Tortoise
from app.database.models.org_unit import OrgUnit
from app.schemas.org_unit_schemas import OrgUnitCreate, OrgUnitUpdate


class OrgUnitRepository:

    @staticmethod
    async def create(data: OrgUnitCreate) -> OrgUnit:
        return await OrgUnit.create(
            name=data.name,
            type_id=data.type_id,
            company_id=data.company_id,
            parent_id=data.parent_id,
        )

    @staticmethod
    async def get_all(
        page: int = 1,
        size: int = 10,
        filters: dict = None,
        orders: list = None
    ) -> tuple[List[OrgUnit], int]:
        qs = OrgUnit.all()
        
        if filters:
            qs = qs.filter(**filters)
            
        if orders:
            qs = qs.order_by(*orders)
        else:
            qs = qs.order_by("name")
            
        qs = qs.distinct()
        
        total = await qs.count()
        items = await qs.offset((page - 1) * size).limit(size).prefetch_related("type")
        
        return items, total

    @staticmethod
    async def get_by_id(org_unit_id: int) -> Optional[OrgUnit]:
        return await OrgUnit.get_or_none(id=org_unit_id).prefetch_related("type")

    @staticmethod
    async def update(org_unit_id: int, data: OrgUnitUpdate) -> Optional[OrgUnit]:
        obj = await OrgUnit.get_or_none(id=org_unit_id)
        if not obj:
            return None
        update_dict = data.model_dump(exclude_unset=True)
        if update_dict:
            obj.update_from_dict(update_dict)
            await obj.save()
        return await OrgUnit.get(id=org_unit_id).prefetch_related("type")

    @staticmethod
    async def soft_delete(org_unit_id: int) -> bool:
        """Desactiva a unidade organizacional (soft delete)."""
        obj = await OrgUnit.get_or_none(id=org_unit_id)
        if not obj:
            return False
        obj.is_active = False
        await obj.save()
        return True

    @staticmethod
    async def get_tree(root_id: int) -> list[dict]:
        """Árvore completa a partir de uma OrgUnit usando CTE recursiva."""
        conn = Tortoise.get_connection("authentication")
        query = """
            WITH RECURSIVE hierarchy AS (
                SELECT
                    ou.id, ou.name, ou.parent_id, out_t.name AS type_name, 0 AS depth
                FROM org_units ou
                JOIN org_unit_types out_t ON ou.type_id = out_t.id
                WHERE ou.id = %s AND ou.is_active = TRUE

                UNION ALL

                SELECT
                    ou.id, ou.name, ou.parent_id, out_t.name AS type_name, h.depth + 1
                FROM org_units ou
                JOIN org_unit_types out_t ON ou.type_id = out_t.id
                INNER JOIN hierarchy h ON ou.parent_id = h.id
                WHERE ou.is_active = TRUE
            )
            SELECT * FROM hierarchy ORDER BY depth, name;
        """
        results = await conn.execute_query_dict(query, [root_id])
        return results

    @staticmethod
    async def get_ancestors(org_unit_id: int) -> list[dict]:
        """Caminho ascendente de uma OrgUnit até à raiz."""
        conn = Tortoise.get_connection("authentication")
        query = """
            WITH RECURSIVE ancestors AS (
                SELECT
                    ou.id, ou.name, ou.parent_id, out_t.name AS type_name, 0 AS depth
                FROM org_units ou
                JOIN org_unit_types out_t ON ou.type_id = out_t.id
                WHERE ou.id = %s AND ou.is_active = TRUE

                UNION ALL

                SELECT
                    ou.id, ou.name, ou.parent_id, out_t.name AS type_name, a.depth + 1
                FROM org_units ou
                JOIN org_unit_types out_t ON ou.type_id = out_t.id
                INNER JOIN ancestors a ON ou.id = a.parent_id
                WHERE ou.is_active = TRUE
            )
            SELECT * FROM ancestors ORDER BY depth DESC;
        """
        results = await conn.execute_query_dict(query, [org_unit_id])
        return results
