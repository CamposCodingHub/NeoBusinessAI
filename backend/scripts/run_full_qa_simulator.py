#!/usr/bin/env python3
"""Simulador QA LexScan — saude, auth, modulos, seguranca e tom da Lex.

Gera relatorio em relatorios_melhorias/simulacoes/qa_full_simulator_YYYYMMDD_HHMMSS.json

Uso:
  cd backend
  python scripts/run_full_qa_simulator.py
  python scripts/run_full_qa_simulator.py --base-url http://127.0.0.1:8000
  python scripts/run_full_qa_simulator.py --email user@example.com --password 'Senha'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)

try:
    from .simulation_auth import create_simulation_access_token
except ImportError:
    from simulation_auth import create_simulation_access_token

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "relatorios_melhorias" / "simulacoes"

ROBOTIC = [
    r"(?i)^\s*(claro|certamente|excelente pergunta|entendi perfeitamente)[!.,]?\b",
    r"(?i)reflex[aã]o final",
    r"(?i)aqui est[aá] o que (eu )?pensei",
    r"(?i)como posso ajudar",
    r"(?i)como (seu|sua) (assistente|copiloto).{0,40}posso ajudar",
    r"[🎯💡✨🚀💭📊🔍✅👋]",
]


@dataclass
class Check:
    suite: str
    name: str
    passed: bool
    detail: str = ""
    latency_ms: int = 0
    score: Optional[float] = None


@dataclass
class Report:
    started_at: str
    base_url: str
    checks: List[Check] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    @property
    def score(self) -> float:
        if not self.checks:
            return 0.0
        vals = [
            c.score if c.score is not None else (100.0 if c.passed else 0.0)
            for c in self.checks
        ]
        return round(sum(vals) / len(vals), 1)


class QA:
    def __init__(self, base: str, email: Optional[str], password: Optional[str]):
        self.base = base.rstrip("/")
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.client = httpx.Client(timeout=45.0, follow_redirects=False)
        self.report = Report(
            started_at=datetime.now(timezone.utc).isoformat(),
            base_url=self.base,
        )

    def close(self) -> None:
        self.client.close()

    def add(self, c: Check) -> None:
        print(f"[{'PASS' if c.passed else 'FAIL'}] {c.suite}/{c.name} — {c.detail[:140]}")
        self.report.checks.append(c)

    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path: str, auth: bool = False) -> httpx.Response:
        return self.client.get(
            f"{self.base}{path}",
            headers=self.headers() if auth else {},
        )

    def post(self, path: str, payload: Dict[str, Any], auth: bool = False) -> httpx.Response:
        return self.client.post(
            f"{self.base}{path}",
            headers=self.headers() if auth else {"Content-Type": "application/json"},
            json=payload,
        )

    def _first_status(
        self,
        paths: Sequence[str],
        *,
        auth: bool = False,
        want: int = 200,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[httpx.Response], str, int]:
        """Try path variants (prefer trailing-slash where registered)."""
        last: Optional[httpx.Response] = None
        used = paths[0] if paths else ""
        t0 = time.perf_counter()
        for path in paths:
            used = path
            for attempt in range(3):
                if method.upper() == "POST":
                    last = self.post(path, payload or {}, auth=auth)
                else:
                    last = self.get(path, auth=auth)
                if last.status_code == want:
                    latency = int((time.perf_counter() - t0) * 1000)
                    return last, used, latency
                # Brief backoff on rate-limit so suite order doesn't flake
                if last.status_code == 429 and attempt < 2:
                    time.sleep(1.2 * (attempt + 1))
                    continue
                break
        latency = int((time.perf_counter() - t0) * 1000)
        return last, used, latency

    def suite_health(self) -> None:
        probes = [
            (["/health/", "/health"], "health"),
            (["/health/ready"], "ready"),
            (["/api/ai/status"], "ai_status"),
        ]
        for paths, name in probes:
            try:
                r, _used, latency = self._first_status(paths, want=200)
                assert r is not None
                self.add(
                    Check(
                        "health",
                        name,
                        r.status_code == 200,
                        f"status={r.status_code}",
                        latency,
                    )
                )
            except Exception as exc:
                self.add(Check("health", name, False, str(exc)))

    def suite_auth(self) -> None:
        t0 = time.perf_counter()
        try:
            if self.email and self.password:
                r = self.post(
                    "/auth/login",
                    {"email": self.email, "password": self.password},
                )
                data = (
                    r.json()
                    if "json" in r.headers.get("content-type", "")
                    else {}
                )
                token = data.get("access_token") or data.get("token")
                ok = r.status_code == 200 and bool(token)
                if ok:
                    self.token = str(token)
                self.add(
                    Check(
                        "auth",
                        "login",
                        ok,
                        f"status={r.status_code}",
                        int((time.perf_counter() - t0) * 1000),
                    )
                )
                return

            # Overnight path: register a throwaway user via simulation_auth
            token = create_simulation_access_token(self.base, "qa-full")
            self.token = token
            self.add(
                Check(
                    "auth",
                    "login",
                    bool(token),
                    "status=200",
                    int((time.perf_counter() - t0) * 1000),
                )
            )
        except Exception as exc:
            self.add(Check("auth", "login", False, str(exc)))

    def suite_modules(self) -> None:
        # Prefer trailing-slash variants when redirect_slashes=False.
        # Intake/approvals list under nested paths (not bare /intake|/approvals).
        endpoints: List[Tuple[List[str], str]] = [
            (["/clients/", "/clients"], "clients"),
            (["/deadlines/", "/deadlines"], "deadlines"),
            (["/documents", "/documents/"], "documents"),
            (["/matters", "/matters/"], "matters"),
            (["/intake/leads", "/intake", "/intake/"], "intake"),
            (["/approvals/outbound", "/approvals", "/approvals/"], "approvals"),
            (["/time/entries", "/time", "/time/"], "time"),
            (["/usage/me"], "usage"),
            (["/ai/audit"], "ai_audit"),
            (["/operations/shortcuts"], "ops_shortcuts"),
            (["/operations/activity"], "ops_activity"),
            (["/operations/today"], "ops_today"),
            (["/orgs", "/orgs/"], "orgs"),
            (["/trust/accounts", "/trust/accounts/"], "trust"),
            (["/esign/envelopes", "/esign/envelopes/"], "esign"),
            (["/monitor/processes", "/monitor/processes/"], "monitor"),
            (["/agenda/hearings", "/agenda/hearings/"], "agenda"),
            (["/poa", "/poa/"], "poa"),
            (["/finance/aging"], "aging"),
            (["/billing/nfse", "/billing/nfse/"], "nfse"),
        ]
        for paths, name in endpoints:
            if not self.token:
                self.add(Check("modules", name, False, "sem token"))
                continue
            try:
                r, _used, latency = self._first_status(paths, auth=True, want=200)
                assert r is not None
                self.add(
                    Check(
                        "modules",
                        name,
                        r.status_code == 200,
                        f"status={r.status_code}",
                        latency,
                    )
                )
            except Exception as exc:
                self.add(Check("modules", name, False, str(exc)))

        # Optional: business-days helper smoke (auth POST)
        if not self.token:
            self.add(Check("modules", "compute_business", False, "sem token"))
        else:
            t0 = time.perf_counter()
            try:
                r = self.post(
                    "/deadlines/compute-business",
                    {"start_date": "2026-09-12", "business_days": 15},
                    auth=True,
                )
                ok = r.status_code == 200 and bool(
                    (r.json() or {}).get("due_date") if "json" in r.headers.get("content-type", "") else False
                )
                self.add(
                    Check(
                        "modules",
                        "compute_business",
                        ok,
                        f"status={r.status_code}",
                        int((time.perf_counter() - t0) * 1000),
                    )
                )
            except Exception as exc:
                self.add(Check("modules", "compute_business", False, str(exc)))

    def suite_security(self) -> None:
        t0 = time.perf_counter()
        try:
            r = self.get("/api/documents")
            ok = r.status_code == 401
            self.add(
                Check(
                    "security",
                    "docs_unauth",
                    ok,
                    f"status={r.status_code}",
                    int((time.perf_counter() - t0) * 1000),
                    100 if ok else 0,
                )
            )
        except Exception as exc:
            self.add(Check("security", "docs_unauth", False, str(exc)))

        t0 = time.perf_counter()
        try:
            # Prefer POST (legacy chat-stream); also accept GET 401.
            r = self.post("/chat-stream", {"message": "ping"})
            if r.status_code != 401:
                r_get = self.get("/chat-stream")
                if r_get.status_code == 401:
                    r = r_get
            ok = r.status_code == 401
            self.add(
                Check(
                    "security",
                    "chat_stream_auth",
                    ok,
                    f"status={r.status_code}",
                    int((time.perf_counter() - t0) * 1000),
                    100 if ok else 0,
                )
            )
        except Exception as exc:
            self.add(Check("security", "chat_stream_auth", False, str(exc)))

    def _score_tone(self, text: str) -> Tuple[float, List[str]]:
        hits = [p for p in ROBOTIC if re.search(p, text)]
        score = 100.0 - 20.0 * len(hits)
        emoji_count = len(re.findall(r"[\U0001F300-\U0001FAFF]", text))
        if emoji_count >= 3:
            hits.append("excessive_emoji")
            score -= 20.0
        return max(0.0, min(100.0, score)), hits

    def suite_ai(self) -> None:
        if not self.token:
            self.add(Check("ai", "tone", False, "sem token"))
            return
        t0 = time.perf_counter()
        try:
            r = self.post(
                "/api/chat/premium",
                {
                    "message": (
                        "Liste riscos praticos de um prazo processual "
                        "de 15 dias uteis no escritorio."
                    ),
                    "conversation_id": f"qa-{int(time.time())}",
                    "response_mode": "quick",
                },
                auth=True,
            )
            data = r.json() if r.status_code == 200 else {}
            answer = data.get("response") or data.get("answer") or ""
            score, hits = self._score_tone(answer)
            # score=100 when no robotic fillers; pass threshold mirrors overnight (>=60)
            ok = r.status_code == 200 and score >= 60
            score_disp = int(score) if score == int(score) else score
            self.add(
                Check(
                    "ai",
                    "tone",
                    ok,
                    f"status={r.status_code} score={score_disp} hits={hits[:2]}",
                    int((time.perf_counter() - t0) * 1000),
                    float(score),
                )
            )
        except Exception as exc:
            self.add(Check("ai", "tone", False, str(exc)))

    def run(self) -> Report:
        print(f"\n=== QA Simulator ===\n{self.base}\n")
        self.suite_health()
        self.suite_auth()
        self.suite_modules()
        self.suite_security()
        self.suite_ai()
        return self.report

    def save(self) -> Path:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = REPORT_DIR / f"qa_full_simulator_{stamp}.json"
        payload = {
            "started_at": self.report.started_at,
            "base_url": self.report.base_url,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "score": self.report.score,
            "checks": [asdict(c) for c in self.report.checks],
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"\nSummary: passed={self.report.passed} failed={self.report.failed} "
            f"score={self.report.score}\n{out}\n"
        )
        return out


def main() -> int:
    p = argparse.ArgumentParser(description="Simulador QA completo LexScan")
    p.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
    )
    p.add_argument("--email", default=os.getenv("QA_EMAIL"))
    p.add_argument("--password", default=os.getenv("QA_PASSWORD"))
    args = p.parse_args()
    qa = QA(args.base_url, args.email, args.password)
    try:
        qa.run()
        qa.save()
        return 0 if qa.report.failed == 0 else 1
    finally:
        qa.close()


if __name__ == "__main__":
    sys.exit(main())
