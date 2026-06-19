'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { AnimatePresence, motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: AiMetadata;
}

interface AiSource {
  code?: string;
  title: string;
  url: string;
  status?: string;
  excerpt?: string;
}

interface SovereignSource {
  source_key: string;
  title: string;
  citation: string;
  url?: string;
  authority?: string;
  excerpt: string;
  score: number;
  semantic_score: number;
  lexical_score: number;
  private?: boolean;
}

interface RealtimeSource {
  title: string;
  url: string;
  authority: string;
  domain: string;
  excerpt: string;
  published_at?: string | null;
  updated_at?: string | null;
  retrieved_at: string;
  score: number;
  source_kind: string;
}

interface AiMetadata {
  quality_score?: number;
  style?: string;
  detected_intent?: string;
  emotional_state?: string;
  context_summary?: string;
  ai_mode?: string;
  interaction_count?: number;
  document_context_used?: boolean;
  response_mode?: 'quick' | 'balanced' | 'deep';
  is_legal_query?: boolean;
  legal_area?: string;
  jurisdiction?: string;
  grounding_status?: string;
  sources?: AiSource[];
  sovereign_sources?: SovereignSource[];
  sovereign_search_used?: boolean;
  realtime_web_used?: boolean;
  realtime_web_status?: string;
  realtime_retrieved_at?: string | null;
  realtime_latency_ms?: number;
  realtime_cache_hit?: boolean;
  realtime_sources?: RealtimeSource[];
  realtime_errors?: string[];
  requires_human_review?: boolean;
  answer_scope?: string;
  model?: string;
  requested_model?: string;
  model_degraded?: boolean;
  model_fallback_used?: boolean;
  provider?: string;
  route?: string;
  latency_ms?: number;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
  provider_fallback_used?: boolean;
  inline_citations?: number;
  source_markers?: number;
  verified_article_citations?: string[];
  citation_quality?: string;
  confidence_level?: string;
  response_complete?: boolean;
  finish_reason?: string;
  verified_articles?: string[];
  unverified_article_references?: string[];
  suppressed_article_references?: string[];
  suppressed_unsupported_lines?: number;
  suppressed_mismatched_paragraph_lines?: number;
  suppressed_mismatched_curated_claim_lines?: number;
  suppressed_invalid_source_lines?: number;
  suppressed_invalid_realtime_lines?: number;
}

interface ChatDocument {
  id: number;
  filename: string;
  title?: string;
  status: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    'Sou a Lex, sua assistente juridica inteligente.\n\nPosso ajudar com contratos, prazos, estrategia processual, produtividade e operacao do escritorio. Envie uma pergunta e eu respondo com base no modo premium quando disponivel.',
  timestamp: new Date(),
};

const SUGGESTED_PROMPTS = [
  'Explique a diferenca entre dolo eventual e culpa consciente no Codigo Penal.',
  'Quais requisitos justificam uma prisao preventiva no processo penal?',
  'Analise os riscos de um contrato de prestacao de servicos.',
  'Compare tutela de urgencia e tutela de evidencia no CPC.',
];

function getStoredUserId() {
  if (typeof window === 'undefined') return 'anonymous';

  try {
    const rawUser = localStorage.getItem('neobusiness_user');
    if (!rawUser) return 'anonymous';
    const parsed = JSON.parse(rawUser);
    return String(parsed?.id || parsed?.user_id || parsed?.email || 'anonymous');
  } catch {
    return 'anonymous';
  }
}

function getAccessToken() {
  if (typeof window === 'undefined') return '';

  try {
    const rawTokens = localStorage.getItem('neobusiness_tokens');
    if (!rawTokens) return '';
    return String(JSON.parse(rawTokens)?.access_token || '');
  } catch {
    return '';
  }
}

