"""add negotiation synthesis summary

Revision ID: 0002_add_negotiation_summary
Revises: 0001_initial_schema
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_negotiation_summary"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("negotiations", sa.Column("synthesis_summary", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("negotiations", "synthesis_summary")
