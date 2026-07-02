from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel


class AppWindow(BaseModel):
  name = fields.CharField(max_length=100) # Display name, e.g., "User Management"
  slug = fields.CharField(max_length=100, unique=True) # Frontend route, e.g., "/users"
  icon = fields.CharField(max_length=50, null=True) # e.g., "fa-users" or "users"

  # Self-referential FK for nested menus (Adjacency List pattern)
  parent = fields.ForeignKeyField('models.AppWindow', related_name='children', null=True)

  order = fields.IntField(default=0) # To control display order in the menu

  class Meta:
    table = "app_windows"