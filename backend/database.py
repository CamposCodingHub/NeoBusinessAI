"""
Configuração do Banco de Dados PostgreSQL - LexScan IA
SQLAlchemy ORM para persistência de dados
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool

# Importar configuração validada
from config import settings

# Base declarativa
Base = declarative_base()
logger = logging.getLogger(__name__)

# Configuração da conexão - PostgreSQL obrigatório
DATABASE_URL = settings.DATABASE_URL
ACTIVE_DATABASE_URL = DATABASE_URL
LOCAL_SQLITE_PATH = (Path(__file__).resolve().parent.parent / "neobusiness_local.db").as_posix()


def _create_sqlite_engine(sqlite_url: str):
    return create_engine(
        sqlite_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )


def _create_primary_engine(database_url: str):
    if database_url.startswith('sqlite'):
        return _create_sqlite_engine(database_url)
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
        connect_args={"client_encoding": "utf8"}
    )

# Engine com pool de conexões - PostgreSQL apenas
# Para SQLite em testes, não usar connect_args
engine = _create_primary_engine(DATABASE_URL)

if not DATABASE_URL.startswith('sqlite') and settings.ENVIRONMENT != 'production':
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Banco PostgreSQL validado com sucesso.")
    except Exception as exc:
        ACTIVE_DATABASE_URL = f"sqlite:///{LOCAL_SQLITE_PATH}"
        logger.warning(
            "Falha ao conectar no PostgreSQL configurado. Ativando fallback SQLite local em desenvolvimento. Erro: %s",
            exc,
        )
        engine = _create_sqlite_engine(ACTIVE_DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================
# MODELOS
# ============================================

class User(Base):
    """Usuário do sistema"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    firebase_uid = Column(String(128), unique=True, index=True)
    password_hash = Column(String(255))  # Senha criptografada
    name = Column(String(255))
    company = Column(String(255))
    phone = Column(String(50))
    role = Column(String(50), default='user')  # user, premium, enterprise, admin
    plan_tier = Column(String(50), default='free')
    subscription_status = Column(String(50), default='inactive')
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    documents_limit = Column(Integer, default=5)
    users_limit = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True, server_default='true')
    
    # Relacionamentos
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.is_active is None:
            self.is_active = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'company': self.company,
            'plan_tier': self.plan_tier,
            'subscription_status': self.subscription_status,
            'documents_limit': self.documents_limit,
            'users_limit': self.users_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }


