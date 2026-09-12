"""
PIX payment provider interface (stub / Asaas placeholder).

No live API keys required for stub mode. Asaas returns not_configured
when ASAAS_API_KEY is missing.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Any, Dict


def _provider_name() -> str:
    raw = (os.getenv("PIX_PROVIDER") or "stub").strip().lower()
    return raw if raw in {"stub", "asaas"} else "stub"


def create_pix_charge(
    amount_cents: int,
    description: str,
    client_ref: str,
) -> Dict[str, Any]:
    """
    Create a PIX charge via the configured provider.

    Returns dict with provider, qr_payload_stub, txid, status.
    status is "pending" for stub (and asaas when keyed), or "not_configured"
    when PIX_PROVIDER=asaas and ASAAS_API_KEY is unset.
    """
    amount = int(amount_cents)
    if amount < 0:
        raise ValueError("amount_cents must be >= 0")

    desc = (description or "").strip() or "PIX charge"
    ref = (client_ref or "").strip() or "anon"
    provider = _provider_name()

    if provider == "asaas":
        api_key = (os.getenv("ASAAS_API_KEY") or "").strip()
        if not api_key:
            return {
                "provider": "asaas",
                "qr_payload_stub": None,
                "txid": None,
                "status": "not_configured",
                "amount_cents": amount,
                "description": desc,
                "client_ref": ref,
                "error": "ASAAS_API_KEY not set",
            }
        # Key present but live Asaas HTTP not implemented in this stub layer.
        digest = hashlib.sha256(f"asaas:{api_key[:8]}:{ref}:{amount}".encode()).hexdigest()[:20]
        txid = f"ASA{digest.upper()}"
        qr = f"00020126PIX_ASAAS_STUB|cents={amount}|ref={ref}|txid={txid}"
        return {
            "provider": "asaas",
            "qr_payload_stub": qr,
            "txid": txid,
            "status": "pending",
            "amount_cents": amount,
            "description": desc,
            "client_ref": ref,
            "note": "Asaas key detected; live API call not enabled in stub layer",
        }

    token = secrets.token_hex(10).upper()
    txid = f"STUB{token}"
    qr = f"00020126PIX_STUB|cents={amount}|ref={ref}|txid={txid}|{desc[:40]}"
    return {
        "provider": "stub",
        "qr_payload_stub": qr,
        "txid": txid,
        "status": "pending",
        "amount_cents": amount,
        "description": desc,
        "client_ref": ref,
    }
