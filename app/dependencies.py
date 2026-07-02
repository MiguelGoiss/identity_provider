from fastapi import Header, HTTPException, status, Request
from typing import List, Optional
from datetime import datetime, timezone
import asyncio

from app.core.config import settings
from app.core.api_key_security import verify_api_key
from app.database.models.service_api_key import ServiceApiKey
from app.database.models.api_key_audit_log import ApiKeyAuditLog

class VerifyInternalAccess:
    def __init__(self, required_scopes: List[str] = None):
        self.required_scopes = required_scopes or []

    async def __call__(self, request: Request, x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")):
        if not x_internal_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Internal Access Denied")
            
        # Legacy Fallback
        if x_internal_key == settings.INTERNAL_API_KEY:
            return True
            
        # New API Key validation
        if not x_internal_key.startswith("sak_"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key format")
            
        key_prefix = x_internal_key[:12]
        api_key = await ServiceApiKey.get_or_none(key_prefix=key_prefix)
        
        if not api_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
            
        if not verify_api_key(x_internal_key, api_key.key_hash):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
            
        if api_key.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"API Key is {api_key.status}")
            
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API Key expired")
            
        if self.required_scopes:
            for scope in self.required_scopes:
                if scope not in api_key.scopes:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing required scope: {scope}")
                    
        # Update last_used_at async
        asyncio.create_task(self._log_usage(api_key, request.client.host if request.client else None))
        
        return True

    async def _log_usage(self, api_key: ServiceApiKey, ip_address: str):
        try:
            api_key.last_used_at = datetime.now(timezone.utc)
            if ip_address:
                api_key.last_used_ip = ip_address
            await api_key.save(update_fields=["last_used_at", "last_used_ip"])
            
            await ApiKeyAuditLog.create(
                api_key=api_key,
                api_key_uuid=api_key.uuid,
                event_type="used",
                performed_by_service=api_key.service_name,
                ip_address=ip_address
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to log API key usage: {e}")

verify_internal_access = VerifyInternalAccess()

async def get_current_user(
  request: Request,
  x_internal_key: str = Header(None, alias="X-Internal-Key"),
  x_user_id: str = Header(None, alias="X-User-Id")
):
  """
  Extracts the user ID from the headers, but ONLY if the request
  carries a valid internal API key.
  """
  await verify_internal_access(request=request, x_internal_key=x_internal_key)
  return {"id": x_user_id}