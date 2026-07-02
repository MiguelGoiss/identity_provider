"""
CryptoService — Encriptação autenticada AES-256-GCM.

Formato do ciphertext armazenado (base64url-safe, sem padding):
    base64( version_byte [1] | nonce [12] | tag [16] | ciphertext [N] )

    version_byte : 0x01 identifica o formato da envelope, permite migração futura.
    nonce        : 12 bytes aleatórios (criptograficamente seguros), nunca reutilizados.
    tag          : 16 bytes de autenticação GCM.
    ciphertext   : texto encriptado de comprimento variável.

AAD (Additional Authenticated Data):
    Formato: b"v=<version>;field=<field_name>"
    Exemplo: b"v=V1;field=person_email.email"

    O AAD é autenticado (não encriptado). Inclui:
      - key_version : binding criptográfico à versão da chave activa.
      - field_name  : binding ao campo específico, impedindo que um ciphertext
                      de um campo seja transplantado para outro campo diferente.

Critérios de segurança:
  - Nonce aleatório de 12 bytes por operação → probabilidade de colisão negligenciável.
  - Tag GCM de 16 bytes → qualquer alteração ao ciphertext é detectada.
  - Usa os.urandom() (CSPRNG do SO) para geração de nonce.
  - Falha explicitamente em caso de erro de decriptação (IntegrityError).
  - Nunca loga o plaintext ou a chave.
"""

import os
import base64
import logging

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# Constantes internas do formato
_FORMAT_VERSION = b"\x01"  # 1 byte — versão do formato de envelope
_NONCE_BYTES = 12           # 96 bits recomendados para AES-GCM
_TAG_BYTES = 16             # 128 bits — tag GCM


class DecryptionError(Exception):
    """Levantada quando a decriptação falha (autenticação ou formato inválido)."""


class CryptoService:
    """
    Serviço de encriptação AES-256-GCM para PII.

    Exemplo de uso:
        from app.crypto.key_provider import KeyProvider
        from app.crypto.crypto_service import CryptoService

        kp = KeyProvider()
        svc = CryptoService(kp)

        blob = svc.encrypt("user@example.com", field_name="person_email.email")
        plain = svc.decrypt(blob, field_name="person_email.email")
    """

    def __init__(self, key_provider) -> None:
        """
        key_provider: instância de KeyProvider (ou qualquer objecto com
                      get_encryption_key() -> bytes e current_version -> str).
        """
        self._kp = key_provider

    # ------------------------------------------------------------------
    # Construção do AAD
    # ------------------------------------------------------------------
    def _build_aad(self, field_name: str) -> bytes:
        """
        Constrói o Additional Authenticated Data para o campo específico.
        Inclui key_version e field_name — ambos são verificados na decriptação.
        """
        return f"v={self._kp.current_version};field={field_name}".encode("utf-8")

    # ------------------------------------------------------------------
    # Encriptação
    # ------------------------------------------------------------------
    def encrypt(self, plaintext: str, field_name: str) -> str:
        """
        Encripta plaintext com AES-256-GCM e devolve um blob base64url-safe.

        Args:
            plaintext  : O valor em claro a encriptar (ex: endereço de e-mail).
            field_name : Nome do campo no formato "modelo.campo" (ex: "person_email.email").
                         Usado no AAD para binding criptográfico ao campo.

        Returns:
            String base64url-safe (sem padding) com o envelope completo.

        Raises:
            ValueError  : Se o plaintext for None ou string vazia.
            RuntimeError: Se a chave não estiver disponível.
        """
        if not plaintext:
            raise ValueError("CryptoService.encrypt: plaintext não pode ser vazio.")

        key = self._kp.get_encryption_key()
        aad = self._build_aad(field_name)

        # Nonce: 12 bytes criptograficamente seguros — nunca reutilizados.
        nonce = os.urandom(_NONCE_BYTES)

        aesgcm = AESGCM(key)
        # encrypt() devolve ciphertext + tag (16 bytes) concatenados
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)

        # tag está nos últimos 16 bytes do output do AESGCM
        tag = ciphertext_with_tag[-_TAG_BYTES:]
        ciphertext = ciphertext_with_tag[:-_TAG_BYTES]

        envelope = _FORMAT_VERSION + nonce + tag + ciphertext

        return base64.urlsafe_b64encode(envelope).rstrip(b"=").decode("ascii")

    # ------------------------------------------------------------------
    # Decriptação
    # ------------------------------------------------------------------
    def decrypt(self, blob: str, field_name: str) -> str:
        """
        Decripta um blob produzido por encrypt().

        Args:
            blob       : String base64url-safe devolvida por encrypt().
            field_name : Deve ser idêntico ao field_name usado em encrypt().
                         O AAD será verificado — qualquer discrepância causa DecryptionError.

        Returns:
            O plaintext original como string UTF-8.

        Raises:
            DecryptionError: Se a autenticação falhar, o formato for inválido
                             ou o AAD não coincidir.
        """
        if not blob:
            raise DecryptionError("CryptoService.decrypt: blob não pode ser vazio.")

        try:
            # Repõe o padding base64 removido no encrypt
            padding = 4 - len(blob) % 4
            padded = blob + ("=" * padding if padding != 4 else "")
            raw = base64.urlsafe_b64decode(padded)
        except Exception as exc:
            raise DecryptionError(f"Blob base64 inválido: {exc}") from exc

        # Validação de comprimento mínimo: 1 (version) + 12 (nonce) + 16 (tag) + ≥1 (cipher)
        _MIN_LEN = 1 + _NONCE_BYTES + _TAG_BYTES + 1
        if len(raw) < _MIN_LEN:
            raise DecryptionError("Envelope demasiado curto; dados corrompidos ou inválidos.")

        # Parse do envelope
        format_version = raw[0:1]
        if format_version != _FORMAT_VERSION:
            raise DecryptionError(
                f"Versão de formato desconhecida: {format_version!r}. "
                "Pode ser necessário usar uma versão mais recente do CryptoService."
            )

        nonce = raw[1: 1 + _NONCE_BYTES]
        tag = raw[1 + _NONCE_BYTES: 1 + _NONCE_BYTES + _TAG_BYTES]
        ciphertext = raw[1 + _NONCE_BYTES + _TAG_BYTES:]

        key = self._kp.get_encryption_key()
        aad = self._build_aad(field_name)

        aesgcm = AESGCM(key)
        try:
            # AESGCM.decrypt() espera ciphertext + tag concatenados
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext + tag, aad)
        except Exception as exc:
            # Não loga o blob nem o erro detalhado para evitar leakage de informação.
            logger.warning(
                "Falha na decriptação do campo '%s'. "
                "Possível adulteração ou chave errada.",
                field_name,
            )
            raise DecryptionError(
                f"Falha na autenticação ou decriptação do campo '{field_name}'."
            ) from exc

        return plaintext_bytes.decode("utf-8")
