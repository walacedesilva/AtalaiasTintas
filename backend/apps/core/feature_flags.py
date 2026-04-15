"""Feature flag configuration for gradual rollout of Spec 4 features.

Usage:
  from apps.core.feature_flags import flag_enabled
  if flag_enabled('inventory_multi_unit', request.user):
      ...

Flags are read from environment variables prefixed with FF_.
Fallback: all flags default to False (safe — disables new behaviour).
"""
from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature flag registry
# ---------------------------------------------------------------------------

FEATURE_FLAGS: dict[str, dict] = {
    # Phase 4 — Inventory & Fiscal Integration
    "inventory_multi_unit": {
        "description": "Enable multi-unit inventory conversions (L, KG, caixa, etc.)",
        "env_var":     "FF_INVENTORY_MULTI_UNIT",
        "default":     False,
        "rollout":     "incremental",  # 10% → 50% → 100%
    },
    "inventory_reservations": {
        "description": "Enable time-limited checkout stock reservations",
        "env_var":     "FF_INVENTORY_RESERVATIONS",
        "default":     False,
        "rollout":     "incremental",
    },
    "nfe_automatica": {
        "description": "Enable automatic NF-e emission for B2B sales (requires SEFAZ cert)",
        "env_var":     "FF_NFE_AUTOMATICA",
        "default":     False,
        "rollout":     "loja_by_loja",  # enable store-by-store during onboarding
    },
    "sefaz_homologacao": {
        "description": "Force SEFAZ homologação (test) environment",
        "env_var":     "FF_SEFAZ_HOMOLOGACAO",
        "default":     True,   # SAFE default: always start in homologação
        "rollout":     "manual",
    },
    "checkout_override_estoque": {
        "description": "Allow manager to override insufficient-stock error at checkout",
        "env_var":     "FF_CHECKOUT_OVERRIDE_ESTOQUE",
        "default":     False,
        "rollout":     "role_based",
    },
}


def flag_enabled(flag_name: str, user=None) -> bool:
    """Return True if the given feature flag is enabled.

    Checks ``FF_<FLAG_NAME>`` environment variable (case-insensitive).
    Falls back to the registry default.
    """
    if flag_name not in FEATURE_FLAGS:
        logger.warning("Unknown feature flag %r — returning False", flag_name)
        return False

    cfg = FEATURE_FLAGS[flag_name]
    env_val = os.environ.get(cfg["env_var"], "").strip().lower()

    if env_val in ("1", "true", "yes", "on"):
        return True
    if env_val in ("0", "false", "no", "off"):
        return False

    return bool(cfg["default"])


def all_flags_status() -> dict[str, bool]:
    """Return a dict of all flag names → current enabled status."""
    return {name: flag_enabled(name) for name in FEATURE_FLAGS}
