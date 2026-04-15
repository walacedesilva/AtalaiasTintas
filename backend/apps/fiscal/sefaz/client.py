"""SEFAZ webservice client — T035, T036, T037.

Implements ``autorizar_nfe``, ``consultar_situacao``, and ``cancelar_nfe``.

Implementation notes
--------------------
* Uses ``requests`` (already in requirements) for HTTP.
* Digital signatures use ``cryptography`` (transitive dep of simplejwt/sentry).
* XML generation via stdlib ``xml.etree.ElementTree``.
* Certificate: A1 format (.pfx / .p12) — loaded once and cached.
* SOAP envelope is assembled manually to avoid a ``zeep``/``suds`` dependency.
* Rate limit: 1 req / 2 s enforced with a simple in-process lock + sleep.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import re
import ssl
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Any

import requests

from .exceptions import (
    SefazCancelamentoError,
    SefazCertificadoError,
    SefazConnectionError,
    SefazRejeicaoError,
    SefazTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SEFAZ webservice URL tables (NF-e model 55)
# Key: (uf_ibge, ambiente)
# ambiente: 1=Produção, 2=Homologação
# ---------------------------------------------------------------------------
_SEFAZ_URLS: dict[int, dict[str, str]] = {
    # SVAN (Sefaz Virtual Ambiente Nacional) — serves most UFs for NF-e 55
    "SVAN": {
        "AUTORIZACAO_PRODUCAO":   "https://nfe.sefaz.gov.br/nfe/services/NFeAutorizacao4",
        "AUTORIZACAO_HOMO":       "https://hom.sefaz.gov.br/nfe/services/NFeAutorizacao4",
        "CONSULTA_PROTOCOLO_PROD": "https://nfe.sefaz.gov.br/nfe/services/NFeConsultaProtocolo4",
        "CONSULTA_PROTOCOLO_HOMO": "https://hom.sefaz.gov.br/nfe/services/NFeConsultaProtocolo4",
        "STATUS_PRODUCAO":        "https://nfe.sefaz.gov.br/nfe/services/NFeStatusServico4",
        "STATUS_HOMO":            "https://hom.sefaz.gov.br/nfe/services/NFeStatusServico4",
        "CANCELAMENTO_PRODUCAO":  "https://nfe.sefaz.gov.br/nfe/services/NFeRecepcaoEvento4",
        "CANCELAMENTO_HOMO":      "https://hom.sefaz.gov.br/nfe/services/NFeRecepcaoEvento4",
    },
    # SP has its own infrastructure
    "SP": {
        "AUTORIZACAO_PRODUCAO":   "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
        "AUTORIZACAO_HOMO":       "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx",
        "CONSULTA_PROTOCOLO_PROD": "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
        "CONSULTA_PROTOCOLO_HOMO": "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx",
        "STATUS_PRODUCAO":        "https://nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
        "STATUS_HOMO":            "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx",
        "CANCELAMENTO_PRODUCAO":  "https://nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
        "CANCELAMENTO_HOMO":      "https://homologacao.nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx",
    },
    # MG has its own instance
    "MG": {
        "AUTORIZACAO_PRODUCAO":   "https://nfe.fazenda.mg.gov.br/nfe/services/NFeAutorizacao4",
        "AUTORIZACAO_HOMO":       "https://hnfe.fazenda.mg.gov.br/nfe/services/NFeAutorizacao4",
        "CONSULTA_PROTOCOLO_PROD": "https://nfe.fazenda.mg.gov.br/nfe/services/NFeConsultaProtocolo4",
        "CONSULTA_PROTOCOLO_HOMO": "https://hnfe.fazenda.mg.gov.br/nfe/services/NFeConsultaProtocolo4",
        "STATUS_PRODUCAO":        "https://nfe.fazenda.mg.gov.br/nfe/services/NFeStatusServico4",
        "STATUS_HOMO":            "https://hnfe.fazenda.mg.gov.br/nfe/services/NFeStatusServico4",
        "CANCELAMENTO_PRODUCAO":  "https://nfe.fazenda.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
        "CANCELAMENTO_HOMO":      "https://hnfe.fazenda.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
    },
}

# UFs served by SVAN
_SVAN_UFS = {
    "AC", "AL", "AP", "DF", "ES", "PB", "RN", "RR", "SE",
    "TO", "AM", "RJ", "RS", "SC",
}

# IBGE code → UF sigla
_IBGE_UF: dict[int, str] = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA",
    16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
    24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE",
    29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT",
    52: "GO", 53: "DF",
}

# Minimum seconds between SEFAZ requests (rate limiting)
_MIN_INTERVAL = 2.0
_last_request_time: float = 0.0
_request_lock = threading.Lock()


# ---------------------------------------------------------------------------
# SefazClient
# ---------------------------------------------------------------------------

class SefazClient:
    """Production-ready SEFAZ NF-e 4.00 client.

    Parameters
    ----------
    certificado_path:
        Absolute path to the .pfx / .p12 A1 certificate file.
    certificado_senha:
        Password for the certificate.
    uf_ibge:
        IBGE code of the issuing state (e.g. 35 for SP, 29 for BA).
    ambiente:
        ``'PRODUCAO'`` or ``'HOMOLOGACAO'`` (default).
    timeout:
        HTTP request timeout in seconds (default 30).
    url_overrides:
        Optional dict mapping ``'AUTORIZACAO'|'CONSULTA_PROTOCOLO'|'CANCELAMENTO'``
        to custom URLs (useful for testing with mock servers).
    """

    def __init__(
        self,
        certificado_path: str,
        certificado_senha: str,
        uf_ibge: int = 35,
        ambiente: str = "HOMOLOGACAO",
        timeout: int = 30,
        url_overrides: dict[str, str] | None = None,
    ) -> None:
        self._certificado_path = certificado_path
        self._certificado_senha = certificado_senha
        self._uf_ibge = uf_ibge
        self._uf = _IBGE_UF.get(uf_ibge, "SP")
        self._ambiente = ambiente.upper()
        self._timeout = timeout
        self._url_overrides = url_overrides or {}
        self._ssl_context: ssl.SSLContext | None = None
        self._cert_files: tuple[str, str] | None = None  # (cert.pem, key.pem)

    # ------------------------------------------------------------------
    # Public API — T035, T036, T037
    # ------------------------------------------------------------------

    def autorizar_nfe(self, xml_assinado: str) -> dict[str, Any]:
        """Submit a signed NF-e XML for authorization.

        Parameters
        ----------
        xml_assinado:
            Complete, digitally-signed NF-e XML (layout 4.00).

        Returns
        -------
        dict with keys:
            ``chave_acesso``, ``numero_protocolo``, ``data_autorizacao``,
            ``status`` (``'AUTORIZADA'`` | ``'REJEITADA'``),
            ``codigo_status``, ``motivo_status``, ``xml_retorno``.

        Raises
        ------
        SefazRejeicaoError
            When SEFAZ rejects the NF-e with a business rule error.
        SefazConnectionError / SefazTimeoutError
            On network failures.
        """
        url = self._get_url("AUTORIZACAO")
        soap_body = _build_soap_nfeautorizacaolote(xml_assinado)
        raw = self._post_soap(url, soap_body, action="NFeAutorizacaoLote")

        return self._parse_retorno_autorizacao(raw)

    def consultar_situacao(self, chave_acesso: str) -> dict[str, Any]:
        """Query SEFAZ for the current status of a NF-e by its access key.

        Returns
        -------
        dict with keys:
            ``chave_acesso``, ``situacao``, ``codigo_status``, ``motivo_status``,
            ``numero_protocolo``, ``data_autorizacao``, ``xml_retorno``.
        """
        url = self._get_url("CONSULTA_PROTOCOLO")
        soap_body = _build_soap_consulta_protocolo(chave_acesso)
        raw = self._post_soap(url, soap_body, action="NFeConsultaNF")

        return self._parse_retorno_consulta(raw, chave_acesso)

    def cancelar_nfe(self, chave_acesso: str, justificativa: str, numero_protocolo: str = "") -> dict[str, Any]:
        """Request cancellation of an authorized NF-e.

        Parameters
        ----------
        chave_acesso:
            44-digit access key of the authorized NF-e.
        justificativa:
            Cancellation reason (min 15, max 255 characters).
        numero_protocolo:
            Authorization protocol number (required by SEFAZ).

        Returns
        -------
        dict with keys:
            ``chave_acesso``, ``status``, ``codigo_status``, ``motivo_status``,
            ``numero_protocolo_cancelamento``, ``xml_retorno``.

        Raises
        ------
        SefazCancelamentoError
            When SEFAZ rejects the cancellation request.
        """
        if len(justificativa) < 15:
            raise SefazCancelamentoError(
                "VAL001",
                f"Justificativa de cancelamento deve ter no mínimo 15 caracteres, recebido {len(justificativa)}",
            )

        url = self._get_url("CANCELAMENTO")
        soap_body = _build_soap_cancelamento(chave_acesso, justificativa, numero_protocolo)
        raw = self._post_soap(url, soap_body, action="NFeRecepcaoEvento")

        return self._parse_retorno_cancelamento(raw, chave_acesso)

    def verificar_status_servico(self) -> dict[str, Any]:
        """Check SEFAZ webservice availability.

        Returns
        -------
        dict with keys: ``disponivel`` (bool), ``codigo_status``, ``motivo``.
        """
        url = self._get_url("STATUS")
        soap_body = _build_soap_status_servico(self._uf_ibge, self._ambiente)
        try:
            raw = self._post_soap(url, soap_body, action="NFeStatusServico")
        except (SefazConnectionError, SefazTimeoutError):
            return {"disponivel": False, "codigo_status": "999", "motivo": "Serviço indisponível"}

        codigo = _extract_tag(raw, "cStat")
        motivo = _extract_tag(raw, "xMotivo")
        return {
            "disponivel": codigo == "107",
            "codigo_status": codigo,
            "motivo": motivo,
        }

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    def _parse_retorno_autorizacao(self, xml: str) -> dict[str, Any]:
        codigo = _extract_tag(xml, "cStat")
        motivo = _extract_tag(xml, "xMotivo")
        chave = _extract_tag(xml, "chNFe")
        protocolo = _extract_tag(xml, "nProt")
        data_auth = _extract_tag(xml, "dhRecbto") or _extract_tag(xml, "dRecbto")

        # SEFAZ 100 = Autorizado, 150 = Autorizado fora do prazo
        if codigo in ("100", "150"):
            return {
                "chave_acesso": chave,
                "numero_protocolo": protocolo,
                "data_autorizacao": data_auth,
                "status": "AUTORIZADA",
                "codigo_status": codigo,
                "motivo_status": motivo,
                "xml_retorno": xml,
            }

        # Rejection codes 2xx, 3xx, 4xx, 5xx
        if codigo and codigo[0] in ("2", "3", "4", "5"):
            raise SefazRejeicaoError(codigo, motivo)

        # Other non-success codes
        return {
            "chave_acesso": chave,
            "numero_protocolo": protocolo,
            "data_autorizacao": data_auth,
            "status": "REJEITADA",
            "codigo_status": codigo,
            "motivo_status": motivo,
            "xml_retorno": xml,
        }

    def _parse_retorno_consulta(self, xml: str, chave_acesso: str) -> dict[str, Any]:
        codigo = _extract_tag(xml, "cStat")
        motivo = _extract_tag(xml, "xMotivo")
        protocolo = _extract_tag(xml, "nProt")
        data_auth = _extract_tag(xml, "dhRecbto") or _extract_tag(xml, "dRecbto")

        # 100=Autorizado, 101=Cancelado, 110=Uso denegado
        status_map = {
            "100": "AUTORIZADA",
            "101": "CANCELADA",
            "110": "DENEGADA",
            "150": "AUTORIZADA",
        }

        return {
            "chave_acesso": chave_acesso,
            "situacao": status_map.get(codigo, "DESCONHECIDA"),
            "codigo_status": codigo,
            "motivo_status": motivo,
            "numero_protocolo": protocolo,
            "data_autorizacao": data_auth,
            "xml_retorno": xml,
        }

    def _parse_retorno_cancelamento(self, xml: str, chave_acesso: str) -> dict[str, Any]:
        codigo = _extract_tag(xml, "cStat")
        motivo = _extract_tag(xml, "xMotivo")
        protocolo = _extract_tag(xml, "nProt")

        if codigo not in ("135", "136", "155"):
            raise SefazCancelamentoError(codigo or "999", motivo or "Cancelamento rejeitado")

        return {
            "chave_acesso": chave_acesso,
            "status": "CANCELADA",
            "codigo_status": codigo,
            "motivo_status": motivo,
            "numero_protocolo_cancelamento": protocolo,
            "xml_retorno": xml,
        }

    # ------------------------------------------------------------------
    # HTTP transport
    # ------------------------------------------------------------------

    def _post_soap(self, url: str, soap_body: str, action: str) -> str:
        headers = {
            "Content-Type": "application/soap+xml; charset=utf-8",
            "SOAPAction": action,
        }
        cert_pem, key_pem = self._get_cert_files()
        _rate_limit()

        try:
            response = requests.post(
                url,
                data=soap_body.encode("utf-8"),
                headers=headers,
                cert=(cert_pem, key_pem),
                timeout=self._timeout,
                verify=True,
            )
            response.raise_for_status()
            return response.text
        except requests.Timeout as exc:
            raise SefazTimeoutError(
                f"Timeout ao contatar SEFAZ ({url!r}): {exc}"
            ) from exc
        except requests.ConnectionError as exc:
            raise SefazConnectionError(
                f"Erro de conexão com SEFAZ ({url!r}): {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise SefazConnectionError(
                f"Erro HTTP ao contatar SEFAZ ({url!r}): {exc}"
            ) from exc

    def _get_cert_files(self) -> tuple[str, str]:
        """Extract PEM cert + key from the .pfx file into temp files and cache."""
        if self._cert_files is not None:
            return self._cert_files

        try:
            from cryptography.hazmat.primitives.serialization import (
                Encoding,
                NoEncryption,
                PrivateFormat,
                pkcs12,
            )
        except ImportError as exc:
            raise SefazCertificadoError(
                "Pacote 'cryptography' necessário para carregar o certificado A1. "
                "Execute: pip install cryptography"
            ) from exc

        try:
            with open(self._certificado_path, "rb") as fh:
                pfx_data = fh.read()
        except OSError as exc:
            raise SefazCertificadoError(
                f"Não foi possível ler o certificado: {self._certificado_path} — {exc}"
            ) from exc

        senha_bytes = self._certificado_senha.encode() if isinstance(self._certificado_senha, str) else self._certificado_senha
        try:
            private_key, certificate, _chain = pkcs12.load_key_and_certificates(pfx_data, senha_bytes)
        except Exception as exc:
            raise SefazCertificadoError(
                f"Falha ao carregar certificado .pfx (senha incorreta?): {exc}"
            ) from exc

        cert_pem = certificate.public_bytes(Encoding.PEM).decode()
        key_pem = private_key.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        ).decode()

        # Write to temp files (requests needs file paths for mTLS)
        import atexit
        import os

        cert_fd, cert_path = tempfile.mkstemp(suffix="_cert.pem")
        key_fd, key_path = tempfile.mkstemp(suffix="_key.pem")
        try:
            os.write(cert_fd, cert_pem.encode())
            os.write(key_fd, key_pem.encode())
        finally:
            os.close(cert_fd)
            os.close(key_fd)

        # Ensure cleanup on process exit
        atexit.register(lambda: _safe_remove(cert_path))
        atexit.register(lambda: _safe_remove(key_path))

        self._cert_files = (cert_path, key_path)
        logger.info("Certificado A1 carregado: %s", self._certificado_path)
        return self._cert_files

    # ------------------------------------------------------------------
    # URL resolution
    # ------------------------------------------------------------------

    def _get_url(self, service: str) -> str:
        """Return the SEFAZ URL for the given service name."""
        # Allow full URL override from settings
        override_key = f"SEFAZ_URL_{service.upper()}"
        if override_key in self._url_overrides:
            return self._url_overrides[override_key]

        suffix = "PRODUCAO" if self._ambiente == "PRODUCAO" else "HOMO"
        key = f"{service.upper()}_{suffix}"

        # Per-UF or SVAN fallback
        uf_urls = _SEFAZ_URLS.get(self._uf)
        if uf_urls and key in uf_urls:
            return uf_urls[key]

        # Fall back to SVAN for unlisted UFs
        svan_urls = _SEFAZ_URLS["SVAN"]
        if key in svan_urls:
            return svan_urls[key]

        raise SefazConnectionError(f"URL SEFAZ não encontrada para serviço '{service}' / UF '{self._uf}'")


# ---------------------------------------------------------------------------
# SOAP envelope builders
# ---------------------------------------------------------------------------

def _build_soap_nfeautorizacaolote(xml_nfe: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        "<soap12:Body>"
        '<nfeAutorizacaoLote xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">'
        '<nfeDadosMsg>'
        '<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
        "<idLote>1</idLote>"
        "<indSinc>1</indSinc>"
        + xml_nfe
        + "</enviNFe>"
        "</nfeDadosMsg>"
        "</nfeAutorizacaoLote>"
        "</soap12:Body>"
        "</soap12:Envelope>"
    )


def _build_soap_consulta_protocolo(chave_acesso: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        "<soap12:Body>"
        '<nfeConsultaNF xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">'
        "<nfeDadosMsg>"
        f'<consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
        "<tpAmb>2</tpAmb>"
        f"<xServ>CONSULTAR</xServ>"
        f"<chNFe>{chave_acesso}</chNFe>"
        "</consSitNFe>"
        "</nfeDadosMsg>"
        "</nfeConsultaNF>"
        "</soap12:Body>"
        "</soap12:Envelope>"
    )


def _build_soap_cancelamento(chave_acesso: str, justificativa: str, protocolo: str) -> str:
    # Evento de cancelamento — evento 110111
    dt_evento = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-00:00")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        "<soap12:Body>"
        '<nfeRecepcaoEvento xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">'
        "<nfeDadosMsg>"
        f'<envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
        "<idLote>1</idLote>"
        "<evento versao=\"1.00\">"
        f'<infEvento Id="ID110111{chave_acesso}01">'
        f"<cOrgao>{chave_acesso[0:2]}</cOrgao>"
        "<tpAmb>2</tpAmb>"
        f"<CNPJ>{chave_acesso[6:20]}</CNPJ>"
        f"<chNFe>{chave_acesso}</chNFe>"
        f"<dhEvento>{dt_evento}</dhEvento>"
        "<tpEvento>110111</tpEvento>"
        "<nSeqEvento>1</nSeqEvento>"
        "<verEvento>1.00</verEvento>"
        "<detEvento versao=\"1.00\">"
        "<descEvento>Cancelamento</descEvento>"
        f"<nProt>{protocolo}</nProt>"
        f"<xJust>{justificativa}</xJust>"
        "</detEvento>"
        "</infEvento>"
        "</evento>"
        "</envEvento>"
        "</nfeDadosMsg>"
        "</nfeRecepcaoEvento>"
        "</soap12:Body>"
        "</soap12:Envelope>"
    )


def _build_soap_status_servico(uf_ibge: int, ambiente: str) -> str:
    tp_amb = "1" if ambiente == "PRODUCAO" else "2"
    cuf = str(uf_ibge)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
        "<soap12:Body>"
        '<nfeStatusServico xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4">'
        "<nfeDadosMsg>"
        f'<consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
        f"<tpAmb>{tp_amb}</tpAmb>"
        f"<cUF>{cuf}</cUF>"
        "<xServ>STATUS</xServ>"
        "</consStatServ>"
        "</nfeDadosMsg>"
        "</nfeStatusServico>"
        "</soap12:Body>"
        "</soap12:Envelope>"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tag(xml: str, tag: str) -> str:
    """Extract inner text of the first occurrence of ``<tag>`` in XML string."""
    match = re.search(rf"<{re.escape(tag)}[^>]*>(.*?)</{re.escape(tag)}>", xml, re.DOTALL)
    return match.group(1).strip() if match else ""


def _rate_limit() -> None:
    """Enforce minimum 2-second interval between SEFAZ requests."""
    global _last_request_time
    with _request_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL - (now - _last_request_time)
        if wait > 0:
            time.sleep(wait)
        _last_request_time = time.monotonic()


def _safe_remove(path: str) -> None:
    """Remove a file, silencing errors."""
    import os
    try:
        os.unlink(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Factory — create SefazClient from Django settings / environment
# ---------------------------------------------------------------------------

def criar_sefaz_client() -> SefazClient:
    """Instantiate a ``SefazClient`` from Django settings or environment variables.

    Settings keys (via ``python-decouple`` or ``os.environ``):
        NFE_CERTIFICADO_PATH, NFE_CERTIFICADO_SENHA,
        NFE_UF_IBGE, NFE_AMBIENTE, NFE_TIMEOUT,
        SEFAZ_URL_AUTORIZACAO, SEFAZ_URL_CONSULTA_PROTOCOLO,
        SEFAZ_URL_CANCELAMENTO (all optional overrides).
    """
    from decouple import config

    overrides: dict[str, str] = {}
    for service in ("AUTORIZACAO", "CONSULTA_PROTOCOLO", "CANCELAMENTO", "STATUS"):
        val = config(f"SEFAZ_URL_{service}", default="")
        if val:
            overrides[f"SEFAZ_URL_{service}"] = val

    return SefazClient(
        certificado_path=config("NFE_CERTIFICADO_PATH", default=""),
        certificado_senha=config("NFE_CERTIFICADO_SENHA", default=""),
        uf_ibge=config("NFE_UF_IBGE", default=35, cast=int),
        ambiente=config("NFE_AMBIENTE", default="HOMOLOGACAO"),
        timeout=config("NFE_TIMEOUT", default=30, cast=int),
        url_overrides=overrides,
    )
