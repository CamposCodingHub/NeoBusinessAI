'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Invoice {
  id: number;
  invoice_number: string;
  description: string;
  amount: number;
  discount: number;
  total: number;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  due_date: string;
  paid_at: string | null;
  client_name: string;
  invoice_type: string;
  reminder_sent: boolean;
}

interface FinanceStats {
  summary: {
    total_billed: number;
    total_pending: number;
    total_overdue: number;
    total_outstanding: number;
  };
  counts: {
    paid: number;
    pending: number;
    overdue: number;
    total: number;
  };
  monthly_revenue: { month: string; month_name: string; revenue: number }[];
  top_debtors: { client_id: number; client_name: string; debt: number }[];
}

interface AgingReport {
  buckets: {
    current: number;
    d31_60: number;
    d61_90: number;
    d90_plus: number;
  };
  total_open: number;
  currency: string;
}

interface CollectionStep {
  code: string;
  label: string;
  tone: string;
  is_current?: boolean;
  suggested_copy?: string;
}

interface CollectionPlan {
  invoice_id: number;
  invoice_number?: string;
  client_name?: string | null;
  amount: number;
  days_from_due: number;
  recommended_step: string;
  steps: CollectionStep[];
}

interface CollectionPlanResponse {
  plans: CollectionPlan[];
  count: number;
  disclaimer: string;
  currency: string;
}

interface CostAdvance {
  id: number;
  description: string;
  amount: number;
  status: 'advanced' | 'reimbursed' | 'written_off';
  client_id?: number | null;
  matter_id?: number | null;
  created_at?: string | null;
}

interface TaxCalendarItem {
  code: string;
  title: string;
  due_hint: string;
  disclaimer: string;
}


interface ProfitabilityClient {
  client_id: number | null;
  client_name: string;
  invoiced: number;
  time_value: number;
  costs_open: number;
  rough_margin: number;
}

interface ProfitabilityReport {
  clients: ProfitabilityClient[];
  note: string;
}

interface TaxCalendarResponse {
  month: string;
  items: TaxCalendarItem[];
  count: number;
  disclaimer: string;
  stub: boolean;
}

