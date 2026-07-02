from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel

class Permission(BaseModel):
  slug = fields.CharField(max_length=100, unique=True) # e.g. "ticket:close", "user:edit"
  description = fields.TextField()
  app_window = fields.ForeignKeyField('models.AppWindow', related_name='permissions', null=True)