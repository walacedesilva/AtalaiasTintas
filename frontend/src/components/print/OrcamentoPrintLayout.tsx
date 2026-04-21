import './print.css';
import type { Loja, PedidoVenda } from '@/types';

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

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('pt-BR');
  } catch {
    return iso;
  }
}

function addDays(iso: string, days: number): string {
  try {
    const d = new Date(iso);
    d.setDate(d.getDate() + days);
    return d.toLocaleDateString('pt-BR');
  } catch {
    return '';
  }
}

// ─── Component ───────────────────────────────────────────────────────────────

interface Props {
  pedido: PedidoVenda;
  loja: Loja;
}

export function OrcamentoPrintLayout({ pedido, loja }: Props) {
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

  const validade = addDays(pedido.data_pedido, 3);

  return (
    <div
      id="orcamento-print"
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
                Orçamento
              </div>
              <div style={{ fontSize: '13px' }}>Nº {pedido.numero_pedido}</div>
              <div style={{ fontSize: '11px' }}>Data: {formatDate(pedido.data_pedido)}</div>
              {validade && (
                <div style={{ fontSize: '11px' }}>Validade: {validade}</div>
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
                {pedido.cliente_nome || 'Consumidor Final'}
              </td>
              <td style={{ width: '50%' }}>
                <strong>Loja:</strong> {loja.nome}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Tabela de Itens ── */}
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
          {pedido.itens.length === 0 && (
            <tr>
              <td colSpan={7} style={{ ...tdStyle, textAlign: 'center', color: '#888' }}>
                Nenhum item
              </td>
            </tr>
          )}
          {pedido.itens.map((item, idx) => (
            <tr key={item.id} style={idx % 2 === 1 ? { backgroundColor: '#fafafa' } : {}}>
              <td style={{ ...tdStyle, textAlign: 'center' }}>{idx + 1}</td>
              <td style={{ ...tdStyle, textAlign: 'left' }}>
                {item.nome_produto}
                {item.observacoes && (
                  <div style={{ fontSize: '10px', color: '#666' }}>{item.observacoes}</div>
                )}
              </td>
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

      {/* ── Totais ── */}
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '12px' }}>
        <tbody>
          <tr>
            <td style={{ width: '60%' }} />
            <td style={{ width: '40%' }}>
              <table style={{ width: '100%', fontSize: '11px' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '2px 4px' }}>Subtotal:</td>
                    <td style={{ padding: '2px 4px', textAlign: 'right' }}>
                      {formatCurrency(pedido.valor_subtotal)}
                    </td>
                  </tr>
                  {parseFloat(pedido.valor_desconto) > 0 && (
                    <tr>
                      <td style={{ padding: '2px 4px' }}>Desconto:</td>
                      <td style={{ padding: '2px 4px', textAlign: 'right', color: '#dc2626' }}>
                        − {formatCurrency(pedido.valor_desconto)}
                      </td>
                    </tr>
                  )}
                  <tr style={{ borderTop: '1px solid #aaa' }}>
                    <td style={{ padding: '4px 4px', fontWeight: 700, fontSize: '13px' }}>
                      TOTAL:
                    </td>
                    <td
                      style={{
                        padding: '4px 4px',
                        textAlign: 'right',
                        fontWeight: 700,
                        fontSize: '13px',
                      }}
                    >
                      {formatCurrency(pedido.valor_total)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>

      {/* ── Rodapé ── */}
      <hr style={{ borderTop: '1px solid #aaa', margin: '8px 0' }} />
      <div style={{ fontSize: '10px', color: '#555', marginBottom: '16px' }}>
        Validade deste orçamento: {validade || '3 dias a partir da emissão'}.
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
        <tbody>
          <tr>
            <td style={{ width: '45%', borderTop: '1px solid #555', paddingTop: '4px', fontSize: '10px' }}>
              Assinatura do Vendedor
            </td>
            <td style={{ width: '10%' }} />
            <td style={{ width: '45%', borderTop: '1px solid #555', paddingTop: '4px', fontSize: '10px' }}>
              Data e Local
            </td>
          </tr>
        </tbody>
      </table>
      <div
        style={{
          marginTop: '16px',
          fontSize: '10px',
          color: '#777',
          textAlign: 'center',
          borderTop: '1px dashed #ccc',
          paddingTop: '6px',
        }}
      >
        Este orçamento não constitui nota fiscal. Sujeito a alterações sem aviso prévio.
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
