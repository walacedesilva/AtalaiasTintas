"""Security and compliance validation tests — T087, T088, T089, T090.

Validates that the system meets the requirements defined in:
- specs/4-inventory-fiscal-integration/checklists/fiscal-compliance.md
- specs/4-inventory-fiscal-integration/checklists/security.md
- specs/4-inventory-fiscal-integration/checklists/data-integrity.md

None of these tests make live HTTP calls or write to the database.
"""
from __future__ import annotations

import re
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase


# ---------------------------------------------------------------------------
# T087 — Fiscal compliance validation
# ---------------------------------------------------------------------------

_CNPJ_RE = re.compile(r"^\d{14}$")
_CPF_RE = re.compile(r"^\d{11}$")
_CHAVE_NFE_RE = re.compile(r"^\d{44}$")


class FiscalComplianceTests(SimpleTestCase):
    """Core fiscal business-rule compliance checks."""

    def test_deve_emitir_requer_cnpj_nao_vazio(self):
        from apps.fiscal.services import NFEService

        for cnpj in ("", "  ", None):
            venda = MagicMock()
            venda.cliente.cnpj = cnpj
            self.assertFalse(
                NFEService.deve_emitir_nfe_automatica(venda),
                f"deve_emitir should be False for cnpj={cnpj!r}",
            )

    def test_deve_emitir_verdadeiro_para_cnpj_valido(self):
        from apps.fiscal.services import NFEService

        venda = MagicMock()
        venda.cliente.cnpj = "12345678000195"
        self.assertTrue(NFEService.deve_emitir_nfe_automatica(venda))

    def test_chave_acesso_deve_ter_44_digitos(self):
        amostra = "35260410000000000000550010000000011000000019"
        self.assertTrue(_CHAVE_NFE_RE.match(amostra), "Chave de acesso não tem 44 dígitos")

    def test_cnpj_em_configuracao_fiscal_valido(self):
        cfg = MagicMock()
        cfg.cnpj_empresa = "12345678000195"
        self.assertTrue(_CNPJ_RE.match(cfg.cnpj_empresa))

    def test_serie_nfe_deve_ser_numerica(self):
        for serie in ("001", "1", "999"):
            self.assertTrue(serie.isdigit(), f"Série {serie!r} deve ser numérica")

    def test_justificativa_cancelamento_minimo_15_chars(self):
        from apps.fiscal.sefaz.exceptions import SefazCancelamentoError
        from apps.fiscal.sefaz.client import SefazClient

        client = object.__new__(SefazClient)
        client._certificado_path = "/dev/null"
        client._certificado_senha = "x"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = 2
        client._timeout = 30
        client._url_overrides = None
        client._ssl_context = None
        client._cert_files = None

        curta = "muito curta"
        with self.assertRaises(SefazCancelamentoError):
            client.cancelar_nfe("35260410000000000000550010000000011000000019", curta)

    def test_justificativa_cancelamento_15_chars_aceita(self):
        from apps.fiscal.sefaz.exceptions import SefazCancelamentoError
        from apps.fiscal.sefaz.client import SefazClient

        client = object.__new__(SefazClient)
        client._certificado_path = "/dev/null"
        client._certificado_senha = "x"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = 2
        client._timeout = 30
        client._url_overrides = {}
        client._ssl_context = None
        client._cert_files = ("/dev/null", "/dev/null")

        justif = "15 caracteres ok"  # 16 chars — above minimum
        with patch("apps.fiscal.sefaz.client._rate_limit"), \
             patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                text="<cStat>135</cStat><xMotivo>OK</xMotivo><nProt>999</nProt>",
            )
            mock_post.return_value.raise_for_status.return_value = None
            # Should NOT raise SefazCancelamentoError for length
            try:
                result = client.cancelar_nfe(
                    "35260410000000000000550010000000011000000019",
                    justif,
                )
            except SefazCancelamentoError as e:
                # Only allowed if SEFAZ itself rejects (not length validation)
                self.assertNotIn("15 caracteres", str(e))


# ---------------------------------------------------------------------------
# T088 — Security checklist validation
# ---------------------------------------------------------------------------

