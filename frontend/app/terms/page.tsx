'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const sections = [
  {
    title: 'Uso da plataforma',
    text: 'A NeoBusiness AI oferece recursos de apoio juridico e operacional. O conteudo gerado deve ser revisado por profissional responsavel antes de qualquer protocolo, decisao contratual ou envio a clientes.',
  },
  {
    title: 'Responsabilidade do usuario',
    text: 'Cada conta e responsavel pela veracidade das informacoes inseridas, pelo tratamento adequado de dados sensiveis e pelo cumprimento das normas da OAB, LGPD e regulacoes aplicaveis.',
  },
  {
    title: 'Disponibilidade e evolucao',
    text: 'Podemos atualizar, expandir ou ajustar recursos para melhorar seguranca, performance, experiencia e conformidade do produto.',
  },
  {
    title: 'Seguranca e acesso',
    text: 'O usuario deve manter credenciais protegidas e comunicar imediatamente qualquer uso indevido, incidente de seguranca ou suspeita de vazamento.',
  },
];

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-12">
      <div className="max-w-4xl mx-auto">
        <Link href="/register" className="text-sm text-cyan-400 hover:text-cyan-300 transition">
          Voltar ao cadastro
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8"
        >
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Termos de Uso
          </h1>
          <p className="mt-4 text-white/60 leading-relaxed">
            Estes termos resumem as regras basicas para uso responsavel da NeoBusiness AI
            no contexto juridico e operacional.
          </p>

          <div className="mt-8 space-y-4">
            {sections.map((section) => (
              <div key={section.title} className="rounded-2xl border border-white/10 bg-black/20 p-5">
                <h2 className="text-lg font-semibold">{section.title}</h2>
                <p className="mt-2 text-white/65 leading-relaxed">{section.text}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
