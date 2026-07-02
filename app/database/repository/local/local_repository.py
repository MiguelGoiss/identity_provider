from typing import List, Optional
from tortoise.transactions import in_transaction
from app.database.models.local import Local
from app.schemas.local import LocalCreate, LocalUpdate

class LocalRepository:

    @staticmethod
    async def create_local(local_data: LocalCreate) -> Local:
        return await Local.create(**local_data.model_dump())

    @staticmethod
    async def get_locals() -> List[Local]:
        return await Local.all()

    @staticmethod
    async def get_local_by_id(local_id: int) -> Optional[Local]:
        return await Local.get_or_none(id=local_id)

    @staticmethod
    async def update_local(local_id: int, local_data: LocalUpdate) -> Optional[Local]:
        local = await Local.get_or_none(id=local_id)
        if not local:
            return None
        
        update_data = local_data.model_dump(exclude_unset=True)
        if update_data:
            await local.update_from_dict(update_data)
            await local.save()
            
        return local

    @staticmethod
    async def delete_local(local_id: int) -> bool:
        local = await Local.get_or_none(id=local_id)
        if not local:
            return False
            
        await local.delete()
        return True
