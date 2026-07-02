from tortoise import fields
from .base import BaseModel
import uuid

class ServiceApiKey(BaseModel):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(unique=True, index=True, default=uuid.uuid4)
    name = fields.CharField(max_length=255)
    service_name = fields.CharField(max_length=255)
    environment = fields.CharField(max_length=50)
    key_prefix = fields.CharField(max_length=12, unique=True, index=True)
    key_hash = fields.CharField(max_length=64)
    status = fields.CharField(max_length=50, default="active")
    scopes = fields.JSONField()
    
    created_by_user = fields.ForeignKeyField("models.User", related_name="created_api_keys", null=True)
    
    last_used_at = fields.DatetimeField(null=True)
    last_used_ip = fields.CharField(max_length=45, null=True)
    expires_at = fields.DatetimeField(null=True)
    revoked_at = fields.DatetimeField(null=True)
    revoked_by_user = fields.ForeignKeyField("models.User", related_name="revoked_api_keys", null=True)
    revocation_reason = fields.TextField(null=True)

    class Meta:
        table = "service_api_keys"
