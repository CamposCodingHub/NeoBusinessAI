"""Minimal tests for PIX payment stub service."""

from __future__ import annotations

import os

import pytest

from services.pix_payment_service import create_pix_charge


@pytest.fixture(autouse=True)
def _clean_pix_env(monkeypatch):
    monkeypatch.delenv("PIX_PROVIDER", raising=False)
    monkeypatch.delenv("ASAAS_API_KEY", raising=False)


def test_stub_create_pix_charge_pending():
    result = create_pix_charge(1500, "Honorarios", "client:42")
    assert result["provider"] == "stub"
    assert result["status"] == "pending"
    assert result["txid"].startswith("STUB")
    assert "PIX_STUB" in result["qr_payload_stub"]
    assert result["amount_cents"] == 1500
    assert result["client_ref"] == "client:42"


def test_asaas_without_key_not_configured(monkeypatch):
    monkeypatch.setenv("PIX_PROVIDER", "asaas")
    result = create_pix_charge(999, "Teste", "ref-1")
    assert result["provider"] == "asaas"
    assert result["status"] == "not_configured"
    assert result["txid"] is None
    assert result["qr_payload_stub"] is None
    assert "ASAAS_API_KEY" in result["error"]


def test_asaas_with_key_returns_pending_stub(monkeypatch):
    monkeypatch.setenv("PIX_PROVIDER", "asaas")
    monkeypatch.setenv("ASAAS_API_KEY", "test_asaas_key_not_live")
    result = create_pix_charge(2500, "Servico", "inv:7")
    assert result["provider"] == "asaas"
    assert result["status"] == "pending"
    assert result["txid"].startswith("ASA")
    assert result["qr_payload_stub"]


def test_unknown_provider_falls_back_to_stub(monkeypatch):
    monkeypatch.setenv("PIX_PROVIDER", "something_else")
    result = create_pix_charge(100, "x", "y")
    assert result["provider"] == "stub"
    assert result["status"] == "pending"
