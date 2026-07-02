from tortoise import fields
from .base import BaseModel
import uuid

class ApiKeyAuditLog(BaseModel):
    id = fields.BigIntField(pk=True)
    api_key = fields.ForeignKeyField("models.ServiceApiKey", related_name="audit_logs")
    api_key_uuid = fields.UUIDField()
    
    event_type = fields.CharField(max_length=50) # "created", "used", "revoked", "rotated", "expired"
    performed_by_user = fields.ForeignKeyField("models.User", related_name="api_key_actions", null=True)
    performed_by_service = fields.CharField(max_length=255, null=True)
    ip_address = fields.CharField(max_length=45, null=True)
    
    timestamp = fields.DatetimeField(auto_now_add=True)
    metadata = fields.JSONField(null=True)

    class Meta:
        table = "api_key_audit_logs"
