'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface MatterNote {
  id: number;
  body: string;
  pinned: boolean;
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

function fmt(iso?: string | null): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default function AnotacoesPage() {
  const router = useRouter();
  const [notes, setNotes] = useState<MatterNote[]>([]);
  const [body, setBody] = useState('');
  const [pinned, setPinned] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/matter-notes');
      if (!res.ok) throw new Error(`Lista falhou (${res.status})`);
      const json = await res.json();
      setNotes(json.notes || []);
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
      const res = await apiFetch('/matter-notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: body.trim(), pinned }),
      });
      if (!res.ok) throw new Error(`Salvar falhou (${res.status})`);
      setBody('');
      setPinned(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
    }
  }

  async function togglePin(note: MatterNote) {
    setError('');
    try {
      const res = await apiFetch(`/matter-notes/${note.id}/pin`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pinned: !note.pinned }),
      });
      if (!res.ok) throw new Error(`Fixar falhou (${res.status})`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro');
    }
  }

  async function remove(id: number) {
    setError('');
    try {
      const res = await apiFetch(`/matter-notes/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Excluir falhou (${res.status})`);
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
              Anotações
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Contexto interno do caso — o que foi combinado, sem misturar com
              petição ou parecer.
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
          <textarea
            required
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Anote o combinado com o cliente ou a equipe…"
            rows={3}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={pinned}
              onChange={(e) => setPinned(e.target.checked)}
            />
            Fixar no topo
          </label>
          <button
            type="submit"
            className="justify-self-start rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500"
          >
            Salvar
          </button>
        </form>

        {error && (
          <p className="mb-4 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-slate-400">Carregando…</p>
        ) : notes.length === 0 ? (
          <p className="text-sm text-slate-400">Nenhuma anotação ainda.</p>
        ) : (
          <ul className="space-y-3">
            {notes.map((note) => (
              <li
                key={note.id}
                className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-4"
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs text-slate-500">
                    {fmt(note.created_at)}
                    {note.pinned ? ' · fixada' : ''}
                  </p>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => void togglePin(note)}
                      className="text-xs text-teal-400 underline hover:text-teal-300"
                    >
                      {note.pinned ? 'Desafixar' : 'Fixar'}
                    </button>
                    <button
                      type="button"
                      onClick={() => void remove(note.id)}
                      className="text-xs text-slate-400 underline hover:text-red-300"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
                <p className="whitespace-pre-wrap text-sm text-slate-200">{note.body}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
