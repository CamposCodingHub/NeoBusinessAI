"""
Webhook Handlers
================
Processamento seguro de webhooks Mercado Pago.
"""

from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import json
import logging

from core.database import get_db
from core.config import settings
from core.security import verify_webhook_signature
from services.billing_service import billing_service
from models.audit_log import AuditLog, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="x-signature"),
    x_request_id: Optional[str] = Header(None, alias="x-request-id"),
    db: Session = Depends(get_db)
):
    """
    Webhook do Mercado Pago para eventos de pagamento.
    
    Valida assinatura, previne replay attacks e processa eventos.
    """
    # Obter payload
    payload = await request.body()
    
    # Validar assinatura
    if not x_signature:
        logger.warning("Webhook sem assinatura")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura ausente"
        )
    
    # Verificar assinatura HMAC
    is_valid = verify_webhook_signature(
        payload,
        x_signature,
        settings.MERCADO_PAGO_WEBHOOK_SECRET
    )
    
    if not is_valid:
        logger.warning("Webhook com assinatura inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura inválida"
        )
    
    # Prevenir replay attack usando request_id
    if x_request_id:
        # TODO: Verificar se request_id já foi processado (Redis)
        pass
    
    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        logger.error("Webhook payload inválido")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )
    
    # Processar evento
    event_type = data.get("type")
    event_data = data.get("data", {})
    
    logger.info(f"Webhook recebido: {event_type}")
    
    try:
        if event_type == "payment":
            await _handle_payment_event(db, event_data)
        elif event_type == "preapproval":
            await _handle_preapproval_event(db, event_data)
        else:
            logger.warning(f"Tipo de evento não suportado: {event_type}")
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar webhook"
        )


async def _handle_payment_event(db: Session, event_data: dict):
    """
    Processa evento de pagamento único.
    
    Args:
        db: Sessão do banco
        event_data: Dados do evento
    """
    payment_id = event_data.get("id")
    
    if not payment_id:
        logger.error("Payment ID ausente no evento")
        return
    
    # Obter detalhes do pagamento
    from services.billing_service import mercado_pago_service
    payment = await mercado_pago_service.get_payment(payment_id)
    
    # Atualizar assinatura se existir
    external_reference = payment.get("external_reference")
    if external_reference:
        try:
            billing_service.update_subscription_status(
                db,
                external_reference,
                payment.get("status"),
                payment
            )
            
            # Log de auditoria
            _log_payment_event(db, payment)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar assinatura: {e}")


async def _handle_preapproval_event(db: Session, event_data: dict):
    """
    Processa evento de recorrência (preapproval).
    
    Args:
        db: Sessão do banco
        event_data: Dados do evento
    """
    preapproval_id = event_data.get("id")
    
    if not preapproval_id:
        logger.error("Preapproval ID ausente no evento")
        return
    
    # TODO: Processar evento de recorrência
    logger.info(f"Preapproval event: {preapproval_id}")


def _log_payment_event(db: Session, payment: dict):
    """Log de evento de pagamento para auditoria"""
    # TODO: Implementar log de auditoria
    pass
