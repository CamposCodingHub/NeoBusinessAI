"""
NeoBusiness AI - Backend API
=============================
Sistema de IA jurÃ­dica com seguranÃ§a enterprise-grade.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import os
import re
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
from datetime import datetime
import logging

# ConfiguraÃ§Ã£o de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variÃ¡veis de ambiente e configuraÃ§Ã£o validada
try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8')
except ImportError:
    pass

# Importar configuraÃ§Ã£o validada (falha rÃ¡pido se invÃ¡lida)
try:
    from config import settings
    logger.info(f"âœ… ConfiguraÃ§Ã£o validada - Environment: {settings.ENVIRONMENT}")
except Exception as e:
    logger.error(f"âŒ Erro na configuraÃ§Ã£o: {e}")
    raise

# ==================== SECURITY IMPORTS ====================
from security import (
    # Auth
    create_access_token, create_refresh_token, verify_token,
    get_current_user, require_role, Role,
    # Rate Limiting
    rate_limit, check_rate_limit,
    RateLimitConfig, CHAT_RATE_LIMIT, UPLOAD_RATE_LIMIT, LOGIN_RATE_LIMIT,
    # Sanitizers
    sanitize_input, sanitize_sql, sanitize_html, validate_email,
    # Validators
    validate_schema, ChatMessageSchema, DocumentUploadSchema, UserCreateSchema
)
from middleware.security_middleware import setup_security_middleware
from middleware.tenant_middleware import MultiTenantMiddleware
from security.file_validation import validate_upload
from routes.auth_routes import router as auth_router
from routes.document_routes import router as document_router
from routes.legal_routes import router as legal_router
from routes.deadline_routes import router as deadline_router
from routes.client_routes import router as client_router
from routes.finance_routes import (
    router as finance_router,
    compat_router as finance_compat_router,
    billing_router,
)
from routes.whatsapp_routes import router as whatsapp_router
from routes.twilio_quick_setup import router as twilio_quick_router
from routes.gdpr_routes import router as gdpr_router
from routes.health_routes import router as health_router
from routes.portal_client_routes import router as portal_client_router
from routes.team_routes import router as team_router
from routes.jurisprudencia_routes import router as jurisprudencia_router
from routes.fila_atendimento_routes import router as fila_atendimento_router
from routes.cobranca_routes import router as cobranca_router
from routes.busca_semantica_routes import router as busca_semantica_router
from routes.marketing_routes import router as marketing_router
from routes.operations_routes import router as operations_router
from routes.sovereign_ai_routes import router as sovereign_ai_router
from routes.whatsapp_integrado_routes import router as whatsapp_integrado_router
from routes.matter_routes import router as matter_router
from routes.intake_routes import router as intake_router
from routes.approvals_routes import router as approvals_router
from routes.time_routes import router as time_router
from routes.usage_routes import router as usage_router
from routes.ai_audit_routes import router as ai_audit_router
from routes.org_routes import router as org_router
from routes.trust_routes import router as trust_router
from routes.esign_routes import router as esign_router
from routes.monitor_routes import router as monitor_router
from routes.compliance_routes import router as compliance_router
from routes.notification_routes import router as notification_router
from routes.agenda_routes import router as agenda_router
from routes.poa_routes import router as poa_router
from routes.tasks_routes import router as tasks_router
from routes.contacts_routes import router as contacts_router
from routes.matter_docs_routes import router as matter_docs_router

# AI Imports
from ai.lexscan_engine import lexscan_engine
from ai.engine import NeoBusinessAI
from ai.premium_conversational_engine import create_premium_ai_engine, PremiumConversationalEngine
from services.legal_ai_orchestrator import LegalAIOrchestrator
from sovereign_ai.search import sovereign_legal_search

# Tools
from tools.ocr_real import process_uploaded_file
from tools.notifications import notification_manager
from tools.pdf_generator import pdf_generator
from tools.stripe_manager import stripe_manager, check_user_limits, PlanTier
from tools.audit_logger import audit_logger, AuditEventType, AuditSeverity
from tools.siem_integration import siem, security_alerts

# Celery Async Processing
try:
    from tasks import queue_document_processing, queue_email, get_task_status
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery nÃ£o disponÃ­vel. Processamento serÃ¡ sÃ­ncrono.")

# ==================== AI ENGINE INITIALIZATION ====================
try:
    premium_ai_engine = create_premium_ai_engine()
    legal_ai_orchestrator = LegalAIOrchestrator(
        premium_ai_engine,
        local_search=sovereign_legal_search,
    )
    PREMIUM_AI_AVAILABLE = True
    logger.info("[OK] Motor Premium de IA carregado! Sistema de 25 etapas ativo.")
except Exception as e:
    legal_ai_orchestrator = None
    PREMIUM_AI_AVAILABLE = False
    logger.error(f"[ERRO] Falha ao carregar motor Premium: {e}")
    print(f"[WARNING] Motor Premium nÃ£o disponÃ­vel: {e}")

# PostgreSQL Database imports
from database import (
    get_db, SessionLocal, init_db,
    User, Document, Deadline, ChatMessage,
    get_user_by_email, create_user, get_or_create_user_by_email,
    get_user_documents, create_document, update_document, get_document as get_db_document,
    create_deadline, get_user_deadlines,
    document_to_dict, deadline_to_dict, user_to_dict, get_user_stats
)
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Inicializa recursos globais da API durante o ciclo de vida da aplicacao."""
    try:
        init_db()
        logger.info("[DB] Estrutura do banco validada/inicializada com sucesso")
    except Exception as exc:
        logger.error(f"[DB] Falha ao inicializar banco: {exc}")
        raise

    yield


app = FastAPI(redirect_slashes=False, lifespan=app_lifespan)
app.add_middleware(MultiTenantMiddleware)

# ==================== CORS FIRST ====================
# CORS deve ser o PRIMEIRO middleware para evitar erros de preflight
# ConfiguraÃ§Ã£o SEGURA baseada no ambiente

# Carregar domÃ­nios permitidos do ambiente
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # ProduÃ§Ã£o: apenas domÃ­nios especÃ­ficos
    allow_origins = ALLOWED_ORIGINS
    allow_credentials = True
    logger.info(f"[CORS] Modo PRODUÃ‡ÃƒO - Origens permitidas: {allow_origins}")
else:
    # Desenvolvimento: permitir localhost
    allow_origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]
    allow_credentials = True
    logger.info(f"[CORS] Modo DESENVOLVIMENTO - Origens permitidas: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Requested-With"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=3600,
)

logger.info("[CORS] Middleware configurado com seguranÃ§a")

# ==================== SECURITY SETUP ====================
setup_security_middleware(app)
logger.info("[OK] Security headers middleware configurado")

# ==================== ROUTES ====================
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(legal_router)
app.include_router(deadline_router)
app.include_router(client_router)
app.include_router(finance_router)
app.include_router(finance_compat_router)
app.include_router(billing_router)
app.include_router(whatsapp_router)
app.include_router(twilio_quick_router)
app.include_router(gdpr_router)
app.include_router(health_router)

