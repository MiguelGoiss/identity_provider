import os
import base64
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
  # APP
  APP_NAME: str = "Authentication Service"
  DEBUG: bool = True

  # DATABASE
  DB_USER: str
  DB_PASSWORD: str
  DB_HOST: str
  DB_PORT: str = "5432"
  DB_NAME: str 
  
  # AUTHENTICATION
  AUTH_KEY_ID: str = Field(default="auth-key-1", description="The Key ID (kid) for JWKS")
  AUTH_PRIVATE_KEY_BASE64: str = Field(
    ..., 
    alias="AUTH_PRIVATE_KEY",
    description="Base64 encoded RSA Private Key"
  )
  
  ALGORITHM: str = "RS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
  REFRESH_TOKEN_EXPIRE_DAYS: int = 7

  INTERNAL_API_KEY: str
  ALLOWED_ORIGINS: str = ""
  
  # EMAIL
  MAIL_USERNAME: str = ""
  MAIL_PASSWORD: str = ""
  MAIL_FROM: str = ""
  MAIL_PORT: int = 587
  MAIL_SERVER: str = ""
  MAIL_STARTTLS: bool = True
  MAIL_SSL_TLS: bool = False
  
  # REDIS
  REDIS_URL: str = "redis://redis:6379/0"


  @property
  def PRIVATE_KEY(self) -> bytes:
    """
    Decodes the Base64 key into bytes for the application to use.
    """
    try:
      return base64.b64decode(self.AUTH_PRIVATE_KEY_BASE64)
    except Exception as e:
      raise ValueError(f"Could not decode AUTH_PRIVATE_KEY: {e}")

  @property
  def PUBLIC_KEY(self) -> bytes:
    """
    Derives the PEM public key from the private key to be used for validation,
    preventing the private key from being passed to decoding functions.
    """
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives import serialization
    private_key_obj = load_pem_private_key(self.PRIVATE_KEY, password=None)
    public_key_obj = private_key_obj.public_key()
    return public_key_obj.public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

  @property
  def DATABASE_URL(self) -> str:
    return f"postgres://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

  model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env.dev"), extra="ignore")


settings = Settings()

TORTOISE_ORM_CONFIG = {
  "connections": {
    "authentication": {
      "engine": "tortoise.backends.asyncpg",
      "credentials": {
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "database": settings.DB_NAME,
        "min_size": 2,
        "max_size": 10,
        "timeout": 15,
      }
    }
  },
  "apps": {
    "models": {
      "models": ["app.database.models", "aerich.models"],
      "default_connection": "authentication",
    },
  },
}

