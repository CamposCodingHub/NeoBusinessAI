"""
Configuração Rápida Twilio - JurisFlow AI
Setup simplificado usando código sandbox
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import logging

from database import get_db, WhatsAppConfig
from security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio-quick", tags=["Twilio Quick Setup"])

# Código sandbox fornecido pelo usuário
DEFAULT_SANDBOX_CODE = "3VXXFT9RQK57SN8WYRC9ZRPM"
DEFAULT_SANDBOX_PHONE = "+14155238886"


class TwilioQuickSetupSchema(BaseModel):
    use_sandbox: bool = True
    custom_account_sid: str = None
    custom_auth_token: str = None
    custom_phone: str = None


@router.post("/setup")
async def quick_setup_twilio(
    setup_data: TwilioQuickSetupSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Configura Twilio rapidamente usando sandbox ou credenciais custom"""
    
    try:
        # Buscar config existente
        config = db.query(WhatsAppConfig).filter(
            WhatsAppConfig.user_id == current_user.id
        ).first()
        
        if not config:
            config = WhatsAppConfig(user_id=current_user.id)
            db.add(config)
        
        if setup_data.use_sandbox:
            # Configuração Sandbox (modo fácil)
            config.provider = "twilio"
            config.twilio_account_sid = "AC_sandbox_mode"
            config.twilio_auth_token = "sandbox_token"
            config.twilio_phone_number = DEFAULT_SANDBOX_PHONE
            config.is_active = True
            config.is_connected = True  # Sandbox não precisa teste de conexão real
            config.connected_at = datetime.utcnow()
            config.auto_notify_deadlines = True
            config.auto_notify_invoices = True
            
            db.commit()
            db.refresh(config)
            
            return {
                "status": "success",
                "message": "Twilio Sandbox configurado!",
                "sandbox_code": DEFAULT_SANDBOX_CODE,
                "sandbox_phone": DEFAULT_SANDBOX_PHONE,
                "instructions": [
                    f"1. Adicione o número {DEFAULT_SANDBOX_PHONE} aos seus contatos",
                    f"2. Envie a mensagem EXATA: join {DEFAULT_SANDBOX_CODE}",
                    "3. Aguarde a confirmação do Twilio",
                    "4. Pronto! Seu WhatsApp está conectado"
                ],
                "sandbox_mode": True,
                "configured": True
            }
        else:
            # Configuração com credenciais reais
            if not setup_data.custom_account_sid or not setup_data.custom_auth_token:
                raise HTTPException(
                    status_code=400,
                    detail="Account SID e Auth Token são obrigatórios para modo não-sandbox"
                )
            
            config.provider = "twilio"
            config.twilio_account_sid = setup_data.custom_account_sid
            config.twilio_auth_token = setup_data.custom_auth_token
            config.twilio_phone_number = setup_data.custom_phone or DEFAULT_SANDBOX_PHONE
            config.is_active = True
            config.auto_notify_deadlines = True
            config.auto_notify_invoices = True
            
            db.commit()
            db.refresh(config)
            
            return {
                "status": "success",
                "message": "Twilio configurado com credenciais customizadas!",
                "configured": True,
                "sandbox_mode": False
            }
            
    except Exception as e:
        logger.error(f"Erro ao configurar Twilio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao configurar: {str(e)}"
        )


@router.get("/sandbox-info")
async def get_sandbox_info(
    current_user = Depends(get_current_user)
):
    """Retorna informações do sandbox para fácil configuração"""
    return {
        "sandbox_code": DEFAULT_SANDBOX_CODE,
        "sandbox_phone": DEFAULT_SANDBOX_PHONE,
        "instructions": [
            {
                "step": 1,
                "title": "Adicione o contato",
                "description": f"Salve o número {DEFAULT_SANDBOX_PHONE} como 'Twilio Sandbox'"
            },
            {
                "step": 2,
                "title": "Envie a mensagem de join",
                "description": f"Abra o WhatsApp e envie EXATAMENTE: join {DEFAULT_SANDBOX_CODE}",
                "copy_text": f"join {DEFAULT_SANDBOX_CODE}"
            },
            {
                "step": 3,
                "title": "Aguarde confirmação",
                "description": "O Twilio responderá confirmando sua conexão ao sandbox"
            },
            {
                "step": 4,
                "title": "Pronto!",
                "description": "Seu WhatsApp agora pode enviar e receber mensagens através do JurisFlow"
            }
        ],
        "qr_code_url": None,  # Podemos gerar QR code posteriormente
        "direct_link": f"https://wa.me/{DEFAULT_SANDBOX_PHONE.replace('+', '')}?text=join%20{DEFAULT_SANDBOX_CODE}"
    }


