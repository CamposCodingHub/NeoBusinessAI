'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface ESignEnvelope {
  id: number;
  title: string;
  status: string;
  signer_email: string;
  signer_name: string;
  provider?: string;
  external_id?: string | null;
  document_id?: number | null;
  created_at?: string | null;
  signed_at?: string | null;
}

const EMPTY_FORM = {
  title: '',
  signer_name: '',
  signer_email: '',
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
    case 'signed':
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    case 'sent':
      return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
    case 'cancelled':
      return 'bg-red-500/20 text-red-300 border-red-500/40';
    default:
      return 'bg-white/10 text-white/70 border-white/20';
  }
}

export default function ESignPage() {
  const router = useRouter();
  const [envelopes, setEnvelopes] = useState<ESignEnvelope[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadEnvelopes = useCallback(async () => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    setError('');
    try {
      const data = await apiFetch('/esign/envelopes');
      setEnvelopes(data.envelopes || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar envelopes');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadEnvelopes();
  }, [loadEnvelopes]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.signer_email.trim() || !form.signer_name.trim()) {
      setError('Preencha título, nome e e-mail do signatário');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiFetch('/esign/envelopes', {
        method: 'POST',
        body: JSON.stringify({
          title: form.title.trim(),
          signer_name: form.signer_name.trim(),
          signer_email: form.signer_email.trim(),
        }),
      });
      setForm(EMPTY_FORM);
      await loadEnvelopes();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar envelope');
    } finally {
      setSaving(false);
    }
  };

  const handleSend = async (id: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/esign/envelopes/${id}/send`, { method: 'POST' });
      await loadEnvelopes();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao enviar');
    } finally {
      setSaving(false);
    }
  };

  const handleMarkSigned = async (id: number) => {
    setSaving(true);
    setError('');
    try {
      await apiFetch(`/esign/envelopes/${id}/mark-signed`, { method: 'POST' });
      await loadEnvelopes();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao marcar assinado');
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
          <p className="trust-kicker">Assinatura eletrônica · stub</p>
          <h1 className="trust-title mt-1">E-Sign</h1>
          <p className="trust-subtitle mt-2 max-w-xl">
            Envelopes ClickSign-style locais (draft → sent → signed). Sem provedor real.
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

      <form onSubmit={handleCreate} className="trust-card mb-8 grid gap-4 p-5 md:grid-cols-2">
        <div className="md:col-span-2">
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">Título</label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Contrato de honorários"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">Signatário</label>
          <input
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.signer_name}
            onChange={(e) => setForm((f) => ({ ...f, signer_name: e.target.value }))}
            placeholder="Nome completo"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wider text-white/50">E-mail</label>
          <input
            type="email"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            value={form.signer_email}
            onChange={(e) => setForm((f) => ({ ...f, signer_email: e.target.value }))}
            placeholder="cliente@empresa.com"
          />
        </div>
        <div className="md:col-span-2">
          <button type="submit" disabled={saving} className="trust-btn-primary">
            {saving ? 'Salvando…' : 'Criar envelope'}
          </button>
        </div>
      </form>

      {envelopes.length === 0 ? (
        <div className="trust-card px-5 py-12 text-center text-sm text-[#94a3b8]">
          Nenhum envelope ainda. Crie o primeiro acima.
        </div>
      ) : (
        <div className="space-y-3">
          {envelopes.map((env) => (
            <article key={env.id} className="trust-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-base font-medium text-white">{env.title}</h2>
                  <span className={`rounded border px-2 py-0.5 text-xs ${statusBadge(env.status)}`}>
                    {env.status}
                  </span>
                </div>
                <p className="mt-1 text-sm text-white/60">
                  {env.signer_name} · {env.signer_email}
                </p>
                {env.external_id ? (
                  <p className="mt-1 text-xs text-white/40">ext: {env.external_id}</p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                {(env.status === 'draft' || env.status === 'sent') && (
                  <button
                    type="button"
                    disabled={saving || env.status === 'sent'}
                    onClick={() => handleSend(env.id)}
                    className="trust-btn-ghost text-sm disabled:opacity-40"
                  >
                    {env.status === 'sent' ? 'Enviado' : 'Enviar'}
                  </button>
                )}
                {env.status !== 'signed' && env.status !== 'cancelled' && (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => handleMarkSigned(env.id)}
                    className="trust-btn-primary text-sm"
                  >
                    Marcar assinado
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
