"""Add width and height columns to notes for resizing support.

Revision ID: 006_add_note_dimensions
Revises: 005_add_permission_to_shares
Create Date: 2024-01-29 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add width and height columns to notes table."""
    op.add_column(
        "notes",
        sa.Column("width", sa.Float(), nullable=False, server_default="200"),
    )
    op.add_column(
        "notes",
        sa.Column("height", sa.Float(), nullable=False, server_default="180"),
    )


def downgrade() -> None:
    """Remove width and height columns from notes table."""
    op.drop_column("notes", "height")
    op.drop_column("notes", "width")
