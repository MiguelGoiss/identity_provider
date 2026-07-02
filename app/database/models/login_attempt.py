from tortoise import fields
from .base import BaseModel

class LoginAttempt(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="login_attempts", null=True)
    user_identity = fields.ForeignKeyField("models.UserIdentity", related_name="login_attempts", null=True)
    application = fields.ForeignKeyField("models.Application", related_name="login_attempts", null=True)
    
    identity_type = fields.CharField(max_length=50, null=True)
    identifier_used = fields.CharField(max_length=255, null=True)
    auth_method = fields.CharField(max_length=50, null=True)
    outcome = fields.CharField(max_length=50)
    
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=512, null=True)
    attempted_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "login_attempts"
