from datetime import datetime, timedelta, timezone
from typing import Annotated
import secrets
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash
from app.database.models import User
from app.database.repository.auth.auth_repository import AuthRepository
from app.schemas.auth_schemas import (
  Token,
  TokenData,
  PasswordResetRequest,
  PasswordResetConfirm,
  RefreshSchema,
  UserIdentifier,
  MeResponse,
  OrgUnitOut
)
from app.database.repository.user.user_repository import UserRepository
from app.utils.email import send_otp_email
from app.utils.request_utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
    _id: str = payload.get("sub")
    if _id is None:
      raise credentials_exception
    token_data = TokenData(id=_id)
  except JWTError:
    raise credentials_exception
  
  user = await User.get_or_none(id=token_data.id).prefetch_related(
    'person_emails', 'person_contacts__contact_type', 'companies__company', 'companies__local', 'companies__org_unit__type', 'profile'
  )
  if user is None:
    raise credentials_exception
  return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
  if current_user.deactivated_at:
    raise HTTPException(status_code=400, detail="Inactive user")
  return current_user

@router.post("/.validate-identifier")
async def verify_user_password(
  payload: UserIdentifier,
  request: Request,
  x_app_client: str | None = Header(default=None)
):
  identity = await AuthRepository.get_identity_with_user(payload.username)
  user = identity.user if identity else None
    
  emails_to = []
  if user:
    emails_to = await AuthRepository.get_user_primary_emails(user)

  if user:
    # If user has a valid password, they log in via password.
    if user.hashed_password and str(user.hashed_password).strip().lower() not in ("none", "null", ""):
      await AuthRepository.log_login_attempt(request, payload.username, "SUCCESS", "password", user, identity, x_app_client)
      return {
        "is_agent": True,
        "is_user": True,
        "is_collaborator": False
      }

    # If no password, they are a collaborator (OTP flow)
    otp = f"{secrets.randbelow(900000) + 100000}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    await AuthRepository.initiate_otp_recovery(user, get_password_hash(otp), expires)

    if emails_to:
      for email in emails_to:
        await send_otp_email(email, otp)
    else:
      logger.warning(f"No email associated with user ID {user.id}. Cannot send OTP.")

    await AuthRepository.log_login_attempt(request, payload.username, "SUCCESS", "otp_request", user, identity, x_app_client)
    return {
      "is_agent": False,
      "is_user": True,
      "is_collaborator": True
    }
    
  await AuthRepository.log_login_attempt(request, payload.username, "USER_NOT_FOUND", None, None, identity, x_app_client)
  # H5 Fix: User Enumeration Mitigation
  # Always return the same response as a collaborator to hide existence of user
  return {
    "is_agent": False,
    "is_user": True,
    "is_collaborator": True
  }

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    x_app_client: str | None = Header(default=None)
):
  identity = await AuthRepository.get_identity_with_user(form_data.username)
  if identity:
    user = await User.get(id=identity.user.id).prefetch_related("profile")
  else:
    user = None
    
  if not user:
    await AuthRepository.log_login_attempt(request, form_data.username, "USER_NOT_FOUND", None, None, identity, x_app_client)
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  if user.deactivated_at:
    await AuthRepository.log_login_attempt(request, form_data.username, "USER_DEACTIVATED", None, user, identity, x_app_client)
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User account is deactivated",
    )

  is_authenticated = False
  auth_method = None
  
  if user.hashed_password and verify_password(form_data.password, user.hashed_password):
    is_authenticated = True
    auth_method = "password"
  elif user.recovery_secret and user.recovery_secret_expires_at:
      now = datetime.now(timezone.utc)
      if user.recovery_secret_expires_at > now:
        if verify_password(form_data.password, user.recovery_secret):
          is_authenticated = True
          auth_method = "otp"
          await AuthRepository.clear_otp(user)
        else:
          user.recovery_attempts += 1
          if user.recovery_attempts > 2:
            await AuthRepository.clear_otp(user, increment_attempts=True)
            await AuthRepository.log_login_attempt(request, form_data.username, "LOCKED_OUT", "otp", user, identity, x_app_client)
            raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Código PIN bloqueado devido a múltiplas tentativas incorretas. Peça um novo PIN.",
              headers={"WWW-Authenticate": "Bearer"},
            )
          else:
            await AuthRepository.increment_recovery_attempts(user)
            await AuthRepository.log_login_attempt(request, form_data.username, "INVALID_OTP", "otp", user, identity, x_app_client)
      else:
        await AuthRepository.log_login_attempt(request, form_data.username, "EXPIRED_OTP", "otp", user, identity, x_app_client)
        raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Código PIN expirado. Peça um novo PIN.",
          headers={"WWW-Authenticate": "Bearer"},
        )

  if not is_authenticated:
    if auth_method != "otp":
      await AuthRepository.log_login_attempt(request, form_data.username, "INVALID_CREDENTIALS", "password", user, identity, x_app_client)
    raise HTTPException(
      status_code=419,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  await AuthRepository.log_login_attempt(request, form_data.username, "SUCCESS", auth_method, user, identity, x_app_client)
  
  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  
  jti = uuid.uuid4().hex
  app_obj = await AuthRepository.get_application_by_slug(x_app_client) if x_app_client else None
      
  await AuthRepository.create_auth_session(
      user=user,
      application=app_obj,
      jti=jti,
      expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
      ip_address=get_client_ip(request),
      user_agent=get_user_agent(request)
  )
  
  access_token = await create_access_token(
    user=user,
    expires_delta=access_token_expires,
    jti=jti
  )
  refresh_token = await create_refresh_token(user=user, jti=jti)
  
  return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_schema: RefreshSchema,
    request: Request,
    x_app_client: str | None = Header(default=None)
):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(refresh_schema.refresh_token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
    _id: str = payload.get("sub")
    token_type: str = payload.get("type")
    jti: str = payload.get("jti")
    if _id is None or token_type != "refresh" or not jti:
      raise credentials_exception
  except JWTError:
    raise credentials_exception
    
  user = await User.get_or_none(id=_id).prefetch_related("profile")
  if not user:
    raise credentials_exception

  # Validar estado — se desactivado ou eliminado, rejeitar refresh
  if user.deactivated_at or user.deleted_at:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="User deactivated or not found",
    )

  session = await AuthRepository.get_auth_session(jti=jti, user_id=user.id)
  if not session or session.revoked_at:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Session revoked or invalid",
    )
    
  await AuthRepository.revoke_session(session)

  new_jti = uuid.uuid4().hex
  app_obj = await AuthRepository.get_application_by_slug(x_app_client) if x_app_client else None
      
  await AuthRepository.create_auth_session(
      user=user,
      application=app_obj,
      jti=new_jti,
      expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
      ip_address=get_client_ip(request),
      user_agent=get_user_agent(request)
  )

  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = await create_access_token(
    user=user,
    expires_delta=access_token_expires,
    jti=new_jti
  )

  new_refresh_token = await create_refresh_token(user=user, jti=new_jti)
  
  return Token(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")

@router.post("/logout")
async def logout(
    refresh_schema: RefreshSchema
):
  try:
    payload = jwt.decode(refresh_schema.refresh_token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
    jti = payload.get("jti")
    if jti:
      session = await AuthRepository.get_auth_session(jti=jti)
      if session and not session.revoked_at:
        await AuthRepository.revoke_session(session)
  except Exception:
    pass
    
  return {"detail": "Logged out successfully"}

@router.get("/me", response_model=MeResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
  """
  Devolve o utilizador actual com org_unit e apps autorizadas.
  Vai sempre à BD — nunca serve dados do JWT em cache.
  """
  user = await User.get_or_none(
    id=current_user.id,
    deactivated_at=None,
    deleted_at=None,
  ).prefetch_related("companies__org_unit__type", "profile")

  if not user:
    raise HTTPException(status_code=401, detail="Account deactivated")

  apps = await AuthRepository.get_user_authorized_apps(user)

  primary_company = await AuthRepository.get_user_primary_company(user)

  org_unit_out = None
  if primary_company and primary_company.org_unit_id and primary_company.org_unit:
    org_unit_out = OrgUnitOut(
      id=primary_company.org_unit.id,
      name=primary_company.org_unit.name,
      type_name=primary_company.org_unit.type.name,
      parent_id=primary_company.org_unit.parent_id,
    )
  username_identity = await AuthRepository.get_username_identity(user)

  return MeResponse(
    id=str(user.id),
    uuid=str(user.uuid),
    first_name=user.profile.first_name if user.profile else None,
    last_name=user.profile.last_name if user.profile else None,
    username=username_identity.identifier if username_identity else None,
    employee_number=primary_company.employee_number if primary_company else None,
    job_title=primary_company.job_title if primary_company else None,
    org_unit=org_unit_out,
    apps=list(apps),
  )

@router.post("/recover-password")
async def recover_password(request: PasswordResetRequest):
  raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
  raise HTTPException(status_code=501, detail="Not implemented")
