# DAY 2026-09-12 — Matter `organization_id` + Lex grounding metadata

## Goal
Daytime tick 3 polish: nullable org scoping on Matter, Lex response metadata for local KB / official codes, thin UI field, and membership tests.

## Deliverables

| Area | Change |
|------|--------|
| `backend/database.py` | `Matter.organization_id` Integer FK nullable + `to_dict`; SQLite `ALTER TABLE matters ADD COLUMN` if missing (same pattern as `users.organization_id`) |
| `backend/routes/matter_routes.py` | Create accepts `organization_id` → `require_org_member`; list accepts `organization_id` (alias of `org_id`); filter already prefers column via `hasattr` |
| `backend/services/legal_ai_orchestrator.py` | `legal_metadata.local_knowledge_hits` when local search ran; `official_sources_used` codes from retrieval |
| `frontend/app/dashboard/matters/page.tsx` | Optional Org ID on existing create form |
| `backend/tests/test_matter_routes.py` | Create-with-org + forbid non-member |

## Matter / org wiring
- Default list/create unchanged when org is omitted.
- Create with `organization_id`: membership required (403 if outsider); column set when present.
- List with `?organization_id=` or `?org_id=`: membership required; `_org_matters_filter` includes `Matter.organization_id == org` now that the column exists (plus owner proxy).

## Lex grounding metadata
- `local_knowledge_hits`: set only when local search path ran (`response_mode != quick` and not quick-document evidence). Quick stays fast (no local search).
- `official_sources_used`: ordered unique codes from `retrieval["sources"]` when any code is present.

## Tests
```bash
cd backend
python -m pytest tests/test_matter_routes.py tests/test_org_access.py -q
```

**Result:** 13 passed (9 matter + 4 org_access).

## Not in scope
Commit/push; full RBAC role matrix; changing quick-mode latency tradeoff.