# MÃ³dulos Etapa 6 + overnight/day
app.include_router(portal_client_router)
app.include_router(team_router)
app.include_router(jurisprudencia_router)
app.include_router(fila_atendimento_router)
app.include_router(cobranca_router)
app.include_router(busca_semantica_router)
app.include_router(marketing_router)
app.include_router(operations_router)
app.include_router(sovereign_ai_router)
app.include_router(whatsapp_integrado_router)
app.include_router(matter_router)
app.include_router(intake_router)
app.include_router(approvals_router)
app.include_router(time_router)
app.include_router(usage_router)
app.include_router(ai_audit_router)
app.include_router(org_router)
app.include_router(trust_router)
app.include_router(esign_router)
app.include_router(monitor_router)
app.include_router(compliance_router)
app.include_router(notification_router)
app.include_router(agenda_router)
app.include_router(poa_router)
app.include_router(tasks_router)
app.include_router(contacts_router)
app.include_router(matter_docs_router)
# CRITICAL-003 FIX: Global error handler to prevent stack trace leaks
import uuid
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para exceÃ§Ãµes nÃ£o tratadas
    NÃƒO expÃµe stack traces ou detalhes internos em produÃ§Ã£o
    """
    error_id = str(uuid.uuid4())[:8]
    
    # Log completo no servidor (para debug)
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error {error_id}: {str(exc)}", exc_info=True)
    
    # Retornar mensagem genÃ©rica para cliente
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': 'Ocorreu um erro interno. Nossa equipe foi notificada.',
            'error_id': error_id,
            'message': 'Se o problema persistir, contate o suporte com o cÃ³digo acima.'
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler para HTTP exceptions"""
    # NÃ£o expor detalhes em erros 500
    if exc.status_code == 500:
        error_id = str(uuid.uuid4())[:8]
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': 'Erro interno do servidor',
                'error_id': error_id
            }
        )
    
    # Outros erros HTTP podem ter detalhes
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'error': exc.detail
        }
    )

ai_instance: Optional[NeoBusinessAI] = None


def get_primary_ai() -> NeoBusinessAI:
    global ai_instance

    if ai_instance is None:
        ai_instance = NeoBusinessAI()

    return ai_instance





@app.post("/chat-stream")
async def chat_stream(
    data: dict,
    current_user=Depends(get_current_user),
):
    user_input = sanitize_input(str(data.get("message") or ""))[:12000]
    if not user_input:
        raise HTTPException(status_code=400, detail="Mensagem nao fornecida")

    async def generator():
        # Prefer premium orchestrator when available (avoid heavy local Phi-3 load)
        if PREMIUM_AI_AVAILABLE and legal_ai_orchestrator:
            result = await legal_ai_orchestrator.answer(
                user_message=user_input,
                user_id=str(current_user.user_id),
                response_mode="quick",
            )
            response = str(result.get("response") or "")
        else:
            response = get_primary_ai().ask(user_input)

        chunk_size = 15
        for i in range(0, len(response), chunk_size):
            yield response[i : i + chunk_size]
            await asyncio.sleep(0.005)

    return StreamingResponse(generator(), media_type="text/plain")


# ============================================
# LEXSCAN IA - ENDPOINTS PARA DASHBOARD
# ============================================

# DEPRECATED: Removido - agora usando PostgreSQL via database.py
# documents_db: List[Dict] = []  # MIGRADO para PostgreSQL

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), manual_text: str = None, user_email: str = None):
    """
    Upload e processamento de documento jurÃ­dico com OCR real
    Verifica limites do plano antes de permitir upload
    USA POSTGRESQL - MIGRADO de SQLite para produÃ§Ã£o
    """
    db = SessionLocal()
    try:
        # SECURITY: Validate email
        if user_email and not validate_email(user_email):
            return JSONResponse({
                'success': False,
                'error': 'Email invÃ¡lido',
                'code': 'INVALID_EMAIL'
            }, status_code=400)
        
        # Verificar limites do usuario (se email fornecido)
        user = None
        if user_email:
            user = get_or_create_user_by_email(db, user_email)
            user_docs_count = len(get_user_documents(db, user.id))
            limits = check_user_limits(user_email, user_docs_count)
            
            if not limits['can_upload']:
                return JSONResponse({
                    'success': False,
                    'error': 'Limite de documentos atingido',
                    'limits': limits,
                    'upgrade_required': True,
                    'plans_url': '/pricing'
                }, status_code=403)
        
        # CRITICAL-002 FIX: Sanitize filename and validate temp paths
        safe_filename = sanitize_filename(file.filename)
        validated_file = await validate_upload(
            file,
            max_size_mb=settings.MAX_FILE_SIZE_MB,
        )
        
        # Additional path traversal validation
        if not safe_filename or safe_filename == 'unnamed_file':
            return JSONResponse({
                'success': False,
                'error': 'Nome de arquivo invÃ¡lido ou nÃ£o seguro.',
                'code': 'INVALID_FILENAME'
            }, status_code=400)
        
        # Validate file size (max 50MB)
        max_file_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_file_size:
            return JSONResponse({
                'success': False,
                'error': f'Arquivo muito grande. Tamanho mÃ¡ximo: 50MB.',
                'code': 'FILE_TOO_LARGE'
            }, status_code=413)
        
        # SECURITY: Check for prompt injection in manual_text
        if manual_text:
            is_malicious, patterns = detect_prompt_injection(manual_text)
            if is_malicious:
                print(f"[SECURITY] Prompt injection detected: {patterns}")
                return JSONResponse({
                    'success': False,
                    'error': 'ConteÃºdo suspeito detectado e bloqueado por seguranÃ§a.',
                    'code': 'SECURITY_VIOLATION'
                }, status_code=400)
        
        # Ler conteÃºdo
        content = validated_file["content"]
        
        print(f"[UPLOAD] Recebido: {safe_filename} ({len(content)} bytes)")
        
        # Extrair texto com OCR real (usando filename sanitizado)
        ocr_result = process_uploaded_file(content, safe_filename, manual_text)
        
        # Se OCR falhou mas nÃ£o tem texto manual, retornar instruÃ§Ãµes
        if not ocr_result['success'] and not manual_text:
            return JSONResponse({
                'success': False,
                'error': ocr_result.get('error', 'Falha no OCR'),
                'ocr_available': False,
                'fallback_option': True,
                'message': 'OCR nÃ£o disponÃ­vel. VocÃª pode enviar o texto manualmente.'
            }, status_code=400)
        
        text_content = ocr_result['text']
        print(f"[UPLOAD] Texto extraÃ­do: {len(text_content)} caracteres")
        
        # Processar com LexScan Engine
        result = lexscan_engine.process_document(text_content)
        
        # MIGRADO: Salvar documento no PostgreSQL
        user_id = user.id if user else None
        
        doc_data = {
            'user_id': user_id,
            'filename': safe_filename,
            'document_type': result.get('document_type', 'unknown'),
            'process_number': result.get('process_number', ''),
            'court': result.get('court', ''),
            'status': result.get('status', ''),
            'text_content': text_content[:10000] if len(text_content) > 10000 else text_content,  # Limitado para DB
            'analysis': result,
            'summary': result.get('summary', ''),
            'parties': result.get('parties', {}),
            'values': result.get('values', []),
        }
        
        db_document = create_document(db, doc_data)
        doc_id = db_document.id
        
        # Criar deadlines se existirem
        deadlines_list = result.get('deadlines', [])
        if deadlines_list:
            for dl in deadlines_list:
                deadline_data = {
                    'user_id': user_id,
                    'document_id': doc_id,
                    'days': dl.get('days', 0),
                    'urgency': dl.get('urgency', 'medium'),
                    'context': dl.get('context', ''),
                    'description': dl.get('description', '')
                }
                create_deadline(db, deadline_data)
        
        # Commit transaction
        db.commit()
        
        # Converte para dicionÃ¡rio para resposta
        document = document_to_dict(db_document)
        print(f"[UPLOAD] Documento salvo no PostgreSQL: ID {doc_id}")
        
        # AUDIT LOG: Registra upload de documento
        audit_logger.log(
            event_type=AuditEventType.DOCUMENT_UPLOAD,
            user_id=str(user_id) if user_id else None,
            user_email=user_email,
            action="upload_document",
            resource_type="document",
            resource_id=str(doc_id),
            details={
                'filename': safe_filename,
                'file_size': len(content),
                'ocr_method': ocr_result.get('method'),
                'pages': ocr_result.get('pages', 1),
                'celery': CELERY_AVAILABLE
            },
            severity=AuditSeverity.LOW,
            success=True
        )
        
        # Notificar usuÃ¡rio (opcional)
        if user_email and notification_manager:
            try:
                notification_manager.send_notification(
                    user_email,
                    f"Documento '{safe_filename}' processado com sucesso!",
                    'success'
                )
            except Exception as e:
                print(f"[NOTIFICATION] Erro: {e}")
        
        response = JSONResponse({
            'success': True,
            'document': document,
            'ocr_info': {
                'method': ocr_result.get('method'),
                'pages': ocr_result.get('pages', 1),
                'text_length': len(text_content),
                'file_type': ocr_result['type']
            },
            'message': f'Documento processado com sucesso! {ocr_result.get("pages", 1)} pÃ¡gina(s) analisada(s).'
        })
        
        # Add security headers
        for key, value in get_security_headers().items():
            response.headers[key] = value
        
        return response
        
    except Exception as e:
        db.rollback()  # Rollback on error
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)
    finally:
        db.close()

