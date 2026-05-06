"""
Celery Tasks - LexScan IA
Processamento assíncrono para operações pesadas
"""

import os
from celery import Celery
from typing import Dict, Any
import json

# Configuração Celery com Redis
# URL do broker (Redis)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

app = Celery('lexscan_tasks', broker=REDIS_URL, backend=REDIS_URL)

# Configurações Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutos máximo
    worker_prefetch_multiplier=1,  # Um job por worker de cada vez
    worker_max_tasks_per_child=1000,  # Restart worker após 1000 tasks
)

# =============================================================================
# TAREFAS DE PROCESSAMENTO DE DOCUMENTOS
# =============================================================================

@app.task(bind=True, max_retries=3)
def process_document_async(self, file_bytes: bytes, filename: str, user_id: int, doc_id: int = None):
    """
    Processa documento de forma assíncrona (OCR + análise)
    
    Args:
        file_bytes: Bytes do arquivo
        filename: Nome do arquivo
        user_id: ID do usuário
        doc_id: ID do documento (se já criado)
    
    Returns:
        Dict com resultado do processamento
    """
    from tools.ocr_real import process_uploaded_file
    from database import SessionLocal, update_document, get_document
    
    try:
        print(f"[CELERY] Iniciando processamento: {filename} (user_id: {user_id})")
        
        # Atualiza status para processing
        db = SessionLocal()
        if doc_id:
            update_document(db, doc_id, {'status': 'processing'})
        
        # 1. OCR
        ocr_result = process_uploaded_file(file_bytes, filename)
        
        if not ocr_result['success']:
            # Falha no OCR
            if doc_id:
                update_document(db, doc_id, {
                    'status': 'ocr_failed',
                    'analysis': {'error': ocr_result.get('error')}
                })
            db.close()
            return {
                'success': False,
                'error': ocr_result.get('error', 'OCR failed'),
                'stage': 'ocr'
            }
        
        text_content = ocr_result['text']
        
        # 2. Análise com LexScan Engine
        from ai.lexscan_engine import lexscan_engine
        analysis_result = lexscan_engine.process_document(text_content)
        
        # 3. Atualiza documento no banco
        if doc_id:
            update_data = {
                'status': 'completed',
                'document_type': analysis_result.get('document_type', 'unknown'),
                'process_number': analysis_result.get('process_number', ''),
                'court': analysis_result.get('court', ''),
                'text_content': text_content[:10000],  # Limitado
                'analysis': analysis_result,
                'summary': analysis_result.get('summary', ''),
                'parties': analysis_result.get('parties', {}),
                'values': analysis_result.get('values', [])
            }
            update_document(db, doc_id, update_data)
            
            # Criar deadlines se existirem
            from database import create_deadline
            deadlines = analysis_result.get('deadlines', [])
            for dl in deadlines:
                deadline_data = {
                    'user_id': user_id,
                    'document_id': doc_id,
                    'days': dl.get('days', 0),
                    'urgency': dl.get('urgency', 'medium'),
                    'context': dl.get('context', ''),
                    'description': dl.get('description', '')
                }
                create_deadline(db, deadline_data)
        
        db.close()
        
        print(f"[CELERY] Processamento completo: {filename}")
        
        return {
            'success': True,
            'document_id': doc_id,
            'pages': ocr_result.get('pages', 1),
            'text_length': len(text_content),
            'analysis': analysis_result
        }
        
    except Exception as exc:
        print(f"[CELERY] Erro no processamento: {exc}")
        # Retry com backoff
        self.retry(countdown=60, exc=exc)


@app.task(bind=True, max_retries=2)
def generate_report_async(self, doc_id: int, report_type: str = 'document'):
    """
    Gera relatório PDF de forma assíncrona
    
    Args:
        doc_id: ID do documento
        report_type: Tipo de relatório ('document' ou 'dashboard')
    
    Returns:
        Dict com resultado
    """
    from database import SessionLocal, get_document, get_user_documents, get_user_deadlines
    from tools.pdf_generator import pdf_generator
    
    try:
        print(f"[CELERY] Gerando relatório: doc_id={doc_id}, type={report_type}")
        
        db = SessionLocal()
        
        if report_type == 'document':
            doc = get_document(db, doc_id)
            if not doc:
                db.close()
                return {'success': False, 'error': 'Documento não encontrado'}
            
            from database import document_to_dict
            doc_dict = document_to_dict(doc)
            pdf_buffer = pdf_generator.generate_document_report(doc_dict)
            
        else:  # dashboard
            doc = get_document(db, doc_id)
            if not doc:
                db.close()
                return {'success': False, 'error': 'Documento não encontrado'}
            
            # Stats do usuário
            from database import get_user_stats, document_to_dict, deadline_to_dict
            stats = get_user_stats(db, doc.user_id)
            user_docs_objs = get_user_documents(db, doc.user_id)
            user_docs = [document_to_dict(d) for d in user_docs_objs]
            
            user_deadlines = get_user_deadlines(db, doc.user_id)
            all_deadlines = [deadline_to_dict(d) for d in user_deadlines]
            
            pdf_buffer = pdf_generator.generate_dashboard_report(
                stats, user_docs, all_deadlines
            )
        
        db.close()
        
        # Salvar em arquivo temporário ou S3
        # Por enquanto, retorna bytes
        return {
            'success': True,
            'pdf_size': len(pdf_buffer.getvalue()),
            'report_type': report_type
        }
        
    except Exception as exc:
        print(f"[CELERY] Erro gerando relatório: {exc}")
        self.retry(countdown=30, exc=exc)


