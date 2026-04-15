"""SEFAZ exception hierarchy (T038).

All exceptions raised by the SEFAZ integration layer inherit from
``SefazError``, making it easy for callers to catch the whole family.
"""
from __future__ import annotations


class SefazError(Exception):
    """Base class for all SEFAZ-related exceptions."""

    def __init__(self, message: str = "", codigo: str = "", motivo: str = "") -> None:
        self.codigo = codigo
        self.motivo = motivo
        super().__init__(message or motivo or "Erro na integração SEFAZ")

    def __str__(self) -> str:  # pragma: no cover
        parts = [super().__str__()]
        if self.codigo:
            parts.append(f"[código={self.codigo}]")
        if self.motivo:
            parts.append(f"[motivo={self.motivo}]")
        return " ".join(parts)


class SefazConnectionError(SefazError):
    """Cannot reach the SEFAZ webservice endpoint."""


class SefazTimeoutError(SefazConnectionError):
    """SEFAZ request exceeded the configured timeout."""


class SefazCertificadoError(SefazError):
    """Problem loading or using the A1 digital certificate."""


class SefazSchemaError(SefazError):
    """Generated NF-e XML does not conform to layout 4.00 schema."""


class SefazRejeicaoError(SefazError):
    """SEFAZ returned a *rejeição* (business-rule rejection).

    Attributes:
        codigo:  SEFAZ rejection code (e.g. "539", "229").
        motivo:  Human-readable reason returned by SEFAZ.
        corrigivel: Whether the error can be corrected and re-submitted.
    """

    # Rejection codes that are permanently invalid (not worth retrying)
    _REJEICOES_DEFINITIVAS = {
        "204", "205", "206", "207", "208", "209",
        "301", "302", "303", "304", "305",
        "498", "499",
    }

    def __init__(self, codigo: str, motivo: str) -> None:
        self.corrigivel = codigo not in self._REJEICOES_DEFINITIVAS
        super().__init__(
            message=f"Rejeição SEFAZ {codigo}: {motivo}",
            codigo=codigo,
            motivo=motivo,
        )


class SefazAutorizacaoError(SefazError):
    """SEFAZ returned a *denegação* (authorization denied with definitive status)."""


class SefazCancelamentoError(SefazError):
    """Cancellation request rejected by SEFAZ."""

    def __init__(self, codigo: str, motivo: str) -> None:
        super().__init__(
            message=f"Cancelamento rejeitado {codigo}: {motivo}",
            codigo=codigo,
            motivo=motivo,
        )
