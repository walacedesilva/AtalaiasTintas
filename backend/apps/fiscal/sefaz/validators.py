"""SEFAZ data validators (T039).

Validates NF-e field values before XML generation and SEFAZ submission.
All public functions raise ``SefazSchemaError`` on invalid data.
"""
from __future__ import annotations

import re
from decimal import Decimal

from .exceptions import SefazSchemaError

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
_RE_CNPJ = re.compile(r"^\d{14}$")
_RE_CPF = re.compile(r"^\d{11}$")
_RE_CEP = re.compile(r"^\d{8}$")
_RE_NCM = re.compile(r"^\d{8}$")
_RE_CFOP = re.compile(r"^\d{4}$")
_RE_CHAVE = re.compile(r"^\d{44}$")
_RE_SERIE = re.compile(r"^\d{1,3}$")


# ---------------------------------------------------------------------------
# CNPJ / CPF
# ---------------------------------------------------------------------------

def validar_cnpj(cnpj: str) -> str:
    """Return the cleaned 14-digit CNPJ string or raise ``SefazSchemaError``."""
    cleaned = re.sub(r"\D", "", cnpj or "")
    if not _RE_CNPJ.match(cleaned):
        raise SefazSchemaError(f"CNPJ inválido: '{cnpj}'")
    if not _dv_cnpj_ok(cleaned):
        raise SefazSchemaError(f"CNPJ com dígitos verificadores inválidos: '{cnpj}'")
    return cleaned


def validar_cpf(cpf: str) -> str:
    """Return the cleaned 11-digit CPF string or raise ``SefazSchemaError``."""
    cleaned = re.sub(r"\D", "", cpf or "")
    if not _RE_CPF.match(cleaned):
        raise SefazSchemaError(f"CPF inválido: '{cpf}'")
    if not _dv_cpf_ok(cleaned):
        raise SefazSchemaError(f"CPF com dígitos verificadores inválidos: '{cpf}'")
    return cleaned


def validar_cpf_ou_cnpj(doc: str) -> tuple[str, str]:
    """Return ``(tipo, doc_limpo)`` where tipo is 'CPF' or 'CNPJ'."""
    cleaned = re.sub(r"\D", "", doc or "")
    if len(cleaned) == 14:
        return "CNPJ", validar_cnpj(cleaned)
    if len(cleaned) == 11:
        return "CPF", validar_cpf(cleaned)
    raise SefazSchemaError(f"Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos, recebido: '{doc}'")


# ---------------------------------------------------------------------------
# Fiscal codes
# ---------------------------------------------------------------------------

def validar_ncm(ncm: str) -> str:
    """Return 8-digit NCM or raise ``SefazSchemaError``."""
    cleaned = re.sub(r"\D", "", ncm or "")
    if not _RE_NCM.match(cleaned):
        raise SefazSchemaError(f"NCM deve ter 8 dígitos: '{ncm}'")
    return cleaned


def validar_cfop(cfop: str) -> str:
    """Return 4-digit CFOP or raise ``SefazSchemaError``."""
    cleaned = re.sub(r"\D", "", cfop or "")
    if not _RE_CFOP.match(cleaned):
        raise SefazSchemaError(f"CFOP deve ter 4 dígitos: '{cfop}'")
    return cleaned


def validar_cep(cep: str) -> str:
    """Return 8-digit postal code or raise ``SefazSchemaError``."""
    cleaned = re.sub(r"\D", "", cep or "")
    if not _RE_CEP.match(cleaned):
        raise SefazSchemaError(f"CEP deve ter 8 dígitos: '{cep}'")
    return cleaned


def validar_chave_acesso(chave: str) -> str:
    """Return 44-digit NF-e access key or raise ``SefazSchemaError``."""
    if not _RE_CHAVE.match(chave or ""):
        raise SefazSchemaError(f"Chave de acesso deve ter 44 dígitos: '{chave}'")
    return chave


# ---------------------------------------------------------------------------
# Numeric
# ---------------------------------------------------------------------------

