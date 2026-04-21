"""
Fiscal Service Layer
====================
XmlNFeParser — parse incoming supplier NF-e XML files (T034 / Importador XML NF-e)
NFEService   — business rules for NF-e emission (T012)
SefazClient  — SEFAZ integration stub (T013) — full implementation in Phase 3
"""
from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# XmlNFeParser — Importador XML NF-e do fornecedor
# ---------------------------------------------------------------------------

# NF-e XML namespaces (layout 4.00)
_NFE_NS = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
}

# Regex for 44-digit NF-e access key
_CHAVE_RE = re.compile(r'^\d{44}$')


class XmlNFeParser:
    """Parse a supplier NF-e XML string and return a structured dict.

    Supports layout NF-e 4.00.  Uses ``xml.etree.ElementTree`` from stdlib —
    no external dependencies required.  ``lxml`` is used when available for
    performance and namespace support.

    Usage::

        parser = XmlNFeParser()
        data = parser.parse(xml_string)
        # data contains: 'emitente', 'nfe', 'itens', 'totais'
    """

    def parse(self, xml_content: str) -> dict[str, Any]:
        """Parse the NF-e XML and return a structured dictionary.

        Raises ``ValueError`` on malformed XML or unsupported namespace.
        """
        try:
            root = self._parse_xml(xml_content)
        except Exception as exc:
            raise ValueError(f"XML inválido: {exc}") from exc

        # Handle both <nfeProc> wrapper and bare <NFe>
        nfe_el = root if root.tag.endswith('}NFe') or root.tag == 'NFe' else (
            self._find(root, 'nfe:NFe') or root
        )
        inf_el = self._find(nfe_el, 'nfe:infNFe')
        if inf_el is None:
            raise ValueError("Elemento <infNFe> não encontrado no XML")

        chave = inf_el.get('Id', '').lstrip('NFe')
        return {
            'chave_acesso': chave,
            'emitente': self._parse_emitente(inf_el),
            'nfe': self._parse_identificacao(inf_el),
            'itens': self._parse_itens(inf_el),
            'totais': self._parse_totais(inf_el),
        }

    # ------------------------------------------------------------------
    # Section parsers
    # ------------------------------------------------------------------

    def _parse_identificacao(self, inf_el) -> dict[str, Any]:
        ide = self._find(inf_el, 'nfe:ide')
        if ide is None:
            return {}
        return {
            'numero': self._text(ide, 'nfe:nNF'),
            'serie': self._text(ide, 'nfe:serie'),
            'data_emissao': self._text(ide, 'nfe:dEmi') or self._text(ide, 'nfe:dhEmi', '').split('T')[0],
            'natureza_operacao': self._text(ide, 'nfe:natOp'),
            'tipo_operacao': self._text(ide, 'nfe:tpNF'),  # 0=entrada, 1=saida
            'uf_emitente': self._text(ide, 'nfe:cUF'),
        }

    def _parse_emitente(self, inf_el) -> dict[str, Any]:
        emit = self._find(inf_el, 'nfe:emit')
        if emit is None:
            return {}
        endereco = self._find(emit, 'nfe:enderEmit')
        return {
            'cnpj': self._text(emit, 'nfe:CNPJ'),
            'cpf': self._text(emit, 'nfe:CPF'),
            'nome': self._text(emit, 'nfe:xNome'),
            'nome_fantasia': self._text(emit, 'nfe:xFant'),
            'ie': self._text(emit, 'nfe:IE'),
            'uf': self._text(endereco, 'nfe:UF') if endereco is not None else None,
            'municipio': self._text(endereco, 'nfe:xMun') if endereco is not None else None,
        }

    def _parse_itens(self, inf_el) -> list[dict[str, Any]]:
        itens = []
        for det in self._findall(inf_el, 'nfe:det'):
            prod = self._find(det, 'nfe:prod')
            if prod is None:
                continue

            imposto_el = self._find(det, 'nfe:imposto')
            icms = self._parse_icms(imposto_el)
            ipi = self._parse_ipi(imposto_el)
            pis = self._parse_pis(imposto_el)
            cofins = self._parse_cofins(imposto_el)

            itens.append({
                'numero_item': det.get('nItem', str(len(itens) + 1)),
                'codigo': self._text(prod, 'nfe:cProd'),
                'cean': self._text(prod, 'nfe:cEAN'),
                'descricao': self._text(prod, 'nfe:xProd'),
                'ncm': self._text(prod, 'nfe:NCM'),
                'cfop': self._text(prod, 'nfe:CFOP'),
                'unidade': self._text(prod, 'nfe:uCom'),
                'quantidade': self._decimal(prod, 'nfe:qCom'),
                'valor_unitario': self._decimal(prod, 'nfe:vUnCom'),
                'valor_total': self._decimal(prod, 'nfe:vProd'),
                'desconto': self._decimal(prod, 'nfe:vDesc'),
                'icms': icms,
                'ipi': ipi,
                'pis': pis,
                'cofins': cofins,
            })
        return itens

    def _parse_totais(self, inf_el) -> dict[str, Any]:
        total_el = self._find(inf_el, 'nfe:total')
        if total_el is None:
            return {}
        ice = self._find(total_el, 'nfe:ICMSTot')
        if ice is None:
            return {}
        return {
            'valor_produtos': self._decimal(ice, 'nfe:vProd'),
            'valor_total': self._decimal(ice, 'nfe:vNF'),
            'valor_desconto': self._decimal(ice, 'nfe:vDesc'),
            'valor_icms': self._decimal(ice, 'nfe:vICMS'),
            'valor_ipi': self._decimal(ice, 'nfe:vIPI'),
            'valor_pis': self._decimal(ice, 'nfe:vPIS'),
            'valor_cofins': self._decimal(ice, 'nfe:vCOFINS'),
        }

    # ------------------------------------------------------------------
    # Tax helpers
    # ------------------------------------------------------------------

    def _parse_icms(self, imposto_el) -> dict[str, Any]:
        if imposto_el is None:
            return {}
        icms_el = self._find(imposto_el, 'nfe:ICMS')
        if icms_el is None:
            return {}
        # Try common sub-elements (ICMS00, ICMS10, ICMS20, ..., CSOSN)
        for child in list(icms_el):
            return {
                'cst': self._text(child, 'nfe:CST') or self._text(child, 'nfe:CSOSN'),
                'aliquota': self._decimal(child, 'nfe:pICMS'),
                'base_calculo': self._decimal(child, 'nfe:vBC'),
                'valor': self._decimal(child, 'nfe:vICMS'),
            }
        return {}

    def _parse_ipi(self, imposto_el) -> dict[str, Any]:
        if imposto_el is None:
            return {}
        ipi_el = self._find(imposto_el, 'nfe:IPI')
        if ipi_el is None:
            return {}
        ipi_trib = self._find(ipi_el, 'nfe:IPITrib') or self._find(ipi_el, 'nfe:IPINT')
        if ipi_trib is None:
            return {}
        return {
            'cst': self._text(ipi_trib, 'nfe:CST'),
            'aliquota': self._decimal(ipi_trib, 'nfe:pIPI'),
            'valor': self._decimal(ipi_trib, 'nfe:vIPI'),
        }

    def _parse_pis(self, imposto_el) -> dict[str, Any]:
        if imposto_el is None:
            return {}
        pis_el = self._find(imposto_el, 'nfe:PIS')
        if pis_el is None:
            return {}
        for child in list(pis_el):
            return {
                'cst': self._text(child, 'nfe:CST'),
                'aliquota': self._decimal(child, 'nfe:pPIS'),
                'valor': self._decimal(child, 'nfe:vPIS'),
            }
        return {}

    def _parse_cofins(self, imposto_el) -> dict[str, Any]:
        if imposto_el is None:
            return {}
        cofins_el = self._find(imposto_el, 'nfe:COFINS')
        if cofins_el is None:
            return {}
        for child in list(cofins_el):
            return {
                'cst': self._text(child, 'nfe:CST'),
                'aliquota': self._decimal(child, 'nfe:pCOFINS'),
                'valor': self._decimal(child, 'nfe:vCOFINS'),
            }
        return {}

    # ------------------------------------------------------------------
    # XML helpers
    # ------------------------------------------------------------------

    def _parse_xml(self, content: str):
        try:
            import lxml.etree as ET
            return ET.fromstring(content.encode() if isinstance(content, str) else content)
        except ImportError:
            import xml.etree.ElementTree as ET
            return ET.fromstring(content)

    def _find(self, el, tag: str):
        if el is None:
            return None
        result = el.find(tag, _NFE_NS)
        if result is None:
            # Try without namespace prefix (files without namespace declaration)
            local = tag.split(':')[-1]
            result = el.find(f'.//{local}')
        return result

    def _findall(self, el, tag: str):
        if el is None:
            return []
        results = el.findall(tag, _NFE_NS)
        if not results:
            local = tag.split(':')[-1]
            results = el.findall(f'.//{local}')
        return results

    def _text(self, el, tag: str, default: str = '') -> str:
        found = self._find(el, tag)
        return (found.text or default).strip() if found is not None else default

    def _decimal(self, el, tag: str) -> Decimal:
        raw = self._text(el, tag, '0')
        try:
            return Decimal(raw.replace(',', '.'))
        except InvalidOperation:
            return Decimal('0')


