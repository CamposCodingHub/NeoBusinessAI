# Overnight 2026-09-12 — Pricing trust / rentabilidade SaaS

Data: 12 de setembro de 2026

## Objetivo

Melhorar de forma cirúrgica a percepção de confiança e clareza comercial da
página de preços (`frontend/app/pricing/page.tsx`), alinhando tokens visuais a
navy/slate/teal e deixando Starter / Professional / Business óbvios com CTA —
sem reescrever a página.

## O que foi feito

### Tokens de confiança (sem neon)

Substituídos gradientes `cyan → purple` e glow neon por:

- Fundo / bordas: `slate-950`, `slate-900`, `slate-700/800`
- Acentos e CTAs: `teal-700` / `teal-600` / `teal-400`
- Popular card: borda `teal-600/50` sólida, sem sombra neon

### Planos e CTAs

| Antes | Depois | CTA |
| --- | --- | --- |
| Explorar | **Starter** | Começar no Starter |
| Profissional | **Professional** | Escolher Professional |
| Escritório | **Business** | Escolher Business |
| Scale | Enterprise (alto volume) | Falar com vendas |

IDs (`starter` / `professional` / `business` / `enterprise`) e fluxo de
registro / contact-sales mantidos.

### Linha de credibilidade

Sob o subtítulo do hero (texto curto, sem cards):

> LGPD · auditoria de IA · aprovação humana no WhatsApp

### Demo `/sim-real`

- Pricing: link no hero + botão **Ver demo** no CTA final
- Contact (`frontend/app/contact/page.tsx`): nota + botão **Ver demo** → `/sim-real`

## Fora de escopo

- `frontend/src/app/pricing/page.tsx` (árvore legado / não usada pelo app router
  principal) — não alterada
- Página de registro — só referenciada; sem mudanças de layout
- Sem commit

## Como validar

1. Abrir `/pricing` — três planos nomeados Starter / Professional / Business
   com CTA claro; accents slate/teal (sem purple/cyan neon).
2. Conferir linha LGPD / auditoria / WhatsApp no hero.
3. Clicar **Abrir demo /sim-real** e **Ver demo** → `/sim-real`.
4. Abrir `/contact` → link/botão para `/sim-real`.
