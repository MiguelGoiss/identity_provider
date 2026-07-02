from pydantic import BaseModel
from typing import List, Optional
from app.schemas.permission_schemas import PermissionResponse, PermissionWithAssignment
from app.schemas.app_window_schemas import AppWindowResponse, AppWindowWithAccess


class RoleCreate(BaseModel):
    name: str
    company_id: Optional[int] = None
    permission_ids: List[int] = []
    app_window_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    app_window_ids: Optional[List[int]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    company_id: Optional[int] = None
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True


class RoleDetailResponse(BaseModel):
    """
    Full role detail – used by GET /roles/{role_id}.
    Returns ALL permissions and app_windows with assigned/accessible flags.
    """
    id: int
    name: str
    company_id: Optional[int] = None
    permissions: List[PermissionWithAssignment] = []
    app_windows: List[AppWindowWithAccess] = []

    class Config:
        from_attributes = True


class RoleListItem(BaseModel):
    id: int
    name: str
    company_id: Optional[int] = None

    class Config:
        from_attributes = True