@app.get("/api/documents")
async def list_documents(current_user=Depends(get_current_user)):
    """
    Lista documentos processados do usuario autenticado.
    """
    db = SessionLocal()
    try:
        user_id = int(current_user.user_id)
        user_docs_objs = get_user_documents(db, user_id)
        user_docs = [document_to_dict(d) for d in user_docs_objs]
        return JSONResponse({
            'success': True,
            'documents': user_docs,
            'total': len(user_docs)
        })
    finally:
        db.close()

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int, user_email: str = None):
    """
    ObtÃ©m detalhes de um documento especÃ­fico
    SECURITY: Verifica propriedade para prevenir IDOR
    """
    db = SessionLocal()
    try:
        doc = get_db_document(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento nÃ£o encontrado")
        
        # Convert to dict for access verification
        doc_dict = document_to_dict(doc)
        
        # SECURITY: Verify document ownership (IDOR protection)
        if not verify_document_access(doc_dict, user_email):
            error = require_auth_error()
            raise HTTPException(status_code=403, detail=error['error'])
        
        return JSONResponse({
            'success': True,
            'document': doc_dict
        })
    finally:
        db.close()

@app.post("/api/documents/{doc_id}/chat")
async def chat_with_document(doc_id: int, data: dict, user_email: str = None):
    """
    Chat contextual sobre um documento
    SECURITY: Verifica propriedade para prevenir IDOR
    """
    db = SessionLocal()
    try:
        doc = get_db_document(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Documento nÃ£o encontrado")
        
        # Convert to dict for access verification
        doc_dict = document_to_dict(doc)
        
        # SECURITY: Verify document ownership (IDOR protection)
        if not verify_document_access(doc_dict, user_email):
            error = require_auth_error()
            raise HTTPException(status_code=403, detail=error['error'])
        
        # SECURITY: Check for prompt injection in question
        question = data.get('question', '')
        is_malicious, patterns = detect_prompt_injection(question)
        if is_malicious:
            return JSONResponse({
                'success': False,
                'error': 'Pergunta bloqueada por seguranÃ§a.',
                'code': 'SECURITY_VIOLATION'
            }, status_code=400)
        
        # PREMIUM AI: Usar motor premium se disponÃ­vel
        if PREMIUM_AI_AVAILABLE and premium_ai_engine:
            try:
                # Gerar resposta premium com 25 etapas ativas
                premium_result = await premium_ai_engine.generate_premium_response(
                    user_message=question,
                    user_id=user_email or f"doc_{doc_id}",
                    document_context=doc_dict.get('content', '')[:2000]  # Contexto limitado
                )
                
                response = premium_result['response']
                premium_metadata = {
                    'quality_score': premium_result.get('quality_score', 0),
                    'style': premium_result.get('style', 'standard'),
                    'detected_intent': premium_result.get('detected_intent', ''),
                    'emotional_state': premium_result.get('emotional_state', 'neutral'),
                    'context_summary': premium_result.get('context_summary', ''),
                    'ai_mode': 'premium'
                }
            except Exception as e:
                # Fallback para motor padrÃ£o
                print(f"[WARNING] Premium AI falhou: {e}. Usando motor padrÃ£o.")
                response = lexscan_engine.chat_with_document(doc_dict, question)
                premium_metadata = {'ai_mode': 'standard', 'error': str(e)}
        else:
            # Usar motor padrÃ£o (LexScan Engine)
            response = lexscan_engine.chat_with_document(doc_dict, question)
            premium_metadata = {'ai_mode': 'standard'}
        
        return JSONResponse({
            'success': True,
            'answer': response,
            'document_id': doc_id,
            'ai_metadata': premium_metadata
        })
    finally:
        db.close()

@app.get("/api/deadlines")
async def get_deadlines(user_email: str = None):
    """
    Retorna prazos dos documentos
    SECURITY: Filtra por usuÃ¡rio para prevenir data leak
    """
    db = SessionLocal()
    try:
        all_deadlines = []
        
        if user_email:
            user = get_user_by_email(db, user_email)
            if user:
                user_deadlines = get_user_deadlines(db, user.id)
                for dl in user_deadlines:
                    dl_dict = deadline_to_dict(dl)
                    if dl.document:
                        dl_dict['document_name'] = dl.document.filename
                        dl_dict['document_type'] = dl.document.document_type
                    all_deadlines.append(dl_dict)
        else:
            # Retorna todos (para compatibilidade)
            from sqlalchemy import desc
            all_dls = db.query(Deadline).order_by(desc(Deadline.created_at)).all()
            all_deadlines = [deadline_to_dict(dl) for dl in all_dls]
        
        # Ordenar por urgÃªncia
        urgency_order = {'high': 0, 'medium': 1, 'low': 2}
        all_deadlines.sort(key=lambda x: urgency_order.get(x.get('urgency', 'medium'), 1))
        
        return JSONResponse({
            'success': True,
            'deadlines': all_deadlines,
            'total': len(all_deadlines),
            'urgent': len([d for d in all_deadlines if d.get('urgency') == 'high'])
        })
    finally:
        db.close()

@app.get("/api/dashboard/stats")
async def dashboard_stats(user_email: str = None):
    """
    EstatÃ­sticas para o dashboard
    SECURITY: Filtra por usuÃ¡rio para prevenir data leak
    """
    db = SessionLocal()
    try:
        if user_email:
            user = get_user_by_email(db, user_email)
            if user:
                stats = get_user_stats(db, user.id)
                # Get last upload
                user_docs_objs = get_user_documents(db, user.id)
                last_upload = None
                if user_docs_objs:
                    last_upload = user_docs_objs[0].created_at.isoformat() if user_docs_objs[0].created_at else None
                
                return JSONResponse({
                    'success': True,
                    'stats': {
                        'total_documents': stats['total_documents'],
                        'total_deadlines': stats['total_deadlines'],
                        'urgent_deadlines': stats['urgent_deadlines'],
                        'document_types': stats['document_types'],
                        'last_upload': last_upload
                    }
                })
            else:
                # UsuÃ¡rio nÃ£o encontrado
                return JSONResponse({
                    'success': True,
                    'stats': {
                        'total_documents': 0,
                        'total_deadlines': 0,
                        'urgent_deadlines': 0,
                        'document_types': {},
                        'last_upload': None
                    }
                })
        else:
            # Retorna estatÃ­sticas globais (para compatibilidade)
            from sqlalchemy import func, desc
            total_docs = db.query(func.count(Document.id)).scalar()
            total_deadlines = db.query(func.count(Deadline.id)).scalar()
            urgent_deadlines = db.query(func.count(Deadline.id)).filter(
                Deadline.urgency == 'high',
                Deadline.is_completed == False
            ).scalar()
            
            # Tipos de documentos
            doc_types_raw = db.query(Document.document_type, func.count(Document.id)).group_by(Document.document_type).all()
            doc_types = {dt: count for dt, count in doc_types_raw}
            
            # Last upload
            last_doc = db.query(Document).order_by(desc(Document.created_at)).first()
            last_upload = last_doc.created_at.isoformat() if last_doc and last_doc.created_at else None
            
            return JSONResponse({
                'success': True,
                'stats': {
                    'total_documents': total_docs,
                    'total_deadlines': total_deadlines,
                    'urgent_deadlines': urgent_deadlines,
                    'document_types': doc_types,
                    'last_upload': last_upload
                }
            })
    finally:
        db.close()

@app.get("/api/system/status")
async def system_status():
    """
    Status do sistema e disponibilidade de OCR
    """
    from tools.ocr_real import ocr_real
    
    return JSONResponse({
        'success': True,
        'system': 'LexScan IA',
        'version': '1.0.0',
        'ocr': {
            'available': ocr_real.tesseract_available,
            'message': 'Tesseract OCR pronto' if ocr_real.tesseract_available else 'Tesseract nÃ£o instalado',
            'install_url': 'https://github.com/UB-Mannheim/tesseract/wiki' if not ocr_real.tesseract_available else None
        },
        'api': {
            'groq_available': lexscan_engine.use_api,
            'message': 'API Groq ativa' if lexscan_engine.use_api else 'Usando modo fallback'
        },
        'notifications': {
            'enabled': notification_manager.enabled,
            'email_configured': bool(notification_manager.smtp_username),
            'setup_instructions': 'Configure SMTP_USERNAME e SMTP_PASSWORD' if not notification_manager.enabled else None
        }
    })


# ============================================
# NOTIFICAÃ‡Ã•ES POR EMAIL
# ============================================

@app.get("/api/notifications/test")
async def test_notifications():
    """
    Testa conexÃ£o com servidor SMTP
    """
    result = notification_manager.test_connection()
    return JSONResponse(result)

@app.post("/api/notifications/send-test")
async def send_test_email(data: dict):
    """
    Envia email de teste
    """
    to_email = data.get('email', '')
    if not to_email:
        return JSONResponse({
            'success': False,
            'error': 'Email de destino nÃ£o fornecido'
        }, status_code=400)
    
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #1e3a5f;">âœ… Teste LexScan IA</h1>
        <p>Este Ã© um email de teste do sistema de notificaÃ§Ãµes.</p>
        <p>Se vocÃª estÃ¡ recebendo este email, o sistema estÃ¡ configurado corretamente!</p>
        <br>
        <p><strong>LexScan IA</strong> - AutomaÃ§Ã£o Documental JurÃ­dica</p>
    </body>
    </html>
    """
    
    result = notification_manager.send_email(
        to_email=to_email,
        subject="ðŸ“§ Teste de NotificaÃ§Ã£o - LexScan IA",
        html_content=html_content,
        text_content="Teste de notificaÃ§Ã£o LexScan IA. Sistema configurado corretamente!"
    )
    
    return JSONResponse(result)

@app.post("/api/notifications/check-deadlines")
async def check_deadlines_and_notify(data: dict):
    """
    Verifica prazos urgentes e envia notificaÃ§Ãµes
    """
    user_email = data.get('email', '')
    
    if not user_email:
        return JSONResponse({
            'success': False,
            'error': 'Email do usuÃ¡rio nÃ£o fornecido'
        }, status_code=400)
    
    if not notification_manager.enabled:
        return JSONResponse({
            'success': False,
            'error': 'Sistema de notificaÃ§Ãµes nÃ£o configurado',
            'setup_instructions': [
                'Configure as variÃ¡veis de ambiente no arquivo .env:',
                'SMTP_SERVER=smtp.gmail.com',
                'SMTP_PORT=587',
                'SMTP_USERNAME=seu_email@gmail.com',
                'SMTP_PASSWORD=sua_senha_de_app'
            ]
        }, status_code=400)
    
    # Verificar prazos e notificar
    notifications = notification_manager.check_and_notify_deadlines(user_email, documents_db)
    
    return JSONResponse({
        'success': True,
        'notifications_sent': len(notifications),
        'notifications': notifications,
        'message': f'{len(notifications)} notificaÃ§Ãµes enviadas para {user_email}'
    })


# ============================================
# EXPORTAÃ‡ÃƒO DE RELATÃ“RIOS PDF
# ============================================

@app.get("/api/documents/{doc_id}/report")
async def generate_document_report(doc_id: int, user_email: str = None):
    """
    Gera relatÃ³rio PDF de um documento especÃ­fico
    SECURITY: Verifica propriedade para prevenir IDOR
    """
    db = SessionLocal()
    try:
        # Buscar documento no PostgreSQL
        doc = get_db_document(db, doc_id)
        
        if not doc:
            return JSONResponse({
                'success': False,
                'error': 'Documento nÃ£o encontrado'
            }, status_code=404)
        
        # Convert to dict for access verification
        doc_dict = document_to_dict(doc)
        
        # SECURITY: Verify document ownership (IDOR protection)
        if not verify_document_access(doc_dict, user_email):
            return JSONResponse({
                'success': False,
                'error': 'Acesso negado. VocÃª nÃ£o tem permissÃ£o para acessar este recurso.',
                'code': 'FORBIDDEN'
            }, status_code=403)
        
        # SECURITY: Sanitize filename
        safe_filename = sanitize_filename(doc_dict.get('filename', 'documento'))
        
        # Gerar PDF
        pdf_buffer = pdf_generator.generate_document_report(doc_dict)
        
        # Nome do arquivo
        filename = f"relatorio_{doc.get('filename', 'documento').replace(' ', '_').replace('.', '_')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

@app.get("/api/reports/dashboard")
async def generate_dashboard_report(user_email: str = None):
    """
    Gera relatÃ³rio geral do dashboard
    SECURITY: Filtra por usuÃ¡rio para prevenir data leak
    """
    db = SessionLocal()
    try:
        # Filter by user if email provided
        if user_email:
            user = get_user_by_email(db, user_email)
            if user:
                stats = get_user_stats(db, user.id)
                user_docs_objs = get_user_documents(db, user.id)
                user_docs = [document_to_dict(d) for d in user_docs_objs]
                
                # Get deadlines
                user_dls = get_user_deadlines(db, user.id)
                all_deadlines = []
                for dl in user_dls:
                    dl_dict = deadline_to_dict(dl)
                    if dl.document:
                        dl_dict['document_name'] = dl.document.filename
                        dl_dict['document_type'] = dl.document.document_type
                    all_deadlines.append(dl_dict)
            else:
                stats = {'total_documents': 0, 'total_deadlines': 0, 'urgent_deadlines': 0, 'document_types': {}}
                user_docs = []
                all_deadlines = []
        else:
            # Global stats
            from sqlalchemy import func, desc
            total_docs = db.query(func.count(Document.id)).scalar()
            total_deadlines = db.query(func.count(Deadline.id)).scalar()
            urgent_deadlines = db.query(func.count(Deadline.id)).filter(
                Deadline.urgency == 'high',
                Deadline.is_completed == False
            ).scalar()
            
            doc_types_raw = db.query(Document.document_type, func.count(Document.id)).group_by(Document.document_type).all()
            doc_types = {dt: count for dt, count in doc_types_raw}
            
            stats = {
                'total_documents': total_docs,
                'total_deadlines': total_deadlines,
                'urgent_deadlines': urgent_deadlines,
                'document_types': doc_types
            }
            
            # Get all docs and deadlines
            user_docs_objs = db.query(Document).order_by(desc(Document.created_at)).all()
            user_docs = [document_to_dict(d) for d in user_docs_objs]
            
            all_dls = db.query(Deadline).order_by(desc(Deadline.created_at)).all()
            all_deadlines = []
            for dl in all_dls:
                dl_dict = deadline_to_dict(dl)
                if dl.document:
                    dl_dict['document_name'] = dl.document.filename
                    dl_dict['document_type'] = dl.document.document_type
                all_deadlines.append(dl_dict)
        
        # Add last_upload to stats
        if user_docs:
            stats['last_upload'] = user_docs[0].get('created_at') if isinstance(user_docs[0], dict) else None
        else:
            stats['last_upload'] = None
        
        # Gerar PDF
        pdf_buffer = pdf_generator.generate_dashboard_report(stats, user_docs, all_deadlines)
        
        # Nome do arquivo com data
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"relatorio_dashboard_{date_str}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


# ============================================
# SISTEMA DE PAGAMENTOS STRIPE
# ============================================

@app.get("/api/plans")
async def get_plans():
    """
    Retorna todos os planos disponiveis
    """
    return JSONResponse({
        'success': True,
        'plans': stripe_manager.get_all_plans(),
        'stripe_configured': stripe_manager.is_configured(),
        'stripe_public_key': stripe_manager.get_public_key() if stripe_manager.is_configured() else None
    })

@app.post("/api/checkout/create")
async def create_checkout(data: dict):
    """
    Cria sessao de checkout Stripe
    """
    plan_id = data.get('plan_id', 'starter')
    email = data.get('email', '')
    
    if not email:
        return JSONResponse({
            'success': False,
            'error': 'Email do cliente nao fornecido'
        }, status_code=400)
    
    try:
        plan_tier = PlanTier(plan_id)
    except ValueError:
        return JSONResponse({
            'success': False,
            'error': 'Plano invalido'
        }, status_code=400)
    
    # URLs de redirecionamento
    success_url = data.get('success_url', 'http://localhost:3000/dashboard?payment=success')
    cancel_url = data.get('cancel_url', 'http://localhost:3000/pricing?payment=cancelled')
    
    result = stripe_manager.create_checkout_session(plan_tier, email, success_url, cancel_url)
    
    if result.get('success'):
        return JSONResponse(result)
    else:
        return JSONResponse(result, status_code=400)

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Recebe webhooks do Stripe
    """
    payload = await request.body()
    signature = request.headers.get('stripe-signature', '')
    
    result = stripe_manager.handle_webhook(payload, signature)
    
    if result.get('success'):
        return JSONResponse({'received': True})
    else:
        return JSONResponse(result, status_code=400)

@app.get("/api/subscription/status")
async def subscription_status(email: str):
    """
    Verifica status da assinatura do usuario
    """
    if not email:
        return JSONResponse({
            'success': False,
            'error': 'Email nao fornecido'
        }, status_code=400)
    
    result = stripe_manager.check_subscription_status(email)
    
    # Adicionar informacoes de uso atual
    user_docs = len([d for d in documents_db if d.get('uploaded_by') == email])
    result['current_usage'] = {
        'documents_uploaded': user_docs,
        'documents_remaining': max(0, result.get('documents_limit', 5) - user_docs)
    }
    
    return JSONResponse(result)

@app.get("/api/user/limits")
async def user_limits(email: str):
    """
    Verifica limites do usuario (para verificacao antes de upload)
    """
    if not email:
        return JSONResponse({
            'success': False,
            'error': 'Email nao fornecido'
        }, status_code=400)
    
    # Contar documentos do usuario
    user_docs = len([d for d in documents_db if d.get('uploaded_by') == email])
    
    limits = check_user_limits(email, user_docs)
    
    return JSONResponse({
        'success': True,
        'limits': limits
    })

@app.post("/api/subscription/cancel")
async def cancel_subscription(data: dict):
    """
    Cancela assinatura do usuario
    """
    email = data.get('email', '')
    
    if not email:
        return JSONResponse({
            'success': False,
            'error': 'Email nao fornecido'
        }, status_code=400)
    
    result = stripe_manager.cancel_subscription(email)
    return JSONResponse(result)


# ============================================
# MFA / 2FA ENDPOINTS (Enterprise Security)
# ============================================

from tools.mfa_service import mfa_service

@app.post("/api/auth/mfa/setup")
async def mfa_setup(data: dict):
    """
    Inicia configuraÃ§Ã£o de MFA (2FA) para usuÃ¡rio
    Retorna QR Code e segredo para configuraÃ§Ã£o no Google Authenticator
    """
    user_id = data.get('user_id')
    user_email = data.get('email')
    
    if not user_id or not user_email:
        return JSONResponse({
            'success': False,
            'error': 'user_id e email sÃ£o obrigatÃ³rios'
        }, status_code=400)
    
    try:
        setup_info = mfa_service.setup_mfa(user_id, user_email)
        
        return JSONResponse({
            'success': True,
            'message': 'MFA configurado. Escaneie o QR Code com Google Authenticator.',
            'qr_code_base64': setup_info['qr_code_base64'],
            'secret': setup_info['secret'],  # Para configuraÃ§Ã£o manual
            'backup_codes': setup_info['backup_codes'],
            'instructions': setup_info['instructions']
        })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)

@app.post("/api/auth/mfa/verify")
async def mfa_verify(data: dict):
    """
    Verifica cÃ³digo MFA e habilita 2FA
    """
    user_id = data.get('user_id')
    token = data.get('token')  # CÃ³digo de 6 dÃ­gitos do app autenticador
    
    if not user_id or not token:
        return JSONResponse({
            'success': False,
            'error': 'user_id e token sÃ£o obrigatÃ³rios'
        }, status_code=400)
    
    success, message = mfa_service.verify_and_enable(user_id, token)
    
    if success:
        return JSONResponse({
            'success': True,
            'message': message,
            'mfa_enabled': True
        })
    else:
        return JSONResponse({
            'success': False,
            'error': message,
            'mfa_enabled': False
        }, status_code=400)

@app.post("/api/auth/mfa/validate")
async def mfa_validate(data: dict, request: Request):
    """
    Valida cÃ³digo MFA durante login
    Chamado apÃ³s autenticaÃ§Ã£o Firebase bem-sucedida
    
    Rate limit: 5 tentativas por minuto por user_id (proteÃ§Ã£o contra brute force)
    """
    user_id = data.get('user_id')
    token = data.get('token')
    
    # CRITICAL-001 FIX: Rate limiting especÃ­fico para MFA (5 tentativas/minuto)
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"mfa:{user_id}:{client_ip}" if user_id else f"mfa:ip:{client_ip}"
    
    allowed, info = check_rate_limit(rate_limit_key, max_requests=5, window_seconds=300)
    
    if not allowed:
        return JSONResponse({
            'success': False,
            'error': 'Muitas tentativas de MFA. Aguarde 5 minutos.',
            'access_granted': False,
            'retry_after': info.get('retry_after', 300)
        }, status_code=429)
    
    if not user_id or not token:
        return JSONResponse({
            'success': False,
            'error': 'user_id e token sÃ£o obrigatÃ³rios'
        }, status_code=400)
    
    success, message = mfa_service.verify_mfa(user_id, token)
    
    if success:
        return JSONResponse({
            'success': True,
            'message': 'MFA validado com sucesso',
            'access_granted': True
        })
    else:
        return JSONResponse({
            'success': False,
            'error': message,
            'access_granted': False
        }, status_code=401)

@app.get("/api/auth/mfa/status")
async def mfa_status(user_id: str):
    """
    Retorna status do MFA para um usuÃ¡rio
    """
    if not user_id:
        return JSONResponse({
            'success': False,
            'error': 'user_id Ã© obrigatÃ³rio'
        }, status_code=400)
    
    status = mfa_service.get_mfa_status(user_id)
    
    return JSONResponse({
        'success': True,
        'mfa_status': status
    })

@app.post("/api/auth/mfa/disable")
async def mfa_disable(data: dict):
    """
    Desabilita MFA para um usuÃ¡rio (requer confirmaÃ§Ã£o)
    """
    user_id = data.get('user_id')
    password = data.get('password')  # Para confirmaÃ§Ã£o extra
    
    if not user_id:
        return JSONResponse({
            'success': False,
            'error': 'user_id Ã© obrigatÃ³rio'
        }, status_code=400)
    
    # Em produÃ§Ã£o, verificar senha com Firebase Auth
    success, message = mfa_service.disable_mfa(user_id, password)
    
    if success:
        return JSONResponse({
            'success': True,
            'message': message,
            'mfa_enabled': False
        })
    else:
        return JSONResponse({
            'success': False,
            'error': message
        }, status_code=400)

@app.post("/api/auth/mfa/backup-codes/regenerate")
async def mfa_regenerate_backup_codes(data: dict):
    """
    Regenera cÃ³digos de backup (requer token MFA vÃ¡lido)
    """
    user_id = data.get('user_id')
    mfa_token = data.get('mfa_token')
    
    if not user_id or not mfa_token:
        return JSONResponse({
            'success': False,
            'error': 'user_id e mfa_token sÃ£o obrigatÃ³rios'
        }, status_code=400)
    
    success, result = mfa_service.regenerate_backup_codes(user_id, mfa_token)
    
    if success:
        return JSONResponse({
            'success': True,
            'message': 'CÃ³digos de backup regenerados',
            'backup_codes': result,
            'warning': 'Guarde os cÃ³digos em local seguro. Eles nÃ£o serÃ£o mostrados novamente!'
        })
    else:
        return JSONResponse({
            'success': False,
            'error': result
        }, status_code=400)


# ============================================
# CELERY ASYNC ENDPOINTS
# ============================================

@app.post("/api/documents/upload-async")
async def upload_document_async(file: UploadFile = File(...), manual_text: str = None, user_email: str = None):
    """
    Upload e processamento ASSÃNCRONO de documento
    Retorna imediatamente com task_id para polling
    """
    if not CELERY_AVAILABLE:
        return JSONResponse({
            'success': False,
            'error': 'Processamento assÃ­ncrono nÃ£o disponÃ­vel. Use /api/documents/upload',
            'code': 'CELERY_UNAVAILABLE'
        }, status_code=503)
    
    db = SessionLocal()
    try:
        # ValidaÃ§Ãµes
        if user_email and not validate_email(user_email):
            return JSONResponse({
                'success': False,
                'error': 'Email invÃ¡lido',
                'code': 'INVALID_EMAIL'
            }, status_code=400)
        
        # Verificar limites
        user = None
        if user_email:
            user = get_or_create_user_by_email(db, user_email)
            user_docs_count = len(get_user_documents(db, user.id))
            limits = check_user_limits(user_email, user_docs_count)
            
            if not limits['can_upload']:
                return JSONResponse({
                    'success': False,
                    'error': 'Limite de documentos atingido',
                    'limits': limits,
                    'upgrade_required': True
                }, status_code=403)
        
        # SECURITY: Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        validated_file = await validate_upload(
            file,
            max_size_mb=settings.MAX_FILE_SIZE_MB,
        )
        
        # SECURITY: Check prompt injection
        if manual_text:
            is_malicious, patterns = detect_prompt_injection(manual_text)
            if is_malicious:
                return JSONResponse({
                    'success': False,
                    'error': 'ConteÃºdo suspeito detectado',
                    'code': 'SECURITY_VIOLATION'
                }, status_code=400)
        
        # Ler conteÃºdo
        content = validated_file["content"]
        
        # Criar documento no banco (status: pending)
        user_id = user.id if user else None
        doc_data = {
            'user_id': user_id,
            'filename': safe_filename,
            'document_type': 'pending',
            'status': 'pending',
            'text_content': '',
            'analysis': {'status': 'queued'},
        }
        
        db_document = create_document(db, doc_data)
        doc_id = db_document.id
        db.commit()
        
        # Enfileirar processamento
        task_id = queue_document_processing(content, safe_filename, user_id, doc_id)
        
        return JSONResponse({
            'success': True,
            'message': 'Documento enfileirado para processamento',
            'document_id': doc_id,
            'task_id': task_id,
            'status': 'pending',
            'check_status_url': f'/api/tasks/{task_id}/status'
        })
        
    except Exception as e:
        db.rollback()
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)
    finally:
        db.close()


