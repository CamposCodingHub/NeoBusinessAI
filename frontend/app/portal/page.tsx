'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/api';

const PORTAL_TOKEN_KEY = 'portal_access_token';
const PORTAL_NAME_KEY = 'portal_client_name';

type TabId = 'documents' | 'invoices' | 'timeline';

interface PortalDocument {
  id: number;
  filename: string;
  title?: string | null;
  file_type?: string | null;
  status?: string | null;
  created_at?: string | null;
}

interface PortalInvoice {
  id: number;
  invoice_number?: string | null;
  description?: string | null;
  total_amount: number;
  status: string;
  due_date?: string | null;
  payment_url?: string | null;
  created_at?: string | null;
}

interface TimelineEvent {
  type: string;
  action: string;
  label: string;
  at?: string | null;
  resource_type?: string | null;
  resource_id?: number | null;
}

function getPortalToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(PORTAL_TOKEN_KEY);
}

async function portalFetch(endpoint: string, options: RequestInit = {}): Promise<any> {
  const token = getPortalToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    let detail = 'Falha na requisição';
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return res.json();
}

function formatMoney(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString('pt-BR');
  } catch {
    return value;
  }
}

function statusClass(status: string): string {
  if (status === 'paid' || status === 'completed' || status === 'processed') {
    return 'bg-[#047857]/10 text-[#047857]';
  }
  if (status === 'overdue') return 'bg-[#b91c1c]/10 text-[#b91c1c]';
  if (status === 'pending') return 'bg-[#b45309]/10 text-[#b45309]';
  return 'bg-[#64748b]/15 text-[#475569]';
}

