"""Add users table and whiteboard privacy/ownership.

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users table and whiteboard ownership/privacy fields."""
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create index on username for fast lookups
    op.create_index("ix_users_username", "users", ["username"])

    # Create a default user for existing whiteboards
    # Password is 'admin' hashed with bcrypt
    op.execute(
        """
        INSERT INTO users (id, username, password_hash)
        VALUES (
            gen_random_uuid(),
            'admin',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.V6OJF8OYI.i0EK'
        )
        """
    )

    # Add owner_id column to whiteboards (nullable first)
    op.add_column(
        "whiteboards",
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Add is_private column to whiteboards
    op.add_column(
        "whiteboards",
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Set all existing whiteboards to the admin user
    op.execute(
        """
        UPDATE whiteboards
        SET owner_id = (SELECT id FROM users WHERE username = 'admin' LIMIT 1)
        """
    )

    # Make owner_id non-nullable
    op.alter_column("whiteboards", "owner_id", nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_whiteboards_owner_id",
        "whiteboards",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create index on owner_id
    op.create_index("ix_whiteboards_owner_id", "whiteboards", ["owner_id"])


def downgrade() -> None:
    """Remove users table and whiteboard ownership/privacy fields."""
    op.drop_index("ix_whiteboards_owner_id", table_name="whiteboards")
    op.drop_constraint("fk_whiteboards_owner_id", "whiteboards", type_="foreignkey")
    op.drop_column("whiteboards", "is_private")
    op.drop_column("whiteboards", "owner_id")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
