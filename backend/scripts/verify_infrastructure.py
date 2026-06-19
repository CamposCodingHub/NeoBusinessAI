"""Verifica dependencias locais sem imprimir credenciais."""

from __future__ import annotations

import json
import os
from pathlib import Path

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def check_database() -> dict:
    engine = create_engine(
        os.environ["DATABASE_URL"],
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"},
    )
    try:
        with engine.connect() as connection:
            return {
                "status": "healthy",
                "database": connection.execute(
                    text("select current_database()")
                ).scalar_one(),
                "encoding": connection.execute(
                    text("select current_setting('server_encoding')")
                ).scalar_one(),
            }
    finally:
        engine.dispose()


def check_redis() -> dict:
    client = redis.from_url(
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
        decode_responses=True,
        socket_connect_timeout=2,
    )
    key = "neobusiness:infrastructure-check"
    client.setex(key, 30, "ok")
    return {
        "status": "healthy" if client.get(key) == "ok" else "unhealthy",
        "persistence": client.config_get("appendonly").get("appendonly"),
    }


if __name__ == "__main__":
    result = {
        "database": check_database(),
        "redis": check_redis(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
