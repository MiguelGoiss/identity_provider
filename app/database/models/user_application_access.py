from tortoise import fields
from .base import BaseModel


class UserApplicationAccess(BaseModel):
    user = fields.ForeignKeyField(
        "models.User", related_name="app_accesses"
    )
    application = fields.ForeignKeyField(
        "models.Application", related_name="user_accesses"
    )
    granted_at = fields.DatetimeField(auto_now_add=True)
    granted_by = fields.ForeignKeyField(
        "models.User", related_name="granted_accesses"
    )

    class Meta:
        table = "user_application_access"
        unique_together = (("user", "application"),)
