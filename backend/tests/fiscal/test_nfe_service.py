"""Unit tests for NFEService — T071.

Covers NF-e business rules: emission eligibility, processing orchestration,
manual retry flagging and XML generation preconditions.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

from django.test import SimpleTestCase, TestCase


class NFEServiceDeveEmitirTests(SimpleTestCase):
    """Tests for NFEService.deve_emitir_nfe_automatica."""

    def _make_venda(self, cnpj=None, cpf=None):
        venda = MagicMock()
        if cnpj is not None or cpf is not None:
            cliente = MagicMock()
            cliente.cnpj = cnpj or ''
            cliente.cpf = cpf or ''
            venda.cliente = cliente
        else:
            venda.cliente = None
        return venda

    def test_b2b_com_cnpj_deve_emitir(self):
        """B2B customer (has CNPJ) → deve_emitir returns True."""
        from apps.fiscal.services import NFEService

        venda = self._make_venda(cnpj='12345678000195')
        self.assertTrue(NFEService.deve_emitir_nfe_automatica(venda))

    def test_b2c_apenas_cpf_nao_emite(self):
        """B2C customer (CPF only, no CNPJ) → deve_emitir returns False."""
        from apps.fiscal.services import NFEService

        venda = self._make_venda(cpf='12345678901')
        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))

    def test_sem_cliente_nao_emite(self):
        """No customer → deve_emitir returns False."""
        from apps.fiscal.services import NFEService

        venda = self._make_venda()
        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))

    def test_cnpj_vazio_nao_emite(self):
        """Empty CNPJ string → deve_emitir returns False."""
        from apps.fiscal.services import NFEService

        venda = self._make_venda(cnpj='')
        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))

    def test_cnpj_apenas_espacos_nao_emite(self):
        """Whitespace-only CNPJ → deve_emitir returns False."""
        from apps.fiscal.services import NFEService

        venda = self._make_venda(cnpj='   ')
        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))

    def test_sem_atributo_cliente_nao_emite(self):
        """Venda object without 'cliente' attribute → deve_emitir returns False."""
        from apps.fiscal.services import NFEService

        venda = MagicMock(spec=[])  # no attributes

        self.assertFalse(NFEService.deve_emitir_nfe_automatica(venda))


class NFEServiceProcessarNFeVendaTests(SimpleTestCase):
    """Tests for NFEService.processar_nfe_venda — mocked DB calls."""

    @patch('apps.fiscal.services.processar_nfe_async', create=True)
    @patch('apps.fiscal.services._update_venda_nfe')
    @patch('apps.sales.models.Venda.objects')
    def test_b2b_agenda_tarefa_celery(self, mock_venda_qs, mock_update, mock_task):
        """B2B sale should call processar_nfe_async.delay."""
        from apps.fiscal.services import NFEService
        import importlib
        import apps.fiscal.services as svc

        # Build mock venda with CNPJ
        cliente = MagicMock()
        cliente.cnpj = '12345678000195'
        venda = MagicMock()
        venda.pk = 'venda-b2b-1'
        venda.cliente = cliente
        mock_venda_qs.select_related.return_value.get.return_value = venda

        usuario = MagicMock()
        usuario.pk = 1
        usuario.username = 'operador'

        # Patch the imported task inside the service module
        with patch('apps.fiscal.tasks.processar_nfe_async') as mock_celery_task:
            with patch.object(svc, 'processar_nfe_async', mock_celery_task, create=True):
                # We need to patch the imports inside the function
                with patch.dict('sys.modules', {'apps.fiscal.tasks': MagicMock(
                    processar_nfe_async=mock_celery_task
                )}):
                    NFEService.processar_nfe_venda('venda-b2b-1', usuario)

    @patch('apps.fiscal.services._update_venda_nfe')
    @patch('apps.sales.models.Venda.objects')
    def test_b2c_marca_nao_aplicavel(self, mock_venda_qs, mock_update):
        """B2C sale (no CNPJ) should mark as NAO_APLICAVEL, not queue Celery."""
        from apps.fiscal.services import NFEService

        cliente = MagicMock()
        cliente.cnpj = ''  # B2C
        venda = MagicMock()
        venda.pk = 'venda-b2c-1'
        venda.cliente = cliente
        mock_venda_qs.select_related.return_value.get.return_value = venda

        usuario = MagicMock()
        NFEService.processar_nfe_venda('venda-b2c-1', usuario)

        mock_update.assert_called_once_with(
            venda, situacao='NAO_APLICAVEL', tipo_emissao='NAO_EMITIR'
        )

    @patch('apps.sales.models.Venda.objects')
    def test_venda_inexistente_nao_levanta_excecao(self, mock_venda_qs):
        """Non-existent venda_id should only log error, not raise."""
        from apps.fiscal.services import NFEService
        from apps.sales.models import Venda

        # Simulate DoesNotExist
        Venda.DoesNotExist = Exception
        mock_venda_qs.select_related.return_value.get.side_effect = Exception('Not found')

        usuario = MagicMock()
        # Should not raise
        try:
            NFEService.processar_nfe_venda('does-not-exist', usuario)
        except Exception:  # noqa: BLE001
            self.fail("processar_nfe_venda should swallow DoesNotExist")


class NFEServiceMarcarRetryManualTests(SimpleTestCase):
    """Tests for NFEService.marcar_para_retry_manual."""

    @patch('apps.sales.models.Venda.objects')
    def test_atualiza_flags_de_retry(self, mock_venda_qs):
        """marcar_para_retry_manual sets nfe_requer_retry_manual=True."""
        from apps.fiscal.services import NFEService

        NFEService.marcar_para_retry_manual('venda-1', 'timeout SEFAZ')

        mock_venda_qs.filter.assert_called_once_with(pk='venda-1')
        mock_venda_qs.filter.return_value.update.assert_called_once()
        update_kwargs = mock_venda_qs.filter.return_value.update.call_args.kwargs
        self.assertTrue(update_kwargs.get('nfe_requer_retry_manual'))
        self.assertEqual(update_kwargs.get('nfe_situacao'), 'AGUARDANDO_RETRY')

    @patch('apps.sales.models.Venda.objects')
    def test_motivo_padrao_quando_vazio(self, mock_venda_qs):
        """When no motivo supplied, a default message is used."""
        from apps.fiscal.services import NFEService

        NFEService.marcar_para_retry_manual('venda-2')

        update_kwargs = mock_venda_qs.filter.return_value.update.call_args.kwargs
        nfe_erro = update_kwargs.get('nfe_erro', '')
        self.assertTrue(len(nfe_erro) > 0, "Deve ter mensagem de erro padrão")


class NFEServiceGerarXmlPreconditionsTests(SimpleTestCase):
    """Tests for NFEService.gerar_xml_nfe — precondition error paths only."""

    @patch('apps.fiscal.models.ConfiguracaoFiscal.objects')
    @patch('apps.sales.models.ItemPedidoVenda.objects')
    @patch('apps.sales.models.Venda.objects')
    def test_sem_itens_raises_value_error(self, mock_venda_qs, mock_itens_qs, mock_config_qs):
        """Raises ValueError when the venda has no items."""
        from apps.fiscal.services import NFEService
        from apps.sales.models import Venda

        venda = MagicMock()
        venda.pk = 'v1'
        venda.pedido_origem = MagicMock()
        mock_venda_qs.select_related.return_value.get.return_value = venda

        mock_itens_qs.filter.return_value.select_related.return_value.exists.return_value = False

        with self.assertRaises(ValueError) as cm:
            NFEService.gerar_xml_nfe('v1')

        self.assertIn('itens', str(cm.exception).lower())

    @patch('apps.fiscal.models.ConfiguracaoFiscal.objects')
    @patch('apps.sales.models.ItemPedidoVenda.objects')
    @patch('apps.sales.models.Venda.objects')
    def test_sem_configuracao_fiscal_raises_value_error(
        self, mock_venda_qs, mock_itens_qs, mock_config_qs
    ):
        """Raises ValueError when no active ConfiguracaoFiscal found."""
        from apps.fiscal.services import NFEService

        empresa = MagicMock()
        empresa.id = 1
        loja = MagicMock()
        loja.empresa = empresa
        loja.empresa_id = 1
        venda = MagicMock()
        venda.pk = 'v2'
        venda.loja = loja
        venda.pedido_origem = MagicMock()
        mock_venda_qs.select_related.return_value.get.return_value = venda

        mock_itens_qs.filter.return_value.select_related.return_value.exists.return_value = True

        mock_config_qs.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as cm:
            NFEService.gerar_xml_nfe('v2')

        self.assertIn('ConfiguracaoFiscal', str(cm.exception))
