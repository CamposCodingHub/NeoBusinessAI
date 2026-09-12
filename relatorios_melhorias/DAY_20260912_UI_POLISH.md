# DAY_20260912 — UI polish (escritório / trust)

Data: 12 de setembro de 2026

## Objetivo

Reduzir ruído visual no dashboard e alinhar landing/CSS ao look profissional navy/slate/teal — sem quebrar o dark dashboard nem apagar tokens existentes.

## Mudanças

### Dashboard (`frontend/app/dashboard/page.tsx`)
- Linha **Operações** reagrupada em seções: **Casos | Financeiro | Equipe | Lex | Demo**
- Links originais preservados (Intake, Matters, Aprovações, Time, Equipe, Orgs, Trust, Finance, E-Sign, Activity, Monitor)
- Lex/Demo: Chat, Peças, Documentos, **Ajuda (`/ajuda`)**, Sim Real, QA Lab, Simulador
- Header e ações rápidas: menos cyan/purple neon; slate/teal calmo

### Landing (`frontend/app/page.tsx`)
- Marca **NeoBusiness AI** em nível de hero; sem purple/neon no hero
- Stats removidos do primeiro viewport (menos competição com a marca)
- CTAs e orbs em teal/slate; features abaixo do fold mantidas

### CSS (`frontend/app/globals.css`)
- Tokens trust preservados; adicionados `--trust-slate` e companions `--trust-on-dark-*`
- Body usa `--trust-ui` (IBM Plex stack do design system)
- `:focus-visible` duplicado removido; outline alinhado ao accent trust

## Fora de escopo
- Sem commit (pedido explícito)
- Sem wipe de arquivos / tokens neon legados
