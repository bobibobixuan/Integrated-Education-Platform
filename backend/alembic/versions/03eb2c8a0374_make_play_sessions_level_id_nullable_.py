"""make play_sessions level_id nullable for pvp

Revision ID: 03eb2c8a0374
Revises: 17bd3a6a2669
Create Date: 2026-05-27 21:37:44.544456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03eb2c8a0374'
down_revision: Union[str, Sequence[str], None] = '17bd3a6a2669'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('play_sessions') as batch_op:
        batch_op.alter_column('level_id', existing_type=sa.INTEGER(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('play_sessions') as batch_op:
        batch_op.alter_column('level_id', existing_type=sa.INTEGER(), nullable=False)
