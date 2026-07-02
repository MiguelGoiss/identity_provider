from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.database.models.user import User
from app.api.v1.endpoints.auth.auth_router import get_current_active_user
from app.database.repository.role.role_repository import RoleRepository

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, user: Annotated[User, Depends(get_current_active_user)]):
        # 1. Get all permissions for the user
        user_permissions = await RoleRepository.get_user_permissions(user.id)
        
        # 2. Check if required permission is present
        if self.required_permission not in user_permissions:
            import logging
            logging.warning(f"User {user.id} attempted unauthorized action. Missing: {self.required_permission}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
