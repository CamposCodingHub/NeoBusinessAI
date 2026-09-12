'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface ActivityEvent {
  id: number;
  action?: string | null;
  summary?: string | null;
  entity_type?: string | null;
  entity_id?: number | null;
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

export default function ActivityPage() {
  const router = useRouter();
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadEvents = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/operations/activity');
      setEvents(data.events || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar atividade');
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
            <p className="trust-kicker">Operações · Lex 2026</p>
            <h1 className="trust-title mt-1">Atividade</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Últimos eventos do feed operacional — ações-chave do escritório para
              observabilidade leve.
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
            Nenhum evento ainda. Ações como intake, matters, time e equipe geram
            registros aqui.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white/90 shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3 font-semibold">Quando</th>
                  <th className="px-3 py-3 font-semibold">Ação</th>
                  <th className="px-3 py-3 font-semibold">Resumo</th>
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
                    <td className="px-3 py-3 font-mono text-xs text-teal-800">
                      {ev.action || '—'}
                    </td>
                    <td className="max-w-[420px] px-3 py-3 text-slate-800">
                      {ev.summary || '—'}
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
