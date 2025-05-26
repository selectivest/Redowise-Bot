"""Add media columns to tasks table

Revision ID: add_media_columns
Revises: previous_migration
Create Date: 2024-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_media_columns'
down_revision: Union[str, None] = 'previous_migration'  # Update this to your last migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add media columns to tasks table
    op.add_column('tasks', sa.Column('media_type', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('media_file_id', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('media_caption', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove media columns from tasks table
    op.drop_column('tasks', 'media_caption')
    op.drop_column('tasks', 'media_file_id')
    op.drop_column('tasks', 'media_type') 