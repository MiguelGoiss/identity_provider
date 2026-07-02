from typing import List, Optional
from app.database.repository.local.local_repository import LocalRepository
from app.schemas.local import LocalCreate, LocalUpdate, LocalResponse

class LocalService:

    @staticmethod
    async def create_local(local_data: LocalCreate) -> LocalResponse:
        local = await LocalRepository.create_local(local_data)
        return LocalResponse.model_validate(local)

    @staticmethod
    async def get_locals() -> List[LocalResponse]:
        locals_list = await LocalRepository.get_locals()
        return [LocalResponse.model_validate(loc) for loc in locals_list]

    @staticmethod
    async def get_local_by_id(local_id: int) -> Optional[LocalResponse]:
        local = await LocalRepository.get_local_by_id(local_id)
        if not local:
            return None
        return LocalResponse.model_validate(local)

    @staticmethod
    async def update_local(local_id: int, local_data: LocalUpdate) -> Optional[LocalResponse]:
        local = await LocalRepository.update_local(local_id, local_data)
        if not local:
            return None
        return LocalResponse.model_validate(local)

    @staticmethod
    async def delete_local(local_id: int) -> bool:
        return await LocalRepository.delete_local(local_id)
