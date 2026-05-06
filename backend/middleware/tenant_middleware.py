"""
Multi-Tenant Middleware
=======================
Garante isolamento completo de dados entre usuários/tenants.
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
import logging
from functools import wraps

from database import get_db, User
from security.auth import get_current_user, TokenData

logger = logging.getLogger(__name__)


class TenantContext:
    """
    Contexto de tenant para isolamento de dados.
    Armazena informações do tenant atual durante a requisição.
    """
    def __init__(self):
        self.user_id: Optional[int] = None
        self.user_email: Optional[str] = None
        self.role: Optional[str] = None
        self.plan_tier: Optional[str] = None
        self.is_active: bool = False
        
    def set_user(self, user: User):
        """Define o usuário/tenant atual"""
        self.user_id = user.id
        self.user_email = user.email
        self.role = user.role
        self.plan_tier = user.plan_tier
        self.is_active = user.is_active
        
    def ensure_active(self):
        """Garante que o tenant está ativo"""
        if not self.is_active:
            raise HTTPException(
                status_code=403,
                detail="Conta desativada. Entre em contato com o suporte."
            )


class MultiTenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que estabelece o contexto de tenant para cada requisição.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Criar contexto de tenant
        request.state.tenant = TenantContext()
        
        # Se houver usuário autenticado, configurar tenant
        try:
            # Tentar obter token do header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from security.auth import verify_token
                token = auth_header.replace("Bearer ", "")
                payload = verify_token(token)
                
                # Buscar usuário no banco
                db = next(get_db())
                try:
                    user = db.query(User).filter(User.id == int(payload["sub"])).first()
                    if user:
                        request.state.tenant.set_user(user)
                        request.state.user = user
                        logger.debug(f"Tenant context set for user: {user.email}")
                finally:
                    db.close()
                    
        except Exception as e:
            # Usuário não autenticado ou token inválido
            pass
        
        # Continuar com a requisição
        response = await call_next(request)
        return response


def get_tenant(request: Request) -> TenantContext:
    """
    Obtém o contexto de tenant da requisição atual.
    
    Usage:
        tenant = get_tenant(request)
        print(tenant.user_id)
    """
    return request.state.tenant


def require_tenant(func):
    """
    Decorator que exige que um tenant esteja configurado.
    
    Usage:
        @app.get("/documents")
        @require_tenant
        async def list_documents(request: Request, tenant: TenantContext = Depends(get_tenant)):
            # tenant.user_id está garantido aqui
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extrair request dos kwargs ou args
        request = kwargs.get('request')
        if not request and args:
            request = args[0]
        
        if not hasattr(request.state, 'tenant') or not request.state.tenant.user_id:
            raise HTTPException(
                status_code=401,
                detail="Autenticação necessária"
            )
        
        # Garantir que tenant está ativo
        request.state.tenant.ensure_active()
        
        return await func(*args, **kwargs)
    
    return wrapper


class TenantAwareQuery:
    """
    Helper para criar queries SQLAlchemy filtradas por tenant.
    """
    
    def __init__(self, db: Session, tenant: TenantContext):
        self.db = db
        self.tenant = tenant
        
    def filter_by_tenant(self, model_class, additional_filters: Dict[str, Any] = None):
        """
        Cria query filtrada pelo tenant_id
        
        Usage:
            query = tenant_query.filter_by_tenant(Document)
            docs = query.all()  # Apenas documentos do tenant atual
        """
        query = self.db.query(model_class).filter(
            model_class.user_id == self.tenant.user_id
        )
        
        if additional_filters:
            for key, value in additional_filters.items():
                query = query.filter(getattr(model_class, key) == value)
                
        return query
    
    def get_by_id(self, model_class, record_id: int):
        """
        Busca registro por ID garantindo que pertence ao tenant
        
        Usage:
            doc = tenant_query.get_by_id(Document, 123)
            if not doc:
                raise HTTPException(404, "Documento não encontrado")
        """
        return self.db.query(model_class).filter(
            model_class.id == record_id,
            model_class.user_id == self.tenant.user_id
        ).first()
    
    def create(self, model_class, **kwargs):
        """
        Cria novo registro associado ao tenant
        
        Usage:
            doc = tenant_query.create(Document, filename="contrato.pdf")
        """
        kwargs['user_id'] = self.tenant.user_id
        instance = model_class(**kwargs)
        self.db.add(instance)
        return instance


def get_tenant_db(
    request: Request,
    db: Session = Depends(get_db)
) -> TenantAwareQuery:
    """
    Dependency que fornece TenantAwareQuery para rotas.
    
    Usage:
        @app.get("/documents")
        async def list_documents(tenant_db: TenantAwareQuery = Depends(get_tenant_db)):
            docs = tenant_db.filter_by_tenant(Document).all()
            return docs
    """
    tenant = get_tenant(request)
    if not tenant.user_id:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária"
        )
    return TenantAwareQuery(db, tenant)


def check_resource_ownership(
    resource_user_id: int,
    current_user: TokenData,
    action: str = "acessar"
) -> None:
    """
    Verifica se usuário tem permissão para acessar recurso.
    
    Args:
        resource_user_id: ID do dono do recurso
        current_user: Usuário autenticado
        action: Ação sendo tentada (para mensagem de erro)
    
    Raises:
        HTTPException: Se usuário não tem permissão
    """
    # Admin pode acessar tudo
    if current_user.role == "admin":
        return
    
    # Usuário comum só acessa seus próprios recursos
    if str(resource_user_id) != current_user.user_id:
        logger.warning(
            f"Tentativa de acesso não autorizado: "
            f"User {current_user.user_id} tentando {action} recurso de User {resource_user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Você não tem permissão para {action} este recurso"
        )


class TenantResourceFilter:
    """
    Filtro para rotas que listam recursos, garantindo apenas dados do tenant.
    """
    
    @staticmethod
    def filter_query(query, user_id_column: str, current_user: TokenData):
        """
        Aplica filtro de tenant em query SQLAlchemy
        
        Usage:
            query = db.query(Document)
            query = TenantResourceFilter.filter_query(query, 'user_id', current_user)
            return query.all()
        """
        # Admin vê tudo
        if current_user.role == "admin":
            return query
        
        # Usuário comum vê apenas seus dados
        return query.filter(getattr(query.column_descriptions[0]['type'], user_id_column) == int(current_user.user_id))


# Middleware para adicionar headers de debug (apenas em desenvolvimento)
class TenantDebugMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de debug sobre o tenant (apenas desenvolvimento).
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Apenas em desenvolvimento
        import os
        if os.getenv("ENVIRONMENT") == "development":
            tenant = getattr(request.state, 'tenant', None)
            if tenant and tenant.user_id:
                response.headers['X-Tenant-ID'] = str(tenant.user_id)
                response.headers['X-Tenant-Role'] = tenant.role or "anonymous"
        
        return response


# Funções utilitárias para logging de acesso
def log_tenant_access(
    tenant: TenantContext,
    resource: str,
    action: str,
    resource_id: Optional[int] = None
):
    """Log de acesso a recursos do tenant"""
    logger.info(
        f"Tenant access: User {tenant.user_email} ({tenant.user_id}) "
        f"{action} {resource}"
        f"{f' ID {resource_id}' if resource_id else ''}"
    )