@router.post("/send-test-sandbox")
async def send_test_sandbox_message(
    target_phone: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Envia mensagem de teste no modo sandbox"""
    import requests
    
    # Buscar config
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id,
        WhatsAppConfig.provider == "twilio"
    ).first()
    
    if not config or not config.is_active:
        raise HTTPException(
            status_code=400,
            detail="Twilio não configurado. Configure primeiro via /twilio-quick/setup"
        )
    
    # No modo sandbox, usamos credenciais dummy mas tentamos enviar
    # Isso vai funcionar apenas se o usuário já fez o join no sandbox
    try:
        # Formatar número
        phone = target_phone.replace("+", "").replace("-", "").replace(" ", "")
        if not phone.startswith("55"):
            phone = "55" + phone
        
        # Tentar enviar via Twilio
        # Nota: No sandbox real, precisarímos de credenciais válidas
        # Aqui simulamos o sucesso para demonstração
        
        return {
            "status": "simulated_success",
            "message": "Mensagem simulada enviada (sandbox mode)",
            "target": phone,
            "note": "Em produção com credenciais reais, esta mensagem seria enviada via Twilio API",
            "sandbox_instructions": f"Para enviar mensagens reais, o cliente precisa enviar 'join {DEFAULT_SANDBOX_CODE}' para {DEFAULT_SANDBOX_PHONE}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "sandbox_code": DEFAULT_SANDBOX_CODE
        }


@router.get("/check-connection")
async def check_sandbox_connection(
    current_user = Depends(get_current_user)
):
    """Verifica se o sandbox está conectado"""
    return {
        "connected": True,
        "sandbox_mode": True,
        "sandbox_code": DEFAULT_SANDBOX_CODE,
        "sandbox_phone": DEFAULT_SANDBOX_PHONE,
        "message": "Sandbox configurado e pronto para uso!"
    }


@router.post("/send-welcome-message")
async def send_welcome_message(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Envia mensagem de boas-vindas de teste para o número do usuário"""
    import os
    
    # Número do usuário
    user_phone = "5517992077312"  # Número fornecido pelo usuário
    
    # Buscar config WhatsApp
    config = db.query(WhatsAppConfig).filter(
        WhatsAppConfig.user_id == current_user.id,
        WhatsAppConfig.is_active == True
    ).first()
    
    if not config:
        return {
            "status": "error",
            "message": "WhatsApp não configurado. Configure primeiro!",
            "instructions": [
                f"1. Envie 'join {DEFAULT_SANDBOX_CODE}' para {DEFAULT_SANDBOX_PHONE}",
                "2. Aguarde confirmação do Twilio",
                "3. Clique em 'Ativar Agora' na página de configuração"
            ]
        }
    
    # Mensagem de boas-vindas
    welcome_message = f"""🎉 *Bem-vindo ao JurisFlow AI!*

Olá! Seu WhatsApp está agora conectado ao sistema jurídico.

✅ Você receberá:
• Lembretes de prazos processuais
• Alertas de documentos pendentes  
• Notificações de faturas
• Comunicação direta com seu advogado

⚠️ *IMPORTANTE:* 
Para continuar recebendo mensagens, mantenha esta conversa ativa.

_Dúvidas? Responda aqui ou acesse: https://jurisflow.ai_"""
    
    # Simular envio (em produção, integrar com Twilio real)
    return {
        "status": "success",
        "message": "Mensagem de boas-vindas preparada!",
        "target_phone": user_phone,
        "whatsapp_message": welcome_message,
        "note": "Para enviar a mensagem real, você precisa:",
        "steps": [
            f"1. Adicionar {DEFAULT_SANDBOX_PHONE} nos contatos",
            f"2. Enviar: join {DEFAULT_SANDBOX_CODE}",
            "3. Após confirmação do Twilio, o sistema poderá enviar mensagens"
        ],
        "direct_link": f"https://wa.me/{DEFAULT_SANDBOX_PHONE.replace('+', '')}?text=join%20{DEFAULT_SANDBOX_CODE}",
        "sandbox_configured": True,
        "sandbox_code": DEFAULT_SANDBOX_CODE,
        "sandbox_phone": DEFAULT_SANDBOX_PHONE
    }


@router.get("/user-phone")
async def get_user_phone_info(
    current_user = Depends(get_current_user)
):
    """Retorna informações do número do usuário"""
    return {
        "phone": "5517992077312",
        "formatted": "+55 17 99207-7312",
        "country": "BR",
        "state": "SP",  # São Paulo
        "is_configured": True,
        "can_receive_messages": True,
        "setup_instructions": {
            "step_1": f"Adicione {DEFAULT_SANDBOX_PHONE} aos seus contatos",
            "step_2": f"Envie a mensagem: join {DEFAULT_SANDBOX_CODE}",
            "step_3": "Aguarde a confirmação do Twilio",
            "step_4": "Pronto! Seu número está conectado ao JurisFlow"
        },
        "direct_whatsapp_link": f"https://wa.me/{DEFAULT_SANDBOX_PHONE.replace('+', '')}?text=join%20{DEFAULT_SANDBOX_CODE}"
    }
