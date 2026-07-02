from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel

class Company(BaseModel):
  name = fields.CharField(max_length=255)
  acronym = fields.CharField(max_length=15, unique=True, null=True)
  deactivated_at = fields.DatetimeField(null=True)