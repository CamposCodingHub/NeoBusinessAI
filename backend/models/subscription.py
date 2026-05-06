"""
Subscription Model
==================
Modelo de assinatura com integração Mercado Pago.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from core.database import Base


class SubscriptionStatus(str, enum.Enum):
    """Status da assinatura"""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class Subscription(Base):
    """Modelo de assinatura"""
    __tablename__ = 'subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Plan
    plan_tier = Column(String(50), nullable=False)  # starter, professional, business, enterprise
    plan_name = Column(String(100), nullable=False)
    
    # Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    
    # Mercado Pago Integration
    external_id = Column(String(255), index=True)  # Mercado Pago preference/preapproval ID
    external_customer_id = Column(String(255))
    
    # Billing Cycle
    billing_interval = Column(String(20))  # monthly, yearly
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    
    # Pricing
    amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="BRL")
    
    # Trial
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    
    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    
    # Custom metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    custom_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")
    
    def is_active(self) -> bool:
        """Verifica se assinatura está ativa"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    def requires_payment(self) -> bool:
        """Verifica se requer pagamento"""
        return self.status == SubscriptionStatus.PAST_DUE
    
    def __repr__(self):
        return f"<Subscription {self.plan_tier} ({self.status})>"


class Invoice(Base):
    """Faturas/pagamentos"""
    __tablename__ = 'invoices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Mercado Pago
    external_id = Column(String(255), unique=True, index=True)  # Mercado Pago payment ID
    payment_method = Column(String(50))  # pix, boleto, credit_card
    
    # Amount
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Status
    status = Column(String(50), nullable=False)  # pending, approved, rejected, cancelled
    
    # Dates
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    
    # Custom metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    custom_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<Invoice {self.external_id} ({self.status})>"
