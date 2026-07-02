import sys

filepath = "/home/miguelgois/code/projects/microservice_helpdesk/authentication/app/routers/auth/auth_router.py"
with open(filepath, "r") as f:
    data = f.read()

# 1. Imports
data = data.replace(
    "from app.database.models import User, UserIdentity, LoginAttempt, AuthSession, Application, PersonEmail, UserApplicationAccess\n",
    "from app.database.models import User\nfrom app.database.repository.auth.auth_repository import AuthRepository\n"
)

# 2. Remove log_login_attempt
start_idx = data.find("async def log_login_attempt(")
end_idx = data.find("@router.post(\"/.validate-identifier\")")
if start_idx != -1 and end_idx != -1:
    data = data[:start_idx] + data[end_idx:]

# 3. verify_user_password 1
data = data.replace(
    "  identity = await UserIdentity.get_or_none(identifier=payload.username).prefetch_related(\"user\")\n  \n  if identity:\n    user = identity.user\n  else:\n    user = None\n    \n  emails_to = []\n  if user:\n    primary_emails = await PersonEmail.filter(user=user, is_primary=True).all()\n    emails_to = [e.email for e in primary_emails]",
    "  identity = await AuthRepository.get_identity_with_user(payload.username)\n  user = identity.user if identity else None\n    \n  emails_to = []\n  if user:\n    emails_to = await AuthRepository.get_user_primary_emails(user)"
)

# 4. log_login_attempt replaces
data = data.replace("await log_login_attempt(", "await AuthRepository.log_login_attempt(")

# 5. OTP initiation
data = data.replace(
    "    otp = f\"{secrets.randbelow(900000) + 100000}\"\n    user.recovery_secret = get_password_hash(otp)\n    user.recovery_secret_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)\n    user.recovery_attempts = 0\n    await User.filter(id=user.id).update(\n        recovery_secret=user.recovery_secret,\n        recovery_secret_expires_at=user.recovery_secret_expires_at,\n        recovery_attempts=0\n    )",
    "    otp = f\"{secrets.randbelow(900000) + 100000}\"\n    expires = datetime.now(timezone.utc) + timedelta(minutes=10)\n    await AuthRepository.initiate_otp_recovery(user, get_password_hash(otp), expires)"
)

# 6. login_for_access_token top
data = data.replace(
    "identity = await UserIdentity.get_or_none(identifier=form_data.username).prefetch_related(\"user\")",
    "identity = await AuthRepository.get_identity_with_user(form_data.username)"
)

# 7. clear otp 1
data = data.replace(
    "          # Clear OTP\n          user.recovery_secret = None\n          user.recovery_secret_expires_at = None\n          user.recovery_attempts = 0\n          await User.filter(id=user.id).update(\n              recovery_secret=None,\n              recovery_secret_expires_at=None,\n              recovery_attempts=0\n          )",
    "          await AuthRepository.clear_otp(user)"
)

# 8. clear otp 2
data = data.replace(
    "          if user.recovery_attempts > 2:\n            user.recovery_secret = None\n            user.recovery_secret_expires_at = None\n            await User.filter(id=user.id).update(\n              recovery_attempts=user.recovery_attempts,\n              recovery_secret=None,\n              recovery_secret_expires_at=None\n            )",
    "          if user.recovery_attempts > 2:\n            await AuthRepository.clear_otp(user, increment_attempts=True)"
)

# 9. increment attempts
data = data.replace(
    "            await User.filter(id=user.id).update(recovery_attempts=user.recovery_attempts)",
    "            await AuthRepository.increment_recovery_attempts(user)"
)

# 10. auth session
data = data.replace(
    "  app_obj = None\n  if x_app_client:\n      app_obj = await Application.get_or_none(slug=x_app_client)\n      \n  await AuthSession.create(\n      user=user,\n      application=app_obj,\n      jti=jti,\n      expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),\n      ip_address=get_client_ip(request),\n      user_agent=get_user_agent(request)\n  )",
    "  app_obj = await AuthRepository.get_application_by_slug(x_app_client) if x_app_client else None\n      \n  await AuthRepository.create_auth_session(\n      user=user,\n      application=app_obj,\n      jti=jti,\n      expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),\n      ip_address=get_client_ip(request),\n      user_agent=get_user_agent(request)\n  )"
)

# 11. read_users_me
data = data.replace(
    "  apps = await UserApplicationAccess.filter(\n    user=user,\n    application__is_active=True,\n  ).values_list(\"application__slug\", flat=True)",
    "  apps = await AuthRepository.get_user_authorized_apps(user)"
)
data = data.replace(
    "  from app.database.models.user_companies import UserCompany\n  primary_company = await UserCompany.filter(user=user, is_primary=True).first()\n\n  from app.database.models.user_identity import UserIdentity\n  username_identity = await UserIdentity.filter(user=user, identity_type=\"username\").first()",
    "  primary_company = await AuthRepository.get_user_primary_company(user)\n  username_identity = await AuthRepository.get_username_identity(user)"
)

with open(filepath, "w") as f:
    f.write(data)

print("Done")
