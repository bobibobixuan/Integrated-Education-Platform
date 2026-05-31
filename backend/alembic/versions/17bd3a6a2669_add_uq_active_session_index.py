"""add_uq_active_session_index

Revision ID: 17bd3a6a2669
Revises: ce0c7c1d26e9
Create Date: 2026-05-26 19:34:29.009177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17bd3a6a2669'
down_revision: Union[str, Sequence[str], None] = 'ce0c7c1d26e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add partial unique index: at most one active session per (user, level)."""
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_active_session "
        "ON play_sessions(user_id, level_id) WHERE status = 'active'"
    )


def downgrade() -> None:
    """Drop the partial unique index."""
    op.execute("DROP INDEX IF EXISTS uq_active_session")
