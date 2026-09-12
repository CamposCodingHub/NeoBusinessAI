'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface FollowUp {
  id: number;
  subject: string;
  status: string;
  due_at?: string | null;
  notes?: string | null;
}

const EMPTY = { subject: '', due_at: '', notes: '' };

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

export default function FollowupsPage() {
  const router = useRouter();
  const [items, setItems] = useState<FollowUp[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/followups?open_only=true');
      if (!res.ok) throw new Error(`Lista falhou (${res.status})`);
      const json = await res.json();
      setItems(json.followups || []);
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
      if (!form.due_at) throw new Error('Informe a data do retorno');
      const payload: Record<string, string> = {
        subject: form.subject.trim(),
        due_at: new Date(form.due_at).toISOString(),
      };
      if (form.notes.trim()) payload.notes = form.notes.trim();
      const res = await apiFetch('/followups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Criar falhou (${res.status})`);
      setForm(EMPTY);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
    }
  }

  async function markDone(id: number) {
    setError('');
    try {
      const res = await apiFetch(`/followups/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'done' }),
      });
      if (!res.ok) throw new Error(`Concluir falhou (${res.status})`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
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
              Follow-ups
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Lembretes de retorno ao cliente — não confundir com prazo
              processual.
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
            placeholder="O que retomar? (ex.: ligar sobre proposta)"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <label className="text-xs text-slate-400">
            Quando retornar
            <input
              required
              type="datetime-local"
              value={form.due_at}
              onChange={(e) => setForm((f) => ({ ...f, due_at: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
          </label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            placeholder="Notas (opcional)"
            rows={2}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="justify-self-start rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
          >
            Agendar
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
          <p className="text-sm text-slate-400">Nenhum follow-up aberto.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div>
                  <p className="font-medium text-white">{item.subject}</p>
                  <p className="mt-1 text-xs text-slate-400">{fmt(item.due_at)}</p>
                  {item.notes ? (
                    <p className="mt-2 text-sm text-slate-300">{item.notes}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => void markDone(item.id)}
                  className="text-xs text-teal-400 underline hover:text-teal-300"
                >
                  Concluir
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
