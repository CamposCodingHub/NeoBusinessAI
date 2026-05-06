"""
PostgreSQL Optimizations - LexScan IA
Índices, PgBouncer config e otimizações de queries
"""

"""
PostgreSQL Database Optimizations - LexScan IA
Migrations, indexes, and query optimizations
"""

from sqlalchemy import text, Index
from database import engine, Base, SessionLocal
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ÍNDICES RECOMENDADOS PARA PERFORMANCE
# =============================================================================

RECOMMENDED_INDEXES = [
    # User indexes
    {
        'table': 'users',
        'name': 'idx_users_email',
        'columns': ['email'],
        'unique': True,
        'reason': 'Busca rápida por email (login, queries)'
    },
    {
        'table': 'users',
        'name': 'idx_users_firebase_uid',
        'columns': ['firebase_uid'],
        'unique': True,
        'reason': 'Lookup por Firebase UID'
    },
    {
        'table': 'users',
        'name': 'idx_users_plan_tier',
        'columns': ['plan_tier'],
        'unique': False,
        'reason': 'Filtrar por tier de plano'
    },
    
    # Document indexes
    {
        'table': 'documents',
        'name': 'idx_documents_user_id',
        'columns': ['user_id'],
        'unique': False,
        'reason': 'Listar documentos do usuário (muito frequente)'
    },
    {
        'table': 'documents',
        'name': 'idx_documents_user_created',
        'columns': ['user_id', 'created_at'],
        'unique': False,
        'reason': 'Ordenar documentos por data'
    },
    {
        'table': 'documents',
        'name': 'idx_documents_status',
        'columns': ['status'],
        'unique': False,
        'reason': 'Filtrar por status (pending, processing, etc)'
    },
    {
        'table': 'documents',
        'name': 'idx_documents_document_type',
        'columns': ['document_type'],
        'unique': False,
        'reason': 'Filtrar por tipo de documento'
    },
    {
        'table': 'documents',
        'name': 'idx_documents_process_number',
        'columns': ['process_number'],
        'unique': False,
        'reason': 'Buscar por número de processo'
    },
    
    # Deadline indexes
    {
        'table': 'deadlines',
        'name': 'idx_deadlines_user_id',
        'columns': ['user_id'],
        'unique': False,
        'reason': 'Listar prazos do usuário'
    },
    {
        'table': 'deadlines',
        'name': 'idx_deadlines_document_id',
        'columns': ['document_id'],
        'unique': False,
        'reason': 'Buscar prazos por documento'
    },
    {
        'table': 'deadlines',
        'name': 'idx_deadlines_urgency',
        'columns': ['urgency'],
        'unique': False,
        'reason': 'Filtrar por urgência (high/medium/low)'
    },
    {
        'table': 'deadlines',
        'name': 'idx_deadlines_due_date',
        'columns': ['due_date'],
        'unique': False,
        'reason': 'Ordenar por data de vencimento'
    },
    {
        'table': 'deadlines',
        'name': 'idx_deadlines_user_urgent',
        'columns': ['user_id', 'urgency', 'is_completed'],
        'unique': False,
        'reason': 'Dashboard: prazos urgentes pendentes'
    },
    
    # Chat message indexes
    {
        'table': 'chat_messages',
        'name': 'idx_chat_document_user',
        'columns': ['document_id', 'user_id'],
        'unique': False,
        'reason': 'Buscar histórico de chat'
    },
    {
        'table': 'chat_messages',
        'name': 'idx_chat_created',
        'columns': ['created_at'],
        'unique': False,
        'reason': 'Limpar mensagens antigas'
    },
    
    # Notification indexes
    {
        'table': 'notifications',
        'name': 'idx_notifications_user_read',
        'columns': ['user_id', 'is_read'],
        'unique': False,
        'reason': 'Contar notificações não lidas'
    },
    
    # Activity log indexes
    {
        'table': 'activity_logs',
        'name': 'idx_activity_user_time',
        'columns': ['user_id', 'created_at'],
        'unique': False,
        'reason': 'Auditoria: atividade do usuário'
    },
    {
        'table': 'activity_logs',
        'name': 'idx_activity_event_type',
        'columns': ['event_type'],
        'unique': False,
        'reason': 'Buscar por tipo de evento'
    },
]


