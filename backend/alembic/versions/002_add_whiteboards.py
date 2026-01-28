"""Add whiteboards table and whiteboard_id to notes.

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add whiteboards table and link notes to whiteboards."""
    # Create whiteboards table
    op.create_table(
        "whiteboards",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create a default whiteboard for existing notes
    op.execute(
        """
        INSERT INTO whiteboards (id, name)
        VALUES (gen_random_uuid(), 'Default')
        """
    )

    # Add whiteboard_id column to notes (nullable first)
    op.add_column(
        "notes",
        sa.Column(
            "whiteboard_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Set all existing notes to the default whiteboard
    op.execute(
        """
        UPDATE notes
        SET whiteboard_id = (SELECT id FROM whiteboards WHERE name = 'Default' LIMIT 1)
        """
    )

    # Make whiteboard_id non-nullable
    op.alter_column("notes", "whiteboard_id", nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_notes_whiteboard_id",
        "notes",
        "whiteboards",
        ["whiteboard_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create index on whiteboard_id
    op.create_index("ix_notes_whiteboard_id", "notes", ["whiteboard_id"])


def downgrade() -> None:
    """Remove whiteboards table and whiteboard_id from notes."""
    op.drop_index("ix_notes_whiteboard_id", table_name="notes")
    op.drop_constraint("fk_notes_whiteboard_id", "notes", type_="foreignkey")
    op.drop_column("notes", "whiteboard_id")
    op.drop_table("whiteboards")