@app.get("/api/tasks/{task_id}/status")
async def get_task_status_endpoint(task_id: str):
    """
    Verifica status de uma tarefa assÃ­ncrona
    """
    if not CELERY_AVAILABLE:
        return JSONResponse({
            'success': False,
            'error': 'Celery nÃ£o disponÃ­vel',
            'code': 'CELERY_UNAVAILABLE'
        }, status_code=503)
    
    status = get_task_status(task_id)
    
    return JSONResponse({
        'success': True,
        'task': status
    })


@app.post("/api/send-email-async")
async def send_email_async_endpoint(data: dict):
    """
    Envia email de forma assÃ­ncrona
    """
    if not CELERY_AVAILABLE:
        return JSONResponse({
            'success': False,
            'error': 'Celery nÃ£o disponÃ­vel',
            'code': 'CELERY_UNAVAILABLE'
        }, status_code=503)
    
    to_email = data.get('to_email')
    subject = data.get('subject')
    html_content = data.get('html_content')
    text_content = data.get('text_content')
    
    if not all([to_email, subject, html_content]):
        return JSONResponse({
            'success': False,
            'error': 'Missing required fields: to_email, subject, html_content'
        }, status_code=400)
    
    task_id = queue_email(to_email, subject, html_content, text_content)
    
    return JSONResponse({
        'success': True,
        'message': 'Email enfileirado',
        'task_id': task_id,
        'check_status_url': f'/api/tasks/{task_id}/status'
    })