def create_indexes():
    """Cria todos os índices recomendados"""
    logger.info("=" * 60)
    logger.info("CRIANDO ÍNDICES DO POSTGRESQL")
    logger.info("=" * 60)
    
    with engine.connect() as conn:
        for idx in RECOMMENDED_INDEXES:
            try:
                unique_str = "UNIQUE " if idx['unique'] else ""
                columns_str = ', '.join(idx['columns'])
                
                sql = f"""
                    CREATE {unique_str} INDEX IF NOT EXISTS {idx['name']} 
                    ON {idx['table']} ({columns_str})
                """
                
                conn.execute(text(sql))
                conn.commit()
                
                logger.info(f"✅ {idx['name']} em {idx['table']}")
                logger.info(f"   └─ {idx['reason']}")
                
            except Exception as e:
                logger.error(f"❌ Erro criando {idx['name']}: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("ÍNDICES CRIADOS COM SUCESSO!")
    logger.info("=" * 60)


def analyze_table_stats():
    """Atualiza estatísticas das tabelas para o query planner"""
    logger.info("\n📊 Analisando estatísticas das tabelas...")
    
    with engine.connect() as conn:
        tables = ['users', 'documents', 'deadlines', 'chat_messages', 'notifications']
        
        for table in tables:
            try:
                conn.execute(text(f"ANALYZE {table}"))
                logger.info(f"✅ Estatísticas atualizadas: {table}")
            except Exception as e:
                logger.error(f"❌ Erro em {table}: {e}")


def get_slow_queries():
    """Consulta para identificar queries lentas (requer pg_stat_statements)"""
    logger.info("\n🐌 Verificando queries lentas...")
    
    queries = [
        """
        -- Habilitar pg_stat_statements (executar como superuser)
        CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
        """,
        """
        -- Queries mais lentas (média)
        SELECT 
            query,
            calls,
            mean_time,
            max_time,
            rows
        FROM pg_stat_statements 
        WHERE mean_time > 100  -- mais de 100ms
        ORDER BY mean_time DESC 
        LIMIT 10;
        """,
    ]
    
    logger.info("⚠️ Execute estas queries manualmente como superuser")
    for q in queries:
        logger.info(f"\n{q}")


# =============================================================================
# PGBOUNCER CONFIGURATION
# =============================================================================

PGBOUNCER_CONFIG = """
; ========================================
; PgBouncer Configuration - LexScan IA
; Connection Pooling for PostgreSQL
; ========================================

[databases]
; Mapeamento de bancos de dados
lexscan = host=localhost port=5432 dbname=lexscan

[pgbouncer]
; Configurações de Pool
pool_mode = transaction           ; Melhor para aplicações web
max_client_conn = 1000            ; Máximo de conexões clientes
default_pool_size = 25            ; Conexões por banco
min_pool_size = 5                 ; Manter conexões quentes
reserve_pool_size = 5              ; Reserva para spikes
reserve_pool_timeout = 3           ; Segundos para usar reserva

; Timeouts (em segundos)
server_lifetime = 3600            ; Reciclar conexões a cada 1h
server_idle_timeout = 600          ; Fechar conexões ociosas após 10min
server_connect_timeout = 10       ; Timeout de conexão
server_login_retry = 15           ; Retry após falha
query_timeout = 60                ; Timeout de query
query_wait_timeout = 30           ; Tempo máximo na fila
client_idle_timeout = 0           ; Não desconectar clientes ociosos
client_login_timeout = 10          ; Timeout de autenticação

; Segurança
auth_type = md5                   ; Autenticação MD5
auth_file = /etc/pgbouncer/userlist.txt
admin_users = postgres, admin     ; Usuários admin
stats_users = stats               ; Usuários para estatísticas

; Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60

; Performance
tcp_keepalive = 1
tcp_keepcnt = 3
tcp_keepidle = 30
tcp_keepintvl = 10

; Listener
listen_addr = 0.0.0.0
listen_port = 6432
unix_socket_dir = /var/run/postgresql

; SSL (desabilitado em dev, habilitar em prod)
; server_tls_sslmode = require
; server_tls_cert_file = /path/to/server.crt
; server_tls_key_file = /path/to/server.key
"""


def generate_pgbouncer_config():
    """Gera arquivo de configuração do PgBouncer"""
    config_path = "pgbouncer/pgbouncer.ini"
    
    import os
    os.makedirs("pgbouncer", exist_ok=True)
    
    with open(config_path, 'w') as f:
        f.write(PGBOUNCER_CONFIG)
    
    logger.info(f"✅ Configuração PgBouncer salva em: {config_path}")
    logger.info("\nPara usar PgBouncer:")
    logger.info("1. Instale: apt-get install pgbouncer")
    logger.info("2. Copie config: cp pgbouncer/pgbouncer.ini /etc/pgbouncer/")
    logger.info("3. Configure usuários: pgbouncer/pgbouncer_auth.py")
    logger.info("4. Inicie: systemctl start pgbouncer")
    logger.info("5. Conecte via porta 6432 ao invés de 5432")


# =============================================================================
# QUERY OPTIMIZATIONS
# =============================================================================

QUERY_OPTIMIZATIONS = {
    'N+1 Queries': {
        'problem': 'Documentos carregando deadlines um por um',
        'solution': 'Usar joinedload ou selectinload do SQLAlchemy',
        'code_before': '''
# PROBLEMA: N+1 queries
docs = db.query(Document).filter_by(user_id=user_id).all()
for doc in docs:
    deadlines_count = len(doc.deadlines)  # Query extra!
        ''',
        'code_after': '''
# SOLUÇÃO: Eager loading
from sqlalchemy.orm import joinedload

docs = db.query(Document).options(
    joinedload(Document.deadlines)
).filter_by(user_id=user_id).all()
        '''
    },
    
    'Full Table Scan': {
        'problem': 'Queries sem WHERE em tabelas grandes',
        'solution': 'Sempre usar índices e filtros',
        'code_before': '''
# PROBLEMA: Full scan
docs = db.query(Document).all()  # Pega TUDO
        ''',
        'code_after': '''
# SOLUÇÃO: Paginação + índice
docs = db.query(Document).filter_by(
    user_id=user_id
).order_by(
    Document.created_at.desc()
).limit(50).offset(page * 50).all()
        '''
    },
    
    'Count Optimization': {
        'problem': 'COUNT(*) em tabelas grandes é lento',
        'solution': 'Usar estimativas ou cache',
        'code_before': '''
# PROBLEMA: Count lento
total = db.query(func.count(Document.id)).scalar()
        ''',
        'code_after': '''
# SOLUÇÃO: Cache ou approx count
total = redis.get(f'count:documents:{user_id}')
if not total:
    total = db.query(func.count(Document.id)).filter_by(user_id=user_id).scalar()
    redis.setex(f'count:documents:{user_id}', 60, total)
        '''
    },
}


def print_query_optimizations():
    """Imprime guia de otimizações de queries"""
    logger.info("\n" + "=" * 60)
    logger.info("GUIA DE OTIMIZAÇÃO DE QUERIES")
    logger.info("=" * 60)
    
    for title, opt in QUERY_OPTIMIZATIONS.items():
        logger.info(f"\n🔴 {title}")
        logger.info(f"   Problema: {opt['problem']}")
        logger.info(f"   Solução: {opt['solution']}")
        logger.info(f"\n   Antes:\n{opt['code_before']}")
        logger.info(f"\n   Depois:\n{opt['code_after']}")


# =============================================================================
# MAINTENANCE PROCEDURES
# =============================================================================

MAINTENANCE_QUERIES = """
-- ========================================
-- ROTINA DE MANUTENÇÃO SEMANAL
-- ========================================

-- 1. VACUUM (reclamar espaço e atualizar estatísticas)
VACUUM ANALYZE;

-- 2. Reindex (reconstruir índices fragmentados)
REINDEX DATABASE lexscan;

-- 3. Limpar logs antigos (mais de 90 dias)
DELETE FROM activity_logs WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM chat_messages WHERE created_at < NOW() - INTERVAL '30 days';

-- 4. Verificar tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 5. Verificar índices não utilizados
SELECT 
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan < 50
ORDER BY pg_relation_size(indexrelid) DESC;

-- 6. Verificar locks ativos
SELECT * FROM pg_locks WHERE NOT granted;

-- 7. Verificar queries longas (mais de 5 minutos)
SELECT 
    pid,
    state,
    query_start,
    NOW() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state = 'active' 
    AND NOW() - query_start > interval '5 minutes';
"""


def generate_maintenance_script():
    """Gera script de manutenção"""
    with open('database_maintenance.sql', 'w') as f:
        f.write(MAINTENANCE_QUERIES)
    
    logger.info("\n✅ Script de manutenção salvo: database_maintenance.sql")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("POSTGRESQL OPTIMIZATION TOOLKIT - LEXSCAN IA")
    print("=" * 70)
    
    print("\n1. Criando índices recomendados...")
    create_indexes()
    
    print("\n2. Atualizando estatísticas...")
    analyze_table_stats()
    
    print("\n3. Gerando configuração PgBouncer...")
    generate_pgbouncer_config()
    
    print("\n4. Guia de otimização de queries...")
    print_query_optimizations()
    
    print("\n5. Gerando script de manutenção...")
    generate_maintenance_script()
    
    print("\n" + "=" * 70)
    print("OTIMIZAÇÕES APLICADAS!")
    print("=" * 70)
    print("\nPróximos passos:")
    print("• Execute database_maintenance.sql semanalmente")
    print("• Configure PgBouncer para connection pooling")
    print("• Monitore queries lentas com pg_stat_statements")
    print("• Ajuste shared_buffers e work_mem no postgresql.conf")
    print("• Configure backups automáticos (pg_dump + WAL)")
    print("=" * 70)
