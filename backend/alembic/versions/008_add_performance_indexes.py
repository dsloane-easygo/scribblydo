"""Add performance indexes for query optimization.

Revision ID: 008_add_performance_indexes
Revises: 007_add_user_names
Create Date: 2025-01-29 12:00:00.000000

This migration adds indexes to improve query performance:
- whiteboards.access_type: Used in list_whiteboards WHERE clause
- whiteboards.created_at: Used for ORDER BY in listing
- notes.created_at: Used for ORDER BY in note listing
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    # Index on whiteboards.access_type for filtering by public/private/shared
    op.create_index(
        "ix_whiteboards_access_type",
        "whiteboards",
        ["access_type"],
        unique=False,
    )

    # Index on whiteboards.created_at for sorting (DESC is common)
    op.create_index(
        "ix_whiteboards_created_at",
        "whiteboards",
        ["created_at"],
        unique=False,
    )

    # Index on notes.created_at for sorting
    op.create_index(
        "ix_notes_created_at",
        "notes",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_notes_created_at", table_name="notes")
    op.drop_index("ix_whiteboards_created_at", table_name="whiteboards")
    op.drop_index("ix_whiteboards_access_type", table_name="whiteboards")
