"""Curadoria e exportacao do dataset juridico supervisionado."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

from sqlalchemy.orm import Session

from database import FineTuningExample

SYSTEM_PROMPT = (
    "Voce e Lex Juris, copiloto juridico brasileiro. Responda com base nas "
    "fontes fornecidas, diferencie norma, interpretacao e aplicacao, nao "
    "invente referencias e indique necessidade de revisao profissional."
)


def redact_sensitive_data(text: str) -> str:
    """Remove identificadores desnecessarios antes de formar datasets."""
    value = text or ""
    replacements = (
        (r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "[CPF_REMOVIDO]"),
        (r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", "[CNPJ_REMOVIDO]"),
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[EMAIL_REMOVIDO]"),
        (r"\b(?:\+?55\s*)?\(?\d{2}\)?\s*\d{4,5}-?\d{4}\b", "[TELEFONE_REMOVIDO]"),
    )
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)
    return value


class TrainingDatasetService:
    def create_example(
        self,
        db: Session,
        *,
        source_type: str,
        domain: str,
        instruction: str,
        input_text: str,
        output_text: str,
        citations: list[dict] | list[str],
        custom_data: Dict[str, Any] | None = None,
    ) -> FineTuningExample:
        safe_instruction = redact_sensitive_data(instruction).strip()
        safe_input = redact_sensitive_data(input_text).strip()
        safe_output = redact_sensitive_data(output_text).strip()
        digest = hashlib.sha256(
            "\n".join(
                [domain, safe_instruction, safe_input, safe_output]
            ).encode("utf-8")
        ).hexdigest()
        existing = (
            db.query(FineTuningExample)
            .filter(FineTuningExample.content_hash == digest)
            .first()
        )
        if existing:
            return existing
        split_value = int(digest[:8], 16) % 100
        dataset_split = (
            "train" if split_value < 80 else
            "validation" if split_value < 90 else
            "test"
        )
        example = FineTuningExample(
            content_hash=digest,
            source_type=source_type,
            domain=domain,
            instruction=safe_instruction,
            input_text=safe_input,
            output_text=safe_output,
            citations=citations,
            custom_data=custom_data or {},
            review_status="pending",
            dataset_split=dataset_split,
        )
        db.add(example)
        db.commit()
        db.refresh(example)
        return example

    def review_example(
        self,
        db: Session,
        *,
        example_id: int,
        reviewer_id: int,
        approved: bool,
        quality_score: float,
        notes: str = "",
    ) -> FineTuningExample:
        example = db.query(FineTuningExample).filter(
            FineTuningExample.id == example_id
        ).first()
        if not example:
            raise ValueError("Exemplo nao encontrado")
        example.review_status = "approved" if approved else "rejected"
        example.reviewer_id = reviewer_id
        example.reviewer_notes = notes
        example.quality_score = quality_score
        example.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(example)
        return example

    def export_jsonl(
        self,
        db: Session,
        *,
        output_dir: Path,
        minimum_quality: float = 0.8,
    ) -> Dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        examples = (
            db.query(FineTuningExample)
            .filter(
                FineTuningExample.review_status == "approved",
                FineTuningExample.quality_score >= minimum_quality,
            )
            .order_by(FineTuningExample.id)
            .all()
        )
        counts = {"train": 0, "validation": 0, "test": 0}
        handles = {
            split: (output_dir / f"{split}.jsonl").open(
                "w",
                encoding="utf-8",
            )
            for split in counts
        }
        try:
            for example in examples:
                split = example.dataset_split or "train"
                if split not in handles:
                    split = "train"
                user_content = example.instruction
                if example.input_text:
                    user_content += f"\n\nCONTEXTO:\n{example.input_text}"
                payload = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": example.output_text},
                    ],
                    "metadata": {
                        "id": example.id,
                        "domain": example.domain,
                        "citations": example.citations or [],
                        "quality_score": example.quality_score,
                    },
                }
                handles[split].write(
                    json.dumps(payload, ensure_ascii=False) + "\n"
                )
                counts[split] += 1
        finally:
            for handle in handles.values():
                handle.close()
        manifest = {
            "generated_at": datetime.utcnow().isoformat(),
            "minimum_quality": minimum_quality,
            "counts": counts,
            "total": sum(counts.values()),
            "format": "messages-jsonl",
            "license_policy": (
                "Somente material autorizado, anonimizado e revisado."
            ),
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return manifest

    @staticmethod
    def stats(db: Session) -> Dict[str, int]:
        statuses = {}
        for status in ("pending", "approved", "rejected"):
            statuses[status] = (
                db.query(FineTuningExample)
                .filter(FineTuningExample.review_status == status)
                .count()
            )
        statuses["total"] = db.query(FineTuningExample).count()
        return statuses


training_dataset_service = TrainingDatasetService()
