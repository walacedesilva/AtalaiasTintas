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


# ---------------------------------------------------------------------------
# NFEService — T012 (skeleton; full implementation in Phase 3)
# ---------------------------------------------------------------------------

class NFEService:
    """Business rules for NF-e emission automation.

    Phase 2 provides the skeleton; full SEFAZ integration is implemented in
    Phase 3 (T041-T046).
    """

    @staticmethod
    def deve_emitir_nfe_automatica(venda) -> bool:
        """Return True if NF-e should be emitted automatically for this sale.

        Rules (from spec clarification):
        - B2B (customer has CNPJ) → True
        - B2C (customer has CPF only) → False
        - No customer data → False
        """
        if not hasattr(venda, 'cliente') or venda.cliente is None:
            return False

        cliente = venda.cliente
        cnpj = getattr(cliente, 'cnpj', None)
        return bool(cnpj and cnpj.strip())

    @staticmethod
    def processar_nfe_venda(venda_id: str, usuario):
        """Trigger NF-e processing for a completed sale.

        In Phase 2, this is a stub that logs the intent and queues an async task.
        Full XML generation and SEFAZ transmission are implemented in Phase 3.
        """
        logger.info(
            "NFE processamento agendado: venda=%s usuario=%s "
            "(implementação completa na Fase 3)",
            venda_id, getattr(usuario, 'username', usuario),
        )


# ---------------------------------------------------------------------------
# SefazClient — T013 (stub; full implementation in Phase 3)
# ---------------------------------------------------------------------------

class SefazClient:
    """Stub SEFAZ client. Full implementation in Phase 3 (T035-T040)."""

    def autorizar_nfe(self, xml_assinado: str) -> dict:
        raise NotImplementedError("SefazClient será implementado na Fase 3")

    def consultar_situacao(self, chave_acesso: str) -> dict:
        raise NotImplementedError("SefazClient será implementado na Fase 3")

    def cancelar_nfe(self, chave_acesso: str, justificativa: str) -> dict:
        raise NotImplementedError("SefazClient será implementado na Fase 3")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today():
    from django.utils import timezone
    return timezone.now().date()
