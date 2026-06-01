"""add story language and user read history

Revision ID: 9d7bce1b2f8c
Revises: 430e052f3b87
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d7bce1b2f8c'
down_revision: Union[str, None] = '430e052f3b87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('read_story_ids', sa.String(), nullable=True))
    op.add_column('stories', sa.Column('language', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('stories', 'language')
    op.drop_column('users', 'read_story_ids')
