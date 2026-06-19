"""
Sistema de Pagamentos Stripe - LexScan IA
Gerencia assinaturas, planos e limites
"""

import stripe
import os
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class PlanTier(Enum):
    """Planos disponíveis"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

# Configurações dos planos
PLANS = {
    PlanTier.STARTER: {
        "name": "Explorar",
        "price_brl": 0,
        "documents_limit": 3,
        "users_limit": 1,
        "features": [
            "10 consultas de IA por mes",
            "Motor juridico de alta precisao",
            "Fontes oficiais",
            "3 documentos por mes"
        ],
        "stripe_price_id": None  # Será configurado no Stripe Dashboard
    },
    PlanTier.PROFESSIONAL: {
        "name": "Profissional",
        "price_brl": 14900,
        "documents_limit": 50,
        "users_limit": 1,
        "features": [
            "150 consultas juridicas por mes",
            "Motor juridico de alta precisao em todas as consultas",
            "30 pesquisas profundas por mes",
            "Citacoes e fontes oficiais",
            "Geracao e revisao de pecas",
            "Memoria contextual"
        ],
        "stripe_price_id": None,
        "popular": True
    },
    PlanTier.BUSINESS: {
        "name": "Escritorio",
        "price_brl": 69900,
        "documents_limit": 500,
        "users_limit": 5,
        "features": [
            "1.000 consultas e 300 pesquisas profundas",
            "Fila prioritaria do motor juridico",
            "Base de conhecimento do escritorio",
            "WhatsApp, cobranca e portal",
            "Fluxos de aprovacao e auditoria",
            "Dashboard de produtividade e risco"
        ],
        "stripe_price_id": None
    },
    PlanTier.ENTERPRISE: {
        "name": "Scale",
        "price_brl": None,  # Sob consulta
        "documents_limit": float('inf'),
        "users_limit": float('inf'),
        "features": [
            "A partir de 15 usuarios",
            "Franquia customizada de IA",
            "API e integracoes dedicadas",
            "SSO, auditoria e ambientes segregados",
            "SLA e implantacao sob medida"
        ],
        "stripe_price_id": None,
        "contact_sales": True
    }
}

class StripeManager:
    """Gerencia integração com Stripe"""
    
    def __init__(self):
        self.api_key = os.getenv('STRIPE_SECRET_KEY', '')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            stripe.api_key = self.api_key
            print(f"[STRIPE] Integracao ativada")
        else:
            print("[STRIPE] Integracao NAO configurada. Configure STRIPE_SECRET_KEY")
    
    def is_configured(self) -> bool:
        """Verifica se Stripe está configurado"""
        return self.enabled
    
    def get_public_key(self) -> str:
        """Retorna chave pública para frontend"""
        return os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    
    def get_plan_config(self, plan_tier: PlanTier) -> Dict:
        """Retorna configuração de um plano"""
        return PLANS.get(plan_tier, {})
    
    def get_all_plans(self) -> List[Dict]:
        """Retorna todos os planos disponíveis"""
        plans = []
        for tier, config in PLANS.items():
            plan_info = {
                "id": tier.value,
                "name": config["name"],
                "price_brl": config["price_brl"],
                "price_formatted": self._format_price(config["price_brl"]),
                "documents_limit": config["documents_limit"],
                "users_limit": config["users_limit"],
                "features": config["features"],
                "popular": config.get("popular", False),
                "contact_sales": config.get("contact_sales", False)
            }
            plans.append(plan_info)
        return plans
    
    def _format_price(self, price_cents: Optional[int]) -> str:
        """Formata preço em centavos para string"""
        if price_cents is None:
            return "Sob consulta"
        reais = price_cents // 100
        centavos = price_cents % 100
        return f"R$ {reais},{centavos:02d}/mes"
    
    def create_checkout_session(self, plan_tier: PlanTier, customer_email: str, success_url: str, cancel_url: str) -> Dict:
        """
        Cria sessão de checkout Stripe
        
        Args:
            plan_tier: Plano escolhido
            customer_email: Email do cliente
            success_url: URL de redirecionamento após sucesso
            cancel_url: URL de redirecionamento após cancelamento
            
        Returns:
            Dicionário com session_id e checkout_url
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Stripe nao configurado",
                "setup_instructions": [
                    "1. Crie conta em https://stripe.com",
                    "2. Obtenha suas chaves API",
                    "3. Configure no .env:",
                    "   STRIPE_SECRET_KEY=sk_test_...",
                    "   STRIPE_PUBLISHABLE_KEY=pk_test_...",
                    "   STRIPE_WEBHOOK_SECRET=whsec_..."
                ]
            }
        
        try:
            plan_config = self.get_plan_config(plan_tier)
            
            # Verificar se é plano enterprise (sob consulta)
            if plan_config.get("contact_sales"):
                return {
                    "success": False,
                    "error": "Plano Enterprise requer contato com vendas",
                    "contact_url": "mailto:vendas@lexscan.ai"
                }
            
            # Criar ou buscar cliente
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)
            
            # Criar sessão de checkout
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': f"LexScan IA - {plan_config['name']}",
                            'description': f"Plano {plan_config['name']} - {plan_config['documents_limit']} documentos/mes"
                        },
                        'unit_amount': plan_config['price_brl'],
                        'recurring': {
                            'interval': 'month'
                        }
                    },
                    'quantity': 1
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'plan_tier': plan_tier.value,
                    'customer_email': customer_email
                }
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "checkout_url": session.url,
                "customer_id": customer.id
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}"
            }
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict:
        """
        Processa webhook do Stripe
        
        Args:
            payload: Body da requisição
            signature: Header Stripe-Signature
            
        Returns:
            Resultado do processamento
        """
        if not self.enabled:
            return {"success": False, "error": "Stripe nao configurado"}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            # Processar evento
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                return self._process_successful_payment(session)
            
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                return self._process_failed_payment(invoice)
            
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                return self._process_cancellation(subscription)
            
            return {"success": True, "event_processed": event['type']}
            
        except stripe.error.SignatureVerificationError:
            return {"success": False, "error": "Assinatura do webhook invalida"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _process_successful_payment(self, session: Dict) -> Dict:
        """Processa pagamento bem-sucedido"""
        plan_tier = session.get('metadata', {}).get('plan_tier')
        customer_email = session.get('customer_email')
        subscription_id = session.get('subscription')
        
        # Aqui você atualizaria o banco de dados
        # Marcando o usuário como assinante ativo
        
        print(f"[STRIPE] Pagamento confirmado: {customer_email} -> {plan_tier}")
        
        return {
            "success": True,
            "event": "checkout.session.completed",
            "customer_email": customer_email,
            "plan_tier": plan_tier,
            "subscription_id": subscription_id
        }
    
    def _process_failed_payment(self, invoice: Dict) -> Dict:
        """Processa pagamento falho"""
        customer_id = invoice.get('customer')
        
        print(f"[STRIPE] Pagamento falho: {customer_id}")
        
        return {
            "success": True,
            "event": "invoice.payment_failed",
            "customer_id": customer_id,
            "action": "notificar_cliente"
        }
    
    def _process_cancellation(self, subscription: Dict) -> Dict:
        """Processa cancelamento de assinatura"""
        customer_id = subscription.get('customer')
        
        print(f"[STRIPE] Assinatura cancelada: {customer_id}")
        
        return {
            "success": True,
            "event": "customer.subscription.deleted",
            "customer_id": customer_id,
            "action": "reverter_para_plano_gratuito"
        }
    
    def check_subscription_status(self, customer_email: str) -> Dict:
        """
        Verifica status da assinatura de um cliente
        
        Args:
            customer_email: Email do cliente
            
        Returns:
            Status da assinatura e plano atual
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Stripe nao configurado",
                "subscription_active": False,
                "plan": "free"
            }
        
        try:
            # Buscar cliente
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if not customers.data:
                return {
                    "success": True,
                    "subscription_active": False,
                    "plan": "free",
                    "documents_limit": 5  # Limite gratuito
                }
            
            customer = customers.data[0]
            
            # Buscar assinaturas ativas
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active',
                limit=1
            )
            
            if subscriptions.data:
                sub = subscriptions.data[0]
                # Extrair plano dos metadados ou do item
                plan_tier = sub.get('metadata', {}).get('plan_tier', 'starter')
                plan_config = self.get_plan_config(PlanTier(plan_tier))
                
                return {
                    "success": True,
                    "subscription_active": True,
                    "plan": plan_tier,
                    "plan_name": plan_config["name"],
                    "documents_limit": plan_config["documents_limit"],
                    "users_limit": plan_config["users_limit"],
                    "current_period_end": sub.get('current_period_end'),
                    "cancel_at_period_end": sub.get('cancel_at_period_end')
                }
            else:
                return {
                    "success": True,
                    "subscription_active": False,
                    "plan": "free",
                    "documents_limit": 5  # Limite gratuito
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "subscription_active": False,
                "plan": "free"
            }
    
    def cancel_subscription(self, customer_email: str) -> Dict:
        """Cancela assinatura de um cliente"""
        if not self.enabled:
            return {"success": False, "error": "Stripe nao configurado"}
        
        try:
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if not customers.data:
                return {"success": False, "error": "Cliente nao encontrado"}
            
            customer = customers.data[0]
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active'
            )
            
            if subscriptions.data:
                for sub in subscriptions.data:
                    stripe.Subscription.delete(sub.id)
                
                return {
                    "success": True,
                    "message": "Assinatura cancelada com sucesso"
                }
            else:
                return {
                    "success": False,
                    "error": "Nenhuma assinatura ativa encontrada"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Instância global
stripe_manager = StripeManager()


def check_user_limits(user_email: str, current_documents: int) -> Dict:
    """
    Verifica se usuário está dentro dos limites do plano
    
    Args:
        user_email: Email do usuário
        current_documents: Quantidade atual de documentos
        
    Returns:
        Status dos limites e permissões
    """
    status = stripe_manager.check_subscription_status(user_email)
    
    if not status.get("subscription_active"):
        limit = 5  # Plano gratuito
    else:
        limit = status.get("documents_limit", 5)
    
    remaining = max(0, limit - current_documents)
    can_upload = current_documents < limit
    
    return {
        "can_upload": can_upload,
        "current_documents": current_documents,
        "documents_limit": limit,
        "documents_remaining": remaining,
        "plan": status.get("plan", "free"),
        "plan_name": status.get("plan_name", "Gratuito"),
        "subscription_active": status.get("subscription_active", False),
        "upgrade_required": not can_upload
    }


if __name__ == "__main__":
    # Teste
    print("=" * 60)
    print("TESTE SISTEMA STRIPE")
    print("=" * 60)
    
    # Mostrar planos
    print("\nPlanos disponiveis:")
    for plan in stripe_manager.get_all_plans():
        print(f"\n{plan['name']}:")
        print(f"  Preco: {plan['price_formatted']}")
        print(f"  Limite: {plan['documents_limit']} documentos")
        print(f"  Usuarios: {plan['users_limit']}")
        print(f"  Features: {', '.join(plan['features'][:3])}...")
        if plan.get('popular'):
            print("  ⭐ POPULAR")
    
    # Verificar configuracao
    if stripe_manager.is_configured():
        print("\n✅ Stripe configurado corretamente")
    else:
        print("\n❌ Stripe NAO configurado")
        print("Configure STRIPE_SECRET_KEY no arquivo .env")
        print("\nPara testes, use modo de desenvolvimento (sem Stripe)")
        print("O sistema permite uploads limitados (5 documentos) no plano gratuito")
