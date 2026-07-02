from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

class BaseModel(models.Model):
  id = fields.IntField(pk=True)
  created_at = fields.DatetimeField(auto_now_add=True)
  updated_at = fields.DatetimeField(auto_now=True)
  
  class Meta:
    abstract = True
