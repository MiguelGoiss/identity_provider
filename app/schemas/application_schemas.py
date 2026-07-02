from pydantic import BaseModel, ConfigDict
from typing import Optional


# --- Application ---

class ApplicationCreate(BaseModel):
    slug: str
    name: str

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class ApplicationResponse(BaseModel):
    id: int
    slug: str
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# --- User Application Access ---

class UserAppAccessGrant(BaseModel):
    application_id: int
    granted_by_id: int

class UserAppAccessResponse(BaseModel):
    id: int
    user_id: int
    application_id: int
    application_slug: str | None = None
    application_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
