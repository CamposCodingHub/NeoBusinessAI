'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'sent' | 'failed';

interface OutboundApproval {
  id: number;
  channel: string;
  recipient: string;
  body: string;
  status: ApprovalStatus;
  source: string;
  related_matter_id?: number | null;
  created_at?: string | null;
  decided_at?: string | null;
  error?: string | null;
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

function sourceLabel(source: string): string {
  const map: Record<string, string> = {
    lex: 'Lex',
    deadline: 'Prazos',
    finance: 'Financeiro',
    manual: 'Manual',
  };
  return map[source] || source;
}

function formatWhen(iso?: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function ApprovalsPage() {
  const router = useRouter();
  const [approvals, setApprovals] = useState<OutboundApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadPending = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/approvals/outbound?status=pending&limit=100');
      setApprovals(data.approvals || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar aprovações');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadPending();
  }, [loadPending]);

  const decide = async (id: number, action: 'approve' | 'reject') => {
    setBusyId(id);
    setError('');
    try {
      await apiFetch(`/approvals/outbound/${id}/${action}`, { method: 'POST' });
      setApprovals((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : `Falha ao ${action === 'approve' ? 'aprovar' : 'rejeitar'}`);
    } finally {
      setBusyId(null);
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
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="trust-kicker">Gate humano · WhatsApp</p>
            <h1 className="trust-title mt-1">Aprovações de envio</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Mensagens geradas por Lex, prazos ou financeiro ficam pendentes até um profissional
              aprovar — agentes de IA não enviam sozinhos ao cliente.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="trust-btn-ghost">
              ← Dashboard
            </Link>
            <button type="button" className="trust-btn-ghost" onClick={() => loadPending()}>
              Atualizar
            </button>
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        <div className="mb-4 text-sm text-[#64748b]">
          {approvals.length === 0
            ? 'Nenhuma mensagem pendente.'
            : `${approvals.length} pendente${approvals.length === 1 ? '' : 's'}`}
        </div>

        <ul className="space-y-4">
          {approvals.map((item) => (
            <li key={item.id} className="trust-card p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[#64748b]">
                    <span className="rounded-md bg-[#0F766E]/10 px-2 py-0.5 text-[#0F766E]">
                      {sourceLabel(item.source)}
                    </span>
                    <span>WhatsApp</span>
                    <span>·</span>
                    <span>{formatWhen(item.created_at)}</span>
                  </div>
                  <p className="mt-2 font-medium text-[#0C1B2A]">
                    Para: {item.recipient}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="trust-btn-primary"
                    disabled={busyId === item.id}
                    onClick={() => decide(item.id, 'approve')}
                  >
                    {busyId === item.id ? '…' : 'Aprovar'}
                  </button>
                  <button
                    type="button"
                    className="trust-btn-ghost"
                    disabled={busyId === item.id}
                    onClick={() => decide(item.id, 'reject')}
                  >
                    Rejeitar
                  </button>
                </div>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-[#334155]">
                {item.body}
              </p>
              {item.related_matter_id != null && (
                <p className="mt-2 text-xs text-[#64748b]">
                  Matter relacionado: #{item.related_matter_id}
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