# ============================================
# RATE LIMITING MIDDLEWARE
# ============================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware de rate limiting global
    Limita requisiÃ§Ãµes por IP
    """
    # Skip rate limiting para health checks e static files
    path = request.url.path
    if path in ['/api/health', '/api/status'] or path.startswith('/static'):
        return await call_next(request)
    
    # Get client IP
    client_ip = request.headers.get('X-Forwarded-For')
    if not client_ip and request.client:
        client_ip = request.client.host
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    else:
        client_ip = "127.0.0.1"  # Fallback para testes

    # Em desenvolvimento local, nao bloquear navegacao e testes automatizados.
    if settings.ENVIRONMENT != "production" and client_ip in {"127.0.0.1", "::1", "localhost"}:
        response = await call_next(request)
        response.headers['X-RateLimit-Bypass'] = 'local-development'
        response.headers['X-RateLimit-Limit'] = '100'
        response.headers['X-RateLimit-Remaining'] = '100'
        return response
    
    # Check rate limit (100 requests per minute per IP)
    allowed, info = check_rate_limit(f"ip:{client_ip}", max_requests=100, window_seconds=60)
    
    if not allowed:
        return JSONResponse(
            {
                'success': False,
                'error': 'Rate limit excedido',
                'retry_after': info.get('retry_after', 60),
                'limit': info.get('limit', 100),
                'remaining': info.get('remaining', 0),
            },
            status_code=429,
            headers={'Retry-After': str(info.get('retry_after', 60))}
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers['X-RateLimit-Limit'] = str(info.get('limit', 100))
    response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
    
    return response


@app.post("/api/chat/premium")
async def premium_chat_endpoint(
    data: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Endpoint Premium de Chat
    Usa o motor de IA com 25 etapas de humanizaÃ§Ã£o e contexto
    
    Features:
    - Respostas humanizadas e naturais
    - MemÃ³ria contextual
    - FormataÃ§Ã£o premium
    - Anti-repetiÃ§Ã£o
    - DetecÃ§Ã£o de intenÃ§Ã£o
    """
    user_message = data.get('message', '')
    document_context = data.get('document_context', '')
    response_mode = data.get('response_mode', 'balanced')
    jurisdiction = data.get('jurisdiction', 'Brasil - federal')
    legal_area = data.get('legal_area')

    user = db.query(User).filter(User.id == int(current_user.user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Usuario nao encontrado ou inativo",
        )

    conversation_id = re.sub(
        r"[^a-zA-Z0-9_-]",
        "",
        str(data.get('conversation_id') or "default"),
    )[:64] or "default"
    user_id = f"{user.id}:{conversation_id}"
    
    if not user_message:
        return JSONResponse({
            'success': False,
            'error': 'Mensagem nÃ£o fornecida'
        }, status_code=400)
    
    if len(user_message) > 12000:
        return JSONResponse({
            'success': False,
            'error': 'Mensagem excede o limite de 12000 caracteres'
        }, status_code=400)

    document_context = str(document_context)[:20000]

    if response_mode not in {'quick', 'balanced', 'deep'}:
        response_mode = 'balanced'

    if not PREMIUM_AI_AVAILABLE or not premium_ai_engine or not legal_ai_orchestrator:
        return JSONResponse({
            'success': False,
            'error': 'Motor Premium nÃ£o disponÃ­vel',
            'ai_mode': 'unavailable'
        }, status_code=503)
    
    try:
        # Gerar resposta premium
        result = await legal_ai_orchestrator.answer(
            user_message=user_message,
            user_id=user_id,
            document_context=document_context,
            response_mode=response_mode,
            jurisdiction=jurisdiction,
            legal_area=legal_area,
        )
        legal_metadata = result.get('legal_metadata', {})
        
        return JSONResponse({
            'success': True,
            'response': result['response'],
            'metadata': {
                'quality_score': result.get('quality_score', 0),
                'style': result.get('style', 'standard'),
                'detected_intent': result.get('detected_intent', ''),
                'emotional_state': result.get('emotional_state', 'neutral'),
                'context_summary': result.get('context_summary', ''),
                'ai_mode': 'premium',
                'plan_tier': user.plan_tier or 'starter',
                'conversation_id': conversation_id,
                'interaction_count': result.get('metadata', {}).get('interaction_count', 0),
                'document_context_used': bool(document_context),
                'response_mode': legal_metadata.get('response_mode', response_mode),
                'is_legal_query': legal_metadata.get('is_legal_query', False),
                'is_professional_query': legal_metadata.get(
                    'is_professional_query',
                    legal_metadata.get('is_legal_query', False),
                ),
                'legal_area': legal_metadata.get('legal_area', 'geral'),
                'professional_domain': legal_metadata.get(
                    'professional_domain',
                    'geral',
                ),
                'jurisdiction': legal_metadata.get('jurisdiction', jurisdiction),
                'grounding_status': legal_metadata.get('grounding_status', 'unverified'),
                'sources': legal_metadata.get('sources', []),
                'sovereign_sources': legal_metadata.get(
                    'sovereign_sources',
                    [],
                ),
                'sovereign_search_used': legal_metadata.get(
                    'sovereign_search_used',
                    False,
                ),
                'realtime_web_used': legal_metadata.get(
                    'realtime_web_used',
                    False,
                ),
                'realtime_web_status': legal_metadata.get(
                    'realtime_web_status',
                    'not_requested',
                ),
                'realtime_retrieved_at': legal_metadata.get(
                    'realtime_retrieved_at',
                ),
                'realtime_latency_ms': legal_metadata.get(
                    'realtime_latency_ms',
                    0,
                ),
                'realtime_cache_hit': legal_metadata.get(
                    'realtime_cache_hit',
                    False,
                ),
                'realtime_sources': legal_metadata.get(
                    'realtime_sources',
                    [],
                ),
                'realtime_errors': legal_metadata.get(
                    'realtime_errors',
                    [],
                ),
                'inline_citations': legal_metadata.get('inline_citations', 0),
                'source_markers': legal_metadata.get('source_markers', 0),
                'verified_article_citations': legal_metadata.get(
                    'verified_article_citations',
                    [],
                ),
                'citation_quality': legal_metadata.get('citation_quality', 'none'),
                'confidence_level': legal_metadata.get('confidence_level', 'geral'),
                'response_complete': legal_metadata.get('response_complete', True),
                'finish_reason': legal_metadata.get('finish_reason', 'stop'),
                'verified_articles': legal_metadata.get('verified_articles', []),
                'unverified_article_references': legal_metadata.get(
                    'unverified_article_references',
                    [],
                ),
                'suppressed_article_references': legal_metadata.get(
                    'suppressed_article_references',
                    [],
                ),
                'suppressed_unsupported_lines': legal_metadata.get(
                    'suppressed_unsupported_lines',
                    0,
                ),
                'suppressed_unsupported_jurisprudence_lines': legal_metadata.get(
                    'suppressed_unsupported_jurisprudence_lines',
                    0,
                ),
                'suppressed_mismatched_paragraph_lines': legal_metadata.get(
                    'suppressed_mismatched_paragraph_lines',
                    0,
                ),
                'suppressed_mismatched_curated_claim_lines': legal_metadata.get(
                    'suppressed_mismatched_curated_claim_lines',
                    0,
                ),
                'suppressed_invalid_source_lines': legal_metadata.get(
                    'suppressed_invalid_source_lines',
                    0,
                ),
                'suppressed_invalid_realtime_lines': legal_metadata.get(
                    'suppressed_invalid_realtime_lines',
                    0,
                ),
                'prompt_leak_blocked': legal_metadata.get(
                    'prompt_leak_blocked',
                    False,
                ),
                'requires_human_review': legal_metadata.get('requires_human_review', False),
                'review_role': legal_metadata.get('review_role', 'usuario'),
                'contingency_mode': legal_metadata.get(
                    'contingency_mode',
                    False,
                ),
                'answer_scope': legal_metadata.get('answer_scope', 'assistencia_geral'),
                'model': legal_metadata.get(
                    'model',
                    result.get('metadata', {}).get('model', 'llama-3.1-8b-instant'),
                ),
                'requested_model': legal_metadata.get(
                    'requested_model',
                    result.get('metadata', {}).get('model', 'llama-3.1-8b-instant'),
                ),
                'provider': legal_metadata.get(
                    'provider',
                    result.get('metadata', {}).get('provider', 'unknown'),
                ),
                'route': legal_metadata.get(
                    'route',
                    result.get('metadata', {}).get('route', ''),
                ),
                'usage': legal_metadata.get(
                    'usage',
                    result.get('metadata', {}).get('usage', {}),
                ),
                'latency_ms': legal_metadata.get(
                    'latency_ms',
                    legal_metadata.get(
                        'total_ms',
                        result.get('metadata', {}).get('latency_ms', 0),
                    ),
                ),
                'total_ms': legal_metadata.get(
                    'total_ms',
                    legal_metadata.get(
                        'latency_ms',
                        result.get('metadata', {}).get('latency_ms', 0),
                    ),
                ),
                'provider_fallback_used': legal_metadata.get(
                    'provider_fallback_used',
                    result.get('metadata', {}).get(
                        'provider_fallback_used',
                        False,
                    ),
                ),
                'model_degraded': legal_metadata.get('model_degraded', False),
                'model_fallback_used': legal_metadata.get(
                    'model_fallback_used',
                    False,
                ),
            }
        })
        
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': f'Erro no motor premium: {str(e)}',
            'ai_mode': 'error'
        }, status_code=500)


@app.get("/api/ai/status")
async def ai_status():
    """
    Retorna status dos motores de IA
    """
    return JSONResponse({
        'premium_ai': {
            'available': PREMIUM_AI_AVAILABLE,
            'features': [
                'personalidade_avancada',
                'anti_repeticao',
                'memoria_contextual',
                'formatacao_premium',
                'raciocinio_inteligente',
                'humanizacao_extrema',
                'deteccao_intencao',
                'profundidade_dinamica',
                'emocao_contextual',
                'auto_critica'
            ] if PREMIUM_AI_AVAILABLE else []
        },
        'standard_ai': {
            'available': True,
            'engine': 'LexScan Engine'
        },
        'status': 'online'
    })


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
