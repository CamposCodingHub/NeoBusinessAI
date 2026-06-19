"""
Schema validation with Pydantic v2.
"""

from typing import Annotated, List, Literal, Optional
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from .sanitizers import (
    sanitize_html,
    sanitize_input,
    sanitize_sql,
    validate_email,
    validate_password,
    validate_uuid,
)


NameStr = Annotated[str, StringConstraints(min_length=2, max_length=100)]
MessageStr = Annotated[str, StringConstraints(min_length=1, max_length=4000)]
FilenameStr = Annotated[str, StringConstraints(min_length=1, max_length=255)]
SearchStr = Annotated[str, StringConstraints(min_length=1, max_length=200)]
SubjectStr = Annotated[str, StringConstraints(min_length=1, max_length=200)]
BodyStr = Annotated[str, StringConstraints(min_length=1, max_length=50000)]
AIQueryStr = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
PhoneStr = Annotated[str, StringConstraints(max_length=20)]
SecretStr = Annotated[str, StringConstraints(min_length=32, max_length=128)]


class UserCreateSchema(BaseModel):
    """Schema para criação de usuário."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "usuario@exemplo.com",
                "password": "SenhaForte123!",
                "name": "João Silva",
            }
        }
    )

    email: EmailStr = Field(
        ...,
        description="Email do usuário",
        json_schema_extra={"example": "usuario@exemplo.com"},
    )
    password: str = Field(..., min_length=8, max_length=128, description="Senha forte")
    name: NameStr = Field(..., description="Nome completo")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        is_valid, message = validate_password(value)
        if not is_valid:
            raise ValueError(message)
        return value

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return sanitize_input(value, max_length=100)


class UserLoginSchema(BaseModel):
    """Schema para login."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ChatMessageSchema(BaseModel):
    """Schema para mensagens de chat."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Analise este contrato de trabalho",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "context": "O usuário é advogado trabalhista",
            }
        }
    )

    message: MessageStr = Field(..., description="Mensagem do usuário")
    conversation_id: Optional[str] = Field(None, description="ID da conversa (opcional)")
    context: Optional[str] = Field(None, max_length=10000, description="Contexto adicional")

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, value: str) -> str:
        value = sanitize_input(value, max_length=4000)
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
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower):
                raise ValueError("Mensagem contém padrões potencialmente maliciosos")
        return value

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not validate_uuid(value):
            raise ValueError("ID de conversa inválido")
        return value

    @field_validator("context")
    @classmethod
    def sanitize_context(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_input(value, max_length=10000)


class DocumentUploadSchema(BaseModel):
    """Schema para upload de documentos."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "contrato_trabalho.pdf",
                "content_type": "application/pdf",
                "size": 1048576,
                "description": "Contrato para revisão",
            }
        }
    )

    filename: FilenameStr = Field(..., description="Nome do arquivo")
    content_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/rtf",
        "text/rtf",
        "image/jpeg",
        "image/png",
        "image/tiff",
    ] = Field(..., description="Tipo MIME do arquivo")
    size: int = Field(..., ge=1, le=50 * 1024 * 1024, description="Tamanho do arquivo em bytes")
    description: Optional[Annotated[str, StringConstraints(max_length=500)]] = Field(
        None,
        description="Descrição opcional do documento",
    )

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        allowed_extensions = {
            ".pdf",
            ".docx",
            ".txt",
            ".rtf",
            ".jpg",
            ".jpeg",
            ".png",
            ".tif",
            ".tiff",
        }
        extension = value.lower().split(".")[-1] if "." in value else ""
        if f".{extension}" not in allowed_extensions:
            raise ValueError(f"Extensão .{extension} não permitida")

        value = sanitize_input(value, max_length=255)
        dangerous_chars = ["/", "\\", "<", ">", ":", '"', "|", "?", "*", "\x00"]
        for char in dangerous_chars:
            if char in value:
                raise ValueError(f"Nome contém caracteres inválidos: {char}")
        return value

    @field_validator("size")
    @classmethod
    def validate_size(cls, value: int) -> int:
        if value > 50 * 1024 * 1024:
            raise ValueError("Arquivo excede 50MB")
        if value == 0:
            raise ValueError("Arquivo não pode estar vazio")
        return value

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_input(value, max_length=500)


