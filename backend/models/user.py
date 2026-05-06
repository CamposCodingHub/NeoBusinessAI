"""
User Model
===========
Modelo de usuário com suporte multi-tenant e RBAC.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from core.database import Base


class UserRole(str, enum.Enum):
    """Roles do sistema"""
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class SubscriptionTier(str, enum.Enum):
    """Planos de assinatura"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class User(Base):
    """Modelo de usuário"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    phone = Column(String(50))
    
    # Roles & Permissions
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.STARTER, nullable=False)
    
    # Email Verification
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    email_verified_at = Column(DateTime(timezone=True))
    
    # Password Reset
    password_reset_token = Column(String(255))
    password_reset_expires_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text)
    
    # Custom metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    custom_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se usuário tem permissão específica"""
        role_permissions = {
            UserRole.USER: ["read_own", "create_own"],
            UserRole.PREMIUM: ["read_own", "create_own", "ai_basic"],
            UserRole.ENTERPRISE: ["read_own", "create_own", "ai_basic", "ai_advanced", "team_management"],
            UserRole.ADMIN: ["*"],  # All permissions
        }
        
        if self.role == UserRole.ADMIN:
            return True
        
        return permission in role_permissions.get(self.role, [])


class Device(Base):
    """Dispositivos do usuário para tracking de sessões"""
    __tablename__ = 'devices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Device Info
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    user_agent = Column(Text)
    ip_address = Column(String(50))
    device_type = Column(String(50))  # mobile, desktop, tablet
    browser = Column(String(50))
    os = Column(String(50))
    
    # Location
    country = Column(String(100))
    city = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)
    
    # Timestamps
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="devices")
    refresh_tokens = relationship("RefreshToken", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device {self.device_id}>"


class RefreshToken(Base):
    """Refresh tokens para rotação segura"""
    __tablename__ = 'refresh_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey('devices.id'), nullable=False)
    
    token = Column(String(500), unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True))
    
    # Timestamps
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    device = relationship("Device", back_populates="refresh_tokens")
    
    def is_valid(self) -> bool:
        """Verifica se token ainda é válido"""
        return not self.is_revoked and self.expires_at > func.now()
    
    def __repr__(self):
        return f"<RefreshToken {self.token[:20]}...>"
