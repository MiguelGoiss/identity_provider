from typing import Optional
from pydantic import BaseModel

class LocalCreate(BaseModel):
    name: str
    short: str
    background: Optional[str] = None
    text: Optional[str] = None
    company_id: int

class LocalUpdate(BaseModel):
    name: Optional[str] = None
    short: Optional[str] = None
    background: Optional[str] = None
    text: Optional[str] = None
    company_id: Optional[int] = None

class LocalResponse(BaseModel):
    id: int
    name: str
    short: str
    background: Optional[str]
    text: Optional[str]
    company_id: int

    class Config:
        from_attributes = True
