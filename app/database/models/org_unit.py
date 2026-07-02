from __future__ import annotations
from tortoise import fields
from .base import BaseModel


class OrgUnit(BaseModel):
    name = fields.CharField(max_length=150)
    type = fields.ForeignKeyField(
        "models.OrgUnitType", related_name="units"
    )
    company = fields.ForeignKeyField(
        "models.Company", related_name="org_units"
    )
    parent = fields.ForeignKeyField(
        "models.OrgUnit",
        null=True,
        related_name="children",
    )
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "org_units"
