'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

const plans = [
  {
    id: 'starter',
    name: 'Explorar',
    description: 'Para conhecer o fluxo com segurança',
    price: 0,
    period: 'sempre',
    features: [
      { text: '10 consultas de IA por mês', included: true },
      { text: 'Motor jurídico de alta precisão', included: true, highlight: true },
      { text: 'Proteção contra respostas inventadas', included: true },
      { text: 'Links para fontes oficiais', included: true },
      { text: '3 documentos por mês', included: true },
      { text: 'Consulta rápida e resumos', included: true },
      { text: 'Pesquisa jurídica profunda', included: false },
      { text: 'Geração completa de peças', included: false },
      { text: 'Automações do escritório', included: false },
    ],
    cta: 'Começar Grátis',
    popular: false,
  },
  {
    id: 'professional',
    name: 'Profissional',
    description: 'Copiloto jurídico para o advogado',
    price: 149,
    period: 'mês',
    features: [
      { text: '150 consultas jurídicas por mês', included: true },
      { text: 'Motor jurídico de alta precisão em todas as consultas', included: true, highlight: true },
      { text: '30 pesquisas profundas por mês', included: true },
      { text: 'Citações e fontes oficiais', included: true, highlight: true },
      { text: '50 documentos com análise contextual', included: true },
      { text: 'Geração e revisão de peças', included: true },
      { text: 'Memória de casos e preferências', included: true },
      { text: 'Prazos, clientes e financeiro', included: true },
      { text: '1 usuário', included: true },
    ],
    cta: 'Escolher Profissional',
    popular: true,
  },
  {
    id: 'business',
    name: 'Escritório',
    description: 'Operação jurídica integrada para equipes',
    price: 699,
    period: 'mês',
    features: [
      { text: 'Tudo do Profissional', included: true },
      { text: '5 usuários incluídos', included: true, highlight: true },
      { text: '1.000 consultas e 300 pesquisas profundas', included: true },
      { text: 'Fila prioritária do motor jurídico', included: true },
      { text: '500 documentos por mês', included: true },
      { text: 'Base de conhecimento do escritório', included: true },
      { text: 'WhatsApp, cobrança e portal do cliente', included: true },
      { text: 'Fluxos de aprovação e auditoria', included: true },
      { text: 'Dashboard de produtividade e risco', included: true },
    ],
    cta: 'Escolher Escritório',
    popular: false,
  },
  {
    id: 'enterprise',
    name: 'Scale',
    description: 'Para operações jurídicas de alto volume',
    price: 1990,
    period: 'mês',
    features: [
      { text: 'A partir de 15 usuários', included: true, highlight: true },
      { text: 'Franquia customizada de IA e documentos', included: true },
      { text: 'API, webhooks e integrações dedicadas', included: true },
      { text: 'Políticas de retenção e segurança', included: true },
      { text: 'SSO, auditoria e ambientes segregados', included: true },
      { text: 'Modelos e workflows customizados', included: true },
      { text: 'SLA e gerente de sucesso', included: true },
      { text: 'Implantação sob medida', included: true },
    ],
    cta: 'Falar com vendas',
    popular: false,
  },
];

