from pydantic import BaseModel, ConfigDict
from typing import Optional


# --- OrgUnitType ---

class OrgUnitTypeCreate(BaseModel):
    name: str
    level: int

class OrgUnitTypeResponse(BaseModel):
    id: int
    name: str
    level: int

    model_config = ConfigDict(from_attributes=True)


# --- OrgUnit ---

class OrgUnitCreate(BaseModel):
    name: str
    type_id: int
    company_id: int
    parent_id: Optional[int] = None

class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    type_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

class OrgUnitResponse(BaseModel):
    id: int
    name: str
    type_id: int
    company_id: int
    parent_id: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class OrgUnitTreeNode(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    type_name: str
    depth: int

class OrgUnitOut(BaseModel):
    """Schema compacto para inclusão no /me e JWT."""
    id: int
    name: str
    type_name: str
    parent_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class OrgUnitTypeListResponse(BaseModel):
    items: list[OrgUnitTypeResponse]
    total: int
    page: int
    size: int
    pages: int
    next_page: Optional[int]
    previous_page: Optional[int]

class OrgUnitListResponse(BaseModel):
    items: list[OrgUnitResponse]
    total: int
    page: int
    size: int
    pages: int
    next_page: Optional[int]
    previous_page: Optional[int]

