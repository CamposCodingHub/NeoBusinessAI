'use client';

import Link from 'next/link';

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-16">
      <div className="max-w-3xl mx-auto rounded-3xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
          Fale com a NeoBusiness AI
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          Para parceria, demonstracao, suporte comercial ou implantacao, fale com nosso time.
        </p>

        <div className="mt-8 grid gap-4">
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Email comercial</div>
            <div className="mt-1 text-lg font-medium">contato@neobusinessai.com</div>
          </div>
          <div className="rounded-2xl bg-black/20 p-5">
            <div className="text-sm text-white/40">Canal recomendado</div>
            <div className="mt-1 text-lg font-medium">Solicitar demonstracao guiada</div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/contact-sales" className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold">
            Solicitar contato comercial
          </Link>
          <Link href="/" className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition">
            Voltar para a home
          </Link>
        </div>
      </div>
    </div>
  );
}
