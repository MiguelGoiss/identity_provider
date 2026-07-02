from tortoise import fields
from .base import BaseModel
from app.crypto.globals import crypto_service

class PersonEmail(BaseModel):
  user = fields.ForeignKeyField("models.User", related_name="person_emails")
  is_primary = fields.BooleanField(default=False)
  is_verified = fields.BooleanField(default=False)
  verified_at = fields.DatetimeField(null=True)
  scope = fields.CharField(max_length=20, default='personal')
  # --- Colunas Encryption at Rest (Fase 2) ---
  email_enc = fields.TextField(null=True)
  email_idx = fields.CharField(max_length=64, null=True, index=True)
  email_key_version = fields.SmallIntField(default=1)

  @property
  def email(self):
    if not self.email_enc:
      return None
    return crypto_service.decrypt(self.email_enc, "person_email.email")

  class Meta:
    table = "person_emails"
    unique_together = (("user", "email_idx"),)
