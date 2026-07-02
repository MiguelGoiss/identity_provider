from tortoise import fields
from .base import BaseModel


class OrgUnitType(BaseModel):
    name = fields.CharField(max_length=100, unique=True)
    level = fields.IntField()
    # 0 = topo (ex: Empresa), 1 = Direcção, 2 = Departamento, 3 = Secção...
    # Apenas informativo — a hierarquia real é definida pelo parent_id em OrgUnit

    class Meta:
        table = "org_unit_types"
        ordering = ["level"]
