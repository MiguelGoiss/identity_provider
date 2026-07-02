import secrets
import hashlib
import hmac

def generate_api_key(environment: str) -> tuple[str, str, str]:
    """
    Gera uma nova API Key.
    
    Returns: (raw_key, key_prefix, key_hash)
    - raw_key: "sak_prd_a1b2c3d4e5f6..." (devolvido uma vez ao utilizador)
    - key_prefix: "sak_prd_a1b2" (guardado para lookup)
    - key_hash: SHA-256 do raw_key (guardado para validação)
    """
    env_prefix_map = {
        "production": "prd",
        "staging": "stg",
        "development": "dev"
    }
    env_prefix = env_prefix_map.get(environment, "unk")
    
    # 32 bytes of randomness gives 64 hex characters
    random_hex = secrets.token_hex(32)
    
    raw_key = f"sak_{env_prefix}_{random_hex}"
    
    # Prefix includes "sak_env_" + first 8 chars of random hex
    # Example: "sak_prd_a1b2c3d4" -> 16 chars max, but model has max_length=12 for prefix
    # Actually, model defined `key_prefix` as max_length=12. Let's adjust prefix length.
    # "sak_prd_a1b2" = 12 characters. (4 + 4 + 4)
    key_prefix = raw_key[:12]
    
    key_hash = hash_api_key(raw_key)
    
    return raw_key, key_prefix, key_hash

def hash_api_key(raw_key: str) -> str:
    """
    Deriva SHA-256 do token.
    A API key gerada com CSPRNG tem entropia suficiente para não necessitar de salt.
    """
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """
    Verifica a chave de API de forma segura contra timing attacks.
    """
    if not raw_key or not stored_hash:
        return False
        
    calculated_hash = hash_api_key(raw_key)
    return hmac.compare_digest(calculated_hash, stored_hash)
