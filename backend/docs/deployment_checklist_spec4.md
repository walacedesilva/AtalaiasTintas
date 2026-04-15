# Production Deployment Checklist — Spec 4 (Inventory & Fiscal Integration)

**Version**: 1.0  
**Date**: 2026-04-14  

---

## Pre-Deployment (T-2 days)

### Database Backup
- [ ] Full database backup completed and verified restorable
- [ ] Backup stored in secure off-site location
- [ ] Snapshot SQL procedures executed (`scripts/rollback_spec4.sql` section 0)
- [ ] Previous migration state recorded (`django_migrations` dump)

### Code Readiness
- [ ] All 92+ tests passing on `main` branch (`manage.py test tests --verbosity=1`)
- [ ] `manage.py check --deploy` returns 0 issues
- [ ] No outstanding merge conflicts on main
- [ ] Code review approved by at least 1 other engineer

### SEFAZ Homologação Testing
- [ ] SefazClient tested against SEFAZ homologação with real certificate
- [ ] autorizar_nfe returns 100 (Autorizado) in homologação
- [ ] consultar_situacao returns correct chave
- [ ] cancelar_nfe returns 135 for a test NF-e
- [ ] verificar_status_servico returns `disponivel=True`

### Feature Flags
- [ ] `FF_SEFAZ_HOMOLOGACAO=true` set in staging
- [ ] `FF_NFE_AUTOMATICA=false` set in production (start disabled)
- [ ] `FF_INVENTORY_RESERVATIONS=false` set in production (start disabled)
- [ ] `FF_INVENTORY_MULTI_UNIT=false` set in production (start disabled)

---

## Deployment Day (T-0)

### Pre-Deployment Window
- [ ] Maintenance window scheduled (off-peak hours, e.g., 22:00-00:00)
- [ ] Team members notified
- [ ] Rollback plan reviewed by deployer (`scripts/rollback_spec4.sql`)
- [ ] Monitoring dashboards open

### Database Migrations
- [ ] `manage.py showmigrations` confirms expected migration state
- [ ] `manage.py migrate --plan` reviewed for expected changes
- [ ] `manage.py migrate` executed successfully
- [ ] No migration errors in logs

### Application Deployment
- [ ] New code deployed to server(s)
- [ ] Static files collected: `manage.py collectstatic`
- [ ] Gunicorn / uWSGI restarted
- [ ] Celery workers restarted

### Smoke Tests
- [ ] `manage.py check` — 0 issues
- [ ] Health check endpoint responds: `curl http://localhost:8000/health/`
- [ ] Admin panel loads without errors
- [ ] `manage.py test tests --verbosity=1` passes on server (optional — staging validated)

---

## Post-Deployment (T+1 hour)

### Feature Flag Gradual Rollout

**Step 1** (first hour): Enable for internal team only
- [ ] `FF_INVENTORY_MULTI_UNIT=true` on 1 test store
- [ ] Verify stock queries work via Django admin
- [ ] Monitor error logs for 15 minutes

**Step 2** (hours 2-4): Enable reservations
- [ ] `FF_INVENTORY_RESERVATIONS=true` on test store
- [ ] Create a test checkout and verify reservation created
- [ ] Verify reservation expires after 30 min

**Step 3** (day 2): Enable NF-e on test store in homologação
- [ ] `FF_NFE_AUTOMATICA=true` on 1 store
- [ ] `FF_SEFAZ_HOMOLOGACAO=true` (keep in test env)
- [ ] Complete a B2B sale and verify NF-e created with situacao=AUTORIZADA
- [ ] Check Celery task completed

**Step 4** (week 2): Production NF-e
- [ ] `FF_SEFAZ_HOMOLOGACAO=false` on production ONLY after Step 3 validated
- [ ] Monitor NF-e queue for first 24 hours
- [ ] Check certificate expiry alerts configured

### Monitoring Verification
- [ ] Celery tasks completing (no task failures in logs)
- [ ] `nfe_situacao` distribution reasonable (`PENDENTE` → `AUTORIZADA` within 30s)
- [ ] No `SefazCertificadoError` in logs
- [ ] Reservation cleanup Celery beat running hourly
- [ ] Log level set correctly (no DEBUG in production)

---

## Post-Deployment (T+24 hours)

### Health Report
- [ ] Total NF-e emitidas in first 24h
- [ ] NF-e rejection rate < 5%
- [ ] AGUARDANDO_RETRY count < 10
- [ ] Stock divergence check (see runbook section 3.3): 0 divergences
- [ ] Performance: average stock query < 500ms (check APM)
- [ ] No certificate expiry alerts

### Rollback Gate
If any of the following are true, initiate rollback:
- [ ] NF-e rejection rate > 20%
- [ ] Celery task failure rate > 10%
- [ ] Stock calculation divergences found
- [ ] `SefazCertificadoError` on production
- [ ] Response time > 2s for checkout endpoints

**Rollback command**:
```bash
# 1. Revert code to previous release
git checkout <previous-tag>

# 2. Apply DB rollback (sections 1-3 of rollback_spec4.sql)
./manage.py dbshell < scripts/rollback_spec4.sql

# 3. Rollback migrations to pre-Spec4 state
./manage.py migrate inventory 0000  # adjust to last pre-spec4 migration
./manage.py migrate fiscal 0000
./manage.py migrate sales 0000

# 4. Restart services
```

---

## Sign-Off

| Role | Name | Approved |
|------|------|----------|
| Developer | | |
| Technical Lead | | |
| QA | | |
| Operations | | |
