'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

interface DeadlineItem {
  id: number;
  description?: string | null;
  due_date?: string | null;
  urgency?: string | null;
}

interface HearingItem {
  id: number;
  title: string;
  hearing_at?: string | null;
  location?: string | null;
}

interface PoaItem {
  id: number;
  title: string;
  expires_at?: string | null;
}

interface TodayBoard {
  deadlines: {
    overdue: DeadlineItem[];
    due_today: DeadlineItem[];
    upcoming: DeadlineItem[];
    counts: { overdue: number; due_today: number; upcoming: number };
  };
  hearings: HearingItem[];
  hearings_count: number;
  powers_expiring: PoaItem[];
  powers_expiring_count: number;
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

function fmt(iso?: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

export default function HojePage() {
  const router = useRouter();
  const [board, setBoard] = useState<TodayBoard | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError('');
    try {
      const res = await apiFetch('/operations/today');
      if (!res.ok) throw new Error(`Falha ao carregar (${res.status})`);
      setBoard(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hasDashboardToken()) {
      router.replace('/login');
      return;
    }
    void load();
  }, [load, router]);

  const counts = board?.deadlines.counts;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Operações
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
              Hoje
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-400">
              Prazos, audiências e procurações a vencer — o que não pode
              escapar nesta manhã.
            </p>
          </div>
          <Link href="/dashboard" className="text-sm text-teal-400 hover:text-teal-300">
            ← Dashboard
          </Link>
        </div>

        {error && (
          <p className="mb-4 text-sm text-red-400" role="alert">
            {error}
          </p>
        )}

        {loading || !board ? (
          <p className="text-sm text-slate-400">Carregando…</p>
        ) : (
          <>
            <div className="mb-8 grid gap-3 sm:grid-cols-4">
              <Stat label="Atrasados" value={counts?.overdue ?? 0} tone="red" />
              <Stat label="Prazos hoje" value={counts?.due_today ?? 0} tone="amber" />
              <Stat label="Audiências" value={board.hearings_count} tone="sky" />
              <Stat label="POA 30d" value={board.powers_expiring_count} tone="teal" />
            </div>

            <Section title="Prazos atrasados" href="/dashboard/deadlines">
              <DeadlineList items={board.deadlines.overdue} empty="Nenhum prazo atrasado." />
            </Section>

            <Section title="Prazos de hoje" href="/dashboard/deadlines">
              <DeadlineList items={board.deadlines.due_today} empty="Nada vence hoje." />
            </Section>

            <Section title="Próximos 7 dias" href="/dashboard/deadlines">
              <DeadlineList items={board.deadlines.upcoming} empty="Sem prazos à frente." />
            </Section>

            <Section title="Audiências / compromissos" href="/dashboard/agenda">
              {board.hearings.length === 0 ? (
                <p className="text-sm text-slate-400">Nenhuma audiência na janela.</p>
              ) : (
                <ul className="space-y-2">
                  {board.hearings.map((h) => (
                    <li key={h.id} className="text-sm text-slate-200">
                      <span className="font-medium text-white">{h.title}</span>
                      <span className="text-slate-400"> — {fmt(h.hearing_at)}</span>
                      {h.location ? (
                        <span className="text-slate-500"> · {h.location}</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title="Procurações a vencer" href="/dashboard/poa">
              {board.powers_expiring.length === 0 ? (
                <p className="text-sm text-slate-400">Nenhuma POA no horizonte de 30 dias.</p>
              ) : (
                <ul className="space-y-2">
                  {board.powers_expiring.map((p) => (
                    <li key={p.id} className="text-sm text-slate-200">
                      <span className="font-medium text-white">{p.title}</span>
                      <span className="text-slate-400"> — {fmt(p.expires_at)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          </>
        )}
      </div>
    </main>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'red' | 'amber' | 'sky' | 'teal';
}) {
  const tones = {
    red: 'border-red-500/30 bg-red-500/10 text-red-200',
    amber: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
    sky: 'border-sky-500/30 bg-sky-500/10 text-sky-200',
    teal: 'border-teal-500/30 bg-teal-500/10 text-teal-200',
  };
  return (
    <div className={`rounded-xl border p-4 ${tones[tone]}`}>
      <p className="text-[11px] uppercase tracking-wide opacity-80">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function Section({
  title,
  href,
  children,
}: {
  title: string;
  href: string;
  children: ReactNode;
}) {
  return (
    <section className="mb-6 rounded-xl border border-slate-700/60 bg-slate-900/40 p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-100">{title}</h2>
        <Link href={href} className="text-xs text-teal-400 hover:text-teal-300">
          Abrir
        </Link>
      </div>
      {children}
    </section>
  );
}

function DeadlineList({
  items,
  empty,
}: {
  items: DeadlineItem[];
  empty: string;
}) {
  if (!items.length) return <p className="text-sm text-slate-400">{empty}</p>;
  return (
    <ul className="space-y-2">
      {items.map((d) => (
        <li key={d.id} className="text-sm text-slate-200">
          <span className="font-medium text-white">
            {d.description || `Prazo #${d.id}`}
          </span>
          <span className="text-slate-400"> — {fmt(d.due_date)}</span>
          {d.urgency ? (
            <span className="ml-2 text-xs uppercase text-slate-500">{d.urgency}</span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
