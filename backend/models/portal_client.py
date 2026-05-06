"""
Modelos para Portal do Cliente
Autenticação e dados do cliente
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class PortalClient(Base):
    """Cliente do portal (acesso para clientes do escritório)"""
    __tablename__ = 'portal_clients'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True, nullable=False)
    
    # Credenciais de acesso
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    
    # Token para acesso direto (magic link)
    access_token = Column(String(255))
    token_expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    client = relationship("Client", back_populates="portal_access")

class PortalActivity(Base):
    """Logs de atividade no portal do cliente"""
    __tablename__ = 'portal_activities'
    
    id = Column(Integer, primary_key=True, index=True)
    portal_client_id = Column(Integer, ForeignKey('portal_clients.id'), nullable=False)
    
    action = Column(String(100), nullable=False)  # login, view_document, download_invoice
    resource_type = Column(String(100))  # document, invoice, deadline
    resource_id = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# Adicionar relação reversa ao Client
from database import Client as ClientModel
ClientModel.portal_access = relationship("PortalClient", back_populates="client", uselist=False)
