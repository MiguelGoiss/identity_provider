from pydantic import BaseModel
from typing import List, Optional


class AppWindowResponse(BaseModel):
    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order: int

    class Config:
        from_attributes = True


class AppWindowWithAccess(BaseModel):
    """AppWindow enriched with accessible flag – used in role detail."""
    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order: int
    accessible: bool

    class Config:
        from_attributes = True


class AppWindowSyncItem(BaseModel):
    """A single window/URI definition sent by the gateway or frontend."""
    name: str
    slug: str
    icon: Optional[str] = None
    parent_slug: Optional[str] = None  # resolved server-side to parent_id
    order: int = 0


class AppWindowSyncRequest(BaseModel):
    windows: List[AppWindowSyncItem]


class AppWindowSyncResult(BaseModel):
    created_count: int
    updated_count: int
