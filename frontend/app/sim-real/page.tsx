'use client';

/**
 * Simulador de Tela Real — LexScan
 * Mostra o escritório operando em tempo real: upload → OCR → prazos →
 * clientes → financeiro → Lex → WhatsApp, com painel vivo e log de eventos.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';

type PhaseId =
  | 'idle'
  | 'lead'
  | 'intake'
  | 'ocr'
  | 'analysis'
  | 'matter'
  | 'firm'
  | 'deadlines'
  | 'monitor'
  | 'crm'
  | 'finance'
  | 'time'
  | 'lex'
  | 'approval'
  | 'whatsapp'
  | 'done';

type EventTone = 'info' | 'success' | 'warning' | 'critical' | 'ai';

interface LiveEvent {
  id: number;
  time: string;
  phase: PhaseId;
  tone: EventTone;
  title: string;
  detail: string;
}

interface SimDoc {
  name: string;
  type: string;
  chars: number;
  status: 'queued' | 'ocr' | 'ready';
  summary: string;
  parties: string[];
  value: string;
}

interface SimDeadline {
  title: string;
  due: string;
  urgency: 'high' | 'medium' | 'low';
  status: 'pending' | 'done';
}

interface SimClient {
  name: string;
  stage: string;
  city: string;
}

interface SimInvoice {
  client: string;
  total: number;
  status: 'pending' | 'overdue' | 'paid';
}

interface LexMessage {
  role: 'user' | 'assistant';
  text: string;
}

const PHASES: Array<{ id: PhaseId; label: string; blurb: string }> = [
  { id: 'lead', label: 'Intake', blurb: 'Lead + COI' },
  { id: 'intake', label: 'Upload', blurb: 'Validação' },
  { id: 'ocr', label: 'OCR', blurb: 'Extração' },
  { id: 'analysis', label: 'Análise', blurb: 'Partes/valores' },
  { id: 'matter', label: 'Caso', blurb: 'Matter aberto' },
  { id: 'firm', label: 'Firm', blurb: 'Org · Trust · E-Sign' },
  { id: 'deadlines', label: 'Prazos', blurb: 'Alertas' },
  { id: 'monitor', label: 'Monitor', blurb: 'Intimação' },
  { id: 'crm', label: 'CRM', blurb: 'Timeline' },
  { id: 'finance', label: 'Financeiro', blurb: 'Aging · NFS-e' },
  { id: 'time', label: 'Time', blurb: 'Honorários' },
  { id: 'lex', label: 'Lex', blurb: 'Copiloto' },
  { id: 'approval', label: 'Aprovação', blurb: 'Gate humano' },
  { id: 'whatsapp', label: 'WhatsApp', blurb: 'Consent + envio' },
  { id: 'done', label: 'Fim', blurb: 'Ciclo OK' },
];

function stamp() {
  return new Date().toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function money(v: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function toneClass(tone: EventTone) {
  switch (tone) {
    case 'success':
      return 'border-[var(--trust-success)]/40 bg-[var(--trust-success)]/10 text-[var(--trust-success)]';
    case 'warning':
      return 'border-[var(--trust-warning)]/40 bg-[var(--trust-warning)]/10 text-[var(--trust-warning)]';
    case 'critical':
      return 'border-[var(--trust-danger)]/40 bg-[var(--trust-danger)]/10 text-[var(--trust-danger)]';
    case 'ai':
      return 'border-[var(--trust-accent)]/40 bg-[var(--trust-accent)]/10 text-[var(--trust-accent-soft)]';
    default:
      return 'border-[var(--trust-border)] bg-[var(--trust-surface-2)] text-[var(--trust-muted)]';
  }
}

export default function RealScreenSimulatorPage() {
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState<PhaseId>('idle');
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [doc, setDoc] = useState<SimDoc | null>(null);
  const [deadlines, setDeadlines] = useState<SimDeadline[]>([]);
  const [clients, setClients] = useState<SimClient[]>([
    { name: 'Grupo Norte Engenharia', stage: 'ativo', city: 'Curitiba' },
  ]);
  const [invoices, setInvoices] = useState<SimInvoice[]>([]);
  const [lex, setLex] = useState<LexMessage[]>([]);
  const [whatsappOut, setWhatsappOut] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [autoLoop, setAutoLoop] = useState(true);
  const stopRef = useRef(false);
  const eventId = useRef(1);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const pushEvent = useCallback((partial: Omit<LiveEvent, 'id' | 'time'>) => {
    const item: LiveEvent = {
      id: eventId.current++,
      time: stamp(),
      ...partial,
    };
    setEvents((prev) => [item, ...prev].slice(0, 80));
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  const phaseIndex = useMemo(() => {
    const idx = PHASES.findIndex((p) => p.id === phase);
    return idx < 0 ? -1 : idx;
  }, [phase]);

  const resetState = () => {
    setPhase('idle');
    setDoc(null);
    setDeadlines([]);
    setInvoices([]);
    setLex([]);
    setWhatsappOut(null);
    setProgress(0);
    setClients([{ name: 'Grupo Norte Engenharia', stage: 'ativo', city: 'Curitiba' }]);
  };

  const runCycle = useCallback(async () => {
    if (running) return;
    setRunning(true);
    stopRef.current = false;
    resetState();
    setEvents([]);
    eventId.current = 1;

    const steps: Array<() => Promise<void>> = [
      async () => {
        setPhase('lead');
        setProgress(4);
        pushEvent({
          phase: 'lead',
          tone: 'info',
          title: 'Lead capturado no Intake',
          detail: 'Grupo Norte Engenharia · screening COI automático: sem conflito',
        });
        await wait(700);
      },
      async () => {
        setPhase('intake');
        setProgress(10);
        pushEvent({
          phase: 'intake',
          tone: 'info',
          title: 'Upload recebido',
          detail: 'Intimacao_TJPR_Norte_2026.pdf · 2.4 MB · validação MIME OK',
        });
        setDoc({
          name: 'Intimacao_TJPR_Norte_2026.pdf',
          type: 'intimação',
          chars: 0,
          status: 'queued',
          summary: 'Aguardando OCR…',
          parties: [],
          value: '—',
        });
        await wait(900);
      },
      async () => {
        setPhase('ocr');
        setProgress(20);
        setDoc((d) => (d ? { ...d, status: 'ocr' } : d));
        pushEvent({
          phase: 'ocr',
          tone: 'info',
          title: 'OCR em execução',
          detail: 'Tesseract + limpeza de layout · página 1/3',
        });
        await wait(700);
        pushEvent({
          phase: 'ocr',
          tone: 'success',
          title: 'Texto extraído',
          detail: '18.420 caracteres · confiança média 94%',
        });
        setDoc((d) =>
          d
            ? {
                ...d,
                chars: 18420,
                status: 'ocr',
              }
            : d,
        );
        await wait(600);
      },
      async () => {
        setPhase('analysis');
        setProgress(35);
        pushEvent({
          phase: 'analysis',
          tone: 'ai',
          title: 'Lex analisando documento',
          detail: 'Classificação + partes + valores + riscos',
        });
        await wait(1100);
        setDoc({
          name: 'Intimacao_TJPR_Norte_2026.pdf',
          type: 'intimação / prazo para contestação',
          chars: 18420,
          status: 'ready',
          summary:
            'Intimação do TJPR em ação de cobrança. Prazo de 15 dias úteis para contestação. Parte autora: Banco Horizonte S.A.; réu: Grupo Norte Engenharia Ltda. Valor da causa R$ 287.450,00.',
          parties: ['Banco Horizonte S.A. (autor)', 'Grupo Norte Engenharia Ltda. (réu)'],
          value: 'R$ 287.450,00',
        });
        pushEvent({
          phase: 'analysis',
          tone: 'success',
          title: 'Análise concluída',
          detail: 'Tipo: intimação · Valor R$ 287.450,00 · Risco alto de preclusão',
        });
        await wait(500);
      },
      async () => {
        setPhase('matter');
        setProgress(40);
        pushEvent({
          phase: 'matter',
          tone: 'success',
          title: 'Caso / Matter aberto',
          detail: 'Norte × Horizonte · contencioso · vinculado ao cliente e ao documento',
        });
        await wait(700);
      },
      async () => {
        setPhase('firm');
        setProgress(42);
        pushEvent({
          phase: 'firm',
          tone: 'info',
          title: 'Org multi-tenant ativa',
          detail: 'Escritório Norte Associados · RBAC member · /dashboard/orgs',
        });
        await wait(450);
        pushEvent({
          phase: 'firm',
          tone: 'success',
          title: 'Trust account reconciliada',
          detail: 'Custódia cliente · saldo OK · /dashboard/trust',
        });
        await wait(400);
        pushEvent({
          phase: 'firm',
          tone: 'info',
          title: 'E-Sign envelope preparado',
          detail: 'Procuração + contrato honorários · /dashboard/esign',
        });
        await wait(550);
      },
      async () => {
        setPhase('deadlines');
        setProgress(50);
        const list: SimDeadline[] = [
          {
            title: 'Contestação — TJPR (Grupo Norte)',
            due: '2026-09-30',
            urgency: 'high',
            status: 'pending',
          },
          {
            title: 'Revisar documentos de defesa',
            due: '2026-09-24',
            urgency: 'medium',
            status: 'pending',
          },
          {
            title: 'Alinhar estratégia com cliente',
            due: '2026-09-18',
            urgency: 'medium',
            status: 'pending',
          },
        ];
        setDeadlines(list);
        pushEvent({
          phase: 'deadlines',
          tone: 'critical',
          title: '3 prazos criados',
          detail: 'Alerta crítico: contestação em 15 dias úteis',
        });
        await wait(800);
      },
      async () => {
        setPhase('monitor');
        setProgress(54);
        pushEvent({
          phase: 'monitor',
          tone: 'warning',
          title: 'Monitor: intimação detectada',
          detail: 'TJPR · processo monitorado · /dashboard/monitor',
        });
        await wait(500);
        pushEvent({
          phase: 'monitor',
          tone: 'success',
          title: 'Alerta de intimação roteado',
          detail: 'Evento → prazos + engagement feed (/operations/activity)',
        });
        await wait(500);
      },
      async () => {
        setPhase('crm');
        setProgress(58);
        setClients([
          { name: 'Grupo Norte Engenharia', stage: 'caso ativo · contencioso', city: 'Curitiba' },
          { name: 'Banco Horizonte (contraparte)', stage: 'parte adversa', city: 'São Paulo' },
        ]);
        pushEvent({
          phase: 'crm',
          tone: 'info',
          title: 'Timeline do cliente atualizada',
          detail: 'Evento vinculado ao caso Norte × Horizonte',
        });
        await wait(400);
        pushEvent({
          phase: 'crm',
          tone: 'success',
          title: 'Documento compartilhado no portal',
          detail: 'POST /documents/{id}/share-portal · cliente vê no /portal',
        });
        await wait(500);
      },
      async () => {
        setPhase('finance');
        setProgress(68);
        setInvoices([
          {
            client: 'Grupo Norte Engenharia',
            total: 8500,
            status: 'pending',
          },
          {
            client: 'Grupo Norte Engenharia',
            total: 4200,
            status: 'overdue',
          },
        ]);
        pushEvent({
          phase: 'finance',
          tone: 'warning',
          title: 'Honorários e cobrança',
          detail: 'Nova fatura R$ 8.500 · inadimplência prévia R$ 4.200',
        });
        await wait(450);
        pushEvent({
          phase: 'finance',
          tone: 'info',
          title: 'Aging de recebíveis',
          detail: 'GET /finance/aging · bucket 31–60: R$ 4.200 · /dashboard/finance',
        });
        await wait(400);
        pushEvent({
          phase: 'finance',
          tone: 'success',
          title: 'NFS-e stub emitida',
          detail: 'POST /billing/nfse → issue-stub · NFS-e-STUB-4821',
        });
        await wait(550);
      },
      async () => {
        setPhase('time');
        setProgress(74);
        pushEvent({
          phase: 'time',
          tone: 'info',
          title: 'Time entry lançado',
          detail: '45 min · análise de intimação · R$ 450 estimados (billable)',
        });
        await wait(500);
        pushEvent({
          phase: 'time',
          tone: 'success',
          title: 'Fatura gerada a partir do time',
          detail: 'POST /time/entries/invoice · status pending · pronto para payment-link',
        });
        await wait(600);
      },
      async () => {
        setPhase('lex');
        setProgress(82);
        setLex([
          {
            role: 'user',
            text: 'Quais riscos deste prazo e o que preciso preparar para a contestação?',
          },
        ]);
        pushEvent({
          phase: 'lex',
          tone: 'ai',
          title: 'Lex consultada',
          detail: 'Modo balanced · grounding documental + operação do escritório',
        });
        await wait(1200);
        setLex((prev) => [
          ...prev,
          {
            role: 'assistant',
            text:
              'Há risco concreto de preclusão se a contestação não for protocolada no prazo de 15 dias úteis. Com base no documento intimação TJPR: (1) confirme a contagem em dias úteis do foro; (2) reúna contrato, extratos e prova de pagamentos do Grupo Norte; (3) mapeie preliminares (ilegitimidade/impugnação ao valor). No financeiro do escritório há fatura vencida de R$ 4.200 — alinhe honorários antes da peça. Isto não substitui revisão humana do advogado responsável.',
          },
        ]);
        pushEvent({
          phase: 'lex',
          tone: 'success',
          title: 'Lex respondeu com restrições claras',
          detail: 'Sem emojis · sem filler · com próximos passos operacionais',
        });
        await wait(900);
      },
      async () => {
        setPhase('approval');
        setProgress(88);
        pushEvent({
          phase: 'approval',
          tone: 'warning',
          title: 'Gate humano de aprovação',
          detail: 'Fila /dashboard/approvals · Lex não auto-envia ao cliente',
        });
        await wait(550);
      },
      async () => {
        setPhase('whatsapp');
        setProgress(94);
        pushEvent({
          phase: 'whatsapp',
          tone: 'info',
          title: 'Consentimento WhatsApp verificado',
          detail: 'Opt-in cliente ativo · template de intimação permitido',
        });
        await wait(400);
        const msg =
          'Olá, Grupo Norte. Identificamos intimação com prazo de contestação. Nossa equipe já abriu o caso e entrará em contato hoje para alinhar documentos. — Escritório via LexScan';
        setWhatsappOut(msg);
        pushEvent({
          phase: 'whatsapp',
          tone: 'success',
          title: 'Mensagem enfileirada para aprovação',
          detail:
            'Produção: queue_whatsapp_for_approval → pending → humano aprova em /dashboard/approvals (sem auto-send)',
        });
        await wait(700);
      },
      async () => {
        setPhase('done');
        setProgress(100);
        pushEvent({
          phase: 'done',
          tone: 'success',
          title: 'Ciclo operacional fechado',
          detail: 'Documento → firm ops → monitor → CRM → aging/NFS-e → Lex → consent → cliente',
        });
      },
    ];

    for (const step of steps) {
      if (stopRef.current) break;
      await step();
    }

    setRunning(false);
  }, [pushEvent, running]);

  useEffect(() => {
    if (!autoLoop) return;
    if (running) return;
    if (phase !== 'idle' && phase !== 'done') return;
    const t = setTimeout(() => {
      void runCycle();
    }, phase === 'done' ? 4000 : 600);
    return () => clearTimeout(t);
  }, [autoLoop, running, phase, runCycle]);

  return (
    <div className="trust-shell min-h-screen">
      <div className="mx-auto max-w-[1440px] px-4 py-6 md:px-8">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="trust-kicker">LexScan · Simulador de tela real</p>
            <h1 className="trust-title mt-1">Escritório operando ao vivo</h1>
            <p className="trust-subtitle mt-2 max-w-2xl">
              Ciclo completo: intake+COI, caso, Org/Trust/E-Sign, monitor de intimação,
              CRM, aging/NFS-e, Lex, consent WhatsApp e gate humano — documento→risco→ação.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/qa-lab" className="trust-btn-ghost">
              QA Lab
            </Link>
            <Link href="/dashboard" className="trust-btn-ghost">
              Dashboard
            </Link>
            <button
              type="button"
              className="trust-btn-ghost"
              onClick={() => setAutoLoop((v) => !v)}
            >
              Auto: {autoLoop ? 'ON' : 'OFF'}
            </button>
            <button
              type="button"
              className="trust-btn-primary"
              disabled={running}
              onClick={() => void runCycle()}
            >
              {running ? 'Executando…' : 'Rodar ciclo'}
            </button>
            <button
              type="button"
              className="trust-btn-ghost"
              onClick={() => {
                stopRef.current = true;
                setAutoLoop(false);
              }}
            >
              Parar
            </button>
          </div>
        </header>

        {/* Progress rail */}
        <div className="trust-card mb-6 p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="text-sm text-[var(--trust-muted)]">
              Fase: <strong className="text-[var(--trust-ink)]">{phase}</strong>
            </span>
            <span className="text-sm text-[var(--trust-muted)]">{progress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[var(--trust-surface-2)]">
            <div
              className="h-full rounded-full bg-[var(--trust-accent)] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-5 md:grid-cols-8">
            {PHASES.map((p, i) => {
              const active = p.id === phase;
              const done = phaseIndex > i || phase === 'done';
              return (
                <div
                  key={p.id}
                  className={`rounded-lg border px-2 py-2 text-center ${
                    active
                      ? 'border-[var(--trust-accent)] bg-[var(--trust-accent)]/10'
                      : done
                        ? 'border-[var(--trust-success)]/30 bg-[var(--trust-success)]/5'
                        : 'border-[var(--trust-border)] bg-[var(--trust-surface)]'
                  }`}
                >
                  <div className="text-[11px] font-semibold text-[var(--trust-ink)]">{p.label}</div>
                  <div className="mt-0.5 text-[10px] text-[var(--trust-muted)]">{p.blurb}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-12">
          {/* Document panel */}
          <section className="trust-card p-4 lg:col-span-4">
            <h2 className="trust-section-title">Documento</h2>
            {!doc ? (
              <p className="mt-3 text-sm text-[var(--trust-muted)]">Aguardando captura…</p>
            ) : (
              <div className="mt-3 space-y-3">
                <div className="rounded-lg border border-[var(--trust-border)] bg-[var(--trust-canvas)] p-3">
                  <div className="text-sm font-medium text-[var(--trust-ink)]">{doc.name}</div>
                  <div className="mt-1 text-xs text-[var(--trust-muted)]">
                    {doc.type} · {doc.chars || '—'} chars · {doc.status}
                  </div>
                </div>
                <p className="text-sm leading-relaxed text-[var(--trust-body)]">{doc.summary}</p>
                {doc.parties.length > 0 && (
                  <ul className="space-y-1 text-sm text-[var(--trust-body)]">
                    {doc.parties.map((p) => (
                      <li key={p}>· {p}</li>
                    ))}
                  </ul>
                )}
                <div className="text-sm">
                  <span className="text-[var(--trust-muted)]">Valor da causa: </span>
                  <strong className="text-[var(--trust-ink)]">{doc.value}</strong>
                </div>
              </div>
            )}
          </section>

          {/* Deadlines + CRM */}
          <section className="trust-card p-4 lg:col-span-4">
            <h2 className="trust-section-title">Prazos & CRM</h2>
            <div className="mt-3 space-y-2">
              {deadlines.length === 0 && (
                <p className="text-sm text-[var(--trust-muted)]">Nenhum prazo ainda.</p>
              )}
              {deadlines.map((d) => (
                <div
                  key={d.title}
                  className="flex items-start justify-between gap-2 rounded-lg border border-[var(--trust-border)] px-3 py-2"
                >
                  <div>
                    <div className="text-sm text-[var(--trust-ink)]">{d.title}</div>
                    <div className="text-xs text-[var(--trust-muted)]">vence {d.due}</div>
                  </div>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] uppercase ${
                      d.urgency === 'high'
                        ? 'bg-[var(--trust-danger)]/15 text-[var(--trust-danger)]'
                        : 'bg-[var(--trust-warning)]/15 text-[var(--trust-warning)]'
                    }`}
                  >
                    {d.urgency}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 border-t border-[var(--trust-border)] pt-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--trust-muted)]">
                Clientes
              </h3>
              <ul className="mt-2 space-y-2">
                {clients.map((c) => (
                  <li key={c.name} className="text-sm text-[var(--trust-body)]">
                    <span className="font-medium text-[var(--trust-ink)]">{c.name}</span>
                    <span className="text-[var(--trust-muted)]">
                      {' '}
                      · {c.stage} · {c.city}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Finance + WhatsApp */}
          <section className="trust-card p-4 lg:col-span-4">
            <h2 className="trust-section-title">Financeiro & WhatsApp</h2>
            <div className="mt-3 space-y-2">
              {invoices.length === 0 && (
                <p className="text-sm text-[var(--trust-muted)]">Sem faturas neste ciclo.</p>
              )}
              {invoices.map((inv, i) => (
                <div
                  key={`${inv.client}-${i}`}
                  className="flex items-center justify-between rounded-lg border border-[var(--trust-border)] px-3 py-2 text-sm"
                >
                  <span className="text-[var(--trust-body)]">{inv.client}</span>
                  <span className="font-medium text-[var(--trust-ink)]">{money(inv.total)}</span>
                  <span
                    className={`text-xs ${
                      inv.status === 'overdue'
                        ? 'text-[var(--trust-danger)]'
                        : inv.status === 'paid'
                          ? 'text-[var(--trust-success)]'
                          : 'text-[var(--trust-warning)]'
                    }`}
                  >
                    {inv.status}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-lg border border-[var(--trust-border)] bg-[var(--trust-canvas)] p-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-[var(--trust-muted)]">
                Saída WhatsApp (aguardando aprovação)
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[var(--trust-body)]">
                {whatsappOut || 'Aguardando enfileiramento para gate humano…'}
              </p>
            </div>
          </section>

          {/* Lex panel */}
          <section className="trust-card p-4 lg:col-span-7">
            <h2 className="trust-section-title">Lex — copiloto ao vivo</h2>
            <div className="mt-3 max-h-[320px] space-y-3 overflow-y-auto rounded-lg border border-[var(--trust-border)] bg-[var(--trust-canvas)] p-3">
              {lex.length === 0 && (
                <p className="text-sm text-[var(--trust-muted)]">Aguardando consulta…</p>
              )}
              {lex.map((m, i) => (
                <div
                  key={`${m.role}-${i}`}
                  className={`rounded-lg px-3 py-2 text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'ml-8 bg-[var(--trust-accent)]/10 text-[var(--trust-ink)]'
                      : 'mr-4 bg-[var(--trust-surface-2)] text-[var(--trust-body)]'
                  }`}
                >
                  {m.text}
                </div>
              ))}
            </div>
          </section>

          {/* Event stream */}
          <section className="trust-card p-4 lg:col-span-5">
            <h2 className="trust-section-title">Stream de eventos</h2>
            <div className="mt-3 max-h-[320px] space-y-2 overflow-y-auto">
              {events.map((e) => (
                <div key={e.id} className={`rounded-lg border px-3 py-2 ${toneClass(e.tone)}`}>
                  <div className="flex items-center justify-between gap-2 text-[11px] opacity-80">
                    <span>{e.time}</span>
                    <span className="uppercase">{e.phase}</span>
                  </div>
                  <div className="mt-1 text-sm font-medium">{e.title}</div>
                  <div className="text-xs opacity-90">{e.detail}</div>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
