from datetime import datetime
from fastapi import Request
from app.database.models import (
    User,
    UserIdentity,
    LoginAttempt,
    AuthSession,
    Application,
    PersonEmail,
    UserApplicationAccess,
    UserCompany
)
from app.utils.request_utils import get_client_ip, get_user_agent
from app.crypto.globals import blind_indexer
from app.crypto.normalizers import normalize_text

class AuthRepository:

    @staticmethod
    async def log_login_attempt(
        request: Request,
        identifier: str,
        outcome: str,
        auth_method: str = None,
        user: User = None,
        identity: UserIdentity = None,
        app_slug: str = None
    ) -> LoginAttempt:
        app_obj = None
        if app_slug:
            app_obj = await Application.get_or_none(slug=app_slug)
        
        return await LoginAttempt.create(
            user=user,
            user_identity=identity,
            application=app_obj,
            identity_type=identity.identity_type if identity else None,
            identifier_used=identifier,
            auth_method=auth_method,
            outcome=outcome,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

    @staticmethod
    async def get_identity_with_user(identifier: str) -> UserIdentity | None:
        norm = normalize_text(identifier)
        idx = blind_indexer.compute("user_identity.identifier", norm)
        return await UserIdentity.get_or_none(identifier_idx=idx).prefetch_related("user")

    @staticmethod
    async def get_user_primary_emails(user: User) -> list[str]:
        emails = await PersonEmail.filter(user=user, is_primary=True).all()
        return [e.email for e in emails]

    @staticmethod
    async def initiate_otp_recovery(user: User, otp_hash: str, expires_at: datetime) -> None:
        user.recovery_secret = otp_hash
        user.recovery_secret_expires_at = expires_at
        user.recovery_attempts = 0
        await User.filter(id=user.id).update(
            recovery_secret=otp_hash,
            recovery_secret_expires_at=expires_at,
            recovery_attempts=0
        )

    @staticmethod
    async def increment_recovery_attempts(user: User) -> None:
        await User.filter(id=user.id).update(recovery_attempts=user.recovery_attempts)
        
    @staticmethod
    async def clear_otp(user: User, increment_attempts: bool = False) -> None:
        user.recovery_secret = None
        user.recovery_secret_expires_at = None
        if not increment_attempts:
            user.recovery_attempts = 0
            await User.filter(id=user.id).update(
                recovery_secret=None,
                recovery_secret_expires_at=None,
                recovery_attempts=0
            )
        else:
            await User.filter(id=user.id).update(
                recovery_secret=None,
                recovery_secret_expires_at=None,
                recovery_attempts=user.recovery_attempts
            )

    @staticmethod
    async def get_application_by_slug(slug: str) -> Application | None:
        return await Application.get_or_none(slug=slug)

    @staticmethod
    async def create_auth_session(
        user: User,
        application: Application | None,
        jti: str,
        expires_at: datetime,
        ip_address: str,
        user_agent: str
    ) -> AuthSession:
        return await AuthSession.create(
            user=user,
            application=application,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    async def get_user_authorized_apps(user: User) -> list[str]:
        apps = await UserApplicationAccess.filter(
            user=user,
            application__is_active=True,
        ).values_list("application__slug", flat=True)
        return list(apps)

    @staticmethod
    async def get_user_primary_company(user: User) -> UserCompany | None:
        return await UserCompany.filter(user=user, is_primary=True).first()

    @staticmethod
    async def get_username_identity(user: User) -> UserIdentity | None:
        return await UserIdentity.filter(user=user, identity_type="username").first()

    @staticmethod
    async def get_auth_session(jti: str, user_id: int | None = None) -> AuthSession | None:
        if user_id is not None:
            return await AuthSession.get_or_none(jti=jti, user_id=user_id)
        return await AuthSession.get_or_none(jti=jti)

    @staticmethod
    async def revoke_session(session: AuthSession) -> None:
        from datetime import timezone
        session.revoked_at = datetime.now(timezone.utc)
        await session.save()
