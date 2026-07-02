from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel


class Role(BaseModel):
  name = fields.CharField(max_length=100)
  company = fields.ForeignKeyField('models.Company', null=True) # Se null, é uma role global
  permissions = fields.ManyToManyField('models.Permission', related_name='roles')
  users = fields.ManyToManyField('models.User', related_name='roles')
  
  # Valida a navegação para o role
  accessible_windows = fields.ManyToManyField(
      'models.AppWindow', 
      related_name='roles', 
      forward_key='appwindow_id', 
      backward_key='role_id'
  )