'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import ParticleBackground from '@/components/effects/ParticleBackground';

const features = [
  {
    icon: '⚡',
    title: 'IA Avançada',
    desc: 'Processamento neural de documentos em milissegundos',
    color: 'from-cyan-500 to-blue-500',
  },
  {
    icon: '🧠',
    title: 'Memória Neural',
    desc: 'Contexto persistente entre conversas e documentos',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: '�',
    title: 'Insights Estratégicos',
    desc: 'Análise preditiva e recomendações inteligentes',
    color: 'from-pink-500 to-rose-500',
  },
  {
    icon: '🔒',
    title: 'Segurança Enterprise',
    desc: 'Criptografia de nível bancário e compliance',
    color: 'from-emerald-500 to-cyan-500',
  },
];

const stats = [
  { value: '500ms', label: 'Tempo de Resposta' },
  { value: '99.9%', label: 'Precisão' },
  { value: '10M+', label: 'Documentos Processados' },
  { value: '24/7', label: 'Disponibilidade' },
];

function AnimatedBackground() {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      {/* Gradient Mesh */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(0,245,255,0.15),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(168,85,247,0.15),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(236,72,153,0.1),transparent_50%)]" />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Floating Orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 blur-3xl"
        animate={{
          x: [0, 30, 0],
          y: [0, -30, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-3xl"
        animate={{
          x: [0, -20, 0],
          y: [0, 20, 0],
          scale: [1, 1.15, 1],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    </div>
  );
}

function GlowingButton({
  children,
  href,
  variant = 'primary',
  className = ''
}: {
  children: React.ReactNode;
  href: string;
  variant?: 'primary' | 'secondary';
  className?: string;
}) {
  const baseStyles = 'relative group px-8 py-4 rounded-xl font-semibold transition-all duration-300 overflow-hidden';
  const variants = {
    primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]',
    secondary: 'bg-white/5 backdrop-blur-sm border border-white/20 text-white hover:bg-white/10 hover:border-white/40',
  };

  return (
    <Link href={href}>
      <motion.button
        className={`${baseStyles} ${variants[variant]} ${className}`}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {variant === 'primary' && (
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
        )}
        <span className="relative z-10 flex items-center gap-2">
          {children}
        </span>
      </motion.button>
    </Link>
  );
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
      className="group relative"
    >
      <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/50 to-purple-500/50 rounded-2xl opacity-0 group-hover:opacity-100 blur transition duration-500" />
      <div className="relative glass-card p-8 h-full">
        <div className={`w-14 h-14 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center text-2xl mb-6 shadow-lg group-hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] transition-shadow duration-300`}>
          {feature.icon}
        </div>
        <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
        <p className="text-white/60 leading-relaxed">{feature.desc}</p>
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleProtectedClick = (path: string) => {
    if (!isAuthenticated) {
      // Salvar destino para redirect após login
      sessionStorage.setItem('redirect_after_login', path);
      router.push('/register');
    } else {
      router.push(path);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-x-hidden">
      <AnimatedBackground />

      {/* Mouse Glow Effect */}
      <div
        className="pointer-events-none fixed z-50 w-[600px] h-[600px] rounded-full opacity-20 blur-3xl transition-transform duration-300 ease-out"
        style={{
          background: 'radial-gradient(circle, rgba(0,245,255,0.3) 0%, transparent 70%)',
          left: mousePosition.x - 300,
          top: mousePosition.y - 300,
        }}
      />

      {/* Navigation */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 w-full z-40 backdrop-blur-md bg-black/20 border-b border-white/5"
      >
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-10 h-10">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl animate-pulse-glow" />
              <div className="absolute inset-[2px] bg-[#0a0a0f] rounded-xl flex items-center justify-center">
                <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  N
                </span>
              </div>
            </div>
            <span className="font-semibold text-lg">NeoBusiness AI</span>
          </Link>

          <div className="flex items-center gap-6">
            <Link href="/simulador" className="text-white/70 hover:text-white transition-colors">
              Simulador
            </Link>
            <button
              onClick={() => handleProtectedClick('/chat')}
              className="text-white/70 hover:text-white transition-colors"
            >
              Chat
            </button>
            <button
              onClick={() => handleProtectedClick('/dashboard')}
              className="text-white/70 hover:text-white transition-colors"
            >
              Dashboard
            </button>
            {isAuthenticated ? (
              <GlowingButton href="/dashboard" variant="primary" className="px-6 py-2 text-sm">
                Dashboard
              </GlowingButton>
            ) : (
              <GlowingButton href="/login" variant="primary" className="px-6 py-2 text-sm">
                Entrar
              </GlowingButton>
            )}
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 pt-20">
        <div className="max-w-6xl mx-auto text-center relative z-10">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-sm text-white/70">Powered by Groq AI</span>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-6xl md:text-8xl font-bold mb-6 leading-tight"
          >
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent">
              Inteligência
            </span>
            <br />
            <span className="text-white">Documental</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl md:text-2xl text-white/60 max-w-3xl mx-auto mb-12 leading-relaxed"
          >
            Sua assistente jurídica com IA avançada.
            Análise de documentos, geração de peças e insights estratégicos em um só lugar.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <GlowingButton href="/register" variant="primary">
              Começar Grátis →
            </GlowingButton>
            <GlowingButton href="/simulador" variant="secondary">
              Abrir Simulador
            </GlowingButton>
            <GlowingButton href="/chat" variant="secondary">
              Ver Demo
            </GlowingButton>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto"
          >
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-sm text-white/50 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Tecnologia de <span className="text-cyan-400">Outro Nível</span>
            </h2>
            <p className="text-xl text-white/60 max-w-2xl mx-auto">
              Ferramentas avançadas impulsionadas por inteligência artificial de última geração
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <FeatureCard key={index} feature={feature} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-6">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-card p-12 md:p-16 relative overflow-hidden"
          >
            {/* Glow Effect */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-r from-cyan-500/30 to-purple-500/30 blur-3xl rounded-full" />

            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                Pronto para o <span className="text-cyan-400">Futuro</span>?
              </h2>
              <p className="text-xl text-white/60 mb-10 max-w-2xl mx-auto">
                Junte-se a milhares de profissionais que já transformaram seu trabalho com IA avançada.
              </p>
              <GlowingButton href="/onboarding" variant="primary" className="text-lg px-10 py-5">
                Começar Agora →
              </GlowingButton>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              N
            </div>
            <span className="font-semibold">NeoBusiness AI</span>
          </div>
          <p className="text-white/40 text-sm">
            © 2026 NeoBusiness AI. Todos os direitos reservados.
          </p>
          <div className="flex items-center gap-6">
            <Link href="/simulador" className="text-white/50 hover:text-white transition-colors text-sm">
              Simulador
            </Link>
            <Link href="/chat" className="text-white/50 hover:text-white transition-colors text-sm">
              Chat
            </Link>
            <Link href="/dashboard" className="text-white/50 hover:text-white transition-colors text-sm">
              Dashboard
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
