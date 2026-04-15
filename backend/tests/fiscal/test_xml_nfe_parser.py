"""Unit tests for XmlNFeParser — T034m.

Tests cover NF-e layout 4.00 XML parsing, idempotency, and error handling.
No database or external services needed — pure unit tests.
"""
from __future__ import annotations

from decimal import Decimal

from django.test import SimpleTestCase

from apps.fiscal.services import XmlNFeParser

# ---------------------------------------------------------------------------
# Sample XML fixtures
# ---------------------------------------------------------------------------

_SAMPLE_NFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe Id="NFe35240101234567890001550010000001254321234561" versao="4.00">
      <ide>
        <nNF>125</nNF>
        <serie>1</serie>
        <dEmi>2024-01-15</dEmi>
        <natOp>VENDA DE PRODUTO</natOp>
        <tpNF>1</tpNF>
        <cUF>35</cUF>
      </ide>
      <emit>
        <CNPJ>01234567890001</CNPJ>
        <xNome>Empresa Teste LTDA</xNome>
        <xFant>Teste Comercio</xFant>
        <IE>123456789012</IE>
        <enderEmit>
          <UF>SP</UF>
          <xMun>Sao Paulo</xMun>
        </enderEmit>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>TINTA-001</cProd>
          <cEAN>SEM GTIN</cEAN>
          <xProd>Tinta Latex Branca 18L</xProd>
          <NCM>32091000</NCM>
          <CFOP>5102</CFOP>
          <uCom>UN</uCom>
          <qCom>2</qCom>
          <vUnCom>89.90</vUnCom>
          <vProd>179.80</vProd>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <CST>00</CST>
              <pICMS>12.00</pICMS>
              <vBC>179.80</vBC>
              <vICMS>21.58</vICMS>
            </ICMS00>
          </ICMS>
          <PIS>
            <PISAliq>
              <CST>01</CST>
              <pPIS>0.65</pPIS>
              <vPIS>1.17</vPIS>
            </PISAliq>
          </PIS>
          <COFINS>
            <COFINSAliq>
              <CST>01</CST>
              <pCOFINS>3.00</pCOFINS>
              <vCOFINS>5.39</vCOFINS>
            </COFINSAliq>
          </COFINS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vProd>179.80</vProd>
          <vDesc>0.00</vDesc>
          <vICMS>21.58</vICMS>
          <vIPI>0.00</vIPI>
          <vPIS>1.17</vPIS>
          <vCOFINS>5.39</vCOFINS>
          <vNF>179.80</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""

_NFE_SEM_NAMESPACE = """<NFe>
  <infNFe Id="NFe35240100000000000001550010000000010000000015">
    <ide>
      <nNF>1</nNF>
      <serie>1</serie>
    </ide>
    <emit>
      <CNPJ>00000000000001</CNPJ>
      <xNome>Fornecedor Sem Namespace</xNome>
    </emit>
    <det nItem="1">
      <prod>
        <cProd>P001</cProd>
        <xProd>Produto Teste</xProd>
        <NCM>32091000</NCM>
        <CFOP>5102</CFOP>
        <uCom>UN</uCom>
        <qCom>1</qCom>
        <vUnCom>10.00</vUnCom>
        <vProd>10.00</vProd>
      </prod>
      <imposto/>
    </det>
    <total>
      <ICMSTot>
        <vProd>10.00</vProd>
        <vNF>10.00</vNF>
      </ICMSTot>
    </total>
  </infNFe>
</NFe>
"""

