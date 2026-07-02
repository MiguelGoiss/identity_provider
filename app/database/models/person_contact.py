from tortoise import fields
from .base import BaseModel
from app.crypto.globals import crypto_service

class ContactType(BaseModel):
  slug = fields.CharField(max_length=50, unique=True)   # "TELEMOVEL", "DDI"
  label = fields.CharField(max_length=100)              # "Telemóvel", "DDI"
  is_active = fields.BooleanField(default=True)

  class Meta:
    table = "contact_types"

class PersonContact(BaseModel):

  user = fields.ForeignKeyField("models.User", related_name="person_contacts")
  contact_type = fields.ForeignKeyField("models.ContactType", related_name="contacts")
  description = fields.CharField(max_length=255, null=True)
  is_public = fields.BooleanField(default=False)
  is_primary = fields.BooleanField(default=False)
  is_verified = fields.BooleanField(default=False)
  verified_at = fields.DatetimeField(null=True)
  scope = fields.CharField(max_length=20, default='personal')
  # --- Colunas Encryption at Rest (Fase 2) ---
  value_enc = fields.TextField(null=True)
  value_idx = fields.CharField(max_length=64, null=True, index=True)
  value_key_version = fields.SmallIntField(default=1)

  @property
  def value(self):
    if not self.value_enc:
      return None
    return crypto_service.decrypt(self.value_enc, "person_contact.value")

  class Meta:
    table = "person_contacts"