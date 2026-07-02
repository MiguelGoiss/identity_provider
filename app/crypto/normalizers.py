"""
Normalizers — Funções puras e determinísticas de normalização de dados PII.

Objetivo:
    Garantir que o mesmo valor semântico produza exactamente o mesmo resultado,
    quer no write path (ao encriptar + indexar) quer no search path (ao pesquisar).

    Qualquer divergência entre os dois paths tornaria o blind index inutilizável.

Regras gerais:
  - Cada função é pura (sem efeitos secundários) e idempotente.
  - Não lançam exceções para inputs válidos; devolvem None apenas se o input for None.
  - Não acedem a estado externo (BD, ficheiros, rede).
  - Devem ser testadas com unit tests antes de serem usadas em produção.

ATENÇÃO: Qualquer alteração a estas funções invalida os blind indexes existentes
na base de dados. Em caso de mudança, é necessário re-indexar todos os registos
afectados.
"""

import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Padrão para dígitos apenas (usado na normalização de telefone)
_RE_NON_DIGIT = re.compile(r"\D")

# Padrão para espaços múltiplos
_RE_MULTI_SPACE = re.compile(r"\s+")


def normalize_email(value: Optional[str]) -> Optional[str]:
    """
    Normaliza um endereço de e-mail para pesquisa determinística.

    Regras aplicadas (por esta ordem):
      1. None / string vazia → devolve None.
      2. Strip de whitespace no início e fim.
      3. Lowercase de toda a string.

    NÃO remove subaddressing (ex: user+tag@domain.com) porque faz parte
    do endereço real de entrega e a sua remoção pode causar falsos positivos.

    Args:
        value: Endereço de e-mail (pode ser None).

    Returns:
        String normalizada ou None se o input for inválido/vazio.

    Examples:
        >>> normalize_email("  User@Example.COM  ")
        'user@example.com'
        >>> normalize_email("User+Tag@Example.COM")
        'user+tag@example.com'
        >>> normalize_email(None)
        None
    """
    if not value:
        return None
    return value.strip().lower()


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """
    Normaliza um número de telefone para pesquisa determinística.

    Regras aplicadas:
      1. None / string vazia → devolve None.
      2. Remove todos os caracteres que não sejam dígitos (espaços, traços, parênteses, +).
      3. Devolve apenas os dígitos.

    NOTA: Não adiciona nem remove prefixos de país (ex: +351). O caller é responsável
    por garantir que os valores são armazenados de forma consistente (ex: sempre com
    prefixo internacional).

    Args:
        value: Número de telefone em qualquer formato.

    Returns:
        String com apenas dígitos, ou None se o input for inválido/vazio.

    Examples:
        >>> normalize_phone("+351 91 234 56 78")
        '351912345678'
        >>> normalize_phone("(+351) 91-234-5678")
        '351912345678'
        >>> normalize_phone(None)
        None
    """
    if not value:
        return None
    return _RE_NON_DIGIT.sub("", value)


def normalize_text(value: Optional[str]) -> Optional[str]:
    """
    Normalização genérica de texto para pesquisa case-insensitive e accent-insensitive.

    Regras aplicadas:
      1. None / string vazia → devolve None.
      2. Strip de whitespace no início e fim.
      3. Normalização Unicode para NFC (composição canónica).
      4. Lowercase.
      5. Compressão de espaços múltiplos para um único espaço.

    Usado para campos como: nome próprio, apelido, cargo, etc.

    Args:
        value: Texto genérico.

    Returns:
        String normalizada ou None se o input for inválido/vazio.

    Examples:
        >>> normalize_text("  João   Silva  ")
        'joão silva'
        >>> normalize_text("MARIA  DA  GRAÇA")
        'maria da graça'
        >>> normalize_text(None)
        None
    """
    if not value:
        return None
    normalized = unicodedata.normalize("NFC", value.strip())
    lowered = normalized.lower()
    return _RE_MULTI_SPACE.sub(" ", lowered)


def normalize_date(value: Optional[str]) -> Optional[str]:
    """
    Normaliza uma data para pesquisa determinística.

    Formato de saída canónico: YYYY-MM-DD (ISO 8601).

    Formatos de entrada suportados:
      - "YYYY-MM-DD" (já no formato correcto)
      - "DD/MM/YYYY" (formato europeu comum)
      - "DD-MM-YYYY" (variante com traços)
      - "YYYY/MM/DD" (variante com barras)

    Args:
        value: String representando uma data.

    Returns:
        String no formato "YYYY-MM-DD" ou None se o input for inválido/vazio/não reconhecido.

    Examples:
        >>> normalize_date("2024-01-15")
        '2024-01-15'
        >>> normalize_date("15/01/2024")
        '2024-01-15'
        >>> normalize_date("15-01-2024")
        '2024-01-15'
        >>> normalize_date("2024/01/15")
        '2024-01-15'
        >>> normalize_date(None)
        None
    """
    if not value:
        return None

    stripped = value.strip()

    # YYYY-MM-DD ou YYYY/MM/DD
    m = re.fullmatch(r"(\d{4})[-/](\d{2})[-/](\d{2})", stripped)
    if m:
        year, month, day = m.group(1), m.group(2), m.group(3)
        return f"{year}-{month}-{day}"

    # DD/MM/YYYY ou DD-MM-YYYY
    m = re.fullmatch(r"(\d{2})[-/](\d{2})[-/](\d{4})", stripped)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        return f"{year}-{month}-{day}"

    logger.warning(
        "normalize_date: formato de data não reconhecido '%s'. Devolvendo None.",
        stripped,
    )
    return None
