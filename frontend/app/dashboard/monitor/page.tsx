'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface MonitoredProcess {
  id: number;
  process_number: string;
  court?: string | null;
  oab_number?: string | null;
  status: string;
  last_checked_at?: string | null;
  created_at?: string | null;
}

interface IntimacaoEvent {
  id: number;
  monitored_process_id: number;
  title: string;
  summary?: string | null;
  published_at?: string | null;
  source: string;
  raw_ref?: string | null;
  acknowledged: boolean;
  created_at?: string | null;
}

const EMPTY_FORM = {
  process_number: '',
  court: '',
  oab_number: '',
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

export default function MonitorPage() {
  const router = useRouter();
  const [processes, setProcesses] = useState<MonitoredProcess[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [events, setEvents] = useState<IntimacaoEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadProcesses = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/monitor/processes');
      const list: MonitoredProcess[] = data.processes || [];
      setProcesses(list);
      if (list.length && selectedId == null) {
        setSelectedId(list[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar processos');
    } finally {
      setLoading(false);
    }
  }, [router, selectedId]);

  const loadEvents = useCallback(async (processId: number) => {
    setError('');
    try {
      const data = await apiFetch(`/monitor/processes/${processId}/events`);
      setEvents(data.events || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar eventos');
    }
  }, []);

  useEffect(() => {
    loadProcesses();
  }, [loadProcesses]);

  useEffect(() => {
    if (selectedId != null) {
      loadEvents(selectedId);
    } else {
      setEvents([]);
    }
  }, [selectedId, loadEvents]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.process_number.trim()) {
      setError('Informe o número do processo');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const data = await apiFetch('/monitor/processes', {
        method: 'POST',
        body: JSON.stringify({
          process_number: form.process_number.trim(),
          court: form.court.trim() || null,
          oab_number: form.oab_number.trim() || null,
        }),
      });
      setForm(EMPTY_FORM);
      const created = data.process as MonitoredProcess;
      await loadProcesses();
      if (created?.id) setSelectedId(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao cadastrar processo');
    } finally {
      setSaving(false);
    }
  };

  const handlePollStub = async (id: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/monitor/processes/${id}/poll-stub`, { method: 'POST' });
      await loadProcesses();
      await loadEvents(id);
      setSelectedId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no poll stub');
    } finally {
      setSaving(false);
    }
  };

  const handleAck = async (eventId: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/monitor/events/${eventId}/ack`, { method: 'POST' });
      if (selectedId != null) await loadEvents(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao acusar recebimento');
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
          <p className="trust-kicker">DJEn / intimações · stub</p>
          <h1 className="trust-title mt-1">Monitor de processos</h1>
          <p className="trust-subtitle mt-2 max-w-xl">
            Cadastro e poll fictício de intimações. Sem scrape CNJ, sem API DJEn real.
          </p>
        </div>
        <Link href="/dashboard" className="trust-btn-ghost">
          ← Dashboard
        </Link>
      </div>

      <div className="mb-6 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
        Stub local: o botão &quot;Poll stub&quot; gera um evento fake claramente rotulado. Não consulta tribunal.
      </div>

      {error ? (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <form onSubmit={handleCreate} className="trust-card mb-8 grid gap-4 p-5 md:grid-cols-3">
        <div className="md:col-span-1">
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">
            Número do processo
          </label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.process_number}
            onChange={(e) => setForm((f) => ({ ...f, process_number: e.target.value }))}
            placeholder="0001234-56.2024.8.26.0100"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">Tribunal</label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.court}
            onChange={(e) => setForm((f) => ({ ...f, court: e.target.value }))}
            placeholder="TJSP"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">OAB</label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.oab_number}
            onChange={(e) => setForm((f) => ({ ...f, oab_number: e.target.value }))}
            placeholder="SP123456"
          />
        </div>
        <div className="md:col-span-3">
          <button type="submit" disabled={saving} className="trust-btn-primary">
            {saving ? 'Salvando…' : 'Monitorar processo'}
          </button>
        </div>
      </form>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-white/50">
            Processos ({processes.length})
          </h2>
          {processes.length === 0 ? (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Nenhum processo monitorado. Cadastre o primeiro acima.
            </div>
          ) : (
            <ul className="space-y-3">
              {processes.map((p) => (
                <li
                  key={p.id}
                  className={`trust-card cursor-pointer p-4 transition ${
                    selectedId === p.id ? 'ring-1 ring-teal-500/50' : ''
                  }`}
                  onClick={() => setSelectedId(p.id)}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-mono text-sm text-white">{p.process_number}</p>
                      <p className="mt-1 text-xs text-white/50">
                        {[p.court, p.oab_number, p.status].filter(Boolean).join(' · ')}
                      </p>
                      {p.last_checked_at ? (
                        <p className="mt-1 text-xs text-white/40">
                          Último poll: {new Date(p.last_checked_at).toLocaleString('pt-BR')}
                        </p>
                      ) : null}
                    </div>
                    <button
                      type="button"
                      disabled={saving}
                      className="rounded-lg border border-amber-500/40 bg-amber-500/15 px-3 py-1.5 text-xs text-amber-200 hover:bg-amber-500/25"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        handlePollStub(p.id);
                      }}
                    >
                      Poll stub
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-white/50">
            Eventos {selectedId != null ? `(processo #${selectedId})` : ''}
          </h2>
          {selectedId == null ? (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Selecione um processo.
            </div>
          ) : events.length === 0 ? (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Sem eventos. Use &quot;Poll stub&quot; para gerar uma intimação fake.
            </div>
          ) : (
            <ul className="space-y-3">
              {events.map((ev) => (
                <li key={ev.id} className="trust-card p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="text-sm text-white">{ev.title}</p>
                      <p className="mt-1 text-xs text-white/50">{ev.summary}</p>
                      <p className="mt-2 text-xs text-white/40">
                        source={ev.source}
                        {ev.raw_ref ? ` · ${ev.raw_ref}` : ''}
                        {ev.acknowledged ? ' · ack' : ' · pendente'}
                      </p>
                    </div>
                    {!ev.acknowledged ? (
                      <button
                        type="button"
                        disabled={saving}
                        className="trust-btn-ghost text-xs"
                        onClick={() => handleAck(ev.id)}
                      >
                        Ack
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
