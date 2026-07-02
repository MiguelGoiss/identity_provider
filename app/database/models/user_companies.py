from tortoise import fields
from .base import BaseModel
from app.crypto.globals import crypto_service

class UserCompany(BaseModel):
  user = fields.ForeignKeyField("models.User", related_name="companies")
  company = fields.ForeignKeyField("models.Company", related_name="users")
  is_primary = fields.BooleanField(default=False)
  
  local = fields.ForeignKeyField("models.Local", related_name="user_companies", null=True)
  org_unit = fields.ForeignKeyField("models.OrgUnit", related_name="user_companies", null=True)
  
  job_title = fields.CharField(max_length=100, null=True)
  admission_date = fields.DateField(null=True)
  termination_date = fields.DateField(null=True)
  employment_type = fields.CharField(max_length=50, null=True)
  status = fields.CharField(max_length=50, default="active", null=True)
  # --- Colunas Encryption at Rest (Fase 2) ---
  employee_number_enc = fields.TextField(null=True)
  employee_number_idx = fields.CharField(max_length=64, null=True, index=True)
  employee_number_key_version = fields.SmallIntField(default=1)
  
  @property
  def employee_number(self):
    if not self.employee_number_enc:
      return None
    return crypto_service.decrypt(self.employee_number_enc, "user_company.employee_number")
  
  class Meta:
    table = "user_companies"
    unique_together=((("user", "company"),))