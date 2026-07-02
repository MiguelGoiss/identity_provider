from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel

import uuid

class User(BaseModel):
  uuid = fields.UUIDField(unique=True, index=True, default=uuid.uuid4)
  
  # Autenticação
  hashed_password = fields.CharField(max_length=255, null=True)
  
  # Segurança e Recuperação
  recovery_secret = fields.CharField(max_length=255, null=True)
  recovery_secret_expires_at = fields.DatetimeField(null=True)
  recovery_attempts = fields.IntField(default=0)
  
  # Estado
  deactivated_at = fields.DatetimeField(null=True)
  deleted_at = fields.DatetimeField(null=True)
  last_time_seen = fields.DatetimeField(null=True)
  
  # Campo de texto para informação extra sem alterar o esquema.
  extra_info = fields.TextField(null=True)
  
  # Relacionamentos

  class Meta:
    table = "users"

