'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface AIAuditEvent {
  id: number;
  conversation_id?: string | null;
  message_preview?: string | null;
  response_preview?: string | null;
  model?: string | null;
  provider?: string | null;
  legal_area?: string | null;
  grounding_status?: string | null;
  requires_human_review?: boolean;
  created_at?: string | null;
}

function hasDashboardToken(): boolean {
  if (typeof window === 'undefined') return false;
  if (localStorage.getItem('token')) return true;
  try {
    const raw = localStorage.getItem('neobusiness_tokens');
    if (!raw) return false;
    return !!JSON.parse(raw)?.access_token;
  } catch {
    return false;
  }
}

function formatWhen(iso?: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function groundingClass(status?: string | null): string {
  const s = (status || '').toLowerCase();
  if (s.includes('verified') || s.includes('grounded')) {
    return 'text-teal-700 bg-teal-50';
  }
  if (s.includes('partial')) {
    return 'text-amber-800 bg-amber-50';
  }
  return 'text-slate-600 bg-slate-100';
}

export default function AIAuditPage() {
  const router = useRouter();
  const [events, setEvents] = useState<AIAuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadEvents = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/ai/audit?limit=50');
      setEvents(data.events || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar auditoria');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  if (loading) {
    return (
      <div className="trust-shell flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#0F766E] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="trust-shell px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker">Compliance · Lex 2026</p>
            <h1 className="trust-title mt-1">Auditoria de IA</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Últimas 50 respostas Lex com preview, modelo, área, grounding e flag de
              revisão humana — trilha pragmática para accountability.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="trust-btn-ghost">
              ← Dashboard
            </Link>
            <button type="button" onClick={loadEvents} className="trust-btn">
              Atualizar
            </button>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {events.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white/80 px-6 py-12 text-center text-slate-500">
            Nenhum evento de auditoria ainda. Use o chat premium Lex para gerar
            registros.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white/90 shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3 font-semibold">Quando</th>
                  <th className="px-3 py-3 font-semibold">Mensagem</th>
                  <th className="px-3 py-3 font-semibold">Resposta</th>
                  <th className="px-3 py-3 font-semibold">Modelo</th>
                  <th className="px-3 py-3 font-semibold">Área</th>
                  <th className="px-3 py-3 font-semibold">Grounding</th>
                  <th className="px-3 py-3 font-semibold">Revisão</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr
                    key={ev.id}
                    className="border-b border-slate-100 align-top last:border-0 hover:bg-slate-50/80"
                  >
                    <td className="whitespace-nowrap px-3 py-3 text-slate-600">
                      {formatWhen(ev.created_at)}
                    </td>
                    <td className="max-w-[180px] px-3 py-3 text-slate-800">
                      <span className="line-clamp-3">{ev.message_preview || '—'}</span>
                    </td>
                    <td className="max-w-[220px] px-3 py-3 text-slate-600">
                      <span className="line-clamp-3">{ev.response_preview || '—'}</span>
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      <div className="font-medium">{ev.model || '—'}</div>
                      <div className="text-xs text-slate-400">{ev.provider || ''}</div>
                    </td>
                    <td className="px-3 py-3 text-slate-700">{ev.legal_area || '—'}</td>
                    <td className="px-3 py-3">
                      <span
                        className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${groundingClass(
                          ev.grounding_status
                        )}`}
                      >
                        {ev.grounding_status || '—'}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      {ev.requires_human_review ? (
                        <span className="font-semibold text-amber-700">Sim</span>
                      ) : (
                        <span className="text-slate-400">Não</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