class Document(Base):
    """Documento do usuário"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    title = Column(String(255))
    content = Column(JSON)
    custom_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy reserved word
    status = Column(String(50), default='uploaded')  # uploaded, processing, completed, error
    # Partes (JSON)
    parties = Column(JSON)
    
    # Dados extraídos (JSON)
    deadlines = Column(JSON)
    values = Column(JSON)
    dates = Column(JSON)
    
    # Análises
    summary = Column(Text)
    analysis = Column(Text)
    key_points = Column(JSON)
    risks = Column(JSON)
    recommendations = Column(JSON)
    
    # Metadados
    processing_time_ms = Column(Integer)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relacionamentos
    owner = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.deadlines is None:
            self.deadlines = []
        if self.values is None:
            self.values = []
        if self.dates is None:
            self.dates = []
        if self.parties is None:
            self.parties = {}
        if self.key_points is None:
            self.key_points = []
        if self.risks is None:
            self.risks = []
        if self.recommendations is None:
            self.recommendations = []


class LegalDocument(Base):
    """Peça jurídica gerada"""
    __tablename__ = 'legal_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    piece_type = Column(String(100), nullable=False)  # peticao_inicial, contestacao, etc
    jurisdiction = Column(String(50), nullable=False)  # civel, trabalhista, tributario
    parties = Column(Text)
    facts = Column(Text)
    requests = Column(Text)
    additional_context = Column(Text)
    content = Column(Text)
    status = Column(String(50), default='generating')  # generating, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime)
    
    user = relationship("User")
    document = relationship("Document")
    
    def to_dict(self, include_text: bool = False) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'document_id': self.document_id,
            'piece_type': self.piece_type,
            'jurisdiction': self.jurisdiction,
            'parties': self.parties,
            'facts': self.facts,
            'requests': self.requests,
            'additional_context': self.additional_context,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
        }
        
        if include_text:
            result['content'] = self.content
        
        return result


class ChatMessage(Base):
    """Mensagens de chat"""
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    
    role = Column(String(20), nullable=True)  # 'user' ou 'assistant'
    content = Column(Text, nullable=True)
    context_used = Column(JSON, default=dict)
    confidence = Column(Float)
    sender_type = Column(String(20), default='user')
    sender_name = Column(String(255))
    sender_phone = Column(String(50), index=True)
    message = Column(Text, nullable=True)
    message_type = Column(String(50), default='text')
    media_url = Column(String(500))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    is_from_whatsapp = Column(Boolean, default=False)
    whatsapp_message_id = Column(String(255))
    context_type = Column(String(50))
    context_id = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    document = relationship("Document", back_populates="chat_messages")

    def __init__(self, **kwargs):
        message = kwargs.get('message')
        content = kwargs.get('content')
        sender_type = kwargs.get('sender_type')
        role = kwargs.get('role')

        if message and not content:
            kwargs['content'] = message
        if content and not message:
            kwargs['message'] = content
        if sender_type and not role:
            kwargs['role'] = sender_type

        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'client_id': self.client_id,
            'role': self.role,
            'content': self.content,
            'message': self.message or self.content,
            'sender_type': self.sender_type,
            'sender_name': self.sender_name,
            'sender_phone': self.sender_phone,
            'message_type': self.message_type,
            'media_url': self.media_url,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_from_whatsapp': self.is_from_whatsapp,
            'whatsapp_message_id': self.whatsapp_message_id,
            'context_type': self.context_type,
            'context_id': self.context_id,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class LegalKnowledgeSource(Base):
    """Fonte versionada da base juridica soberana."""

    __tablename__ = "legal_knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    source_key = Column(String(160), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(80), nullable=False, index=True)
    authority = Column(String(255), index=True)
    jurisdiction = Column(String(160), index=True)
    legal_area = Column(String(120), index=True)
    url = Column(String(1000))
    status = Column(String(50), default="active", nullable=False, index=True)
    content_hash = Column(String(64), index=True)
    custom_data = Column(JSON, default=dict)
    last_collected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LegalKnowledgeChunk(Base):
    """Trecho citavel usado pela busca lexical e semantica."""

    __tablename__ = "legal_knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(
        Integer,
        ForeignKey("legal_knowledge_sources.id"),
        nullable=False,
        index=True,
    )
    external_id = Column(String(255), index=True)
    ordinal = Column(Integer, default=0, nullable=False)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    normalized_content = Column(Text, nullable=False)
    embedding = Column(JSON)
    embedding_model = Column(String(160))
    token_count = Column(Integer)
    citation = Column(String(1000))
    court = Column(String(80), index=True)
    legal_area = Column(String(120), index=True)
    document_date = Column(DateTime, index=True)
    custom_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("LegalKnowledgeSource")


class AIInferenceEvent(Base):
    """Auditoria tecnica e financeira de cada tentativa de inferencia."""

    __tablename__ = "ai_inference_events"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    conversation_id = Column(String(128), index=True)
    provider = Column(String(80), nullable=False, index=True)
    endpoint = Column(String(500))
    route = Column(String(80), index=True)
    requested_model = Column(String(160), index=True)
    actual_model = Column(String(160), index=True)
    status = Column(String(50), nullable=False, index=True)
    error_code = Column(String(80), index=True)
    error_message = Column(Text)
    latency_ms = Column(Integer)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0)
    fallback_used = Column(Boolean, default=False)
    custom_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AIEvaluationRun(Base):
    """Resultado versionado dos benchmarks de promocao de modelos."""

    __tablename__ = "ai_evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    dataset_name = Column(String(160), nullable=False, index=True)
    dataset_version = Column(String(80), nullable=False)
    candidate_provider = Column(String(80), nullable=False)
    candidate_model = Column(String(160), nullable=False)
    baseline_provider = Column(String(80))
    baseline_model = Column(String(160))
    status = Column(String(50), nullable=False, index=True)
    score = Column(Float, default=0)
    metrics = Column(JSON, default=dict)
    results = Column(JSON, default=list)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AIResearchJob(Base):
    """Pesquisa profunda executada fora do ciclo HTTP."""

    __tablename__ = "ai_research_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(String(128), index=True)
    task_id = Column(String(64), index=True)
    status = Column(String(50), default="queued", nullable=False, index=True)
    progress = Column(Integer, default=0)
    stage = Column(String(80), default="queued")
    query = Column(Text, nullable=False)
    document_context = Column(Text)
    jurisdiction = Column(String(160), default="Brasil - federal")
    legal_area = Column(String(120))
    requested_model = Column(String(160))
    actual_model = Column(String(160))
    provider = Column(String(80))
    result = Column(Text)
    result_metadata = Column(JSON, default=dict)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class FineTuningExample(Base):
    """Exemplo juridico revisavel para especializacao futura do modelo."""

    __tablename__ = "fine_tuning_examples"

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    source_type = Column(String(80), nullable=False, index=True)
    domain = Column(String(120), nullable=False, index=True)
    instruction = Column(Text, nullable=False)
    input_text = Column(Text, default="")
    output_text = Column(Text, nullable=False)
    citations = Column(JSON, default=list)
    custom_data = Column(JSON, default=dict)
    review_status = Column(String(50), default="pending", index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_notes = Column(Text)
    quality_score = Column(Float)
    dataset_split = Column(String(20), default="train", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)


class Deadline(Base):
    """Prazo processual (denormalizado para queries rápidas)"""
    __tablename__ = 'deadlines'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    days = Column(Integer)
    due_date = Column(DateTime)
    urgency = Column(String(20))  # 'high', 'medium', 'low'
    context = Column(String(500))
    description = Column(Text)
    
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'document_id': self.document_id,
            'days': self.days,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'urgency': self.urgency,
            'context': self.context,
            'description': self.description,
            'is_completed': self.is_completed,
            'notification_sent': self.notification_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Notification(Base):
    """Notificações enviadas"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    type = Column(String(50))  # 'email', 'sms', 'push'
    subject = Column(String(500))
    content = Column(Text)
    recipient = Column(String(255))
    
    status = Column(String(50), default='pending')  # 'pending', 'sent', 'failed'
    sent_at = Column(DateTime)
    error_message = Column(Text)
    
    # Para notificações de prazos
    deadline_id = Column(Integer, ForeignKey('deadlines.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")


class ActivityLog(Base):
    """Log de atividades (auditoria)"""
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    action = Column(String(100), nullable=False)  # 'upload', 'delete', 'chat', 'export', etc.
    resource_type = Column(String(50))  # 'document', 'user', 'subscription'
    resource_id = Column(Integer)
    
    details = Column(JSON, default=dict)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SubscriptionHistory(Base):
    """Histórico de assinaturas"""
    __tablename__ = 'subscription_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    plan_tier = Column(String(50))
    price_paid_cents = Column(Integer)
    currency = Column(String(3), default='BRL')
    
    status = Column(String(50))  # 'active', 'cancelled', 'expired'
    started_at = Column(DateTime)
    ends_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    stripe_subscription_id = Column(String(255))
    stripe_invoice_id = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Client(Base):
    """Cliente do escritório"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Dados do cliente (com índices para busca rápida)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(255))  # Criptografado
    cpf_cnpj = Column(String(255))  # Criptografado
    
    # Endereço
    address = Column(Text)  # Criptografado
    city = Column(String(100), index=True)
    state = Column(String(50), index=True)
    zip_code = Column(String(255))  # Criptografado
    
    # Dados adicionais (com índices para filtros comuns)
    notes = Column(Text)
    status = Column(String(50), default='active', index=True)  # active, inactive, prospect
    
    # Régua de cobrança
    payment_day = Column(Integer, default=10)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Retorna dict com dados descriptografados"""
        from security.encryption import decrypt_field
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': decrypt_field(self.phone),
            'cpf_cnpj': decrypt_field(self.cpf_cnpj),
            'address': decrypt_field(self.address),
            'city': self.city,
            'state': self.state,
            'zip_code': decrypt_field(self.zip_code),
            'status': self.status,
            'payment_day': self.payment_day,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def set_sensitive_data(self, **kwargs):
        """Define dados sensíveis com criptografia"""
        from security.encryption import encrypt_field
        if 'phone' in kwargs:
            self.phone = encrypt_field(kwargs['phone'])
        if 'cpf_cnpj' in kwargs:
            self.cpf_cnpj = encrypt_field(kwargs['cpf_cnpj'])
        if 'address' in kwargs:
            self.address = encrypt_field(kwargs['address'])
        if 'zip_code' in kwargs:
            self.zip_code = encrypt_field(kwargs['zip_code'])


class Invoice(Base):
    """Fatura/Cobrança do cliente"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    
    # Dados da fatura
    invoice_number = Column(String(50), unique=True)
    description = Column(String(500))
    
    # Valores
    amount_cents = Column(Integer, nullable=False)  # Valor em centavos
    discount_cents = Column(Integer, default=0)
    total_cents = Column(Integer, nullable=False)
    
    # Status
    status = Column(String(50), default='pending')  # pending, paid, overdue, cancelled
    
    # Datas
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime)
    
    # Tipo de cobrança
    invoice_type = Column(String(50), default='monthly')  # monthly, success_fee, service
    
    # Processo vinculado (se for êxito)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    # Método de pagamento
    payment_method = Column(String(50))  # boleto, pix, credit_card
    payment_reference = Column(String(255))  # Código do boleto/pix
    
    # Régua de cobrança
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'invoice_number': self.invoice_number,
            'description': self.description,
            'amount': self.amount_cents / 100,
            'discount': self.discount_cents / 100,
            'total': self.total_cents / 100,
            'status': self.status,
            'invoice_type': self.invoice_type,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'payment_method': self.payment_method,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WhatsAppConfig(Base):
    """Configuração de integração WhatsApp"""
    __tablename__ = 'whatsapp_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Provider: twilio, evolution_api, wppconnect, etc.
    provider = Column(String(50), default='twilio')
    
    # Configurações Twilio
    twilio_account_sid = Column(String(255))
    twilio_auth_token = Column(String(255))
    twilio_phone_number = Column(String(50))  # +5511999999999
    
    # Configurações Evolution API
    evolution_api_url = Column(String(255))
    evolution_api_key = Column(String(255))
    evolution_instance = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=False)
    connected_at = Column(DateTime)
    
    # Configurações de notificação automática
    auto_notify_deadlines = Column(Boolean, default=True)
    auto_notify_invoices = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context_type = Column(String(50))  # deadline, invoice, document, general
    context_id = Column(Integer)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'twilio_phone_number': self.twilio_phone_number,
            'evolution_api_url': self.evolution_api_url,
            'evolution_instance': self.evolution_instance,
            'is_active': self.is_active,
            'is_connected': self.is_connected,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'auto_notify_deadlines': self.auto_notify_deadlines,
            'auto_notify_invoices': self.auto_notify_invoices,
            'context_type': self.context_type,
            'context_id': self.context_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationQueue(Base):
    """Fila de notificações automáticas"""
    __tablename__ = 'notification_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Target
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    target_phone = Column(String(50), nullable=False)
    
    # Conteúdo
    notification_type = Column(String(50))  # deadline_reminder, invoice_reminder, deadline_alert
    message = Column(Text, nullable=False)
    
    # Status
    status = Column(String(50), default='pending')  # pending, sent, failed, cancelled
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    error_message = Column(String(500))
    
    # Contexto
    related_id = Column(Integer)  # ID do prazo/fatura relacionado
    related_type = Column(String(50))  # deadline, invoice
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# FUNÇÕES UTILITÁRIAS
# ============================================

@contextmanager
def get_db():
    """Context manager para sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# FastAPI async dependency - use this with Depends()
async def get_db_async():
    """Async dependency for FastAPI. Use: db: Session = Depends(get_db_async)"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    """Sync dependency for FastAPI. Use: db: Session = Depends(get_db)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def db_session():
    """Context manager para scripts, tarefas e utilitarios locais."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _apply_sqlite_development_migrations():
    """Ajustes de schema para ambientes locais SQLite."""
    if not ACTIVE_DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = connection.exec_driver_sql("PRAGMA table_info(deadlines)").fetchall()
        if not columns:
            return

        document_column = next((column for column in columns if column[1] == "document_id"), None)
        if not document_column or document_column[3] == 0:
            return

        logger.info(
            "Aplicando migracao local SQLite: liberando document_id opcional na tabela deadlines."
        )
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql(
            """
            CREATE TABLE deadlines_new (
                id INTEGER NOT NULL PRIMARY KEY,
                document_id INTEGER,
                user_id INTEGER NOT NULL,
                days INTEGER,
                due_date DATETIME,
                urgency VARCHAR(20),
                context VARCHAR(500),
                description TEXT,
                is_completed BOOLEAN,
                completed_at DATETIME,
                notification_sent BOOLEAN,
                notification_sent_at DATETIME,
                created_at DATETIME,
                FOREIGN KEY(document_id) REFERENCES documents (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO deadlines_new (
                id, document_id, user_id, days, due_date, urgency, context,
                description, is_completed, completed_at, notification_sent,
                notification_sent_at, created_at
            )
            SELECT
                id, document_id, user_id, days, due_date, urgency, context,
                description, is_completed, completed_at, notification_sent,
                notification_sent_at, created_at
            FROM deadlines
            """
        )
        connection.exec_driver_sql("DROP TABLE deadlines")
        connection.exec_driver_sql("ALTER TABLE deadlines_new RENAME TO deadlines")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def init_db():
    """Inicializa o banco de dados (cria tabelas)"""
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_development_migrations()
    print("Banco de dados inicializado com sucesso!")


def drop_db():
    """Remove todas as tabelas (cuidado!)"""
    Base.metadata.drop_all(bind=engine)
    print("Todas as tabelas foram removidas")


def reset_db():
    """Reset completo do banco (cuidado!)"""
    drop_db()
    init_db()


# ============================================
# OPERAÇÕES CRUD - USERS
# ============================================

def create_user(db: Session, email: str, firebase_uid: str = None, name: str = None) -> User:
    """Cria um novo usuário"""
    user = User(
        email=email,
        firebase_uid=firebase_uid,
        name=name,
        plan_tier='free',
        documents_limit=5
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    """Busca usuário por Firebase UID"""
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def update_user_plan(db: Session, user_id: int, plan_tier: str, documents_limit: int):
    """Atualiza plano do usuário"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.plan_tier = plan_tier
        user.documents_limit = documents_limit
        db.commit()
    return user


def count_user_documents(db: Session, user_id: int) -> int:
    """Conta documentos do usuário"""
    return db.query(Document).filter(Document.user_id == user_id).count()


# ============================================
# OPERAÇÕES CRUD - DOCUMENTS
# ============================================

def create_document(db: Session, user_id: int, filename: str, **kwargs) -> Document:
    """Cria um novo documento"""
    doc = Document(
        user_id=user_id,
        filename=filename,
        **kwargs
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, doc_id: int, user_id: int = None) -> Optional[Document]:
    """Busca documento por ID"""
    query = db.query(Document).filter(Document.id == doc_id)
    if user_id:
        query = query.filter(Document.user_id == user_id)
    return query.first()


def get_user_documents(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[Document]:
    """Lista documentos do usuário com paginação"""
    return db.query(Document)\
        .filter(Document.user_id == user_id)\
        .order_by(Document.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_document_status(db: Session, doc_id: int, status: str, **kwargs):
    """Atualiza status do documento"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = status
        for key, value in kwargs.items():
            setattr(doc, key, value)
        if status == 'processed':
            doc.processed_at = datetime.utcnow()
        db.commit()
    return doc


def update_document(db: Session, doc_id: int, user_id: int, **kwargs) -> Optional[Document]:
    """Atualiza um documento existente"""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == user_id
    ).first()
    if doc:
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        db.commit()
        db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: int, user_id: int) -> bool:
    """Remove documento"""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == user_id
    ).first()
    if doc:
        db.delete(doc)
        db.commit()
        return True
    return False


# ============================================
# OPERAÇÕES - DEADLINES
# ============================================

def create_deadlines(db: Session, document_id: int, user_id: int, deadlines: List[Dict]):
    """Cria prazos para um documento"""
    for dl in deadlines:
        deadline = Deadline(
            document_id=document_id,
            user_id=user_id,
            days=dl.get('days'),
            urgency=dl.get('urgency'),
            context=dl.get('context'),
            description=dl.get('description')
        )
        db.add(deadline)
    db.commit()


def get_user_deadlines(db: Session, user_id: int) -> List[Deadline]:
    """Retorna todos os prazos de um usuário"""
    return db.query(Deadline).filter(
        Deadline.user_id == user_id
    ).order_by(Deadline.due_date.asc()).all()


def get_upcoming_deadlines(db: Session, user_id: int, days: int = 30) -> List[Deadline]:
    """Retorna prazos dos próximos dias"""
    from datetime import timedelta
    
    cutoff = datetime.utcnow() + timedelta(days=days)
    
    return db.query(Deadline)\
        .filter(
            Deadline.user_id == user_id,
            Deadline.is_completed == False,
            Deadline.due_date <= cutoff
        )\
        .order_by(Deadline.due_date.asc())\
        .all()


def mark_deadline_complete(db: Session, deadline_id: int, user_id: int) -> bool:
    """Marca prazo como completo"""
    dl = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == user_id
    ).first()
    if dl:
        dl.is_completed = True
        dl.completed_at = datetime.utcnow()
        db.commit()
        return True
    return False


# ============================================
# ESTATÍSTICAS
# ============================================

def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Retorna estatísticas do usuário"""
    from sqlalchemy import func
    
    total_docs = db.query(func.count(Document.id))\
        .filter(Document.user_id == user_id)\
        .scalar()
    
    total_deadlines = db.query(func.count(Deadline.id))\
        .filter(Deadline.user_id == user_id)\
        .scalar()
    
    urgent_deadlines = db.query(func.count(Deadline.id))\
        .filter(
            Deadline.user_id == user_id,
            Deadline.urgency == 'high',
            Deadline.is_completed == False
        )\
        .scalar()
    
    # Tipos de documentos
    doc_types = db.query(Document.document_type, func.count(Document.id))\
        .filter(Document.user_id == user_id)\
        .group_by(Document.document_type)\
        .all()
    
    return {
        'total_documents': total_docs,
        'total_deadlines': total_deadlines,
        'urgent_deadlines': urgent_deadlines,
        'document_types': {dt: count for dt, count in doc_types}
    }


# ============================================
# HELPER FUNCTIONS - SERIALIZATION
# ============================================

def document_to_dict(doc: Document) -> Dict[str, Any]:
    """Converte objeto Document para dicionário"""
    if not doc:
        return None
    
    return {
        'id': doc.id,
        'user_id': doc.user_id,
        'filename': doc.filename,
        'document_type': doc.document_type,
        'process_number': doc.process_number,
        'court': doc.court,
        'status': doc.status,
        'text_content': doc.text_content,
        'analysis': doc.analysis,
        'summary': doc.summary,
        'parties': doc.parties,
        'values': doc.values,
        'created_at': doc.created_at.isoformat() if doc.created_at else None,
        'processed_at': doc.processed_at.isoformat() if doc.processed_at else None,
        'deadlines': [deadline_to_dict(d) for d in doc.deadlines] if doc.deadlines else []
    }


def deadline_to_dict(dl: Deadline) -> Dict[str, Any]:
    """Converte objeto Deadline para dicionário"""
    if not dl:
        return None
    
    return {
        'id': dl.id,
        'document_id': dl.document_id,
        'days': dl.days,
        'urgency': dl.urgency,
        'context': dl.context,
        'description': dl.description,
        'due_date': dl.due_date.isoformat() if dl.due_date else None,
        'is_completed': dl.is_completed,
        'completed_at': dl.completed_at.isoformat() if dl.completed_at else None
    }


def user_to_dict(user: User) -> Dict[str, Any]:
    """Converte objeto User para dicionário"""
    if not user:
        return None
    
    return {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'plan_tier': user.plan_tier,
        'documents_limit': user.documents_limit,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }


# ============================================
# DATABASE INITIALIZATION - SYNC WITH EMAIL
# ============================================

def get_or_create_user_by_email(db: Session, email: str, firebase_uid: str = None, full_name: str = None) -> User:
    """Busca ou cria usuário por email (para sincronização com main.py)"""
    user = get_user_by_email(db, email)
    if not user:
        user = create_user(db, email, firebase_uid, full_name)
    return user


# ============================================
# TESTES
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO BANCO DE DADOS - LexScan IA")
    print("=" * 60)
    
    # Inicializar banco
    init_db()
    
    # Testar operações
    with db_session() as db:
        # Criar usuário de teste
        user = create_user(db, "teste@lexscan.ai", "firebase-123", "Usuário Teste")
        print(f"✅ Usuário criado: ID {user.id}")
        
        # Criar documento
        doc = create_document(
            db,
            user_id=user.id,
            filename="teste.pdf",
            document_type="peticao_inicial",
            process_number="12345-67.2024.8.26.0001",
            status="processed"
        )
        print(f"✅ Documento criado: ID {doc.id}")
        
        # Buscar usuário
        found_user = get_user_by_email(db, "teste@lexscan.ai")
        print(f"✅ Usuário encontrado: {found_user.email}")
        
        # Contar documentos
        count = count_user_documents(db, user.id)
        print(f"✅ Documentos do usuário: {count}")
        
        # Estatísticas
        stats = get_user_stats(db, user.id)
        print(f"✅ Estatísticas: {stats}")
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)


# Aliases para compatibilidade
from typing import List, Dict
def create_deadline(db, document_id: int, user_id: int, deadline_data: Dict):
    """Alias para create_deadlines (compatibilidade)"""
    return create_deadlines(db, document_id, user_id, [deadline_data])

from database import (
    get_db, SessionLocal, init_db,
    User, Document, Deadline, ChatMessage, LegalDocument,
    get_user_by_email, create_user, get_or_create_user_by_email,
    get_user_documents, create_document, update_document, get_document as get_db_document,
    create_deadline, get_user_deadlines,
    document_to_dict, deadline_to_dict, user_to_dict, get_user_stats
)
