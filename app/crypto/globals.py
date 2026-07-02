from app.crypto.key_provider import KeyProvider
from app.crypto.crypto_service import CryptoService
from app.crypto.blind_indexer import BlindIndexer

key_provider = KeyProvider()
crypto_service = CryptoService(key_provider)
blind_indexer = BlindIndexer(key_provider)