# =============================================================================
# TAREFAS DE EMAIL
# =============================================================================

@app.task(bind=True, max_retries=3)
def send_email_async(self, to_email: str, subject: str, html_content: str, text_content: str = None):
    """
    Envia email de forma assíncrona
    
    Args:
        to_email: Destinatário
        subject: Assunto
        html_content: Conteúdo HTML
        text_content: Conteúdo texto (opcional)
    
    Returns:
        Dict com resultado
    """
    from tools.notifications import notification_manager
    
    try:
        print(f"[CELERY] Enviando email para: {to_email}")
        
        result = notification_manager.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        return result
        
    except Exception as exc:
        print(f"[CELERY] Erro enviando email: {exc}")
        self.retry(countdown=120, exc=exc)  # Retry em 2 minutos


@app.task(bind=True, max_retries=2)
def check_and_notify_deadlines(self):
    """
    Verifica prazos próximos e envia notificações
    
    Executado periodicamente (cron job)
    """
    from database import SessionLocal
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        print("[CELERY] Verificando prazos...")
        
        db = SessionLocal()
        
        # Busca deadlines urgentes (próximos 3 dias)
        from database import Deadline, User
        
        three_days = datetime.now() + timedelta(days=3)
        
        urgent_deadlines = db.query(Deadline, User).join(User).filter(
            Deadline.is_completed == False,
            Deadline.urgency == 'high'
        ).all()
        
        notifications_sent = 0
        
        for deadline, user in urgent_deadlines:
            # Enviar notificação
            subject = f"⏰ Prazo Urgente: {deadline.description[:50]}..."
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #dc2626;">⚠️ Prazo Urgente!</h2>
                <p><strong>Descrição:</strong> {deadline.description}</p>
                <p><strong>Contexto:</strong> {deadline.context}</p>
                <p><strong>Urgência:</strong> {deadline.urgency}</p>
                <br>
                <p>Acesse o LexScan IA para mais detalhes.</p>
            </body>
            </html>
            """
            
            # Envia async
            send_email_async.delay(user.email, subject, html_content)
            notifications_sent += 1
        
        db.close()
        
        print(f"[CELERY] Notificações enviadas: {notifications_sent}")
        
        return {
            'success': True,
            'notifications_sent': notifications_sent,
            'urgent_deadlines_found': len(urgent_deadlines)
        }
        
    except Exception as exc:
        print(f"[CELERY] Erro verificando prazos: {exc}")
        self.retry(countdown=300, exc=exc)


# =============================================================================
# TAREFAS DE LIMPEZA E MANUTENÇÃO
# =============================================================================

@app.task
def cleanup_old_documents(days: int = 30):
    """
    Remove documentos antigos (soft delete)
    
    Args:
        days: Documentos mais antigos que X dias
    """
    from database import SessionLocal
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Soft delete - marca como deleted
    from sqlalchemy import update
    from database import Document
    
    result = db.execute(
        update(Document)
        .where(Document.created_at < cutoff_date)
        .where(Document.status != 'deleted')
        .values(status='deleted')
    )
    
    db.commit()
    db.close()
    
    print(f"[CELERY] Documentos marcados como deleted: {result.rowcount}")
    
    return {
        'success': True,
        'documents_marked': result.rowcount
    }


# =============================================================================
# SCHEDULE (Agendamento de tarefas periódicas)
# =============================================================================

app.conf.beat_schedule = {
    'check-deadlines-every-hour': {
        'task': 'tasks.check_and_notify_deadlines',
        'schedule': 3600.0,  # A cada hora
    },
    'cleanup-old-documents-daily': {
        'task': 'tasks.cleanup_old_documents',
        'schedule': 86400.0,  # Uma vez por dia
        'args': (90,)  # Documentos com 90+ dias
    },
}


# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def queue_document_processing(file_bytes: bytes, filename: str, user_id: int, doc_id: int = None):
    """
    Enfileira processamento de documento
    
    Args:
        file_bytes: Bytes do arquivo
        filename: Nome do arquivo
        user_id: ID do usuário
        doc_id: ID do documento (opcional)
    
    Returns:
        task_id: ID da tarefa Celery
    """
    task = process_document_async.delay(file_bytes, filename, user_id, doc_id)
    return task.id


def queue_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """
    Enfileira envio de email
    
    Args:
        to_email: Destinatário
        subject: Assunto
        html_content: Conteúdo HTML
        text_content: Conteúdo texto
    
    Returns:
        task_id: ID da tarefa Celery
    """
    task = send_email_async.delay(to_email, subject, html_content, text_content)
    return task.id


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Obtém status de uma tarefa
    
    Args:
        task_id: ID da tarefa
    
    Returns:
        Dict com status e resultado
    """
    result = app.AsyncResult(task_id)
    
    return {
        'task_id': task_id,
        'status': result.status,
        'ready': result.ready(),
        'successful': result.successful() if result.ready() else None,
        'result': result.result if result.ready() and result.successful() else None,
        'error': str(result.result) if result.ready() and not result.successful() else None
    }


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CELERY TASKS - LexScan IA")
    print("=" * 60)
    print("\nTarefas disponíveis:")
    print("  1. process_document_async")
    print("  2. generate_report_async")
    print("  3. send_email_async")
    print("  4. check_and_notify_deadlines")
    print("  5. cleanup_old_documents")
    print("\nPara iniciar worker:")
    print("  celery -A tasks worker --loglevel=info")
    print("\nPara iniciar beat (scheduler):")
    print("  celery -A tasks beat --loglevel=info")
    print("=" * 60)
