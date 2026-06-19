"""Exercise document upload and analysis with generated extreme files."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

try:
    from .simulation_auth import create_simulation_access_token
except ImportError:
    from simulation_auth import create_simulation_access_token


API_URL = os.getenv("NEOBUSINESS_API_URL", "http://127.0.0.1:8000")
ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT_DIR / "backend" / "runtime" / "stress_documents"
REPORT_DIR = ROOT_DIR / "relatorios_melhorias" / "simulacoes"


def timed_request(method: str, url: str, **kwargs) -> tuple[requests.Response, float]:
    started_at = time.perf_counter()
    response = requests.request(method, url, timeout=kwargs.pop("timeout", 240), **kwargs)
    return response, round(time.perf_counter() - started_at, 3)


def upload(
    path: Path,
    token: str,
    expected_status: int,
) -> dict[str, Any]:
    with path.open("rb") as handle:
        response, latency = timed_request(
            "POST",
            f"{API_URL}/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (path.name, handle, "application/octet-stream")},
            timeout=300,
        )
    body = response.json() if response.content else {}
    return {
        "status": response.status_code,
        "expected_status": expected_status,
        "passed": response.status_code == expected_status,
        "latency_seconds": latency,
        "body": body,
    }


def analyze(
    document_id: int,
    token: str,
    expected_terminal_status: str = "completed",
) -> dict[str, Any]:
    response, enqueue_latency = timed_request(
        "POST",
        f"{API_URL}/documents/{document_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        timeout=600,
    )
    enqueue_body = response.json() if response.content else {}
    if response.status_code not in {200, 202}:
        return {
            "status": response.status_code,
            "expected_status": 202,
            "passed": False,
            "latency_seconds": enqueue_latency,
            "body": enqueue_body,
        }

    deadline = time.monotonic() + 600
    polls = 0
    status_body: dict[str, Any] = {}
    while time.monotonic() < deadline:
        polls += 1
        status_response = requests.get(
            f"{API_URL}/documents/{document_id}/processing-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        status_body = status_response.json() if status_response.content else {}
        if status_body.get("status") in {"completed", "error"}:
            break
        time.sleep(1)

    detail_response = requests.get(
        f"{API_URL}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    detail = detail_response.json() if detail_response.content else {}
    content = detail.get("content") or {}
    metadata = detail.get("metadata") or {}
    body = {
        "message": enqueue_body.get("message"),
        "document_id": document_id,
        "status": detail.get("status") or status_body.get("status"),
        "progress": status_body.get("progress"),
        "polls": polls,
        "error_message": detail.get("error_message"),
        "metadata": metadata,
        "summary_characters": len(
            str(detail.get("summary") or content.get("summary") or "")
        ),
        "analysis_characters": len(
            str(detail.get("analysis") or content.get("analysis") or "")
        ),
        "extracted_text_characters_returned": len(
            str(detail.get("content") or content.get("extracted_text") or "")
        ),
    }
    if expected_terminal_status == "completed":
        functional_analysis = (
            body["status"] == "completed"
            and body["summary_characters"] > 50
            and body["analysis_characters"] > 300
            and metadata.get("analysis_mode") != "failed"
        )
    else:
        functional_analysis = (
            body["status"] == expected_terminal_status
            and bool(body["error_message"])
        )
    return {
        "status": response.status_code,
        "expected_status": 202,
        "expected_terminal_status": expected_terminal_status,
        "passed": response.status_code in {200, 202} and functional_analysis,
        "latency_seconds": round(
            enqueue_latency + max(0, polls - 1),
            3,
        ),
        "body": body,
    }


def delete(document_id: Optional[int], token: str) -> None:
    if not document_id:
        return
    requests.delete(
        f"{API_URL}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )


def main() -> None:
    if not (FIXTURE_DIR / "manifest.json").exists():
        raise RuntimeError(
            "Fixtures ausentes. Execute scripts/generate_stress_documents.py primeiro."
        )

    token = create_simulation_access_token(
        API_URL,
        "document-stress",
        documents_limit=20,
    )
    scenarios = [
        ("large_txt", "atlas_12mb.txt", 200, "completed"),
        ("large_pdf", "atlas_250_paginas.pdf", 200, "completed"),
        ("large_docx", "atlas_9000_paragrafos.docx", 200, "completed"),
        ("large_rtf", "atlas_5mb.rtf", 200, "completed"),
        ("official_irpf", "receita_irpf_2026.pdf", 200, "completed"),
        ("page_limit_pdf", "acima_limite_501_paginas.pdf", 200, "error"),
        ("oversized", "acima_limite_51mb.txt", 413, None),
        ("disguised", "executavel_disfarcado.pdf", 400, None),
    ]
    results = []

    for name, filename, upload_status, analysis_status in scenarios:
        path = FIXTURE_DIR / filename
        if not path.exists() or not path.stat().st_size:
            results.append(
                {
                    "scenario": name,
                    "passed": False,
                    "error": "fixture ausente ou vazio",
                }
            )
            continue

        upload_result = upload(path, token, upload_status)
        document_id = (upload_result.get("body") or {}).get("document_id")
        analysis_result = None
        try:
            if upload_result["passed"] and analysis_status is not None and document_id:
                analysis_result = analyze(document_id, token, analysis_status)
        finally:
            delete(document_id, token)

        results.append(
            {
                "scenario": name,
                "file": filename,
                "size_bytes": path.stat().st_size,
                "upload": upload_result,
                "analysis": analysis_result,
                "passed": upload_result["passed"]
                and (analysis_result is None or analysis_result["passed"]),
            }
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"estresse_documentos_{timestamp}.json"
    markdown_path = REPORT_DIR / f"estresse_documentos_{timestamp}.md"
    payload = {
        "generated_at": datetime.now().isoformat(),
        "api_url": API_URL,
        "passed": sum(1 for result in results if result["passed"]),
        "total": len(results),
        "remote_ai_analyses": sum(
            1
            for result in results
            if ((result.get("analysis") or {}).get("body") or {})
            .get("metadata", {})
            .get("analysis_mode")
            == "remote_ai"
        ),
        "local_structured_analyses": sum(
            1
            for result in results
            if ((result.get("analysis") or {}).get("body") or {})
            .get("metadata", {})
            .get("analysis_mode")
            == "local_structured"
        ),
        "results": results,
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Estresse extremo de documentos",
        "",
        f"- Resultado: {payload['passed']}/{payload['total']} cenarios aprovados",
        f"- API: {API_URL}",
        "",
        "| Cenario | Tamanho | Upload | Analise | Resultado |",
        "|---|---:|---:|---:|---|",
    ]
    for result in results:
        upload_result = result.get("upload") or {}
        analysis_result = result.get("analysis") or {}
        lines.append(
            "| {scenario} | {size} | {upload} | {analysis} | {passed} |".format(
                scenario=result["scenario"],
                size=result.get("size_bytes", 0),
                upload=upload_result.get("status", "-"),
                analysis=analysis_result.get("status", "-"),
                passed="APROVADO" if result["passed"] else "FALHOU",
            )
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    if payload["passed"] != payload["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
