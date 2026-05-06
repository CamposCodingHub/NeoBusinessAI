"""
Database Configuration
======================
Setup de PostgreSQL com suporte multi-tenant.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco.
    Garante fechamento automático.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa o banco de dados (cria tabelas)"""
    from models.tenant import Tenant
    from models.user import User, Device, RefreshToken
    from models.subscription import Subscription, Invoice
    from models.document import Document
    from models.audit_log import AuditLog
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def set_tenant_context(tenant_id: str):
    """
    Define o contexto do tenant para a sessão atual.
    Usado com Row Level Security (RLS).
    """
    from sqlalchemy import text
    
    with engine.connect() as conn:
        conn.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        conn.commit()
