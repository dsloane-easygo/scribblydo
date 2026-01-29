"""Add access_type and whiteboard_shares table.

Revision ID: 004
Revises: 003
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the access_type enum
    access_type_enum = postgresql.ENUM('public', 'private', 'shared', name='accesstype', create_type=False)
    access_type_enum.create(op.get_bind(), checkfirst=True)

    # Add access_type column to whiteboards
    op.add_column(
        'whiteboards',
        sa.Column(
            'access_type',
            sa.Enum('public', 'private', 'shared', name='accesstype'),
            nullable=True,
        )
    )

    # Migrate existing data: is_private=true -> private, is_private=false -> public
    op.execute("""
        UPDATE whiteboards
        SET access_type = CASE
            WHEN is_private = true THEN 'private'::accesstype
            ELSE 'public'::accesstype
        END
    """)

    # Make access_type non-nullable with default
    op.alter_column('whiteboards', 'access_type', nullable=False, server_default='public')

    # Drop the is_private column
    op.drop_column('whiteboards', 'is_private')

    # Create whiteboard_shares table
    op.create_table(
        'whiteboard_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('whiteboard_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['whiteboard_id'], ['whiteboards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_whiteboard_shares_whiteboard_id', 'whiteboard_shares', ['whiteboard_id'])
    op.create_index('ix_whiteboard_shares_user_id', 'whiteboard_shares', ['user_id'])
    # Unique constraint to prevent duplicate shares
    op.create_unique_constraint('uq_whiteboard_shares_whiteboard_user', 'whiteboard_shares', ['whiteboard_id', 'user_id'])


def downgrade() -> None:
    # Drop whiteboard_shares table
    op.drop_constraint('uq_whiteboard_shares_whiteboard_user', 'whiteboard_shares', type_='unique')
    op.drop_index('ix_whiteboard_shares_user_id', table_name='whiteboard_shares')
    op.drop_index('ix_whiteboard_shares_whiteboard_id', table_name='whiteboard_shares')
    op.drop_table('whiteboard_shares')

    # Add is_private column back
    op.add_column(
        'whiteboards',
        sa.Column('is_private', sa.Boolean(), nullable=True, server_default='false')
    )

    # Migrate data back
    op.execute("""
        UPDATE whiteboards
        SET is_private = CASE
            WHEN access_type = 'private' THEN true
            ELSE false
        END
    """)

    op.alter_column('whiteboards', 'is_private', nullable=False)

    # Drop access_type column
    op.drop_column('whiteboards', 'access_type')

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS accesstype")
