"""
Plan Model
===========
Modelo de planos de assinatura com limites.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum

from core.database import Base


class PlanTier(str, enum.Enum):
    """Tiers de planos"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Plan(Base):
    """Modelo de plano de assinatura"""
    __tablename__ = 'plans'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    tier = Column(SQLEnum(PlanTier), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    monthly_price = Column(Integer, nullable=False)  # Em centavos
    yearly_price = Column(Integer, nullable=False)
    currency = Column(String(3), default="BRL")
    
    # Limits
    limits = Column(JSONB, default={})
    """
    {
        "documents": 100,
        "ai_requests": 1000,
        "storage_gb": 10,
        "team_members": 5,
        "ocr_pages": 500,
        "embeddings": 1000
    }
    """
    
    # Features
    features = Column(JSONB, default=list)
    """
    [
        "ocr",
        "ai_analysis",
        "legal_templates",
        "api_access",
        "priority_support",
        "custom_branding"
    ]
    """
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    
    # Custom metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    custom_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Plan {self.name} ({self.tier.value})>"
    
    def to_dict(self):
        """Converte para dict serializável"""
        return {
            "tier": self.tier.value,
            "name": self.name,
            "description": self.description,
            "monthly_price": self.monthly_price / 100,  # Convert to decimal
            "yearly_price": self.yearly_price / 100,
            "currency": self.currency,
            "limits": self.limits,
            "features": self.features
        }


# Planos padrão
DEFAULT_PLANS = [
    {
        "tier": PlanTier.STARTER,
        "name": "Starter",
        "description": "Para advogados e escritórios pequenos",
        "monthly_price": 4990,  # R$ 49,90
        "yearly_price": 49900,  # R$ 499,00
        "limits": {
            "documents": 10,
            "ai_requests": 100,
            "storage_gb": 1,
            "team_members": 1,
            "ocr_pages": 50,
            "embeddings": 100
        },
        "features": [
            "ocr",
            "basic_ai_analysis",
            "5 legal_templates"
        ]
    },
    {
        "tier": PlanTier.PROFESSIONAL,
        "name": "Professional",
        "description": "Para escritórios em crescimento",
        "monthly_price": 14990,  # R$ 149,90
        "yearly_price": 149900,  # R$ 1.499,00
        "limits": {
            "documents": 100,
            "ai_requests": 1000,
            "storage_gb": 10,
            "team_members": 5,
            "ocr_pages": 500,
            "embeddings": 1000
        },
        "features": [
            "ocr",
            "advanced_ai_analysis",
            "all_legal_templates",
            "api_access",
            "priority_support"
        ]
    },
    {
        "tier": PlanTier.BUSINESS,
        "name": "Business",
        "description": "Para escritórios médios e grandes",
        "monthly_price": 49990,  # R$ 499,90
        "yearly_price": 499900,  # R$ 4.999,00
        "limits": {
            "documents": 1000,
            "ai_requests": 10000,
            "storage_gb": 100,
            "team_members": 25,
            "ocr_pages": 5000,
            "embeddings": 10000
        },
        "features": [
            "ocr",
            "advanced_ai_analysis",
            "all_legal_templates",
            "api_access",
            "priority_support",
            "custom_branding",
            "dedicated_support"
        ]
    },
    {
        "tier": PlanTier.ENTERPRISE,
        "name": "Enterprise",
        "description": "Solução personalizada para grandes operações",
        "monthly_price": 149990,  # R$ 1.499,90
        "yearly_price": 1499900,  # R$ 14.999,00
        "limits": {
            "documents": -1,  # Unlimited
            "ai_requests": -1,
            "storage_gb": -1,
            "team_members": -1,
            "ocr_pages": -1,
            "embeddings": -1
        },
        "features": [
            "ocr",
            "advanced_ai_analysis",
            "all_legal_templates",
            "api_access",
            "priority_support",
            "custom_branding",
            "dedicated_support",
            "sla_99.9",
            "custom_integrations",
            "on_premise_option"
        ]
    }
]
