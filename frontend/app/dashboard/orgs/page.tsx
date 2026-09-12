'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface Organization {
  id: number;
  name: string;
  slug: string;
  owner_user_id: number;
  plan_tier: string;
  my_role?: string;
  created_at?: string | null;
}

const EMPTY_FORM = {
  name: '',
  slug: '',
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

export default function OrgsPage() {
  const router = useRouter();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState<'member' | 'admin'>('member');
  const [selectedOrgId, setSelectedOrgId] = useState<number | null>(null);
  const [addingMember, setAddingMember] = useState(false);

  const loadOrgs = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/orgs');
      setOrgs(data.organizations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar organizações');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadOrgs();
  }, [loadOrgs]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    setError('');
    try {
      const payload: Record<string, string> = { name: form.name.trim() };
      if (form.slug.trim()) payload.slug = form.slug.trim().toLowerCase();
      await apiFetch('/orgs', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setForm(EMPTY_FORM);
      await loadOrgs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar organização');
    } finally {
      setSaving(false);
    }
  };

  const handleAddMember = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedOrgId || !memberEmail.trim()) return;
    setAddingMember(true);
    setError('');
    try {
      await apiFetch(`/orgs/${selectedOrgId}/members`, {
        method: 'POST',
        body: JSON.stringify({
          email: memberEmail.trim().toLowerCase(),
          role: memberRole,
        }),
      });
      setMemberEmail('');
      setMemberRole('member');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao adicionar membro');
    } finally {
      setAddingMember(false);
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
            <p className="trust-kicker">Multi-tenant · MVP</p>
            <h1 className="trust-title mt-1">Organizações</h1>
            <p className="trust-subtitle mt-2 max-w-xl">
              Crie uma organização (você vira owner) e adicione membros existentes por e-mail.
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

        <form
          onSubmit={handleCreate}
          className="trust-card mb-8 grid gap-4 p-5 sm:grid-cols-[1fr_1fr_auto]"
        >
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Nome *
            </label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="Meu Escritório"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Slug (opcional)
            </label>
            <input
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="meu-escritorio"
            />
          </div>
          <div className="flex items-end">
            <button type="submit" disabled={saving} className="trust-btn-primary w-full sm:w-auto">
              {saving ? 'Criando…' : 'Criar org'}
            </button>
          </div>
        </form>

        <form
          onSubmit={handleAddMember}
          className="trust-card mb-8 grid gap-4 p-5 sm:grid-cols-[1fr_1fr_auto_auto]"
        >
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Org (para adicionar membro)
            </label>
            <select
              value={selectedOrgId ?? ''}
              onChange={(e) =>
                setSelectedOrgId(e.target.value ? Number(e.target.value) : null)
              }
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
            >
              <option value="">Selecione…</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name} ({o.my_role || 'member'})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              E-mail do membro *
            </label>
            <input
              type="email"
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
              placeholder="colega@escritorio.com"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#64748b]">
              Papel
            </label>
            <select
              value={memberRole}
              onChange={(e) => setMemberRole(e.target.value as 'member' | 'admin')}
              className="w-full rounded-lg border border-[#d7dde5] bg-white px-3 py-2 text-sm text-[#0C1B2A] outline-none focus:border-[#0F766E]"
            >
              <option value="member">member</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={addingMember || !selectedOrgId}
              className="trust-btn-primary w-full sm:w-auto"
            >
              {addingMember ? 'Adicionando…' : 'Add membro'}
            </button>
          </div>
        </form>

        <div className="space-y-3">
          {orgs.length === 0 && (
            <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
              Nenhuma organização ainda. Crie a primeira acima.
            </div>
          )}
          {orgs.map((org) => (
            <article key={org.id} className="trust-card p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h2 className="text-base font-semibold text-[#0C1B2A]">{org.name}</h2>
                  <p className="mt-1 text-sm text-[#64748b]">
                    <code className="text-xs">{org.slug}</code>
                    {' · '}
                    plano {org.plan_tier}
                    {org.my_role ? ` · você: ${org.my_role}` : ''}
                  </p>
                </div>
                <span className="rounded-full bg-[#0F766E]/10 px-3 py-1 text-xs font-semibold text-[#0F766E]">
                  #{org.id}
                </span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
