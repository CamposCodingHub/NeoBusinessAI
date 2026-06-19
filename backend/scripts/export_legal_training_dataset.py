"""Exporta apenas exemplos anonimizados e aprovados para JSONL."""

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import SessionLocal, init_db
from sovereign_ai.training import training_dataset_service


def main():
    init_db()
    db = SessionLocal()
    try:
        output_dir = (
            Path(__file__).resolve().parent.parent
            / "runtime"
            / "training"
            / "legal-v1"
        )
        manifest = training_dataset_service.export_jsonl(
            db,
            output_dir=output_dir,
        )
        print(manifest)
    finally:
        db.close()


if __name__ == "__main__":
    main()
