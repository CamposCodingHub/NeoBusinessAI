'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

type ModuleId =
  | 'overview'
  | 'documents'
  | 'deadlines'
  | 'clients'
  | 'finance'
  | 'legal'
  | 'whatsapp'
  | 'reports'
  | 'chat'
  | 'operations';

type Tone = 'info' | 'success' | 'warning';

interface SimDocument {
  id: number;
  name: string;
  status: 'uploaded' | 'processing' | 'completed';
  type: string;
  summary: string;
}

interface SimDeadline {
  id: number;
  title: string;
  dueDate: string;
  urgency: 'high' | 'medium' | 'low';
  status: 'pending' | 'completed';
  source: string;
}

interface SimClient {
  id: number;
  name: string;
  stage: 'lead' | 'active' | 'delayed';
  city: string;
}

interface SimInvoice {
  id: number;
  clientName: string;
  description: string;
  total: number;
  status: 'pending' | 'paid' | 'overdue';
  reminderSent: boolean;
}

interface SimPiece {
  id: number;
  title: string;
  basedOn: string;
  status: 'draft' | 'reviewed';
}

interface SimMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
}

interface SimLog {
  id: number;
  module: ModuleId;
  label: string;
  tone: Tone;
  time: string;
}

interface AdvancedOps {
  portalSessions: number;
  jurisprudenceQueries: number;
  queueAssignments: number;
  marketingCampaigns: number;
  semanticSearches: number;
}

const MODULES: Array<{ id: ModuleId; label: string; blurb: string }> = [
  { id: 'overview', label: 'Visao Geral', blurb: 'Mapa da plataforma e simulacao ponta a ponta.' },
  { id: 'documents', label: 'Documentos', blurb: 'Upload, OCR, resumo e extração de acao.' },
  { id: 'deadlines', label: 'Prazos', blurb: 'Alertas, priorizacao e conclusao.' },
  { id: 'clients', label: 'Clientes', blurb: 'CRM juridico e conversao de leads.' },
  { id: 'finance', label: 'Financeiro', blurb: 'Faturas, cobranca e caixa.' },
  { id: 'legal', label: 'Pecas', blurb: 'Rascunhos guiados por contexto.' },
  { id: 'whatsapp', label: 'WhatsApp', blurb: 'Notificacoes e contato com cliente.' },
  { id: 'reports', label: 'Relatorios', blurb: 'Visao executiva e indicadores.' },
  { id: 'chat', label: 'Chat IA', blurb: 'Assistente conversacional contextual.' },
  { id: 'operations', label: 'Operacoes', blurb: 'Portal, fila, marketing e busca.' },
];

const initialDocuments: SimDocument[] = [
  {
    id: 1,
    name: 'Contrato_societario_alpha.pdf',
    status: 'completed',
    type: 'contrato',
    summary: 'Clausulas de confidencialidade, foro e vigencia identificadas.',
  },
  {
    id: 2,
    name: 'Intimacao_cliente_rocha.pdf',
    status: 'uploaded',
    type: 'processual',
    summary: 'Arquivo aguardando analise automatica.',
  },
];

const initialDeadlines: SimDeadline[] = [
  {
    id: 1,
    title: 'Responder intimacao do Cliente Rocha',
    dueDate: '2026-06-20',
    urgency: 'high',
    status: 'pending',
    source: 'Intimacao_cliente_rocha.pdf',
  },
  {
    id: 2,
    title: 'Revisar clausula de foro do contrato Alpha',
    dueDate: '2026-06-24',
    urgency: 'medium',
    status: 'pending',
    source: 'Contrato_societario_alpha.pdf',
  },
  {
    id: 3,
    title: 'Enviar check-in ao cliente Beta',
    dueDate: '2026-06-18',
    urgency: 'low',
    status: 'completed',
    source: 'CRM',
  },
];

const initialClients: SimClient[] = [
  { id: 1, name: 'Grupo Alpha', stage: 'active', city: 'Sao Paulo' },
  { id: 2, name: 'Cliente Rocha', stage: 'active', city: 'Ribeirao Preto' },
  { id: 3, name: 'Prospecto Horizonte', stage: 'lead', city: 'Campinas' },
];

const initialInvoices: SimInvoice[] = [
  {
    id: 1,
    clientName: 'Grupo Alpha',
    description: 'Honorarios consultivos de junho',
    total: 4800,
    status: 'pending',
    reminderSent: false,
  },
  {
    id: 2,
    clientName: 'Cliente Rocha',
    description: 'Acompanhamento processual',
    total: 3200,
    status: 'overdue',
    reminderSent: true,
  },
];

