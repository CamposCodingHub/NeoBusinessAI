"""Conflict-of-interest screening for Intake leads (PMS must-have).

Scans Clients, Matters and other Leads of the same firm (user_id) for
name / email / phone matches. Pragmatic: exact email, digits-only phone,
normalized + fuzzy name.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from database import Client, Lead, Matter

logger = logging.getLogger(__name__)

NAME_FUZZY_THRESHOLD = 0.88
MIN_PHONE_DIGITS = 8
CONFLICT_NOTES_PREFIX = "[CONFLICT]"


@dataclass
class ConflictMatch:
    source: str  # client | matter | lead
    entity_id: int
    field: str  # name | email | phone | opposing_party
    value: str
    score: float = 1.0


@dataclass
class ConflictScreenResult:
    has_conflict: bool = False
    matches: List[ConflictMatch] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if not self.matches:
            return ""
        parts = [
            f"{m.source}#{m.entity_id} ({m.field}={m.value})"
            for m in self.matches[:12]
        ]
        return "Possível conflito: " + "; ".join(parts)


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_email(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_phone(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\D+", "", str(value))


def phones_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if len(a) < MIN_PHONE_DIGITS or len(b) < MIN_PHONE_DIGITS:
        return False
    if a == b:
        return True
    # BR / intl: compare last 8–9 digits
    return a[-9:] == b[-9:] or a[-8:] == b[-8:]


def names_match(a: str, b: str) -> Tuple[bool, float]:
    if not a or not b:
        return False, 0.0
    if a == b:
        return True, 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    if ratio >= NAME_FUZZY_THRESHOLD:
        return True, ratio
    # containment for longer names (e.g. "Ana Silva" vs "Ana Silva Santos")
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= 6 and shorter in longer:
        return True, 0.9
    return False, ratio


def _client_phone_plain(client: Client) -> str:
    try:
        from security.encryption import decrypt_field

        return decrypt_field(client.phone) or ""
    except Exception:
        return client.phone or ""


def screen_conflicts(
    db: Session,
    user_id: int,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    exclude_lead_id: Optional[int] = None,
) -> ConflictScreenResult:
    """Return matches against Clients, Matters and other Leads for this firm."""
    result = ConflictScreenResult()
    n_name = normalize_text(name)
    n_email = normalize_email(email)
    n_phone = normalize_phone(phone)

    if not n_name and not n_email and not n_phone:
        return result

    # --- Clients ---
    clients = db.query(Client).filter(Client.user_id == user_id).all()
    for client in clients:
        c_name = normalize_text(client.name)
        ok, score = names_match(n_name, c_name)
        if ok:
            result.matches.append(
                ConflictMatch("client", client.id, "name", client.name or "", score)
            )
        if n_email and normalize_email(client.email) == n_email:
            result.matches.append(
                ConflictMatch("client", client.id, "email", client.email or "")
            )
        c_phone = normalize_phone(_client_phone_plain(client))
        if phones_match(n_phone, c_phone):
            result.matches.append(
                ConflictMatch("client", client.id, "phone", c_phone)
            )

    # --- Matters (opposing party / title) ---
    matters = db.query(Matter).filter(Matter.user_id == user_id).all()
    for matter in matters:
        for field_name, raw in (
            ("opposing_party", matter.opposing_party),
            ("title", matter.title),
        ):
            ok, score = names_match(n_name, normalize_text(raw))
            if ok and n_name:
                result.matches.append(
                    ConflictMatch(
                        "matter",
                        matter.id,
                        field_name,
                        raw or "",
                        score,
                    )
                )

    # --- Other leads ---
    lead_q = db.query(Lead).filter(Lead.user_id == user_id)
    if exclude_lead_id is not None:
        lead_q = lead_q.filter(Lead.id != exclude_lead_id)
    for lead in lead_q.all():
        ok, score = names_match(n_name, normalize_text(lead.name))
        if ok:
            result.matches.append(
                ConflictMatch("lead", lead.id, "name", lead.name or "", score)
            )
        if n_email and normalize_email(lead.email) == n_email:
            result.matches.append(
                ConflictMatch("lead", lead.id, "email", lead.email or "")
            )
        if phones_match(n_phone, normalize_phone(lead.phone)):
            result.matches.append(
                ConflictMatch("lead", lead.id, "phone", normalize_phone(lead.phone))
            )

    # de-dupe by (source, id, field)
    seen = set()
    unique: List[ConflictMatch] = []
    for m in result.matches:
        key = (m.source, m.entity_id, m.field)
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)
    result.matches = unique
    result.has_conflict = bool(unique)
    if result.has_conflict:
        logger.info(
            "Conflict screen user=%s matches=%s",
            user_id,
            len(unique),
        )
    return result


def apply_conflict_on_create(
    lead: Lead,
    screen: ConflictScreenResult,
    manual_flag: bool = False,
) -> None:
    if screen.has_conflict:
        lead.conflict_flag = True
        lead.conflict_detail = screen.summary
        lead.notes = _merge_conflict_notes(lead.notes, screen.summary)
    else:
        lead.conflict_flag = bool(manual_flag)
        lead.conflict_detail = None


def apply_conflict_on_update(
    lead: Lead,
    screen: ConflictScreenResult,
    manual_flag: Optional[bool] = None,
) -> None:
    had_auto = bool(getattr(lead, "conflict_detail", None))
    if screen.has_conflict:
        lead.conflict_flag = True
        lead.conflict_detail = screen.summary
        lead.notes = _merge_conflict_notes(lead.notes, screen.summary)
        return

    lead.conflict_detail = None
    lead.notes = _strip_conflict_notes(lead.notes)
    if manual_flag is not None:
        lead.conflict_flag = bool(manual_flag)
    elif had_auto:
        # auto-flag cleared when identity no longer matches
        lead.conflict_flag = False


def _merge_conflict_notes(notes: Optional[str], summary: str) -> str:
    cleaned = _strip_conflict_notes(notes)
    block = f"{CONFLICT_NOTES_PREFIX} {summary}"
    if cleaned:
        return f"{block}\n{cleaned}"
    return block


def _strip_conflict_notes(notes: Optional[str]) -> Optional[str]:
    if not notes:
        return notes
    lines = [
        line
        for line in notes.splitlines()
        if not line.strip().startswith(CONFLICT_NOTES_PREFIX)
    ]
    joined = "\n".join(lines).strip()
    return joined or None
