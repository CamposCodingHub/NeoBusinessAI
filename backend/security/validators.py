"""
Validação de Schema com Pydantic
=================================
Validação rigorosa de todos os inputs usando Pydantic schemas.
"""

from pydantic import BaseModel, Field, validator, EmailStr, constr
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
import re

from .sanitizers import (
    sanitize_input,
    validate_email,
    validate_password,
    validate_uuid,
    sanitize_sql,
    sanitize_html
)


class UserCreateSchema(BaseModel):
    """Schema para criação de usuário"""
    email: EmailStr = Field(
        ...,
        description="Email do usuário",
        example="usuario@exemplo.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha forte"
    )
    name: constr(min_length=2, max_length=100) = Field(
        ...,
        description="Nome completo"
    )
    
    @validator('password')
    def validate_password_strength(cls, v):
        is_valid, message = validate_password(v)
        if not is_valid:
            raise ValueError(message)
        return v
    
    @validator('name')
    def sanitize_name(cls, v):
        return sanitize_input(v, max_length=100)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "usuario@exemplo.com",
                "password": "SenhaForte123!",
                "name": "João Silva"
            }
        }


class UserLoginSchema(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ChatMessageSchema(BaseModel):
    """Schema para mensagens de chat"""
    message: constr(min_length=1, max_length=4000) = Field(
        ...,
        description="Mensagem do usuário"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="ID da conversa (opcional)"
    )
    context: Optional[str] = Field(
        None,
        max_length=10000,
        description="Contexto adicional"
    )
    
    @validator('message')
    def sanitize_message(cls, v):
        # Sanitização básica
        v = sanitize_input(v, max_length=4000)
        
        # Verificar tentativas de prompt injection
        dangerous_patterns = [
            r"ignore previous instructions",
            r"ignore all instructions",
            r"system prompt",
            r"you are now",
            r"disregard",
            r"forget everything",
            r"new role:",
            r"developer mode",
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower):
                raise ValueError("Mensagem contém padrões potencialmente maliciosos")
        
        return v
    
    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        if v is None:
            return v
        if not validate_uuid(v):
            raise ValueError("ID de conversa inválido")
        return v
    
    @validator('context')
    def sanitize_context(cls, v):
        if v is None:
            return v
        return sanitize_input(v, max_length=10000)
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Analise este contrato de trabalho",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "context": "O usuário é advogado trabalhista"
            }
        }


class DocumentUploadSchema(BaseModel):
    """Schema para upload de documentos"""
    filename: constr(min_length=1, max_length=255) = Field(
        ...,
        description="Nome do arquivo"
    )
    content_type: Literal[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ] = Field(
        ...,
        description="Tipo MIME do arquivo"
    )
    size: int = Field(
        ...,
        ge=1,
        le=10 * 1024 * 1024,  # 10MB máximo
        description="Tamanho do arquivo em bytes"
    )
    description: Optional[constr(max_length=500)] = Field(
        None,
        description="Descrição opcional do documento"
    )
    
    @validator('filename')
    def validate_filename(cls, v):
        # Validar extensão
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        ext = v.lower().split('.')[-1] if '.' in v else ''
        if f'.{ext}' not in allowed_extensions:
            raise ValueError(f"Extensão .{ext} não permitida")
        
        # Sanitizar nome
        v = sanitize_input(v, max_length=255)
        
        # Verificar caracteres perigosos
        dangerous = ['/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous:
            if char in v:
                raise ValueError(f"Nome contém caracteres inválidos: {char}")
        
        return v
    
    @validator('size')
    def validate_size(cls, v):
        if v > 10 * 1024 * 1024:
            raise ValueError("Arquivo excede 10MB")
        if v == 0:
            raise ValueError("Arquivo não pode estar vazio")
        return v
    
    @validator('description')
    def sanitize_description(cls, v):
        if v is None:
            return v
        return sanitize_input(v, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "contrato_trabalho.pdf",
                "content_type": "application/pdf",
                "size": 1048576,
                "description": "Contrato para revisão"
            }
        }


