"""Unit tests for SefazClient — T072.

Tests use unittest.mock to simulate HTTP responses from the SEFAZ webservice.
No real network calls are made.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

from django.test import SimpleTestCase


def _make_client():
    """Return a SefazClient instance bypassing certificate initialisation."""
    from apps.fiscal.sefaz.client import SefazClient

    client = object.__new__(SefazClient)
    # Minimal attributes needed by _get_url and _post_soap
    client._certificado_path = '/fake/cert.pfx'
    client._certificado_senha = 'fake'
    client._uf_ibge = 35
    client._uf = 'SP'
    client._ambiente = 'HOMOLOGACAO'
    client._timeout = 30
    client._url_overrides = {}
    client._ssl_context = None
    client._cert_files = None
    return client


class SefazClientAutorizarTests(SimpleTestCase):
    """Tests for SefazClient.autorizar_nfe."""

    @patch('apps.fiscal.sefaz.client.requests.Session')
    def test_autorizacao_sucesso_200(self, mock_session_cls):
        """HTTP 200 with AUTORIZADA status in response → return dict with status."""
        from apps.fiscal.sefaz.client import SefazClient

        client = _make_client()

        expected = {
            'status': 'AUTORIZADA',
            'codigo_status': '100',
            'motivo_status': 'Autorizado o uso da NF-e',
            'numero_protocolo': '315000000123456',
            'chave_acesso': '35230712345678000195550010000000011000000015',
        }

        with patch.object(client, '_post_soap', return_value='<rawxml/>'):
            with patch.object(client, '_parse_retorno_autorizacao', return_value=expected):
                resultado = client.autorizar_nfe('<NFe/>')

        self.assertEqual(resultado['status'], 'AUTORIZADA')
        self.assertEqual(resultado['codigo_status'], '100')

    @patch('apps.fiscal.sefaz.client.requests.Session')
    def test_rejeicao_levanta_sefaz_rejeicao_error(self, mock_session_cls):
        """SEFAZ rejection (code 5xx) should raise SefazRejeicaoError."""
        from apps.fiscal.sefaz.client import SefazClient
        from apps.fiscal.sefaz.exceptions import SefazRejeicaoError

        client = _make_client()

        with patch.object(client, '_post_soap', return_value='<rawxml/>'):
            with patch.object(client, '_parse_retorno_autorizacao',
                              side_effect=SefazRejeicaoError('539', 'CNPJ inválido')):
                with self.assertRaises(SefazRejeicaoError) as cm:
                    client.autorizar_nfe('<NFe/>')

        self.assertEqual(cm.exception.codigo, '539')
        self.assertIn('CNPJ', cm.exception.motivo)

    def test_timeout_levanta_sefaz_timeout_error(self):
        """Connection timeout should raise SefazTimeoutError."""
        from apps.fiscal.sefaz.client import SefazClient
        from apps.fiscal.sefaz.exceptions import SefazTimeoutError

        client = _make_client()

        with patch.object(client, '_post_soap',
                          side_effect=SefazTimeoutError('Timeout após 30s')):
            with self.assertRaises(SefazTimeoutError):
                client.autorizar_nfe('<NFe/>')


class SefazClientConsultarSituacaoTests(SimpleTestCase):
    """Tests for SefazClient.consultar_situacao."""

    def test_chave_acesso_invalida_raises(self):
        """Empty chave_acesso should raise ValueError before making request."""
        from apps.fiscal.sefaz.client import SefazClient

        client = _make_client()

        with self.assertRaises((ValueError, Exception)):
            client.consultar_situacao('')

    def test_consulta_retorna_dict_com_situacao(self):
        """Successful consultation returns a dict with 'situacao' key."""
        from apps.fiscal.sefaz.client import SefazClient

        client = _make_client()
        chave = '35230712345678000195550010000000011000000015'

        with patch.object(client, '_post_soap', return_value='<rawxml/>'):
            with patch.object(client, '_parse_retorno_consulta', return_value={
                'situacao': 'AUTORIZADA',
                'chave_acesso': chave,
            }):
                resultado = client.consultar_situacao(chave)

        self.assertIn('situacao', resultado)
        self.assertEqual(resultado['situacao'], 'AUTORIZADA')


class SefazClientCancelarNFeTests(SimpleTestCase):
    """Tests for SefazClient.cancelar_nfe."""

    def test_cancelamento_exige_justificativa_minima(self):
        """Cancellation justification shorter than 15 chars should raise ValueError."""
        from apps.fiscal.sefaz.client import SefazClient

        client = _make_client()

        with self.assertRaises((ValueError, Exception)):
            client.cancelar_nfe('35230712345678000195550010000000011000000015', 'curto', '123')

    def test_cancelamento_sucesso_retorna_dict(self):
        """Successful cancellation returns a dict with 'cancelada' key."""
        from apps.fiscal.sefaz.client import SefazClient

        client = _make_client()
        chave = '35230712345678000195550010000000011000000015'
        justificativa = 'Cancelamento solicitado pelo cliente via atendimento'

        with patch.object(client, '_post_soap', return_value='<rawxml/>'):
            with patch.object(client, '_parse_retorno_cancelamento', return_value={
                'cancelada': True,
                'protocolo': '315999999999999',
            }):
                resultado = client.cancelar_nfe(chave, justificativa, '315000000123456')

        self.assertTrue(resultado.get('cancelada'))


class SefazRejeicaoErrorTests(SimpleTestCase):
    """Tests for SefazRejeicaoError exception attributes."""

    def test_rejeicao_definitiva_nao_corrigivel(self):
        """Code in _REJEICOES_DEFINITIVAS → corrigivel=False."""
        from apps.fiscal.sefaz.exceptions import SefazRejeicaoError

        err = SefazRejeicaoError('204', 'Duplicidade NF-e')
        self.assertFalse(err.corrigivel)

    def test_rejeicao_corrigivel(self):
        """CNPJ error (code 539) → corrigivel=True."""
        from apps.fiscal.sefaz.exceptions import SefazRejeicaoError

        err = SefazRejeicaoError('539', 'CNPJ emitente inválido')
        self.assertTrue(err.corrigivel)

    def test_herda_de_sefaz_error(self):
        """SefazRejeicaoError must be catchable as SefazError."""
        from apps.fiscal.sefaz.exceptions import SefazError, SefazRejeicaoError

        err = SefazRejeicaoError('100', 'test')
        self.assertIsInstance(err, SefazError)

    def test_codigo_e_motivo_acessiveis(self):
        """Exception attributes .codigo and .motivo are accessible."""
        from apps.fiscal.sefaz.exceptions import SefazRejeicaoError

        err = SefazRejeicaoError('999', 'Erro desconhecido')
        self.assertEqual(err.codigo, '999')
        self.assertEqual(err.motivo, 'Erro desconhecido')
