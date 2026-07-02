from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
import bcrypt
import uuid
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
  """
  Checks if the plain password matches the hash.
  Note: bcrypt.checkpw expects BYTES, not strings.
  """
  if not plain_password or not hashed_password:
    return False
      
  # Convert inputs to bytes
  plain_password_bytes = plain_password.encode('utf-8')
  hashed_password_bytes = hashed_password.encode('utf-8')

  try:
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
  except ValueError:
    # This handles cases where the hash in DB is malformed/invalid
    return False

def get_password_hash(password: str) -> str:
  """
  Hashes a password with a random salt.
  """
  pwd_bytes = password.encode('utf-8')
  salt = bcrypt.gensalt()
  hashed = bcrypt.hashpw(pwd_bytes, salt)
  
  # Return as string for database storage
  return hashed.decode('utf-8')

async def create_access_token(user, expires_delta: Union[timedelta, None] = None, jti: str = None) -> str:
  """
  Gera um access token JWT com o novo payload multi-app.
  Inclui: identidade, org_unit, company primária, apps autorizadas.
  Permissões internas do auth service NÃO são propagadas.
  """
  from app.database.models.user_application_access import UserApplicationAccess
  from app.database.models.user_companies import UserCompany

  # Obter apps autorizadas
  apps = await UserApplicationAccess.filter(
    user=user,
    application__is_active=True,
  ).values_list("application__slug", flat=True)

  # Obter company_id primária via UserCompany
  primary_company = await UserCompany.filter(
    user=user, is_primary=True
  ).first()
  company_id = primary_company.company_id if primary_company else None

  # Obter org_unit info
  org_unit = None
  org_unit_type_name = None
  if primary_company and primary_company.org_unit_id:
    await primary_company.fetch_related("org_unit__type")
    org_unit = primary_company.org_unit
    if org_unit:
      org_unit_type_name = org_unit.type.name

  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

  to_encode = {
    "sub": str(user.id),
    "uuid": str(user.uuid),
    "first_name": user.profile.first_name if user.profile else None,
    "last_name": user.profile.last_name if user.profile else None,
    "full_name": user.profile.full_name if user.profile else None,
    "employee_number": primary_company.employee_number if primary_company else None,
    "company_id": company_id,
    "org_unit_id": org_unit.id if org_unit else None,
    "org_unit_type": org_unit_type_name,
    "job_title": primary_company.job_title if primary_company else None,
    "apps": list(apps),
    "exp": expire,
    "jti": jti or uuid.uuid4().hex,
    "type": "access",
  }

  encoded_jwt = jwt.encode(
    to_encode,
    settings.PRIVATE_KEY,
    algorithm=settings.ALGORITHM,
    headers={"kid": settings.AUTH_KEY_ID}
  )
  return encoded_jwt

async def create_refresh_token(user, expires_delta: Union[timedelta, None] = None, jti: str = None) -> str:
  """
  Gera um refresh token JWT com dados mínimos de identidade.
  """
  from app.database.models.user_companies import UserCompany
  
  primary_company = await UserCompany.filter(
    user=user, is_primary=True
  ).first()

  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

  to_encode = {
    "sub": str(user.id),
    "uuid": str(user.uuid),
    "first_name": user.profile.first_name if user.profile else None,
    "last_name": user.profile.last_name if user.profile else None,
    "full_name": user.profile.full_name if user.profile else None,
    "employee_number": primary_company.employee_number if primary_company else None,
    "exp": expire,
    "jti": jti or uuid.uuid4().hex,
    "type": "refresh",
  }

  encoded_jwt = jwt.encode(
    to_encode,
    settings.PRIVATE_KEY,
    algorithm=settings.ALGORITHM,
    headers={"kid": settings.AUTH_KEY_ID}
  )
  return encoded_jwt

