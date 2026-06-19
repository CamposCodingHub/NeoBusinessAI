'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const steps = [
  {
    id: 1,
    title: 'Bem-vindo ao Futuro',
    subtitle: 'Sua inteligência documental de última geração',
    description: 'Análise de documentos, geração de peças e insights estratégicos impulsionados por IA avançada.',
    action: 'Começar Jornada',
  },
  {
    id: 2,
    title: 'Qual sua área?',
    subtitle: 'Personalizaremos a experiência para você',
    options: [
      { id: 'civel', label: 'Cível', icon: '⚖️', color: 'from-cyan-500 to-blue-500' },
      { id: 'trabalhista', label: 'Trabalhista', icon: '👷', color: 'from-purple-500 to-pink-500' },
      { id: 'empresarial', label: 'Empresarial', icon: '🏢', color: 'from-pink-500 to-rose-500' },
      { id: 'tributario', label: 'Tributário', icon: '💰', color: 'from-amber-500 to-orange-500' },
      { id: 'outro', label: 'Outro', icon: '📋', color: 'from-emerald-500 to-cyan-500' },
    ],
  },
  {
    id: 3,
    title: 'Tudo Pronto!',
    subtitle: 'Vamos começar sua jornada',
    description: 'Você está pronto para experimentar o poder da IA no seu dia a dia jurídico.',
    action: 'Acessar Plataforma',
  },
];

