from fastapi import APIRouter, Depends
from app.dependencies import VerifyInternalAccess

from .endpoints.user.user_router import router as user_router
from .endpoints.company.company_router import router as company_router
from .endpoints.local.local_router import router as local_router
from .endpoints.auth.auth_router import router as auth_router
from .endpoints.auth.jwks import router as jwks_router
from .endpoints.roles.role_router import router as role_router
from .endpoints.permissions.permission_router import router as permission_router
from .endpoints.app_windows.app_window_router import router as app_window_router
from .endpoints.org_unit_types.org_unit_type_router import router as org_unit_type_router
from .endpoints.org_units.org_unit_router import router as org_unit_router
from .endpoints.applications.application_router import router as application_router
from .endpoints.user_app_access.user_app_access_router import router as user_app_access_router
from .endpoints.internal.internal_router import router as internal_router
from .endpoints.service_api_keys.service_api_key_router import router as service_api_key_router
from .endpoints.uploads.uploads_router import router as uploads_router

api_router = APIRouter()

internal_admin_dependency = Depends(VerifyInternalAccess(["internal:admin"]))

# Endpoints sem prefixo
api_router.include_router(jwks_router)
api_router.include_router(auth_router)
api_router.include_router(uploads_router)
api_router.include_router(internal_router, dependencies=[internal_admin_dependency])

# Endpoints com prefixo /api/v1
api_router.include_router(user_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(company_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(local_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(role_router, prefix="/api/v1")
api_router.include_router(permission_router, prefix="/api/v1")
api_router.include_router(app_window_router, prefix="/api/v1")
api_router.include_router(service_api_key_router, prefix="/api/v1")
api_router.include_router(org_unit_type_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(org_unit_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(application_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
api_router.include_router(user_app_access_router, prefix="/api/v1", dependencies=[internal_admin_dependency])