'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const sections = [
  {
    title: 'Dados coletados',
    text: 'Podemos tratar dados de cadastro, uso da plataforma, documentos enviados e configuracoes operacionais para prestar o servico, melhorar a experiencia e manter trilhas de seguranca.',
  },
  {
    title: 'Finalidade',
    text: 'Os dados sao usados para autenticacao, processamento de documentos, automacoes, suporte, monitoramento tecnico e evolucao do produto.',
  },
  {
    title: 'Protecao',
    text: 'Aplicamos controles de acesso, logs, segregacao por usuario e mecanismos de seguranca compativeis com um produto juridico orientado a conformidade.',
  },
  {
    title: 'Direitos do titular',
    text: 'O usuario pode solicitar revisao, atualizacao ou exclusao de dados conforme a natureza das informacoes e as exigencias legais aplicaveis.',
  },
];

export default function PrivacyPage() {
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
          <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Politica de Privacidade
          </h1>
          <p className="mt-4 text-white/60 leading-relaxed">
            Este resumo descreve como a NeoBusiness AI trata informacoes para operar
            com seguranca, rastreabilidade e responsabilidade.
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
