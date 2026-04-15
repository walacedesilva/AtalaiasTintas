"""Unit tests for reservation system — T073.

Tests cover EstoqueService reservation lifecycle: creation, confirmation,
cancellation, and expiry/availability interactions.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from django.test import SimpleTestCase, TestCase


class ReservaCreationTests(TestCase):
    """Tests for EstoqueService.criar_reserva — unit/mock level."""

    def _mock_setup(self, quantidade_atual=Decimal('100'), quantidade_reservada=Decimal('0')):
        """Return common mocks for criar_reserva tests."""
        mock_conv = MagicMock(return_value=Decimal('10'))
        mock_unidade = MagicMock()
        mock_unidade_qs = MagicMock()
        mock_unidade_qs.get.return_value = mock_unidade

        estoque = MagicMock()
        estoque.quantidade_atual = quantidade_atual
        estoque.quantidade_reservada = quantidade_reservada
        mock_estoque_qs = MagicMock()
        mock_estoque_qs.select_for_update.return_value.get.return_value = estoque

        mock_reserva = MagicMock()
        mock_reserva_qs = MagicMock()
        mock_reserva_qs.create.return_value = mock_reserva

        return mock_conv, mock_unidade_qs, mock_estoque_qs, mock_reserva_qs, estoque, mock_reserva

    @patch('apps.inventory.services.timezone')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.inventory.models.EstoqueLoja.objects')
    @patch('apps.inventory.models.UnidadeMedida.objects')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    def test_cria_reserva_com_estoque_suficiente(
        self, mock_conv, mock_unidade_qs, mock_estoque_qs, mock_reserva_qs, mock_tz
    ):
        """criar_reserva succeeds when disponivel >= requested."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('10')
        mock_unidade_qs.get.return_value = MagicMock()

        estoque = MagicMock()
        estoque.quantidade_atual = Decimal('100')
        estoque.quantidade_reservada = Decimal('20')
        mock_estoque_qs.select_for_update.return_value.get.return_value = estoque

        reserva = MagicMock()
        mock_reserva_qs.create.return_value = reserva

        mock_tz.now.return_value = MagicMock()
        mock_tz.timedelta.return_value = MagicMock()

        usuario = MagicMock()
        with patch('django.db.transaction.atomic'):
            resultado = EstoqueService.criar_reserva(
                'p', 1, Decimal('10'), 1, 'sess-1', usuario
            )

        self.assertEqual(resultado, reserva)

    @patch('apps.inventory.services.timezone')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.inventory.models.EstoqueLoja.objects')
    @patch('apps.inventory.models.UnidadeMedida.objects')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    def test_cria_reserva_estoque_insuficiente_raises(
        self, mock_conv, mock_unidade_qs, mock_estoque_qs, mock_reserva_qs, mock_tz
    ):
        """criar_reserva raises ValueError when disponivel < requested."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('200')  # needs 200 base units
        mock_unidade_qs.get.return_value = MagicMock()

        estoque = MagicMock()
        estoque.quantidade_atual = Decimal('50')   # only 50 available
        estoque.quantidade_reservada = Decimal('10')
        mock_estoque_qs.select_for_update.return_value.get.return_value = estoque

        usuario = MagicMock()
        with self.assertRaises(ValueError) as cm:
            with patch('django.db.transaction.atomic'):
                EstoqueService.criar_reserva(
                    'p', 1, Decimal('200'), 1, 'sess-2', usuario
                )

        self.assertIn('insuficiente', str(cm.exception).lower())

    @patch('apps.inventory.services.timezone')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    @patch('apps.inventory.models.EstoqueLoja.objects')
    @patch('apps.inventory.models.UnidadeMedida.objects')
    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    def test_reserva_incrementa_quantidade_reservada(
        self, mock_conv, mock_unidade_qs, mock_estoque_qs, mock_reserva_qs, mock_tz
    ):
        """Creating a reservation increments estoque.quantidade_reservada."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('5')
        mock_unidade_qs.get.return_value = MagicMock()

        estoque = MagicMock()
        estoque.quantidade_atual = Decimal('50')
        estoque.quantidade_reservada = Decimal('10')
        mock_estoque_qs.select_for_update.return_value.get.return_value = estoque

        mock_reserva_qs.create.return_value = MagicMock()
        mock_tz.now.return_value = MagicMock()
        mock_tz.timedelta.return_value = MagicMock()

        usuario = MagicMock()
        with patch('django.db.transaction.atomic'):
            EstoqueService.criar_reserva('p', 1, Decimal('5'), 1, 'sess-3', usuario)

        # quantidade_reservada should have been incremented by 5
        self.assertEqual(estoque.quantidade_reservada, Decimal('15'))
        estoque.save.assert_called_once()


