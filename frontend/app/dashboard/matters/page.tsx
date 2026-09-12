'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type MatterStatus = 'open' | 'pending' | 'closed';

interface Matter {
  id: number;
  title: string;
  client_id?: number | null;
  practice_area?: string | null;
  status: MatterStatus;
  opposing_party?: string | null;
  court?: string | null;
  process_number?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

const STATUS_META: { id: MatterStatus; label: string }[] = [
  { id: 'open', label: 'Aberto' },
  { id: 'pending', label: 'Pendente' },
  { id: 'closed', label: 'Encerrado' },
];

const EMPTY_FORM = {
  title: '',
  practice_area: '',
  opposing_party: '',
  court: '',
  process_number: '',
  notes: '',
  status: 'open' as MatterStatus,
  organization_id: '',
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

function statusBadgeClass(status: MatterStatus): string {
  if (status === 'open') return 'bg-[#0F766E]/10 text-[#0F766E]';
  if (status === 'pending') return 'bg-[#b45309]/10 text-[#b45309]';
  return 'bg-[#64748b]/15 text-[#475569]';
}

export default function MattersPage() {
  const router = useRouter();
  const [matters, setMatters] = useState<Matter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [filter, setFilter] = useState<MatterStatus | 'all'>('all');

  const loadMatters = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/matters?limit=200');
      setMatters(data.matters || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar casos');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadMatters();
  }, [loadMatters]);

  const visible = useMemo(() => {
    if (filter === 'all') return matters;
    return matters.filter((m) => m.status === filter);
  }, [matters, filter]);

  const counts = useMemo(() => {
    return {
      open: matters.filter((m) => m.status === 'open').length,
      pending: matters.filter((m) => m.status === 'pending').length,
      closed: matters.filter((m) => m.status === 'closed').length,
    };
  }, [matters]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    setError('');
    try {
      await apiFetch('/matters', {
        method: 'POST',
        body: JSON.stringify({
          title: form.title.trim(),
          practice_area: form.practice_area.trim() || null,
          opposing_party: form.opposing_party.trim() || null,
          court: form.court.trim() || null,
          process_number: form.process_number.trim() || null,
          notes: form.notes.trim() || null,
          status: form.status,
          ...(form.organization_id.trim()
            ? { organization_id: Number(form.organization_id.trim()) }
            : {}),
        }),
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await loadMatters();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar caso');
    } finally {
      setSaving(false);
    }
  };

  const setStatus = async (matter: Matter, status: MatterStatus) => {
    if (matter.status === status) return;
    setError('');
    try {
      await apiFetch(`/matters/${matter.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setMatters((prev) =>
        prev.map((item) => (item.id === matter.id ? { ...item, status } : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status');
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
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker">Ciclo de vida unificado</p>
            <h1 className="trust-title mt-1">Casos / Matters</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Centralize título, área, partes, foro e andamento — open, pending ou closed —
              num único registro operacional.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="trust-btn-ghost">
              ← Dashboard
            </Link>
            <button
              type="button"
              className="trust-btn-primary"
              onClick={() => setShowForm((v) => !v)}
            >
              {showForm ? 'Fechar formulário' : '+ Novo caso'}
            </button>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        <div className="mb-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
              filter === 'all'
                ? 'bg-[#0C1B2A] text-white'
                : 'bg-white text-[#475569] border border-[#e2e8f0]'
            }`}
          >
            Todos ({matters.length})
          </button>
          {STATUS_META.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setFilter(s.id)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                filter === s.id
                  ? 'bg-[#0C1B2A] text-white'
                  : 'bg-white text-[#475569] border border-[#e2e8f0]'
              }`}
            >
              {s.label} ({counts[s.id]})
            </button>
          ))}
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="trust-card mb-8 grid gap-4 p-5 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Título *
              </label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="Ex.: Ação de cobrança — Silva vs. XYZ"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Área de prática
              </label>
              <input
                value={form.practice_area}
                onChange={(e) => setForm({ ...form, practice_area: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="Trabalhista, Cível…"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Status
              </label>
              <select
                value={form.status}
                onChange={(e) =>
                  setForm({ ...form, status: e.target.value as MatterStatus })
                }
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              >
                {STATUS_META.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Parte contrária
              </label>
              <input
                value={form.opposing_party}
                onChange={(e) => setForm({ ...form, opposing_party: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="Réu / autor adverso"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Foro / Tribunal
              </label>
              <input
                value={form.court}
                onChange={(e) => setForm({ ...form, court: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="TRT-2, TJSP…"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Nº do processo
              </label>
              <input
                value={form.process_number}
                onChange={(e) => setForm({ ...form, process_number: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="0000000-00.0000.0.00.0000"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Org ID (opcional)
              </label>
              <input
                type="number"
                min="1"
                value={form.organization_id}
                onChange={(e) => setForm({ ...form, organization_id: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="ID da organização"
              />
            </div>
            <div className="md:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Notas
              </label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={3}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="Andamentos, próximos passos…"
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <button type="submit" disabled={saving} className="trust-btn-primary">
                {saving ? 'Salvando…' : 'Criar caso'}
              </button>
            </div>
          </form>
        )}

        <div className="space-y-3">
          {visible.length === 0 && (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Nenhum caso neste filtro. Crie o primeiro para unificar o ciclo de vida.
            </div>
          )}
          {visible.map((matter) => (
            <article key={matter.id} className="trust-card p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-base font-semibold text-[#0C1B2A]">{matter.title}</h2>
                    <span
                      className={`rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase ${statusBadgeClass(matter.status)}`}
                    >
                      {STATUS_META.find((s) => s.id === matter.status)?.label || matter.status}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#64748b]">
                    {matter.practice_area && <span>{matter.practice_area}</span>}
                    {matter.process_number && <span>Proc. {matter.process_number}</span>}
                    {matter.court && <span>{matter.court}</span>}
                    {matter.opposing_party && <span>vs. {matter.opposing_party}</span>}
                  </div>
                  {matter.notes && (
                    <p className="mt-2 line-clamp-2 text-sm text-[#475569]">{matter.notes}</p>
                  )}
                </div>
                <div className="flex flex-wrap gap-1">
                  {STATUS_META.filter((s) => s.id !== matter.status).map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStatus(matter, s.id)}
                      className="rounded border border-[#e2e8f0] bg-white px-2 py-1 text-[11px] text-[#475569] hover:border-[#0F766E] hover:text-[#0F766E]"
                    >
                      → {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