const initialPieces: SimPiece[] = [
  {
    id: 1,
    title: 'Minuta de notificacao extrajudicial',
    basedOn: 'Contrato_societario_alpha.pdf',
    status: 'reviewed',
  },
];

const initialMessages: SimMessage[] = [
  {
    id: 1,
    role: 'assistant',
    content:
      'Sou a Lex operando em modo simulador. Posso resumir documentos, sugerir pecas, priorizar prazos e montar comunicacoes.',
  },
];

const initialLogs: SimLog[] = [
  {
    id: 1,
    module: 'overview',
    label: 'Simulador inicializado com os modulos principais do produto.',
    tone: 'info',
    time: '08:00:00',
  },
];

const initialAdvancedOps: AdvancedOps = {
  portalSessions: 1,
  jurisprudenceQueries: 2,
  queueAssignments: 3,
  marketingCampaigns: 1,
  semanticSearches: 4,
};

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowStamp() {
  return new Date().toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

function toneClasses(tone: Tone) {
  if (tone === 'success') {
    return 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300';
  }
  if (tone === 'warning') {
    return 'border-amber-500/40 bg-amber-500/10 text-amber-300';
  }
  return 'border-cyan-500/30 bg-cyan-500/10 text-cyan-200';
}

function urgencyClasses(urgency: 'high' | 'medium' | 'low') {
  if (urgency === 'high') {
    return 'bg-red-500/20 text-red-300 border border-red-500/40';
  }
  if (urgency === 'medium') {
    return 'bg-amber-500/20 text-amber-300 border border-amber-500/40';
  }
  return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
}

function statusClasses(status: string) {
  if (status === 'completed' || status === 'paid' || status === 'reviewed') {
    return 'bg-emerald-500/15 text-emerald-300';
  }
  if (status === 'processing' || status === 'pending' || status === 'draft') {
    return 'bg-amber-500/15 text-amber-300';
  }
  if (status === 'overdue') {
    return 'bg-red-500/15 text-red-300';
  }
  return 'bg-cyan-500/15 text-cyan-200';
}

function nextId<T extends { id: number }>(items: T[]) {
  return items.length === 0 ? 1 : Math.max(...items.map((item) => item.id)) + 1;
}

function PrimaryButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}

function SecondaryButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white/80 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <p className="text-sm text-white/50">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
      <p className="mt-2 text-xs text-white/35">{hint}</p>
    </div>
  );
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        <p className="mt-1 text-sm text-white/50">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

