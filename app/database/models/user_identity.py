from tortoise import fields
from .base import BaseModel
from app.crypto.globals import crypto_service

class UserIdentity(BaseModel):
  user = fields.ForeignKeyField("models.User", related_name="identities")
  identity_type = fields.CharField(max_length=50)  # ex: "email", "username", "nif"
  is_primary = fields.BooleanField(default=False)
  is_verified = fields.BooleanField(default=False)
  verified_at = fields.DatetimeField(null=True)
  # --- Colunas Encryption at Rest (Fase 2) ---
  identifier_enc = fields.TextField(null=True)
  identifier_idx = fields.CharField(max_length=64, null=True, unique=True, index=True)
  identifier_key_version = fields.SmallIntField(default=1)

  @property
  def identifier(self):
    if not self.identifier_enc:
      return None
    return crypto_service.decrypt(self.identifier_enc, "user_identity.identifier")

  class Meta:
    table = "user_identities"
