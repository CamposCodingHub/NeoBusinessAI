'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Persona = 'advogado' | 'contador';

type TaxCalendarItem = {
  code: string;
  title: string;
  due_hint: string;
  disclaimer: string;
};

const MODULE_LINKS = [
  { href: '/dashboard/deadlines', label: 'Prazos' },
  { href: '/dashboard/finance', label: 'Financeiro' },
  { href: '/dashboard/trust', label: 'Trust' },
  { href: '/sim-real', label: 'Sim Real' },
  { href: '/chat', label: 'Lex Chat' },
] as const;

const CHECKLISTS: Record<
  Persona,
  { id: string; title: string; blurb: string; items: string[] }[]
> = {
  advogado: [
    {
      id: 'prazos',
      title: 'Prazos processuais',
      blurb: 'Rotina diária para não perder intimação nem contagem.',
      items: [
        'Conferir intimações do dia (PJe / diário / e-mail do tribunal)',
        'Registrar prazo no módulo Prazos com data-fim e alerta D-3 / D-1',
        'Vincular prazo ao matter e responsável interno',
        'Revisar fila de urgentes antes do fim do expediente',
      ],
    },
    {
      id: 'honorarios',
      title: 'Honorários e inadimplência ética',
      blurb: 'Cobrança profissional — sem constrangimento (EOAB).',
      items: [
        'Contrato / proposta com escopo, forma e vencimento claros',
        'Emitir fatura e acompanhar aging (0–30 / 31–60 / 61–90 / 90+)',
        'Usar régua ética: D-3 lembrete → D0 → D+3 gentil → D+7 formal',
        'Documentar tratativas; evitar exposição pública do cliente',
      ],
    },
    {
      id: 'custas',
      title: 'Custas e adiantamentos',
      blurb: 'Separar despesa do escritório de reembolso do cliente.',
      items: [
        'Registrar adiantamento (guias, perícia, diligência) com valor e caso',
        'Pedir reembolso no contrato ou fatura específica',
        'Marcar status: advanced → reimbursed (ou written_off com justificativa)',
        'Reconciliar com trust / conta corrente do cliente quando aplicável',
      ],
    },
    {
      id: 'lgpd',
      title: 'LGPD e WhatsApp',
      blurb: 'Consentimento e finalidade antes de qualquer mensagem.',
      items: [
        'Confirmar consentimento WhatsApp e finalidade (prazo / cobrança / status)',
        'Não misturar conteúdo sensível em grupo sem necessidade',
        'Usar fila de aprovação outbound para mensagens de risco',
        'Registrar opt-out e respeitar imediatamente',
      ],
    },
  ],
  contador: [
    {
      id: 'fiscais',
      title: 'Obrigações fiscais (metodologia)',
      blurb: 'Checklist de processo — sem alíquotas inventadas. Confirme na legislação vigente e no regime do cliente.',
      items: [
        'Mapear regime (Simples / Lucro Presumido / Lucro Real / MEI) no cadastro do cliente',
        'Listar entregas do mês: apuração, DCTF/PGDAS (se couber), e-Social / REINF quando aplicável',
        'Cruzar notas fiscais emitidas vs. recebidas antes de fechar o período',
        'Guardar evidências e prazos oficiais; Lex não substitui consulta à norma atualizada',
      ],
    },
    {
      id: 'reforma-esocial',
      title: 'Reforma Tributária / eSocial × DCTFWeb',
      blurb:
        'Dor operacional frequente: cruzamento e transição IBS/CBS. Método apenas — sem alíquotas nem datas de vencimento inventadas como fato.',
      items: [
        'Cruzamento eSocial × EFD-Reinf × DCTFWeb: conferir consistência S-1200/S-1210 (método) — remuneração, pagamentos e débitos alinhados antes de transmitir',
        'Reforma: manter apuração paralela quando couber; validar campos IBS-CBS em NF conforme leiaute vigente (confirmar calendário oficial vigente)',
        'Disclaimer: LexScan auxilia a rotina; o contador CRC valida e responde pela entrega; legislação e calendários mudam',
      ],
    },
    {
      id: 'honorarios-cont',
      title: 'Honorários e inadimplência',
      blurb: 'Mesma disciplina financeira, tom profissional.',
      items: [
        'Proposta de serviços contábeis com recorrência e vencimento',
        'Acompanhar aging e régua ética no Financeiro',
        'Separar honorários de valores de terceiros / guias',
        'Formalizar renegociação por escrito',
      ],
    },
    {
      id: 'custas-cont',
      title: 'Custas e adiantamentos',
      blurb: 'Guias e taxas pagas pelo escritório em nome do cliente.',
      items: [
        'Lançar adiantamento com descrição da guia / competência',
        'Solicitar reembolso ou compensar na próxima fatura',
        'Atualizar status após comprovante do cliente',
        'Não misturar com receita de honorários no mesmo lançamento',
      ],
    },
    {
      id: 'lgpd-cont',
      title: 'LGPD e WhatsApp',
      blurb: 'Dados fiscais e pessoais exigem base legal e minimização.',
      items: [
        'Enviar documentos só por canal autorizado e com consentimento',
        'Evitar CPF/CNPJ e senhas em mensagem aberta',
        'Preferir link autenticado / portal quando disponível',
        'Registrar finalidade e retenção no processo interno',
      ],
    },
  ],
};

