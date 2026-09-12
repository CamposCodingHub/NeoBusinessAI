"""Carrega o playbook profissional interno (truncado para system_context)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PLAYBOOK_PATH = Path(__file__).resolve().parent / "professional_playbook.md"
DEFAULT_MAX_CHARS = 2000


@lru_cache(maxsize=4)
def load_professional_playbook(max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Retorna o playbook interno, limitado a max_chars caracteres."""
    if max_chars <= 0:
        return ""
    text = PLAYBOOK_PATH.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n..."


def playbook_exists() -> bool:
    return PLAYBOOK_PATH.is_file()
