import uuid
from typing import Tuple, List, Optional
from datetime import datetime

from app.database.repository.service_api_key.service_api_key_repository import ServiceApiKeyRepository
from app.schemas.service_api_key_schemas import (
    ServiceApiKeyCreate,
    ServiceApiKeyCreatedResponse,
    ServiceApiKeyResponse,
    ApiKeyAuditLogResponse,
    PaginatedServiceApiKeyResponse,
    PaginatedApiKeyAuditLogResponse
)

class ServiceApiKeyService:

    @staticmethod
    async def create_api_key(data: ServiceApiKeyCreate, user_id: int) -> ServiceApiKeyCreatedResponse:
        raw_key, api_key = await ServiceApiKeyRepository.create_api_key(
            name=data.name,
            service_name=data.service_name,
            environment=data.environment,
            scopes=data.scopes,
            expires_at=data.expires_at,
            created_by_user_id=user_id
        )
        
        return ServiceApiKeyCreatedResponse(
            raw_key=raw_key,
            uuid=api_key.uuid,
            name=api_key.name,
            service_name=api_key.service_name,
            environment=api_key.environment,
            key_prefix=api_key.key_prefix,
            status=api_key.status,
            scopes=api_key.scopes,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at
        )

    @staticmethod
    async def list_keys(environment: Optional[str], status: Optional[str], page: int, size: int) -> PaginatedServiceApiKeyResponse:
        total, keys = await ServiceApiKeyRepository.list_keys(environment, status, page, size)
        items = [
            ServiceApiKeyResponse(
                uuid=k.uuid,
                name=k.name,
                service_name=k.service_name,
                environment=k.environment,
                key_prefix=k.key_prefix,
                status=k.status,
                scopes=k.scopes,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                expires_at=k.expires_at
            ) for k in keys
        ]
        return PaginatedServiceApiKeyResponse(total=total, items=items, page=page, size=size)

    @staticmethod
    async def revoke_key(key_uuid: uuid.UUID, user_id: int, reason: Optional[str]) -> Optional[ServiceApiKeyResponse]:
        api_key = await ServiceApiKeyRepository.get_by_uuid(key_uuid)
        if not api_key or api_key.status == "revoked":
            return None
            
        revoked_key = await ServiceApiKeyRepository.revoke_key(api_key, user_id, reason)
        return ServiceApiKeyResponse(
            uuid=revoked_key.uuid,
            name=revoked_key.name,
            service_name=revoked_key.service_name,
            environment=revoked_key.environment,
            key_prefix=revoked_key.key_prefix,
            status=revoked_key.status,
            scopes=revoked_key.scopes,
            created_at=revoked_key.created_at,
            last_used_at=revoked_key.last_used_at,
            expires_at=revoked_key.expires_at
        )

    @staticmethod
    async def rotate_key(key_uuid: uuid.UUID, user_id: int) -> Optional[ServiceApiKeyCreatedResponse]:
        api_key = await ServiceApiKeyRepository.get_by_uuid(key_uuid)
        if not api_key:
            return None
            
        raw_key, new_api_key = await ServiceApiKeyRepository.rotate_key(api_key, user_id)
        return ServiceApiKeyCreatedResponse(
            raw_key=raw_key,
            uuid=new_api_key.uuid,
            name=new_api_key.name,
            service_name=new_api_key.service_name,
            environment=new_api_key.environment,
            key_prefix=new_api_key.key_prefix,
            status=new_api_key.status,
            scopes=new_api_key.scopes,
            created_at=new_api_key.created_at,
            expires_at=new_api_key.expires_at
        )

    @staticmethod
    async def get_audit_logs(key_uuid: uuid.UUID, page: int, size: int) -> PaginatedApiKeyAuditLogResponse:
        total, logs = await ServiceApiKeyRepository.get_audit_logs(key_uuid, page, size)
        items = [
            ApiKeyAuditLogResponse(
                uuid=l.api_key_uuid,
                event_type=l.event_type,
                performed_by_user_id=l.performed_by_user_id,
                performed_by_service=l.performed_by_service,
                ip_address=l.ip_address,
                timestamp=l.timestamp,
                metadata=l.metadata
            ) for l in logs
        ]
        return PaginatedApiKeyAuditLogResponse(total=total, items=items, page=page, size=size)
