from typing import Any
from app.database.repository.user.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserListResponse, UserUpdate, UserBatchDetailsOut, UserDetailsOut
from app.utils.query_parser import QueryParser
import math

class UserService:
    
  @staticmethod
  async def create_user(user_data: UserCreate) -> UserResponse:
    # Here we could add business logic, e.g., check if username already exists if not handled by DB constraints,
    # or send welcome emails, etc.
    
    user = await UserRepository.create_user(user_data)
    
    created_user = await UserRepository.get_user_by_id(user.id)
    
    return UserResponse.model_validate(created_user)

  @staticmethod
  async def get_users(
      page: int,
      size: int,
      filters: list[str] | None = None,
      order: str | None = None
  ) -> UserListResponse:
    
    parsed_filters = QueryParser.parse_filters(filters)
    parsed_orders = QueryParser.parse_order(order)
    
    items, total = await UserRepository.get_users(page, size, parsed_filters, parsed_orders)
    
    pages = math.ceil(total / size)
    
    next_page = page + 1 if page < pages else None
    previous_page = page - 1 if page > 1 else None
    
    return UserListResponse(
      items=[UserResponse.model_validate(item) for item in items],
      total=total,
      page=page,
      size=size,
      pages=pages,
      next_page=next_page,
      previous_page=previous_page
    )

  @staticmethod
  async def update_user(user_id: int, user_data: UserUpdate) -> UserResponse | None:
    user = await UserRepository.update_user(user_id, user_data)
    if not user:
      return None
        
    # Fetch fresh data with relations
    updated_user = await UserRepository.get_user_by_id(user.id)
    return UserResponse.model_validate(updated_user)

  @staticmethod
  async def deactivate_user(user_id: int) -> bool:
    return await UserRepository.deactivate_user(user_id)

  @staticmethod
  async def update_photo(user_id: int, photo_uri: str) -> bool:
    return await UserRepository.update_photo(user_id, photo_uri)
  
  @staticmethod
  async def fetch_batch_users(user_ids: list[str]) -> list[UserBatchDetailsOut] | None:
    users = await UserRepository.get_batch_users(user_ids)
    if not users:
      return None
    return users
  
  @staticmethod
  async def get_user_by_id(user_id: int) -> UserDetailsOut | None:
    user = await UserRepository.get_user_by_id(user_id)
    if not user:
      return None
    return UserDetailsOut.model_validate(user)

  @staticmethod
  async def get_user_login_attempts(user_id: int):
    return await UserRepository.get_user_login_attempts(user_id)

  @staticmethod
  async def revoke_all_sessions(user_id: int):
    await UserRepository.revoke_all_sessions(user_id)

  @staticmethod
  async def add_user_company(user_id: int, data: Any):
    return await UserRepository.add_user_company(user_id, data)

  @staticmethod
  async def update_user_company(user_id: int, company_id: int, data: Any):
    return await UserRepository.update_user_company(user_id, company_id, data)

  @staticmethod
  async def remove_user_company(user_id: int, company_id: int):
    return await UserRepository.remove_user_company(user_id, company_id)