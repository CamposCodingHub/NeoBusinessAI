"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";

const colors = {
  primary: "#1e3a5f",
  secondary: "#c9a227",
  accent: "#10b981",
  danger: "#ef4444",
  dark: "#0f172a",
  light: "#f8fafc",
  gray: "#64748b"
};

interface Plan {
  id: string;
  name: string;
  price_brl: number | null;
  price_formatted: string;
  documents_limit: number | string;
  users_limit: number | string;
  features: string[];
  popular: boolean;
  contact_sales: boolean;
}

export default function PricingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState<string>("free");
  const [stripeConfigured, setStripeConfigured] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    loadPlans();
    if (user?.email) {
      loadCurrentSubscription();
    }
  }, [user]);

  const loadPlans = async () => {
    try {
      const res = await fetch(`${API_URL}/api/plans`);
      const data = await res.json();
      if (data.success) {
        setPlans(data.plans);
        setStripeConfigured(data.stripe_configured);
      }
    } catch (error) {
      console.error("Erro ao carregar planos:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentSubscription = async () => {
    try {
      const res = await fetch(`${API_URL}/api/subscription/status?email=${user?.email}`);
      const data = await res.json();
      if (data.success) {
        setCurrentPlan(data.plan || "free");
      }
    } catch (error) {
      console.error("Erro ao carregar assinatura:", error);
    }
  };

  const handleSubscribe = async (planId: string) => {
    if (!user?.email) {
      router.push("/login");
      return;
    }

    if (!stripeConfigured) {
      alert("Sistema de pagamentos em configuracao. Entre em contato com vendas@lexscan.ai");
      return;
    }

    setCheckoutLoading(planId);

    try {
      const res = await fetch(`${API_URL}/api/checkout/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: planId,
          email: user.email,
          success_url: `${window.location.origin}/dashboard?payment=success`,
          cancel_url: `${window.location.origin}/pricing?payment=cancelled`
        })
      });

      const data = await res.json();

      if (data.success && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        alert(data.error || "Erro ao criar checkout");
      }
    } catch (error) {
      alert("Erro ao processar pagamento");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const formatLimit = (limit: number | string) => {
    if (typeof limit === "string") return limit;
    if (limit === Infinity || limit > 10000) return "Ilimitado";
    return limit.toString();
  };

  if (loading) {
    return (
      <div style={{ background: colors.dark, minHeight: "100vh", color: colors.light, display: "flex", alignItems: "center", justifyContent: "center" }}>
        Carregando planos...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: colors.dark }}>
      <Sidebar />

      <main style={{ flex: 1, marginLeft: "260px", padding: "40px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "50px" }}>
          <h1 style={{ color: colors.light, fontSize: "36px", marginBottom: "16px" }}>
            💰 Planos e Preços
          </h1>
          <p style={{ color: colors.gray, fontSize: "18px" }}>
            Escolha o plano ideal para seu escritório
          </p>

          {!stripeConfigured && (
            <div style={{
              background: `${colors.secondary}20`,
              border: `1px solid ${colors.secondary}`,
              borderRadius: "8px",
              padding: "16px",
              marginTop: "20px",
              color: colors.secondary
            }}>
              ⚠️ Sistema de pagamentos em modo de desenvolvimento.
              <br />Configure Stripe para habilitar pagamentos reais.
            </div>
          )}
        </div>

        {/* Plans Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px" }}>
          {plans.map((plan) => {
            const isCurrentPlan = currentPlan === plan.id;
            const isLoading = checkoutLoading === plan.id;

            return (
              <div
                key={plan.id}
                style={{
                  background: colors.primary,
                  borderRadius: "16px",
                  padding: "32px",
                  border: plan.popular ? `2px solid ${colors.secondary}` : `1px solid ${colors.primary}`,
                  position: "relative"
                }}
              >
                {/* Badge Popular */}
                {plan.popular && (
                  <div style={{
                    position: "absolute",
                    top: "-12px",
                    right: "24px",
                    background: colors.secondary,
                    color: colors.dark,
                    padding: "6px 16px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "bold"
                  }}>
                    ⭐ POPULAR
                  </div>
                )}

                {/* Badge Plano Atual */}
                {isCurrentPlan && (
                  <div style={{
                    position: "absolute",
                    top: "-12px",
                    left: "24px",
                    background: colors.accent,
                    color: colors.light,
                    padding: "6px 16px",
                    borderRadius: "20px",
                    fontSize: "12px",
                    fontWeight: "bold"
                  }}>
                    PLANO ATUAL
                  </div>
                )}

                {/* Plan Name */}
                <h3 style={{ color: colors.light, fontSize: "24px", marginBottom: "8px" }}>
                  {plan.name}
                </h3>

                {/* Price */}
                <div style={{ marginBottom: "24px" }}>
                  <span style={{ color: colors.light, fontSize: "36px", fontWeight: "bold" }}>
                    {plan.price_formatted}
                  </span>
                </div>

                {/* Limits */}
                <div style={{
                  background: `${colors.dark}50`,
                  borderRadius: "8px",
                  padding: "16px",
                  marginBottom: "24px"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ color: colors.gray }}>Documentos:</span>
                    <span style={{ color: colors.light, fontWeight: "bold" }}>
                      {formatLimit(plan.documents_limit)}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: colors.gray }}>Usuários:</span>
                    <span style={{ color: colors.light, fontWeight: "bold" }}>
                      {formatLimit(plan.users_limit)}
                    </span>
                  </div>
                </div>

                {/* Features */}
                <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px 0" }}>
                  {plan.features.map((feature, idx) => (
                    <li
                      key={idx}
                      style={{
                        color: colors.light,
                        marginBottom: "8px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px"
                      }}
                    >
                      <span style={{ color: colors.accent }}>✓</span>
                      <span style={{ fontSize: "14px" }}>{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                {plan.contact_sales ? (
                  <button
                    onClick={() => window.location.href = "mailto:vendas@lexscan.ai"}
                    style={{
                      width: "100%",
                      padding: "14px 24px",
                      borderRadius: "8px",
                      border: `1px solid ${colors.secondary}`,
                      background: "transparent",
                      color: colors.secondary,
                      cursor: "pointer",
                      fontSize: "16px",
                      fontWeight: "bold"
                    }}
                  >
                    📧 Falar com Vendas
                  </button>
                ) : isCurrentPlan ? (
                  <button
                    disabled
                    style={{
                      width: "100%",
                      padding: "14px 24px",
                      borderRadius: "8px",
                      border: "none",
                      background: colors.accent,
                      color: colors.light,
                      cursor: "default",
                      fontSize: "16px",
                      fontWeight: "bold"
                    }}
                  >
                    ✓ Você está neste plano
                  </button>
                ) : (
                  <button
                    onClick={() => handleSubscribe(plan.id)}
                    disabled={isLoading}
                    style={{
                      width: "100%",
                      padding: "14px 24px",
                      borderRadius: "8px",
                      border: "none",
                      background: plan.popular ? colors.secondary : `${colors.secondary}80`,
                      color: colors.dark,
                      cursor: isLoading ? "wait" : "pointer",
                      fontSize: "16px",
                      fontWeight: "bold",
                      opacity: isLoading ? 0.7 : 1
                    }}
                  >
                    {isLoading ? "Processando..." : "🔥 Assinar Agora"}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Additional Info */}
        <div style={{
          marginTop: "50px",
          background: `${colors.primary}30`,
          borderRadius: "12px",
          padding: "24px"
        }}>
          <h3 style={{ color: colors.light, marginBottom: "16px" }}>📋 Informações Importantes</h3>
          <ul style={{ color: colors.gray, lineHeight: "1.8" }}>
            <li>Todos os planos incluem suporte técnico</li>
            <li>Cancele a qualquer momento sem multa</li>
            <li>14 dias de garantia de satisfação</li>
            <li>Atualize ou downgrader seu plano quando quiser</li>
            <li>Para planos Enterprise, entre em contato para negociação personalizada</li>
          </ul>
        </div>

        {/* Back to Dashboard */}
        <div style={{ marginTop: "30px", textAlign: "center" }}>
          <button
            onClick={() => router.push("/dashboard")}
            style={{
              background: "transparent",
              border: "none",
              color: colors.gray,
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            ← Voltar para Dashboard
          </button>
        </div>
      </main>
    </div>
  );
}
