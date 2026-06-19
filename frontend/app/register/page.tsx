'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

const useCases = [
  { id: 'lawyer', label: 'Advogado Autônomo', icon: '⚖️', description: 'Prática jurídica individual' },
  { id: 'firm_small', label: 'Escritório Pequeno', icon: '🏢', description: 'Até 5 advogados' },
  { id: 'firm_medium', label: 'Escritório Médio', icon: '🏛️', description: '6-20 advogados' },
  { id: 'firm_large', label: 'Escritório Grande', icon: '⚡', description: '20+ advogados' },
  { id: 'corporate', label: 'Jurídico Corporativo', icon: '💼', description: 'Departamento jurídico' },
  { id: 'consultant', label: 'Consultor Jurídico', icon: '📊', description: 'Consultoria especializada' },
];

const steps = [
  { id: 1, title: 'Crie sua conta', description: 'Informações básicas' },
  { id: 2, title: 'Seu perfil', description: 'Como você vai usar' },
  { id: 3, title: 'Escolha seu plano', description: 'Compare e decida' },
];

export default function RegisterPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Form data
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [company, setCompany] = useState('');
  const [useCase, setUseCase] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);

  const { register } = useAuth();
  const router = useRouter();

  const validateStep1 = () => {
    if (!email || !password || !confirmPassword) {
      setError('Preencha todos os campos');
      return false;
    }
    if (password !== confirmPassword) {
      setError('Senhas não coincidem');
      return false;
    }
    if (password.length < 8) {
      setError('Senha deve ter pelo menos 8 caracteres');
      return false;
    }
    if (!/[A-Z]/.test(password)) {
      setError('A senha deve conter pelo menos uma letra maiúscula');
      return false;
    }
    if (!/[a-z]/.test(password)) {
      setError('A senha deve conter pelo menos uma letra minúscula');
      return false;
    }
    if (!/\d/.test(password)) {
      setError('A senha deve conter pelo menos um número');
      return false;
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setError('A senha deve conter pelo menos um caractere especial');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!name || !useCase) {
      setError('Preencha todos os campos obrigatórios');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    setError('');
    if (currentStep === 1 && validateStep1()) {
      setCurrentStep(2);
    } else if (currentStep === 2 && validateStep2()) {
      setCurrentStep(3);
    }
  };

  const handleBack = () => {
    setError('');
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async (plan: string) => {
    if (!acceptTerms) {
      setError('Aceite os termos de uso para continuar');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await register(email, password, name, {
        company,
        use_case: useCase,
      });
      // Salvar plano selecionado (para upgrade futuro)
      localStorage.setItem('selected_plan', plan);
      router.push('/onboarding');
      // Redirect é feito no register para onboarding
    } catch (err: any) {
      setError(err.message || 'Erro ao criar conta');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,245,255,0.15),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(168,85,247,0.1),transparent_50%)]" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                             linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }}
        />
      </div>

      {/* Floating Orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-gradient-to-r from-cyan-500/10 to-blue-500/10 blur-3xl"
        animate={{ x: [0, 30, 0], y: [0, -30, 0], scale: [1, 1.1, 1] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gradient-to-r from-purple-500/10 to-pink-500/10 blur-3xl"
        animate={{ x: [0, -20, 0], y: [0, 20, 0], scale: [1, 1.15, 1] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-2xl">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((step) => (
              <div key={step.id} className="flex items-center">
                <motion.div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm ${
                    step.id <= currentStep
                      ? 'bg-gradient-to-r from-cyan-500 to-purple-500'
                      : 'bg-white/10'
                  }`}
                  animate={step.id === currentStep ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 1, repeat: Infinity }}
                >
                  {step.id < currentStep ? '✓' : step.id}
                </motion.div>
                <div className="ml-3 hidden sm:block">
                  <p className="font-medium text-sm">{step.title}</p>
                  <p className="text-xs text-white/50">{step.description}</p>
                </div>
                {step.id < steps.length && (
                  <div className="w-12 sm:w-24 h-0.5 mx-4 bg-white/10">
                    <motion.div
                      className="h-full bg-gradient-to-r from-cyan-500 to-purple-500"
                      initial={{ width: '0%' }}
                      animate={{ width: step.id < currentStep ? '100%' : '0%' }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Form Card */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="glass-card p-8 relative"
        >
          <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/50 to-purple-500/50 rounded-2xl blur opacity-30" />

          <div className="relative">
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
              >
                {error}
              </motion.div>
            )}

            {/* STEP 1: Account Info */}
            {currentStep === 1 && (
              <div className="space-y-5">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2">Crie sua conta</h2>
                  <p className="text-white/50">Comece sua jornada com a NeoBusiness AI</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Email *</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    placeholder="seu@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Senha *</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    placeholder="Mínimo 8 caracteres"
                  />
                  <p className="mt-1 text-xs text-white/30">
                    Use: maiúscula, minúscula, número e caractere especial
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Confirmar Senha *</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    placeholder="Repita a senha"
                  />
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleNext}
                  className="w-full py-4 px-8 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:shadow-[0_0_40px_rgba(6,182,212,0.7)] transition-all"
                >
                  Continuar →
                </motion.button>
              </div>
            )}

            {/* STEP 2: Profile */}
            {currentStep === 2 && (
              <div className="space-y-5">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2">Seu perfil</h2>
                  <p className="text-white/50">Personalize sua experiência</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Nome completo *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    placeholder="Seu nome"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Empresa/Escritório</label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all"
                    placeholder="Nome da empresa (opcional)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-4">Como você vai usar? *</label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {useCases.map((uc) => (
                      <motion.button
                        key={uc.id}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setUseCase(uc.id)}
                        className={`p-4 rounded-xl border-2 text-left transition-all ${
                          useCase === uc.id
                            ? 'border-cyan-500 bg-cyan-500/10'
                            : 'border-white/10 bg-white/5 hover:border-white/30'
                        }`}
                      >
                        <div className="text-2xl mb-2">{uc.icon}</div>
                        <div className="font-medium text-sm">{uc.label}</div>
                        <div className="text-xs text-white/50 mt-1">{uc.description}</div>
                      </motion.button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleBack}
                    className="flex-1 py-4 px-8 rounded-xl bg-white/10 text-white font-semibold hover:bg-white/20 transition-all"
                  >
                    ← Voltar
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleNext}
                    className="flex-1 py-4 px-8 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold shadow-[0_0_30px_rgba(6,182,212,0.5)] hover:shadow-[0_0_40px_rgba(6,182,212,0.7)] transition-all"
                  >
                    Ver planos →
                  </motion.button>
                </div>
              </div>
            )}

            {/* STEP 3: Plan Selection */}
            {currentStep === 3 && (
              <div className="space-y-5">
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-bold mb-2">Escolha seu plano</h2>
                  <p className="text-white/50">Comece grátis ou acelere com Premium</p>
                </div>

                {/* Free Plan */}
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="p-6 rounded-xl border border-white/10 bg-white/5 relative"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-bold">Starter</h3>
                      <p className="text-white/50 text-sm">Para experimentar</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">Grátis</div>
                    </div>
                  </div>
                  <ul className="mt-4 space-y-2 text-sm">
                    <li className="flex items-center gap-2">✅ Até 5 documentos</li>
                    <li className="flex items-center gap-2">✅ Chat básico</li>
                    <li className="flex items-center gap-2">✅ Análises simples</li>
                  </ul>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSubmit('free')}
                    disabled={isLoading}
                    className="w-full mt-4 py-3 rounded-xl bg-white/10 text-white font-medium hover:bg-white/20 transition-all"
                  >
                    {isLoading ? 'Criando...' : 'Começar Grátis'}
                  </motion.button>
                </motion.div>

                {/* Pro Plan - Highlighted */}
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="p-6 rounded-xl border-2 border-cyan-500 bg-gradient-to-br from-cyan-500/10 to-purple-500/10 relative"
                >
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-xs font-semibold">
                    MAIS POPULAR
                  </div>
                  <div className="flex justify-between items-start mt-2">
                    <div>
                      <h3 className="text-lg font-bold">Professional</h3>
                      <p className="text-white/50 text-sm">Para advogados sérios</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">R$97<span className="text-sm font-normal text-white/50">/mês</span></div>
                    </div>
                  </div>
                  <ul className="mt-4 space-y-2 text-sm">
                    <li className="flex items-center gap-2">✅ Documentos ilimitados</li>
                    <li className="flex items-center gap-2">✅ IA avançada</li>
                    <li className="flex items-center gap-2">✅ Geração de peças</li>
                    <li className="flex items-center gap-2">✅ Relatórios premium</li>
                    <li className="flex items-center gap-2">✅ Suporte prioritário</li>
                  </ul>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSubmit('professional')}
                    disabled={isLoading}
                    className="w-full mt-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-medium shadow-[0_0_20px_rgba(6,182,212,0.5)]"
                  >
                    {isLoading ? 'Criando...' : 'Escolher Professional'}
                  </motion.button>
                </motion.div>

                {/* Terms */}
                <div className="flex items-start gap-3 mt-4">
                  <input
                    type="checkbox"
                    checked={acceptTerms}
                    onChange={(e) => setAcceptTerms(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-white/30 bg-white/5 text-cyan-500 focus:ring-cyan-500"
                  />
                  <p className="text-xs text-white/50">
                    Aceito os{' '}
                    <Link href="/terms" className="text-cyan-400 hover:underline">Termos de Uso</Link>
                    {' '}e{' '}
                    <Link href="/privacy" className="text-cyan-400 hover:underline">Política de Privacidade</Link>
                  </p>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleBack}
                  className="w-full py-3 rounded-xl bg-white/10 text-white font-medium hover:bg-white/20 transition-all"
                >
                  ← Voltar
                </motion.button>
              </div>
            )}
          </div>
        </motion.div>

        {/* Login Link */}
        <p className="mt-6 text-center text-sm text-white/50">
          Já tem uma conta?{' '}
          <Link href="/login" className="text-cyan-400 hover:text-cyan-300 font-medium">
            Fazer login
          </Link>
        </p>
      </div>
    </div>
  );
}
