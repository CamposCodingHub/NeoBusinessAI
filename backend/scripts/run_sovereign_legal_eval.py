"""Executa o gate local de qualidade do modelo juridico."""

import asyncio
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import settings
from database import SessionLocal, init_db
from sovereign_ai.evaluation import legal_model_evaluator


async def main():
    init_db()
    db = SessionLocal()
    try:
        dataset = (
            Path(__file__).resolve().parent.parent
            / "evals"
            / "legal_sovereign_v1.json"
        )
        result = await legal_model_evaluator.run(
            db,
            dataset_path=dataset,
            candidate_model=settings.LOCAL_AI_BALANCED_MODEL,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
