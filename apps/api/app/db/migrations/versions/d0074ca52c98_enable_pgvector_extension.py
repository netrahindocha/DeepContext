"""enable pgvector extension

Revision ID: d0074ca52c98
Revises: 8a12a1e785bf
Create Date: 2026-06-15 11:56:20.915011

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d0074ca52c98"
down_revision: Union[str, Sequence[str], None] = "8a12a1e785bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
