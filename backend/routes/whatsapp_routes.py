"""
Módulo WhatsApp - JurisFlow AI
Integração com Twilio e Evolution API para comunicação
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging
import os
import requests

from database import get_db, WhatsAppConfig, ChatMessage, NotificationQueue, Client, Deadline, Invoice
from security import get_current_user
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


# ============================================
# MODELOS Pydantic
# ============================================

class WhatsAppConfigSchema(BaseModel):
    provider: str = "twilio"
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    evolution_api_url: Optional[str] = None
    evolution_api_key: Optional[str] = None
    evolution_instance: Optional[str] = None
    auto_notify_deadlines: bool = True
    auto_notify_invoices: bool = True


class SendMessageSchema(BaseModel):
    phone: str
    message: str
    client_id: Optional[int] = None
    context_type: Optional[str] = None
    context_id: Optional[int] = None


# ============================================
# CONFIGURAÇÃO
# ============================================

@router.get("/config")
async def get_whatsapp_config(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retorna configuração atual do WhatsApp (sem dados sensíveis)"""
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id
    ).first()
    
    if not config:
        return {
            "is_configured": False,
            "is_active": False,
            "provider": "twilio",
            "auto_notify_deadlines": True,
            "auto_notify_invoices": True
        }
    
    return {
        "is_configured": True,
        "is_active": config.is_active,
        "is_connected": config.is_connected,
        "provider": config.provider,
        "phone_number": config.twilio_phone_number if config.provider == "twilio" else None,
        "auto_notify_deadlines": config.auto_notify_deadlines,
        "auto_notify_invoices": config.auto_notify_invoices,
        "connected_at": config.connected_at.isoformat() if config.connected_at else None
    }


