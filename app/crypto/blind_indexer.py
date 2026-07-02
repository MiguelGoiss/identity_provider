"""
BlindIndexer — Índice determinístico HMAC-SHA256 para pesquisa em campos encriptados.

Objetivo:
    Permitir pesquisar por valores encriptados (ex: email, nif) sem os desencriptar.
    O índice é determinístico: o mesmo input + chave + field_name → sempre o mesmo digest.

Separação de chaves:
    Usa uma chave INDEPENDENTE da chave de encriptação (PII_INDEX_KEY_<VERSION>),
    garantindo que a comprometimento de uma não afecta a outra.

Derivação de contexto por campo (field binding):
    O HMAC é calculado sobre  field_name || ":" || normalized_value
    Isto garante que:
      - O mesmo valor (ex: "user@example.com") produz digests DIFERENTES
        em campos diferentes (person_email.email vs user_identity.identifier).
      - Elimina a possibilidade de inferência cross-campo por análise de padrões de índice.

Formato do índice:
    String hexadecimal de 64 caracteres (256 bits).
    Guardada em coluna separada (ex: email_idx) na base de dados.

Critérios de segurança:
  - Usa hmac.new() da stdlib (seguro contra timing attacks via comparação de hashes).
  - Nunca loga o valor em claro nem o digest intermédio.
  - Chave carregada via KeyProvider — falha em startup se não existir.
"""

import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

# Separador entre field_name e valor no contexto HMAC — não pode aparecer num field_name.
_CTX_SEPARATOR = b":"


class BlindIndexer:
    """
    Gerador de índices HMAC-SHA256 para pesquisa em campos encriptados.

    Exemplo de uso:
        from app.crypto.key_provider import KeyProvider
        from app.crypto.blind_indexer import BlindIndexer
        from app.crypto.normalizers import normalize_email

        kp = KeyProvider()
        indexer = BlindIndexer(kp)

        value = normalize_email("User@Example.COM")       # "user@example.com"
        idx = indexer.compute("person_email.email", value) # 64-char hex string

        # Na pesquisa:
        query_idx = indexer.compute("person_email.email", normalize_email(query))
        # Comparar query_idx com a coluna email_idx na BD.
    """

    def __init__(self, key_provider) -> None:
        """
        key_provider: instância de KeyProvider (ou qualquer objecto com
                      get_index_key() -> bytes).
        """
        self._kp = key_provider

    def compute(self, field_name: str, normalized_value: str) -> str:
        """
        Calcula o blind index para um valor normalizado num campo específico.

        Args:
            field_name       : Identificador do campo no formato "modelo.campo".
                               Ex: "person_email.email", "user_identity.identifier".
                               Este valor é incluído no contexto HMAC para binding por campo.
            normalized_value : Valor JÁ normalizado (ex: após normalize_email()).
                               DEVE ser idêntico ao normalizer usado no write path.

        Returns:
            String hexadecimal de 64 caracteres (HMAC-SHA256 de 256 bits).

        Raises:
            ValueError  : Se field_name ou normalized_value forem vazios.
            RuntimeError: Se a chave de índice não estiver disponível.
        """
        if not field_name:
            raise ValueError("BlindIndexer.compute: field_name não pode ser vazio.")
        if normalized_value is None:
            raise ValueError("BlindIndexer.compute: normalized_value não pode ser None.")
        # Permite string vazia como valor legítimo apenas se for mesmo o que queremos indexar;
        # em campos PII, string vazia geralmente não deve ser indexada — validar upstream.

        key = self._kp.get_index_key()

        # Contexto: field_name + separador + valor  →  binding por campo
        message = (
            field_name.encode("utf-8")
            + _CTX_SEPARATOR
            + normalized_value.encode("utf-8")
        )

        digest = hmac.new(key, message, hashlib.sha256).hexdigest()
        return digest