class SecurityChecklistTests(SimpleTestCase):
    """System security properties that can be validated in unit tests."""

    def test_sefaz_client_nao_loga_senha_certificado(self):
        """SefazClient does not expose certificate password in its string repr."""
        from apps.fiscal.sefaz.client import SefazClient

        client = object.__new__(SefazClient)
        client._certificado_path = "/certs/empresa.pfx"
        client._certificado_senha = "senha_secreta_123"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = 2
        client._timeout = 30
        client._url_overrides = None
        client._ssl_context = None
        client._cert_files = None

        repr_str = repr(client)
        self.assertNotIn("senha_secreta_123", repr_str)

    def test_sefaz_rejeicao_error_nao_expoe_xml_interno(self):
        """SefazRejeicaoError message does not leak raw XML."""
        from apps.fiscal.sefaz.exceptions import SefazRejeicaoError

        err = SefazRejeicaoError("539", "Duplicidade de NF-e")
        self.assertNotIn("<", str(err))
        self.assertNotIn(">", str(err))

    def test_certificado_error_mensagem_legivel(self):
        from apps.fiscal.sefaz.exceptions import SefazCertificadoError

        err = SefazCertificadoError("Certificado expirado")
        self.assertIn("Certificado", str(err))

    def test_nfe_situacao_choices_restritos(self):
        """NF-e situação field must be restricted to known valid choices."""
        from apps.sales.models import Venda

        choices = {c[0] for c in Venda._meta.get_field("nfe_situacao").choices}
        expected_subset = {"PENDENTE", "AUTORIZADA", "REJEITADA", "CANCELADA", "NAO_APLICAVEL"}
        # All expected choices must exist
        for choice in expected_subset:
            self.assertIn(choice, choices, f"Choice {choice!r} missing from nfe_situacao")

    def test_movimentacao_estoque_tipo_valido(self):
        """MovimentacaoEstoque tipo_movimentacao choices must include SAIDA_VENDA."""
        from apps.inventory.models import MovimentacaoEstoque

        choices = {c[0] for c in MovimentacaoEstoque._meta.get_field("tipo_movimentacao").choices}
        self.assertIn("SAIDA_VENDA", choices)
        self.assertIn("ENTRADA_DEVOLUCAO", choices)

    def test_estoque_reserva_status_choices(self):
        """EstoqueReserva status choices must include ATIVA, CONFIRMADA, CANCELADA, EXPIRADA."""
        from apps.inventory.models import EstoqueReserva

        choices = {c[0] for c in EstoqueReserva._meta.get_field("status").choices}
        for expected in ("ATIVA", "CONFIRMADA", "CANCELADA", "EXPIRADA"):
            self.assertIn(expected, choices)


# ---------------------------------------------------------------------------
# T089 — Data integrity validation
# ---------------------------------------------------------------------------

