"""Coleta e indexa fontes oficiais na base juridica local."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from database import SessionLocal, init_db
from sovereign_ai.search import sovereign_legal_search


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codes",
        nargs="+",
        default=["CF88", "CP", "CPP", "CC", "CPC"],
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--with-embeddings", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        results = await sovereign_legal_search.bootstrap_official_sources(
            db,
            source_codes=args.codes,
            force=args.force,
            generate_embeddings=args.with_embeddings,
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
        print(json.dumps(sovereign_legal_search.stats(db), indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
