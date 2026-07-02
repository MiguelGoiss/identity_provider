from pydantic import BaseModel
from typing import Optional

class PermissionCreate(BaseModel):
    slug: str
    description: str
    app_window_id: Optional[int] = None

class PermissionUpdate(BaseModel):
    description: str
    app_window_id: Optional[int] = None

class PermissionResponse(BaseModel):
    id: int
    slug: str
    description: str
    app_window_id: Optional[int] = None

    class Config:
        from_attributes = True

class PermissionWithAssignment(BaseModel):
    """Permission enriched with assignment flag – used in role detail."""
    id: int
    slug: str
    description: str
    app_window_id: Optional[int] = None
    assigned: bool

    class Config:
        from_attributes = True
