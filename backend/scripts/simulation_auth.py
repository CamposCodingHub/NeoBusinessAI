"""Autenticacao compartilhada pelos simuladores locais da API."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def create_simulation_access_token(
    api_url: str,
    prefix: str,
    *,
    documents_limit: int | None = None,
) -> str:
    email = f"{prefix}-{int(time.time() * 1000)}@example.com"
    payload = {
        "email": email,
        "password": "SenhaForte123!",
        "name": f"Simulacao {prefix}",
    }
    request = urllib.request.Request(
        f"{api_url}/auth/register",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body: dict[str, Any] = json.loads(
                response.read().decode("utf-8")
            )
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Falha ao autenticar simulacao: HTTP {exc.code}: {error_body}"
        ) from exc

    access_token = str(body.get("access_token") or "")
    if not access_token:
        raise RuntimeError("Registro da simulacao nao retornou access token")

    if documents_limit is not None:
        user_id = body.get("user_id")
        if not user_id:
            raise RuntimeError(
                "Registro da simulacao nao retornou user_id para elevar limite local"
            )
        backend_dir = str(Path(__file__).resolve().parents[1])
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from database import SessionLocal, User

        with SessionLocal() as session:
            user = session.query(User).filter(User.id == int(user_id)).first()
            if not user:
                raise RuntimeError("Usuario local da simulacao nao foi encontrado")
            user.plan_tier = "enterprise"
            user.subscription_status = "active"
            user.documents_limit = documents_limit
            session.commit()

    return access_token
