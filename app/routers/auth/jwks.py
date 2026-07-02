from fastapi import APIRouter
from fastapi.responses import JSONResponse
from jose import jwk
from app.core.config import settings

router = APIRouter()

def get_dynamic_jwks():
    key = jwk.construct(settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
    public_key_dict = key.public_key().to_dict()
    public_key_dict["kid"] = settings.AUTH_KEY_ID
    public_key_dict["use"] = "sig"
    return {"keys": [public_key_dict]}

@router.get("/.well-known/jwks.json", response_class=JSONResponse)
async def get_jwks():
    """
    Devolve as public keys
    A Gateway chama este endpoint para verificar os tokens assinados pelo serviço.
    """
    return get_dynamic_jwks()