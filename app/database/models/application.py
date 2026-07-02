from tortoise import fields
from .base import BaseModel


class Application(BaseModel):
    slug = fields.CharField(max_length=50, unique=True)
    # ex: "helpdesk", "hrm", "contabilidade"
    name = fields.CharField(max_length=100)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "applications"
