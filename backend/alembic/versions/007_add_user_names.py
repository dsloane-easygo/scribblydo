"""Add first_name and last_name columns to users table.

Revision ID: 007_add_user_names
Revises: 006_add_note_dimensions
Create Date: 2024-01-29 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add first_name and last_name columns to users table."""
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(100), nullable=True),
    )

    # Update test users with names
    op.execute(
        """
        UPDATE users
        SET first_name = 'Damian', last_name = 'Sloane'
        WHERE username = 'damian.sloane'
        """
    )
    op.execute(
        """
        UPDATE users
        SET first_name = 'Luke', last_name = 'Mcwha'
        WHERE username = 'luke.mcwha'
        """
    )
    op.execute(
        """
        UPDATE users
        SET first_name = 'Admin', last_name = 'User'
        WHERE username = 'admin'
        """
    )


def downgrade() -> None:
    """Remove first_name and last_name columns from users table."""
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
