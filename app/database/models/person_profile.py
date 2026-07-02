from tortoise import fields
from .base import BaseModel
from datetime import date
from app.crypto.globals import crypto_service

class PersonProfile(BaseModel):
    user = fields.OneToOneField("models.User", related_name="profile")
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    preferred_name = fields.CharField(max_length=100, null=True)
    locale = fields.CharField(max_length=10, default="pt-PT")
    time_zone = fields.CharField(max_length=50, default="Europe/Lisbon")
    photo_uri = fields.CharField(max_length=255, null=True)
    # --- Colunas Encryption at Rest (Fase 2) ---
    full_name_enc = fields.TextField(null=True)
    full_name_idx = fields.CharField(max_length=64, null=True, index=True)
    full_name_key_version = fields.SmallIntField(default=1)
    tax_id_enc = fields.TextField(null=True)
    tax_id_idx = fields.CharField(max_length=64, null=True, unique=True, index=True)
    tax_id_key_version = fields.SmallIntField(default=1)
    birth_date_enc = fields.TextField(null=True)
    birth_date_key_version = fields.SmallIntField(default=1)

    @property
    def full_name(self):
        if not self.full_name_enc:
            return None
        return crypto_service.decrypt(self.full_name_enc, "person_profile.full_name")

    @property
    def tax_id(self):
        if not self.tax_id_enc:
            return None
        return crypto_service.decrypt(self.tax_id_enc, "person_profile.tax_id")

    @property
    def birth_date(self):
        if not self.birth_date_enc:
            return None
        decrypted = crypto_service.decrypt(self.birth_date_enc, "person_profile.birth_date")
        if decrypted:
            try:
                return date.fromisoformat(decrypted)
            except ValueError:
                return decrypted
        return None

    class Meta:
        table = "person_profiles"
