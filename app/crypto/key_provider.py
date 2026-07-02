"""
Key Provider — abstração para carregar chaves criptográficas de variáveis de ambiente.

Suporta:
  - PII_ENCRYPTION_KEY_<VERSION>  : Chave AES-256 de 32 bytes (hex-encoded)
  - PII_INDEX_KEY_<VERSION>       : Chave HMAC de 32 bytes (hex-encoded)
  - PII_CURRENT_KEY_VERSION       : Versão activa (default "v1")

Critérios de segurança:
  - Nunca devolve um fallback hardcoded — falha em startup se a chave não existir.
  - Chaves são validadas a 32 bytes exactos (256 bits).
  - Chaves são lidas uma vez e guardadas em memória durante o ciclo de vida do processo.
  - TODO(security): Em produção substituir por integração com Vault / KMS.
"""

import os
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_REQUIRED_KEY_BYTES = 32  # 256 bits


def _load_hex_key(env_var: str) -> bytes:
    """
    Lê uma variável de ambiente como string hexadecimal e devolve os bytes.
    Falha explicitamente se a variável não existir ou tiver comprimento inválido.
    """
    raw = os.environ.get(env_var)
    if not raw:
        raise RuntimeError(
            f"[KeyProvider] Variável de ambiente obrigatória '{env_var}' não está definida. "
            "O serviço não pode arrancar sem as chaves de encriptação de PII."
        )
    try:
        key_bytes = bytes.fromhex(raw.strip())
    except ValueError as exc:
        raise RuntimeError(
            f"[KeyProvider] '{env_var}' não é um valor hexadecimal válido: {exc}"
        ) from exc

    if len(key_bytes) != _REQUIRED_KEY_BYTES:
        raise RuntimeError(
            f"[KeyProvider] '{env_var}' tem {len(key_bytes)} bytes; "
            f"são necessários exactamente {_REQUIRED_KEY_BYTES} bytes (256 bits)."
        )
    return key_bytes


class KeyProvider:
    """
    Ponto único de acesso às chaves criptográficas do serviço.

    Exemplo de uso:
        kp = KeyProvider()
        enc_key = kp.get_encryption_key()   # bytes — chave AES-256 activa
        idx_key = kp.get_index_key()        # bytes — chave HMAC activa

    Para rotação futura:
        kp = KeyProvider(version="v2")      # carrega PII_ENCRYPTION_KEY_V2 / PII_INDEX_KEY_V2
    """

    def __init__(self, version: str | None = None) -> None:
        """
        version: se None, usa PII_CURRENT_KEY_VERSION (default "v1").
        """
        if version is None:
            version = os.environ.get("PII_CURRENT_KEY_VERSION", "v1")
        self.version: str = version.upper()  # normaliza para maiúsculas, ex: "V1"

    @lru_cache(maxsize=None)
    def _enc_var_name(self) -> str:
        return f"PII_ENCRYPTION_KEY_{self.version}"

    @lru_cache(maxsize=None)
    def _idx_var_name(self) -> str:
        return f"PII_INDEX_KEY_{self.version}"

    def get_encryption_key(self) -> bytes:
        """
        Devolve a chave AES-256 da versão activa.
        Falha se a variável não estiver definida ou for inválida.
        """
        return _load_hex_key(self._enc_var_name())

    def get_index_key(self) -> bytes:
        """
        Devolve a chave HMAC-SHA256 da versão activa.
        Falha se a variável não estiver definida ou for inválida.
        """
        return _load_hex_key(self._idx_var_name())

    @property
    def current_version(self) -> str:
        """Devolve a versão activa normalizada (ex: 'V1')."""
        return self.version