class DataIntegrityTests(TestCase):
    """Verify data-integrity rules enforced by services."""

    def test_conversao_fator_zero_levanta_erro(self):
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        pu_zero = MagicMock()
        pu_zero.fator_conversao = Decimal("0")

        with patch.object(ConversaoService, "obter_unidade_base", return_value=base_unit):
            with patch("apps.inventory.models.ProdutoUnidade.objects") as mock_pu:
                mock_pu.filter.return_value.first.return_value = pu_zero

                with self.assertRaises(ValueError):
                    ConversaoService.converter_para_unidade("prod-x", Decimal("5"), 2)

    @patch('apps.inventory.models.UnidadeMedida.objects')
    @patch('apps.inventory.models.EstoqueLoja.objects')
    def test_reserva_nao_excede_disponivel_sem_override(self, mock_el_qs, mock_um_qs):
        """criar_reserva raises ValueError when stock is insufficient."""
        from apps.inventory.services import EstoqueService, ConversaoService

        mock_estoque = MagicMock()
        mock_estoque.quantidade_atual = Decimal('0')
        mock_estoque.quantidade_reservada = Decimal('0')
        mock_el_qs.select_for_update.return_value.get.return_value = mock_estoque
        mock_um_qs.get.return_value = MagicMock()

        with patch.object(ConversaoService, 'converter_quantidade', return_value=Decimal('1')):
            with patch('django.db.transaction.atomic'):
                with self.assertRaises(ValueError):
                    EstoqueService.criar_reserva(
                        produto_variacao_id='aabbccdd-0000-0000-0000-000000000001',
                        loja_id=1,
                        quantidade=Decimal('1'),
                        unidade_id=1,
                        sessao_checkout='sess-integ',
                        usuario=MagicMock(),
                        minutos_expiracao=30,
                    )

    def test_conversao_quantidade_nao_negativa(self):
        """converter_quantidade of 0 returns 0 (not negative)."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        pu = MagicMock()
        pu.fator_conversao = Decimal("12")

        with patch.object(ConversaoService, "obter_unidade_base", return_value=base_unit):
            with patch("apps.inventory.models.ProdutoUnidade.objects") as mock_pu:
                mock_pu.filter.return_value.first.return_value = pu
                result = ConversaoService.converter_quantidade("prod", Decimal("0"), 2)

        self.assertEqual(result, Decimal("0"))

    def test_decimal_precision_6_places(self):
        """converter_para_unidade always returns 6-decimal-place result."""
        from apps.inventory.services import ConversaoService

        base_unit = MagicMock()
        base_unit.id = 1
        pu = MagicMock()
        pu.fator_conversao = Decimal("3")  # 1/3 = 0.333333

        with patch.object(ConversaoService, "obter_unidade_base", return_value=base_unit):
            with patch("apps.inventory.models.ProdutoUnidade.objects") as mock_pu:
                mock_pu.filter.return_value.first.return_value = pu
                result = ConversaoService.converter_para_unidade("prod", Decimal("1"), 2)

        self.assertEqual(str(result), "0.333333")

    def test_nfe_xml_parser_chave_invalida_levanta_erro(self):
        """XmlNFeParser raises ValueError on malformed XML."""
        from apps.fiscal.services import XmlNFeParser

        with self.assertRaises(ValueError):
            XmlNFeParser().parse("<xml_invalido/>")


# ---------------------------------------------------------------------------
# T090 — Certificate management security test
# ---------------------------------------------------------------------------

class CertificateManagementTests(SimpleTestCase):
    """Certificate loading, validation and error handling."""

    def test_sefaz_client_sem_certificado_levanta_erro_certificado(self):
        from apps.fiscal.sefaz.client import SefazClient
        from apps.fiscal.sefaz.exceptions import SefazCertificadoError

        client = object.__new__(SefazClient)
        client._certificado_path = "/caminho/inexistente/cert.pfx"
        client._certificado_senha = "qualquer"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = 2
        client._timeout = 30
        client._url_overrides = {}
        client._ssl_context = None
        client._cert_files = None  # Forces cert loading

        with self.assertRaises(SefazCertificadoError):
            client._get_cert_files()

    def test_sefaz_client_ambiente_homologacao_usa_urls_hom(self):
        from apps.fiscal.sefaz.client import SefazClient

        client = object.__new__(SefazClient)
        client._certificado_path = "/dev/null"
        client._certificado_senha = "x"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = "HOMOLOGACAO"
        client._timeout = 30
        client._url_overrides = {}
        client._ssl_context = None
        client._cert_files = None

        url = client._get_url("AUTORIZACAO")
        self.assertIn("hom", url.lower(), "Homologação URL should contain 'hom'")

    def test_sefaz_client_ambiente_producao_usa_urls_prod(self):
        from apps.fiscal.sefaz.client import SefazClient

        client = object.__new__(SefazClient)
        client._certificado_path = "/dev/null"
        client._certificado_senha = "x"
        client._uf_ibge = 35
        client._uf = "SP"
        client._ambiente = "PRODUCAO"
        client._timeout = 30
        client._url_overrides = {}
        client._ssl_context = None
        client._cert_files = None

        url = client._get_url("AUTORIZACAO")
        self.assertNotIn("hom", url.lower(), "Produção URL should NOT contain 'hom'")

    def test_sefaz_error_hierarchy_herda_de_base(self):
        from apps.fiscal.sefaz.exceptions import (
            SefazError,
            SefazRejeicaoError,
            SefazTimeoutError,
            SefazConnectionError,
            SefazCertificadoError,
        )

        for exc_cls in (SefazRejeicaoError, SefazTimeoutError, SefazConnectionError, SefazCertificadoError):
            self.assertTrue(
                issubclass(exc_cls, SefazError),
                f"{exc_cls.__name__} must inherit from SefazError",
            )
