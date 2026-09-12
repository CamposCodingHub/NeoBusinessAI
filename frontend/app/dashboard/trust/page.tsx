'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface TrustAccount {
  id: number;
  name: string;
  currency: string;
  organization_id?: number | null;
  balance?: number;
  created_at?: string | null;
}

interface TrustEntry {
  id: number;
  entry_type: string;
  amount: number;
  memo?: string | null;
  client_id?: number | null;
  matter_id?: number | null;
  created_at?: string | null;
}

interface ReconcileSummary {
  book_balance: number;
  client_subtotals: { client_id: number; balance: number }[];
  unallocated_balance: number;
  as_of?: string;
  note?: string;
}

const EMPTY_ACCOUNT = { name: '', currency: 'BRL' };
const EMPTY_ENTRY = {
  entry_type: 'deposit' as 'deposit' | 'withdrawal' | 'transfer' | 'adjustment',
  amount: '',
  memo: '',
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

function formatMoney(value: number, currency = 'BRL'): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency });
}

export default function TrustAccountingPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<TrustAccount[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [entries, setEntries] = useState<TrustEntry[]>([]);
  const [balance, setBalance] = useState<number | null>(null);
  const [reconcile, setReconcile] = useState<ReconcileSummary | null>(null);
  const [reconcileLoading, setReconcileLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [accountForm, setAccountForm] = useState(EMPTY_ACCOUNT);
  const [entryForm, setEntryForm] = useState(EMPTY_ENTRY);

  const loadAccounts = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/trust/accounts');
      const list: TrustAccount[] = data.accounts || [];
      setAccounts(list);
      if (list.length && selectedId == null) {
        setSelectedId(list[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar contas trust');
    } finally {
      setLoading(false);
    }
  }, [router, selectedId]);

  const loadLedger = useCallback(async (accountId: number) => {
    setError('');
    try {
      const data = await apiFetch(`/trust/accounts/${accountId}/ledger`);
      setEntries(data.entries || []);
      setBalance(typeof data.balance === 'number' ? data.balance : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar ledger');
    }
  }, []);

  const loadReconcile = useCallback(async (accountId: number) => {
    setReconcileLoading(true);
    setError('');
    try {
      const data = await apiFetch(`/trust/accounts/${accountId}/reconcile`);
      setReconcile({
        book_balance: Number(data.book_balance ?? 0),
        client_subtotals: Array.isArray(data.client_subtotals) ? data.client_subtotals : [],
        unallocated_balance: Number(data.unallocated_balance ?? 0),
        as_of: data.as_of,
        note: data.note,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar reconciliação');
      setReconcile(null);
    } finally {
      setReconcileLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    if (selectedId != null) {
      loadLedger(selectedId);
      setReconcile(null);
    } else {
      setEntries([]);
      setBalance(null);
      setReconcile(null);
    }
  }, [selectedId, loadLedger]);

  const handleCreateAccount = async (e: FormEvent) => {
    e.preventDefault();
    if (!accountForm.name.trim()) return;
    setSaving(true);
    setError('');
    try {
      const created = await apiFetch('/trust/accounts', {
        method: 'POST',
        body: JSON.stringify({
          name: accountForm.name.trim(),
          currency: accountForm.currency.trim() || 'BRL',
        }),
      });
      setAccountForm(EMPTY_ACCOUNT);
      await loadAccounts();
      if (created?.account?.id) setSelectedId(created.account.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar conta');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateEntry = async (e: FormEvent) => {
    e.preventDefault();
    if (selectedId == null) return;
    const amount = Number(entryForm.amount);
    if (!amount || amount <= 0) {
      setError('Informe um valor > 0');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/trust/accounts/${selectedId}/entries`, {
        method: 'POST',
        body: JSON.stringify({
          entry_type: entryForm.entry_type,
          amount,
          memo: entryForm.memo.trim() || null,
        }),
      });
      setEntryForm(EMPTY_ENTRY);
      await loadAccounts();
      await loadLedger(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao lançar entrada');
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

  const selected = accounts.find((a) => a.id === selectedId) || null;

  return (
    <div className="trust-shell px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker">Trust / IOLTA — stub</p>
            <h1 className="trust-title mt-1">Conta de custódia</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Ledger local de valores de clientes. Não é integração bancária e não há PIX.
            </p>
          </div>
          <Link href="/dashboard" className="trust-btn-ghost">
            ← Dashboard
          </Link>
        </header>

        <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-900">
          Stub de contabilidade trust (estilo IOLTA). Saldo = depósitos − saques − transferências.
          Sem conexão com banco, Open Finance ou PIX.
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        <form
          onSubmit={handleCreateAccount}
          className="trust-card mb-8 grid gap-4 p-5 sm:grid-cols-[1fr_120px_auto]"
        >
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Nome da conta *
            </label>
            <input
              required
              value={accountForm.name}
              onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="IOLTA Principal"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Moeda
            </label>
            <input
              value={accountForm.currency}
              onChange={(e) => setAccountForm({ ...accountForm, currency: e.target.value })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="BRL"
            />
          </div>
          <div className="flex items-end">
            <button type="submit" disabled={saving} className="trust-btn-primary w-full sm:w-auto">
              {saving ? 'Salvando…' : 'Criar conta'}
            </button>
          </div>
        </form>

        <div className="trust-card mb-8 p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Conta ativa
              </label>
              <select
                value={selectedId ?? ''}
                onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}
                className="min-w-[220px] rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              >
                <option value="">Selecione…</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({formatMoney(a.balance ?? 0, a.currency)})
                  </option>
                ))}
              </select>
            </div>
            {selected && (
              <div className="flex flex-wrap items-end gap-3">
                <div className="text-right">
                  <p className="text-xs uppercase tracking-wide text-[#64748b]">Saldo</p>
                  <p className="text-2xl font-semibold text-[#0F766E]">
                    {formatMoney(balance ?? selected.balance ?? 0, selected.currency)}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={reconcileLoading || selectedId == null}
                  onClick={() => selectedId != null && loadReconcile(selectedId)}
                  className="trust-btn-ghost"
                >
                  {reconcileLoading ? 'Reconciliando…' : 'Resumo reconciliação'}
                </button>
              </div>
            )}
          </div>

          {reconcile && selected && (
            <div className="mb-4 rounded-lg border border-[#d7dde5] bg-[#f8fafc] px-4 py-3 text-sm">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                Reconciliação tripartite (stub)
              </p>
              <div className="flex flex-wrap gap-6">
                <div>
                  <span className="text-[#64748b]">Livro </span>
                  <span className="font-semibold text-[#0C1B2A]">
                    {formatMoney(reconcile.book_balance, selected.currency)}
                  </span>
                </div>
                <div>
                  <span className="text-[#64748b]">Não alocado </span>
                  <span className="font-semibold text-[#0C1B2A]">
                    {formatMoney(reconcile.unallocated_balance, selected.currency)}
                  </span>
                </div>
              </div>
              {reconcile.client_subtotals.length > 0 ? (
                <ul className="mt-2 space-y-1 text-[#0C1B2A]">
                  {reconcile.client_subtotals.map((row) => (
                    <li key={row.client_id}>
                      Cliente #{row.client_id}: {formatMoney(row.balance, selected.currency)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-[#64748b]">Nenhum subtotal por cliente.</p>
              )}
              <p className="mt-2 text-xs text-[#94a3b8]">
                {reconcile.note || 'stub — not bank feed'}
                {reconcile.as_of
                  ? ` · ${new Date(reconcile.as_of).toLocaleString('pt-BR')}`
                  : ''}
              </p>
            </div>
          )}

          {selectedId != null && (
            <form
              onSubmit={handleCreateEntry}
              className="grid gap-4 border-t border-[#e8edf2] pt-4 sm:grid-cols-[140px_1fr_1fr_auto]"
            >
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                  Tipo
                </label>
                <select
                  value={entryForm.entry_type}
                  onChange={(e) =>
                    setEntryForm({
                      ...entryForm,
                      entry_type: e.target.value as typeof entryForm.entry_type,
                    })
                  }
                  className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                >
                  <option value="deposit">Depósito</option>
                  <option value="withdrawal">Saque</option>
                  <option value="transfer">Transferência</option>
                  <option value="adjustment">Ajuste</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                  Valor *
                </label>
                <input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={entryForm.amount}
                  onChange={(e) => setEntryForm({ ...entryForm, amount: e.target.value })}
                  className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                  placeholder="1000.00"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                  Memo
                </label>
                <input
                  value={entryForm.memo}
                  onChange={(e) => setEntryForm({ ...entryForm, memo: e.target.value })}
                  className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
                  placeholder="Retainer / honorários"
                />
              </div>
              <div className="flex items-end">
                <button type="submit" disabled={saving} className="trust-btn-primary w-full sm:w-auto">
                  Lançar
                </button>
              </div>
            </form>
          )}
        </div>

        <div className="trust-card overflow-hidden">
          <div className="border-b border-[#e8edf2] px-5 py-3">
            <h2 className="text-sm font-semibold text-[#0C1B2A]">Ledger</h2>
          </div>
          {entries.length === 0 ? (
            <p className="px-5 py-8 text-sm text-[#64748b]">Nenhum lançamento nesta conta.</p>
          ) : (
            <ul className="divide-y divide-[#e8edf2]">
              {entries.map((e) => (
                <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                  <div>
                    <span className="font-medium capitalize text-[#0C1B2A]">{e.entry_type}</span>
                    {e.memo ? <span className="ml-2 text-[#64748b]">— {e.memo}</span> : null}
                    <div className="text-xs text-[#94a3b8]">
                      {e.created_at ? new Date(e.created_at).toLocaleString('pt-BR') : ''}
                    </div>
                  </div>
                  <span
                    className={
                      e.entry_type === 'deposit' || e.entry_type === 'adjustment'
                        ? 'font-semibold text-[#0F766E]'
                        : 'font-semibold text-[#b91c1c]'
                    }
                  >
                    {e.entry_type === 'deposit' || e.entry_type === 'adjustment' ? '+' : '−'}
                    {formatMoney(e.amount, selected?.currency || 'BRL')}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