export default function PortalPage() {
  const [token, setToken] = useState<string | null>(null);
  const [clientName, setClientName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState('');

  const [tab, setTab] = useState<TabId>('documents');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [documents, setDocuments] = useState<PortalDocument[]>([]);
  const [invoices, setInvoices] = useState<PortalInvoice[]>([]);
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    const existing = getPortalToken();
    if (existing) {
      setToken(existing);
      setClientName(localStorage.getItem(PORTAL_NAME_KEY) || '');
    }
  }, []);

  const loadData = useCallback(async () => {
    if (!getPortalToken()) return;
    setLoading(true);
    setError('');
    try {
      const [docsRes, invRes, tlRes, meRes] = await Promise.all([
        portalFetch('/portal/documents?limit=50'),
        portalFetch('/portal/invoices?limit=50'),
        portalFetch('/portal/timeline?limit=40'),
        portalFetch('/portal/me'),
      ]);
      setDocuments(docsRes.documents || []);
      setInvoices(invRes.invoices || []);
      setEvents(tlRes.events || []);
      if (meRes.client_name) {
        setClientName(meRes.client_name);
        localStorage.setItem(PORTAL_NAME_KEY, meRes.client_name);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao carregar portal';
      setError(msg);
      if (msg.toLowerCase().includes('token') || msg.toLowerCase().includes('401')) {
        localStorage.removeItem(PORTAL_TOKEN_KEY);
        localStorage.removeItem(PORTAL_NAME_KEY);
        setToken(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) loadData();
  }, [token, loadData]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoggingIn(true);
    setLoginError('');
    try {
      const data = await portalFetch('/portal/login', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), password }),
      });
      localStorage.setItem(PORTAL_TOKEN_KEY, data.access_token);
      if (data.client_name) {
        localStorage.setItem(PORTAL_NAME_KEY, data.client_name);
        setClientName(data.client_name);
      }
      setToken(data.access_token);
      setPassword('');
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Falha no login');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(PORTAL_TOKEN_KEY);
    localStorage.removeItem(PORTAL_NAME_KEY);
    setToken(null);
    setClientName('');
    setDocuments([]);
    setInvoices([]);
    setEvents([]);
  };

  if (!token) {
    return (
      <div className="trust-shell flex min-h-screen items-center justify-center px-4">
        <div className="trust-card w-full max-w-md p-8">
          <p className="trust-kicker mb-2">NeoBusinessAI</p>
          <h1 className="trust-title mb-2">Portal do Cliente</h1>
          <p className="trust-subtitle mb-6">
            Acesse documentos e faturas compartilhados pelo seu escritório.
          </p>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                E-mail
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="seu@email.com"
                autoComplete="username"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Senha
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>
            {loginError && (
              <p className="rounded-lg bg-[#b91c1c]/10 px-3 py-2 text-sm text-[#b91c1c]">
                {loginError}
              </p>
            )}
            <button type="submit" disabled={loggingIn} className="trust-btn-primary w-full">
              {loggingIn ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-[#94a3b8]">
            Acesso exclusivo ao seu escritório.{' '}
            <Link href="/login" className="text-[#0F766E] hover:underline">
              Área do profissional
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="trust-shell px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker mb-1">Portal do Cliente</p>
            <h1 className="trust-title">
              Olá{clientName ? `, ${clientName}` : ''}
            </h1>
            <p className="trust-subtitle mt-1">
              Documentos, faturas e acompanhamento — somente leitura.
            </p>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={loadData} className="trust-btn-ghost">
              Atualizar
            </button>
            <button type="button" onClick={handleLogout} className="trust-btn-ghost">
              Sair
            </button>
          </div>
        </header>

        <nav className="mb-6 flex flex-wrap gap-2">
          {(
            [
              { id: 'documents', label: 'Documentos' },
              { id: 'invoices', label: 'Faturas' },
              { id: 'timeline', label: 'Timeline' },
            ] as { id: TabId; label: string }[]
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={
                tab === item.id
                  ? 'trust-btn-primary'
                  : 'trust-btn-ghost'
              }
            >
              {item.label}
            </button>
          ))}
        </nav>

        {error && (
          <p className="mb-4 rounded-lg bg-[#b91c1c]/10 px-3 py-2 text-sm text-[#b91c1c]">
            {error}
          </p>
        )}

        {loading && (
          <p className="mb-4 text-sm text-[#64748b]">Carregando…</p>
        )}

        {tab === 'documents' && (
          <section className="trust-card p-5">
            <h2 className="trust-section-title mb-4">Documentos compartilhados</h2>
            {documents.length === 0 && !loading ? (
              <p className="py-8 text-center text-sm text-[#94a3b8]">
                Nenhum documento compartilhado ainda.
              </p>
            ) : (
              <ul className="divide-y divide-[#e2e8f0]">
                {documents.map((doc) => (
                  <li
                    key={doc.id}
                    className="flex flex-wrap items-center justify-between gap-2 py-3"
                  >
                    <div>
                      <p className="text-sm font-semibold text-[#0C1B2A]">
                        {doc.title || doc.filename}
                      </p>
                      <p className="text-xs text-[#64748b]">
                        {doc.filename}
                        {doc.file_type ? ` · ${doc.file_type}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {doc.status && (
                        <span
                          className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${statusClass(doc.status)}`}
                        >
                          {doc.status}
                        </span>
                      )}
                      <span className="text-xs text-[#94a3b8]">
                        {formatDate(doc.created_at)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {tab === 'invoices' && (
          <section className="trust-card p-5">
            <h2 className="trust-section-title mb-4">Faturas</h2>
            {invoices.length === 0 && !loading ? (
              <p className="py-8 text-center text-sm text-[#94a3b8]">
                Nenhuma fatura encontrada.
              </p>
            ) : (
              <ul className="divide-y divide-[#e2e8f0]">
                {invoices.map((inv) => (
                  <li
                    key={inv.id}
                    className="flex flex-wrap items-center justify-between gap-2 py-3"
                  >
                    <div>
                      <p className="text-sm font-semibold text-[#0C1B2A]">
                        {inv.invoice_number || `Fatura #${inv.id}`}
                      </p>
                      <p className="text-xs text-[#64748b]">
                        {inv.description || 'Sem descrição'}
                        {' · '}
                        Venc. {formatDate(inv.due_date)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-[#0C1B2A]">
                        {formatMoney(inv.total_amount)}
                      </span>
                      <span
                        className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase ${statusClass(inv.status)}`}
                      >
                        {inv.status}
                      </span>
                      {inv.payment_url && inv.status !== 'paid' && inv.status !== 'cancelled' && (
                        <a
                          href={inv.payment_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-semibold text-[#0F766E] underline-offset-2 hover:underline"
                        >
                          Pagar
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {tab === 'timeline' && (
          <section className="trust-card p-5">
            <h2 className="trust-section-title mb-2">Timeline</h2>
            <p className="mb-4 text-xs text-[#94a3b8]">
              Placeholder MVP — atividades do portal e eventos recentes do seu caso.
            </p>
            {events.length === 0 && !loading ? (
              <p className="py-8 text-center text-sm text-[#94a3b8]">
                Sem eventos ainda. Faça login ou aguarde compartilhamentos do escritório.
              </p>
            ) : (
              <ol className="relative space-y-4 border-l border-[#d7dde5] pl-5">
                {events.map((ev, idx) => (
                  <li key={`${ev.type}-${ev.resource_id}-${idx}`} className="relative">
                    <span className="absolute -left-[1.4rem] top-1 h-2.5 w-2.5 rounded-full bg-[#0F766E]" />
                    <p className="text-sm font-medium text-[#0C1B2A]">{ev.label}</p>
                    <p className="text-xs text-[#94a3b8]">
                      {ev.type} · {formatDate(ev.at)}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
