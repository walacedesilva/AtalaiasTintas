"""SEFAZ VCR cassette-based tests — T079, T080, T081, T082.

Uses cassette JSON fixtures in tests/fiscal/cassettes/ to replay real-world
SEFAZ SOAP responses without live HTTP calls.  The SefazClient is configured
via _make_client() (bypasses __init__) and requests.post is patched to
return the cassette response.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from apps.fiscal.sefaz.client import SefazClient
from apps.fiscal.sefaz.exceptions import (
    SefazRejeicaoError,
    SefazTimeoutError,
    SefazConnectionError,
)

# ---------------------------------------------------------------------------
# Cassette helpers (T079)
# ---------------------------------------------------------------------------

CASSETTES_DIR = Path(__file__).parent / "cassettes"


def _load_cassette(name: str) -> dict:
    """Load a cassette JSON fixture by filename stem (without .json)."""
    path = CASSETTES_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _mock_response_from_cassette(cassette: dict) -> MagicMock:
    """Build a mock requests.Response from a cassette dict."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = cassette["http_status"]
    resp.text = cassette["response_body"]
    resp.raise_for_status.return_value = None
    return resp


def _make_client() -> SefazClient:
    """Create a SefazClient bypassing __init__ (no real cert needed)."""
    client = object.__new__(SefazClient)
    client._certificado_path = "/dev/null"
    client._certificado_senha = "test"
    client._uf_ibge = 35  # São Paulo
    client._uf = "SP"
    client._ambiente = "HOMOLOGACAO"
    client._timeout = 30
    client._url_overrides = {}
    client._ssl_context = None
    client._cert_files = ("/tmp/cert.pem", "/tmp/key.pem")  # bypass _get_cert_files
    return client


# ---------------------------------------------------------------------------
# T079 — Validate cassette files exist and are well-formed
# ---------------------------------------------------------------------------

class CassetteFilesTests(SimpleTestCase):
    """Ensure all cassette fixtures are present and parseable."""

    def _assert_cassette_valid(self, name: str):
        cassette = _load_cassette(name)
        self.assertIn("http_status", cassette)
        self.assertIn("response_body", cassette)
        self.assertIn("description", cassette)
        self.assertIsInstance(cassette["response_body"], str)
        self.assertGreater(len(cassette["response_body"]), 50)

    def test_cassette_autorizacao_sucesso_existe(self):
        self._assert_cassette_valid("autorizacao_sucesso")

    def test_cassette_rejeicao_539_existe(self):
        self._assert_cassette_valid("rejeicao_539")

    def test_cassette_consulta_autorizada_existe(self):
        self._assert_cassette_valid("consulta_autorizada")

    def test_cassette_cancelamento_sucesso_existe(self):
        self._assert_cassette_valid("cancelamento_sucesso")


# ---------------------------------------------------------------------------
# T080 — SEFAZ authorization success test (VCR replay)
# ---------------------------------------------------------------------------