def validar_quantidade(qtde: Decimal | str | float) -> Decimal:
    """Raise ``SefazSchemaError`` if quantity is not positive."""
    d = _to_decimal(qtde)
    if d <= Decimal("0"):
        raise SefazSchemaError(f"Quantidade deve ser positiva: {qtde}")
    return d


def validar_valor(valor: Decimal | str | float, campo: str = "valor") -> Decimal:
    """Raise ``SefazSchemaError`` if monetary value is negative."""
    d = _to_decimal(valor)
    if d < Decimal("0"):
        raise SefazSchemaError(f"Campo '{campo}' não pode ser negativo: {valor}")
    return d


# ---------------------------------------------------------------------------
# NF-e document-level validation
# ---------------------------------------------------------------------------

def validar_dados_nfe(dados: dict) -> list[str]:
    """Validate a full NF-e data dict; return a list of error messages.

    An empty list means the data is valid.  This is a non-raising variant
    suitable for pre-flight checks in the UI layer.

    Expected top-level keys: emitente, destinatario, itens, totais.
    """
    erros: list[str] = []

    emit = dados.get("emitente") or {}
    dest = dados.get("destinatario") or {}
    itens = dados.get("itens") or []
    totais = dados.get("totais") or {}

    # Emitente
    if not emit.get("cnpj"):
        erros.append("Emitente: CNPJ obrigatório")
    else:
        try:
            validar_cnpj(emit["cnpj"])
        except SefazSchemaError as exc:
            erros.append(f"Emitente: {exc}")

    if not emit.get("nome"):
        erros.append("Emitente: razão social obrigatória")
    if not emit.get("uf"):
        erros.append("Emitente: UF obrigatória")

    # Destinatário
    doc_dest = dest.get("cnpj") or dest.get("cpf")
    if doc_dest:
        try:
            validar_cpf_ou_cnpj(doc_dest)
        except SefazSchemaError as exc:
            erros.append(f"Destinatário: {exc}")

    # Itens
    if not itens:
        erros.append("NF-e deve conter pelo menos um item")
    for i, item in enumerate(itens, 1):
        prefix = f"Item {i}"
        if not item.get("descricao"):
            erros.append(f"{prefix}: descrição obrigatória")
        if not item.get("ncm"):
            erros.append(f"{prefix}: NCM obrigatório")
        else:
            try:
                validar_ncm(item["ncm"])
            except SefazSchemaError as exc:
                erros.append(f"{prefix}: {exc}")
        if not item.get("cfop"):
            erros.append(f"{prefix}: CFOP obrigatório")
        try:
            validar_quantidade(item.get("quantidade", 0))
        except SefazSchemaError as exc:
            erros.append(f"{prefix}: {exc}")
        try:
            validar_valor(item.get("valor_unitario", 0), "valor_unitario")
        except SefazSchemaError as exc:
            erros.append(f"{prefix}: {exc}")

    # Totais
    if totais:
        try:
            validar_valor(totais.get("valor_total", 0), "valor_total")
        except SefazSchemaError as exc:
            erros.append(f"Totais: {exc}")

    return erros


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        raise SefazSchemaError(f"Valor não numérico: {value!r}")


def _dv_cnpj_ok(cnpj: str) -> bool:
    """Validate CNPJ check digits."""
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    nums = [int(c) for c in cnpj]
    # First digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    rem = sum(n * w for n, w in zip(nums[:12], weights1)) % 11
    d1 = 0 if rem < 2 else 11 - rem
    # Second digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    rem = sum(n * w for n, w in zip(nums[:13], weights2)) % 11
    d2 = 0 if rem < 2 else 11 - rem
    return nums[12] == d1 and nums[13] == d2


def _dv_cpf_ok(cpf: str) -> bool:
    """Validate CPF check digits."""
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    nums = [int(c) for c in cpf]
    # First digit
    rem = sum(n * (10 - i) for i, n in enumerate(nums[:9])) % 11
    d1 = 0 if rem < 2 else 11 - rem
    # Second digit
    rem = sum(n * (11 - i) for i, n in enumerate(nums[:10])) % 11
    d2 = 0 if rem < 2 else 11 - rem
    return nums[9] == d1 and nums[10] == d2
