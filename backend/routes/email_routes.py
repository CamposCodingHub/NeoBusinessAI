"""
Rotas API para Integração com Email - LexScan IA
Endpoints para gerenciar contas de email e processar mensagens
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

from tools.email_integration import (
    email_manager, EmailAccount, EmailMessage,
    EmailIntegrationManager
)
from tools.security import encrypt_credential, decrypt_credential

router = APIRouter(prefix="/api/email", tags=["email"])


# ============================================
# MODELOS Pydantic
# ============================================

class EmailAccountCreate(BaseModel):
    user_id: int
    email_address: EmailStr
    password: str
    provider: Optional[str] = None  # auto-detect if not provided
    imap_server: Optional[str] = None
    imap_port: Optional[int] = 993
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = 587


class EmailAccountResponse(BaseModel):
    id: int
    email_address: str
    provider: str
    is_active: bool
    last_sync: Optional[str]
    created_at: Optional[str]


class EmailTestRequest(BaseModel):
    email_address: EmailStr
    password: str
    provider: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: int = 993
    smtp_server: Optional[str] = None
    smtp_port: int = 587


class EmailTestResponse(BaseModel):
    success: bool
    message: str
    detected_provider: Optional[str] = None


class EmailMessageResponse(BaseModel):
    id: str
    subject: str
    sender: str
    sender_name: str
    date: str
    body_preview: str
    summary: str
    urgency_score: float
    is_important: bool
    is_read: bool
    category: str
    action_items: List[str]


class EmailSyncRequest(BaseModel):
    account_id: int
    folder: str = "INBOX"
    limit: int = 50
    since_hours: Optional[int] = 24
    unread_only: bool = False


class EmailSendRequest(BaseModel):
    account_id: int
    to: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None


class EmailAnalyticsResponse(BaseModel):
    total_emails: int
    legal_emails: int
    urgent_emails: int
    unread_count: int
    categories: Dict[str, int]
    daily_stats: List[Dict]


class DailySummaryRequest(BaseModel):
    account_id: int
    hours: int = 24


class DailySummaryResponse(BaseModel):
    summary: str
    generated_at: str
    total_processed: int
    important_found: int


# ============================================
# ENDPOINTS
# ============================================

@router.post("/test-connection", response_model=EmailTestResponse)
async def test_email_connection(request: EmailTestRequest):
    """
    Testa a conexão com servidor de email
    Não salva nada, apenas verifica se as credenciais funcionam
    """
    try:
        # Detectar provedor se não especificado
        provider = request.provider
        if not provider:
            provider = email_manager.detect_provider(request.email_address)
        
        # Obter configurações do provedor
        settings = email_manager.get_provider_settings(provider)
        
        # Criar conta temporária para teste
        account = EmailAccount(
            id=0,  # Temporário
            user_id=0,
            email_address=request.email_address,
            provider=provider,
            imap_server=request.imap_server or settings['imap_server'],
            imap_port=request.imap_port or settings['imap_port'],
            smtp_server=request.smtp_server or settings['smtp_server'],
            smtp_port=request.smtp_port or settings['smtp_port'],
            username=request.email_address,  # Geralmente email = username
            password=request.password
        )
        
        # Testar conexão
        success, message = email_manager.test_connection(account)
        
        return EmailTestResponse(
            success=success,
            message=message,
            detected_provider=provider
        )
        
    except Exception as e:
        return EmailTestResponse(
            success=False,
            message=f"Erro ao testar conexão: {str(e)}",
            detected_provider=None
        )


@router.post("/accounts", response_model=EmailAccountResponse)
async def create_email_account(account: EmailAccountCreate):
    """
    Configura uma nova conta de email para integração
    """
    try:
        # Detectar provedor se não especificado
        provider = account.provider
        if not provider:
            provider = email_manager.detect_provider(account.email_address)
        
        # Obter configurações
        settings = email_manager.get_provider_settings(provider)
        
        # SECURITY: Encrypt password before saving
        encrypted_password = encrypt_credential(account.password)
        
        # Criar no banco de dados (implementação depende do database.py)
        # Aqui simulamos a criação
        new_account = EmailAccount(
            id=1,  # Simulado
            user_id=account.user_id,
            email_address=account.email_address,
            provider=provider,
            imap_server=account.imap_server or settings['imap_server'],
            imap_port=account.imap_port or settings['imap_port'],
            smtp_server=account.smtp_server or settings['smtp_server'],
            smtp_port=account.smtp_port or settings['smtp_port'],
            username=account.email_address,
            password=encrypted_password,  # ✅ Senha criptografada AES-256
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        return EmailAccountResponse(
            id=new_account.id,
            email_address=new_account.email_address,
            provider=new_account.provider,
            is_active=new_account.is_active,
            last_sync=None,
            created_at=new_account.created_at.isoformat() if new_account.created_at else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar conta: {str(e)}")


@router.get("/accounts", response_model=List[EmailAccountResponse])
async def list_email_accounts(user_id: int):
    """
    Lista todas as contas de email configuradas para um usuário
    """
    # Simulação - em produção consultaria o banco
    accounts = [
        EmailAccountResponse(
            id=1,
            email_address="advogado@escritorio.com.br",
            provider="corporate",
            is_active=True,
            last_sync="2024-05-02T15:30:00",
            created_at="2024-04-01T10:00:00"
        )
    ]
    return accounts


@router.delete("/accounts/{account_id}")
async def delete_email_account(account_id: int, user_id: int):
    """
    Remove uma conta de email
    """
    try:
        # Verificar se conta pertence ao usuário
        # Remover do banco
        # Fechar conexões abertas
        
        return {
            "success": True,
            "message": "Conta de email removida com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync", response_model=List[EmailMessageResponse])
async def sync_emails(request: EmailSyncRequest):
    """
    Sincroniza emails da caixa de entrada
    Busca emails novos e processa com IA
    """
    try:
        # Simulação - em produção buscaria conta do banco
        account = EmailAccount(
            id=request.account_id,
            user_id=1,
            email_address="advogado@escritorio.com.br",
            provider="corporate",
            imap_server="mail.escritorio.com.br",
            imap_port=993,
            smtp_server="smtp.escritorio.com.br",
            smtp_port=587,
            username="advogado@escritorio.com.br",
            password="password123"  # Simulado
        )
        
        # Calcular data de corte
        since = None
        if request.since_hours:
            since = datetime.utcnow() - __import__('datetime').timedelta(hours=request.since_hours)
        
        # Buscar emails
        emails = email_manager.fetch_emails(
            account=account,
            folder=request.folder,
            limit=request.limit,
            since=since,
            unread_only=request.unread_only
        )
        
        # Processar com IA
        analyzed_emails = []
        for email_msg in emails:
            analyzed = email_manager.analyze_email_with_ai(email_msg)
            analyzed_emails.append(analyzed)
        
        # Converter para resposta
        response = []
        for email_msg in analyzed_emails:
            response.append(EmailMessageResponse(
                id=email_msg.id,
                subject=email_msg.subject,
                sender=email_msg.sender,
                sender_name=email_msg.sender_name,
                date=email_msg.date.isoformat() if email_msg.date else "",
                body_preview=email_msg.body_text[:200] + "..." if len(email_msg.body_text) > 200 else email_msg.body_text,
                summary=email_msg.summary,
                urgency_score=email_msg.urgency_score,
                is_important=email_msg.is_important,
                is_read=email_msg.is_read,
                category=email_msg.category,
                action_items=email_msg.action_items or []
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sincronização: {str(e)}")


@router.get("/important/{account_id}", response_model=List[EmailMessageResponse])
async def get_important_emails(account_id: int, hours: int = 24):
    """
    Retorna emails importantes identificados pela IA
    Urgência > 0.7 ou categorizados como 'legal'
    """
    try:
        # Simulação
        important = [
            EmailMessageResponse(
                id="1",
                subject="Prazo para Contestação - Processo nº 12345-67.2024.8.26.0001",
                sender="sistema@tjsp.jus.br",
                sender_name="TJSP - Sistema Processual",
                date="2024-05-02T14:20:00",
                body_preview="Senhor Advogado, Vossa Excelência foi intimado para apresentar contestação...",
                summary="Intimação eletrônica com prazo de 15 dias para contestação.",
                urgency_score=0.95,
                is_important=True,
                is_read=False,
                category="legal",
                action_items=["Verificar autos", "Preparar contestação", "Agendar prazo"]
            ),
            EmailMessageResponse(
                id="2",
                subject="Reunião de caso - João Silva vs Empresa ABC",
                sender="cliente@email.com",
                sender_name="João Silva",
                date="2024-05-02T10:15:00",
                body_preview="Prezado Dr., Gostaria de agendar uma reunião...",
                summary="Cliente solicitando reunião para discutir andamento do processo.",
                urgency_score=0.6,
                is_important=True,
                is_read=False,
                category="client",
                action_items=["Agendar reunião", "Preparar relatório"]
            )
        ]
        return important
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_email(request: EmailSendRequest):
    """
    Envia um email usando a conta configurada
    """
    try:
        # Simulação
        return {
            "success": True,
            "message": "Email enviado com sucesso",
            "message_id": "msg_123456"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar email: {str(e)}")


@router.post("/daily-summary", response_model=DailySummaryResponse)
async def generate_daily_summary(request: DailySummaryRequest):
    """
    Gera um resumo diário dos emails com análise de IA
    """
    try:
        # Simulação de conta
        account = EmailAccount(
            id=request.account_id,
            user_id=1,
            email_address="advogado@escritorio.com.br",
            provider="corporate",
            imap_server="mail.escritorio.com.br",
            imap_port=993,
            smtp_server="smtp.escritorio.com.br",
            smtp_port=587,
            username="advogado@escritorio.com.br",
            password="password123"
        )
        
        # Buscar emails importantes
        emails = email_manager.get_important_emails(account, hours=request.hours)
        
        # Gerar resumo
        summary = email_manager.generate_daily_summary(account, emails)
        
        return DailySummaryResponse(
            summary=summary,
            generated_at=datetime.utcnow().isoformat(),
            total_processed=len(emails),
            important_found=len([e for e in emails if e.is_important or e.urgency_score > 0.7])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")


@router.get("/analytics/{account_id}", response_model=EmailAnalyticsResponse)
async def get_email_analytics(
    account_id: int,
    days: int = 7
):
    """
    Retorna estatísticas de uso e análises
    """
    try:
        # Simulação de analytics
        return EmailAnalyticsResponse(
            total_emails=147,
            legal_emails=32,
            urgent_emails=8,
            unread_count=12,
            categories={
                "legal": 32,
                "client": 28,
                "internal": 41,
                "other": 46
            },
            daily_stats=[
                {"date": "2024-04-26", "total": 18, "legal": 4, "urgent": 1},
                {"date": "2024-04-27", "total": 22, "legal": 5, "urgent": 2},
                {"date": "2024-04-28", "total": 15, "legal": 3, "urgent": 0},
                {"date": "2024-04-29", "total": 25, "legal": 6, "urgent": 2},
                {"date": "2024-04-30", "total": 28, "legal": 7, "urgent": 2},
                {"date": "2024-05-01", "total": 20, "legal": 4, "urgent": 0},
                {"date": "2024-05-02", "total": 19, "legal": 3, "urgent": 1}
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-read/{account_id}")
async def mark_email_as_read(account_id: int, message_id: str):
    """
    Marca um email específico como lido no servidor
    """
    try:
        return {
            "success": True,
            "message": "Email marcado como lido"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_supported_providers():
    """
    Lista os provedores de email suportados e suas configurações
    """
    return {
        "providers": [
            {
                "id": "gmail",
                "name": "Gmail / Google Workspace",
                "settings": {
                    "imap_server": "imap.gmail.com",
                    "imap_port": 993,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587
                },
                "auth_notes": "Use App Password, não senha normal"
            },
            {
                "id": "outlook",
                "name": "Outlook / Microsoft 365",
                "settings": {
                    "imap_server": "outlook.office365.com",
                    "imap_port": 993,
                    "smtp_server": "smtp.office365.com",
                    "smtp_port": 587
                },
                "auth_notes": "Suporta OAuth2 ou senha normal"
            },
            {
                "id": "yahoo",
                "name": "Yahoo Mail",
                "settings": {
                    "imap_server": "imap.mail.yahoo.com",
                    "imap_port": 993,
                    "smtp_server": "smtp.mail.yahoo.com",
                    "smtp_port": 587
                },
                "auth_notes": "Use App Password"
            },
            {
                "id": "icloud",
                "name": "iCloud Mail",
                "settings": {
                    "imap_server": "imap.mail.me.com",
                    "imap_port": 993,
                    "smtp_server": "smtp.mail.me.com",
                    "smtp_port": 587
                },
                "auth_notes": "Gere senha específica para app"
            },
            {
                "id": "corporate",
                "name": "Servidor Corporativo",
                "settings": {
                    "custom": True
                },
                "auth_notes": "Configure IMAP/SMTP manualmente"
            }
        ]
    }


# ============================================
# AGENDAMENTO AUTOMÁTICO (para implementar com celery/APScheduler)
# ============================================

"""
TODO: Implementar agendamento para:
1. Sincronização automática a cada 15 minutos
2. Resumo diário às 7h da manhã
3. Alertas de emails urgentes em tempo real

Exemplo com APScheduler:

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', minutes=15)
def sync_all_emails():
    # Buscar todas as contas ativas
    # Sincronizar cada uma
    # Enviar alertas de urgentes
    pass

@scheduler.scheduled_job('cron', hour=7, minute=0)
def send_daily_summaries():
    # Gerar resumos para todos os usuários
    # Enviar por email
    pass

scheduler.start()
"""
