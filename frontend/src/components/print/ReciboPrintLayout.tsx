import './print.css';
import type { Loja, Venda, FormaPagamento } from '@/types';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCNPJ(cnpj: string): string {
  const d = cnpj.replace(/\D/g, '');
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDatetime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

const FORMA_LABELS: Record<FormaPagamento, string> = {
  DINHEIRO: 'Dinheiro',
  PIX: 'PIX',
  CARTAO_CREDITO: 'Cartão de Crédito',
  CARTAO_DEBITO: 'Cartão de Débito',
  CREDIARIO: 'Crediário',
  TRANSFERENCIA: 'Transferência',
};

// ─── Component ───────────────────────────────────────────────────────────────

interface Props {
  venda: Venda;
  loja: Loja;
}

export function ReciboPrintLayout({ venda, loja }: Props) {
  const empresa = loja.empresa_data;
  const nomeEmpresa = empresa?.nome_fantasia || empresa?.razao_social || loja.nome;
  const cnpjFormatado = empresa ? formatCNPJ(empresa.cnpj) : '';

  const enderecoLoja = [
    loja.endereco,
    loja.numero,
    loja.bairro,
    loja.cidade && loja.uf ? `${loja.cidade}/${loja.uf}` : (loja.cidade || loja.uf),
  ]
    .filter(Boolean)
    .join(', ');

  const pagamentos = venda.pagamentos ?? [];
  const pedidoItens = venda.pedido_itens ?? [];

  const totalPago = pagamentos.reduce(
    (sum, p) => sum + parseFloat(p.valor),
    0,
  );

  return (
    <div
      id="recibo-print"
      className="print-root"
      style={{ fontFamily: 'Arial, sans-serif', fontSize: '12px', color: '#111', padding: '8px' }}
    >
      {/* ── Cabeçalho ── */}
      <table style={{ width: '100%', marginBottom: '8px', borderCollapse: 'collapse' }}>
        <tbody>
          <tr>
            <td style={{ verticalAlign: 'top', width: '70%' }}>
              <div style={{ fontWeight: 700, fontSize: '15px' }}>{nomeEmpresa}</div>
              {empresa?.razao_social && empresa.razao_social !== nomeEmpresa && (
                <div style={{ fontSize: '11px', color: '#555' }}>{empresa.razao_social}</div>
              )}
              {cnpjFormatado && (
                <div style={{ fontSize: '11px' }}>CNPJ: {cnpjFormatado}</div>
              )}
              {enderecoLoja && <div style={{ fontSize: '11px' }}>{enderecoLoja}</div>}
              {loja.telefone && <div style={{ fontSize: '11px' }}>Tel: {loja.telefone}</div>}
            </td>
            <td style={{ verticalAlign: 'top', textAlign: 'right', width: '30%' }}>
              <div style={{ fontWeight: 700, fontSize: '16px', textTransform: 'uppercase' }}>
                Recibo de Venda
              </div>
              <div style={{ fontSize: '13px' }}>Nº {venda.numero_venda}</div>
              <div style={{ fontSize: '11px' }}>
                {formatDatetime(venda.data_venda)}
              </div>
              {venda.pedido_origem_numero && (
                <div style={{ fontSize: '10px', color: '#666' }}>
                  Pedido: {venda.pedido_origem_numero}
                </div>
              )}
            </td>
          </tr>
        </tbody>
      </table>

      <hr style={{ borderTop: '1px solid #aaa', margin: '4px 0' }} />

      {/* ── Dados do Cliente ── */}
      <div style={{ marginBottom: '8px', fontSize: '11px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            <tr>
              <td style={{ width: '50%' }}>
                <strong>Cliente:</strong>{' '}
                {venda.cliente_nome || 'Consumidor Final'}
              </td>
              <td style={{ width: '50%' }}>
                <strong>Loja:</strong> {loja.nome}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Tabela de Itens ── */}
      {pedidoItens.length > 0 && (
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            marginBottom: '8px',
            fontSize: '11px',
          }}
        >
          <thead>
            <tr style={{ backgroundColor: '#f3f4f6' }}>
              <th style={thStyle}>#</th>
              <th style={{ ...thStyle, textAlign: 'left', width: '40%' }}>Produto</th>
              <th style={thStyle}>Un.</th>
              <th style={thStyle}>Qtd</th>
              <th style={thStyle}>Preço Unit.</th>
              <th style={thStyle}>Desconto</th>
              <th style={thStyle}>Total</th>
            </tr>
          </thead>
          <tbody>
            {pedidoItens.map((item, idx) => (
              <tr key={item.id} style={idx % 2 === 1 ? { backgroundColor: '#fafafa' } : {}}>
                <td style={{ ...tdStyle, textAlign: 'center' }}>{idx + 1}</td>
                <td style={{ ...tdStyle, textAlign: 'left' }}>{item.nome_produto}</td>
                <td style={{ ...tdStyle, textAlign: 'center' }}>{item.unidade_sigla}</td>
                <td style={{ ...tdStyle, textAlign: 'right' }}>
                  {parseFloat(item.quantidade).toLocaleString('pt-BR')}
                </td>
                <td style={{ ...tdStyle, textAlign: 'right' }}>
                  {formatCurrency(item.preco_unitario)}
                </td>
                <td style={{ ...tdStyle, textAlign: 'right' }}>
                  {parseFloat(item.desconto_valor) > 0
                    ? formatCurrency(item.desconto_valor)
                    : '—'}
                </td>
                <td style={{ ...tdStyle, textAlign: 'right', fontWeight: 600 }}>
                  {formatCurrency(item.preco_total)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ── Totais ── */}
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '12px' }}>
        <tbody>
          <tr>
            <td style={{ width: '60%' }} />
            <td style={{ width: '40%' }}>
              <table style={{ width: '100%', fontSize: '11px' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '2px 4px' }}>Total da venda:</td>
                    <td style={{ padding: '2px 4px', textAlign: 'right' }}>
                      {formatCurrency(venda.valor_total)}
                    </td>
                  </tr>
                  {parseFloat(venda.valor_desconto) > 0 && (
                    <tr>
                      <td style={{ padding: '2px 4px' }}>Desconto:</td>
                      <td style={{ padding: '2px 4px', textAlign: 'right', color: '#dc2626' }}>
                        − {formatCurrency(venda.valor_desconto)}
                      </td>
                    </tr>
                  )}
                  <tr style={{ borderTop: '1px solid #aaa' }}>
                    <td style={{ padding: '4px 4px', fontWeight: 700, fontSize: '13px' }}>
                      VALOR LÍQUIDO:
                    </td>
                    <td
                      style={{
                        padding: '4px 4px',
                        textAlign: 'right',
                        fontWeight: 700,
                        fontSize: '13px',
                      }}
                    >
                      {formatCurrency(venda.valor_liquido)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>

      {/* ── Pagamentos ── */}
      {pagamentos.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          <div
            style={{
              fontWeight: 600,
              fontSize: '12px',
              marginBottom: '4px',
              borderBottom: '1px solid #ccc',
              paddingBottom: '2px',
            }}
          >
            Pagamentos
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
            <tbody>
              {pagamentos.map((pag) => (
                <tr key={pag.id}>
                  <td style={{ padding: '2px 4px' }}>
                    {FORMA_LABELS[pag.forma] ?? pag.forma}
                  </td>
                  <td style={{ padding: '2px 4px', textAlign: 'right' }}>
                    {formatCurrency(pag.valor)}
                  </td>
                  {pag.troco && parseFloat(pag.troco) > 0 ? (
                    <td style={{ padding: '2px 4px', textAlign: 'right', color: '#059669' }}>
                      Troco: {formatCurrency(pag.troco)}
                    </td>
                  ) : (
                    <td />
                  )}
                </tr>
              ))}
              <tr style={{ borderTop: '1px solid #aaa', fontWeight: 700 }}>
                <td style={{ padding: '4px 4px' }}>Total pago:</td>
                <td style={{ padding: '4px 4px', textAlign: 'right', fontSize: '13px' }}>
                  {formatCurrency(totalPago)}
                </td>
                <td />
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* ── Chave NF-e (condicional) ── */}
      {venda.nfe_chave_acesso && (
        <div
          style={{
            border: '1px solid #ccc',
            borderRadius: '4px',
            padding: '6px',
            marginBottom: '12px',
            fontSize: '10px',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '2px' }}>Nota Fiscal Eletrônica</div>
          <div style={{ fontFamily: 'monospace', letterSpacing: '0.5px', wordBreak: 'break-all' }}>
            Chave: {venda.nfe_chave_acesso}
          </div>
          {venda.nfe_protocolo && (
            <div>Protocolo: {venda.nfe_protocolo}</div>
          )}
          <div style={{ marginTop: '4px', color: '#555' }}>
            Consulte em: nfe.fazenda.gov.br
          </div>
        </div>
      )}

      {/* ── Rodapé ── */}
      <hr style={{ borderTop: '1px dashed #ccc', margin: '8px 0' }} />
      <div
        style={{
          fontSize: '10px',
          color: '#777',
          textAlign: 'center',
        }}
      >
        Guarde este recibo para sua garantia.
        {!venda.nfe_chave_acesso && ' Este recibo não substitui nota fiscal.'}
      </div>
    </div>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const thStyle: React.CSSProperties = {
  border: '1px solid #ccc',
  padding: '4px 6px',
  fontWeight: 600,
  textAlign: 'right',
  backgroundColor: '#f3f4f6',
};

const tdStyle: React.CSSProperties = {
  border: '1px solid #ddd',
  padding: '3px 6px',
};
