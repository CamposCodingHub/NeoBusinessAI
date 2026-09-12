# DAY 2026-09-12 — Org-scoped RBAC (multi-tenant polish)

## Goal
Pragmatic organization membership helpers for daytime multi-tenant access, lightly wired into Matter list/get without breaking default ownership behavior.

## Deliverables

| Path | Role |
|------|------|
| `backend/services/org_access.py` | `get_user_org_ids`, `require_org_member` (403), `user_can_access_resource` |
| `backend/tests/test_org_access.py` | ≥4 unit tests (no full `main` import) |
| `backend/routes/matter_routes.py` | Optional `org_id` query on list/get |
| This report | Schema future work + sovereign local search notes |

## RBAC rules
- **Same user**: `user_id == resource_user_id` → allow.
- **Org member**: `resource_org_id` set and user is in `organization_members` → allow.
- **`require_org_member`**: missing membership → HTTP 403 (not 404).

## Matter wiring
- Default (no `org_id`): unchanged — only matters where `Matter.user_id == current_user.id`.
- With `?org_id=N`: caller must be org member; list/get filters to matters owned by the org **owner**.
- If `Matter.organization_id` exists later, filter also includes `organization_id == org_id` (helper already checks `hasattr`).

## Schema — future work (skipped today)
`Matter` currently has **no** `organization_id` column. Adding a nullable FK is deliberately deferred to avoid migrations/breakage in this polish pass.

Suggested follow-up:
1. `matters.organization_id INTEGER NULL` + SQLite local migration (same pattern as `users.organization_id`).
2. Set `organization_id` on create when the user has a primary org.
3. Prefer column filter over “owner’s matters” proxy once populated.

## Sovereign local search (LegalAIOrchestrator)
Verified wiring in `main.py`:

```python
legal_ai_orchestrator = LegalAIOrchestrator(
    ...,
    local_search=sovereign_legal_search,
)
```

Gate in `legal_ai_orchestrator.py` (~lines 190–194):

- Runs `local_search.search` when `self.local_search` is set **and** `response_mode != "quick"` **and** not `quick_document_evidence`.
- **Quick** intentionally skips local KB for latency.
- **Balanced / deep** already call sovereign local search when `local_search` is injected — no code change required for this day task.

### How to enable local KB
| Mode | Local sovereign search |
|------|------------------------|
| `quick` | Skipped (latency) |
| `balanced` | On (default path) |
| `deep` | On |

Pass `response_mode="balanced"` or `"deep"` on the chat/orchestrator call; ensure `sovereign_legal_search` remains passed into `LegalAIOrchestrator` (already done in `main.py` / `tasks.py`).

## Tests
```bash
cd backend
python -m pytest tests/test_org_access.py -q
```

## Not in scope
Full RBAC matrix (roles beyond membership), Matter schema migration, changing quick-mode latency tradeoff.
