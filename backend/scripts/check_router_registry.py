#!/usr/bin/env python3
"""
CLI guard: ensure main.py still registers overnight/daytime routers.

Exit codes:
  0 — all required include_router / middleware / auth checks pass
  1 — one or more checks failed

Usage (from backend/):
  python scripts/check_router_registry.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from tests.test_router_registry import (  # noqa: E402
    REQUIRED_INCLUDE_ROUTERS,
    check_router_registry,
)


def main() -> int:
    failures = check_router_registry()
    if failures:
        print("FAIL: router registry check")
        for msg in failures:
            print(f"  - {msg}")
        print(
            "Required routers: "
            + ", ".join(REQUIRED_INCLUDE_ROUTERS)
        )
        return 1

    print("OK: router registry — all required include_router lines present")
    print("OK: setup_security_middleware(app) active")
    print("OK: GET /api/documents uses Depends(get_current_user)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