# ---------------------------------------------------------------------------
# EntradaMercadoriaService — create/confirm entries from parsed XML (T034)
# ---------------------------------------------------------------------------

class EntradaMercadoriaService:
    """Workflow for importing supplier NF-e XMLs and updating stock."""

    @staticmethod
    def importar_xml(xml_content: str, loja_id: int, usuario) -> 'apps.inventory.models.EntradaMercadoria':
        """Parse an NF-e XML and create an EntradaMercadoria record (RASCUNHO).

        Items are imported with status=PENDENTE until the operator links each
        item to an existing ProdutoVariacao.

        Returns the created EntradaMercadoria.
        """
        from apps.inventory.models import EntradaMercadoria, EntradaMercadoriaItem

        parser = XmlNFeParser()
        data = parser.parse(xml_content)

        emitente = data.get('emitente', {})
        nfe_info = data.get('nfe', {})
        totais = data.get('totais', {})
        chave = data.get('chave_acesso', '')

        # Validate chave
        if chave and not _CHAVE_RE.match(chave):
            logger.warning("Chave de acesso inválida: %s", chave)
            chave = None

        # Idempotency: do not import the same NF-e twice
        if chave:
            existing = EntradaMercadoria.objects.filter(chave_acesso_nfe=chave).first()
            if existing:
                logger.info("NF-e já importada: chave=%s", chave)
                return existing

        from django.db import transaction
        with transaction.atomic():
            entrada = EntradaMercadoria.objects.create(
                loja_id=loja_id,
                usuario=usuario,
                tipo_entrada='COMPRA',
                fornecedor_cnpj=emitente.get('cnpj') or emitente.get('cpf'),
                fornecedor_nome=emitente.get('nome'),
                fornecedor_uf=emitente.get('uf'),
                chave_acesso_nfe=chave or None,
                numero_nfe=nfe_info.get('numero'),
                serie_nfe=nfe_info.get('serie'),
                data_emissao_nfe=nfe_info.get('data_emissao') or None,
                xml_nfe=xml_content,
                data_entrada=_today(),
                valor_total_nfe=totais.get('valor_total', Decimal('0')),
                status='PENDENTE',
            )

            for item_data in data.get('itens', []):
                EntradaMercadoriaItem.objects.create(
                    entrada=entrada,
                    descricao_nfe=item_data.get('descricao', ''),
                    codigo_nfe=item_data.get('codigo'),
                    ncm=item_data.get('ncm'),
                    cfop=item_data.get('cfop'),
                    cean=item_data.get('cean'),
                    quantidade=item_data.get('quantidade', Decimal('0')),
                    unidade_nfe=item_data.get('unidade'),
                    valor_unitario=item_data.get('valor_unitario', Decimal('0')),
                    valor_total=item_data.get('valor_total', Decimal('0')),
                    desconto=item_data.get('desconto', Decimal('0')),
                    valor_icms=item_data.get('icms', {}).get('valor', Decimal('0')),
                    valor_ipi=item_data.get('ipi', {}).get('valor', Decimal('0')),
                    valor_pis=item_data.get('pis', {}).get('valor', Decimal('0')),
                    valor_cofins=item_data.get('cofins', {}).get('valor', Decimal('0')),
                    status='PENDENTE',
                )

        logger.info(
            "NF-e importada: chave=%s fornecedor=%s itens=%d",
            chave, emitente.get('nome'), len(data.get('itens', [])),
        )
        return entrada

    @staticmethod
    def confirmar_entrada(entrada_id: str, usuario) -> 'apps.inventory.models.EntradaMercadoria':
        """Process all VINCULADO items: update their stock via EstoqueService.

        Items without a linked ProdutoVariacao are skipped (logged as warning).
        Returns the updated EntradaMercadoria.
        """
        from apps.inventory.models import EntradaMercadoria, EntradaMercadoriaItem
        from apps.inventory.services import EstoqueService
        from django.db import transaction
        from django.utils import timezone as tz

        with transaction.atomic():
            entrada = EntradaMercadoria.objects.select_for_update().get(pk=entrada_id)
            if entrada.status not in ('PENDENTE', 'RASCUNHO'):
                raise ValueError(f"Entrada já processada: status={entrada.status}")

            itens = EntradaMercadoriaItem.objects.filter(entrada=entrada, status='VINCULADO')
            if not itens.exists():
                raise ValueError("Nenhum item vinculado a produto. Vincule os itens antes de confirmar.")

            valor_total = Decimal('0')
            for item in itens:
                if not item.produto_id:
                    logger.warning("Item sem produto vinculado, ignorado: %s", item.pk)
                    item.status = 'IGNORADO'
                    item.save(update_fields=['status'])
                    continue

                unidade_id = item.unidade_id  # may be None
                if unidade_id is None:
                    # Use product's stock unit
                    unidade_id = item.produto.unidade_estoque_id

                mov, lote = EstoqueService.processar_entrada(
                    produto_variacao_id=str(item.produto_id),
                    loja_id=entrada.loja_id,
                    quantidade=item.quantidade,
                    unidade_id=unidade_id,
                    usuario=usuario,
                    tipo_movimentacao='ENTRADA_COMPRA',
                    documento_referencia=entrada.chave_acesso_nfe or str(entrada.pk),
                )
                item.status = 'PROCESSADO'
                item.save(update_fields=['status', 'lote'])
                valor_total += item.valor_total

            entrada.status = 'CONFIRMADA'
            entrada.valor_total_entrada = valor_total
            entrada.data_conferencia = tz.now()
            entrada.save(update_fields=['status', 'valor_total_entrada', 'data_conferencia', 'updated_at'])

        logger.info("Entrada confirmada: id=%s", entrada_id)
        return entrada

    @staticmethod
    def criar_manual(
        loja_id: int,
        usuario,
        numero_nfe: str,
        serie_nfe: str,
        fornecedor_cnpj: str,
        data_emissao_nfe,
        itens: list[dict],
        fornecedor_nome: str | None = None,
        fornecedor_uf: str | None = None,
        valor_total_nfe: 'Decimal | None' = None,
        chave_acesso_nfe: str | None = None,
        observacoes: str = '',
    ) -> 'apps.inventory.models.EntradaMercadoria':
        """Create an EntradaMercadoria from manual form data (no XML required).

        Validates CNPJ/CPF and enforces idempotency by chave_acesso_nfe when
        provided.  At least one item is required.

        Raises ``ValueError`` with a human-readable message on invalid input.
        """
        from apps.inventory.models import EntradaMercadoria, EntradaMercadoriaItem
        from django.db import transaction

        # -- Input validation -------------------------------------------------
        if not itens:
            raise ValueError("É necessário informar pelo menos um item.")

        cnpj_limpo = re.sub(r'\D', '', fornecedor_cnpj or '')
        if not _validar_cnpj_cpf(cnpj_limpo):
            raise ValueError(f"CNPJ/CPF inválido: {fornecedor_cnpj!r}")

        if chave_acesso_nfe:
            if not _CHAVE_RE.match(chave_acesso_nfe):
                raise ValueError("Chave de acesso deve ter exatamente 44 dígitos numéricos.")
            existing = EntradaMercadoria.objects.filter(chave_acesso_nfe=chave_acesso_nfe).first()
            if existing:
                logger.info("Entrada já existe para chave=%s", chave_acesso_nfe)
                return existing

        # -- Creation ---------------------------------------------------------
        with transaction.atomic():
            entrada = EntradaMercadoria.objects.create(
                loja_id=loja_id,
                usuario=usuario,
                tipo_entrada='COMPRA',
                fornecedor_cnpj=cnpj_limpo,
                fornecedor_nome=fornecedor_nome,
                fornecedor_uf=fornecedor_uf,
                chave_acesso_nfe=chave_acesso_nfe or None,
                numero_nfe=numero_nfe,
                serie_nfe=serie_nfe,
                data_emissao_nfe=data_emissao_nfe or None,
                data_entrada=_today(),
                valor_total_nfe=valor_total_nfe or Decimal('0'),
                status='PENDENTE',
                origem_entrada='MANUAL',
                observacoes=observacoes,
            )

            for item_data in itens:
                quantidade = Decimal(str(item_data.get('quantidade', 0)))
                valor_unitario = Decimal(str(item_data.get('valor_unitario', 0)))
                EntradaMercadoriaItem.objects.create(
                    entrada=entrada,
                    descricao_nfe=item_data.get('descricao_nfe', ''),
                    codigo_nfe=item_data.get('codigo_nfe') or None,
                    ncm=item_data.get('ncm') or None,
                    cfop=item_data.get('cfop') or None,
                    quantidade=quantidade,
                    unidade_nfe=item_data.get('unidade_nfe') or None,
                    valor_unitario=valor_unitario,
                    valor_total=(quantidade * valor_unitario).quantize(Decimal('0.01')),
                    status='PENDENTE',
                )

        logger.info(
            "Entrada manual criada: id=%s fornecedor=%s itens=%d",
            entrada.pk, fornecedor_nome or cnpj_limpo, len(itens),
        )
        return entrada


