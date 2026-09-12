# Overnight 2026-09-11 — Dashboard Operações links

Data: 11 de setembro de 2026

## O que foi feito

Inserida na `frontend/app/dashboard/page.tsx` uma fila compacta **Operações**
(após o header), com links trust teal/navy (Tailwind slate/teal compatível com
o fundo escuro do dashboard; utilitários `.trust-*` existem mas são shell claro):

| Rota | Label |
| --- | --- |
| `/dashboard/intake` | Intake |
| `/dashboard/matters` | Matters |
| `/dashboard/approvals` | Aprovações |
| `/dashboard/time` | Time |
| `/sim-real` | Sim Real |
| `/qa-lab` | QA Lab |
| `/portal` | Portal |

Intake / Matters / Time / Approvals já existiam em **Ações Rápidas**; a nova
fila também cobre Sim Real, QA Lab e Portal. Sem rewrite do dashboard.

## Escopo

Cirúrgico — apenas a row de links + este relatório. Sem commit.
