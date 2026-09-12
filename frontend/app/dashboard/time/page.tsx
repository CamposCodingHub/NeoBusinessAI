'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface TimeEntry {
  id: number;
  description: string;
  minutes: number;
  hourly_rate?: number | null;
  billable: boolean;
  work_date?: string | null;
  invoiced_at?: string | null;
  created_at?: string | null;
  estimated_amount?: number | null;
}

interface TimeSummary {
  total_minutes: number;
  billable_minutes: number;
  billable_amount_estimate: number;
  total_hours: number;
  billable_hours: number;
  total_entries: number;
}

const EMPTY_FORM = {
  description: '',
  minutes: '60',
  hourly_rate: '350',
  billable: true,
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

function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}min`;
}

export default function TimeEntriesPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [summary, setSummary] = useState<TimeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [invoicing, setInvoicing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadData = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const [listData, summaryData] = await Promise.all([
        apiFetch('/time/entries?limit=100'),
        apiFetch('/time/summary'),
      ]);
      setEntries(listData.entries || []);
      setSummary(summaryData);
      setSelectedIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar horas');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const invoiceableIds = entries
    .filter((e) => e.billable && !e.invoiced_at && e.hourly_rate != null)
    .map((e) => e.id);

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAllInvoiceable = () => {
    if (
      invoiceableIds.length > 0 &&
      invoiceableIds.every((id) => selectedIds.includes(id))
    ) {
      setSelectedIds([]);
    } else {
      setSelectedIds(invoiceableIds);
    }
  };

  const handleInvoiceSelected = async () => {
    if (selectedIds.length === 0) {
      setError('Selecione ao menos um lançamento faturável');
      return;
    }
    setInvoicing(true);
    setError('');
    setSuccess('');
    try {
      const data = await apiFetch('/time/entries/invoice', {
        method: 'POST',
        body: JSON.stringify({ entry_ids: selectedIds }),
      });
      setSuccess(
        `Fatura ${data.invoice_number || data.invoice?.invoice_number} criada — ${formatCurrency(data.total ?? 0)}`
      );
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao faturar horas');
    } finally {
      setInvoicing(false);
    }
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.description.trim()) return;
    const minutes = parseInt(form.minutes, 10);
    if (!minutes || minutes <= 0) {
      setError('Informe minutos válidos');
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const rateRaw = form.hourly_rate.trim();
      const hourly_rate = rateRaw === '' ? null : parseFloat(rateRaw);
      await apiFetch('/time/entries', {
        method: 'POST',
        body: JSON.stringify({
          description: form.description.trim(),
          minutes,
          hourly_rate: Number.isFinite(hourly_rate as number) ? hourly_rate : null,
          billable: form.billable,
        }),
      });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao lançar horas');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    setError('');
    setSuccess('');
    try {
      await apiFetch(`/time/entries/${id}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao remover lançamento');
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
            <p className="trust-kicker">PMS · horas faturáveis</p>
            <h1 className="trust-title mt-1">Time Entries</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Lance minutos trabalhados, taxa horária e acompanhe a estimativa
              faturável — MVP pragmático para o escritório.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="trust-btn-ghost">
              ← Dashboard
            </Link>
            <button
              type="button"
              className="trust-btn-ghost"
              disabled={selectedIds.length === 0 || invoicing}
              onClick={handleInvoiceSelected}
            >
              {invoicing ? 'Faturando…' : 'Faturar selecionados'}
            </button>
            <button
              type="button"
              className="trust-btn-primary"
              onClick={() => setShowForm((v) => !v)}
            >
              {showForm ? 'Fechar formulário' : '+ Lançar horas'}
            </button>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-xl border border-[#0F766E]/25 bg-[#0F766E]/08 px-4 py-3 text-sm text-[#0F766E]">
            {success}
          </div>
        )}

        {summary && (
          <div className="mb-8 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-[#e2e8f0] bg-white px-4 py-3">
              <p className="text-xs font-medium uppercase tracking-wide text-[#64748b]">
                Total
              </p>
              <p className="mt-1 text-2xl font-semibold text-[#0C1B2A]">
                {formatMinutes(summary.total_minutes)}
              </p>
            </div>
            <div className="rounded-xl border border-[#e2e8f0] bg-white px-4 py-3">
              <p className="text-xs font-medium uppercase tracking-wide text-[#64748b]">
                Faturável
              </p>
              <p className="mt-1 text-2xl font-semibold text-[#0F766E]">
                {formatMinutes(summary.billable_minutes)}
              </p>
            </div>
            <div className="rounded-xl border border-[#e2e8f0] bg-white px-4 py-3">
              <p className="text-xs font-medium uppercase tracking-wide text-[#64748b]">
                Estimativa
              </p>
              <p className="mt-1 text-2xl font-semibold text-[#0C1B2A]">
                {formatCurrency(summary.billable_amount_estimate || 0)}
              </p>
            </div>
          </div>
        )}

        {showForm && (
          <form
            onSubmit={handleCreate}
            className="mb-8 rounded-xl border border-[#e2e8f0] bg-white p-5 shadow-sm"
          >
            <h2 className="mb-4 text-lg font-semibold text-[#0C1B2A]">
              Novo lançamento
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block sm:col-span-2">
                <span className="mb-1 block text-sm font-medium text-[#475569]">
                  Descrição
                </span>
                <input
                  required
                  value={form.description}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, description: e.target.value }))
                  }
                  className="w-full rounded-lg border border-[#e2e8f0] px-3 py-2 text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                  placeholder="Ex.: Análise de petição inicial"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-[#475569]">
                  Minutos
                </span>
                <input
                  required
                  type="number"
                  min={1}
                  max={1440}
                  value={form.minutes}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, minutes: e.target.value }))
                  }
                  className="w-full rounded-lg border border-[#e2e8f0] px-3 py-2 text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-[#475569]">
                  Taxa horária (R$)
                </span>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={form.hourly_rate}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, hourly_rate: e.target.value }))
                  }
                  className="w-full rounded-lg border border-[#e2e8f0] px-3 py-2 text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                  placeholder="350"
                />
              </label>
              <label className="flex items-center gap-2 sm:col-span-2">
                <input
                  type="checkbox"
                  checked={form.billable}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, billable: e.target.checked }))
                  }
                  className="h-4 w-4 rounded border-[#cbd5e1] text-[#0F766E]"
                />
                <span className="text-sm text-[#475569]">Faturável</span>
              </label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="trust-btn-ghost"
                onClick={() => setShowForm(false)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="trust-btn-primary"
                disabled={saving}
              >
                {saving ? 'Salvando…' : 'Salvar lançamento'}
              </button>
            </div>
          </form>
        )}

        <section className="rounded-xl border border-[#e2e8f0] bg-white">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e2e8f0] px-5 py-3">
            <h2 className="text-base font-semibold text-[#0C1B2A]">
              Lançamentos ({entries.length})
            </h2>
            {invoiceableIds.length > 0 && (
              <button
                type="button"
                className="text-sm text-[#0F766E] hover:underline"
                onClick={toggleSelectAllInvoiceable}
              >
                {invoiceableIds.every((id) => selectedIds.includes(id))
                  ? 'Limpar seleção'
                  : 'Selecionar faturáveis'}
              </button>
            )}
          </div>
          {entries.length === 0 ? (
            <div className="px-5 py-10 text-center text-sm text-[#64748b]">
              Nenhum lançamento ainda. Use “+ Lançar horas” para começar.
            </div>
          ) : (
            <ul className="divide-y divide-[#f1f5f9]">
              {entries.map((entry) => {
                const canInvoice =
                  entry.billable && !entry.invoiced_at && entry.hourly_rate != null;
                return (
                  <li
                    key={entry.id}
                    className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
                  >
                    <div className="flex min-w-0 flex-1 items-start gap-3">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-[#cbd5e1] text-[#0F766E]"
                        disabled={!canInvoice}
                        checked={selectedIds.includes(entry.id)}
                        onChange={() => toggleSelect(entry.id)}
                        aria-label={`Selecionar ${entry.description}`}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-[#0C1B2A]">
                          {entry.description}
                        </p>
                        <p className="mt-0.5 text-sm text-[#64748b]">
                          {formatMinutes(entry.minutes)}
                          {entry.hourly_rate != null
                            ? ` · ${formatCurrency(entry.hourly_rate)}/h`
                            : ''}
                          {entry.work_date
                            ? ` · ${new Date(entry.work_date + 'T12:00:00').toLocaleDateString('pt-BR')}`
                            : ''}
                          {entry.invoiced_at ? (
                            <span className="ml-2 text-[#64748b]">faturado</span>
                          ) : entry.billable ? (
                            <span className="ml-2 text-[#0F766E]">faturável</span>
                          ) : (
                            <span className="ml-2 text-[#94a3b8]">
                              não faturável
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-[#0C1B2A]">
                        {entry.estimated_amount != null
                          ? formatCurrency(entry.estimated_amount)
                          : '—'}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDelete(entry.id)}
                        className="rounded-lg px-2 py-1 text-sm text-[#b91c1c] hover:bg-[#b91c1c]/08"
                      >
                        Remover
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
