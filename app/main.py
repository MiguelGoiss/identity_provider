from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import register_db_exceptions
from tortoise.contrib.fastapi import register_tortoise
from app.core.config import TORTOISE_ORM_CONFIG, settings

import logging
from tortoise import Tortoise

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("--- INFO: Auth Service Startup Initiated ---")
  await Tortoise.init(config=TORTOISE_ORM_CONFIG)
  yield
  logger.info("--- INFO: Auth Service Shutdown Initiated ---")
  await Tortoise.close_connections()
  
# --- 2. Application Definition ---
app = FastAPI(
  title="Auth Service",
  description="Microservice for Identity, Authentication, and User Management.",
  version="0.9.0",
  lifespan=lifespan, # Inject the manager defined above
  docs_url="/docs" if settings.DEBUG else None,
  redoc_url="/redoc" if settings.DEBUG else None,
  openapi_url="/openapi.json" if settings.DEBUG else None,
)



# Parse allowed origins
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")] if settings.ALLOWED_ORIGINS else []

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# --- 4. Exception Handlers ---
register_db_exceptions(app)

from app.utils.query_parser import UnsupportedFilterError
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(UnsupportedFilterError)
async def unsupported_filter_exception_handler(request: Request, exc: UnsupportedFilterError):
  return JSONResponse(
    status_code=400,
    content={"detail": str(exc)},
  )

from app.dependencies import verify_internal_access, VerifyInternalAccess

# --- 5. Routers ---
from app.routers import (
  user_router,
  company_router,
  local_router,
  auth_router,
  jwks_router,
  role_router,
  permission_router,
  app_window_router,
  org_unit_type_router,
  org_unit_router,
  application_router,
  user_app_access_router,
  internal_router,
  service_api_key_router,
  uploads_router
)

app.include_router(jwks_router)
app.include_router(auth_router)

internal_admin_dependency = Depends(VerifyInternalAccess(["internal:admin"]))

# Adiciona o router principal das aplicações que contém as sub-rotas
app.include_router(user_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(company_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(local_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(role_router, prefix="/api/v1")
app.include_router(permission_router, prefix="/api/v1")
app.include_router(app_window_router, prefix="/api/v1")
app.include_router(service_api_key_router, prefix="/api/v1")
app.include_router(uploads_router)

app.include_router(org_unit_type_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(org_unit_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(application_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(user_app_access_router, prefix="/api/v1", dependencies=[internal_admin_dependency])
app.include_router(internal_router, dependencies=[internal_admin_dependency])

# --- 5. Base Endpoints ---
@app.get("/", tags=["System"])
async def root():
  """
  Root endpoint to verify the service is reachable.
  """
  return {
    "service": "Auth Service", 
    "status": "operational",
    "documentation": "/docs"
  }

@app.get("/health", tags=["System"])
async def health_check():
  """
  Health check for Docker/Kubernetes probes.
  """
  try:
    connection = Tortoise.get_connection("authentication")
    await connection.execute_query("SELECT 1")
    return {"status": "ok"}
  except Exception as e:
    from fastapi import HTTPException
    logger.error(f"Health check failed: {e}")
    raise HTTPException(status_code=503, detail="Database connection failed")