export default function SimuladorPage() {
  const [activeModule, setActiveModule] = useState<ModuleId>('overview');
  const [isRunning, setIsRunning] = useState(false);
  const [reportRevision, setReportRevision] = useState(1);
  const [documents, setDocuments] = useState<SimDocument[]>(initialDocuments);
  const [deadlines, setDeadlines] = useState<SimDeadline[]>(initialDeadlines);
  const [clients, setClients] = useState<SimClient[]>(initialClients);
  const [invoices, setInvoices] = useState<SimInvoice[]>(initialInvoices);
  const [pieces, setPieces] = useState<SimPiece[]>(initialPieces);
  const [messages, setMessages] = useState<SimMessage[]>(initialMessages);
  const [logs, setLogs] = useState<SimLog[]>(initialLogs);
  const [chatInput, setChatInput] = useState('');
  const [whatsAppConnected, setWhatsAppConnected] = useState(false);
  const [whatsAppAutoMode, setWhatsAppAutoMode] = useState(true);
  const [advancedOps, setAdvancedOps] = useState<AdvancedOps>(initialAdvancedOps);
  const [presentationMode, setPresentationMode] = useState(false);
  const [presentationStep, setPresentationStep] = useState(
    'Ambiente pronto para uma demonstracao visual guiada.',
  );
  const [presentationProgress, setPresentationProgress] = useState(0);

  useEffect(() => {
    const url = new URL(window.location.href);
    if (url.searchParams.get('presentation') === '1') {
      setPresentationMode(true);
      setPresentationStep('Modo apresentacao ativado via link.');
    }
  }, []);

  const pushLog = (module: ModuleId, label: string, tone: Tone = 'info') => {
    setLogs((prev) => [
      { id: Date.now() + Math.random(), module, label, tone, time: nowStamp() },
      ...prev,
    ].slice(0, 18));
  };

  const updatePresentation = (module: ModuleId, label: string, progress: number) => {
    setActiveModule(module);
    setPresentationStep(label);
    setPresentationProgress(progress);
  };

  const resetSimulation = () => {
    setActiveModule('overview');
    setIsRunning(false);
    setReportRevision(1);
    setDocuments(initialDocuments);
    setDeadlines(initialDeadlines);
    setClients(initialClients);
    setInvoices(initialInvoices);
    setPieces(initialPieces);
    setMessages(initialMessages);
    setLogs(initialLogs);
    setChatInput('');
    setWhatsAppConnected(false);
    setWhatsAppAutoMode(true);
    setAdvancedOps(initialAdvancedOps);
    setPresentationProgress(0);
    setPresentationStep('Ambiente reiniciado e pronto para nova demonstracao.');
  };

  const uploadDocument = () => {
    const newDocument: SimDocument = {
      id: nextId(documents),
      name: `Peticao_${documents.length + 1}.pdf`,
      status: 'uploaded',
      type: 'processual',
      summary: 'Arquivo recebido e aguardando OCR, leitura e classificacao.',
    };

    setDocuments((prev) => [newDocument, ...prev]);
    pushLog('documents', `Upload simulado de ${newDocument.name}.`, 'success');
  };

  const analyzeLatestDocument = async () => {
    const target = documents.find((document) => document.status === 'uploaded');

    if (!target) {
      pushLog('documents', 'Nenhum documento novo para analisar.', 'warning');
      return;
    }

    setDocuments((prev) =>
      prev.map((document) =>
        document.id === target.id ? { ...document, status: 'processing' } : document,
      ),
    );
    pushLog('documents', `OCR e leitura iniciados em ${target.name}.`, 'info');

    await wait(600);

    const extractedDeadline: SimDeadline = {
      id: nextId(deadlines),
      title: `Prazo extraido de ${target.name}`,
      dueDate: '2026-06-23',
      urgency: 'high',
      status: 'pending',
      source: target.name,
    };

    setDocuments((prev) =>
      prev.map((document) =>
        document.id === target.id
          ? {
              ...document,
              status: 'completed',
              summary:
                'Documento processado com sucesso; prazo, partes e pedido principal identificados.',
            }
          : document,
      ),
    );
    setDeadlines((prev) => [extractedDeadline, ...prev]);
    pushLog('documents', `${target.name} analisado e convertido em acao operacional.`, 'success');
  };

  const createDeadline = () => {
    const newDeadline: SimDeadline = {
      id: nextId(deadlines),
      title: `Revisao interna ${deadlines.length + 1}`,
      dueDate: '2026-06-26',
      urgency: 'medium',
      status: 'pending',
      source: 'Simulador',
    };

    setDeadlines((prev) => [newDeadline, ...prev]);
    pushLog('deadlines', `Novo prazo criado: ${newDeadline.title}.`, 'success');
  };

  const completeUrgentDeadline = () => {
    const target = deadlines.find((deadline) => deadline.status === 'pending');

    if (!target) {
      pushLog('deadlines', 'Nao ha prazos pendentes para concluir.', 'warning');
      return;
    }

    setDeadlines((prev) =>
      prev.map((deadline) =>
        deadline.id === target.id ? { ...deadline, status: 'completed' } : deadline,
      ),
    );
    pushLog('deadlines', `Prazo concluido: ${target.title}.`, 'success');
  };

  const deleteLastDeadline = () => {
    const removable = deadlines.find((deadline) => deadline.status === 'pending');

    if (!removable) {
      pushLog('deadlines', 'Nenhum prazo pendente disponivel para exclusao.', 'warning');
      return;
    }

    setDeadlines((prev) => prev.filter((deadline) => deadline.id !== removable.id));
    pushLog('deadlines', `Prazo removido: ${removable.title}.`, 'warning');
  };

  const addClientLead = () => {
    const newClient: SimClient = {
      id: nextId(clients),
      name: `Novo Prospecto ${clients.length + 1}`,
      stage: 'lead',
      city: 'Belo Horizonte',
    };

    setClients((prev) => [newClient, ...prev]);
    pushLog('clients', `Lead criado para ${newClient.name}.`, 'success');
  };

  const convertLead = () => {
    const lead = clients.find((client) => client.stage === 'lead');

    if (!lead) {
      pushLog('clients', 'Nao ha leads para converter agora.', 'warning');
      return;
    }

    setClients((prev) =>
      prev.map((client) =>
        client.id === lead.id ? { ...client, stage: 'active' } : client,
      ),
    );
    pushLog('clients', `${lead.name} convertido em cliente ativo.`, 'success');
  };

  const createInvoice = () => {
    const preferredClient =
      clients.find((client) => client.stage === 'active') ?? clients[0];

    if (!preferredClient) {
      pushLog('finance', 'Sem clientes ativos para gerar fatura.', 'warning');
      return;
    }

    const newInvoice: SimInvoice = {
      id: nextId(invoices),
      clientName: preferredClient.name,
      description: `Pacote consultivo ${invoices.length + 1}`,
      total: 2500 + invoices.length * 350,
      status: 'pending',
      reminderSent: false,
    };

    setInvoices((prev) => [newInvoice, ...prev]);
    pushLog('finance', `Fatura criada para ${preferredClient.name}.`, 'success');
  };

  const sendReminder = () => {
    const target = invoices.find(
      (invoice) => invoice.status !== 'paid' && !invoice.reminderSent,
    );

    if (!target) {
      pushLog('finance', 'Todas as faturas abertas ja receberam lembrete.', 'warning');
      return;
    }

    setInvoices((prev) =>
      prev.map((invoice) =>
        invoice.id === target.id
          ? {
              ...invoice,
              status: invoice.status === 'pending' ? 'overdue' : invoice.status,
              reminderSent: true,
            }
          : invoice,
      ),
    );
    pushLog('finance', `Lembrete de cobranca enviado para ${target.clientName}.`, 'success');
  };

  const markInvoicePaid = () => {
    const target = invoices.find((invoice) => invoice.status !== 'paid');

    if (!target) {
      pushLog('finance', 'Nao existem faturas abertas para baixar.', 'warning');
      return;
    }

    setInvoices((prev) =>
      prev.map((invoice) =>
        invoice.id === target.id ? { ...invoice, status: 'paid' } : invoice,
      ),
    );
    pushLog('finance', `Fatura liquidada: ${target.description}.`, 'success');
  };

  const generatePiece = () => {
    const sourceDocument =
      documents.find((document) => document.status === 'completed') ?? documents[0];

    if (!sourceDocument) {
      pushLog('legal', 'Sem documento base para gerar peca.', 'warning');
      return;
    }

    const newPiece: SimPiece = {
      id: nextId(pieces),
      title: `Minuta estrategica ${pieces.length + 1}`,
      basedOn: sourceDocument.name,
      status: 'draft',
    };

    setPieces((prev) => [newPiece, ...prev]);
    pushLog('legal', `Peca gerada a partir de ${sourceDocument.name}.`, 'success');
  };

  const reviewPiece = () => {
    const target = pieces.find((piece) => piece.status === 'draft');

    if (!target) {
      pushLog('legal', 'Nao ha rascunhos aguardando revisao.', 'warning');
      return;
    }

    setPieces((prev) =>
      prev.map((piece) => (piece.id === target.id ? { ...piece, status: 'reviewed' } : piece)),
    );
    pushLog('legal', `Rascunho revisado: ${target.title}.`, 'success');
  };

  const connectWhatsApp = () => {
    setWhatsAppConnected(true);
    pushLog('whatsapp', 'Quick setup concluido e canal conectado.', 'success');
  };

  const scheduleWhatsAppNotifications = () => {
    if (!whatsAppConnected) {
      pushLog('whatsapp', 'Conecte o canal antes de agendar notificacoes.', 'warning');
      return;
    }

    setWhatsAppAutoMode(true);
    pushLog('whatsapp', 'Notificacoes automaticas de prazo e cobranca agendadas.', 'success');
  };

  const testWhatsAppNumber = () => {
    if (!whatsAppConnected) {
      pushLog('whatsapp', 'O teste foi bloqueado porque o canal ainda nao esta ativo.', 'warning');
      return;
    }

    pushLog('whatsapp', 'Mensagem de boas-vindas enviada para o numero de teste.', 'success');
  };

  const refreshReports = () => {
    setReportRevision((prev) => prev + 1);
    pushLog('reports', 'Resumo executivo recalculado com os dados simulados atuais.', 'success');
  };

  const generateExecutiveSummary = () => {
    pushLog(
      'reports',
      'Sumario gerado: prazos criticos e cobranca merecem atencao primeiro.',
      'info',
    );
  };

  const simulatePortalSession = () => {
    setAdvancedOps((prev) => ({ ...prev, portalSessions: prev.portalSessions + 1 }));
    pushLog('operations', 'Portal do cliente acessado com timeline e documentos compartilhados.', 'success');
  };

  const simulateJurisprudence = () => {
    setAdvancedOps((prev) => ({ ...prev, jurisprudenceQueries: prev.jurisprudenceQueries + 1 }));
    pushLog('operations', 'Pesquisa jurisprudencial simulada com filtros por tema e tribunal.', 'info');
  };

  const simulateQueue = () => {
    setAdvancedOps((prev) => ({ ...prev, queueAssignments: prev.queueAssignments + 1 }));
    pushLog('operations', 'Fila de atendimento redistribuida entre advogado e assistente.', 'success');
  };

  const simulateMarketing = () => {
    setAdvancedOps((prev) => ({ ...prev, marketingCampaigns: prev.marketingCampaigns + 1 }));
    pushLog('operations', 'Campanha de captacao OAB acionada para leads mornos.', 'info');
  };

  const simulateSemanticSearch = () => {
    setAdvancedOps((prev) => ({ ...prev, semanticSearches: prev.semanticSearches + 1 }));
    pushLog('operations', 'Busca semantica executada sobre base documental do escritorio.', 'success');
  };

  const sendChatMessage = (preset?: string) => {
    const outgoing = (preset ?? chatInput).trim();

    if (!outgoing) {
      pushLog('chat', 'Digite ou escolha um prompt antes de enviar.', 'warning');
      return;
    }

    const userMessage: SimMessage = {
      id: Date.now(),
      role: 'user',
      content: outgoing,
    };

    const assistantMessage: SimMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: `Contexto do simulador: ${documents.filter((document) => document.status === 'completed').length} documentos prontos, ${deadlines.filter((deadline) => deadline.status === 'pending').length} prazos pendentes e ${invoices.filter((invoice) => invoice.status !== 'paid').length} faturas abertas. Minha recomendacao imediata e atacar prazo critico, depois cobranca e depois gerar a peca correspondente.`,
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setChatInput('');
    pushLog('chat', `Pergunta enviada ao copiloto: "${outgoing}".`, 'success');
  };

  const runFullSimulation = async () => {
    if (isRunning) {
      return;
    }

    const shortPause = presentationMode ? 850 : 200;
    const mediumPause = presentationMode ? 1200 : 300;
    const analysisPause = presentationMode ? 1600 : 600;

    setIsRunning(true);
    updatePresentation('documents', 'Abrindo documentos e simulando novo upload.', 8);
    uploadDocument();
    await wait(mediumPause);
    setPresentationStep('Executando OCR, leitura e extracao de acao do documento.');
    await analyzeLatestDocument();
    await wait(analysisPause);

    updatePresentation('deadlines', 'Priorizando prazos a partir do documento analisado.', 22);
    completeUrgentDeadline();
    await wait(shortPause);

    updatePresentation('clients', 'Atualizando pipeline comercial com um novo lead.', 34);
    addClientLead();
    await wait(shortPause);
    setPresentationStep('Convertendo lead em cliente ativo dentro do fluxo.');
    convertLead();
    await wait(shortPause);

    updatePresentation('finance', 'Gerando cobranca e testando a regua financeira.', 48);
    createInvoice();
    await wait(shortPause);
    sendReminder();
    await wait(shortPause);
    setPresentationStep('Baixando a fatura para refletir recuperacao de receita.');
    markInvoicePaid();
    await wait(shortPause);

    updatePresentation('legal', 'Transformando contexto documental em peca revisavel.', 61);
    generatePiece();
    await wait(shortPause);
    reviewPiece();
    await wait(shortPause);

    updatePresentation('whatsapp', 'Conectando o canal e simulando automacoes com cliente.', 74);
    connectWhatsApp();
    await wait(shortPause);
    scheduleWhatsAppNotifications();
    await wait(shortPause);
    testWhatsAppNumber();
    await wait(shortPause);

    updatePresentation('operations', 'Passando pelos modulos avancados de operacao.', 86);
    simulatePortalSession();
    await wait(shortPause);
    simulateJurisprudence();
    await wait(shortPause);
    simulateSemanticSearch();
    await wait(shortPause);

    updatePresentation('reports', 'Recalculando indicadores e leitura executiva.', 94);
    refreshReports();
    await wait(shortPause);
    generateExecutiveSummary();
    await wait(shortPause);

    updatePresentation('chat', 'Encerrando com uma consulta ao copiloto juridico.', 99);
    sendChatMessage('Quais sao os riscos prioritarios do escritorio hoje?');
    await wait(shortPause);

    pushLog('overview', 'Simulacao ponta a ponta concluida com sucesso.', 'success');
    setPresentationProgress(100);
    setPresentationStep('Apresentacao concluida com sucesso.');
    setIsRunning(false);
  };

  const completedDocuments = documents.filter((document) => document.status === 'completed').length;
  const pendingDeadlines = deadlines.filter((deadline) => deadline.status === 'pending').length;
  const openInvoices = invoices.filter((invoice) => invoice.status !== 'paid');
  const recoveredRevenue = invoices
    .filter((invoice) => invoice.status === 'paid')
    .reduce((total, invoice) => total + invoice.total, 0);

  const moduleContent = () => {
    if (activeModule === 'overview') {
      return (
        <SectionCard
          title="Simulador maestro do produto"
          subtitle="Este ambiente encena os fluxos mais importantes do NeoBusiness AI sem depender de login, API ou dados reais."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <p className="text-sm font-semibold text-white">O que esta sendo coberto</p>
              <div className="mt-3 grid gap-2 text-sm text-white/70">
                <p>Upload documental e analise operacional</p>
                <p>Prazos e priorizacao</p>
                <p>Clientes, faturamento e cobranca</p>
                <p>Geracao de peca e revisao</p>
                <p>WhatsApp, portal, fila e busca</p>
                <p>Resumo executivo e copiloto IA</p>
              </div>
            </div>
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4">
              <p className="text-sm font-semibold text-cyan-100">Leitura estrategica</p>
              <p className="mt-3 text-sm leading-6 text-cyan-50/80">
                A simulacao mostra que o projeto funciona melhor como plataforma operacional juridica com IA nativa do que como simples chat juridico.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {MODULES.filter((module) => module.id !== 'overview').map((module) => (
              <button
                key={module.id}
                onClick={() => setActiveModule(module.id)}
                className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition hover:border-cyan-500/40 hover:bg-white/10"
              >
                <p className="font-semibold text-white">{module.label}</p>
                <p className="mt-2 text-sm text-white/50">{module.blurb}</p>
              </button>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'documents') {
      return (
        <SectionCard
          title="Simulacao de documentos"
          subtitle="Reproduz upload, OCR, resumo e transformacao do documento em tarefa acionavel."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={uploadDocument}>Simular upload</PrimaryButton>
            <SecondaryButton onClick={() => void analyzeLatestDocument()}>
              Analisar ultimo documento
            </SecondaryButton>
          </div>

          <div className="mt-6 space-y-3">
            {documents.map((document) => (
              <div key={document.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{document.name}</p>
                    <p className="mt-1 text-sm text-white/45">{document.type}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(document.status)}`}>
                    {document.status}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-white/65">{document.summary}</p>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'deadlines') {
      return (
        <SectionCard
          title="Simulacao de prazos"
          subtitle="Encena criacao, triagem e fechamento de prazos como centro do risco operacional."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={createDeadline}>Criar prazo</PrimaryButton>
            <SecondaryButton onClick={completeUrgentDeadline}>Concluir mais urgente</SecondaryButton>
            <SecondaryButton onClick={deleteLastDeadline}>Excluir um pendente</SecondaryButton>
          </div>

          <div className="mt-6 space-y-3">
            {deadlines.map((deadline) => (
              <div key={deadline.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{deadline.title}</p>
                    <p className="mt-1 text-sm text-white/45">
                      Vence em {deadline.dueDate} via {deadline.source}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${urgencyClasses(deadline.urgency)}`}>
                      {deadline.urgency}
                    </span>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(deadline.status)}`}>
                      {deadline.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'clients') {
      return (
        <SectionCard
          title="Simulacao de clientes e CRM"
          subtitle="Mostra como lead vira cliente ativo dentro do mesmo ecossistema."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={addClientLead}>Cadastrar lead</PrimaryButton>
            <SecondaryButton onClick={convertLead}>Converter lead</SecondaryButton>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-2">
            {clients.map((client) => (
              <div key={client.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-white">{client.name}</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(client.stage)}`}>
                    {client.stage}
                  </span>
                </div>
                <p className="mt-2 text-sm text-white/50">{client.city}</p>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'finance') {
      return (
        <SectionCard
          title="Simulacao financeira"
          subtitle="Encena emissao, cobranca e baixa financeira, que e um dos eixos de valor do produto."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={createInvoice}>Gerar fatura</PrimaryButton>
            <SecondaryButton onClick={sendReminder}>Enviar lembrete</SecondaryButton>
            <SecondaryButton onClick={markInvoicePaid}>Marcar paga</SecondaryButton>
          </div>

          <div className="mt-6 space-y-3">
            {invoices.map((invoice) => (
              <div key={invoice.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{invoice.clientName}</p>
                    <p className="mt-1 text-sm text-white/45">{invoice.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-white">{formatCurrency(invoice.total)}</p>
                    <span className={`mt-2 inline-flex rounded-full px-3 py-1 text-xs font-medium ${statusClasses(invoice.status)}`}>
                      {invoice.status}
                    </span>
                  </div>
                </div>
                <p className="mt-3 text-sm text-white/55">
                  Lembrete enviado: {invoice.reminderSent ? 'sim' : 'nao'}
                </p>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'legal') {
      return (
        <SectionCard
          title="Simulacao de pecas juridicas"
          subtitle="Transforma contexto documental em rascunho juridico revisavel."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={generatePiece}>Gerar peca</PrimaryButton>
            <SecondaryButton onClick={reviewPiece}>Revisar ultimo rascunho</SecondaryButton>
          </div>

          <div className="mt-6 space-y-3">
            {pieces.map((piece) => (
              <div key={piece.id} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{piece.title}</p>
                    <p className="mt-1 text-sm text-white/45">Base: {piece.basedOn}</p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(piece.status)}`}>
                    {piece.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'whatsapp') {
      return (
        <SectionCard
          title="Simulacao de WhatsApp"
          subtitle="Reforca o diferencial de comunicacao operacional do projeto."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={connectWhatsApp}>Quick setup</PrimaryButton>
            <SecondaryButton onClick={scheduleWhatsAppNotifications}>
              Agendar notificacoes
            </SecondaryButton>
            <SecondaryButton onClick={testWhatsAppNumber}>Testar meu numero</SecondaryButton>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <p className="text-sm text-white/50">Status do canal</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {whatsAppConnected ? 'Conectado e pronto para automacoes' : 'Aguardando ativacao'}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <p className="text-sm text-white/50">Modo automatico</p>
              <p className="mt-2 text-xl font-semibold text-white">
                {whatsAppAutoMode ? 'Prazos e cobranca ligados' : 'Modo manual'}
              </p>
            </div>
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'reports') {
      return (
        <SectionCard
          title="Simulacao de relatorios"
          subtitle="Mostra a leitura executiva do escritorio a partir do estado atual da plataforma."
        >
          <div className="flex flex-wrap gap-3">
            <PrimaryButton onClick={refreshReports}>Atualizar indicadores</PrimaryButton>
            <SecondaryButton onClick={generateExecutiveSummary}>
              Gerar sumario executivo
            </SecondaryButton>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <MetricCard
              label="Revisao"
              value={`v${reportRevision}`}
              hint="Cada atualizacao recompila os sinais simulados."
            />
            <MetricCard
              label="Receita recuperada"
              value={formatCurrency(recoveredRevenue)}
              hint="Soma das faturas baixadas no ambiente de teste."
            />
            <MetricCard
              label="Prazos pendentes"
              value={String(pendingDeadlines)}
              hint="A prioridade executiva continua sendo prazo e cobranca."
            />
          </div>
        </SectionCard>
      );
    }

    if (activeModule === 'chat') {
      return (
        <SectionCard
          title="Simulacao de copiloto IA"
          subtitle="O assistente conversa com o estado atual do escritorio em vez de responder no vazio."
        >
          <div className="flex flex-wrap gap-3">
            <SecondaryButton onClick={() => sendChatMessage('Quais prazos pedem acao hoje?')}>
              Pergunta sobre prazos
            </SecondaryButton>
            <SecondaryButton onClick={() => sendChatMessage('Quais clientes e cobrancas merecem atencao?')}>
              Pergunta sobre caixa
            </SecondaryButton>
          </div>

          <div className="mt-6 space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`rounded-2xl p-4 ${
                  message.role === 'assistant'
                    ? 'border border-cyan-500/20 bg-cyan-500/10'
                    : 'border border-white/10 bg-black/20'
                }`}
              >
                <p className="text-xs uppercase tracking-[0.2em] text-white/40">
                  {message.role === 'assistant' ? 'Lex' : 'Usuario'}
                </p>
                <p className="mt-2 text-sm leading-6 text-white/80">{message.content}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col gap-3 md:flex-row">
            <input
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Digite uma pergunta para o copiloto..."
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-cyan-500/40"
            />
            <PrimaryButton onClick={() => sendChatMessage()}>Enviar</PrimaryButton>
          </div>
        </SectionCard>
      );
    }

    return (
      <SectionCard
        title="Simulacao de operacoes avancadas"
        subtitle="Cobre modulos previstos no backend que ampliam a tese de plataforma."
      >
        <div className="flex flex-wrap gap-3">
          <PrimaryButton onClick={simulatePortalSession}>Portal do cliente</PrimaryButton>
          <SecondaryButton onClick={simulateJurisprudence}>Pesquisa jurisprudencial</SecondaryButton>
          <SecondaryButton onClick={simulateQueue}>Fila de atendimento</SecondaryButton>
          <SecondaryButton onClick={simulateMarketing}>Campanha OAB</SecondaryButton>
          <SecondaryButton onClick={simulateSemanticSearch}>Busca semantica</SecondaryButton>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            label="Portal"
            value={String(advancedOps.portalSessions)}
            hint="Sessoes simuladas do cliente final."
          />
          <MetricCard
            label="Jurisprudencia"
            value={String(advancedOps.jurisprudenceQueries)}
            hint="Consultas guiadas por contexto."
          />
          <MetricCard
            label="Fila"
            value={String(advancedOps.queueAssignments)}
            hint="Distribuicoes automaticas do trabalho."
          />
          <MetricCard
            label="Marketing"
            value={String(advancedOps.marketingCampaigns)}
            hint="Acoes de nutricao e captacao."
          />
          <MetricCard
            label="Busca"
            value={String(advancedOps.semanticSearches)}
            hint="Consultas sobre a base documental."
          />
        </div>
      </SectionCard>
    );
  };

  return (
    <div className="min-h-screen bg-[#06070c] text-white">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(0,245,255,0.12),transparent_30%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.12),transparent_28%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:42px_42px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-[32px] border border-white/10 bg-white/5 p-8 shadow-2xl"
        >
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.3em] text-cyan-300/80">
                Simulador do Produto
              </p>
              <h1 className="mt-3 text-4xl font-bold leading-tight text-white md:text-5xl">
                Ambiente interativo para encenar a operacao completa do NeoBusiness AI
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-white/60">
                Aqui o produto vira uma demo navegavel: cada clique atualiza documentos, prazos, clientes, cobranca, chat, WhatsApp e os modulos operacionais previstos no backend.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <PrimaryButton onClick={() => void runFullSimulation()} disabled={isRunning}>
                {isRunning ? 'Rodando fluxo completo...' : 'Executar simulacao completa'}
              </PrimaryButton>
              <SecondaryButton onClick={() => setPresentationMode((prev) => !prev)}>
                {presentationMode ? 'Modo apresentacao: ligado' : 'Modo apresentacao: desligado'}
              </SecondaryButton>
              <SecondaryButton onClick={resetSimulation}>Reiniciar ambiente</SecondaryButton>
              <Link
                href="/"
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white/80 transition hover:bg-white/10"
              >
                Voltar para a landing
              </Link>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Documentos concluidos"
              value={String(completedDocuments)}
              hint="Sinal de maturidade do fluxo documental."
            />
            <MetricCard
              label="Prazos pendentes"
              value={String(pendingDeadlines)}
              hint="Risco operacional vivo na simulacao."
            />
            <MetricCard
              label="Faturas em aberto"
              value={String(openInvoices.length)}
              hint="Base para cobranca e automacoes."
            />
            <MetricCard
              label="WhatsApp"
              value={whatsAppConnected ? 'Ativo' : 'Desligado'}
              hint="Canal de relacionamento operacional com o cliente."
            />
          </div>

          <div className="mt-6 rounded-[28px] border border-cyan-500/20 bg-cyan-500/8 p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <p className="text-xs uppercase tracking-[0.25em] text-cyan-200/70">
                  Modo Visual
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {presentationMode ? 'Demonstracao guiada ativada' : 'Demonstracao guiada pronta para ativar'}
                </p>
                <p className="mt-3 text-sm leading-6 text-cyan-50/75">{presentationStep}</p>
              </div>
              <div className="min-w-[140px] rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-right">
                <p className="text-xs uppercase tracking-[0.2em] text-white/35">Progresso</p>
                <p className="mt-2 text-3xl font-bold text-white">{presentationProgress}%</p>
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/8">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-400 to-emerald-400 transition-all duration-500"
                style={{ width: `${presentationProgress}%` }}
              />
            </div>
            <p className="mt-3 text-xs text-white/45">
              Quando ativado, a simulacao desacelera e troca os modulos em sequencia para facilitar a observacao ao vivo.
            </p>
          </div>
        </motion.div>

        <div className="mt-8 grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div className="rounded-[28px] border border-white/10 bg-white/5 p-4">
            <p className="px-3 pb-3 text-xs uppercase tracking-[0.25em] text-white/40">
              Modulos
            </p>
            <div className="space-y-2">
              {MODULES.map((module) => (
                <button
                  key={module.id}
                  onClick={() => setActiveModule(module.id)}
                  className={`w-full rounded-2xl p-3 text-left transition ${
                    activeModule === module.id
                      ? 'border border-cyan-500/40 bg-cyan-500/15'
                      : 'border border-transparent bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <p className="font-semibold text-white">{module.label}</p>
                  <p className="mt-1 text-xs leading-5 text-white/45">{module.blurb}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            {moduleContent()}

            <SectionCard
              title="Log da simulacao"
              subtitle="Cada botao relevante deixa rastros aqui para provar o comportamento do fluxo."
            >
              <div className="space-y-3">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className={`rounded-2xl border px-4 py-3 ${toneClasses(log.tone)}`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-sm font-medium">{log.label}</p>
                      <span className="text-xs uppercase tracking-[0.2em] opacity-80">
                        {log.module} - {log.time}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    </div>
  );
}
