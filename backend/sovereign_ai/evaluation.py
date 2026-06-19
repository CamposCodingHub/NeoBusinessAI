"""Benchmark local e gate de promocao de modelos."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from database import AIEvaluationRun
from sovereign_ai.gateway import SovereignAIGateway
from sovereign_ai.search import normalize_text


class LegalModelEvaluator:
    def __init__(self, gateway: SovereignAIGateway | None = None):
        self.gateway = gateway or SovereignAIGateway()

    async def run(
        self,
        db: Session,
        *,
        dataset_path: Path,
        candidate_model: str,
    ) -> Dict[str, Any]:
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
        run_id = uuid.uuid4().hex
        run = AIEvaluationRun(
            run_id=run_id,
            dataset_name=dataset["name"],
            dataset_version=dataset["version"],
            candidate_provider="local-primary",
            candidate_model=candidate_model,
            status="running",
        )
        db.add(run)
        db.commit()

        results: List[Dict[str, Any]] = []
        for case in dataset["cases"]:
            response = await self.gateway.create_chat_completion(
                model=candidate_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "MODO DE TRABALHO PROFISSIONAL JURIDICO. "
                            "Use as fontes oficiais fornecidas e cite-as. "
                            + case.get(
                                "system",
                                "Voce e um copiloto de pesquisa juridica.",
                            )
                        ),
                    },
                    {"role": "user", "content": case["prompt"]},
                ],
                max_tokens=int(case.get("max_tokens", 500)),
                temperature=0.1,
                top_p=0.9,
            )
            answer = response.choices[0].message.content
            result = self._score_case(case, answer)
            result.update(
                {
                    "id": case["id"],
                    "latency_ms": response.latency_ms,
                    "model": response.model,
                    "provider": response.provider,
                    "answer_excerpt": answer[:1200],
                }
            )
            results.append(result)

        score = (
            sum(item["score"] for item in results) / len(results)
            if results else 0
        )
        critical_failures = sum(
            bool(item["critical_failure"]) for item in results
        )
        metrics = {
            "average_score": round(score, 6),
            "critical_failures": critical_failures,
            "cases": len(results),
            "average_latency_ms": round(
                sum(item["latency_ms"] for item in results)
                / max(1, len(results)),
                2,
            ),
            "promotion_threshold": 0.78,
        }
        run.status = (
            "approved"
            if score >= 0.78 and critical_failures == 0
            else "rejected"
        )
        run.score = score
        run.metrics = metrics
        run.results = results
        run.completed_at = datetime.utcnow()
        db.commit()
        return {
            "run_id": run_id,
            "status": run.status,
            "score": score,
            "metrics": metrics,
            "results": results,
        }

    @staticmethod
    def _score_case(case: Dict[str, Any], answer: str) -> Dict[str, Any]:
        normalized = normalize_text(answer)
        required = [
            normalize_text(term) for term in case.get("required_terms", [])
        ]
        forbidden = [
            normalize_text(term) for term in case.get("forbidden_terms", [])
        ]
        required_hits = sum(term in normalized for term in required)
        forbidden_hits = [
            term for term in forbidden if term in normalized
        ]
        term_score = required_hits / max(1, len(required))
        citation_required = bool(case.get("citation_required"))
        citation_present = bool(
            re.search(r"\[(?:fonte|base local)\s+\d+\]", answer, re.I)
        )
        citation_score = (
            1.0 if not citation_required or citation_present else 0.0
        )
        structure_score = min(1.0, len(answer.strip()) / 500)
        no_leak = not any(
            marker in normalized
            for marker in (
                "system prompt",
                "instrucoes internas",
                "chave de api",
            )
        )
        score = (
            term_score * 0.45
            + citation_score * 0.25
            + structure_score * 0.15
            + (1.0 if no_leak else 0.0) * 0.15
        )
        critical_failure = bool(forbidden_hits) or not no_leak
        return {
            "score": round(score, 6),
            "required_hits": required_hits,
            "required_total": len(required),
            "forbidden_hits": forbidden_hits,
            "citation_present": citation_present,
            "critical_failure": critical_failure,
        }


legal_model_evaluator = LegalModelEvaluator()
