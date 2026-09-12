'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type InviteRole = 'user' | 'admin';
type InviteStatus = 'pending' | 'accepted' | 'revoked';

interface TeamInvite {
  id: number;
  email: string;
  role: InviteRole | string;
  status: InviteStatus | string;
  created_at?: string | null;
  accepted_at?: string | null;
  token?: string;
}

const EMPTY_FORM = {
  email: '',
  role: 'user' as InviteRole,
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

function statusBadgeClass(status: string): string {
  if (status === 'pending') return 'bg-[#b45309]/10 text-[#b45309]';
  if (status === 'accepted') return 'bg-[#0F766E]/10 text-[#0F766E]';
  return 'bg-[#64748b]/15 text-[#475569]';
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

export default function TeamPage() {
  const router = useRouter();
  const [invites, setInvites] = useState<TeamInvite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [lastToken, setLastToken] = useState<string | null>(null);

  const loadInvites = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/team/invites');
      setInvites(data.invites || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar convites');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadInvites();
  }, [loadInvites]);

  const handleInvite = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.email.trim()) return;
    setSaving(true);
    setError('');
    setLastToken(null);
    try {
      const data = await apiFetch('/team/invites', {
        method: 'POST',
        body: JSON.stringify({
          email: form.email.trim().toLowerCase(),
          role: form.role,
        }),
      });
      const created = data.invite as TeamInvite | undefined;
      if (created?.token) setLastToken(created.token);
      setForm(EMPTY_FORM);
      await loadInvites();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar convite');
    } finally {
      setSaving(false);
    }
  };

  const revokeInvite = async (id: number) => {
    if (!confirm('Revogar este convite?')) return;
    setBusyId(id);
    setError('');
    try {
      await apiFetch(`/team/invites/${id}/revoke`, { method: 'POST' });
      setInvites((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: 'revoked' } : item)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao revogar convite');
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
            <p className="trust-kicker">Multi-usuário · escritório</p>
            <h1 className="trust-title mt-1">Equipe / Convites</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Convide colaboradores por e-mail (user ou admin) e revogue pendentes —
              token de aceite é mostrado uma vez na criação.
            </p>
          </div>
          <Link href="/dashboard" className="trust-btn-ghost">
            ← Dashboard
          </Link>
        </header>

        {error && (
          <div className="mb-4 rounded-xl border border-[#b91c1c]/25 bg-[#b91c1c]/08 px-4 py-3 text-sm text-[#b91c1c]">
            {error}
          </div>
        )}

        {lastToken && (
          <div className="mb-4 rounded-xl border border-[#0F766E]/25 bg-[#0F766E]/08 px-4 py-3 text-sm text-[#0F766E]">
            <p className="font-semibold">Token de aceite (copie agora — não será listado de novo):</p>
            <code className="mt-1 block break-all text-xs text-[#0C1B2A]">{lastToken}</code>
          </div>
        )}

        <form onSubmit={handleInvite} className="trust-card mb-8 grid gap-4 p-5 sm:grid-cols-[1fr_auto_auto]">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              E-mail *
            </label>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="colega@escritorio.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Papel
            </label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as InviteRole })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
            >
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="flex items-end">
            <button type="submit" disabled={saving} className="trust-btn-primary w-full sm:w-auto">
              {saving ? 'Enviando…' : 'Convidar'}
            </button>
          </div>
        </form>

        <div className="space-y-3">
          {invites.length === 0 && (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Nenhum convite ainda. Convide o primeiro membro da equipe.
            </div>
          )}
          {invites.map((invite) => (
            <article key={invite.id} className="trust-card p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-base font-semibold text-[#0C1B2A]">{invite.email}</h2>
                    <span
                      className={`rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase ${statusBadgeClass(invite.status)}`}
                    >
                      {invite.status}
                    </span>
                    <span className="rounded-md bg-[#0C1B2A]/06 px-2 py-0.5 text-[11px] font-semibold uppercase text-[#475569]">
                      {invite.role}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-[#64748b]">
                    Criado {formatWhen(invite.created_at)}
                    {invite.accepted_at ? ` · Aceito ${formatWhen(invite.accepted_at)}` : ''}
                  </p>
                </div>
                {invite.status === 'pending' && (
                  <button
                    type="button"
                    disabled={busyId === invite.id}
                    onClick={() => revokeInvite(invite.id)}
                    className="rounded border border-[#b91c1c]/30 bg-white px-3 py-1.5 text-xs font-semibold text-[#b91c1c] hover:bg-[#b91c1c]/08 disabled:opacity-50"
                  >
                    {busyId === invite.id ? 'Revogando…' : 'Revogar'}
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
