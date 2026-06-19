"""
Multi-Tenancy Database Layer
=============================
Isolamento de dados por tenant para SaaS multi-tenant
Baseado em referências enterprise (SAP, Snowflake)
"""

from sqlalchemy import Column, String, Integer, CheckConstraint, Index
from sqlalchemy.orm import declared_attr
from database import Base


class TenantAwareMixin:
    """
    Mixin para adicionar isolamento de tenant aos modelos
    """
    @declared_attr
    def tenant_id(cls):
        return Column(String(128), nullable=False, index=True, default='default')
    
    __table_args__ = (
        CheckConstraint('tenant_id IS NOT NULL', name='ck_tenant_id_not_null'),
    )


class Tenant(Base):
    """Modelo de Tenant (organização/empresa)"""
    __tablename__ = 'tenants'
    
    id = Column(String(128), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    plan_tier = Column(String(50), default='free')  # free, starter, professional, business
    status = Column(String(50), default='active')  # active, suspended, cancelled
    settings = Column(dict, default={})
    created_at = Column(Integer, default=lambda: int(__import__('datetime').datetime.utcnow().timestamp()))
    updated_at = Column(Integer, default=lambda: int(__import__('datetime').datetime.utcnow().timestamp()))
    
    # Limites por plano
    documents_limit = Column(Integer, default=5)
    users_limit = Column(Integer, default=1)
    api_calls_limit = Column(Integer, default=1000)
    
    # Métricas de uso
    documents_count = Column(Integer, default=0)
    users_count = Column(Integer, default=0)
    api_calls_count = Column(Integer, default=0)
    
    # Índices
    __table_args__ = (
        Index('idx_tenant_slug', 'slug'),
        Index('idx_tenant_plan', 'plan_tier'),
        Index('idx_tenant_status', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'plan_tier': self.plan_tier,
            'status': self.status,
            'documents_limit': self.documents_limit,
            'users_limit': self.users_limit,
            'api_calls_limit': self.api_calls_limit,
            'documents_count': self.documents_count,
            'users_count': self.users_count,
            'api_calls_count': self.api_calls_count,
        }


class TenantUser(Base):
    """Relação entre Tenant e User"""
    __tablename__ = 'tenant_users'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(50), default='member')  # owner, admin, member
    invited_at = Column(Integer, default=lambda: int(__import__('datetime').datetime.utcnow().timestamp()))
    joined_at = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_tenant_user_tenant', 'tenant_id'),
        Index('idx_tenant_user_user', 'user_id'),
        Index('idx_tenant_user_role', 'role'),
    )


class TenantUsage(Base):
    """Métricas de uso por tenant"""
    __tablename__ = 'tenant_usage'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    period = Column(String(20), nullable=False)  # YYYY-MM
    metric_type = Column(String(50), nullable=False)  # documents, api_calls, storage
    value = Column(Integer, default=0)
    recorded_at = Column(Integer, default=lambda: int(__import__('datetime').datetime.utcnow().timestamp()))
    
    __table_args__ = (
        Index('idx_tenant_usage_tenant', 'tenant_id'),
        Index('idx_tenant_usage_period', 'period'),
        Index('idx_tenant_usage_metric', 'metric_type'),
    )


def get_tenant_by_slug(slug: str) -> Tenant:
    """Obtém tenant por slug"""
    from database import SessionLocal
    session = SessionLocal()
    try:
        return session.query(Tenant).filter(Tenant.slug == slug).first()
    finally:
        session.close()


def create_tenant(name: str, slug: str, plan_tier: str = 'free') -> Tenant:
    """Cria novo tenant"""
    from database import SessionLocal
    import uuid
    
    session = SessionLocal()
    try:
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            plan_tier=plan_tier
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        return tenant
    finally:
        session.close()


def check_tenant_limits(tenant_id: str, metric: str = 'documents') -> bool:
    """
    Verifica se tenant atingiu limites
    metric: documents, users, api_calls
    """
    from database import SessionLocal
    
    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return False
        
        if metric == 'documents':
            return tenant.documents_count < tenant.documents_limit
        elif metric == 'users':
            return tenant.users_count < tenant.users_limit
        elif metric == 'api_calls':
            return tenant.api_calls_count < tenant.api_calls_limit
        
        return True
    finally:
        session.close()


def increment_tenant_usage(tenant_id: str, metric: str = 'documents', amount: int = 1):
    """Incrementa contador de uso do tenant"""
    from database import SessionLocal
    
    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return
        
        if metric == 'documents':
            tenant.documents_count += amount
        elif metric == 'users':
            tenant.users_count += amount
        elif metric == 'api_calls':
            tenant.api_calls_count += amount
        
        session.commit()
    finally:
        session.close()