class SefazAutorizacaoVCRTests(SimpleTestCase):
    """Replay autorizacao_sucesso cassette through SefazClient."""

    def setUp(self):
        self.client = _make_client()
        self.cassette = _load_cassette("autorizacao_sucesso")
        self.chave = "35260410000000000000550010000000011000000019"
        self.xml_nfe = f"<NFe><infNFe Id='NFe{self.chave}'></infNFe></NFe>"

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_autorizacao_retorna_chave_acesso(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        result = self.client.autorizar_nfe(self.xml_nfe)

        self.assertEqual(result["status"], "AUTORIZADA")
        self.assertEqual(result["codigo_status"], "100")
        self.assertIn("chave_acesso", result)
        self.assertIn("numero_protocolo", result)
        mock_post.assert_called_once()

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_autorizacao_retorna_protocolo_correto(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        result = self.client.autorizar_nfe(self.xml_nfe)

        self.assertEqual(result["numero_protocolo"], "135260410000000001")
        self.assertIsNotNone(result["data_autorizacao"])

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_autorizacao_faz_post_para_url_correta(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        self.client.autorizar_nfe(self.xml_nfe)

        called_url = mock_post.call_args[0][0]
        self.assertIn("nfeautorizacao", called_url.lower())


# ---------------------------------------------------------------------------
# T081 — SEFAZ rejection handling test (VCR replay)
# ---------------------------------------------------------------------------

class SefazRejeicaoVCRTests(SimpleTestCase):
    """Replay rejeicao_539 cassette and verify exception raised."""

    def setUp(self):
        self.client = _make_client()
        self.cassette = _load_cassette("rejeicao_539")
        self.chave = "35260410000000000000550010000000011000000019"
        self.xml_nfe = f"<NFe><infNFe Id='NFe{self.chave}'></infNFe></NFe>"

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_rejeicao_levanta_sefaz_rejeicao_error(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        with self.assertRaises(SefazRejeicaoError) as cm:
            self.client.autorizar_nfe(self.xml_nfe)

        self.assertEqual(cm.exception.codigo, "539")

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_rejeicao_539_e_corrigivel(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        with self.assertRaises(SefazRejeicaoError) as cm:
            self.client.autorizar_nfe(self.xml_nfe)

        self.assertTrue(cm.exception.corrigivel)

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_rejeicao_motivo_vem_da_resposta(self, mock_post, mock_rate):
        mock_post.return_value = _mock_response_from_cassette(self.cassette)

        with self.assertRaises(SefazRejeicaoError) as cm:
            self.client.autorizar_nfe(self.xml_nfe)

        self.assertIn("Duplicidade", cm.exception.motivo)

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_consulta_autorizada_retorna_status(self, mock_post, mock_rate):
        """Validate consulta cassette in the same test module."""
        cassette = _load_cassette("consulta_autorizada")
        mock_post.return_value = _mock_response_from_cassette(cassette)

        result = self.client.consultar_situacao(self.chave)

        self.assertEqual(result["situacao"], "AUTORIZADA")
        self.assertEqual(result["codigo_status"], "100")


# ---------------------------------------------------------------------------
# T082 — SEFAZ timeout and connection error handling
# ---------------------------------------------------------------------------

class SefazTimeoutVCRTests(SimpleTestCase):
    """Simulate HTTP-level errors (timeout, connection refused)."""

    def setUp(self):
        self.client = _make_client()
        self.chave = "35260410000000000000550010000000011000000019"
        self.xml_nfe = f"<NFe><infNFe Id='NFe{self.chave}'></infNFe></NFe>"

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post", side_effect=requests.Timeout("timed out"))
    def test_timeout_levanta_sefaz_timeout_error(self, mock_post, mock_rate):
        with self.assertRaises(SefazTimeoutError):
            self.client.autorizar_nfe(self.xml_nfe)

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post", side_effect=requests.ConnectionError("ECONNREFUSED"))
    def test_connection_error_levanta_sefaz_connection_error(self, mock_post, mock_rate):
        with self.assertRaises(SefazConnectionError):
            self.client.autorizar_nfe(self.xml_nfe)

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post", side_effect=requests.Timeout("timed out"))
    def test_verificar_status_servico_com_timeout_retorna_indisponivel(self, mock_post, mock_rate):
        result = self.client.verificar_status_servico()

        self.assertFalse(result["disponivel"])
        self.assertEqual(result["codigo_status"], "999")

    @patch("apps.fiscal.sefaz.client._rate_limit")
    @patch("requests.post")
    def test_cancelamento_sucesso_via_cassette(self, mock_post, mock_rate):
        cassette = _load_cassette("cancelamento_sucesso")
        mock_post.return_value = _mock_response_from_cassette(cassette)

        result = self.client.cancelar_nfe(
            self.chave,
            "Justificativa de cancelamento de teste",
            numero_protocolo="135260410000000001",
        )

        self.assertEqual(result["status"], "CANCELADA")
        self.assertEqual(result["codigo_status"], "135")
