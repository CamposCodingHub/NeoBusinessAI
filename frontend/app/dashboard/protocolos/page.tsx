'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface Protocol {
  id: number;
  title: string;
  protocol_number: string;
  system: string;
  court?: string | null;
  status: string;
  filed_at?: string | null;
  notes?: string | null;
}

const EMPTY = {
  title: '',
  protocol_number: '',
  system: 'pje',
  court: '',
  filed_at: '',
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

export default function ProtocolosPage() {
  const router = useRouter();
  const [items, setItems] = useState<Protocol[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/protocols?pending_only=true');
      if (!res.ok) throw new Error(`Lista falhou (${res.status})`);
      const json = await res.json();
      setItems(json.protocols || []);
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
        title: form.title.trim(),
        protocol_number: form.protocol_number.trim(),
        system: form.system,
      };
      if (form.court.trim()) payload.court = form.court.trim();
      if (form.notes.trim()) payload.notes = form.notes.trim();
      if (form.filed_at) payload.filed_at = new Date(form.filed_at).toISOString();
      const res = await apiFetch('/protocols', {
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

  async function markConfirmed(id: number) {
    setError('');
    try {
      const res = await apiFetch(`/protocols/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'confirmed' }),
      });
      if (!res.ok) throw new Error(`Confirmar falhou (${res.status})`);
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
              Protocolos
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Guarde o número da petição (PJe, e-SAJ, PROJUDI) antes de
              perder o comprovante na pasta do tribunal.
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
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Peça (ex.: Contestação, Agravo)"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <input
            required
            value={form.protocol_number}
            onChange={(e) =>
              setForm((f) => ({ ...f, protocol_number: e.target.value }))
            }
            placeholder="Número do protocolo"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-slate-400">
              Sistema
              <select
                value={form.system}
                onChange={(e) => setForm((f) => ({ ...f, system: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              >
                <option value="pje">PJe</option>
                <option value="esaj">e-SAJ</option>
                <option value="projudi">PROJUDI</option>
                <option value="tj">TJ / outro tribunal</option>
                <option value="outro">Outro</option>
              </select>
            </label>
            <label className="text-xs text-slate-400">
              Protocolado em
              <input
                type="datetime-local"
                value={form.filed_at}
                onChange={(e) => setForm((f) => ({ ...f, filed_at: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              />
            </label>
          </div>
          <input
            value={form.court}
            onChange={(e) => setForm((f) => ({ ...f, court: e.target.value }))}
            placeholder="Tribunal / vara (opcional)"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
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
          <p className="text-sm text-slate-400">Nenhum protocolo pendente.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div>
                  <p className="font-medium text-white">{item.title}</p>
                  <p className="mt-1 font-mono text-sm text-teal-300/90">
                    {item.protocol_number}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    {item.system.toUpperCase()}
                    {item.court ? ` · ${item.court}` : ''} · {fmt(item.filed_at)}
                  </p>
                  {item.notes ? (
                    <p className="mt-2 text-sm text-slate-300">{item.notes}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => void markConfirmed(item.id)}
                  className="text-xs text-teal-400 underline hover:text-teal-300"
                >
                  Confirmar
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
