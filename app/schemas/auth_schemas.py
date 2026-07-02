from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class RefreshSchema(BaseModel):
    refresh_token: str
    
class UserIdentifier(BaseModel):
    username: str


# --- /me Response Schemas ---

class OrgUnitOut(BaseModel):
    id: int
    name: str
    type_name: str
    parent_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    id: str
    uuid: str
    first_name: str
    last_name: str
    username: str | None = None
    employee_number: str | None = None
    job_title: str | None = None
    org_unit: OrgUnitOut | None = None
    apps: list[str] = []  # slugs das apps autorizadas