// Animated Logo Component
function AnimatedLogo() {
  return (
    <div className="relative w-24 h-24 mx-auto mb-6">
      {/* Outer glow ring */}
      <motion.div
        className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500 to-purple-500"
        animate={{
          scale: [1, 1.1, 1],
          rotate: [0, 5, -5, 0],
          opacity: [0.5, 0.8, 0.5]
        }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
      {/* Middle ring */}
      <motion.div
        className="absolute inset-1 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-400"
        animate={{
          scale: [1, 1.05, 1],
          rotate: [0, -3, 3, 0],
        }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
      />
      {/* Inner core */}
      <div className="absolute inset-2 rounded-lg bg-[#0a0a0f] flex items-center justify-center">
        <span className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          N
        </span>
      </div>
      {/* Floating particles */}
      {[...Array(3)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 rounded-full bg-cyan-400"
          initial={{ x: '50%', y: '50%' }}
          animate={{
            x: ['50%', '20%', '80%', '50%'],
            y: ['50%', '20%', '60%', '50%'],
            opacity: [0.8, 0.3, 0.8],
          }}
          transition={{
            duration: 3 + i,
            repeat: Infinity,
            delay: i * 0.5,
          }}
        />
      ))}
    </div>
  );
}

// Success Animation Component
function SuccessAnimation() {
  return (
    <div className="relative w-24 h-24 mx-auto mb-6">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="w-full h-full rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 flex items-center justify-center"
      >
        <motion.svg
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="w-12 h-12 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          strokeWidth={3}
        >
          <motion.path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 13l4 4L19 7"
          />
        </motion.svg>
      </motion.div>
      {/* Confetti effect */}
      {[...Array(12)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 rounded-full"
          style={{
            background: ['#00f5ff', '#a855f7', '#ec4899', '#3b82f6'][i % 4],
          }}
          initial={{ x: '50%', y: '50%', scale: 0 }}
          animate={{
            x: `${50 + 40 * Math.cos((i * 30 * Math.PI) / 180)}%`,
            y: `${50 + 40 * Math.sin((i * 30 * Math.PI) / 180)}%`,
            scale: [0, 1, 0],
            opacity: [1, 1, 0],
          }}
          transition={{
            duration: 1,
            delay: 0.5 + i * 0.05,
            ease: "easeOut",
          }}
        />
      ))}
    </div>
  );
}

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const router = useRouter();
  const { user } = useAuth();

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleComplete = () => {
    // Marcar onboarding como completo
    localStorage.setItem('onboarding_completed', 'true');
    localStorage.setItem('onboarding_area', selectedOption || 'outro');

    // Atualizar usuário no backend (opcional - se tiver endpoint)
    // Por enquanto, apenas redireciona
    router.push('/dashboard');
  };

  const handleSkip = () => {
    localStorage.setItem('onboarding_completed', 'true');
    router.push('/dashboard');
  };

  const step = steps[currentStep];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,245,255,0.15),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(168,85,247,0.1),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(236,72,153,0.1),transparent_50%)]" />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                             linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      {/* Floating orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-72 h-72 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 blur-3xl"
        animate={{
          x: [0, 30, 0],
          y: [0, -30, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-72 h-72 rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-3xl"
        animate={{
          x: [0, -20, 0],
          y: [0, 20, 0],
          scale: [1, 1.15, 1],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-xl">
        {/* Progress Bar */}
        <div className="flex gap-2 mb-10">
          {steps.map((_, idx) => (
            <div key={idx} className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-purple-500"
                initial={{ width: '0%' }}
                animate={{
                  width: idx < currentStep ? '100%' : idx === currentStep ? '50%' : '0%'
                }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          ))}
        </div>

        {/* Card */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="glass-card p-10 relative"
          >
            {/* Glowing border effect */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/50 to-purple-500/50 rounded-2xl blur opacity-30" />

            <div className="relative">
              {/* Step Content */}
              {step.id === 1 && (
                <div className="text-center">
                  <AnimatedLogo />
                  <motion.h1
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-3xl font-bold mb-3 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent"
                  >
                    {step.title}
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="text-white/50 mb-2"
                  >
                    {step.subtitle}
                  </motion.p>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="text-white/70 mb-8 max-w-md mx-auto"
                  >
                    {step.description}
                  </motion.p>
                </div>
              )}

              {step.id === 2 && (
                <div className="text-center">
                  <motion.h1
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-2xl font-bold mb-3"
                  >
                    {step.title}
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-white/50 mb-8"
                  >
                    {step.subtitle}
                  </motion.p>

                  <div className="grid grid-cols-2 gap-3 mb-8">
                    {step.options?.map((option, idx) => (
                      <motion.button
                        key={option.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.2 + idx * 0.05 }}
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setSelectedOption(option.id)}
                        className={`relative group p-5 rounded-xl border-2 transition-all duration-300 ${
                          selectedOption === option.id
                            ? 'border-cyan-500 bg-gradient-to-br from-cyan-500/10 to-purple-500/10'
                            : 'border-white/10 bg-white/5 hover:border-white/30 hover:bg-white/10'
                        }`}
                      >
                        <div className={`absolute inset-0 bg-gradient-to-r ${option.color} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`} />
                        <div className="relative text-3xl mb-2">{option.icon}</div>
                        <div className="relative font-medium">{option.label}</div>
                      </motion.button>
                    ))}
                  </div>
                </div>
              )}

              {step.id === 3 && (
                <div className="text-center">
                  <SuccessAnimation />
                  <motion.h1
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="text-3xl font-bold mb-3"
                  >
                    {step.title}
                  </motion.h1>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="text-white/50 mb-2"
                  >
                    {step.subtitle}
                  </motion.p>
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="text-white/70 mb-8 max-w-md mx-auto"
                  >
                    {step.description}
                  </motion.p>
                </div>
              )}

              {/* Action Button */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                {step.id === 3 ? (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleComplete}
                    className="w-full py-4 px-8 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold text-lg shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:shadow-[0_0_40px_rgba(6,182,212,0.7)] transition-shadow"
                  >
                    <span className="flex items-center justify-center gap-2">
                      {step.action}
                      <motion.span
                        animate={{ x: [0, 5, 0] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        →
                      </motion.span>
                    </span>
                  </motion.button>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNext}
                    disabled={step.id === 2 && !selectedOption}
                    className={`w-full py-4 px-8 rounded-xl font-semibold text-lg transition-all ${
                      step.id === 2 && !selectedOption
                        ? 'bg-white/10 text-white/40 cursor-not-allowed'
                        : 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:shadow-[0_0_40px_rgba(6,182,212,0.7)]'
                    }`}
                  >
                    <span className="flex items-center justify-center gap-2">
                      {step.action || 'Continuar'}
                      <motion.span
                        animate={{ x: [0, 5, 0] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        →
                      </motion.span>
                    </span>
                  </motion.button>
                )}
              </motion.div>

              {/* Skip Link */}
              {currentStep > 0 && currentStep < steps.length - 1 && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.6 }}
                  onClick={handleSkip}
                  className="w-full text-center text-sm text-white/30 mt-6 hover:text-white/60 transition-colors"
                >
                  Pular onboarding
                </motion.button>
              )}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Step indicator */}
        <div className="flex justify-center gap-2 mt-6">
          {steps.map((_, idx) => (
            <motion.div
              key={idx}
              className={`w-2 h-2 rounded-full transition-colors ${
                idx === currentStep ? 'bg-cyan-400' : idx < currentStep ? 'bg-white/30' : 'bg-white/10'
              }`}
              animate={idx === currentStep ? { scale: [1, 1.2, 1] } : {}}
              transition={{ duration: 1, repeat: Infinity }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