# ---------------------------------------------------------------------------
# NFEService — T012 skeleton + T041-T044 full implementation
# ---------------------------------------------------------------------------

class NFEService:
    """Business rules and orchestration for NF-e emission automation.

    T041 — deve_emitir_nfe_automatica
    T042 — processar_nfe_venda
    T043 — gerar_xml_nfe
    T044 — enviar_sefaz
    """

    # Max automatic retry attempts before flagging for manual review
    MAX_TENTATIVAS_AUTO: int = 3

    # ------------------------------------------------------------------
    # T041 — Business rule: should NF-e be emitted automatically?
    # ------------------------------------------------------------------

    @staticmethod
    def deve_emitir_nfe_automatica(venda) -> bool:
        """Return True if NF-e should be emitted automatically for this sale.

        Rules (from spec clarification):
        - B2B (customer has CNPJ) → True (automatic)
        - B2C (customer has CPF only) → False (manual, optional)
        - No customer data → False
        """
        if not hasattr(venda, 'cliente') or venda.cliente is None:
            return False
        cnpj = getattr(venda.cliente, 'cnpj', None)
        return bool(cnpj and cnpj.strip())

    # ------------------------------------------------------------------
    # T042 — Orchestrate NF-e processing for a completed sale
    # ------------------------------------------------------------------

    @staticmethod
    def processar_nfe_venda(venda_id: str, usuario) -> None:
        """Trigger NF-e processing for a completed sale.

        Creates / updates the NotaFiscal record and queues the async Celery
        task ``processar_nfe_async``.  Idempotent: calling again while a task
        is already running has no effect.
        """
        from apps.fiscal.models import NotaFiscal, ConfiguracaoFiscal
        from apps.sales.models import Venda
        from django.db import transaction

        try:
            venda = Venda.objects.select_related('cliente', 'loja', 'loja__empresa').get(pk=venda_id)
        except Venda.DoesNotExist:
            logger.error("processar_nfe_venda: Venda %s não encontrada", venda_id)
            return

        if not NFEService.deve_emitir_nfe_automatica(venda):
            logger.info("Venda %s não requer NF-e automática (B2C ou sem cliente)", venda_id)
            _update_venda_nfe(venda, situacao='NAO_APLICAVEL', tipo_emissao='NAO_EMITIR')
            return

        # Mark as pending before queuing
        _update_venda_nfe(venda, situacao='PENDENTE', tipo_emissao='AUTOMATICA_B2B')

        # Queue async processing (avoids blocking the HTTP response)
        try:
            from apps.fiscal.tasks import processar_nfe_async
            processar_nfe_async.delay(str(venda_id), getattr(usuario, 'pk', None))
            logger.info("NF-e agendada para venda %s (usuário=%s)", venda_id, getattr(usuario, 'username', usuario))
        except Exception as exc:
            logger.error("Falha ao agendar NF-e para venda %s: %s", venda_id, exc)

    # ------------------------------------------------------------------
    # T043 — Generate NF-e XML from Venda data
    # ------------------------------------------------------------------

    @staticmethod
    def gerar_xml_nfe(venda_id: str) -> str:
        """Build a NF-e 4.00 XML string from the given Venda.

        The XML is NOT signed here — signing requires the A1 certificate and
        is done inside ``enviar_sefaz``.

        Returns the unsigned XML string (``<NFe>...</NFe>``).
        Raises ``ValueError`` if required data is missing.
        """
        from apps.sales.models import Venda, ItemPedidoVenda
        from apps.fiscal.models import ConfiguracaoFiscal
        from apps.fiscal.sefaz.validators import validar_dados_nfe, SefazSchemaError

        venda = (
            Venda.objects
            .select_related('cliente', 'loja', 'loja__empresa', 'pedido_origem')
            .get(pk=venda_id)
        )

        itens_pedido = ItemPedidoVenda.objects.filter(
            pedido=venda.pedido_origem
        ).select_related('produto_variacao', 'produto_variacao__produto')

        if not itens_pedido.exists():
            raise ValueError(f"Venda {venda_id} não possui itens")

        config = ConfiguracaoFiscal.objects.filter(
            empresa=venda.loja.empresa, nfe_ativo=True
        ).first()
        if config is None:
            raise ValueError(
                f"ConfiguracaoFiscal não encontrada para empresa {venda.loja.empresa_id}"
            )

        xml = _NFeXmlBuilder(venda, itens_pedido, config).build()

        # Pre-flight validation
        from apps.fiscal.sefaz.validators import validar_dados_nfe
        erros = validar_dados_nfe(_extract_nfe_data_for_validation(venda, itens_pedido))
        if erros:
            raise ValueError("Dados NF-e inválidos: " + "; ".join(erros))

        return xml

    # ------------------------------------------------------------------
    # T044 — Submit signed XML to SEFAZ and update record
    # ------------------------------------------------------------------

    @staticmethod
    def enviar_sefaz(nota_fiscal_id: str) -> dict:
        """Send a NotaFiscal to SEFAZ and update its record.

        Returns the SEFAZ response dict from ``SefazClient.autorizar_nfe``.
        On ``SefazRejeicaoError`` or other errors the NotaFiscal is updated
        accordingly and the exception is re-raised for the caller to handle.
        """
        from apps.fiscal.models import NotaFiscal, LogEventosFiscais
        from apps.fiscal.sefaz.client import criar_sefaz_client
        from apps.fiscal.sefaz.exceptions import SefazError, SefazRejeicaoError
        from django.db import transaction
        from django.utils import timezone as tz

        with transaction.atomic():
            nota = NotaFiscal.objects.select_for_update().get(pk=nota_fiscal_id)
            nota.situacao = 'ENVIADA'
            nota.data_envio = tz.now()
            nota.save(update_fields=['situacao', 'data_envio', 'updated_at'])

        client = criar_sefaz_client()

        try:
            resultado = client.autorizar_nfe(nota.xml_envio or "")
        except SefazError as exc:
            with transaction.atomic():
                nota = NotaFiscal.objects.select_for_update().get(pk=nota_fiscal_id)
                nota.situacao = 'REJEITADA' if isinstance(exc, SefazRejeicaoError) else 'RASCUNHO'
                nota.save(update_fields=['situacao', 'updated_at'])
                LogEventosFiscais.objects.create(
                    nota_fiscal=nota,
                    tipo_evento='ERRO_TRANSMISSAO',
                    descricao=str(exc),
                    codigo_retorno=getattr(exc, 'codigo', ''),
                    mensagem_retorno=getattr(exc, 'motivo', str(exc)),
                    xml_envio=nota.xml_envio,
                )
            raise

        with transaction.atomic():
            nota = NotaFiscal.objects.select_for_update().get(pk=nota_fiscal_id)
            nota.situacao = resultado.get('status', 'AUTORIZADA')
            nota.protocolo_autorizacao = resultado.get('numero_protocolo', '')
            nota.chave_acesso = resultado.get('chave_acesso') or nota.chave_acesso
            nota.data_autorizacao = tz.now() if resultado.get('status') == 'AUTORIZADA' else None
            nota.xml_retorno = resultado.get('xml_retorno', '')
            nota.save(update_fields=[
                'situacao', 'protocolo_autorizacao', 'chave_acesso',
                'data_autorizacao', 'xml_retorno', 'updated_at',
            ])
            LogEventosFiscais.objects.create(
                nota_fiscal=nota,
                tipo_evento='EMISSAO',
                descricao=f"Autorização SEFAZ: {resultado.get('motivo_status')}",
                codigo_retorno=resultado.get('codigo_status', ''),
                mensagem_retorno=resultado.get('motivo_status', ''),
                xml_envio=nota.xml_envio,
                xml_retorno=resultado.get('xml_retorno', ''),
            )

            # Propagate protocol to Venda
            if nota.situacao == 'AUTORIZADA' and nota.venda_id:
                nota.venda.__class__.objects.filter(pk=nota.venda_id).update(
                    nfe_situacao='AUTORIZADA',
                    nfe_protocolo=nota.protocolo_autorizacao,
                    nfe_chave_acesso=nota.chave_acesso,
                    nfe_erro=None,
                )

        return resultado

    # ------------------------------------------------------------------
    # Helper — retry manual
    # ------------------------------------------------------------------

    @staticmethod
    def marcar_para_retry_manual(venda_id: str, motivo: str = "") -> None:
        """Flag a sale's NF-e as requiring manual retry."""
        from apps.sales.models import Venda
        Venda.objects.filter(pk=venda_id).update(
            nfe_situacao='AGUARDANDO_RETRY',
            nfe_requer_retry_manual=True,
            nfe_erro=motivo or "Máximo de tentativas automáticas atingido",
        )


