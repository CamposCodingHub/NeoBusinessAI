'use client';

import Link from 'next/link';

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white px-6 py-16">
      <div className="max-w-3xl mx-auto rounded-3xl border border-slate-700/70 bg-slate-900/50 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-100 to-teal-300 bg-clip-text text-transparent">
          Fale com a NeoBusiness AI
        </h1>
        <p className="mt-4 text-slate-400 leading-relaxed">
          Para parceria, demonstracao, suporte comercial ou implantacao, fale com nosso time.
        </p>
        <p className="mt-3 text-sm text-slate-500">
          Prefere explorar sozinho?{' '}
          <Link href="/sim-real" className="text-teal-400/90 hover:text-teal-300 underline underline-offset-2">
            Abrir demo em /sim-real
          </Link>
        </p>

        <div className="mt-8 grid gap-4">
          <div className="rounded-2xl bg-slate-900/60 border border-slate-700/60 p-5">
            <div className="text-sm text-slate-500">Email comercial</div>
            <div className="mt-1 text-lg font-medium">contato@neobusinessai.com</div>
          </div>
          <div className="rounded-2xl bg-slate-900/60 border border-slate-700/60 p-5">
            <div className="text-sm text-slate-500">Canal recomendado</div>
            <div className="mt-1 text-lg font-medium">Solicitar demonstracao guiada</div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/contact-sales" className="px-5 py-3 rounded-xl bg-teal-700 hover:bg-teal-600 font-semibold transition-colors">
            Solicitar contato comercial
          </Link>
          <Link href="/sim-real" className="px-5 py-3 rounded-xl border border-slate-600 hover:border-teal-600/60 transition">
            Ver demo
          </Link>
          <Link href="/" className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 transition">
            Voltar para a home
          </Link>
        </div>
      </div>
    </div>
  );
}
