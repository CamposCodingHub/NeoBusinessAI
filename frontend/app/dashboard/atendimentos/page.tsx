'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface ContactLog {
  id: number;
  subject: string;
  channel: string;
  summary?: string | null;
  contacted_at?: string | null;
  client_id?: number | null;
}

const EMPTY = {
  subject: '',
  channel: 'phone',
  summary: '',
  contacted_at: '',
};

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

function fmt(iso?: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

const CHANNEL_LABEL: Record<string, string> = {
  phone: 'Telefone',
  whatsapp: 'WhatsApp',
  email: 'E-mail',
  in_person: 'Presencial',
  other: 'Outro',
};

export default function AtendimentosPage() {
  const router = useRouter();
  const [items, setItems] = useState<ContactLog[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/contacts/logs');
      if (!res.ok) throw new Error(`Lista falhou (${res.status})`);
      const json = await res.json();
      setItems(json.logs || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    void load();
  }, [load, router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const payload: Record<string, string> = {
        subject: form.subject.trim(),
        channel: form.channel,
      };
      if (form.summary.trim()) payload.summary = form.summary.trim();
      if (form.contacted_at) {
        payload.contacted_at = new Date(form.contacted_at).toISOString();
      }
      const res = await apiFetch('/contacts/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Salvar falhou (${res.status})`);
      setForm(EMPTY);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar');
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Casos
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
              Atendimentos
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Histórico de ligações, WhatsApp e reuniões — para não depender da
              memória ou do chat pessoal.
            </p>
          </div>
          <Link href="/dashboard" className="text-sm text-teal-400 hover:text-teal-300">
            ← Dashboard
          </Link>
        </div>

        <form
          onSubmit={onSubmit}
          className="mb-8 grid gap-3 rounded-xl border border-slate-700/60 bg-slate-900/50 p-5"
        >
          <input
            required
            value={form.subject}
            onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
            placeholder="Assunto do contato"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-slate-400">
              Canal
              <select
                value={form.channel}
                onChange={(e) =>
                  setForm((f) => ({ ...f, channel: e.target.value }))
                }
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              >
                <option value="phone">Telefone</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="email">E-mail</option>
                <option value="in_person">Presencial</option>
                <option value="other">Outro</option>
              </select>
            </label>
            <label className="text-xs text-slate-400">
              Quando
              <input
                type="datetime-local"
                value={form.contacted_at}
                onChange={(e) =>
                  setForm((f) => ({ ...f, contacted_at: e.target.value }))
                }
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              />
            </label>
          </div>
          <textarea
            value={form.summary}
            onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
            placeholder="Resumo do que foi combinado"
            rows={3}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="justify-self-start rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
          >
            Registrar
          </button>
        </form>

        {error && (
          <p className="mb-4 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-slate-400">Carregando…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhum atendimento registrado.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((log) => (
              <li
                key={log.id}
                className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium text-white">{log.subject}</p>
                  <p className="text-xs text-slate-400">{fmt(log.contacted_at)}</p>
                </div>
                <p className="mt-1 text-xs uppercase tracking-wide text-teal-400/90">
                  {CHANNEL_LABEL[log.channel] || log.channel}
                </p>
                {log.summary ? (
                  <p className="mt-2 text-sm text-slate-300 whitespace-pre-wrap">
                    {log.summary}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
