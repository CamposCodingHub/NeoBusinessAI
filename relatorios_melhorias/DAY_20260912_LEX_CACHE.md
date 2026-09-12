# DAY_20260912 — Lex retrieve TTL cache

Data: 12 de setembro de 2026

## Situação anterior

Em `OfficialLegalSourcesService`:

- Já existia cache **por URL** em `_fetch_text()` (`self._cache`, TTL default **21600s / 6h**) — evita re-download do HTML/PDF oficial.
- `retrieve()` **não** tinha cache do resultado agregado da consulta (análise + excerpts + grounding).

## Mudança

Cache in-memory **thread-safe** para `retrieve()`:

| Item | Detalhe |
| --- | --- |
| Chave | SHA-256 de `normalize_text(query)` + `max_sources` |
| Estrutura | `dict[str, (timestamp, result_dict)]` protegido por `threading.Lock` |
| TTL | **1200s (20 min)** — faixa 10–30 min |
| Correção | Deep-copy do resultado no get/set; miss/expirado → compute normal |

URL fetch cache permanece inalterado (camada inferior).

## Micro-benchmark (opcional / local)

```python
import time
from services.official_legal_sources_service import OfficialLegalSourcesService
svc = OfficialLegalSourcesService()
q = "artigo 5 CF/88 direitos fundamentais"
# cold
t0 = time.perf_counter(); svc.retrieve(q); cold = time.perf_counter() - t0
# warm (retrieve TTL hit — sem re-analisar / re-extrair)
t0 = time.perf_counter(); svc.retrieve(q); warm = time.perf_counter() - t0
print(cold, warm)
```

Esperado: **warm << cold** quando a query normalizada coincide (hit de `_retrieve_cache`).
Se a URL já estiver no `_cache` de fetch, cold também fica mais rápido — o cache de `retrieve` evita até o custo de análise/extração.

## Nota

Sem commit (pedido explícito). Não altera grounding/correctness além de servir o mesmo payload dentro do TTL.
