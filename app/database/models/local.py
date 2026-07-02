from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel


class Local(BaseModel):
  name = fields.CharField(max_length=155)
  short = fields.CharField(max_length=15)
  background = fields.CharField(max_length=15, null=True)
  text = fields.CharField(max_length=15, null=True)
  
  company = fields.ForeignKeyField("models.Company", related_name="locals")