export default function AjudaPage() {
  const [persona, setPersona] = useState<Persona>('advogado');
  const [taxItems, setTaxItems] = useState<TaxCalendarItem[]>([]);
  const [taxMonth, setTaxMonth] = useState<string>('');
  const [taxDisclaimer, setTaxDisclaimer] = useState<string>('');
  const lists = CHECKLISTS[persona];

  useEffect(() => {
    if (persona !== 'contador') return;
    const tokensStr = typeof window !== 'undefined' ? localStorage.getItem('neobusiness_tokens') : null;
    let token = '';
    try {
      token = tokensStr ? JSON.parse(tokensStr)?.access_token || '' : '';
    } catch {
      token = '';
    }
    if (!token) return;
    const now = new Date();
    const month = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;
    fetch(`${API_URL}/finance/tax-calendar?month=${month}`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'omit',
    })
      .then(async (r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        setTaxMonth(data.month || month);
        setTaxItems(data.items || []);
        setTaxDisclaimer(data.disclaimer || '');
      })
      .catch(() => {});
  }, [persona]);

  return (
    <div className="ajuda-root min-h-screen text-[#E8EEF4]">
      <div className="ajuda-atmosphere" aria-hidden />
      <header className="relative mx-auto max-w-5xl px-6 pt-10 pb-6 sm:px-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link href="/dashboard" className="text-sm text-[#94A3B8] hover:text-[#5EEAD4] transition">
            ← Dashboard
          </Link>
          <nav className="flex flex-wrap gap-3 text-sm">
            {MODULE_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="text-[#94A3B8] hover:text-[#5EEAD4] transition underline-offset-4 hover:underline"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="mt-14 sm:mt-20">
          <p className="font-[family-name:var(--font-ajuda-brand)] text-5xl sm:text-7xl tracking-tight text-[#F1F5F9]">
            LexScan
          </p>
          <h1 className="mt-4 max-w-xl text-xl sm:text-2xl font-medium text-[#CBD5E1] leading-snug">
            Central de Ajuda para o dia a dia do escritório
          </h1>
          <p className="mt-3 max-w-lg text-[#94A3B8] text-sm sm:text-base leading-relaxed">
            Checklists práticos por persona — prazos, honorários éticos, custas, LGPD e rotina fiscal
            (metodologia, sem inventar alíquotas).
          </p>

          <div className="mt-8 flex gap-2" role="tablist" aria-label="Persona">
            {(
              [
                { id: 'advogado' as const, label: 'Advogado' },
                { id: 'contador' as const, label: 'Contador' },
              ]
            ).map((p) => (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={persona === p.id}
                onClick={() => setPersona(p.id)}
                className={`px-5 py-2.5 text-sm font-medium transition border-b-2 ${
                  persona === p.id
                    ? 'border-[#0F766E] text-[#5EEAD4]'
                    : 'border-transparent text-[#64748B] hover:text-[#94A3B8]'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="relative mx-auto max-w-5xl px-6 pb-20 sm:px-10">
        {persona === 'contador' && taxItems.length > 0 && (
          <section className="mb-12 border-t border-[#1E293B] pt-10">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0F766E]">
              Mês {taxMonth}
            </p>
            <h2 className="mt-2 text-lg font-semibold text-[#F1F5F9]">
              Lembretes de obrigações (metodologia)
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-[#94A3B8] leading-relaxed">
              {taxDisclaimer ||
                'Stub — confirmar calendário RFB/prefeitura vigente. Não é API oficial.'}
            </p>
            <ul className="mt-6 space-y-4">
              {taxItems.map((item) => (
                <li key={item.code} className="grid gap-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:gap-8">
                  <p className="text-sm font-medium text-[#E8EEF4]">{item.title}</p>
                  <div>
                    <p className="text-sm text-[#CBD5E1]">{item.due_hint}</p>
                    <p className="mt-1 text-xs text-[#64748B]">{item.disclaimer}</p>
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm flex flex-wrap gap-x-4 gap-y-2">
              <Link href="/dashboard/finance" className="text-[#5EEAD4] hover:underline underline-offset-4">
                Ver também no Financeiro →
              </Link>
              <a href="#reforma-esocial" className="text-[#5EEAD4] hover:underline underline-offset-4">
                Checklist Reforma / eSocial × DCTFWeb →
              </a>
            </p>
          </section>
        )}

        <ol className="space-y-12 border-t border-[#1E293B] pt-10">
          {lists.map((block, idx) => (
            <li
              key={block.id}
              id={block.id}
              className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:gap-10 scroll-mt-24"
            >
              <div>
                <span className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0F766E]">
                  {String(idx + 1).padStart(2, '0')}
                </span>
                <h2 className="mt-2 text-lg font-semibold text-[#F1F5F9]">{block.title}</h2>
                <p className="mt-2 text-sm text-[#94A3B8] leading-relaxed">{block.blurb}</p>
              </div>
              <ul className="space-y-3 text-sm text-[#CBD5E1]">
                {block.items.map((item) => (
                  <li key={item} className="flex gap-3 leading-relaxed">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#0F766E]" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>

        <aside className="mt-16 border-t border-[#1E293B] pt-8">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">Módulos</p>
          <p className="mt-2 text-sm text-[#94A3B8] max-w-xl">
            Abra o fluxo certo sem sair do ritmo do expediente.
          </p>
          <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {MODULE_LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="text-[#5EEAD4] hover:underline underline-offset-4">
                {l.label} →
              </Link>
            ))}
          </div>
        </aside>
      </main>

      <style dangerouslySetInnerHTML={{
        __html: `
          @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
          .ajuda-root {
            --font-ajuda-brand: 'Fraunces', Georgia, 'Times New Roman', serif;
            background: #0B1220;
            position: relative;
          }
          .ajuda-atmosphere {
            pointer-events: none;
            position: fixed;
            inset: 0;
            background:
              radial-gradient(ellipse 80% 50% at 10% -10%, rgba(15, 118, 110, 0.22), transparent 55%),
              radial-gradient(ellipse 60% 40% at 90% 20%, rgba(30, 58, 95, 0.35), transparent 50%),
              linear-gradient(180deg, #0B1220 0%, #0C1B2A 45%, #0F172A 100%);
            z-index: 0;
          }
          .ajuda-root > *:not(.ajuda-atmosphere) {
            position: relative;
            z-index: 1;
          }
        `,
      }} />
    </div>
  );
}
