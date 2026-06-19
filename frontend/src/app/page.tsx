"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const router = useRouter();
  const { user } = useAuth();
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Cores LexScan
  const colors = {
    primary: "#1e3a5f",
    secondary: "#c9a227",
    accent: "#10b981",
    danger: "#ef4444",
    dark: "#0f172a",
    light: "#f8fafc"
  };

  const features = [
    {
      icon: "📄",
      title: "OCR Inteligente",
      description: "Extraia texto automaticamente de PDFs, imagens e documentos escaneados com 99% de precisão.",
      color: colors.primary,
    },
    {
      icon: "⏰",
      title: "Detecção de Prazos",
      description: "Identifica automaticamente prazos processuais, audiências e datas críticas.",
      color: colors.danger,
    },
    {
      icon: "🤖",
      title: "IA Jurídica",
      description: "Resumos automáticos, análise de documentos e chat contextual treinado em direito.",
      color: colors.secondary,
    },
    {
      icon: "🔔",
      title: "Alertas Automáticos",
      description: "Notificações por email, WhatsApp e SMS para nunca perder um prazo.",
      color: colors.accent,
    },
  ];

  const steps = [
    {
      step: "01",
      title: "Upload",
      desc: "Arraste e solte documentos ou importe de emails",
      icon: "📤"
    },
    {
      step: "02",
      title: "Análise",
      desc: "Nossa IA processa e extrai informações relevantes",
      icon: "⚡"
    },
    {
      step: "03",
      title: "Prazos",
      desc: "Detecta automaticamente datas e prazos críticos",
      icon: "🎯"
    },
    {
      step: "04",
      title: "Ação",
      desc: "Receba alertas e tome decisões com segurança",
      icon: "✅"
    }
  ];

  const testimonials = [
    {
      name: "Dr. Carlos Silva",
      role: "Advogado Sênior",
      firm: "Silva & Associados",
      text: "Economizamos 15 horas semanais de trabalho manual. LexScan transformou nossa produtividade.",
      image: "👨‍💼"
    },
    {
      name: "Dra. Maria Oliveira",
      role: "Sócia Fundadora",
      firm: "Oliveira Advocacia",
      text: "Nunca mais perdemos um prazo. O sistema de alertas é simplesmente salvador.",
      image: "👩‍💼"
    },
    {
      name: "Dr. Ricardo Mendes",
      role: "Diretor Jurídico",
      firm: "Mendes Corporate",
      text: "ROI impressionante. Em 2 meses o software se pagou com economia de horas.",
      image: "👨‍⚖️"
    }
  ];

  const pricing = [
    {
      name: "STARTER",
      price: "297",
      description: "Para escritórios iniciantes",
      features: [
        "50 documentos/mês",
        "OCR básico",
        "Resumo automático",
        "1 usuário",
        "Suporte por email"
      ],
      popular: false,
      cta: "Começar Agora"
    },
    {
      name: "PROFESSIONAL",
      price: "897",
      description: "Para escritórios em crescimento",
      features: [
        "200 documentos/mês",
        "OCR avançado + IA",
        "Detecção de prazos",
        "Chat contextual",
        "5 usuários",
        "API básica",
        "Suporte prioritário"
      ],
      popular: true,
      cta: "Mais Popular"
    },
    {
      name: "BUSINESS",
      price: "2.500",
      description: "Para grandes escritórios",
      features: [
        "Documentos ilimitados",
        "IA treinável personalizada",
        "White-label",
        "Integrações ERP",
        "20 usuários",
        "API completa",
        "Consultoria incluída",
        "SLA garantido"
      ],
      popular: false,
      cta: "Falar com Vendas"
    }
  ];

  return (
    <main className="landing">
      {/* Background */}
      <div className="animated-bg">
        <div
          className="glow-orb orb-1"
          style={{
            transform: `translate(${mousePosition.x * 0.02}px, ${mousePosition.y * 0.02}px)`,
            background: `radial-gradient(circle, ${colors.primary}40 0%, transparent 70%)`
          }}
        />
        <div
          className="glow-orb orb-2"
          style={{
            transform: `translate(${-mousePosition.x * 0.01}px, ${-mousePosition.y * 0.01}px)`,
            background: `radial-gradient(circle, ${colors.secondary}30 0%, transparent 70%)`
          }}
        />
      </div>

      {/* Navigation */}
      <nav className="top-nav" style={{ background: 'rgba(30, 58, 95, 0.95)', borderBottom: `1px solid ${colors.secondary}40` }}>
        <div className="nav-brand">
          <span className="brand-icon" style={{ fontSize: '28px' }}>⚖️</span>
          <span className="brand-text" style={{ color: colors.light, fontWeight: 700 }}>LexScan IA</span>
        </div>
        <div className="nav-actions">
          {user ? (
            <button className="btn-primary" onClick={() => router.push("/dashboard")} style={{ background: colors.secondary, color: colors.dark }}>
              Ir para Dashboard
            </button>
          ) : (
            <>
              <button className="btn-ghost" onClick={() => router.push("/login")} style={{ color: colors.light }}>
                Entrar
              </button>
              <button className="btn-primary" onClick={() => router.push("/register")} style={{ background: colors.secondary, color: colors.dark }}>
                Teste Grátis
              </button>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-fullscreen" style={{ background: `linear-gradient(135deg, ${colors.dark} 0%, ${colors.primary} 100%)` }}>
        <div className="hero-content">
          <div className="badge" style={{ background: `${colors.secondary}20`, border: `1px solid ${colors.secondary}40`, color: colors.secondary }}>
            <span className="badge-dot" style={{ background: colors.accent }} />
            <span>IA para Escritórios Jurídicos</span>
          </div>

          <h1 className="hero-title" style={{ color: colors.light }}>
            Nunca Mais Perca
            <span className="gradient-text" style={{ background: `linear-gradient(135deg, ${colors.secondary} 0%, ${colors.accent} 100%)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}> um Prazo</span>
          </h1>

          <p className="hero-subtitle" style={{ color: '#94a3b8' }}>
            LexScan IA processa documentos jurídicos automaticamente, detecta prazos processuais
            e envia alertas para sua equipe. Economize 15+ horas semanais de trabalho manual.
          </p>

          <div className="hero-buttons">
            <button
              className="btn-primary btn-glow"
              onClick={() => router.push("/register")}
              style={{ background: colors.secondary, color: colors.dark, fontSize: '18px', padding: '16px 32px' }}
            >
              <span>🚀</span> Começar Teste Grátis
            </button>
            <button
              className="btn-secondary"
              onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
              style={{ border: `2px solid ${colors.secondary}`, color: colors.secondary }}
            >
              <span>▶️</span> Ver Demonstração
            </button>
          </div>

          <div className="trust-badge" style={{ color: '#94a3b8' }}>
            <span>✓</span> 14 dias grátis <span style={{ margin: '0 12px' }}>•</span>
            <span>✓</span> Sem cartão de crédito <span style={{ margin: '0 12px' }}>•</span>
            <span>✓</span> Cancelamento fácil
          </div>
        </div>

        <div className="scroll-indicator">
          <div className="scroll-mouse" style={{ border: `2px solid ${colors.secondary}` }}>
            <div className="scroll-wheel" style={{ background: colors.secondary }} />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" style={{ background: colors.dark, padding: '100px 24px' }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag" style={{ color: colors.secondary }}>RECURSOS</span>
            <h2 style={{ color: colors.light }}>Tudo Que Seu Escritório Precisa</h2>
            <p style={{ color: '#94a3b8' }}>Automatize tarefas repetitivas e foque no que realmente importa: seus clientes.</p>
          </div>

          <div className="features-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            {features.map((feature, idx) => (
              <div key={idx} className="feature-card" style={{ background: `${colors.primary}30`, border: `1px solid ${colors.primary}50`, borderRadius: '16px', padding: '32px' }}>
                <div className="feature-icon" style={{ fontSize: '48px', marginBottom: '16px' }}>{feature.icon}</div>
                <h3 style={{ color: colors.light, marginBottom: '12px' }}>{feature.title}</h3>
                <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works" style={{ background: `${colors.primary}10`, padding: '100px 24px' }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag" style={{ color: colors.secondary }}>COMO FUNCIONA</span>
            <h2 style={{ color: colors.light }}>Em 4 Passos Simples</h2>
          </div>

          <div className="steps-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '32px', maxWidth: '1000px', margin: '0 auto' }}>
            {steps.map((step, idx) => (
              <div key={idx} className="step-card" style={{ textAlign: 'center', padding: '24px' }}>
                <div className="step-number" style={{ fontSize: '14px', color: colors.secondary, fontWeight: 700, marginBottom: '16px' }}>PASSO {step.step}</div>
                <div className="step-icon" style={{ fontSize: '48px', marginBottom: '16px' }}>{step.icon}</div>
                <h3 style={{ color: colors.light, marginBottom: '8px' }}>{step.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: '14px' }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section" style={{ background: colors.dark, padding: '100px 24px' }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag" style={{ color: colors.secondary }}>DEPOIMENTOS</span>
            <h2 style={{ color: colors.light }}>O Que Dizem Nossos Clientes</h2>
          </div>

          <div className="testimonials-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            {testimonials.map((item, idx) => (
              <div key={idx} className="testimonial-card" style={{ background: `${colors.primary}30`, border: `1px solid ${colors.primary}50`, borderRadius: '16px', padding: '32px' }}>
                <div className="stars" style={{ color: colors.secondary, marginBottom: '16px' }}>★★★★★</div>
                <p style={{ color: colors.light, fontSize: '16px', lineHeight: '1.7', marginBottom: '24px', fontStyle: 'italic' }}>"{item.text}"</p>
                <div className="testimonial-author" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div className="author-avatar" style={{ fontSize: '40px' }}>{item.image}</div>
                  <div>
                    <div className="author-name" style={{ color: colors.light, fontWeight: 600 }}>{item.name}</div>
                    <div className="author-role" style={{ color: '#94a3b8', fontSize: '14px' }}>{item.role} • {item.firm}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="pricing-section" id="pricing" style={{ background: `${colors.primary}10`, padding: '100px 24px' }}>
        <div className="container">
          <div className="section-header">
            <span className="section-tag" style={{ color: colors.secondary }}>PREÇOS</span>
            <h2 style={{ color: colors.light }}>Planos Para Todo Tamanho</h2>
            <p style={{ color: '#94a3b8' }}>Escolha o plano ideal para seu escritório. Todos incluem 14 dias grátis.</p>
          </div>

          <div className="pricing-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            {pricing.map((plan, idx) => (
              <div
                key={idx}
                className="pricing-card"
                style={{
                  background: plan.popular ? `${colors.primary}50` : `${colors.primary}20`,
                  border: plan.popular ? `2px solid ${colors.secondary}` : `1px solid ${colors.primary}40`,
                  borderRadius: '16px',
                  padding: '40px 32px',
                  position: 'relative'
                }}
              >
                {plan.popular && (
                  <div className="popular-badge" style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: colors.secondary, color: colors.dark, padding: '6px 16px', borderRadius: '20px', fontSize: '12px', fontWeight: 700 }}>
                    MAIS POPULAR
                  </div>
                )}
                <h3 style={{ color: colors.light, fontSize: '14px', letterSpacing: '2px', marginBottom: '8px' }}>{plan.name}</h3>
                <div className="price" style={{ color: colors.light, fontSize: '48px', fontWeight: 700, marginBottom: '8px' }}>
                  R${plan.price}<span style={{ fontSize: '16px', color: '#94a3b8' }}>/mês</span>
                </div>
                <p style={{ color: '#94a3b8', marginBottom: '24px' }}>{plan.description}</p>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px 0' }}>
                  {plan.features.map((feature, fidx) => (
                    <li key={fidx} style={{ color: colors.light, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: colors.accent }}>✓</span> {feature}
                    </li>
                  ))}
                </ul>
                <button
                  className="btn-pricing"
                  style={{
                    width: '100%',
                    padding: '14px',
                    borderRadius: '8px',
                    background: plan.popular ? colors.secondary : 'transparent',
                    color: plan.popular ? colors.dark : colors.light,
                    border: plan.popular ? 'none' : `2px solid ${colors.secondary}`,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                  onClick={() => router.push("/register")}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section" style={{ background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.dark} 100%)`, padding: '100px 24px', textAlign: 'center' }}>
        <div className="container" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h2 style={{ color: colors.light, fontSize: '36px', marginBottom: '16px' }}>
            Pronto Para Revolucionar Seu Escritório?
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '18px', marginBottom: '32px' }}>
            Junte-se a centenas de escritórios que economizam 15+ horas semanais com LexScan IA.
          </p>
          <button
            className="btn-cta"
            onClick={() => router.push("/register")}
            style={{
              background: colors.secondary,
              color: colors.dark,
              padding: '18px 40px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '18px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            🚀 Começar Teste Grátis de 14 Dias
          </button>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '16px' }}>
            Não precisa de cartão de crédito • Setup em 5 minutos • Suporte humano
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer" style={{ background: colors.dark, borderTop: `1px solid ${colors.primary}40`, padding: '60px 24px 24px' }}>
        <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="footer-content" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '40px', marginBottom: '40px' }}>
            <div>
              <div className="footer-brand" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <span style={{ fontSize: '28px' }}>⚖️</span>
                <span style={{ color: colors.light, fontWeight: 700, fontSize: '20px' }}>LexScan IA</span>
              </div>
              <p style={{ color: '#94a3b8', lineHeight: '1.6' }}>
                Inteligência Artificial para automatização de processos documentais jurídicos.
              </p>
            </div>
            <div>
              <h4 style={{ color: colors.light, marginBottom: '16px' }}>Produto</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {['Funcionalidades', 'Preços', 'Integrações', 'API'].map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>
                    <a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>{item}</a>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ color: colors.light, marginBottom: '16px' }}>Empresa</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {['Sobre', 'Blog', 'Carreiras', 'Contato'].map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>
                    <a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>{item}</a>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 style={{ color: colors.light, marginBottom: '16px' }}>Legal</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {['Privacidade', 'Termos', 'LGPD', 'Segurança'].map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>
                    <a href="#" style={{ color: '#94a3b8', textDecoration: 'none' }}>{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="footer-bottom" style={{ borderTop: `1px solid ${colors.primary}30`, paddingTop: '24px', textAlign: 'center', color: '#64748b' }}>
            <p>© 2026 LexScan IA. Todos os direitos reservados. ⚖️</p>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        .landing {
          min-height: 100vh;
          background: ${colors.dark};
          color: ${colors.light};
          overflow-x: hidden;
        }

        .animated-bg {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 0;
        }

        .glow-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.6;
        }

        .orb-1 {
          width: 600px;
          height: 600px;
          top: -200px;
          right: -100px;
        }

        .orb-2 {
          width: 500px;
          height: 500px;
          bottom: -100px;
          left: -100px;
        }

        .top-nav {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 24px;
          backdrop-filter: blur(12px);
        }

        .nav-brand {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .nav-actions {
          display: flex;
          gap: 12px;
        }

        .btn-ghost {
          padding: 10px 20px;
          border-radius: 8px;
          border: none;
          background: transparent;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          padding: 10px 20px;
          border-radius: 8px;
          border: none;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 600;
        }

        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(201, 162, 39, 0.3);
        }

        .hero-fullscreen {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          z-index: 1;
          padding: 120px 24px 80px;
        }

        .hero-content {
          max-width: 900px;
          text-align: center;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          border-radius: 50px;
          font-size: 14px;
          margin-bottom: 32px;
        }

        .badge-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .hero-title {
          font-size: 56px;
          font-weight: 700;
          line-height: 1.1;
          margin-bottom: 24px;
        }

        .gradient-text {
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
          font-size: 20px;
          max-width: 700px;
          margin: 0 auto 40px;
          line-height: 1.6;
        }

        .hero-buttons {
          display: flex;
          gap: 16px;
          justify-content: center;
          margin-bottom: 32px;
          flex-wrap: wrap;
        }

        .btn-secondary {
          padding: 16px 32px;
          border-radius: 8px;
          background: transparent;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .btn-secondary:hover {
          background: rgba(201, 162, 39, 0.1);
        }

        .trust-badge {
          font-size: 14px;
        }

        .scroll-indicator {
          position: absolute;
          bottom: 40px;
          left: 50%;
          transform: translateX(-50%);
        }

        .scroll-mouse {
          width: 26px;
          height: 40px;
          border-radius: 13px;
          position: relative;
        }

        .scroll-wheel {
          width: 4px;
          height: 8px;
          border-radius: 2px;
          position: absolute;
          top: 8px;
          left: 50%;
          transform: translateX(-50%);
          animation: scroll 1.5s infinite;
        }

        @keyframes scroll {
          0% { transform: translateX(-50%) translateY(0); opacity: 1; }
          100% { transform: translateX(-50%) translateY(12px); opacity: 0; }
        }

        .section-header {
          text-align: center;
          margin-bottom: 60px;
        }

        .section-tag {
          font-size: 14px;
          letter-spacing: 2px;
          font-weight: 600;
          display: block;
          margin-bottom: 16px;
        }

        .section-header h2 {
          font-size: 36px;
          margin-bottom: 16px;
        }

        .container {
          max-width: 1200px;
          margin: 0 auto;
          position: relative;
          z-index: 1;
        }

        .feature-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 40px rgba(30, 58, 95, 0.3);
        }

        .testimonial-card:hover {
          transform: translateY(-4px);
        }

        .pricing-card:hover {
          transform: translateY(-8px);
        }

        @media (max-width: 768px) {
          .hero-title {
            font-size: 36px;
          }

          .hero-subtitle {
            font-size: 16px;
          }

          .top-nav {
            padding: 12px 16px;
          }

          .nav-actions {
            gap: 8px;
          }

          .btn-ghost, .btn-primary {
            padding: 8px 12px;
            font-size: 14px;
          }
        }
      `}</style>
    </main>
  );
}
