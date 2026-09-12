'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface Hearing {
  id: number;
  title: string;
  location?: string | null;
  hearing_at: string;
  status: string;
  notes?: string | null;
  client_id?: number | null;
  matter_id?: number | null;
  created_at?: string | null;
}

const EMPTY_FORM = {
  title: '',
  location: '',
  hearing_at: '',
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
    case 'done':
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    case 'cancelled':
      return 'bg-red-500/20 text-red-300 border-red-500/40';
    default:
      return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
  }
}

function formatWhen(iso: string): string {
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default function AgendaPage() {
  const router = useRouter();
  const [hearings, setHearings] = useState<Hearing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadHearings = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/agenda/hearings');
      setHearings(data.hearings || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar agenda');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadHearings();
  }, [loadHearings]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.hearing_at) {
      setError('Informe título e data/hora');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiFetch('/agenda/hearings', {
        method: 'POST',
        body: JSON.stringify({
          title: form.title.trim(),
          hearing_at: new Date(form.hearing_at).toISOString(),
          location: form.location.trim() || null,
          notes: form.notes.trim() || null,
        }),
      });
      setForm(EMPTY_FORM);
      await loadHearings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar compromisso');
    } finally {
      setSaving(false);
    }
  };

  const patchStatus = async (id: number, status: string) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/agenda/hearings/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      await loadHearings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="trust-shell flex min-h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#0F766E] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="trust-shell px-4 py-8 sm:px-8">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="trust-kicker">Operações · audiências</p>
          <h1 className="trust-title mt-1">Agenda</h1>
          <p className="trust-subtitle mt-2 max-w-xl">
            Audiências e compromissos do dia a dia. Stub local — sem sync de calendário externo.
          </p>
        </div>
        <Link href="/dashboard" className="trust-btn-ghost">
          ← Dashboard
        </Link>
      </div>

      {error ? (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleCreate} className="trust-card mb-8 grid gap-4 p-5 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">
            Título
          </label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Audiência de instrução"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">
            Data e hora
          </label>
          <input
            type="datetime-local"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.hearing_at}
            onChange={(e) => setForm((f) => ({ ...f, hearing_at: e.target.value }))}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">
            Local
          </label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.location}
            onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            placeholder="Fórum / Zoom / escritório"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">
            Notas
          </label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            placeholder="Opcional"
          />
        </div>
        <div className="md:col-span-2">
          <button type="submit" disabled={saving} className="trust-btn-primary">
            {saving ? 'Salvando…' : 'Adicionar compromisso'}
          </button>
        </div>
      </form>

      <div className="space-y-3">
        {hearings.length === 0 ? (
          <p className="text-sm text-white/50">Nenhum compromisso ainda.</p>
        ) : (
          hearings.map((h) => (
            <div
              key={h.id}
              className="trust-card flex flex-wrap items-start justify-between gap-3 p-4"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-medium text-white">{h.title}</h2>
                  <span
                    className={`rounded border px-2 py-0.5 text-xs uppercase tracking-wide ${statusBadge(h.status)}`}
                  >
                    {h.status}
                  </span>
                </div>
                <p className="mt-1 text-sm text-white/60">{formatWhen(h.hearing_at)}</p>
                {h.location ? (
                  <p className="mt-0.5 text-sm text-white/45">{h.location}</p>
                ) : null}
                {h.notes ? (
                  <p className="mt-1 text-xs text-white/40">{h.notes}</p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                {h.status !== 'done' ? (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => patchStatus(h.id, 'done')}
                    className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-500/20"
                  >
                    Concluir
                  </button>
                ) : null}
                {h.status !== 'cancelled' ? (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => patchStatus(h.id, 'cancelled')}
                    className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs text-red-200 hover:bg-red-500/20"
                  >
                    Cancelar
                  </button>
                ) : null}
                {h.status !== 'scheduled' ? (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => patchStatus(h.id, 'scheduled')}
                    className="rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-xs text-white/70 hover:bg-white/10"
                  >
                    Reabrir
                  </button>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
