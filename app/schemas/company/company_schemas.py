from pydantic import BaseModel, ConfigDict
from app.schemas.local import LocalResponse

class CompanyCreate(BaseModel):
    name: str
    acronym: str | None = None

class CompanyUpdate(BaseModel):
    name: str | None = None
    acronym: str | None = None

class CompanyResponse(BaseModel):
    id: int
    name: str
    acronym: str | None
    deactivated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
        
class CompanyOut(BaseModel):
    id: int
    name: str
    acronym: str | None
    deactivated_at: str | None = None
    locals: list[LocalResponse] = []

    model_config = ConfigDict(from_attributes=True)