class DocumentSearchSchema(BaseModel):
    """Schema para busca de documentos"""
    query: constr(min_length=1, max_length=200) = Field(
        ...,
        description="Termo de busca"
    )
    filters: Optional[dict] = Field(
        None,
        description="Filtros adicionais"
    )
    page: int = Field(1, ge=1, description="Página de resultados")
    limit: int = Field(20, ge=1, le=100, description="Itens por página")
    
    @validator('query')
    def sanitize_query(cls, v):
        v = sanitize_input(v, max_length=200)
        # Sanitização SQL para busca
        v = sanitize_sql(v, strict=False)
        return v


class EmailSendSchema(BaseModel):
    """Schema para envio de email"""
    recipient_email: EmailStr
    subject: constr(min_length=1, max_length=200) = Field(..., description="Assunto")
    body: constr(min_length=1, max_length=50000) = Field(..., description="Corpo do email")
    attachments: Optional[List[str]] = Field(None, max_items=5, description="IDs de anexos")
    
    @validator('subject')
    def sanitize_subject(cls, v):
        return sanitize_input(v, max_length=200)
    
    @validator('body')
    def sanitize_body(cls, v):
        # Permitir HTML básico mas sanitizar
        return sanitize_html(v, allowed_tags=['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li'])
    
    @validator('recipient_email')
    def validate_recipient(cls, v):
        if not validate_email(v):
            raise ValueError("Email inválido")
        return v


class AIQuerySchema(BaseModel):
    """Schema para queries de IA"""
    query: constr(min_length=1, max_length=2000) = Field(..., description="Pergunta/comando")
    document_ids: Optional[List[str]] = Field(None, max_items=10, description="IDs de documentos para contexto")
    response_format: Optional[Literal['text', 'json', 'markdown']] = 'text'
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    
    @validator('query')
    def validate_query(cls, v):
        v = sanitize_input(v, max_length=2000)
        
        # Bloquear tentativas de jailbreak
        jailbreak_patterns = [
            r"ignore previous",
            r"disregard all",
            r"system instruction",
            r"you are a.*now",
            r"developer mode",
            r"DAN mode",
            r"jailbreak",
        ]
        
        v_lower = v.lower()
        for pattern in jailbreak_patterns:
            if re.search(pattern, v_lower):
                raise ValueError("Query contém padrões de manipulação")
        
        return v
    
    @validator('document_ids', each_item=True)
    def validate_doc_id(cls, v):
        if not validate_uuid(v):
            raise ValueError(f"ID de documento inválido: {v}")
        return v


class PaginationSchema(BaseModel):
    """Schema base para paginação"""
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    sort_order: Optional[Literal['asc', 'desc']] = 'desc'


class UserUpdateSchema(BaseModel):
    """Schema para atualização de usuário"""
    name: Optional[constr(min_length=2, max_length=100)] = None
    email: Optional[EmailStr] = None
    phone: Optional[constr(max_length=20)] = None
    
    @validator('name')
    def sanitize_name(cls, v):
        if v is None:
            return v
        return sanitize_input(v, max_length=100)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remover tudo exceto números
        v = re.sub(r'\D', '', v)
        if len(v) < 8 or len(v) > 15:
            raise ValueError("Número de telefone inválido")
        return v


class WebhookSchema(BaseModel):
    """Schema para webhooks"""
    url: str = Field(..., description="URL do webhook")
    events: List[Literal['document.created', 'document.updated', 'email.received', 'chat.message']] = Field(
        ...,
        min_items=1,
        max_items=10
    )
    secret: Optional[constr(min_length=32, max_length=128)] = None
    
    @validator('url')
    def validate_webhook_url(cls, v):
        from .sanitizers import validate_url
        if not validate_url(v, allowed_schemes=['https']):
            raise ValueError("URL de webhook deve ser HTTPS válida")
        return v


def validate_schema(data: dict, schema_class) -> BaseModel:
    """
    Função helper para validar dados contra schema
    
    Args:
        data: Dicionário com dados
        schema_class: Classe do schema Pydantic
    
    Returns:
        Instância validada do schema
    
    Raises:
        ValidationError: Se dados inválidos
    """
    return schema_class(**data)


def sanitize_model_dict(model_dict: dict) -> dict:
    """
    Sanitiza todos os valores string em um dicionário
    
    Args:
        model_dict: Dicionário do modelo
    
    Returns:
        Dicionário sanitizado
    """
    result = {}
    for key, value in model_dict.items():
        if isinstance(value, str):
            result[key] = sanitize_input(value)
        elif isinstance(value, dict):
            result[key] = sanitize_model_dict(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
