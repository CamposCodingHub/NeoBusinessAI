"""
Guard against main.py dropping overnight / daytime routers.

Parses main.py as text (no uvicorn / full app import) so CI and local
pytest stay lightweight and do not pull the whole FastAPI stack.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = BACKEND_ROOT / "main.py"

# Overnight / daytime modules that previously vanished from main.py
REQUIRED_INCLUDE_ROUTERS = (
    "matter_router",
    "intake_router",
    "approvals_router",
    "time_router",
    "usage_router",
    "ai_audit_router",
    "org_router",
    "trust_router",
    "esign_router",
    "monitor_router",
    "agenda_router",
    "poa_router",
    "tasks_router",
    "contacts_router",
    "matter_docs_router",
    "matter_notes_router",
    "followups_router",
    "protocols_router",
    "compliance_router",
    "billing_router",
)


def load_main_source() -> str:
    assert MAIN_PY.is_file(), f"main.py not found at {MAIN_PY}"
    return MAIN_PY.read_text(encoding="utf-8")


def find_missing_include_routers(source: str) -> list[str]:
    missing: list[str] = []
    for name in REQUIRED_INCLUDE_ROUTERS:
        # Active include only — commented lines must not satisfy the check
        pattern = rf"(?m)^\s*app\.include_router\(\s*{re.escape(name)}\s*\)"
        if not re.search(pattern, source):
            missing.append(name)
    return missing


def security_middleware_is_active(source: str) -> bool:
    """True when setup_security_middleware(app) appears on a non-commented line."""
    return bool(
        re.search(r"(?m)^\s*setup_security_middleware\(\s*app\s*\)", source)
    )


def documents_list_uses_auth(source: str) -> bool:
    """
    Heuristic: @app.get("/api/documents") followed soon by Depends(get_current_user).
    """
    match = re.search(
        r'@app\.get\(\s*["\']/api/documents["\']\s*\)\s*\n'
        r'(?:.*\n){0,8}?'
        r'.*Depends\(\s*get_current_user\s*\)',
        source,
    )
    return match is not None


def check_router_registry(source: str | None = None) -> list[str]:
    """
    Return a list of human-readable failure messages (empty = OK).
    """
    text = source if source is not None else load_main_source()
    failures: list[str] = []

    missing = find_missing_include_routers(text)
    if missing:
        failures.append(
            "missing active include_router for: " + ", ".join(missing)
        )

    if not security_middleware_is_active(text):
        failures.append(
            "setup_security_middleware(app) missing or commented out"
        )

    if not documents_list_uses_auth(text):
        failures.append(
            'GET /api/documents must use Depends(get_current_user) nearby'
        )

    return failures


def test_required_overnight_routers_are_included():
    source = load_main_source()
    missing = find_missing_include_routers(source)
    assert not missing, (
        "main.py dropped required include_router lines: "
        + ", ".join(missing)
    )


def test_security_middleware_not_commented():
    source = load_main_source()
    assert security_middleware_is_active(source), (
        "setup_security_middleware(app) must be present and not commented"
    )


def test_documents_list_endpoint_requires_auth():
    source = load_main_source()
    assert documents_list_uses_auth(source), (
        'GET "/api/documents" should use Depends(get_current_user) nearby'
    )


def test_router_registry_all_checks():
    failures = check_router_registry()
    assert not failures, "router registry failures:\n- " + "\n- ".join(failures)