const faqs = [
  {
    q: 'Posso mudar de plano depois?',
    a: 'Sim! Você pode fazer upgrade ou downgrade a qualquer momento. O valor é rateado proporcionalmente.',
  },
  {
    q: 'A IA fica menos precisa nos planos menores?',
    a: 'Não. Toda consulta jurídica usa o motor de alta precisão, fontes e auditoria automática. Os planos mudam volume, profundidade, prioridade de fila, automações, documentos e recursos de equipe.',
  },
  {
    q: 'A resposta da IA substitui a revisão do advogado?',
    a: 'Não. A plataforma acelera pesquisa, análise e redação, mas destaca fontes, lacunas e pontos que exigem validação profissional.',
  },
  {
    q: 'O que consome uma pesquisa profunda?',
    a: 'Consultas que usam mais contexto, evidências oficiais, auditoria de artigos e análise estruturada extensa. A precisão jurídica não é reduzida nos planos menores.',
  },
  {
    q: 'Posso cancelar quando quiser?',
    a: 'Sim, sem multas nem compromissos. O acesso continua até o final do período pago.',
  },
];

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const router = useRouter();

  const handlePlanSelect = (planId: string) => {
    if (planId === 'enterprise') {
      // Redirecionar para formulário de contato
      router.push('/contact-sales');
    } else {
      // Salvar plano selecionado e redirecionar para registro
      localStorage.setItem('selected_plan', planId);
      router.push('/register');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 flex items-center justify-center font-bold text-sm">
                N
              </div>
              <span className="font-semibold">NeoBusiness AI</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/login" className="text-white/70 hover:text-white transition-colors text-sm">
                Login
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Começar
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-transparent"
          >
            Inteligência jurídica que vale o investimento
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-white/60 mb-8 max-w-2xl mx-auto"
          >
            A mesma base de segurança em todos os planos. Você paga por profundidade,
            volume, automação e capacidade de transformar pesquisa em trabalho concluído.
          </motion.p>

          {/* Billing Toggle */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-3 p-1 bg-white/5 rounded-full border border-white/10"
          >
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              Mensal
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                billingCycle === 'yearly'
                  ? 'bg-gradient-to-r from-cyan-500 to-purple-500 text-white'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              Anual
              <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                -20%
              </span>
            </button>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -5 }}
                className={`relative rounded-2xl p-6 ${
                  plan.popular
                    ? 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border-2 border-cyan-500/50'
                    : 'bg-white/5 border border-white/10'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-xs font-semibold">
                    MAIS POPULAR
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-1">{plan.name}</h3>
                  <p className="text-sm text-white/50">{plan.description}</p>
                </div>

                <div className="mb-6">
                  {plan.price !== null ? (
                    <>
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-bold">
                          R${billingCycle === 'yearly' && plan.price ? Math.round(plan.price * 0.8) : plan.price}
                        </span>
                        <span className="text-white/50">/{plan.period}</span>
                      </div>
                      {billingCycle === 'yearly' && plan.price && plan.price > 0 && (
                        <p className="text-xs text-green-400 mt-1">
                          Economize R${Math.round(plan.price * 0.2 * 12)}/ano
                        </p>
                      )}
                    </>
                  ) : (
                    <div className="text-2xl font-bold">Personalizado</div>
                  )}
                </div>

                <ul className="space-y-3 mb-6 text-sm">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      {feature.included ? (
                        <span className="text-green-400">✓</span>
                      ) : (
                        <span className="text-white/20">×</span>
                      )}
                      <span className={feature.included ? (feature.highlight ? 'text-white font-medium' : 'text-white/70') : 'text-white/30'}>
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handlePlanSelect(plan.id)}
                  className={`w-full py-3 rounded-xl font-medium transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-[0_0_20px_rgba(6,182,212,0.5)]'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  {plan.cta}
                </motion.button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 border-t border-white/10">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Perguntas Frequentes</h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <h3 className="font-semibold mb-2">{faq.q}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{faq.a}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ainda tem dúvidas?</h2>
          <p className="text-white/60 mb-8">
            Nossa equipe está pronta para ajudar você a escolher o melhor plano.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold hover:opacity-90 transition-opacity"
            >
              Começar Grátis
            </Link>
            <Link
              href="/contact"
              className="px-8 py-4 rounded-xl bg-white/10 text-white font-semibold hover:bg-white/20 transition-colors"
            >
              Falar com Especialista
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-white/40 text-sm">
            © 2026 NeoBusiness AI. Todos os direitos reservados.
          </p>
          <div className="flex gap-6 text-sm">
            <Link href="/terms" className="text-white/40 hover:text-white transition-colors">Termos</Link>
            <Link href="/privacy" className="text-white/40 hover:text-white transition-colors">Privacidade</Link>
            <Link href="/security" className="text-white/40 hover:text-white transition-colors">Segurança</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
