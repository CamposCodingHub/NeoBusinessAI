'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface PowerOfAttorney {
  id: number;
  title: string;
  status: string;
  granted_at?: string | null;
  expires_at?: string | null;
  notes?: string | null;
  client_id?: number | null;
  matter_id?: number | null;
}

const EMPTY_FORM = {
  title: '',
  expires_at: '',
  notes: '',
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

function statusBadge(status: string): string {
  switch (status) {
    case 'expired':
      return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    case 'revoked':
      return 'bg-red-500/20 text-red-300 border-red-500/40';
    default:
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
  }
}

function formatWhen(iso?: string | null): string {
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

export default function PoaPage() {
  const router = useRouter();
  const [items, setItems] = useState<PowerOfAttorney[]>([]);
  const [expiring, setExpiring] = useState<PowerOfAttorney[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const [all, soon] = await Promise.all([
        apiFetch('/poa'),
        apiFetch('/poa/expiring?days=30'),
      ]);
      if (!all.ok) throw new Error(`Lista falhou (${all.status})`);
      if (!soon.ok) throw new Error(`Vencimentos falhou (${soon.status})`);
      const allJson = await all.json();
      const soonJson = await soon.json();
      setItems(allJson.powers || []);
      setExpiring(soonJson.powers || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar');
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
      const payload: Record<string, string> = { title: form.title.trim() };
      if (form.expires_at) {
        payload.expires_at = new Date(form.expires_at).toISOString();
      }
      if (form.notes.trim()) payload.notes = form.notes.trim();
      const res = await apiFetch('/poa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Criar falhou (${res.status})`);
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar');
    }
  }

  async function revoke(id: number) {
    setError('');
    try {
      const res = await apiFetch(`/poa/${id}/revoke`, { method: 'POST' });
      if (!res.ok) throw new Error(`Revogar falhou (${res.status})`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao revogar');
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Casos
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
              Procurações
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Controle operacional de validade — alerta antes de audiência ou
              petição. Não substitui registro cartorial.
            </p>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-teal-400 hover:text-teal-300"
          >
            ← Dashboard
          </Link>
        </div>

        {expiring.length > 0 && (
          <section className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <h2 className="text-sm font-semibold text-amber-200">
              Vencem em 30 dias ({expiring.length})
            </h2>
            <ul className="mt-2 space-y-1 text-sm text-amber-100/90">
              {expiring.map((p) => (
                <li key={p.id}>
                  {p.title} — {formatWhen(p.expires_at)}
                </li>
              ))}
            </ul>
          </section>
        )}

        <form
          onSubmit={onSubmit}
          className="mb-8 grid gap-3 rounded-xl border border-slate-700/60 bg-slate-900/50 p-5"
        >
          <h2 className="text-sm font-semibold text-slate-200">Nova procuração</h2>
          <input
            required
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Título (ex.: ad judicia — processo 0001234)"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <label className="text-xs text-slate-400">
            Validade
            <input
              type="datetime-local"
              value={form.expires_at}
              onChange={(e) =>
                setForm((f) => ({ ...f, expires_at: e.target.value }))
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
          </label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            placeholder="Notas internas (opcional)"
            rows={2}
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
          <p className="text-sm text-slate-400">Nenhuma procuração cadastrada.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((p) => (
              <li
                key={p.id}
                className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{p.title}</p>
                    <p className="mt-1 text-xs text-slate-400">
                      Validade: {formatWhen(p.expires_at)}
                    </p>
                    {p.notes && (
                      <p className="mt-2 text-sm text-slate-300">{p.notes}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-md border px-2 py-0.5 text-xs ${statusBadge(p.status)}`}
                    >
                      {p.status}
                    </span>
                    {p.status === 'active' && (
                      <button
                        type="button"
                        onClick={() => void revoke(p.id)}
                        className="text-xs text-slate-400 underline hover:text-red-300"
                      >
                        Revogar
                      </button>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
