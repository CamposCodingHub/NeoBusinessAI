'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

type Prefs = {
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  days_before: number;
  quiet_hours_start: number | null;
  quiet_hours_end: number | null;
};

const DEFAULTS: Prefs = {
  email_enabled: true,
  whatsapp_enabled: false,
  days_before: 3,
  quiet_hours_start: null,
  quiet_hours_end: null,
};

function hasToken(): boolean {
  if (typeof window === 'undefined') return false;
  if (localStorage.getItem('token')) return true;
  try {
    const raw = localStorage.getItem('neobusiness_tokens');
    return !!JSON.parse(raw || '{}')?.access_token;
  } catch {
    return false;
  }
}

export default function SettingsPage() {
  const router = useRouter();
  const [prefs, setPrefs] = useState<Prefs>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [digestCount, setDigestCount] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [waPhone, setWaPhone] = useState('');
  const [waConsentMsg, setWaConsentMsg] = useState<string | null>(null);
  const [waConsentBusy, setWaConsentBusy] = useState(false);

  useEffect(() => {
    if (!hasToken()) {
      router.replace('/login');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await apiFetch('/notifications/preferences');
        if (!cancelled && data?.preferences) {
          setPrefs({
            email_enabled: !!data.preferences.email_enabled,
            whatsapp_enabled: !!data.preferences.whatsapp_enabled,
            days_before: Number(data.preferences.days_before ?? 3),
            quiet_hours_start: data.preferences.quiet_hours_start ?? null,
            quiet_hours_end: data.preferences.quiet_hours_end ?? null,
          });
        }
        const digest = await apiFetch('/notifications/deadline-digest');
        if (!cancelled) setDigestCount(digest?.count ?? 0);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Falha ao carregar');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
  
  const handleWhatsAppConsent = async () => {
    if (!waPhone.trim()) {
      setWaConsentMsg('Informe o telefone do cliente.');
      return;
    }
    setWaConsentBusy(true);
    setWaConsentMsg(null);
    try {
      await apiFetch('/compliance/whatsapp-consent', {
        method: 'POST',
        body: JSON.stringify({ phone: waPhone.trim(), source: 'manual' }),
      });
      setWaConsentMsg('Consentimento WhatsApp registrado.');
      setWaPhone('');
    } catch (e: unknown) {
      setWaConsentMsg(
        e instanceof Error ? e.message : 'Falha ao registrar consentimento'
      );
    } finally {
      setWaConsentBusy(false);
    }
  };

  return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const data = await apiFetch('/notifications/preferences', {
        method: 'PUT',
        body: JSON.stringify({
          email_enabled: prefs.email_enabled,
          whatsapp_enabled: prefs.whatsapp_enabled,
          days_before: prefs.days_before,
          quiet_hours_start: prefs.quiet_hours_start,
          quiet_hours_end: prefs.quiet_hours_end,
          clear_quiet_hours:
            prefs.quiet_hours_start == null && prefs.quiet_hours_end == null,
        }),
      });
      if (data?.preferences) {
        setPrefs({
          email_enabled: !!data.preferences.email_enabled,
          whatsapp_enabled: !!data.preferences.whatsapp_enabled,
          days_before: Number(data.preferences.days_before ?? 3),
          quiet_hours_start: data.preferences.quiet_hours_start ?? null,
          quiet_hours_end: data.preferences.quiet_hours_end ?? null,
        });
      }
      const digest = await apiFetch('/notifications/deadline-digest');
      setDigestCount(digest?.count ?? 0);
      setMessage('Preferências salvas.');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao salvar');
    } finally {
      setSaving(false);
    }
  }

  async function handleLgpdExport() {
    if (!hasToken()) {
      router.replace('/login');
      return;
    }
    setExporting(true);
    setMessage(null);
    setError(null);
    try {
      const data = await apiFetch('/gdpr/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `neobusiness-lgpd-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setMessage('Exportação LGPD baixada.');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao exportar dados');
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white px-6 py-16">
      <div className="max-w-3xl mx-auto rounded-3xl border border-white/10 bg-white/5 p-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          Configuracoes
        </h1>
        <p className="mt-4 text-white/65 leading-relaxed">
          Preferencias de alerta de prazos do escritorio. O digest e apenas preview — nenhum
          e-mail ou WhatsApp e enviado automaticamente neste MVP.
        </p>

        {loading ? (
          <p className="mt-8 text-white/50">Carregando…</p>
        ) : (
          <div className="mt-8 space-y-6">
            <h2 className="text-xl font-semibold text-white/90">Alertas de prazos</h2>

            <label className="flex items-center justify-between gap-4">
              <span>E-mail</span>
              <input
                type="checkbox"
                checked={prefs.email_enabled}
                onChange={(e) => setPrefs({ ...prefs, email_enabled: e.target.checked })}
              />
            </label>

            <label className="flex items-center justify-between gap-4">
              <span>WhatsApp</span>
              <input
                type="checkbox"
                checked={prefs.whatsapp_enabled}
                onChange={(e) => setPrefs({ ...prefs, whatsapp_enabled: e.target.checked })}
              />
            </label>

            <label className="flex flex-col gap-2">
              <span>Dias de antecedencia</span>
              <input
                type="number"
                min={0}
                max={90}
                className="rounded-xl bg-black/40 border border-white/10 px-4 py-2 w-32"
                value={prefs.days_before}
                onChange={(e) =>
                  setPrefs({ ...prefs, days_before: Number(e.target.value) || 0 })
                }
              />
            </label>

            <div className="grid grid-cols-2 gap-4">
              <label className="flex flex-col gap-2">
                <span>Quiet hours inicio (0–23)</span>
                <input
                  type="number"
                  min={0}
                  max={23}
                  placeholder="—"
                  className="rounded-xl bg-black/40 border border-white/10 px-4 py-2"
                  value={prefs.quiet_hours_start ?? ''}
                  onChange={(e) =>
                    setPrefs({
                      ...prefs,
                      quiet_hours_start:
                        e.target.value === '' ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
              <label className="flex flex-col gap-2">
                <span>Quiet hours fim (0–23)</span>
                <input
                  type="number"
                  min={0}
                  max={23}
                  placeholder="—"
                  className="rounded-xl bg-black/40 border border-white/10 px-4 py-2"
                  value={prefs.quiet_hours_end ?? ''}
                  onChange={(e) =>
                    setPrefs({
                      ...prefs,
                      quiet_hours_end:
                        e.target.value === '' ? null : Number(e.target.value),
                    })
                  }
                />
              </label>
            </div>

            {digestCount !== null && (
              <p className="text-sm text-white/55">
                Preview do digest: <strong className="text-white/80">{digestCount}</strong>{' '}
                prazo(s) na janela atual.
              </p>
            )}

            {message && <p className="text-sm text-emerald-400">{message}</p>}
            {error && <p className="text-sm text-red-400">{error}</p>}

            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-semibold disabled:opacity-50"
            >
              {saving ? 'Salvando…' : 'Salvar preferencias'}
            </button>
          </div>
        )}

        
        <section className="mt-8 rounded-2xl border border-slate-700/50 bg-[#0f172a]/40 p-5">
          <h2 className="text-lg font-semibold text-slate-100">Consentimento WhatsApp (LGPD)</h2>
          <p className="mt-2 text-sm text-slate-400">
            Stub de opt-in antes de envios outbound. O approve em Aprovacoes exige consentimento ativo.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 items-end">
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Telefone
              <input
                value={waPhone}
                onChange={(e) => setWaPhone(e.target.value)}
                placeholder="5511999990000"
                className="rounded-lg border border-slate-600 bg-slate-900/60 px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <button
              type="button"
              onClick={handleWhatsAppConsent}
              disabled={waConsentBusy || loading}
              className="rounded-lg border border-teal-500/40 bg-teal-500/15 px-4 py-2 text-sm text-teal-100 hover:bg-teal-500/25 disabled:opacity-50"
            >
              {waConsentBusy ? 'Salvando…' : 'Registrar consentimento'}
            </button>
          </div>
          {waConsentMsg ? (
            <p className="mt-3 text-xs text-slate-300">{waConsentMsg}</p>
          ) : null}
        </section>

<section className="trust-card mt-8 p-5">
          <h2 className="trust-section-title">Privacidade (LGPD)</h2>
          <p className="mt-2 text-sm text-[var(--trust-muted)]">
            Baixe um pacote JSON com os dados associados à sua conta autenticada.
          </p>
          <button
            type="button"
            onClick={handleLgpdExport}
            disabled={exporting || loading}
            className="trust-btn-primary mt-4 disabled:opacity-50"
          >
            {exporting ? 'Exportando…' : 'Exportar meus dados (LGPD)'}
          </button>
        </section>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/dashboard"
            className="px-5 py-3 rounded-xl bg-white/10 hover:bg-white/15 transition"
          >
            Ir para o dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
