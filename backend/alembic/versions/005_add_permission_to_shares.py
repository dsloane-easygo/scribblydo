"""Add permission column to whiteboard_shares.

Revision ID: 005
Revises: 004
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the permission_level enum
    permission_enum = postgresql.ENUM('read', 'write', 'admin', name='permissionlevel', create_type=False)
    permission_enum.create(op.get_bind(), checkfirst=True)

    # Add permission column to whiteboard_shares with default 'write'
    op.add_column(
        'whiteboard_shares',
        sa.Column(
            'permission',
            sa.Enum('read', 'write', 'admin', name='permissionlevel'),
            nullable=True,
        )
    )

    # Set default value for existing shares
    op.execute("UPDATE whiteboard_shares SET permission = 'write' WHERE permission IS NULL")

    # Make the column non-nullable
    op.alter_column('whiteboard_shares', 'permission', nullable=False, server_default='write')


def downgrade() -> None:
    # Drop the permission column
    op.drop_column('whiteboard_shares', 'permission')

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS permissionlevel")
