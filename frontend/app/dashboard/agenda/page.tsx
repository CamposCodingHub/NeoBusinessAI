'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch, API_BASE_URL } from '@/lib/api';

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

interface PrepItem {
  id: number;
  title: string;
  status: string;
  hearing_id: number;
}

interface WitnessItem {
  id: number;
  name: string;
  phone?: string | null;
  role: string;
  status: string;
  hearing_id: number;
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
  const [prepByHearing, setPrepByHearing] = useState<Record<number, PrepItem[]>>({});
  const [openPrep, setOpenPrep] = useState<number | null>(null);
  const [witnessByHearing, setWitnessByHearing] = useState<Record<number, WitnessItem[]>>({});
  const [openWitness, setOpenWitness] = useState<number | null>(null);
  const [witnessName, setWitnessName] = useState('');
  const [witnessPhone, setWitnessPhone] = useState('');

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

  const loadPrep = async (hearingId: number) => {
    setError('');
    try {
      const data = await apiFetch(`/agenda/hearings/${hearingId}/prep`);
      setPrepByHearing((prev) => ({ ...prev, [hearingId]: data.items || [] }));
      setOpenPrep(hearingId);
      setOpenWitness(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar prep');
    }
  };

  const seedPrep = async (hearingId: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/agenda/hearings/${hearingId}/prep/seed`, { method: 'POST' });
      await loadPrep(hearingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar checklist');
    } finally {
      setSaving(false);
    }
  };

  const markPrepDone = async (hearingId: number, itemId: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/agenda/prep/${itemId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'done' }),
      });
      await loadPrep(hearingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar prep');
    } finally {
      setSaving(false);
    }
  };

  const loadWitnesses = async (hearingId: number) => {
    setError('');
    try {
      const data = await apiFetch(`/agenda/hearings/${hearingId}/witnesses`);
      setWitnessByHearing((prev) => ({ ...prev, [hearingId]: data.witnesses || [] }));
      setOpenWitness(hearingId);
      setOpenPrep(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar testemunhas');
    }
  };

  const addWitness = async (hearingId: number) => {
    if (!witnessName.trim()) return;
    setSaving(true);
    setError('');
    try {
      const payload: Record<string, string> = { name: witnessName.trim() };
      if (witnessPhone.trim()) payload.phone = witnessPhone.trim();
      await apiFetch(`/agenda/hearings/${hearingId}/witnesses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      setWitnessName('');
      setWitnessPhone('');
      await loadWitnesses(hearingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao adicionar testemunha');
    } finally {
      setSaving(false);
    }
  };

  const confirmWitness = async (hearingId: number, witnessId: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/agenda/witnesses/${witnessId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'confirmed' }),
      });
      await loadWitnesses(hearingId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao confirmar testemunha');
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


  const downloadIcs = async () => {
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/agenda/calendar.ics`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`ICS falhou (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'lexscan-agenda.ics';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao exportar ICS');
    }
  };


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

            <div className="mb-4 flex justify-end">
        <button
          type="button"
          onClick={() => void downloadIcs()}
          className="rounded-lg border border-teal-500/40 bg-teal-500/10 px-3 py-1.5 text-xs text-teal-200 hover:bg-teal-500/20"
        >
          Exportar ICS
        </button>
      </div>
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
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void loadPrep(h.id)}
                  className="rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-500/20"
                >
                  Prep
                </button>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => void loadWitnesses(h.id)}
                  className="rounded-lg border border-violet-500/40 bg-violet-500/10 px-3 py-1.5 text-xs text-violet-200 hover:bg-violet-500/20"
                >
                  Testemunhas
                </button>
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
              {openPrep === h.id ? (
                <div className="mt-3 w-full border-t border-white/10 pt-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <p className="text-xs uppercase tracking-wide text-white/50">
                      Checklist de preparação
                    </p>
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void seedPrep(h.id)}
                      className="text-xs text-[#5EEAD4] underline hover:text-teal-200"
                    >
                      Seed padrão
                    </button>
                  </div>
                  {(prepByHearing[h.id] || []).length === 0 ? (
                    <p className="text-xs text-white/40">
                      Nenhum item — use “Seed padrão”.
                    </p>
                  ) : (
                    <ul className="space-y-1">
                      {(prepByHearing[h.id] || []).map((item) => (
                        <li
                          key={item.id}
                          className="flex items-center justify-between gap-2 text-sm text-white/80"
                        >
                          <span>
                            {item.title}{' '}
                            <span className="text-xs text-white/40">({item.status})</span>
                          </span>
                          {item.status === 'pending' ? (
                            <button
                              type="button"
                              disabled={saving}
                              onClick={() => void markPrepDone(h.id, item.id)}
                              className="text-xs text-emerald-300 underline"
                            >
                              Feito
                            </button>
                          ) : null}

              {openWitness === h.id ? (
                <div className="mt-3 w-full border-t border-white/10 pt-3">
                  <p className="mb-2 text-xs uppercase tracking-wide text-white/50">
                    Testemunhas
                  </p>
                  <div className="mb-3 flex flex-wrap gap-2">
                    <input
                      value={witnessName}
                      onChange={(e) => setWitnessName(e.target.value)}
                      placeholder="Nome"
                      className="min-w-[10rem] flex-1 rounded-lg border border-white/15 bg-black/30 px-2 py-1.5 text-sm"
                    />
                    <input
                      value={witnessPhone}
                      onChange={(e) => setWitnessPhone(e.target.value)}
                      placeholder="Telefone"
                      className="w-36 rounded-lg border border-white/15 bg-black/30 px-2 py-1.5 text-sm"
                    />
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void addWitness(h.id)}
                      className="rounded-lg bg-teal-600 px-3 py-1.5 text-xs text-white hover:bg-teal-500"
                    >
                      Adicionar
                    </button>
                  </div>
                  {(witnessByHearing[h.id] || []).length === 0 ? (
                    <p className="text-xs text-white/40">Nenhuma testemunha ainda.</p>
                  ) : (
                    <ul className="space-y-1">
                      {(witnessByHearing[h.id] || []).map((w) => (
                        <li
                          key={w.id}
                          className="flex items-center justify-between gap-2 text-sm text-white/80"
                        >
                          <span>
                            {w.name}
                            {w.phone ? (
                              <span className="text-white/45"> · {w.phone}</span>
                            ) : null}{' '}
                            <span className="text-xs text-white/40">({w.status})</span>
                          </span>
                          {w.status === 'pending' ? (
                            <button
                              type="button"
                              disabled={saving}
                              onClick={() => void confirmWitness(h.id, w.id)}
                              className="text-xs text-emerald-300 underline"
                            >
                              Confirmar
                            </button>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : null}

                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
