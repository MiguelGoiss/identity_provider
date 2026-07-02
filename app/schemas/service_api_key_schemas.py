from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

class ServiceApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    service_name: str = Field(..., max_length=255)
    environment: str = Field(..., max_length=50, pattern="^(development|staging|production)$")
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

class ServiceApiKeyCreatedResponse(BaseModel):
    raw_key: str
    uuid: uuid.UUID
    name: str
    service_name: str
    environment: str
    key_prefix: str
    status: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

class ServiceApiKeyResponse(BaseModel):
    uuid: uuid.UUID
    name: str
    service_name: str
    environment: str
    key_prefix: str
    status: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    
class RevokeRequest(BaseModel):
    reason: Optional[str] = None

class ApiKeyAuditLogResponse(BaseModel):
    uuid: uuid.UUID
    event_type: str
    performed_by_user_id: Optional[int]
    performed_by_service: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime
    metadata: Optional[dict]

class PaginatedServiceApiKeyResponse(BaseModel):
    total: int
    items: List[ServiceApiKeyResponse]
    page: int
    size: int

class PaginatedApiKeyAuditLogResponse(BaseModel):
    total: int
    items: List[ApiKeyAuditLogResponse]
    page: int
    size: int
