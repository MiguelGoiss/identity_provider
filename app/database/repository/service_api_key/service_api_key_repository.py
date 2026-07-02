from typing import List, Tuple, Optional
from datetime import datetime, timezone
import uuid

from app.database.models.service_api_key import ServiceApiKey
from app.database.models.api_key_audit_log import ApiKeyAuditLog
from app.core.api_key_security import generate_api_key

class ServiceApiKeyRepository:
    
    @staticmethod
    async def create_api_key(
        name: str,
        service_name: str,
        environment: str,
        scopes: list[str],
        expires_at: Optional[datetime],
        created_by_user_id: int
    ) -> Tuple[str, ServiceApiKey]:
        """
        Creates a new Service API Key and logs the creation.
        Returns the raw_key (to be shown once) and the ServiceApiKey instance.
        """
        raw_key, key_prefix, key_hash = generate_api_key(environment)
        
        api_key = await ServiceApiKey.create(
            name=name,
            service_name=service_name,
            environment=environment,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            expires_at=expires_at,
            created_by_user_id=created_by_user_id,
            status="active"
        )
        
        await ApiKeyAuditLog.create(
            api_key=api_key,
            api_key_uuid=api_key.uuid,
            event_type="created",
            performed_by_user_id=created_by_user_id
        )
        
        return raw_key, api_key

    @staticmethod
    async def get_by_uuid(key_uuid: uuid.UUID) -> Optional[ServiceApiKey]:
        return await ServiceApiKey.get_or_none(uuid=key_uuid)

    @staticmethod
    async def list_keys(
        environment: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Tuple[int, List[ServiceApiKey]]:
        query = ServiceApiKey.all()
        
        if environment:
            query = query.filter(environment=environment)
        if status:
            query = query.filter(status=status)
            
        total = await query.count()
        keys = await query.offset((page - 1) * size).limit(size).order_by("-created_at")
        
        return total, keys

    @staticmethod
    async def revoke_key(
        api_key: ServiceApiKey,
        revoked_by_user_id: int,
        reason: Optional[str] = None
    ) -> ServiceApiKey:
        api_key.status = "revoked"
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoked_by_user_id = revoked_by_user_id
        api_key.revocation_reason = reason
        await api_key.save()
        
        await ApiKeyAuditLog.create(
            api_key=api_key,
            api_key_uuid=api_key.uuid,
            event_type="revoked",
            performed_by_user_id=revoked_by_user_id,
            metadata={"reason": reason}
        )
        
        return api_key

    @staticmethod
    async def rotate_key(
        api_key: ServiceApiKey,
        rotated_by_user_id: int
    ) -> Tuple[str, ServiceApiKey]:
        """
        Rotates an API key: creates a new one with same properties and revokes the old one.
        Returns the new raw_key and the new ServiceApiKey instance.
        """
        raw_key, new_api_key = await ServiceApiKeyRepository.create_api_key(
            name=f"{api_key.name} (Rotated)",
            service_name=api_key.service_name,
            environment=api_key.environment,
            scopes=api_key.scopes,
            expires_at=api_key.expires_at,
            created_by_user_id=rotated_by_user_id
        )
        
        # Revoke the old key
        await ServiceApiKeyRepository.revoke_key(
            api_key=api_key,
            revoked_by_user_id=rotated_by_user_id,
            reason="Rotated"
        )
        
        # Log rotation for both
        await ApiKeyAuditLog.create(
            api_key=api_key,
            api_key_uuid=api_key.uuid,
            event_type="rotated",
            performed_by_user_id=rotated_by_user_id,
            metadata={"new_key_uuid": str(new_api_key.uuid)}
        )
        
        return raw_key, new_api_key

    @staticmethod
    async def get_audit_logs(key_uuid: uuid.UUID, page: int = 1, size: int = 50) -> Tuple[int, List[ApiKeyAuditLog]]:
        query = ApiKeyAuditLog.filter(api_key_uuid=key_uuid)
        total = await query.count()
        logs = await query.offset((page - 1) * size).limit(size).order_by("-timestamp")
        return total, logs