@router.post("/config")
async def save_whatsapp_config(
    config_data: WhatsAppConfigSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Salva configuração do WhatsApp"""
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id
    ).first()
    
    if config:
        # Update
        config.provider = config_data.provider
        if config_data.provider == "twilio":
            config.twilio_account_sid = config_data.twilio_account_sid
            config.twilio_auth_token = config_data.twilio_auth_token
            config.twilio_phone_number = config_data.twilio_phone_number
        else:
            config.evolution_api_url = config_data.evolution_api_url
            config.evolution_api_key = config_data.evolution_api_key
            config.evolution_instance = config_data.evolution_instance
        config.auto_notify_deadlines = config_data.auto_notify_deadlines
        config.auto_notify_invoices = config_data.auto_notify_invoices
    else:
        # Create
        config = WhatsAppConfig(
            user_id=current_user.id,
            provider=config_data.provider,
            twilio_account_sid=config_data.twilio_account_sid if config_data.provider == "twilio" else None,
            twilio_auth_token=config_data.twilio_auth_token if config_data.provider == "twilio" else None,
            twilio_phone_number=config_data.twilio_phone_number if config_data.provider == "twilio" else None,
            evolution_api_url=config_data.evolution_api_url if config_data.provider == "evolution_api" else None,
            evolution_api_key=config_data.evolution_api_key if config_data.provider == "evolution_api" else None,
            evolution_instance=config_data.evolution_instance if config_data.provider == "evolution_api" else None,
            auto_notify_deadlines=config_data.auto_notify_deadlines,
            auto_notify_invoices=config_data.auto_notify_invoices
        )
        db.add(config)
    
    db.commit()
    db.refresh(config)
    
    # Test connection
    try:
        if config.provider == "twilio" and config.twilio_account_sid and config.twilio_auth_token:
            # Test Twilio connection
            import requests
            response = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}.json",
                auth=(config.twilio_account_sid, config.twilio_auth_token),
                timeout=10
            )
            if response.status_code == 200:
                config.is_connected = True
                config.is_active = True
                config.connected_at = datetime.utcnow()
                db.commit()
                return {"message": "Configuração salva e conectada com sucesso!", "is_connected": True}
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}")
    
    return {"message": "Configuração salva. Verifique as credenciais.", "is_connected": False}


@router.post("/config/test")
async def test_whatsapp_connection(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Testa a conexão com o provedor WhatsApp"""
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=400, detail="Configuração não encontrada")
    
    try:
        if config.provider == "twilio":
            response = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}.json",
                auth=(config.twilio_account_sid, config.twilio_auth_token),
                timeout=10
            )
            if response.status_code == 200:
                config.is_connected = True
                config.is_active = True
                config.connected_at = datetime.utcnow()
                db.commit()
                return {"status": "connected", "message": "Conexão com Twilio OK"}
            else:
                return {"status": "error", "message": f"Erro Twilio: {response.status_code}"}
        
        elif config.provider == "evolution_api":
            # Test Evolution API
            response = requests.get(
                f"{config.evolution_api_url}/instance/connectionState/{config.evolution_instance}",
                headers={"apikey": config.evolution_api_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                config.is_connected = data.get("state") == "open"
                config.is_active = config.is_connected
                db.commit()
                return {"status": "connected" if config.is_connected else "disconnected", 
                        "message": f"Estado: {data.get('state')}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================
# ENVIO DE MENSAGENS
# ============================================

@router.post("/send")
async def send_whatsapp_message(
    message_data: SendMessageSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Envia mensagem via WhatsApp"""
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id,
        WhatsAppConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(status_code=400, detail="WhatsApp não configurado")
    
    # Formatar número
    phone = message_data.phone.replace("+", "").replace("-", "").replace(" ", "")
    if not phone.startswith("55"):
        phone = "55" + phone
    
    message_sent = False
    error_msg = None
    
    try:
        if config.provider == "twilio":
            # Send via Twilio
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages.json",
                auth=(config.twilio_account_sid, config.twilio_auth_token),
                data={
                    "From": f"whatsapp:{config.twilio_phone_number}",
                    "To": f"whatsapp:+{phone}",
                    "Body": message_data.message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                message_sent = True
                twilio_data = response.json()
                message_id = twilio_data.get("sid")
            else:
                error_msg = f"Twilio error: {response.status_code}"
                logger.error(f"Twilio error: {response.text}")
        
        elif config.provider == "evolution_api":
            # Send via Evolution API
            response = requests.post(
                f"{config.evolution_api_url}/message/sendText/{config.evolution_instance}",
                headers={"apikey": config.evolution_api_key},
                json={
                    "number": phone,
                    "text": message_data.message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                message_sent = True
                data = response.json()
                message_id = data.get("key", {}).get("id")
            else:
                error_msg = f"Evolution API error: {response.status_code}"
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao enviar mensagem: {e}")
    
    # Salvar no banco
    chat_message = ChatMessage(
        user_id=current_user.id,
        client_id=message_data.client_id,
        sender_type="user",
        sender_name=current_user.name,
        sender_phone=config.twilio_phone_number if config.provider == "twilio" else config.evolution_instance,
        message=message_data.message,
        message_type="text",
        is_from_whatsapp=True,
        whatsapp_message_id=message_id if message_sent else None,
        context_type=message_data.context_type,
        context_id=message_data.context_id
    )
    db.add(chat_message)
    db.commit()
    
    if message_sent:
        return {
            "message": "Mensagem enviada com sucesso",
            "chat_message_id": chat_message.id,
            "whatsapp_message_id": message_id
        }
    else:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {error_msg}")


# ============================================
# WEBHOOK
# ============================================

@router.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook para receber mensagens do Twilio"""
    form_data = await request.form()
    
    from_number = form_data.get("From", "").replace("whatsapp:", "")
    to_number = form_data.get("To", "").replace("whatsapp:", "")
    body = form_data.get("Body", "")
    message_sid = form_data.get("MessageSid")
    
    logger.info(f"Mensagem recebida de {from_number}: {body[:50]}...")
    
    # Encontrar usuário pelo número de telefone
    # (Buscar config que tenha esse número como twilio_phone_number)
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.twilio_phone_number == to_number,
        WhatsAppConfig.is_active == True
    ).first()
    
    if not config:
        logger.warning(f"Nenhum usuário encontrado para número: {to_number}")
        return {"status": "ok"}  # Twilio precisa de 200
    
    # Encontrar cliente pelo número
    client = db.query(Client).filter(
        Client.user_id == config.user_id,
        Client.phone == from_number
    ).first()
    
    # Salvar mensagem
    chat_message = ChatMessage(
        user_id=config.user_id,
        client_id=client.id if client else None,
        sender_type="client",
        sender_name=client.name if client else from_number,
        sender_phone=from_number,
        message=body,
        message_type="text",
        is_from_whatsapp=True,
        whatsapp_message_id=message_sid
    )
    db.add(chat_message)
    db.commit()
    
    # Enviar notificação para o usuário (via SSE ou push notification)
    # TODO: Implementar notificação em tempo real
    
    return {"status": "ok"}


# ============================================
# CHAT HISTORY
# ============================================

@router.get("/conversations")
async def get_conversations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retorna lista de conversas (por cliente/número)"""
    # Agrupar mensagens por sender_phone
    from sqlalchemy import func
    
    conversations = db.query(
        ChatMessage.sender_phone,
        ChatMessage.sender_name,
        func.count(ChatMessage.id).label("message_count"),
        func.max(ChatMessage.created_at).label("last_message_at")
    ).filter(
        ChatMessage.user_id == current_user.id
    ).group_by(ChatMessage.sender_phone).all()
    
    result = []
    for conv in conversations:
        # Buscar última mensagem
        last_message = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id,
            ChatMessage.sender_phone == conv.sender_phone
        ).order_by(ChatMessage.created_at.desc()).first()
        
        # Buscar cliente
        client = db.query(Client).filter(
            Client.user_id == current_user.id,
            Client.phone == conv.sender_phone
        ).first()
        
        result.append({
            "phone": conv.sender_phone,
            "name": conv.sender_name or client.name if client else conv.sender_phone,
            "client_id": client.id if client else None,
            "unread_count": db.query(ChatMessage).filter(
                ChatMessage.user_id == current_user.id,
                ChatMessage.sender_phone == conv.sender_phone,
                ChatMessage.is_read == False,
                ChatMessage.sender_type == "client"
            ).count(),
            "last_message": last_message.message if last_message else None,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "message_count": conv.message_count
        })
    
    # Ordenar por última mensagem
    result.sort(key=lambda x: x["last_message_at"] or "", reverse=True)
    
    return {"conversations": result}


@router.get("/messages/{phone}")
async def get_messages(
    phone: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retorna mensagens de uma conversa específica"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id,
        ChatMessage.sender_phone == phone
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    # Marcar como lidas
    for msg in messages:
        if msg.sender_type == "client" and not msg.is_read:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
    db.commit()
    
    return {
        "messages": [msg.to_dict() for msg in reversed(messages)],
        "phone": phone
    }


# ============================================
# NOTIFICAÇÕES AUTOMÁTICAS
# ============================================

@router.post("/schedule-deadline-notifications")
async def schedule_deadline_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Agenda notificações automáticas de prazos"""
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id,
        WhatsAppConfig.is_active == True,
        WhatsAppConfig.auto_notify_deadlines == True
    ).first()
    
    if not config:
        return {"message": "Notificações automáticas desabilitadas"}
    
    now = datetime.utcnow()
    
    # Buscar prazos dos próximos 7 dias que ainda não foram notificados
    upcoming_deadlines = db.query(Deadline).filter(
        Deadline.user_id == current_user.id,
        Deadline.is_completed == False,
        Deadline.notification_sent == False,
        Deadline.due_date <= now + timedelta(days=7),
        Deadline.due_date >= now
    ).all()
    
    notifications_created = 0
    
    for deadline in upcoming_deadlines:
        # Verificar se cliente tem telefone
        if deadline.client_id:
            client = db.query(Client).filter(
                Client.id == deadline.client_id,
                Client.user_id == current_user.id
            ).first()
            
            if client and client.phone:
                days_until = (deadline.due_date - now).days
                
                # Criar mensagem
                if days_until == 0:
                    message = f"🔴 *ALERTA DE PRAZO*\n\nOlá {client.name}, o prazo para '{deadline.description}' vence *HOJE*!\n\nEntre em contato conosco urgentemente."
                elif days_until == 1:
                    message = f"⚠️ *Prazo Amanhã*\n\nOlá {client.name}, lembramos que '{deadline.description}' vence *AMANHÃ* ({deadline.due_date.strftime('%d/%m/%Y')})."
                else:
                    message = f"📅 *Lembrete de Prazo*\n\nOlá {client.name}, '{deadline.description}' vence em {days_until} dias ({deadline.due_date.strftime('%d/%m/%Y')})."
                
                # Agendar notificação
                notification = NotificationQueue(
                    user_id=current_user.id,
                    client_id=client.id,
                    target_phone=client.phone,
                    notification_type="deadline_reminder",
                    message=message,
                    related_id=deadline.id,
                    related_type="deadline",
                    scheduled_at=deadline.due_date - timedelta(days=1) if days_until > 1 else now
                )
                db.add(notification)
                notifications_created += 1
                
                # Marcar prazo como notificado
                deadline.notification_sent = True
    
    db.commit()
    
    return {
        "message": f"{notifications_created} notificações agendadas",
        "deadlines_processed": len(upcoming_deadlines),
        "notifications_created": notifications_created
    }


@router.post("/send-pending-notifications")
async def send_pending_notifications(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint para enviar notificações pendentes (chamado por cron)"""
    now = datetime.utcnow()
    
    # Buscar notificações pendentes
    pending = db.query(NotificationQueue).filter(
        NotificationQueue.status == "pending",
        NotificationQueue.scheduled_at <= now
    ).all()
    
    sent = 0
    failed = 0
    
    for notification in pending:
        # Buscar config do usuário
        config = db.query(WhatsAppConfig).filter(
            WhatsAppConfig.user_id == notification.user_id,
            WhatsAppConfig.is_active == True
        ).first()
        
        if not config:
            notification.status = "failed"
            notification.error_message = "WhatsApp não configurado"
            failed += 1
            continue
        
        try:
            # Enviar mensagem (usar a mesma lógica do send_whatsapp_message)
            # Simulação para desenvolvimento
            notification.status = "sent"
            notification.sent_at = now
            sent += 1
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            failed += 1
    
    db.commit()
    
    return {
        "processed": len(pending),
        "sent": sent,
        "failed": failed
    }
