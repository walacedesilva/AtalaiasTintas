# Spec 4 — Operational Runbook: Inventory & Fiscal Integration

**System**: AtalaiasTintas — NF-e Automation & Multi-Unit Inventory  
**Last updated**: 2026-04-14  
**Owner**: Backend team  

---

## 1. System Architecture

```
Operador → Django API → VendaService → EstoqueService (reservas)
                                     → NFEService (B2B)
                                          → Celery task → SefazClient
                                                             → SEFAZ SOAP
```

Key models: `EstoqueLoja`, `EstoqueReserva`, `MovimentacaoEstoque`, `Venda`, `NotaFiscal`, `ConfiguracaoFiscal`

---

## 2. Daily Operations

### 2.1 Check NF-e Queue

```bash
# View pending NF-e tasks
./manage.py shell -c "from apps.sales.models import Venda; print(Venda.objects.filter(nfe_situacao='PENDENTE').count())"

# View NF-e in AGUARDANDO_RETRY
./manage.py shell -c "from apps.sales.models import Venda; print(Venda.objects.filter(nfe_situacao='AGUARDANDO_RETRY').count())"
```

### 2.2 Check Reservation Backlog

```bash
./manage.py shell -c "
from apps.inventory.models import EstoqueReserva
from django.utils import timezone
expired = EstoqueReserva.objects.filter(status='ATIVA', expira_em__lt=timezone.now()).count()
print(f'Expired reservations: {expired}')
"
```

### 2.3 Clean Expired Reservations (manual)

```bash
./manage.py shell -c "
from apps.inventory.models import EstoqueReserva
from django.utils import timezone
count = EstoqueReserva.objects.filter(status='ATIVA', expira_em__lt=timezone.now()).update(status='EXPIRADA')
print(f'Marked {count} reservations as EXPIRADA')
"
```

---

## 3. Incident Response

### 3.1 SEFAZ Service Down

**Symptoms**: NF-e tasks fail with `SefazConnectionError` or `SefazTimeoutError`

**Steps**:
1. Check SEFAZ status: https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx
2. Check Celery logs: `tail -f /var/log/celery/worker.log`
3. If confirmed down: sales can continue but NF-e will queue
4. When SEFAZ recovers: tasks will auto-retry via `AGUARDANDO_RETRY`
5. If tasks don't auto-retry: manually re-queue:
   ```bash
   ./manage.py shell -c "
   from apps.fiscal.services import NFEService
   from apps.sales.models import Venda
   from django.contrib.auth import get_user_model
   User = get_user_model()
   system_user = User.objects.filter(is_superuser=True).first()
   stuck = Venda.objects.filter(nfe_situacao='AGUARDANDO_RETRY')
   for v in stuck:
       NFEService.processar_nfe_venda(str(v.pk), system_user)
   print(f'Re-queued {stuck.count()} NF-e tasks')
   "
   ```

### 3.2 NF-e Permanent Rejection (non-corrigível)

**Symptoms**: `SefazRejeicaoError` with `corrigivel=False`, `nfe_requer_retry_manual=True`

**Steps**:
1. Identify the rejection code and motivo in logs / admin
2. Consult SEFAZ rejection table: http://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=YBv0TqyJaXQ=
3. Fix the underlying data (CNPJ, NCM code, etc.)
4. Re-trigger NF-e emission via Django admin or:
   ```bash
   ./manage.py shell -c "
   from apps.fiscal.services import NFEService
   from apps.sales.models import Venda
   venda = Venda.objects.get(numero_venda='V-2026-12345')
   venda.nfe_requer_retry_manual = False
   venda.nfe_situacao = 'PENDENTE'
   venda.save()
   "
   ```

### 3.3 Incorrect Stock After Migration

**Symptoms**: `calcular_disponibilidade` returns wrong value; movimentações missing

**Steps**:
1. Compare EstoqueLoja.quantidade_disponivel with sum of SAIDA_VENDA movements:
   ```bash
   ./manage.py shell -c "
   from apps.inventory.models import EstoqueLoja, MovimentacaoEstoque
   from django.db.models import Sum
   for el in EstoqueLoja.objects.select_related('produto_variacao')[:20]:
       saidas = MovimentacaoEstoque.objects.filter(
           produto_id=el.produto_variacao_id,
           loja_id=el.loja_id,
           tipo_movimentacao='SAIDA_VENDA',
       ).aggregate(total=Sum('quantidade_base'))['total'] or 0
       entradas = MovimentacaoEstoque.objects.filter(
           produto_id=el.produto_variacao_id,
           loja_id=el.loja_id,
           tipo_movimentacao__in=['ENTRADA', 'DEVOLUCAO_VENDA'],
       ).aggregate(total=Sum('quantidade_base'))['total'] or 0
       calculado = entradas - saidas
       if abs(float(calculado) - float(el.quantidade_disponivel)) > 0.001:
           print(f'DIVERGENCE: {el.produto_variacao.nome_completo} calculado={calculado} atual={el.quantidade_disponivel}')
   "
   ```
2. For each divergent product, create a correction MovimentacaoEstoque (type=AJUSTE_ENTRADA or AJUSTE_SAIDA)

### 3.4 Digital Certificate Expired

**Symptoms**: `SefazCertificadoError`: "Certificado expirado"

**Steps**:
1. Obtain new A1 certificate from certificate authority (e-CPF/e-CNPJ)
2. Place `.pfx` file in the secure certs directory
3. Update `ConfiguracaoFiscal.certificado_path` via admin (or env var)
4. Test in homologação: `FF_SEFAZ_HOMOLOGACAO=true`
5. Place in production
6. Verify: `./manage.py shell -c "from apps.fiscal.sefaz.client import SefazClient; c = SefazClient.from_configuracao(loja_id=1); print(c.verificar_status_servico())"`

---

## 4. Scheduled Maintenance

| Task | Frequency | Command |
|------|-----------|---------|
| Clean expired reservations | Hourly (Celery beat) | `limpar_reservas_expiradas` task |
| Check NF-e retry queue | Every 15 min | `processar_retry_nfe` task |
| Certificate expiry check | Daily | `verificar_certificados_expirando` task |
| DB vacuum (SQLite) | Weekly | `./manage.py dbshell <<< 'VACUUM;'` |

---

## 5. Useful Commands

```bash
# Check system health
./manage.py check --deploy

# View Celery worker status
celery -A tintas_system inspect active

# Force retry all AGUARDANDO_RETRY NF-e
./manage.py shell -c "
from apps.fiscal.tasks import processar_retry_nfe
processar_retry_nfe.delay()
"

# Feature flag status
./manage.py shell -c "
from apps.core.feature_flags import all_flags_status
import json; print(json.dumps(all_flags_status(), indent=2))
"
```

---

## 6. Escalation

| Severity | Response Time | Contact |
|----------|--------------|---------|
| CRITICAL (SEFAZ down, cert expired) | 30 min | Backend lead |
| HIGH (NF-e queue > 100 pending) | 2 hours | Backend team |
| MEDIUM (performance degradation) | 1 business day | Team |
| LOW (manual retry needed) | By next business day | Support |
