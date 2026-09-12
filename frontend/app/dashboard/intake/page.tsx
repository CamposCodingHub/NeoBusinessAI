'use client';

import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type LeadStatus = 'new' | 'qualified' | 'meeting' | 'won' | 'lost';

interface Lead {
  id: number;
  name: string;
  email?: string | null;
  phone?: string | null;
  practice_area?: string | null;
  source?: string | null;
  status: LeadStatus;
  notes?: string | null;
  conflict_flag: boolean;
  created_at?: string | null;
}

const COLUMNS: { id: LeadStatus; label: string }[] = [
  { id: 'new', label: 'Novo' },
  { id: 'qualified', label: 'Qualificado' },
  { id: 'meeting', label: 'Reunião' },
  { id: 'won', label: 'Ganho' },
  { id: 'lost', label: 'Perdido' },
];

const EMPTY_FORM = {
  name: '',
  email: '',
  phone: '',
  practice_area: '',
  source: 'manual',
  notes: '',
  conflict_flag: false,
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

export default function IntakePage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadLeads = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/intake/leads?limit=200');
      setLeads(data.leads || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar leads');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const byStatus = useMemo(() => {
    const map: Record<LeadStatus, Lead[]> = {
      new: [],
      qualified: [],
      meeting: [],
      won: [],
      lost: [],
    };
    for (const lead of leads) {
      const key = (COLUMNS.find((c) => c.id === lead.status)?.id || 'new') as LeadStatus;
      map[key].push(lead);
    }
    return map;
  }, [leads]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    setError('');
    try {
      await apiFetch('/intake/leads', {
        method: 'POST',
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim() || null,
          phone: form.phone.trim() || null,
          practice_area: form.practice_area.trim() || null,
          source: form.source.trim() || 'manual',
          notes: form.notes.trim() || null,
          conflict_flag: form.conflict_flag,
        }),
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await loadLeads();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar lead');
    } finally {
      setSaving(false);
    }
  };

  const moveLead = async (lead: Lead, status: LeadStatus) => {
    if (lead.status === status) return;
    setError('');
    try {
      await apiFetch(`/intake/leads/${lead.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      setLeads((prev) =>
        prev.map((item) => (item.id === lead.id ? { ...item, status } : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar status');
    }
  };

  const convertLead = async (lead: Lead) => {
    if (lead.conflict_flag) {
      setError('Remova o flag de conflito antes de converter.');
      return;
    }
    if (!confirm(`Converter "${lead.name}" em cliente?`)) return;
    setError('');
    try {
      await apiFetch(`/intake/leads/${lead.id}/convert`, { method: 'POST' });
      await loadLeads();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao converter lead');
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
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker">Captação comercial</p>
            <h1 className="trust-title mt-1">Intake / Leads</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Pipeline profissional: qualifique, agende e converta leads em clientes —
              com flag de conflito de interesse.
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
              {showForm ? 'Fechar formulário' : '+ Novo lead'}
            </button>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        {showForm && (
          <form onSubmit={handleCreate} className="trust-card mb-8 grid gap-4 p-5 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Nome *
              </label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="Nome do lead"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                E-mail
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="contato@exemplo.com"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Telefone
              </label>
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="(11) 99999-0000"
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
                placeholder="Trabalhista, Família…"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Fonte
              </label>
              <input
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                placeholder="site, indicação, WhatsApp…"
              />
            </div>
            <div className="flex items-end gap-3 pb-1">
              <label className="flex items-center gap-2 text-sm text-[#334155]">
                <input
                  type="checkbox"
                  checked={form.conflict_flag}
                  onChange={(e) => setForm({ ...form, conflict_flag: e.target.checked })}
                  className="rounded border-[#d7dde5] text-[#0F766E]"
                />
                Possível conflito de interesse
              </label>
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
                placeholder="Resumo do contato inicial…"
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <button type="submit" disabled={saving} className="trust-btn-primary">
                {saving ? 'Salvando…' : 'Criar lead'}
              </button>
            </div>
          </form>
        )}

        <div className="grid gap-4 overflow-x-auto pb-4 lg:grid-cols-5">
          {COLUMNS.map((col) => (
            <section key={col.id} className="trust-card min-w-[220px] p-3">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="trust-section-title">{col.label}</h2>
                <span className="rounded-md bg-[#0F766E]/10 px-2 py-0.5 text-xs font-semibold text-[#0F766E]">
                  {byStatus[col.id].length}
                </span>
              </div>
              <div className="space-y-3">
                {byStatus[col.id].length === 0 && (
                  <p className="px-1 py-6 text-center text-xs text-[#94a3b8]">Nenhum lead</p>
                )}
                {byStatus[col.id].map((lead) => (
                  <article
                    key={lead.id}
                    className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-semibold text-[#0C1B2A]">{lead.name}</h3>
                      {lead.conflict_flag && (
                        <span className="shrink-0 rounded bg-[#b91c1c]/10 px-1.5 py-0.5 text-[10px] font-bold uppercase text-[#b91c1c]">
                          Conflito
                        </span>
                      )}
                    </div>
                    {lead.practice_area && (
                      <p className="mt-1 text-xs text-[#64748b]">{lead.practice_area}</p>
                    )}
                    {(lead.email || lead.phone) && (
                      <p className="mt-1 truncate text-xs text-[#475569]">
                        {lead.email || lead.phone}
                      </p>
                    )}
                    {lead.source && (
                      <p className="mt-1 text-[11px] uppercase tracking-wide text-[#94a3b8]">
                        {lead.source}
                      </p>
                    )}

                    <div className="mt-3 flex flex-wrap gap-1">
                      {COLUMNS.filter((c) => c.id !== lead.status).map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => moveLead(lead, c.id)}
                          className="rounded border border-[#e2e8f0] bg-white px-1.5 py-0.5 text-[10px] text-[#475569] hover:border-[#0F766E] hover:text-[#0F766E]"
                        >
                          → {c.label}
                        </button>
                      ))}
                    </div>

                    {lead.status !== 'won' && lead.status !== 'lost' && (
                      <button
                        type="button"
                        onClick={() => convertLead(lead)}
                        className="mt-3 w-full rounded-lg bg-[#0F766E] px-2 py-1.5 text-xs font-semibold text-white hover:bg-[#115e59]"
                      >
                        Converter em cliente
                      </button>
                    )}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
