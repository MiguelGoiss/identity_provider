"""
Crypto layer for Encryption at Rest (PII protection).

This package provides:
  - CryptoService   : AES-256-GCM authenticated encryption/decryption
  - BlindIndexer    : HMAC-SHA256 deterministic search index
  - Normalizers     : Pure, deterministic data-normalization functions
  - KeyProvider     : Env-based key loading with version support
"""

from .crypto_service import CryptoService
from .blind_indexer import BlindIndexer
from .normalizers import normalize_email, normalize_phone, normalize_text, normalize_date
from .key_provider import KeyProvider

__all__ = [
    "CryptoService",
    "BlindIndexer",
    "normalize_email",
    "normalize_phone",
    "normalize_text",
    "normalize_date",
    "KeyProvider",
]
