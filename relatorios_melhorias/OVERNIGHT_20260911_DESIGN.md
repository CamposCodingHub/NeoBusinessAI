# Overnight 2026-09-11 — Design TRUST (navy / slate / teal)

Data: 11 de setembro de 2026

## Objetivo

Trocar a linguagem visual “AI neon” (roxo/rosa/ciano brilhante) por uma
paleta de **confiança profissional** nas superfícies operacionais e nos
tokens de marca do frontend — sem reescrever o produto inteiro.

## Paleta TRUST

| Token | Hex | Uso |
| --- | --- | --- |
| Ink / Navy | `#0C1B2A` | Fundo escuro da landing, títulos, âncora de marca |
| Navy UI | `#0f172a` | Hierarquia secundária / superfícies elevadas |
| Slate body | `#334155` | Texto corrido em shells claros |
| Slate muted | `#64748b` | Metadados, hints, labels |
| Canvas | `#f7f8fa` / `#eef2f6` | Fundo operacional claro |
| Accent teal | `#0F766E` | CTAs, foco, links, progresso |
| Teal soft | `#0d9488` | Hover / highlights suaves |
| Teal deep | `#115e59` | Hover de botão primário |
| Success / Warning / Danger | `#047857` / `#b45309` / `#b91c1c` | Estados semânticos |

CSS variables e utilitários: `frontend/app/globals.css` (`.trust-shell`,
`.trust-card`, `.trust-btn-primary`, `.trust-btn-ghost`, etc.).

Tokens Tailwind: `frontend/tailwind.config.ts` — `brand.*` agora é navy/slate;
`accent.teal*` é canônico; `accent.cyan` / `purple` / `pink` permanecem como
**aliases** remapeados para tons trust (compatibilidade de classnames legadas).

## O que foi aplicado nesta entrega

1. **`tailwind.config.ts`** — brand navy/slate, accent teal, gradients/shadows
   sem glow roxo neon.
2. **`app/page.tsx`** — ajustes cirúrgicos: fundos, orbs, hero gradient,
   botões e hovers de cyan/purple → teal/navy.
3. **`app/simulador/page.tsx`** — chips de navegação para `/sim-real` e
   `/qa-lab` no header.
4. **`app/qa-lab/page.tsx`** — wrapper e UI em `trust-shell` / `trust-card` /
   `trust-btn-*` (sem ciano neon).
5. **`/sim-real`** (já existente) — referência de shell claro trust.

## Intenção WCAG

- **Contraste de texto:** ink `#0C1B2A` e body `#334155` sobre canvas claro
  (`#f7f8fa` / branco) visam AA para texto normal (≥ 4.5:1). Teal `#0F766E`
  em botão com texto quase-branco (`#f8fafc`) visa AA para UI/CTA.
- **Não depender só da cor:** estados de QA usam label textual
  (`pass` / `fail` / `running`) além de tom semântico.
- **Foco:** inputs no QA Lab usam `focus:border` no accent teal (borda
  visível, não apenas glow).
- **Evitar neon:** glows altos de ciano/roxo reduzem legibilidade e
  contrastam mal com texto fino; a paleta trust prioriza contraste estável
  e superfície calma.

## O que deliberadamente NÃO fazer

- Purple-on-white / gradient roxo “AI SaaS”
- Cream + terracotta clichê
- Layout broadsheet (regras finas, tipografia jornalística densa)
- Reescrita completa da landing ou do dashboard

## Próximos passos (opcional)

- Migrar dashboard/pricing/onboarding dos gradientes `cyan→purple` legados
  para `brand`/`accent.teal` conforme for tocando cada tela.
- Auditar contraste com ferramenta (axe / Lighthouse) em `/qa-lab` e
  `/sim-real` com tema claro.
