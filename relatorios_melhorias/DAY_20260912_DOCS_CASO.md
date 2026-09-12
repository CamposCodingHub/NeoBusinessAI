# Checklist documental do caso
## 12/09/2026 — tick diurno (~16:00)

### Dor
Escritório perde tempo cobrando RG, comprovante, procuração — sem lista única do que falta.

### Entrega
- Modelo `MatterDocItem` (pending / received / waived)
- API JWT `/matter-docs` + `POST /matter-docs/seed-intake` (títulos estáticos)
- Incluído em `GET /operations/today` (`docs_pending`)
- UI `/dashboard/docs-caso`
- Testes + QA simulator + router guard

### Limite
Não armazena arquivos; não é DMS nem OCR.
