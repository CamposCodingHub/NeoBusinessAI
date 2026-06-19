'use client';

import Link from 'next/link';

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-16">
      <div className="max-w-4xl mx-auto rounded-3xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-300 to-cyan-400 bg-clip-text text-transparent">
          Centro de Seguranca
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          Esta area resume a postura de seguranca do produto e direciona para o painel
          completo de auditoria e observabilidade.
        </p>

        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Controles</div>
            <div className="mt-2 font-medium">Autenticacao, logs, isolamento por usuario</div>
          </div>
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Privacidade</div>
            <div className="mt-2 font-medium">Fluxos preparados para LGPD e auditoria</div>
          </div>
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Acompanhamento</div>
            <div className="mt-2 font-medium">Dashboard dedicado com status operacional</div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/security-dashboard" className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold">
            Abrir dashboard de seguranca
          </Link>
          <Link href="/" className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition">
            Voltar para a home
          </Link>
        </div>
      </div>
    </div>
  );
}
