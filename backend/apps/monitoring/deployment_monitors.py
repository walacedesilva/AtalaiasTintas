"""Deployment monitoring and alerting configuration for Spec 4.

Integrates with Sentry (already in requirements) and Django's logging.
Extend this module to push metrics to Prometheus / Grafana / Datadog.
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alert thresholds (milliseconds)
# ---------------------------------------------------------------------------

THRESHOLDS = {
    "stock_query_ms":     1_000,   # < 1 s
    "nfe_processing_ms": 30_000,   # < 30 s
    "reservation_ms":     5_000,   # < 5 s per session
    "sefaz_request_ms":  15_000,   # < 15 s per SEFAZ call
}

# ---------------------------------------------------------------------------
# Monitoring decorators
# ---------------------------------------------------------------------------


def monitor_latency(operation_name: str, threshold_key: str | None = None) -> Callable:
    """Decorator that logs execution time and fires an alert if threshold is exceeded."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                logger.info("[PERF] %s: %.1fms", operation_name, elapsed_ms)

                if threshold_key and threshold_key in THRESHOLDS:
                    limit = THRESHOLDS[threshold_key]
                    if elapsed_ms > limit:
                        logger.warning(
                            "[ALERT] %s exceeded threshold: %.1fms > %dms",
                            operation_name, elapsed_ms, limit,
                        )
                        _send_alert(operation_name, elapsed_ms, limit)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# NF-e specific monitors
# ---------------------------------------------------------------------------


def alert_nfe_rejected(chave_acesso: str, codigo: str, motivo: str) -> None:
    """Log and alert when SEFAZ rejects an NF-e."""
    logger.error(
        "[NFE-REJECTED] chave=%s codigo=%s motivo=%s",
        chave_acesso, codigo, motivo,
    )
    _send_alert(
        "nfe_rejected",
        extra={"chave": chave_acesso, "codigo": codigo, "motivo": motivo},
    )


def alert_nfe_retry_limit(venda_id: str, tentativas: int) -> None:
    """Alert when an NF-e has exhausted automatic retry attempts."""
    logger.error(
        "[NFE-RETRY-LIMIT] venda=%s tentativas=%d — MANUAL REVIEW REQUIRED",
        venda_id, tentativas,
    )
    _send_alert("nfe_retry_limit", extra={"venda_id": venda_id, "tentativas": tentativas})


def alert_sefaz_unavailable(url: str) -> None:
    """Alert when SEFAZ webservice is unreachable."""
    logger.critical("[SEFAZ-DOWN] url=%s — check SEFAZ status page", url)
    _send_alert("sefaz_unavailable", extra={"url": url})


def alert_certificate_expiry(loja_id: int, days_remaining: int) -> None:
    """Alert when a SEFAZ digital certificate is about to expire."""
    level = "CRITICAL" if days_remaining <= 7 else "WARNING"
    logger.log(
        logging.CRITICAL if level == "CRITICAL" else logging.WARNING,
        "[CERT-EXPIRY] loja=%d expira em %d dia(s)",
        loja_id, days_remaining,
    )
    _send_alert("cert_expiry", extra={"loja_id": loja_id, "days_remaining": days_remaining})


# ---------------------------------------------------------------------------
# Stock monitors
# ---------------------------------------------------------------------------


def alert_stock_below_minimum(produto_id: str, loja_id: int, atual: float, minimo: float) -> None:
    """Alert when stock falls below minimum threshold."""
    logger.warning(
        "[STOCK-LOW] produto=%s loja=%d atual=%.2f minimo=%.2f",
        produto_id, loja_id, atual, minimo,
    )


def alert_reservation_expiry_backlog(count: int) -> None:
    """Alert when there is a large backlog of expired reservations to clean up."""
    if count > 500:
        logger.warning("[RESERVA-EXPIRY-BACKLOG] %d expired reservations pending cleanup", count)


# ---------------------------------------------------------------------------
# Internal: send alert (stub — integrate with Sentry / PagerDuty / etc.)
# ---------------------------------------------------------------------------


def _send_alert(event_name: str, elapsed_ms: float | None = None, threshold_ms: int | None = None,
                extra: dict | None = None) -> None:
    """Send alert to monitoring backend.

    Replace this stub with real integrations:
    - Sentry:    sentry_sdk.capture_message(...)
    - PagerDuty: requests.post(PAGERDUTY_URL, json={...})
    - Slack:     requests.post(WEBHOOK_URL, json={"text": ...})
    """
    payload: dict = {"event": event_name}
    if elapsed_ms is not None:
        payload["elapsed_ms"] = round(elapsed_ms, 1)
    if threshold_ms is not None:
        payload["threshold_ms"] = threshold_ms
    if extra:
        payload.update(extra)

    logger.debug("[ALERT-STUB] %s", payload)
