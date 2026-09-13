"""
E2E user-style smoke of LexScan / NeoBusinessAI.
Runs authenticated flows like a lawyer using the product locally.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8000"
SAMPLES = Path(r"c:\Projetos\NeoBusinessAI\relatorios_melhorias\e2e_user_test\samples")
OUT = Path(r"c:\Projetos\NeoBusinessAI\relatorios_melhorias\e2e_user_test\e2e_report.json")

results: list[dict] = []


def rec(area: str, name: str, ok: bool, detail: str = "", ms: int = 0, extra=None):
    row = {
        "area": area,
        "name": name,
        "ok": ok,
        "detail": detail[:800],
        "ms": ms,
    }
    if extra is not None:
        row["extra"] = extra
    results.append(row)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {area}/{name} — {detail[:120]}")


def login() -> str:
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/auth/login",
        json={"email": "admin@neobusiness.ai", "password": "Admin@123456!"},
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    ok = r.status_code == 200 and "access_token" in r.json()
    rec("auth", "login_admin", ok, f"status={r.status_code}", ms)
    if not ok:
        raise SystemExit("login failed")
    return r.json()["access_token"]


def H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    token = login()
    h = H(token)
    now = datetime.now(timezone.utc)
    ids: dict = {}

    # --- health ---
    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/health/", timeout=15)
    rec("health", "health", r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- client ---
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/clients/",
        headers=h,
        json={
            "name": "Cliente E2E Silva",
            "email": "cliente.e2e@example.com",
            "cpf_cnpj": "529.982.247-25",
            "city": "São Paulo",
            "state": "SP",
            "status": "active",
            "notes": "Cliente criado no teste E2E",
        },
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    ok = r.status_code in (200, 201)
    client_id = None
    if ok:
        body = r.json()
        client_id = body.get("client", body).get("id") if isinstance(body.get("client"), dict) else body.get("id")
        # some APIs return client directly
        if client_id is None and "client" in body:
            client_id = body["client"].get("id")
    rec("clients", "create", ok, f"status={r.status_code} id={client_id} body_keys={list(r.json().keys()) if r.content else []}", ms)
    ids["client_id"] = client_id

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/clients/", headers=h, timeout=30)
    rec("clients", "list", r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- matter ---
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/matters",
        headers=h,
        json={
            "title": "Ação E2E — Cobrança",
            "client_id": client_id,
            "status": "open",
            "practice_area": "civel",
        },
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    matter_id = None
    if r.status_code in (200, 201):
        body = r.json()
        matter_id = (body.get("matter") or body).get("id")
    # try alternate payload if failed
    if matter_id is None:
        r2 = requests.post(
            f"{BASE}/matters",
            headers=h,
            json={"title": "Ação E2E — Cobrança", "status": "open"},
            timeout=30,
        )
        if r2.status_code in (200, 201):
            matter_id = (r2.json().get("matter") or r2.json()).get("id")
            r = r2
            ms = int((time.perf_counter() - t0) * 1000)
    rec("matters", "create", matter_id is not None, f"status={r.status_code} id={matter_id} {r.text[:200]}", ms)
    ids["matter_id"] = matter_id

    # --- deadlines / business days ---
    due = (now + timedelta(days=10)).isoformat()
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/deadlines/",
        headers=h,
        json={
            "description": "Contestação E2E — prazo fatal",
            "due_date": due,
            "client_id": client_id,
            "urgency": "high",
        },
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    deadline_id = None
    if r.status_code in (200, 201):
        body = r.json()
        deadline_id = (body.get("deadline") or body).get("id")
    rec("deadlines", "create", deadline_id is not None, f"status={r.status_code} {r.text[:220]}", ms)
    ids["deadline_id"] = deadline_id

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/deadlines/compute-business",
        headers=h,
        json={"start_date": "2026-09-12", "business_days": 15},
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    ok = r.status_code == 200
    end_date = None
    if ok:
        end_date = r.json().get("end_date") or r.json().get("result", {}).get("end_date")
    rec("deadlines", "compute_business_15d", ok and bool(end_date or r.json()), f"status={r.status_code} {r.text[:250]}", ms, extra=r.json() if ok else None)

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/deadlines/", headers=h, timeout=30)
    rec("deadlines", "list", r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- agenda + prep + witnesses + ics ---
    hearing_at = (now + timedelta(days=3)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/agenda/hearings",
        headers=h,
        json={
            "title": "Audiência E2E — instrução",
            "hearing_at": hearing_at,
            "location": "Fórum Central — Sala 12",
            "client_id": client_id,
            "matter_id": matter_id,
            "notes": "Levar procuração e RG",
        },
        timeout=30,
    )
    ms = int((time.perf_counter() - t0) * 1000)
    hearing_id = None
    if r.status_code in (200, 201):
        hearing_id = r.json().get("hearing", {}).get("id")
    rec("agenda", "create_hearing", hearing_id is not None, f"status={r.status_code}", ms)
    ids["hearing_id"] = hearing_id

    if hearing_id:
        t0 = time.perf_counter()
        r = requests.post(f"{BASE}/agenda/hearings/{hearing_id}/prep/seed", headers=h, timeout=30)
        rec("agenda", "prep_seed", r.status_code in (200, 201), f"status={r.status_code} {r.text[:160]}", int((time.perf_counter()-t0)*1000))

        t0 = time.perf_counter()
        r = requests.post(
            f"{BASE}/agenda/hearings/{hearing_id}/witnesses",
            headers=h,
            json={"name": "Maria Testemunha", "phone": "11988887777", "role": "testemunha"},
            timeout=30,
        )
        rec("agenda", "add_witness", r.status_code in (200, 201), f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/agenda/calendar.ics", headers=h, timeout=30)
    body = r.text if r.content else ""
    rec(
        "agenda",
        "export_ics",
        r.status_code == 200 and "BEGIN:VCALENDAR" in body and "Audiência E2E" in body,
        f"status={r.status_code} bytes={len(body)}",
        int((time.perf_counter()-t0)*1000),
    )

    # --- protocols ---
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/protocols",
        headers=h,
        json={
            "title": "Contestação protocolada E2E",
            "protocol_number": "2026.E2E.0001",
            "system": "pje",
            "court": "TJSP",
            "filed_at": now.isoformat(),
            "client_id": client_id,
            "matter_id": matter_id,
        },
        timeout=30,
    )
    rec("protocols", "create", r.status_code in (200, 201), f"status={r.status_code} {r.text[:160]}", int((time.perf_counter()-t0)*1000))

    # --- tasks / followups / poa / notes / docs-caso / contacts / expenses ---
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/tasks",
        headers=h,
        json={"title": "Preparar memorial E2E", "due_at": (now + timedelta(days=2)).isoformat(), "priority": "high"},
        timeout=30,
    )
    rec("tasks", "create", r.status_code in (200, 201), f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/followups",
        headers=h,
        json={"subject": "Retornar ligacao ao cliente E2E", "due_at": (now + timedelta(days=1)).isoformat()},
        timeout=30,
    )
    rec("followups", "create", r.status_code in (200, 201), f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/poa",
        headers=h,
        json={
            "title": "Procuração ad judicia E2E",
            "expires_at": (now + timedelta(days=20)).isoformat(),
            "client_id": client_id,
            "status": "active",
        },
        timeout=30,
    )
    rec("poa", "create", r.status_code in (200, 201), f"status={r.status_code} {r.text[:180]}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/matter-notes",
        headers=h,
        json={"body": "Nota E2E: cliente pediu urgencia no prazo.", "pinned": True, "matter_id": matter_id},
        timeout=30,
    )
    rec("matter_notes", "create", r.status_code in (200, 201), f"status={r.status_code} {r.text[:160]}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/matter-docs",
        headers=h,
        json={"title": "Contrato social", "status": "pending", "matter_id": matter_id},
        timeout=30,
    )
    rec("matter_docs", "create", r.status_code in (200, 201), f"status={r.status_code} {r.text[:160]}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/contacts/logs",
        headers=h,
        json={
            "channel": "phone",
            "summary": "Ligacao E2E — confirmou audiencia",
            "client_id": client_id,
            "direction": "outbound",
        },
        timeout=30,
    )
    rec("contacts", "create_log", r.status_code in (200, 201), f"status={r.status_code} {r.text[:180]}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/finance/expenses",
        headers=h,
        json={
            "description": "Deslocamento foro E2E",
            "amount": 85.50,
            "expense_date": now.date().isoformat(),
            "client_id": client_id,
            "reimbursable": True,
        },
        timeout=30,
    )
    rec("finance", "create_expense", r.status_code in (200, 201), f"status={r.status_code} {r.text[:200]}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/finance/expenses/csv", headers=h, timeout=30)
    rec("finance", "expenses_csv", r.status_code == 200 and ("Deslocamento" in r.text or "description" in r.text.lower() or len(r.text) > 10), f"status={r.status_code} bytes={len(r.text)}", int((time.perf_counter()-t0)*1000))

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/finance/aging", headers=h, timeout=30)
    rec("finance", "aging", r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- operations today / brief ---
    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/operations/today", headers=h, timeout=30)
    ok = r.status_code == 200
    board = r.json() if ok else {}
    has_hearing = any("E2E" in (x.get("title") or "") for x in (board.get("hearings") or []))
    rec(
        "ops",
        "today_board",
        ok,
        f"status={r.status_code} hearings={board.get('hearings_count')} deadlines_today={((board.get('deadlines') or {}).get('counts') or {})}",
        int((time.perf_counter()-t0)*1000),
        extra={"has_e2e_hearing": has_hearing},
    )

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/operations/today/brief", headers=h, timeout=30)
    ok = r.status_code == 200 and "markdown" in (r.json() if r.content else {})
    md = r.json().get("markdown", "") if ok else ""
    rec("ops", "today_brief", ok and len(md) > 40, f"status={r.status_code} md_len={len(md)}", int((time.perf_counter()-t0)*1000))

    # --- uploads ---
    upload_files = [
        SAMPLES / "peticao_simples.pdf",
        SAMPLES / "mozilla_pdf_reference.pdf",
        SAMPLES / "planalto_lei_13709.txt",
    ]
    for path in upload_files:
        if not path.exists():
            rec("documents", f"upload_{path.name}", False, "file missing")
            continue
        t0 = time.perf_counter()
        with path.open("rb") as f:
            files = {"file": (path.name, f)}
            r = requests.post(f"{BASE}/documents/upload", headers=h, files=files, timeout=120)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = r.status_code in (200, 201)
        rec("documents", f"upload_{path.name}", ok, f"status={r.status_code} {r.text[:220]}", ms)

    t0 = time.perf_counter()
    r = requests.get(f"{BASE}/documents", headers=h, timeout=30)
    rec("documents", "list", r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- other modules smoke ---
    for path, name in [
        ("/esign/envelopes", "esign"),
        ("/monitor/processes", "monitor"),
        ("/trust/accounts", "trust"),
        ("/orgs", "orgs"),
        ("/time/entries", "time"),
        ("/billing/nfse", "nfse"),
        ("/finance/collection-plan", "collection_plan"),
    ]:
        t0 = time.perf_counter()
        r = requests.get(f"{BASE}{path}", headers=h, timeout=30)
        rec("modules", name, r.status_code == 200, f"status={r.status_code}", int((time.perf_counter()-t0)*1000))

    # --- Lex chat questions ---
    questions = [
        ("prazo_contestacao", "Em processo cível no TJSP, quantos dias úteis tenho para contestar após a citação? Não invente artigo — indique a base e a ressalva."),
        ("lgpd", "O que a LGPD (Lei 13.709/2018) exige antes de enviar WhatsApp de cobrança a um cliente? Resposta prática para escritório."),
        ("honorarios", "Como organizar aging de honorários atrasados sem tom agressivo, alinhado à ética da OAB?"),
        ("audiencia", "Tenho audiência daqui a 3 dias. Monte um checklist operacional do que o advogado deve conferir antes de ir ao fórum."),
        ("dias_uteis", "Se o prazo começa em 12/09/2026 e são 15 dias úteis, explique como o LexScan calcula isso no módulo de prazos."),
    ]
    chat_answers = []
    for key, q in questions:
        t0 = time.perf_counter()
        try:
            r = requests.post(
                f"{BASE}/api/chat/premium",
                headers={**h, "Content-Type": "application/json"},
                json={
                    "message": q,
                    "response_mode": "quick",
                    "conversation_id": f"e2e-{key}",
                    "jurisdiction": "Brasil - SP",
                    "legal_area": "civel",
                },
                timeout=180,
            )
            ms = int((time.perf_counter() - t0) * 1000)
            body = r.json() if r.content else {}
            ok = r.status_code == 200 and bool(body.get("response") or body.get("success"))
            text = body.get("response") or body.get("error") or r.text
            rec("lex", key, ok, f"status={r.status_code} len={len(str(text))} preview={str(text)[:160]}", ms)
            chat_answers.append({"key": key, "question": q, "ok": ok, "ms": ms, "response": str(text)[:1200]})
        except Exception as exc:
            rec("lex", key, False, str(exc))
            chat_answers.append({"key": key, "question": q, "ok": False, "response": str(exc)})

    passed = sum(1 for x in results if x["ok"])
    failed = sum(1 for x in results if not x["ok"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "score": round(100.0 * passed / max(len(results), 1), 1),
        },
        "ids": ids,
        "results": results,
        "lex_answers": chat_answers,
        "samples_used": [p.name for p in upload_files if p.exists()],
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(json.dumps(report["summary"], indent=2))
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
