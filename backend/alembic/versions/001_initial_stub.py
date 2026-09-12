"""Initial schema stub — empty upgrade.

Revision ID: 001_initial_stub
Revises:
Create Date: 2026-09-11

This revision intentionally does nothing. Existing databases already have
tables created via SQLAlchemy `Base.metadata.create_all` / app bootstrap.

Next steps:
  1. Point DATABASE_URL at Postgres
  2. alembic revision --autogenerate -m "sync_existing_schema"
  3. Review the generated upgrade() carefully before applying
  4. alembic upgrade head
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "001_initial_stub"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op baseline so Alembic history can start cleanly."""
    pass


def downgrade() -> None:
    """No-op baseline."""
    pass
