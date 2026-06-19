'use client';

import Link from 'next/link';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-16">
      <div className="max-w-3xl mx-auto rounded-3xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          Configuracoes
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          Esta area foi criada para absorver acessos legados e servir como base para futuras
          preferencias de usuario, perfil, integracoes e politicas do workspace.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/dashboard" className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold">
            Ir para o dashboard
          </Link>
          <Link href="/security" className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition">
            Ver seguranca
          </Link>
        </div>
      </div>
    </div>
  );
}
