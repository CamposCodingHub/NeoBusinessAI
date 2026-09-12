'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface DocItem {
  id: number;
  title: string;
  status: string;
  notes?: string | null;
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

export default function DocsCasoPage() {
  const router = useRouter();
  const [items, setItems] = useState<DocItem[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/matter-docs');
      if (!res.ok) throw new Error(`Lista falhou (${res.status})`);
      const json = await res.json();
      setItems(json.items || []);
      setPendingCount(json.pending_count || 0);
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
      const res = await apiFetch('/matter-docs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim() }),
      });
      if (!res.ok) throw new Error(`Criar falhou (${res.status})`);
      setTitle('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
    }
  }

  async function seedIntake() {
    setError('');
    try {
      const res = await apiFetch('/matter-docs/seed-intake', { method: 'POST' });
      if (!res.ok) throw new Error(`Seed falhou (${res.status})`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
    }
  }

  async function setStatus(id: number, status: string) {
    setError('');
    try {
      const res = await apiFetch(`/matter-docs/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(`Atualizar falhou (${res.status})`);
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
              Docs do caso
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Checklist do que ainda falta do cliente — {pendingCount} pendente(s).
              Não é repositório de arquivos.
            </p>
          </div>
          <Link href="/dashboard" className="text-sm text-teal-400 hover:text-teal-300">
            ← Dashboard
          </Link>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void seedIntake()}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:border-teal-500/50"
          >
            Seed intake básico
          </button>
        </div>

        <form
          onSubmit={onSubmit}
          className="mb-8 flex flex-wrap gap-3 rounded-xl border border-slate-700/60 bg-slate-900/50 p-5"
        >
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Documento faltante (ex.: comprovante de endereço)"
            className="min-w-[220px] flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
          >
            Adicionar
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
          <p className="text-sm text-slate-400">Nenhum item no checklist.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div>
                  <p className="font-medium text-white">{item.title}</p>
                  <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">
                    {item.status}
                  </p>
                  {item.notes ? (
                    <p className="mt-2 text-sm text-slate-300">{item.notes}</p>
                  ) : null}
                </div>
                {item.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => void setStatus(item.id, 'received')}
                      className="text-xs text-teal-400 underline hover:text-teal-300"
                    >
                      Recebido
                    </button>
                    <button
                      type="button"
                      onClick={() => void setStatus(item.id, 'waived')}
                      className="text-xs text-slate-400 underline hover:text-slate-200"
                    >
                      Dispensar
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
