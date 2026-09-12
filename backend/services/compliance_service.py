"""
Compliance Service
===================
Serviço de LGPD/GDPR — exportação e retenção de dados do escritório.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Campos de perfil nunca incluídos no pacote de exportação
_PROFILE_DENYLIST = frozenset(
    {
        "password_hash",
        "password",
        "hashed_password",
        "secret",
        "api_key",
        "token",
        "refresh_token",
        "stripe_customer_id",
        "stripe_subscription_id",
    }
)


class ConsentType(str):
    """Tipos de consentimento"""

    MARKETING = "marketing"
    ANALYTICS = "analytics"
    DATA_PROCESSING = "data_processing"
    EMAIL_COMMUNICATIONS = "email_communications"


class ComplianceService:
    """Serviço de compliance LGPD/GDPR (firm user)."""

    @staticmethod
    def _safe_section(
        name: str,
        fn: Callable[[], Any],
        partial_errors: List[Dict[str, str]],
        default: Any,
    ) -> Any:
        """Executa uma seção best-effort; falha isolada não derruba o export."""
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — pacote de compliance deve sobreviver
            logger.warning("GDPR export section '%s' failed: %s", name, exc)
            partial_errors.append({"section": name, "error": str(exc)})
            try:
                # Limpa sessão se a query deixou-a em estado inválido
                # (caller passa db via closure — rollback best-effort no fn)
                pass
            except Exception:
                pass
            return default

    @staticmethod
    def _profile_from_user(user: Any) -> Dict[str, Any]:
        """Serializa perfil sem hashes/segredos."""
        raw = {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "name": getattr(user, "name", None),
            "company": getattr(user, "company", None),
            "phone": getattr(user, "phone", None),
            "role": getattr(user, "role", None),
            "plan_tier": getattr(user, "plan_tier", None),
            "subscription_status": getattr(user, "subscription_status", None),
            "documents_limit": getattr(user, "documents_limit", None),
            "users_limit": getattr(user, "users_limit", None),
            "is_active": getattr(user, "is_active", None),
            "created_at": (
                user.created_at.isoformat()
                if getattr(user, "created_at", None)
                else None
            ),
            "updated_at": (
                user.updated_at.isoformat()
                if getattr(user, "updated_at", None)
                else None
            ),
            "last_login": (
                user.last_login.isoformat()
                if getattr(user, "last_login", None)
                else None
            ),
        }
        return {k: v for k, v in raw.items() if k not in _PROFILE_DENYLIST}

    @staticmethod
    def export_user_data(db: Session, user_id: Any) -> Dict[str, Any]:
        """
        Exporta pacote JSON do usuário autenticado (LGPD Art. 18 / GDPR portability).

        Best-effort: se uma tabela/coluna faltar, a seção é marcada em
        ``partial_errors`` e o restante do pacote é retornado.
        Nunca inclui password_hash nem segredos.
        """
        from database import (
            ChatMessage,
            Client,
            Document,
            Invoice,
            Lead,
            Matter,
            User,
        )

        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            uid = user_id

        user = db.query(User).filter(User.id == uid).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        partial_errors: List[Dict[str, str]] = []
        package: Dict[str, Any] = {
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "2.0",
                "legal_basis": "LGPD Art. 18 (Portabilidade) / GDPR Art. 20",
                "user_id": uid,
            },
            "profile": ComplianceService._profile_from_user(user),
            "clients_count": 0,
            "documents": [],
            "invoices_summary": {
                "count": 0,
                "total_amount_cents": 0,
                "by_status": {},
                "items": [],
            },
            "chat_messages_count": 0,
            "leads_count": 0,
            "matters_count": 0,
            "partial_errors": partial_errors,
        }

        def _count_clients() -> int:
            try:
                return db.query(Client).filter(Client.user_id == uid).count()
            except Exception:
                db.rollback()
                raise

        def _documents_meta() -> List[Dict[str, Any]]:
            try:
                docs = db.query(Document).filter(Document.user_id == uid).all()
                return [
                    {
                        "id": d.id,
                        "filename": d.filename,
                        "original_filename": getattr(d, "original_filename", None),
                        "file_type": d.file_type,
                        "file_size": d.file_size,
                        "status": d.status,
                        "title": getattr(d, "title", None),
                        "created_at": (
                            d.created_at.isoformat() if d.created_at else None
                        ),
                        "updated_at": (
                            d.updated_at.isoformat()
                            if getattr(d, "updated_at", None)
                            else None
                        ),
                    }
                    for d in docs
                ]
            except Exception:
                db.rollback()
                raise

        def _invoices_summary() -> Dict[str, Any]:
            try:
                invoices = db.query(Invoice).filter(Invoice.user_id == uid).all()
                by_status: Dict[str, int] = {}
                total = 0
                items: List[Dict[str, Any]] = []
                for inv in invoices:
                    st = inv.status or "unknown"
                    by_status[st] = by_status.get(st, 0) + 1
                    cents = int(getattr(inv, "total_cents", 0) or 0)
                    total += cents
                    items.append(
                        {
                            "id": inv.id,
                            "invoice_number": inv.invoice_number,
                            "client_id": inv.client_id,
                            "status": inv.status,
                            "total_cents": cents,
                            "due_date": (
                                inv.due_date.isoformat() if inv.due_date else None
                            ),
                            "issue_date": (
                                inv.issue_date.isoformat()
                                if getattr(inv, "issue_date", None)
                                else None
                            ),
                            "created_at": (
                                inv.created_at.isoformat()
                                if getattr(inv, "created_at", None)
                                else None
                            ),
                        }
                    )
                return {
                    "count": len(invoices),
                    "total_amount_cents": total,
                    "by_status": by_status,
                    "items": items,
                }
            except Exception:
                db.rollback()
                raise

        def _count_chat() -> int:
            try:
                return (
                    db.query(ChatMessage).filter(ChatMessage.user_id == uid).count()
                )
            except Exception:
                db.rollback()
                raise

        def _count_leads() -> int:
            try:
                return db.query(Lead).filter(Lead.user_id == uid).count()
            except Exception:
                db.rollback()
                raise

        def _count_matters() -> int:
            try:
                return db.query(Matter).filter(Matter.user_id == uid).count()
            except Exception:
                db.rollback()
                raise

        package["clients_count"] = ComplianceService._safe_section(
            "clients_count", _count_clients, partial_errors, 0
        )
        package["documents"] = ComplianceService._safe_section(
            "documents", _documents_meta, partial_errors, []
        )
        package["invoices_summary"] = ComplianceService._safe_section(
            "invoices_summary",
            _invoices_summary,
            partial_errors,
            {
                "count": 0,
                "total_amount_cents": 0,
                "by_status": {},
                "items": [],
            },
        )
        package["chat_messages_count"] = ComplianceService._safe_section(
            "chat_messages_count", _count_chat, partial_errors, 0
        )
        package["leads_count"] = ComplianceService._safe_section(
            "leads_count", _count_leads, partial_errors, 0
        )
        package["matters_count"] = ComplianceService._safe_section(
            "matters_count", _count_matters, partial_errors, 0
        )

        # Garantia final: nenhum segredo no JSON
        profile = package.get("profile") or {}
        for banned in _PROFILE_DENYLIST:
            profile.pop(banned, None)
        package["profile"] = profile

        serialized = str(package)
        if "password_hash" in serialized.lower():
            logger.error("GDPR export leaked password_hash — stripping package keys")
            package["profile"] = {
                k: v
                for k, v in package["profile"].items()
                if "password" not in k.lower() and "hash" not in k.lower()
            }

        return package

    @staticmethod
    def get_retention_policy() -> Dict[str, int]:
        """Política de retenção de dados (em dias)."""
        return {
            "user_profile": 2555,  # 7 anos após conta deletada
            "documents": 1825,  # 5 anos
            "audit_logs": 2555,  # 7 anos
            "payment_data": 2555,  # 7 anos (fiscal)
            "consent_records": 2555,  # 7 anos
            "analytics_data": 730,  # 2 anos
        }

    @staticmethod
    def check_data_retention(db: Session) -> list:
        """Placeholder — verificação de retenção."""
        _ = db
        _ = ComplianceService.get_retention_policy()
        return []


compliance_service = ComplianceService()