function getConversationStorageKey() {
  return `neobusiness_chat_${getStoredUserId()}`;
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      data-testid={`chat-message-${message.role}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed ${
          isUser
            ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 text-white rounded-br-md'
            : 'bg-white/5 border border-white/10 text-white/90 rounded-bl-md'
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap">{message.content}</div>
        ) : (
          <>
            {message.metadata?.model_degraded ? (
              <div className="mb-4 rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
                O modelo juridico principal ficou indisponivel. Esta resposta foi
                produzida em contingencia e exige verificacao reforcada.
              </div>
            ) : null}
            {message.metadata?.model_fallback_used ? (
              <div className="mb-4 rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-xs text-cyan-100">
                O motor juridico alternativo de alta capacidade concluiu esta
                resposta porque o modelo principal estava temporariamente limitado.
              </div>
            ) : null}
            {message.metadata?.response_complete === false ? (
              <div className="mb-4 rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
                A resposta atingiu o limite de extensao. Solicite continuacao antes
                de utilizar a conclusao.
              </div>
            ) : null}
            <div className="prose prose-invert prose-sm max-w-none prose-headings:text-white prose-strong:text-white prose-a:text-cyan-300">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          </>
        )}
        {!isUser && message.metadata?.sources?.length ? (
          <div className="mt-4 border-t border-white/10 pt-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/35">
              Fontes oficiais
            </div>
            <div className="space-y-2">
              {message.metadata.sources.map((source) => (
                <div
                  key={`${message.id}-${source.url}`}
                  className="block rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-3 py-2 text-xs text-cyan-200 hover:bg-cyan-500/10"
                >
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium hover:text-white"
                  >
                    {source.code ? `${source.code} - ` : ''}
                    {source.title}
                  </a>
                  {source.excerpt ? (
                    <details className="mt-2 text-white/55">
                      <summary className="cursor-pointer text-cyan-200/70">
                        Ver evidencia normativa recuperada
                      </summary>
                      <div className="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap border-t border-white/10 pt-2 leading-5">
                        {source.excerpt}
                      </div>
                    </details>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {!isUser && message.metadata?.sovereign_sources?.length ? (
          <div className="mt-4 border-t border-white/10 pt-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-300/60">
              Base juridica soberana local
            </div>
            <div className="space-y-2">
              {message.metadata.sovereign_sources.map((source) => (
                <details
                  key={`${message.id}-${source.source_key}-${source.citation}`}
                  className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-xs text-emerald-100"
                >
                  <summary className="cursor-pointer font-medium">
                    {source.citation} - relevancia{' '}
                    {Math.round(source.score * 100)}%
                  </summary>
                  <div className="mt-2 whitespace-pre-wrap border-t border-white/10 pt-2 leading-5 text-white/55">
                    {source.excerpt}
                  </div>
                  {source.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-emerald-300 hover:text-white"
                    >
                      Abrir fonte original
                    </a>
                  ) : null}
                </details>
              ))}
            </div>
          </div>
        ) : null}
        {!isUser && message.metadata?.realtime_sources?.length ? (
          <div className="mt-4 border-t border-white/10 pt-3">
            <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-300/70">
              Fontes oficiais consultadas agora
            </div>
            <div className="space-y-2">
              {message.metadata.realtime_sources.map((source) => (
                <details
                  key={`${message.id}-${source.url}`}
                  className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-xs text-amber-100"
                >
                  <summary className="cursor-pointer font-medium">
                    {source.authority} - {source.title}
                  </summary>
                  <div className="mt-2 border-t border-white/10 pt-2 leading-5 text-white/60">
                    <p className="whitespace-pre-wrap">{source.excerpt}</p>
                    <p className="mt-2 text-white/35">
                      Consultado em{' '}
                      {new Date(source.retrieved_at).toLocaleString('pt-BR')}
                    </p>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-amber-300 hover:text-white"
                    >
                      Abrir pagina oficial
                    </a>
                  </div>
                </details>
              ))}
            </div>
          </div>
        ) : null}
        <div className="mt-3 text-[11px] text-white/35">
          {message.timestamp.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </motion.div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [aiMode, setAiMode] = useState<'premium' | 'simulado' | 'carregando'>(
    'carregando'
  );
  const [errorMessage, setErrorMessage] = useState('');
  const [lastMetadata, setLastMetadata] = useState<AiMetadata | null>(null);
  const [historyReady, setHistoryReady] = useState(false);
  const [documents, setDocuments] = useState<ChatDocument[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [documentContext, setDocumentContext] = useState('');
  const [documentLoading, setDocumentLoading] = useState(false);
  const [responseMode, setResponseMode] = useState<
    'quick' | 'balanced' | 'deep'
  >('balanced');
  const [researchProgress, setResearchProgress] = useState(0);
  const [researchStage, setResearchStage] = useState('');
  const [sovereignStatus, setSovereignStatus] = useState<{
    status: string;
    models?: {
      fast?: string;
      quick?: string;
      balanced?: string;
      deep?: string;
    };
    knowledge?: { sources?: number; chunks?: number; embedded_chunks?: number };
  } | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const modeLabel = useMemo(() => {
    if (sovereignStatus?.status === 'healthy') return 'IA soberana local';
    if (aiMode === 'premium') return 'IA local conectada';
    if (aiMode === 'simulado') return 'Fallback inteligente ativo';
    return 'Verificando motor de IA';
  }, [aiMode, sovereignStatus]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(getConversationStorageKey());
      if (stored) {
        const parsed = JSON.parse(stored) as Array<
          Omit<Message, 'timestamp'> & { timestamp: string }
        >;
        const restored = parsed
          .filter((message) => message?.content && message?.role)
          .slice(-60)
          .map((message) => ({
            ...message,
            timestamp: new Date(message.timestamp),
          }));
        if (restored.length > 0) {
          setMessages(restored);
        }
      }
    } catch (error) {
      console.error('Erro ao restaurar conversa:', error);
    } finally {
      setHistoryReady(true);
    }
  }, []);

  useEffect(() => {
    if (!historyReady) return;

    const serializable = messages.slice(-60).map((message) => ({
      ...message,
      timestamp: message.timestamp.toISOString(),
    }));
    localStorage.setItem(
      getConversationStorageKey(),
      JSON.stringify(serializable)
    );
  }, [historyReady, messages]);

  useEffect(() => {
    const loadDocuments = async () => {
      const accessToken = getAccessToken();
      if (!accessToken) return;

      try {
        const response = await fetch(`${API_URL}/documents/?limit=100`, {
          headers: { Authorization: `Bearer ${accessToken}` },
          credentials: 'omit',
        });
        if (!response.ok) return;
        const data = await response.json();
        setDocuments(
          (Array.isArray(data?.documents) ? data.documents : []).filter(
            (document: ChatDocument) => document.status === 'completed'
          )
        );
      } catch (error) {
        console.error('Erro ao carregar documentos para o chat:', error);
      }
    };

    void loadDocuments();
  }, []);

  useEffect(() => {
    const loadDocumentContext = async () => {
      if (selectedDocumentIds.length === 0) {
        setDocumentContext('');
        return;
      }

      const accessToken = getAccessToken();
      if (!accessToken) return;

      setDocumentLoading(true);
      try {
        const selected = documents.filter((document) =>
          selectedDocumentIds.includes(String(document.id))
        );
        const perDocumentBudget = Math.max(
          2500,
          Math.floor(18000 / Math.max(1, selected.length))
        );
        const payloads = await Promise.all(
          selected.map(async (document) => {
            const response = await fetch(
              `${API_URL}/documents/${document.id}`,
              {
                headers: { Authorization: `Bearer ${accessToken}` },
                credentials: 'omit',
              }
            );
            if (!response.ok) {
              throw new Error(
                `Documento ${document.title || document.filename} indisponivel`
              );
            }
            const data = await response.json();
            const content = data?.content || {};
            return [
              `ARQUIVO: ${document.title || document.filename}`,
              `RESUMO: ${data?.summary || content?.summary || 'Nao informado'}`,
              `ANALISE: ${data?.analysis || content?.analysis || 'Nao informada'}`,
              `PARTES: ${JSON.stringify(content?.parties || {})}`,
              `PRAZOS: ${JSON.stringify(content?.deadlines || [])}`,
              `VALORES: ${JSON.stringify(content?.values || [])}`,
              `TEXTO EXTRAIDO: ${String(content?.extracted_text || '').slice(0, 3500)}`,
            ].join('\n').slice(0, perDocumentBudget);
          })
        );
        setDocumentContext(payloads.join('\n\n--- PROXIMO ARQUIVO ---\n\n'));
      } catch (error) {
        console.error('Erro ao carregar contexto documental:', error);
        setDocumentContext('');
        setErrorMessage('Nao foi possivel carregar o contexto do documento.');
      } finally {
        setDocumentLoading(false);
      }
    };

    void loadDocumentContext();
  }, [documents, selectedDocumentIds]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const sovereignResponse = await fetch(
          `${API_URL}/ai/sovereign/status`
        );
        const sovereignData = await sovereignResponse.json();
        setSovereignStatus(sovereignData);
        setAiMode(
          sovereignResponse.ok && sovereignData?.status === 'healthy'
            ? 'premium'
            : 'simulado'
        );
      } catch (error) {
        console.error('Erro ao validar IA:', error);
        setAiMode('simulado');
      }
    };

    void checkStatus();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${Math.min(
      textareaRef.current.scrollHeight,
      200
    )}px`;
  }, [input]);

  const appendAssistantMessage = (content: string, metadata?: AiMetadata) => {
    setMessages((current) => [
      ...current,
      {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content,
        timestamp: new Date(),
        metadata,
      },
    ]);
    setLastMetadata(metadata || null);
  };

  const waitForResearchJob = async (
    jobId: number,
    accessToken: string
  ): Promise<{ response: string; metadata: AiMetadata }> => {
    for (let attempt = 0; attempt < 1200; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      const response = await fetch(
        `${API_URL}/ai/sovereign/research-jobs/${jobId}`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          credentials: 'omit',
        }
      );
      const data = await response.json().catch(() => null);
      if (!response.ok || !data) {
        throw new Error('Nao foi possivel acompanhar a pesquisa profunda.');
      }
      setResearchProgress(Number(data.progress || 0));
      setResearchStage(String(data.stage || 'processing'));
      if (data.status === 'completed' && data.result) {
        return {
          response: data.result,
          metadata: {
            ...(data.metadata?.legal_metadata || {}),
            quality_score: data.metadata?.quality_score,
            ai_mode: 'sovereign_deep',
            response_mode: 'deep',
            provider: data.provider,
            model: data.model,
          },
        };
      }
      if (data.status === 'error') {
        throw new Error(data.error || 'A pesquisa profunda falhou.');
      }
    }
    throw new Error('A pesquisa profunda excedeu uma hora.');
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const prompt = input.trim();
    setErrorMessage('');
    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        content: prompt,
        timestamp: new Date(),
      },
    ]);
    setInput('');
    setIsTyping(true);
    setResearchProgress(0);
    setResearchStage('');

    try {
      const accessToken = getAccessToken();
      if (!accessToken) {
        throw new Error('Sessao expirada. Faca login novamente.');
      }
      if (responseMode === 'deep') {
        const queuedResponse = await fetch(
          `${API_URL}/ai/sovereign/research-jobs`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
              query: prompt,
              conversation_id: 'main',
              document_context: documentContext,
              jurisdiction: 'Brasil - federal',
              legal_area: lastMetadata?.is_legal_query
                ? lastMetadata.legal_area
                : undefined,
            }),
          }
        );
        const queuedData = await queuedResponse.json().catch(() => null);
        if (!queuedResponse.ok || !queuedData?.job_id) {
          throw new Error(
            queuedData?.detail || 'Falha ao enfileirar pesquisa profunda'
          );
        }
        setResearchProgress(Number(queuedData.progress || 5));
        setResearchStage('queued');
        const completed = await waitForResearchJob(
          Number(queuedData.job_id),
          accessToken
        );
        appendAssistantMessage(completed.response, completed.metadata);
        setAiMode('premium');
        return;
      }

      const response = await fetch(`${API_URL}/api/chat/premium`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          message: prompt,
          conversation_id: 'main',
          document_context: documentContext,
          response_mode: responseMode,
          jurisdiction: 'Brasil - federal',
          legal_area: lastMetadata?.is_legal_query
            ? lastMetadata.legal_area
            : undefined,
        }),
      });

      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.success || !data?.response) {
        throw new Error(data?.error || 'Falha ao conversar com a IA premium');
      }

      appendAssistantMessage(data.response, data.metadata || null);
      setAiMode('premium');
    } catch (error) {
      console.error('Erro no chat premium:', error);
      setErrorMessage(
        'Nao foi possivel acessar o motor de IA. Nenhuma orientacao juridica foi simulada.'
      );
      appendAssistantMessage(
        'O motor especializado esta indisponivel neste momento. Para sua seguranca, a Lex nao gerou uma resposta juridica local sem fontes. Tente novamente em instantes.',
        {
        ai_mode: 'simulado',
        style: 'falha_segura',
        model_degraded: true,
      }
      );
      setAiMode('simulado');
    } finally {
      setIsTyping(false);
      setResearchProgress(0);
      setResearchStage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const clearConversation = () => {
    const nextWelcome = { ...WELCOME_MESSAGE, timestamp: new Date() };
    setMessages([nextWelcome]);
    setLastMetadata(null);
    setErrorMessage('');
    localStorage.removeItem(getConversationStorageKey());
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex flex-col">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(0,245,255,0.08),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(168,85,247,0.08),transparent_45%)]" />
        <div className="absolute inset-0 opacity-[0.02]" style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.12) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }} />
      </div>

      <motion.header
        initial={{ y: -16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative z-10 border-b border-white/5 backdrop-blur-md bg-black/20"
      >
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 flex items-center justify-center font-bold">
                N
              </div>
              <div>
                <div className="font-semibold">Lex Assistant</div>
                <div className="text-xs text-white/40">Chat inteligente do NeoBusiness AI</div>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1 rounded-full text-xs border ${
                aiMode === 'premium'
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : aiMode === 'simulado'
                    ? 'border-amber-500/40 bg-amber-500/10 text-amber-300'
                    : 'border-white/15 bg-white/5 text-white/50'
              }`}
            >
              {modeLabel}
            </span>
            <button
              onClick={clearConversation}
              className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm text-white/70 hover:text-white transition"
            >
              Limpar conversa
            </button>
            <Link
              href="/dashboard"
              className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-sm text-white/70 hover:text-white transition"
            >
              Voltar ao dashboard
            </Link>
          </div>
        </div>
      </motion.header>

      <div className="relative z-10 flex-1 overflow-hidden">
        <div className="max-w-6xl mx-auto h-full grid lg:grid-cols-[1fr_300px] gap-6 px-4 py-6">
          <div className="flex flex-col min-h-0 rounded-3xl border border-white/10 bg-black/20 backdrop-blur-xl">
            <div className="p-5 border-b border-white/5">
              <h1 className="text-xl font-semibold">Conversa com IA</h1>
              <p className="text-sm text-white/45 mt-1">
                Respostas guiadas por contexto juridico e operacao do escritorio.
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="inline-flex items-center gap-3 rounded-2xl rounded-bl-md border border-white/10 bg-white/5 px-5 py-4 text-sm text-white/60"
                >
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:120ms]" />
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:240ms]" />
                  </div>
                {responseMode === 'deep'
                  ? `Pesquisa local: ${researchStage || 'preparando'} - ${researchProgress}%`
                  : 'Processando resposta...'}
                </motion.div>
              )}

              <div ref={bottomRef} />
            </div>

            <div className="border-t border-white/5 p-4">
              {errorMessage && (
                <div className="mb-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
                  {errorMessage}
                </div>
              )}

              <div className="mb-3 flex flex-wrap gap-2">
                {[
                  ['quick', 'Consulta rapida'],
                  ['balanced', 'Analise juridica'],
                  ['deep', 'Pesquisa profunda'],
                ].map(([mode, label]) => (
                  <button
                    key={mode}
                    onClick={() =>
                      setResponseMode(mode as 'quick' | 'balanced' | 'deep')
                    }
                    className={`rounded-full border px-3 py-1.5 text-xs transition ${
                      responseMode === mode
                        ? 'border-cyan-400/50 bg-cyan-400/15 text-cyan-200'
                        : 'border-white/10 bg-white/5 text-white/45 hover:text-white'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="relative flex items-end gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 focus-within:border-cyan-500/40">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Pergunte sobre leis, jurisprudencia, contratos, estrategia processual ou seus documentos..."
                  className="flex-1 bg-transparent resize-none outline-none text-sm text-white placeholder-white/35 min-h-[24px] max-h-[200px] py-2"
                  rows={1}
                />

                <motion.button
                  onClick={() => void handleSend()}
                  disabled={!input.trim() || isTyping}
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  className={`px-4 py-3 rounded-xl text-sm font-semibold transition ${
                    input.trim() && !isTyping
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_24px_rgba(6,182,212,0.45)]'
                      : 'bg-white/10 text-white/30 cursor-not-allowed'
                  }`}
                >
                  Enviar
                </motion.button>
              </div>

              <div className="mt-2 flex items-center justify-between text-xs text-white/30">
                <span>Enter envia. Shift + Enter quebra linha.</span>
                <span>Confira dados sensiveis e validacoes juridicas antes de usar em producao.</span>
              </div>
            </div>
          </div>

          <aside className="rounded-3xl border border-white/10 bg-black/20 backdrop-blur-xl p-5 space-y-5 h-fit">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/40">
                Estado da IA
              </h2>
              <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="text-lg font-semibold">
                  {sovereignStatus?.status === 'healthy'
                    ? 'Motor soberano online'
                    : aiMode === 'premium'
                      ? 'Motor local online'
                      : 'Modo contingencia'}
                </div>
                <p className="text-sm text-white/45 mt-1">
                  {sovereignStatus?.status === 'healthy'
                    ? `${sovereignStatus.knowledge?.sources || 0} fontes e ${sovereignStatus.knowledge?.chunks || 0} trechos locais.`
                    : 'O servidor local nao respondeu. Nenhuma conclusao juridica sera simulada.'}
                </p>
                {sovereignStatus?.models ? (
                  <div className="mt-3 space-y-1 text-xs text-white/35">
                    <div>Rapido: {sovereignStatus.models.quick}</div>
                    <div>Analise: {sovereignStatus.models.balanced}</div>
                    <div>Profundo: {sovereignStatus.models.deep}</div>
                  </div>
                ) : null}
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/40">
                Documento em contexto
              </h2>
              <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 p-4">
                <select
                  aria-label="Documento em contexto"
                  multiple
                  value={selectedDocumentIds}
                  onChange={(event) =>
                    setSelectedDocumentIds(
                      Array.from(event.target.selectedOptions).map(
                        (option) => option.value
                      )
                    )
                  }
                  className="w-full rounded-xl border border-white/10 bg-[#11131b] px-3 py-2 text-sm text-white outline-none focus:border-cyan-500/50"
                  size={Math.min(5, Math.max(2, documents.length + 1))}
                >
                  {documents.map((document) => (
                    <option key={document.id} value={document.id}>
                      {document.title || document.filename}
                    </option>
                  ))}
                </select>
                <p
                  data-testid="document-context-status"
                  className="mt-3 text-xs leading-5 text-white/45"
                >
                  {documentLoading
                    ? 'Carregando contexto...'
                    : documentContext
                      ? `Contexto analisado conectado: ${selectedDocumentIds.length} documento(s).`
                      : 'Selecione um ou mais documentos concluidos. Use Ctrl para escolher varios.'}
                </p>
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/40">
                Sugestoes
              </h2>
              <div className="mt-3 space-y-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="w-full text-left rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-3 text-sm text-white/75 transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/40">
                Ultima resposta
              </h2>
              <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70 space-y-2">
                <div>Modo: {lastMetadata?.ai_mode || aiMode}</div>
                <div>Estilo: {lastMetadata?.style || 'nao informado'}</div>
                <div>Intencao: {lastMetadata?.detected_intent || 'nao detectada'}</div>
                <div>Emocao: {lastMetadata?.emotional_state || 'neutra'}</div>
                <div>Area: {lastMetadata?.legal_area || 'geral'}</div>
                <div>
                  Fundamentacao:{' '}
                  {lastMetadata?.grounding_status === 'official_sources'
                    ? 'fontes oficiais'
                    : lastMetadata?.grounding_status === 'official_links'
                      ? 'links oficiais'
                      : 'nao verificada'}
                </div>
                <div>
                  Profundidade:{' '}
                  {lastMetadata?.response_mode || responseMode}
                </div>
                <div>Modelo: {lastMetadata?.model || 'roteamento automatico'}</div>
                <div>Provedor: {lastMetadata?.provider || 'local automatico'}</div>
                <div>Rota: {lastMetadata?.route || 'nao informada'}</div>
                <div>
                  Latencia:{' '}
                  {typeof lastMetadata?.latency_ms === 'number'
                    ? `${(lastMetadata.latency_ms / 1000).toFixed(1)}s`
                    : 'nao informada'}
                </div>
                <div>
                  Tokens:{' '}
                  {lastMetadata?.usage?.total_tokens ?? 'nao informados'}
                </div>
                <div>
                  Base local:{' '}
                  {lastMetadata?.sovereign_search_used
                    ? 'consultada'
                    : 'sem resultado adicional'}
                </div>
                <div>
                  Internet oficial:{' '}
                  {lastMetadata?.realtime_web_used
                    ? `consultada (${lastMetadata.realtime_sources?.length || 0} fontes)`
                    : lastMetadata?.realtime_web_status === 'error'
                      ? 'falha na consulta'
                      : 'nao solicitada'}
                </div>
                {lastMetadata?.realtime_retrieved_at ? (
                  <div>
                    Atualidade:{' '}
                    {new Date(
                      lastMetadata.realtime_retrieved_at
                    ).toLocaleString('pt-BR')}
                  </div>
                ) : null}
                <div>
                  Confianca:{' '}
                  {lastMetadata?.confidence_level || 'nao classificada'}
                </div>
                <div>
                  Citacoes no texto:{' '}
                  {lastMetadata?.inline_citations ?? 'nao auditadas'}
                </div>
                <div>
                  Resposta:{' '}
                  {lastMetadata?.response_complete === false
                    ? 'incompleta por limite'
                    : 'concluida'}
                </div>
                <div>
                  Artigos verificados:{' '}
                  {lastMetadata?.verified_articles?.length
                    ? lastMetadata.verified_articles.join(', ')
                    : 'nenhum no recorte'}
                </div>
                <div>
                  Referencias fora do recorte:{' '}
                  {lastMetadata?.unverified_article_references?.length
                    ? lastMetadata.unverified_article_references.join(', ')
                    : 'nenhuma'}
                </div>
                <div>
                  Trechos suprimidos:{' '}
                  {lastMetadata?.suppressed_unsupported_lines || 0}
                </div>
                <div>
                  Paragrafos inconsistentes:{' '}
                  {lastMetadata?.suppressed_mismatched_paragraph_lines || 0}
                </div>
                <div>
                  Associacoes normativas bloqueadas:{' '}
                  {lastMetadata?.suppressed_mismatched_curated_claim_lines || 0}
                </div>
                <div>
                  Fontes invalidas bloqueadas:{' '}
                  {lastMetadata?.suppressed_invalid_source_lines || 0}
                </div>
                <div>
                  Atualizacoes invalidas bloqueadas:{' '}
                  {lastMetadata?.suppressed_invalid_realtime_lines || 0}
                </div>
                <div>
                  Execucao:{' '}
                  {lastMetadata?.model_degraded
                    ? 'contingencia, revisar'
                    : lastMetadata?.model_fallback_used
                      ? 'motor robusto alternativo'
                    : 'modelo solicitado concluido'}
                </div>
                <div>
                  Documento:{' '}
                  {lastMetadata?.document_context_used
                    ? 'contexto utilizado'
                    : selectedDocumentIds.length
                      ? 'contexto enviado'
                      : 'nao selecionado'}
                </div>
                <div>
                  Qualidade:{' '}
                  {typeof lastMetadata?.quality_score === 'number'
                    ? `${lastMetadata.quality_score}`
                    : 'nao disponivel'}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