class ReservaConfirmacaoTests(TestCase):
    """Tests for EstoqueService.confirmar_reservas."""

    @patch('apps.inventory.models.EstoqueReserva.objects')
    def test_confirma_reservas_ativas_da_sessao(self, mock_reserva_qs):
        """All ATIVA reservations for the session are set to CONFIRMADA."""
        from apps.inventory.services import EstoqueService

        reserva1 = MagicMock()
        reserva1.status = 'ATIVA'
        reserva2 = MagicMock()
        reserva2.status = 'ATIVA'

        mock_reserva_qs.select_for_update.return_value.filter.return_value = [reserva1, reserva2]

        with patch('django.db.transaction.atomic'):
            resultado = EstoqueService.confirmar_reservas('sess-4', 'venda-42')

        self.assertEqual(len(resultado), 2)
        for r in [reserva1, reserva2]:
            self.assertEqual(r.status, 'CONFIRMADA')
            self.assertEqual(r.venda_id, 'venda-42')
            r.save.assert_called_once()

    @patch('apps.inventory.models.EstoqueReserva.objects')
    def test_sem_reservas_retorna_lista_vazia(self, mock_reserva_qs):
        """Session with no reservations returns empty list."""
        from apps.inventory.services import EstoqueService

        mock_reserva_qs.select_for_update.return_value.filter.return_value = []

        with patch('django.db.transaction.atomic'):
            resultado = EstoqueService.confirmar_reservas('sess-empty', 'venda-0')

        self.assertEqual(resultado, [])


class ReservaCancelamentoTests(TestCase):
    """Tests for EstoqueService.cancelar_reservas."""

    @patch('apps.inventory.models.EstoqueLoja.objects')
    @patch('apps.inventory.models.EstoqueReserva.objects')
    def test_cancela_reservas_e_marca_cancelada(self, mock_reserva_qs, mock_estoque_qs):
        """cancelar_reservas sets each reservation status to CANCELADA."""
        from apps.inventory.models import EstoqueLoja
        from apps.inventory.services import EstoqueService

        reserva = MagicMock()
        reserva.status = 'ATIVA'
        reserva.quantidade_reservada = Decimal('10')
        reserva.produto = MagicMock()

        mock_reserva_qs.select_for_update.return_value.filter.return_value = [reserva]
        # EstoqueLoja not found → DoesNotExist (caught silently by the service)
        mock_estoque_qs.select_for_update.return_value.get.side_effect = EstoqueLoja.DoesNotExist

        with patch('django.db.transaction.atomic'):
            EstoqueService.cancelar_reservas('sess-5')

        self.assertEqual(reserva.status, 'CANCELADA')
        reserva.save.assert_called_once()


class DisponibilidadeComReservaTests(SimpleTestCase):
    """Tests que disponibilidade subtracts reservas correctamente."""

    @patch('apps.inventory.models.EstoqueLoja.objects')
    def test_disponivel_desconta_reservado(self, mock_qs):
        """quantidade_disponivel = quantidade_atual - quantidade_reservada."""
        from apps.inventory.services import EstoqueService

        estoque = MagicMock()
        estoque.quantidade_disponivel = Decimal('80')  # 100 - 20
        mock_qs.get.return_value = estoque

        resultado = EstoqueService.calcular_disponibilidade('p', 1)
        self.assertEqual(resultado, Decimal('80'))

    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    def test_verificar_disponibilidade_exata_retorna_true(self, mock_calc, mock_conv):
        """Exact available quantity → verificar returns True (boundary condition)."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('50')
        mock_calc.return_value = Decimal('50')

        self.assertTrue(EstoqueService.verificar_disponibilidade('p', 1, Decimal('50'), 1))

    @patch('apps.inventory.services.ConversaoService.converter_quantidade')
    @patch('apps.inventory.services.EstoqueService.calcular_disponibilidade')
    def test_verificar_disponibilidade_um_a_mais_retorna_false(self, mock_calc, mock_conv):
        """One unit over available → verificar returns False (boundary condition)."""
        from apps.inventory.services import EstoqueService

        mock_conv.return_value = Decimal('51')
        mock_calc.return_value = Decimal('50')

        self.assertFalse(EstoqueService.verificar_disponibilidade('p', 1, Decimal('51'), 1))
