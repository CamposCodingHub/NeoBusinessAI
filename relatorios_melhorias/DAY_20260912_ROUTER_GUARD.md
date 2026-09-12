# DAY_20260912 — Router registry guard (daytime tick 11)

Data: 12 de setembro de 2026

## Problema

Uma regressão em `backend/main.py` removeu (ou comentou) `include_router` de módulos overnight/daytime. O app subia sem matter/intake/approvals/time/usage/audit/org/trust/esign/monitor/compliance — falha silenciosa até alguém bater na rota.

## Entrega (somente ADD — `main.py` não foi alterado)

| Item | Papel |
| --- | --- |
| `backend/tests/test_router_registry.py` | Lê `main.py` como texto (sem uvicorn / import full app) e falha se faltar router, middleware ou auth no list de docs |
| `backend/scripts/check_router_registry.py` | CLI deploy-preflight; exit `1` se faltar algo |
| Este relatório | Documenta o guard |

## Checagens

1. **include_router ativos** (linha não comentada) para:
   `matter_router`, `intake_router`, `approvals_router`, `time_router`, `usage_router`, `ai_audit_router`, `org_router`, `trust_router`, `esign_router`, `monitor_router`, `compliance_router`, `billing_router`
2. **`setup_security_middleware(app)`** presente e **não** comentado
3. **Heurística** em `@app.get("/api/documents")`: `Depends(get_current_user)` nas linhas seguintes

## Como rodar

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_router_registry.py -q
.\venv311\Scripts\python.exe scripts/check_router_registry.py
```

Usar o CLI antes de deploys locais/Docker para pegar regressão de registry sem subir o servidor.

## Regras respeitadas

- Não reescrever / limpar `main.py`
- Não remover nenhum `include_router`
- Apenas test + script + relatório
- Sem commit neste tick