export default function FinancePage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<FinanceStats | null>(null);
  const [overdueList, setOverdueList] = useState<Invoice[]>([]);
  const [aging, setAging] = useState<AgingReport | null>(null);
  const [collectionPlan, setCollectionPlan] = useState<CollectionPlanResponse | null>(null);
  const [costAdvances, setCostAdvances] = useState<CostAdvance[]>([]);
  const [taxCalendar, setTaxCalendar] = useState<TaxCalendarResponse | null>(null);
  const [profitability, setProfitability] = useState<ProfitabilityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending' | 'paid' | 'overdue'>('all');
  const [costForm, setCostForm] = useState({ description: '', amount: '', client_id: '', matter_id: '' });

  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    discount: '0',
    client_id: '',
    due_days: '7',
    invoice_type: 'service'
  });

  const getToken = () => {
    const tokensStr = localStorage.getItem('neobusiness_tokens');
    if (!tokensStr) return '';
    try {
      const tokens = JSON.parse(tokensStr);
      return tokens?.access_token || '';
    } catch { return ''; }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  const fetchData = async () => {
    const token = getToken();
    if (!token) return;

    try {
      // Fetch invoices
      const invResponse = await fetch(`${API_URL}/finance/invoices?status=${filter === 'all' ? '' : filter}`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (invResponse.ok) {
        const data = await invResponse.json();
        setInvoices(data.invoices || []);
      }

      // Fetch stats
      const statsResponse = await fetch(`${API_URL}/finance/dashboard?period_days=180`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data);
      }

      // Fetch overdue list
      const overdueResponse = await fetch(`${API_URL}/finance/overdue/list`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (overdueResponse.ok) {
        const data = await overdueResponse.json();
        setOverdueList(data.overdue_invoices || []);
      }

      // Receivables aging (BI light)
      const agingResponse = await fetch(`${API_URL}/finance/aging`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (agingResponse.ok) {
        const data = await agingResponse.json();
        setAging(data);
      }

      // Ethical collection plan (régua EOAB stub)
      const planResponse = await fetch(`${API_URL}/finance/collection-plan`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (planResponse.ok) {
        setCollectionPlan(await planResponse.json());
      }

      // Custas / cost advances
      const costResponse = await fetch(`${API_URL}/finance/cost-advances`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (costResponse.ok) {
        const data = await costResponse.json();
        setCostAdvances(data.items || []);
      }


      // Client profitability stub
      const profitResponse = await fetch(`${API_URL}/finance/profitability?limit=10`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (profitResponse.ok) {
        setProfitability(await profitResponse.json());
      }

      // Tax calendar methodological stub (not RFB API)
      const now = new Date();
      const month = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}`;
      const taxResponse = await fetch(`${API_URL}/finance/tax-calendar?month=${month}`, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'omit',
      });
      if (taxResponse.ok) {
        setTaxCalendar(await taxResponse.json());
      }
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCostAdvance = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    if (!token || !costForm.description || !costForm.amount) return;
    try {
      const response = await fetch(`${API_URL}/finance/cost-advances`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
        body: JSON.stringify({
          description: costForm.description,
          amount: parseFloat(costForm.amount),
          client_id: costForm.client_id ? parseInt(costForm.client_id, 10) : null,
          matter_id: costForm.matter_id ? parseInt(costForm.matter_id, 10) : null,
        }),
      });
      if (response.ok) {
        setCostForm({ description: '', amount: '', client_id: '', matter_id: '' });
        fetchData();
      }
    } catch (error) {
      console.error('Erro ao registrar custas:', error);
    }
  };

  const handleCostStatus = async (id: number, status: CostAdvance['status']) => {
    const token = getToken();
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/finance/cost-advances/${id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
        body: JSON.stringify({ status }),
      });
      if (response.ok) fetchData();
    } catch (error) {
      console.error('Erro ao atualizar custas:', error);
    }
  };

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/finance/invoices`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'omit',
        body: JSON.stringify({
          description: formData.description,
          amount: parseFloat(formData.amount),
          discount: parseFloat(formData.discount),
          client_id: formData.client_id ? parseInt(formData.client_id) : null,
          due_days: parseInt(formData.due_days),
          invoice_type: formData.invoice_type
        })
      });

      if (response.ok) {
        setShowForm(false);
        setFormData({ description: '', amount: '', discount: '0', client_id: '', due_days: '7', invoice_type: 'service' });
        fetchData();
      }
    } catch (error) {
      console.error('Erro ao criar fatura:', error);
    }
  };

  const handleMarkPaid = async (id: number) => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/finance/invoices/${id}/pay`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) fetchData();
    } catch (error) {
      console.error('Erro ao marcar como paga:', error);
    }
  };

  const handleSendReminder = async (id: number) => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/finance/invoices/${id}/send-reminder`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) {
        alert('Lembrete enviado!');
        fetchData();
      }
    } catch (error) {
      console.error('Erro ao enviar lembrete:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'bg-emerald-500/20 text-emerald-400';
      case 'pending': return 'bg-amber-500/20 text-amber-400';
      case 'overdue': return 'bg-red-500/20 text-red-400';
      default: return 'bg-white/10 text-white/60';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'paid': return 'Pago';
      case 'pending': return 'Pendente';
      case 'overdue': return 'Atrasado';
      case 'cancelled': return 'Cancelado';
      default: return status;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0C1B2A] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0C1B2A] text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ← Voltar
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Gestão Financeira
              </h1>
              <p className="text-white/60">Faturas, receitas e inadimplência</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-cyan-600 rounded-xl font-semibold hover:opacity-90 transition"
            >
              + Nova Fatura
            </button>
            <button
              onClick={() => {
                localStorage.removeItem('neobusiness_tokens');
                window.location.href = '/login';
              }}
              className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition text-sm"
            >
              Sair
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4">
              <p className="text-emerald-400 text-sm">Total Faturado</p>
              <p className="text-2xl font-bold text-emerald-400">{formatCurrency(stats.summary.total_billed)}</p>
              <p className="text-white/40 text-xs">{stats.counts.paid} faturas pagas</p>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
              <p className="text-amber-400 text-sm">Pendente</p>
              <p className="text-2xl font-bold text-amber-400">{formatCurrency(stats.summary.total_pending)}</p>
              <p className="text-white/40 text-xs">{stats.counts.pending} faturas</p>
            </div>
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <p className="text-red-400 text-sm">Atrasado</p>
              <p className="text-2xl font-bold text-red-400">{formatCurrency(stats.summary.total_overdue)}</p>
              <p className="text-white/40 text-xs">{stats.counts.overdue} faturas</p>
            </div>
            <div className="bg-white/5 border border-white/20 rounded-xl p-4">
              <p className="text-white/60 text-sm">A Receber</p>
              <p className="text-2xl font-bold text-white">{formatCurrency(stats.summary.total_outstanding)}</p>
              <p className="text-white/40 text-xs">Pendente + Atrasado</p>
            </div>
          </div>
        )}


        {/* Receivables aging — navy/teal, no card clutter */}
        {aging && (
          <section className="mb-8 border-t border-[#0F766E]/30 pt-6">
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">
                  Contas a receber
                </p>
                <h2 className="mt-1 text-xl font-semibold text-[#E8EEF4]">Aging de honorários</h2>
                <p className="mt-1 text-sm text-[#94A3B8]">
                  Buckets por dias desde o vencimento · {aging.currency}
                </p>
              </div>
              <p className="text-lg font-semibold text-[#0F766E]">
                Aberto: {formatCurrency(aging.total_open)}
              </p>
            </div>
            <div className="flex items-end gap-3 h-36 sm:gap-5">
              {([
                { key: 'current', label: '0–30', value: aging.buckets.current },
                { key: 'd31_60', label: '31–60', value: aging.buckets.d31_60 },
                { key: 'd61_90', label: '61–90', value: aging.buckets.d61_90 },
                { key: 'd90_plus', label: '90+', value: aging.buckets.d90_plus },
              ] as const).map((bucket) => {
                const max = Math.max(
                  aging.buckets.current,
                  aging.buckets.d31_60,
                  aging.buckets.d61_90,
                  aging.buckets.d90_plus,
                  1
                );
                const height = Math.max(4, (bucket.value / max) * 100);
                return (
                  <div key={bucket.key} className="flex flex-1 flex-col items-center gap-2">
                    <span className="text-xs text-[#94A3B8]">{formatCurrency(bucket.value)}</span>
                    <div
                      className="w-full max-w-[72px] rounded-t-md bg-gradient-to-t from-[#0C1B2A] to-[#0F766E]"
                      style={{ height: `${height}%` }}
                      title={formatCurrency(bucket.value)}
                    />
                    <span className="text-xs font-medium text-[#CBD5E1]">{bucket.label}</span>
                  </div>
                );
              })}
            </div>
          </section>
        )}


        {/* Client profitability stub */}
        {profitability && (
          <section className="mb-8 border-t border-[#0F766E]/30 pt-6">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">
                Rentabilidade
              </p>
              <h2 className="mt-1 text-xl font-semibold text-[#E8EEF4]">Lucro por cliente (estimativa)</h2>
              <p className="mt-1 text-sm text-[#94A3B8]">{profitability.note}</p>
            </div>
            {profitability.clients.length === 0 ? (
              <p className="text-sm text-[#64748B]">Sem atividade faturável ainda.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-[#1E293B] text-xs uppercase tracking-wide text-[#64748B]">
                      <th className="py-2 pr-3 font-medium">Cliente</th>
                      <th className="py-2 pr-3 font-medium text-right">Faturado</th>
                      <th className="py-2 pr-3 font-medium text-right">Horas</th>
                      <th className="py-2 pr-3 font-medium text-right">Custas abertas</th>
                      <th className="py-2 font-medium text-right">Margem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profitability.clients.map((c) => (
                      <tr
                        key={c.client_id ?? `none-${c.client_name}`}
                        className="border-b border-[#1E293B]/80 last:border-0"
                      >
                        <td className="py-2.5 pr-3 text-[#E8EEF4]">{c.client_name}</td>
                        <td className="py-2.5 pr-3 text-right text-[#CBD5E1]">{formatCurrency(c.invoiced)}</td>
                        <td className="py-2.5 pr-3 text-right text-[#94A3B8]">{formatCurrency(c.time_value)}</td>
                        <td className="py-2.5 pr-3 text-right text-[#94A3B8]">{formatCurrency(c.costs_open)}</td>
                        <td className={`py-2.5 text-right font-semibold ${c.rough_margin >= 0 ? 'text-[#0F766E]' : 'text-red-400'}`}>
                          {formatCurrency(c.rough_margin)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* Ethical collection plan — EOAB stub */}
        {collectionPlan && (
          <section className="mb-8 border-t border-[#0F766E]/30 pt-6">
            <div className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">
                Régua ética
              </p>
              <h2 className="mt-1 text-xl font-semibold text-[#E8EEF4]">Plano de cobrança (stub)</h2>
              <p className="mt-2 max-w-3xl text-sm text-[#94A3B8] leading-relaxed">
                {collectionPlan.disclaimer}
              </p>
            </div>
            {collectionPlan.plans.length === 0 ? (
              <p className="text-sm text-[#64748B]">Nenhuma fatura aberta para planejar.</p>
            ) : (
              <div className="space-y-4">
                {collectionPlan.plans.slice(0, 8).map((plan) => (
                  <div key={plan.invoice_id} className="border-b border-[#1E293B] pb-4 last:border-0">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <div>
                        <p className="font-medium text-[#E8EEF4]">
                          {plan.client_name || 'Sem cliente'} · {plan.invoice_number || `#${plan.invoice_id}`}
                        </p>
                        <p className="text-xs text-[#94A3B8]">
                          {plan.days_from_due < 0
                            ? `Vence em ${Math.abs(plan.days_from_due)} dia(s)`
                            : plan.days_from_due === 0
                              ? 'Vence hoje'
                              : `${plan.days_from_due} dia(s) em atraso`}
                          {' · '}sugerido: {plan.recommended_step}
                        </p>
                      </div>
                      <span className="text-[#0F766E] font-semibold">{formatCurrency(plan.amount)}</span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {plan.steps.map((step) => (
                        <span
                          key={step.code}
                          title={step.suggested_copy}
                          className={`px-2.5 py-1 text-xs border ${
                            step.is_current
                              ? 'border-[#0F766E] text-[#5EEAD4] bg-[#0F766E]/15'
                              : 'border-[#334155] text-[#64748B]'
                          }`}
                        >
                          {step.code} {step.label}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Tax calendar — methodological stub (not RFB API) */}
        {taxCalendar && (
          <section className="mb-8 border-t border-[#0F766E]/30 pt-6">
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">
                  Contador
                </p>
                <h2 className="mt-1 text-xl font-semibold text-[#E8EEF4]">
                  Obrigações do mês ({taxCalendar.month})
                </h2>
                <p className="mt-2 max-w-3xl text-sm text-[#94A3B8] leading-relaxed">
                  {taxCalendar.disclaimer}
                </p>
              </div>
              <Link href="/ajuda#reforma-esocial" className="text-sm text-[#5EEAD4] hover:underline">
                Reforma / eSocial × DCTFWeb →
              </Link>
            </div>
            <ul className="space-y-4">
              {taxCalendar.items.map((item) => (
                <li key={item.code} className="border-b border-[#1E293B] pb-4 last:border-0">
                  <p className="font-medium text-[#E8EEF4]">{item.title}</p>
                  <p className="mt-1 text-sm text-[#CBD5E1]">{item.due_hint}</p>
                  <p className="mt-1 text-xs text-[#64748B]">{item.disclaimer}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Custas / cost advances */}
        <section className="mb-8 border-t border-[#0F766E]/30 pt-6">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#5EEAD4]">
                Custas
              </p>
              <h2 className="mt-1 text-xl font-semibold text-[#E8EEF4]">Adiantamentos de custas</h2>
              <p className="mt-1 text-sm text-[#94A3B8]">
                Guias e despesas processuais — advanced / reimbursed / written_off
              </p>
            </div>
            <Link href="/ajuda" className="text-sm text-[#5EEAD4] hover:underline">
              Ver checklist →
            </Link>
          </div>
          <form onSubmit={handleCreateCostAdvance} className="mb-4 grid gap-3 sm:grid-cols-4">
            <input
              type="text"
              value={costForm.description}
              onChange={(e) => setCostForm({ ...costForm, description: e.target.value })}
              placeholder="Descrição (ex.: guia inicial)"
              className="sm:col-span-2 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-[#0F766E]/50"
              required
            />
            <input
              type="number"
              step="0.01"
              value={costForm.amount}
              onChange={(e) => setCostForm({ ...costForm, amount: e.target.value })}
              placeholder="Valor R$"
              className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-[#0F766E]/50"
              required
            />
            <button
              type="submit"
              className="px-4 py-2 bg-[#0F766E]/30 hover:bg-[#0F766E]/45 text-[#5EEAD4] rounded-lg text-sm font-medium transition"
            >
              Registrar
            </button>
          </form>
          {costAdvances.length === 0 ? (
            <p className="text-sm text-[#64748B]">Nenhum adiantamento registrado.</p>
          ) : (
            <div className="space-y-2">
              {costAdvances.slice(0, 10).map((row) => (
                <div
                  key={row.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-2 border-b border-[#1E293B]"
                >
                  <div>
                    <p className="text-sm text-[#E8EEF4]">{row.description}</p>
                    <p className="text-xs text-[#64748B]">
                      {row.status}
                      {row.created_at
                        ? ` · ${new Date(row.created_at).toLocaleDateString('pt-BR')}`
                        : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[#CBD5E1]">{formatCurrency(row.amount)}</span>
                    {row.status === 'advanced' && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleCostStatus(row.id, 'reimbursed')}
                          className="px-2 py-1 text-xs text-[#5EEAD4] hover:bg-[#0F766E]/20 rounded"
                        >
                          Reembolsado
                        </button>
                        <button
                          type="button"
                          onClick={() => handleCostStatus(row.id, 'written_off')}
                          className="px-2 py-1 text-xs text-[#94A3B8] hover:bg-white/5 rounded"
                        >
                          Baixar
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Monthly Chart */}
        {stats && stats.monthly_revenue.length > 0 && (
          <div className="bg-white/5 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Receita Mensal (6 meses)</h2>
            <div className="flex items-end gap-4 h-40">
              {stats.monthly_revenue.map((month, idx) => {
                const max = Math.max(...stats.monthly_revenue.map(m => m.revenue)) || 1;
                const height = (month.revenue / max) * 100;
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full bg-cyan-500/30 rounded-t-lg relative group" style={{ height: `${height}%` }}>
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white/10 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                        {formatCurrency(month.revenue)}
                      </div>
                    </div>
                    <span className="text-xs text-white/40">{month.month_name}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Overdue Alert */}
        {overdueList.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
            <h2 className="text-lg font-semibold text-red-400 mb-3">⚠️ Régua de Cobrança - Atrasados</h2>
            <div className="space-y-2">
              {overdueList.slice(0, 5).map((inv) => (
                <div key={inv.id} className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-red-500 text-white rounded text-xs font-bold">
                      {(inv as any).days_overdue} dias
                    </span>
                    <div>
                      <p className="font-medium">{inv.client_name}</p>
                      <p className="text-sm text-white/50">{inv.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold">{formatCurrency(inv.total)}</span>
                    <button
                      onClick={() => handleSendReminder(inv.id)}
                      disabled={inv.reminder_sent}
                      className={`px-3 py-1 rounded-lg text-sm transition ${
                        inv.reminder_sent
                          ? 'bg-white/10 text-white/40'
                          : 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400'
                      }`}
                    >
                      {inv.reminder_sent ? 'Lembrete enviado' : 'Enviar lembrete'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* New Invoice Form */}
        {showForm && (
          <div className="bg-white/5 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Nova Fatura</h2>
            <form onSubmit={handleCreateInvoice} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-2">Descrição</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Ex: Honorários advocatícios - Maio/2025"
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Valor (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Desconto (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.discount}
                  onChange={(e) => setFormData({ ...formData, discount: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">ID Cliente</label>
                <input
                  type="text"
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  placeholder="Opcional"
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Dias para Vencimento</label>
                <input
                  type="number"
                  value={formData.due_days}
                  onChange={(e) => setFormData({ ...formData, due_days: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50"
                />
              </div>
              <div className="md:col-span-3 flex gap-3">
                <button
                  type="submit"
                  className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-600 rounded-lg font-semibold hover:opacity-90 transition"
                >
                  Criar Fatura
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-4">
          {(['all', 'pending', 'paid', 'overdue'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg transition ${
                filter === f
                  ? 'bg-emerald-500/30 text-emerald-400 border border-emerald-500/50'
                  : 'bg-white/5 text-white/60 hover:bg-white/10'
              }`}
            >
              {f === 'all' ? 'Todas' : f === 'pending' ? 'Pendentes' : f === 'paid' ? 'Pagas' : 'Atrasadas'}
            </button>
          ))}
        </div>

        {/* Invoices Table */}
        <div className="bg-white/5 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold">
              Faturas <span className="text-white/40 text-sm">({invoices.length})</span>
            </h2>
          </div>

          {invoices.length === 0 ? (
            <div className="text-center py-12 text-white/40">
              <div className="text-4xl mb-4">💰</div>
              <p>Nenhuma fatura encontrada</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-4 text-white/60 font-medium">Número</th>
                    <th className="text-left p-4 text-white/60 font-medium">Cliente</th>
                    <th className="text-left p-4 text-white/60 font-medium">Descrição</th>
                    <th className="text-left p-4 text-white/60 font-medium">Valor</th>
                    <th className="text-left p-4 text-white/60 font-medium">Vencimento</th>
                    <th className="text-left p-4 text-white/60 font-medium">Status</th>
                    <th className="text-left p-4 text-white/60 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-white/5">
                      <td className="p-4 font-mono text-sm">{inv.invoice_number}</td>
                      <td className="p-4">{inv.client_name || '-'}</td>
                      <td className="p-4 text-white/80">{inv.description}</td>
                      <td className="p-4 font-semibold">{formatCurrency(inv.total)}</td>
                      <td className="p-4 text-white/60">
                        {new Date(inv.due_date).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-lg text-sm ${getStatusColor(inv.status)}`}>
                          {getStatusLabel(inv.status)}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          {inv.status === 'pending' && (
                            <button
                              onClick={() => handleMarkPaid(inv.id)}
                              className="px-3 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg transition text-sm"
                            >
                              Marcar paga
                            </button>
                          )}
                          {(inv.status === 'pending' || inv.status === 'overdue') && !inv.reminder_sent && (
                            <button
                              onClick={() => handleSendReminder(inv.id)}
                              className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded-lg transition text-sm"
                            >
                              Lembrete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Top Debtors */}
        {stats && stats.top_debtors.length > 0 && (
          <div className="mt-6 bg-white/5 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">🏆 Top Devedores</h2>
            <div className="space-y-2">
              {stats.top_debtors.map((debtor, idx) => (
                <div key={debtor.client_id} className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-white/40">#{idx + 1}</span>
                    <span className="font-medium">{debtor.client_name}</span>
                  </div>
                  <span className="text-red-400 font-bold">{formatCurrency(debtor.debt)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
