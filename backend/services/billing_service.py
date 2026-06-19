"""
Billing Service
===============
Integração com Mercado Pago para assinaturas recorrentes.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import httpx
import json

from core.config import settings
from models.subscription import Subscription, Invoice, SubscriptionStatus
from models.user import User, SubscriptionTier
from core.security import verify_webhook_signature


class MercadoPagoService:
    """Serviço de integração com Mercado Pago"""
    
    def __init__(self):
        self.access_token = settings.MERCADO_PAGO_ACCESS_TOKEN
        self.base_url = "https://api.mercadopago.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_checkout_preference(
        self,
        plan_tier: str,
        billing_interval: str,
        user_email: str,
        success_url: str,
        failure_url: str,
        pending_url: str
    ) -> Dict[str, Any]:
        """
        Cria preferência de checkout no Mercado Pago.
        
        Args:
            plan_tier: Tier do plano (starter, professional, etc)
            billing_interval: Intervalo de cobrança (monthly, yearly)
            user_email: Email do usuário
            success_url: URL de sucesso
            failure_url: URL de falha
            pending_url: URL de pendência
            
        Returns:
            Dict com preference_id e init_point
        """
        # Obter preço do plano
        price = self._get_plan_price(plan_tier, billing_interval)
        plan_name = self._get_plan_name(plan_tier)
        
        # Criar preference
        preference_data = {
            "items": [
                {
                    "title": f"NeoBusiness AI - {plan_name} ({billing_interval})",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": price
                }
            ],
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            "auto_return": "approved",
            "metadata": {
                "plan_tier": plan_tier,
                "billing_interval": billing_interval,
                "user_email": user_email
            },
            "external_reference": f"{plan_tier}_{billing_interval}_{user_email}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/checkout/preferences",
                headers=self.headers,
                json=preference_data
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao criar preferência: {response.text}"
                )
            
            return response.json()
    
    async def create_preapproval_plan(
        self,
        plan_tier: str,
        billing_interval: str,
        price: float
    ) -> Dict[str, Any]:
        """
        Cria plano de recorrência (preapproval).
        
        Args:
            plan_tier: Tier do plano
            billing_interval: Intervalo de cobrança
            price: Preço do plano
            
        Returns:
            Dict com plan_id
        """
        plan_name = self._get_plan_name(plan_tier)
        
        plan_data = {
            "reason": f"NeoBusiness AI - {plan_name}",
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months" if billing_interval == "monthly" else "years",
                "transaction_amount": price,
                "currency_id": "BRL"
            },
            "back_url": "https://neobusiness.ai/billing/success",
            "payment_methods_allowed": {
                "payment_types": [
                    {"id": "credit_card"},
                    {"id": "pix"},
                    {"id": "boleto"}
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preapproval_plan",
                headers=self.headers,
                json=plan_data
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao criar plano: {response.text}"
                )
            
            return response.json()
    
    async def create_subscription(
        self,
        preapproval_plan_id: str,
        user_email: str,
        card_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria assinatura de recorrência.
        
        Args:
            preapproval_plan_id: ID do plano de recorrência
            user_email: Email do usuário
            card_token: Token do cartão (opcional)
            
        Returns:
            Dict com subscription details
        """
        subscription_data = {
            "preapproval_plan_id": preapproval_plan_id,
            "payer_email": user_email,
            "card_token_id": card_token,
            "auto_recurring": True,
            "back_url": "https://neobusiness.ai/billing/success",
            "reason": "NeoBusiness AI Subscription"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preapproval",
                headers=self.headers,
                json=subscription_data
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao criar assinatura: {response.text}"
                )
            
            return response.json()
    
    async def cancel_subscription(self, preapproval_id: str) -> bool:
        """
        Cancela assinatura de recorrência.
        
        Args:
            preapproval_id: ID da assinatura Mercado Pago
            
        Returns:
            True se cancelado com sucesso
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/preapproval/{preapproval_id}",
                headers=self.headers,
                json={"status": "cancelled"}
            )
            
            return response.status_code == 200
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um pagamento.
        
        Args:
            payment_id: ID do pagamento Mercado Pago
            
        Returns:
            Dict com detalhes do pagamento
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/payments/{payment_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pagamento não encontrado"
                )
            
            return response.json()
    
    def _get_plan_price(self, plan_tier: str, billing_interval: str) -> float:
        """Retorna preço do plano"""
        prices = {
            "starter": {"monthly": 0.0, "yearly": 0.0},
            "professional": {"monthly": 149.00, "yearly": 1430.00},
            "business": {"monthly": 699.00, "yearly": 6710.00},
            "enterprise": {"monthly": 1990.00, "yearly": 19100.00}
        }
        return prices.get(plan_tier, {}).get(billing_interval, 0)
    
    def _get_plan_name(self, plan_tier: str) -> str:
        """Retorna nome do plano"""
        names = {
            "starter": "Explorar",
            "professional": "Profissional",
            "business": "Escritorio",
            "enterprise": "Scale"
        }
        return names.get(plan_tier, "Starter")


class BillingService:
    """Serviço de billing interno"""
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: str,
        tenant_id: str,
        plan_tier: str,
        external_id: str,
        billing_interval: str = "monthly"
    ) -> Subscription:
        """
        Cria assinatura no banco.
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            tenant_id: ID do tenant
            plan_tier: Tier do plano
            external_id: ID externo (Mercado Pago)
            billing_interval: Intervalo de cobrança
            
        Returns:
            Subscription criada
        """
        price = MercadoPagoService()._get_plan_price(plan_tier, billing_interval)
        plan_name = MercadoPagoService()._get_plan_name(plan_tier)
        
        subscription = Subscription(
            tenant_id=tenant_id,
            user_id=user_id,
            plan_tier=plan_tier,
            plan_name=plan_name,
            status=SubscriptionStatus.PENDING,
            external_id=external_id,
            billing_interval=billing_interval,
            amount=price,
            currency="BRL"
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def update_subscription_status(
        db: Session,
        external_id: str,
        status: str,
        payment_data: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        Atualiza status da assinatura via webhook.
        
        Args:
            db: Sessão do banco
            external_id: ID externo do pagamento
            status: Novo status
            payment_data: Dados do pagamento
            
        Returns:
            Subscription atualizada
        """
        subscription = db.query(Subscription).filter(
            Subscription.external_id == external_id
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assinatura não encontrada"
            )
        
        # Mapear status Mercado Pago para interno
        status_mapping = {
            "approved": SubscriptionStatus.ACTIVE,
            "pending": SubscriptionStatus.PENDING,
            "rejected": SubscriptionStatus.PAST_DUE,
            "cancelled": SubscriptionStatus.CANCELLED
        }
        
        subscription.status = status_mapping.get(status, SubscriptionStatus.PENDING)
        
        # Atualizar períodos se pagamento aprovado
        if status == "approved":
            if subscription.billing_interval == "monthly":
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            else:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
            subscription.current_period_start = datetime.utcnow()
        
        # Criar invoice se houver dados de pagamento
        if payment_data:
            BillingService._create_invoice(db, subscription, payment_data)
        
        db.commit()
        db.refresh(subscription)
        
        return subscription
    
    @staticmethod
    def _create_invoice(
        db: Session,
        subscription: Subscription,
        payment_data: Dict[str, Any]
    ) -> Invoice:
        """Cria invoice/fatura"""
        invoice = Invoice(
            subscription_id=subscription.id,
            tenant_id=subscription.tenant_id,
            external_id=payment_data.get("id"),
            payment_method=payment_data.get("payment_type_id"),
            amount=float(payment_data.get("transaction_amount", 0)),
            currency=payment_data.get("currency_id", "BRL"),
            status=payment_data.get("status", "pending"),
            due_date=datetime.fromisoformat(payment_data.get("date_approved")) if payment_data.get("date_approved") else None,
            paid_at=datetime.utcnow() if payment_data.get("status") == "approved" else None
        )
        
        db.add(invoice)
        db.commit()
        
        return invoice
    
    @staticmethod
    def check_subscription_limits(
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Verifica limites do plano do usuário.
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            
        Returns:
            Dict com limites e uso atual
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Limites por plano
        limits = {
            SubscriptionTier.STARTER: {
                "documents": 10,
                "ai_requests": 100,
                "storage_gb": 1,
                "team_members": 1
            },
            SubscriptionTier.PROFESSIONAL: {
                "documents": 100,
                "ai_requests": 1000,
                "storage_gb": 10,
                "team_members": 5
            },
            SubscriptionTier.BUSINESS: {
                "documents": 1000,
                "ai_requests": 10000,
                "storage_gb": 100,
                "team_members": 25
            },
            SubscriptionTier.ENTERPRISE: {
                "documents": -1,  # Unlimited
                "ai_requests": -1,
                "storage_gb": -1,
                "team_members": -1
            }
        }
        
        plan_limits = limits.get(user.subscription_tier, limits[SubscriptionTier.STARTER])
        
        # TODO: Calcular uso atual
        current_usage = {
            "documents": 0,
            "ai_requests": 0,
            "storage_gb": 0,
            "team_members": 0
        }
        
        return {
            "plan": user.subscription_tier.value,
            "limits": plan_limits,
            "usage": current_usage,
            "can_upload": plan_limits["documents"] == -1 or current_usage["documents"] < plan_limits["documents"],
            "can_use_ai": plan_limits["ai_requests"] == -1 or current_usage["ai_requests"] < plan_limits["ai_requests"]
        }


# Singleton instances
mercado_pago_service = MercadoPagoService()
billing_service = BillingService()