# ---------------------------------------------------------------------------
# SefazClient — kept as thin facade for backwards compat (full impl in sefaz/)
# ---------------------------------------------------------------------------

class SefazClient:
    """Thin facade re-exporting the full client from ``apps.fiscal.sefaz``."""

    def __init__(self):
        from apps.fiscal.sefaz.client import criar_sefaz_client
        self._client = criar_sefaz_client()

    def autorizar_nfe(self, xml_assinado: str) -> dict:
        return self._client.autorizar_nfe(xml_assinado)

    def consultar_situacao(self, chave_acesso: str) -> dict:
        return self._client.consultar_situacao(chave_acesso)

    def cancelar_nfe(self, chave_acesso: str, justificativa: str, numero_protocolo: str = "") -> dict:
        return self._client.cancelar_nfe(chave_acesso, justificativa, numero_protocolo)


# ---------------------------------------------------------------------------
# _NFeXmlBuilder — T043 internal helper (T045 — XML generation)
# ---------------------------------------------------------------------------

class _NFeXmlBuilder:
    """Builds an unsigned NF-e 4.00 XML from sale data."""

    _NFE_NS = 'http://www.portalfiscal.inf.br/nfe'

    def __init__(self, venda, itens, config):
        self._venda = venda
        self._itens = list(itens)
        self._config = config

    def build(self) -> str:
        from decouple import config as env
        from django.utils import timezone as tz

        venda = self._venda
        cliente = venda.cliente
        empresa = venda.loja.empresa
        loja = venda.loja
        now = tz.now()

        # Derive sequential NF-e number — increment stored counter
        self._config.nfe_numero_atual += 1
        self._config.save(update_fields=['nfe_numero_atual'])
        num_nfe = str(self._config.nfe_numero_atual).zfill(9)
        serie = str(self._config.nfe_serie).zfill(3)
        tp_amb = "1" if self._config.nfe_ambiente == 'PRODUCAO' else "2"
        cnpj_emit = re.sub(r'\D', '', empresa.cnpj or '')
        uf_ibge = env('NFE_UF_IBGE', default='35')

        # Content
        itens_xml = "".join(self._item_xml(i + 1, item) for i, item in enumerate(self._itens))
        valor_total = sum(
            (item.preco_total or Decimal('0')) for item in self._itens
        )
        valor_desconto = Decimal(str(venda.valor_desconto or '0'))
        valor_liquido = valor_total - valor_desconto

        dest_xml = self._dest_xml(cliente)
        dhEmis = now.strftime('%Y-%m-%dT%H:%M:%S') + '-03:00'

        xml = (
            f'<NFe xmlns="{self._NFE_NS}">'
            f'<infNFe versao="4.00" Id="NFe{cnpj_emit}000000000000000000000000000000000000000000">'
            # Identificação
            "<ide>"
            f"<cUF>{uf_ibge}</cUF>"
            f"<cNF>00000001</cNF>"
            "<natOp>VENDA DE PRODUTO</natOp>"
            "<mod>55</mod>"
            f"<serie>{self._config.nfe_serie}</serie>"
            f"<nNF>{num_nfe}</nNF>"
            f"<dhEmi>{dhEmis}</dhEmi>"
            "<tpNF>1</tpNF>"
            "<idDest>1</idDest>"
            f"<cMunFG>{loja.codigo_municipio_ibge or '0000000'}</cMunFG>"
            "<tpImp>1</tpImp>"
            f"<tpEmis>1</tpEmis>"
            "<cDV>0</cDV>"
            f"<tpAmb>{tp_amb}</tpAmb>"
            "<finNFe>1</finNFe>"
            "<indFinal>1</indFinal>"
            "<indPres>1</indPres>"
            "<procEmi>0</procEmi>"
            "<verProc>1.0</verProc>"
            "</ide>"
            # Emitente
            f"<emit>"
            f"<CNPJ>{cnpj_emit}</CNPJ>"
            f"<xNome>{_esc(empresa.razao_social)}</xNome>"
            f"<xFant>{_esc(empresa.nome_fantasia or empresa.razao_social)}</xFant>"
            "<enderEmit>"
            f"<xLgr>{_esc(empresa.endereco or '')}</xLgr>"
            f"<nro>{_esc(empresa.numero or 'SN')}</nro>"
            f"<xBairro>{_esc(empresa.bairro or '')}</xBairro>"
            f"<cMun>0000000</cMun>"
            f"<xMun>{_esc(empresa.cidade or '')}</xMun>"
            f"<UF>{empresa.uf or 'SP'}</UF>"
            f"<CEP>{re.sub(chr(92) + 'D', '', empresa.cep or '00000000')}</CEP>"
            "<cPais>1058</cPais>"
            "<xPais>Brasil</xPais>"
            "</enderEmit>"
            f"<IE>{re.sub(chr(92) + 'D', '', empresa.inscricao_estadual or 'ISENTO')}</IE>"
            "<CRT>1</CRT>"
            "</emit>"
            # Destinatário
            + dest_xml
            # Itens
            + itens_xml
            # Totais
            + f"<total><ICMSTot>"
            f"<vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson>"
            f"<vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST>"
            f"<vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet>"
            f"<vProd>{valor_total:.2f}</vProd>"
            "<vFrete>0.00</vFrete><vSeg>0.00</vSeg>"
            f"<vDesc>{valor_desconto:.2f}</vDesc>"
            "<vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol>"
            "<vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS>"
            "<vOutro>0.00</vOutro>"
            f"<vNF>{valor_liquido:.2f}</vNF>"
            "</ICMSTot></total>"
            # Transporte
            "<transp><modFrete>9</modFrete></transp>"
            # Pagamento
            + self._pag_xml(valor_liquido)
            + "</infNFe></NFe>"
        )
        return xml

    def _dest_xml(self, cliente) -> str:
        if cliente is None:
            return "<dest><CPF>00000000000</CPF><xNome>CONSUMIDOR</xNome><indIEDest>9</indIEDest></dest>"

        doc_tag = ""
        if cliente.cnpj:
            cnpj = re.sub(r'\D', '', cliente.cnpj)
            doc_tag = f"<CNPJ>{cnpj}</CNPJ>"
        elif cliente.cpf:
            cpf = re.sub(r'\D', '', cliente.cpf)
            doc_tag = f"<CPF>{cpf}</CPF>"

        nome = _esc(cliente.razao_social or cliente.nome or 'CONSUMIDOR')
        return (
            f"<dest>{doc_tag}"
            f"<xNome>{nome}</xNome>"
            "<indIEDest>9</indIEDest>"
            "</dest>"
        )

    def _item_xml(self, seq: int, item) -> str:
        pv = item.produto_variacao
        produto = pv.produto if hasattr(pv, 'produto') else pv
        ncm = re.sub(r'\D', '', getattr(produto, 'ncm', '') or '00000000').ljust(8, '0')[:8]
        cfop = '5102'  # default: sale within state
        descricao = _esc(getattr(produto, 'nome', str(produto)))
        unidade = 'UN'
        qtde = item.quantidade or Decimal('1')
        vunit = item.preco_unitario or Decimal('0')
        vtotal = item.preco_total or (qtde * vunit)

        return (
            f"<det nItem=\"{seq}\">"
            "<prod>"
            f"<cProd>{_esc(str(getattr(pv, 'codigo', seq)))}</cProd>"
            "<cEAN>SEM GTIN</cEAN>"
            f"<xProd>{descricao}</xProd>"
            f"<NCM>{ncm}</NCM>"
            f"<CFOP>{cfop}</CFOP>"
            f"<uCom>{unidade}</uCom>"
            f"<qCom>{qtde:.4f}</qCom>"
            f"<vUnCom>{vunit:.10f}</vUnCom>"
            f"<vProd>{vtotal:.2f}</vProd>"
            "<cEANTrib>SEM GTIN</cEANTrib>"
            f"<uTrib>{unidade}</uTrib>"
            f"<qTrib>{qtde:.4f}</qTrib>"
            f"<vUnTrib>{vunit:.10f}</vUnTrib>"
            "<indTot>1</indTot>"
            "</prod>"
            "<imposto>"
            "<ICMS><ICMS40><orig>0</orig><CST>40</CST></ICMS40></ICMS>"
            "<PIS><PISAliq><CST>01</CST><vBC>0.00</vBC><pPIS>0.00</pPIS><vPIS>0.00</vPIS></PISAliq></PIS>"
            "<COFINS><COFINSAliq><CST>01</CST><vBC>0.00</vBC><pCOFINS>0.00</pCOFINS><vCOFINS>0.00</vCOFINS></COFINSAliq></COFINS>"
            "</imposto>"
            "</det>"
        )

    def _pag_xml(self, valor: Decimal) -> str:
        return (
            "<pag>"
            "<detPag>"
            "<tPag>01</tPag>"
            f"<vPag>{valor:.2f}</vPag>"
            "</detPag>"
            "</pag>"
        )


