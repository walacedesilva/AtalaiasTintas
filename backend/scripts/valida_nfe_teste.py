"""
Script de validação do XML de teste NF-e para importação no Controle de Estoque.
Uso: python manage.py shell < scripts/valida_nfe_teste.py
  ou: python scripts/valida_nfe_teste.py (rodando direto com o venv ativo)
"""
import os, sys, django

# Garante que o Django está configurado quando rodado fora do shell
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
    django.setup()

from apps.fiscal.services import XmlNFeParser

xml_path = os.path.join(os.path.dirname(__file__), 'nfe_teste_pigmentos.xml')
with open(xml_path, encoding='utf-8') as f:
    xml = f.read()

data = XmlNFeParser().parse(xml)

print('=' * 60)
print('RESULTADO DO PARSE — NF-e TESTE PIGMENTOS')
print('=' * 60)
emit = data['emitente']
nfe  = data['nfe']
tot  = data['totais']
print(f"Chave de acesso : {data['chave_acesso']}")
print(f"Emitente        : {emit.get('nome')} | CNPJ {emit.get('cnpj')}")
print(f"UF/Município    : {emit.get('uf')} — {emit.get('municipio')}")
print(f"NF-e nº {nfe.get('numero')} série {nfe.get('serie')} em {nfe.get('data_emissao')}")
print(f"Nat. Operação   : {nfe.get('natureza_operacao')}")
print(f"Total NF-e      : R$ {tot.get('valor_total')}")
print()
print(f"{'#':<3} {'Código':<18} {'Descrição':<40} {'Qtd':>8} {'Un':<4} {'R$/un':>10} {'Total':>10}")
print('-' * 100)
for item in data['itens']:
    print(
        f"{item['numero_item']:<3} {item['codigo']:<18} {item['descricao'][:40]:<40} "
        f"{float(item['quantidade']):>8.3f} {item['unidade']:<4} "
        f"{float(item['valor_unitario']):>10.4f} {float(item['valor_total']):>10.2f}"
    )
print('-' * 100)
print()
print('✓ XML válido — pronto para importar no Controle de Estoque')
print()
print('COMO IMPORTAR:')
print('  1. Acesse http://localhost:3001/inventory')
print('  2. Clique em "Importar XML NF-e"')
print(f'  3. Selecione: scripts/nfe_teste_pigmentos.xml')
print('  4. Vincule os itens a ProdutoVariacao e confirme a entrada')
