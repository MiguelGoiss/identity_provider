from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from .base import BaseModel


class UserLog(BaseModel):
  id = fields.BigIntField(pk=True)
  user_target = fields.ForeignKeyField('models.User', related_name='audit_logs')
  changed_by = fields.ForeignKeyField('models.User', related_name='changes_made', null=True)
  
  action = fields.CharField(max_length=50) # UPDATE, DELETE, CREATE, LOGIN_ATTEMPT
  table_affected = fields.CharField(max_length=50) # "users", "user_contacts"
  
  # Store the diff
  old_values = fields.JSONField(null=True)
  new_values = fields.JSONField(null=True)
  
  timestamp = fields.DatetimeField(auto_now_add=True)