def _update_venda_nfe(venda, situacao: str, tipo_emissao: str | None = None, erro: str | None = None) -> None:
    """Update NF-e fields on a Venda instance atomically."""
    from apps.sales.models import Venda
    update = {'nfe_situacao': situacao}
    if tipo_emissao is not None:
        update['nfe_tipo_emissao'] = tipo_emissao
    if erro is not None:
        update['nfe_erro'] = erro
    Venda.objects.filter(pk=venda.pk).update(**update)


def _extract_nfe_data_for_validation(venda, itens) -> dict:
    """Build the minimal dict expected by ``validar_dados_nfe``."""
    empresa = venda.loja.empresa
    cliente = venda.cliente
    return {
        'emitente': {
            'cnpj': getattr(empresa, 'cnpj', ''),
            'nome': getattr(empresa, 'razao_social', ''),
            'uf': getattr(empresa, 'uf', ''),
        },
        'destinatario': {
            'cnpj': getattr(cliente, 'cnpj', None),
            'cpf': getattr(cliente, 'cpf', None),
        } if cliente else {},
        'itens': [
            {
                'descricao': getattr(
                    getattr(i.produto_variacao, 'produto', i.produto_variacao),
                    'nome', str(i.produto_variacao)
                ),
                'ncm': getattr(
                    getattr(i.produto_variacao, 'produto', i.produto_variacao),
                    'ncm', '00000000'
                ) or '00000000',
                'cfop': '5102',
                'quantidade': i.quantidade,
                'valor_unitario': i.preco_unitario,
            }
            for i in itens
        ],
        'totais': {'valor_total': str(venda.valor_total or '0')},
    }


def _esc(text: str) -> str:
    """Escape XML special characters."""
    return (
        str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&apos;')
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today():
    from django.utils import timezone
    return timezone.now().date()


def _validar_cnpj_cpf(digitos: str) -> bool:
    """Validate CNPJ (14 digits) or CPF (11 digits) using the modulo-11 algorithm.

    Accepts only digit strings (no formatting characters).
    Returns False for all-same-digit sequences (e.g. 00000000000000).
    """
    if len(digitos) == 11:
        return _validar_cpf(digitos)
    if len(digitos) == 14:
        return _validar_cnpj(digitos)
    return False


def _validar_cpf(cpf: str) -> bool:
    if len(set(cpf)) == 1:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10 % 11) % 10
    if d1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10 % 11) % 10
    return d2 == int(cpf[10])


def _validar_cnpj(cnpj: str) -> bool:
    if len(set(cnpj)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    d1 = 11 - (soma % 11)
    d1 = 0 if d1 >= 10 else d1
    if d1 != int(cnpj[12]):
        return False
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    d2 = 11 - (soma % 11)
    d2 = 0 if d2 >= 10 else d2
    return d2 == int(cnpj[13])