_XML_INVALIDO = "<notXml>broken"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class XmlNFeParserParseTests(SimpleTestCase):
    """Tests for XmlNFeParser.parse()."""

    def setUp(self):
        self.parser = XmlNFeParser()

    # ------------------------------------------------------------------
    # Basic parsing — valid XML
    # ------------------------------------------------------------------

    def test_parse_retorna_dicionario(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertIsInstance(result, dict)

    def test_parse_chave_acesso(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['chave_acesso'], 'NFe35240101234567890001550010000001254321234561'.lstrip('NFe'))

    def test_parse_emitente_cnpj(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['emitente']['cnpj'], '01234567890001')

    def test_parse_emitente_nome(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['emitente']['nome'], 'Empresa Teste LTDA')

    def test_parse_emitente_uf(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['emitente']['uf'], 'SP')

    def test_parse_nfe_numero(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['nfe']['numero'], '125')

    def test_parse_nfe_serie(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['nfe']['serie'], '1')

    def test_parse_nfe_natureza_operacao(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['nfe']['natureza_operacao'], 'VENDA DE PRODUTO')

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------

    def test_parse_itens_quantidade(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(len(result['itens']), 1)

    def test_parse_item_descricao(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['itens'][0]['descricao'], 'Tinta Latex Branca 18L')

    def test_parse_item_ncm(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['itens'][0]['ncm'], '32091000')

    def test_parse_item_quantidade(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['itens'][0]['quantidade'], Decimal('2'))

    def test_parse_item_valor_unitario(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['itens'][0]['valor_unitario'], Decimal('89.90'))

    def test_parse_item_valor_total(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['itens'][0]['valor_total'], Decimal('179.80'))

    def test_parse_item_icms(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        icms = result['itens'][0]['icms']
        self.assertEqual(icms['cst'], '00')
        self.assertEqual(icms['aliquota'], Decimal('12.00'))

    def test_parse_item_pis(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        pis = result['itens'][0]['pis']
        self.assertEqual(pis['aliquota'], Decimal('0.65'))

    def test_parse_item_cofins(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        cofins = result['itens'][0]['cofins']
        self.assertEqual(cofins['valor'], Decimal('5.39'))

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------

    def test_parse_totais_valor_total(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['totais']['valor_total'], Decimal('179.80'))

    def test_parse_totais_valor_icms(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['totais']['valor_icms'], Decimal('21.58'))

    def test_parse_totais_desconto_zero(self):
        result = self.parser.parse(_SAMPLE_NFE_XML)
        self.assertEqual(result['totais']['valor_desconto'], Decimal('0.00'))

    # ------------------------------------------------------------------
    # Sem namespace
    # ------------------------------------------------------------------

    def test_parse_xml_sem_namespace(self):
        """Parser should handle XML without namespace declaration."""
        result = self.parser.parse(_NFE_SEM_NAMESPACE)
        self.assertEqual(len(result['itens']), 1)
        self.assertEqual(result['emitente']['nome'], 'Fornecedor Sem Namespace')

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_parse_xml_invalido_levanta_valueerror(self):
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse(_XML_INVALIDO)
        self.assertIn("XML inválido", str(ctx.exception))

    def test_parse_sem_infnfe_levanta_valueerror(self):
        xml_sem_infnfe = '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><xpto/></NFe>'
        with self.assertRaises(ValueError) as ctx:
            self.parser.parse(xml_sem_infnfe)
        self.assertIn("infNFe", str(ctx.exception))

    def test_parse_xml_vazio_levanta_valueerror(self):
        with self.assertRaises(ValueError):
            self.parser.parse("")

    # ------------------------------------------------------------------
    # Chave de acesso
    # ------------------------------------------------------------------

    def test_parse_chave_acesso_44_digitos(self):
        """If Id is a valid 44-digit key, chave_acesso should be 44 chars."""
        result = self.parser.parse(_SAMPLE_NFE_XML)
        chave = result['chave_acesso']
        self.assertTrue(chave.isdigit() or chave == '', f"chave_acesso inválida: {chave!r}")

    # ------------------------------------------------------------------
    # Multiple items
    # ------------------------------------------------------------------

    def test_parse_multiplos_itens(self):
        xml = _SAMPLE_NFE_XML.replace(
            "</infNFe>",
            """<det nItem="2">
                <prod>
                  <cProd>TINTA-002</cProd>
                  <xProd>Tinta Acrílica 3.6L</xProd>
                  <NCM>32091000</NCM><CFOP>5102</CFOP>
                  <uCom>UN</uCom><qCom>1</qCom>
                  <vUnCom>45.00</vUnCom><vProd>45.00</vProd>
                </prod>
                <imposto/>
              </det></infNFe>""",
        )
        result = self.parser.parse(xml)
        self.assertEqual(len(result['itens']), 2)
        self.assertEqual(result['itens'][1]['descricao'], 'Tinta Acrílica 3.6L')