class DocumentSearchSchema(BaseModel):
    """Schema para busca de documentos."""

    query: SearchStr = Field(..., description="Termo de busca")
    filters: Optional[dict] = Field(None, description="Filtros adicionais")
    page: int = Field(1, ge=1, description="Página de resultados")
    limit: int = Field(20, ge=1, le=100, description="Itens por página")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, value: str) -> str:
        value = sanitize_input(value, max_length=200)
        return sanitize_sql(value, strict=False)


class EmailSendSchema(BaseModel):
    """Schema para envio de email."""

    recipient_email: EmailStr
    subject: SubjectStr = Field(..., description="Assunto")
    body: BodyStr = Field(..., description="Corpo do email")
    attachments: Optional[List[str]] = Field(None, max_length=5, description="IDs de anexos")

    @field_validator("subject")
    @classmethod
    def sanitize_subject(cls, value: str) -> str:
        return sanitize_input(value, max_length=200)

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, value: str) -> str:
        return sanitize_html(value, allowed_tags=["p", "br", "strong", "em", "a", "ul", "ol", "li"])

    @field_validator("recipient_email")
    @classmethod
    def validate_recipient(cls, value: EmailStr) -> EmailStr:
        if not validate_email(str(value)):
            raise ValueError("Email inválido")
        return value


class AIQuerySchema(BaseModel):
    """Schema para queries de IA."""

    query: AIQueryStr = Field(..., description="Pergunta/comando")
    document_ids: Optional[List[str]] = Field(None, max_length=10, description="IDs de documentos para contexto")
    response_format: Optional[Literal["text", "json", "markdown"]] = "text"
    temperature: Optional[float] = Field(0.7, ge=0, le=2)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = sanitize_input(value, max_length=2000)
        jailbreak_patterns = [
            r"ignore previous",
            r"disregard all",
            r"system instruction",
            r"you are a.*now",
            r"developer mode",
            r"DAN mode",
            r"jailbreak",
        ]
        value_lower = value.lower()
        for pattern in jailbreak_patterns:
            if re.search(pattern, value_lower):
                raise ValueError("Query contém padrões de manipulação")
        return value

    @field_validator("document_ids")
    @classmethod
    def validate_doc_ids(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        for item in value:
            if not validate_uuid(item):
                raise ValueError(f"ID de documento inválido: {item}")
        return value


class PaginationSchema(BaseModel):
    """Schema base para paginação."""

    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    sort_order: Optional[Literal["asc", "desc"]] = "desc"


class UserUpdateSchema(BaseModel):
    """Schema para atualização de usuário."""

    name: Optional[NameStr] = None
    email: Optional[EmailStr] = None
    phone: Optional[PhoneStr] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return sanitize_input(value, max_length=100)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = re.sub(r"\D", "", value)
        if len(value) < 8 or len(value) > 15:
            raise ValueError("Número de telefone inválido")
        return value


class WebhookSchema(BaseModel):
    """Schema para webhooks."""

    url: str = Field(..., description="URL do webhook")
    events: List[Literal["document.created", "document.updated", "email.received", "chat.message"]] = Field(
        ...,
        min_length=1,
        max_length=10,
    )
    secret: Optional[SecretStr] = None

    @field_validator("url")
    @classmethod
    def validate_webhook_url(cls, value: str) -> str:
        from .sanitizers import validate_url

        if not validate_url(value, allowed_schemes=["https"]):
            raise ValueError("URL de webhook deve ser HTTPS válida")
        return value


def validate_schema(data: dict, schema_class) -> BaseModel:
    """Valida um dicionário contra um schema Pydantic."""

    return schema_class(**data)


def sanitize_model_dict(model_dict: dict) -> dict:
    """Sanitiza todos os valores string em um dicionário."""

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
