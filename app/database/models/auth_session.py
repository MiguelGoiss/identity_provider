from tortoise import fields
from .base import BaseModel

class AuthSession(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="auth_sessions")
    application = fields.ForeignKeyField("models.Application", related_name="auth_sessions", null=True)
    
    jti = fields.CharField(max_length=255, unique=True, index=True)
    issued_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()
    revoked_at = fields.DatetimeField(null=True)
    
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=512, null=True)

    class Meta:
        table = "auth_sessions"
