"""Concurrent API benchmark for the persisted document processing queue."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

try:
    from .simulation_auth import create_simulation_access_token
except ImportError:
    from simulation_auth import create_simulation_access_token


API_URL = os.getenv("NEOBUSINESS_API_URL", "http://127.0.0.1:8000")
ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT_DIR / "backend" / "runtime" / "stress_documents"
REPORT_DIR = ROOT_DIR / "relatorios_melhorias" / "simulacoes"
FILES = [
    "atlas_12mb.txt",
    "atlas_250_paginas.pdf",
    "atlas_9000_paragrafos.docx",
    "atlas_5mb.rtf",
]


def upload(path: Path, token: str) -> dict[str, Any]:
    started_at = time.perf_counter()
    with path.open("rb") as handle:
        response = requests.post(
            f"{API_URL}/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (path.name, handle, "application/octet-stream")},
            timeout=300,
        )
    latency = round(time.perf_counter() - started_at, 3)
    response.raise_for_status()
    return {
        "file": path.name,
        "upload_latency_seconds": latency,
        **response.json(),
    }


def enqueue(document_id: int, token: str) -> dict[str, Any]:
    started_at = time.perf_counter()
    response = requests.post(
        f"{API_URL}/documents/{document_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    latency = round(time.perf_counter() - started_at, 3)
    response.raise_for_status()
    return {
        "enqueue_latency_seconds": latency,
        **response.json(),
    }


def status(document_id: int, token: str) -> dict[str, Any]:
    response = requests.get(
        f"{API_URL}/documents/{document_id}/processing-status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    token = create_simulation_access_token(API_URL, "async-queue-stress")
    fixtures = [FIXTURE_DIR / filename for filename in FILES]
    missing = [str(path) for path in fixtures if not path.exists()]
    if missing:
        raise RuntimeError(f"Fixtures ausentes: {missing}")

    with ThreadPoolExecutor(max_workers=len(fixtures)) as executor:
        uploads = list(executor.map(lambda path: upload(path, token), fixtures))

    with ThreadPoolExecutor(max_workers=len(uploads)) as executor:
        queued = list(
            executor.map(
                lambda item: enqueue(int(item["document_id"]), token),
                uploads,
            )
        )

    started_at = time.perf_counter()
    state: dict[int, dict[str, Any]] = {
        int(item["document_id"]): {
            "first_processing_seconds": None,
            "completed_seconds": None,
            "last_status": "queued",
            "progress_samples": [],
        }
        for item in uploads
    }
    timeout_at = time.monotonic() + 900
    while time.monotonic() < timeout_at:
        all_terminal = True
        for document_id, item in state.items():
            current = status(document_id, token)
            elapsed = round(time.perf_counter() - started_at, 3)
            item["last_status"] = current["status"]
            sample = {
                "elapsed_seconds": elapsed,
                "status": current["status"],
                "progress": current.get("progress", 0),
                "stage": current.get("processing_stage"),
            }
            if not item["progress_samples"] or (
                item["progress_samples"][-1]["status"],
                item["progress_samples"][-1]["progress"],
            ) != (sample["status"], sample["progress"]):
                item["progress_samples"].append(sample)
            if (
                current["status"] == "processing"
                and item["first_processing_seconds"] is None
            ):
                item["first_processing_seconds"] = elapsed
            if current["status"] in {"completed", "error"}:
                if item["completed_seconds"] is None:
                    item["completed_seconds"] = elapsed
                item["error_message"] = current.get("error_message")
                item["processing_time_ms"] = current.get("processing_time_ms")
            else:
                all_terminal = False
        if all_terminal:
            break
        time.sleep(1)

    for document_id in state:
        requests.delete(
            f"{API_URL}/documents/{document_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

    results = []
    queued_by_id = {
        int(item["document_id"]): item
        for item in queued
    }
    for upload_result in uploads:
        document_id = int(upload_result["document_id"])
        item = state[document_id]
        results.append(
            {
                **upload_result,
                **queued_by_id[document_id],
                **item,
                "passed": (
                    item["last_status"] == "completed"
                    and queued_by_id[document_id]["enqueue_latency_seconds"] < 3
                    and any(
                        sample["progress"] >= 10
                        for sample in item["progress_samples"]
                    )
                ),
            }
        )

    payload = {
        "generated_at": datetime.now().isoformat(),
        "api_url": API_URL,
        "documents": len(results),
        "passed": sum(result["passed"] for result in results),
        "total_elapsed_seconds": round(time.perf_counter() - started_at, 3),
        "results": results,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"estresse_fila_assincrona_{timestamp}.json"
    md_path = REPORT_DIR / f"estresse_fila_assincrona_{timestamp}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# Estresse da fila assincrona",
        "",
        f"- Aprovados: {payload['passed']}/{payload['documents']}",
        f"- Tempo total: {payload['total_elapsed_seconds']}s",
        "",
        "| Arquivo | Enfileirar | Inicio | Final | Estado |",
        "|---|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['file']} | {result['enqueue_latency_seconds']}s | "
            f"{result['first_processing_seconds']}s | "
            f"{result['completed_seconds']}s | {result['last_status']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": payload["passed"],
                "documents": payload["documents"],
                "total_elapsed_seconds": payload["total_elapsed_seconds"],
                "reports": [str(json_path), str(md_path)],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    if payload["passed"] != payload["documents"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
