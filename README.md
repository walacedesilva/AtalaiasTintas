# 🎨 Atalaias Tintas - Sistema de Gestão Completo

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Sobre o Projeto

Sistema completo de gestão para loja de tintas desenvolvido em Python/Django, com funcionalidades específicas para o segmento:

### 🚀 Funcionalidades Principais

- **🎨 Motor Tintométrico** - Fórmulas e cálculos automáticos
- **📦 Gestão de Estoque** - Controle multinível com conversões
- **💰 PDV Inteligente** - Margens em tempo real 
- **🛒 Multi-Marketplace** - Integração ML, Amazon, Shopee
- **🧾 Fiscal Completo** - NF-e, NFC-e, SAT automático
- **👥 CRM Cromático** - Histórico de cores por cliente
- **💳 Crediário Próprio** - Análise de crédito com IA
- **📊 Business Intelligence** - Dashboards em tempo real

### 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Integração    │
│   React/PWA     │────│   Django/APIs   │────│   Marketplaces  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDV Desktop   │    │   PostgreSQL    │    │   SEFAZ/Fiscal │
│   PyQt6         │    │   Redis Cache   │    │   APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🌟 Diferenciais Únicos

- ⚡ **Sincronização < 5s** entre PDV e marketplaces
- 🎨 **Motor tintométrico** com baixa automática de insumos  
- 🧾 **Emissão fiscal** em 30 segundos
- 💳 **Score de crédito** próprio com ML
- 📱 **PWA móvel** para vendedores

## 🚀 Roadmap de Desenvolvimento

### Fase 1: Infraestrutura Core (Meses 1-2)
- [ ] Configuração Django + PostgreSQL
- [ ] Modelagem banco de dados
- [ ] Sistema de autenticação
- [ ] APIs básicas

### Fase 2: Gestão de Estoque (Meses 3-4)  
- [ ] Conversão de unidades
- [ ] Importador XML NFe
- [ ] Sistema de reservas
- [ ] Controle lotes/validade

### Fase 3: Motor Tintométrico (Meses 5-6)
- [ ] Cadastro fórmulas/cores
- [ ] Cálculo automático custos
- [ ] Integração dispensadores
- [ ] Baixa automática insumos

### Fase 4: PDV e CRM (Meses 7-8)
- [ ] Interface PDV PyQt6
- [ ] Histórico cromático
- [ ] Sistema crediário
- [ ] Análise crédito IA

### Fase 5: Marketplaces (Meses 9-10)
- [ ] Hub MercadoLivre/Amazon
- [ ] Sincronização tempo real
- [ ] Faturamento automático
- [ ] Gestão pedidos

### Fase 6: BI e Fiscal (Meses 11-12)
- [ ] Dashboards gerenciais
- [ ] Emissão NF-e/NFC-e/SAT
- [ ] SPED Fiscal automático
- [ ] Relatórios compliance

## 🛠️ Tecnologias

### Backend
- **Python 3.11+** - Linguagem principal
- **Django 4.2+** - Framework web
- **Django REST Framework** - APIs
- **PostgreSQL** - Banco principal
- **Redis** - Cache e filas
- **Celery** - Processamento assíncrono

### Frontend
- **React 18+** - Interface web
- **Next.js** - Framework React
- **PWA** - App móvel
- **PyQt6** - PDV desktop

### Integrações
- **AWS/Docker** - Infraestrutura cloud
- **APIs SEFAZ** - Fiscal brasileiro
- **MercadoLivre/Amazon** - Marketplaces
- **Correios/Transportadoras** - Logística

### Analytics/BI
- **Pandas/NumPy** - Processamento dados
- **Scikit-learn** - Machine Learning
- **Chart.js** - Gráficos
- **ReportLab** - Relatórios PDF

## 📦 Estrutura do Projeto

```
atalaias-tintas/
├── backend/                 # Django Backend
│   ├── apps/
│   │   ├── core/           # Configurações centrais
│   │   ├── products/       # Gestão produtos
│   │   ├── inventory/      # Controle estoque  
│   │   ├── tintometry/     # Sistema tintométrico
│   │   ├── sales/          # Vendas e PDV
│   │   ├── crm/            # Gestão clientes
│   │   ├── financial/      # Crediário/pagamentos
│   │   ├── integrations/   # APIs externas
│   │   ├── analytics/      # BI e relatórios
│   │   └── fiscal/         # Conformidade fiscal
│   └── config/             # Settings Django
├── frontend/               # React Frontend
├── mobile/                 # PWA Mobile
├── desktop/                # PDV PyQt6
├── docs/                   # Documentação
└── deploy/                 # Docker/K8s configs
```

## 🚀 Quick Start

```bash
# Clone o repositório
git clone https://github.com/walacedesilva/AtalaiasTintas.git
cd AtalaiasTintas

# Backend Django
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend React
cd ../frontend  
npm install
npm start

# PDV Desktop
cd ../desktop
pip install -r requirements.txt
python main.py
```

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Contato

**Desenvolvedor:** Walace de Silva  
**Email:** [contato@atalaiastintas.com.br](mailto:contato@atalaiastintas.com.br)  
**LinkedIn:** [Walace de Silva](https://linkedin.com/in/walacesilva)

---

⭐ **Se este projeto foi útil, dê uma estrela!** ⭐