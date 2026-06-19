'use client';

import Link from 'next/link';

export default function ContactSalesPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-16">
      <div className="max-w-4xl mx-auto rounded-3xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          Vendas e Implantacao
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          Esta pagina centraliza o fluxo comercial para escritorios, departamentos juridicos
          e operacoes que precisam de onboarding assistido.
        </p>

        <div className="mt-8 grid md:grid-cols-3 gap-4">
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Perfil ideal</div>
            <div className="mt-2 font-medium">Times com alto volume documental</div>
          </div>
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Escopo</div>
            <div className="mt-2 font-medium">Treinamento, setup e desenho de fluxo</div>
          </div>
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Contato</div>
            <div className="mt-2 font-medium">sales@neobusinessai.com</div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/pricing" className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition">
            Voltar para planos
          </Link>
          <Link href="/register" className="px-5 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-600 font-semibold">
            Iniciar teste
          </Link>
        </div>
      </div>
    </div>
  );
}
