# Overnight Security Hardening — 2026-09-11

## Changes

1. **Legacy API auth (JWT required)**  
   `/api/documents`, `/api/documents/{id}`, `/api/documents/{id}/chat`, `/api/documents/{id}/report`, `/api/deadlines`, `/api/dashboard/stats`, and `/api/reports/dashboard` now require `Depends(get_current_user)` and filter by `current_user.user_id`. Query `user_email` is no longer trusted for authorization.

2. **`/chat-stream`**  
   Requires JWT. Anonymous streaming removed; uses authenticated primary AI engine (`get_full_system_prompt` via `NeoBusinessAI.ask`).

3. **`verify_document_access` (fail-closed)**  
   In `backend/tools/security.py`: returns `False` unless ownership is proven via `user_id` (preferred) or legacy `uploaded_by` + email. Missing identity or owner fields ⇒ deny.

4. **SECRET_KEY / JWT**  
   - `backend/config.py`: production/staging reject weak/default `SECRET_KEY`; development warns.  
   - `backend/security/auth.py`: resolves `JWT_SECRET_KEY`/`SECRET_KEY` with the same policy (fail hard outside development).

5. **Middleware**  
   Re-enabled **security headers only** (`setup_security_headers_middleware`) to avoid double-CORS breakage. Full `setup_security_middleware` remains available with `include_cors=False` if needed later.

## Files touched

- `backend/main.py`
- `backend/tools/security.py`
- `backend/security/auth.py`
- `backend/config.py`
- `backend/middleware/security_middleware.py`
- `backend/middleware/__init__.py`
- `backend/test_security_fixes.py`
- `relatorios_melhorias/OVERNIGHT_20260911_SECURITY.md`
