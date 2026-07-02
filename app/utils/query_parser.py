from typing import Any, Callable
from tortoise.expressions import Q
import logging
from dataclasses import dataclass
from app.crypto.key_provider import KeyProvider
from app.crypto.crypto_service import CryptoService
from app.crypto.blind_indexer import BlindIndexer
from app.crypto.normalizers import normalize_email, normalize_phone, normalize_text, normalize_date

logger = logging.getLogger(__name__)

class UnsupportedFilterError(Exception):
    pass

@dataclass(frozen=True)
class FieldSearchPolicy:
    orm_field: str
    mode: str          # "plain" | "blind_index"
    allowed_ops: frozenset[str]
    normalizer: Callable[[str], str] | None
    orderable: bool

class QueryParser:
    """
    Parses query parameters for filtering and ordering.
    Format: field:operator:value
    """
    
    OPERATORS = {
      "eq": "",
      "neq": "__not",
      "gt": "__gt",
      "gte": "__gte",
      "lt": "__lt",
      "lte": "__lte",
      "like": "__contains",
      "ilike": "__icontains",
      "in": "__in",
      "not_in": "__not_in",
      "isnull": "__isnull"
    }

    _blind_ops = frozenset({"eq", "in"})
    _plain_ops = frozenset(OPERATORS.keys())
    
    FIELDS = {
      # User fields
      "id": FieldSearchPolicy("id", "plain", frozenset({"eq", "in"}), None, True),
      "first_name": FieldSearchPolicy("profile__first_name", "plain", _plain_ops, None, True),
      "last_name": FieldSearchPolicy("profile__last_name", "plain", _plain_ops, None, True),
      "username": FieldSearchPolicy("identities__identifier_idx", "blind_index", _blind_ops, normalize_text, False),
      "employee_number": FieldSearchPolicy("companies__employee_number_idx", "blind_index", _blind_ops, normalize_text, False),
      "tax_id": FieldSearchPolicy("profile__tax_id_idx", "blind_index", _blind_ops, normalize_text, False),
      "created_at": FieldSearchPolicy("created_at", "plain", _plain_ops, None, True),
      
      # Related fields
      "company_id": FieldSearchPolicy("companies__company__id", "plain", _plain_ops, None, True),
      "company_name": FieldSearchPolicy("companies__company__name", "plain", _plain_ops, None, True),
      "local_id": FieldSearchPolicy("companies__local__id", "plain", _plain_ops, None, True),
      "local_name": FieldSearchPolicy("companies__local__name", "plain", _plain_ops, None, True),
      
      # Reverse relations
      "email": FieldSearchPolicy("person_emails__email_idx", "blind_index", _blind_ops, normalize_email, False),
      "contact": FieldSearchPolicy("person_contacts__value_idx", "blind_index", _blind_ops, normalize_text, False),
      
      # OrgUnit fields
      "org_unit_name": FieldSearchPolicy("name", "plain", _plain_ops, None, True),
      "org_unit_type_id": FieldSearchPolicy("type_id", "plain", _plain_ops, None, True),
      "org_unit_company_id": FieldSearchPolicy("company_id", "plain", _plain_ops, None, True),
      "org_unit_parent_id": FieldSearchPolicy("parent_id", "plain", _plain_ops, None, True),
      "org_unit_is_active": FieldSearchPolicy("is_active", "plain", _plain_ops, None, True),
      
      # OrgUnitType fields
      "org_unit_type_name": FieldSearchPolicy("name", "plain", _plain_ops, None, True),
      "org_unit_type_level": FieldSearchPolicy("level", "plain", _plain_ops, None, True),
    }

    @classmethod
    def parse_filters(cls, filters: list[str]) -> dict[str, Any]:
      parsed_filters = {}
      if not filters:
        return parsed_filters
          
      for filter_str in filters:
        parts = filter_str.split(":", 2)
        if len(parts) != 3:
          raise UnsupportedFilterError(f"Invalid filter format: {filter_str}")
            
        field, operator, value = parts
        
        if field not in cls.FIELDS:
          raise UnsupportedFilterError(f"Field not allowed: {field}")
            
        policy = cls.FIELDS[field]
        
        if operator not in cls.OPERATORS:
          raise UnsupportedFilterError(f"Operator not allowed: {operator}")
          
        if operator not in policy.allowed_ops:
          raise UnsupportedFilterError(f"Operator '{operator}' not allowed for field '{field}'")
        
        orm_field = policy.orm_field
        orm_operator = cls.OPERATORS[operator]
        
        # Process value based on mode
        if policy.mode == "blind_index":
            _kp = KeyProvider()
            _indexer = BlindIndexer(_kp)
            
            def process_value(val: str) -> str:
                norm_val = policy.normalizer(val) if policy.normalizer else val
                
                # Determine context from field name for indexer. This has to match the repository.
                context_map = {
                    "username": "user_identity.identifier",
                    "employee_number": "user_company.employee_number",
                    "tax_id": "person_profile.tax_id",
                    "email": "person_email.email",
                    "contact": "person_contact.value",
                }
                ctx = context_map.get(field, "default")
                if not norm_val:
                    return ""
                return _indexer.compute(ctx, norm_val)

            if operator in ["in", "not_in"]:
                val_list = value.split(",")
                value = [process_value(v) for v in val_list]
            else:
                value = process_value(value)
        else:
            # Plain processing
            if operator in ["in", "not_in"]:
              value = value.split(",")
            elif operator == "isnull":
              value = value.lower() == "true"
            else:
              lower_val = value.lower()
              if lower_val == "true":
                value = True
              elif lower_val == "false":
                value = False
        
        key = f"{orm_field}{orm_operator}"
        parsed_filters[key] = value
              
      return parsed_filters

    @classmethod
    def parse_order(cls, order: str | None) -> list[str]:
      if not order:
        return []
          
      orders = []
      for item in order.split(","):
        direction = ""
        field = item
        
        if item.startswith("-"):
          direction = "-"
          field = item[1:]
        
        if field not in cls.FIELDS:
            raise UnsupportedFilterError(f"Field not allowed for sorting: {field}")
            
        policy = cls.FIELDS[field]
        if not policy.orderable:
            raise UnsupportedFilterError(f"Field '{field}' is not orderable")
        
        orders.append(f"{direction}{policy.orm_field}")
              
      return orders
