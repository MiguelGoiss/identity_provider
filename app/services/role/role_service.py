from typing import List, Optional
from app.database.repository.role.role_repository import RoleRepository
from app.database.models.role import Role
from app.schemas.role_schemas import RoleCreate, RoleUpdate


class RoleService:

    @staticmethod
    async def get_all_roles(company_id: Optional[int] = None) -> List[Role]:
        return await RoleRepository.get_all_roles(company_id)

    @staticmethod
    async def create_role(data: RoleCreate) -> Role:
        return await RoleRepository.create_role(data)

    @staticmethod
    async def get_role_detail(role_id: int) -> Optional[dict]:
        return await RoleRepository.get_role_detail(role_id)

    @staticmethod
    async def update_role(role_id: int, data: RoleUpdate) -> Optional[Role]:
        return await RoleRepository.update_role(role_id, data)

    @staticmethod
    async def delete_role(role_id: int) -> bool:
        return await RoleRepository.delete_role(role_id)
