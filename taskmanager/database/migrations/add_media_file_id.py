"""Add media_file_id column to tasks table."""

from sqlalchemy import text

# Up migration
def upgrade(connection):
    connection.execute(text("""
        ALTER TABLE tasks
        ADD COLUMN media_file_id VARCHAR;
    """))

# Down migration
def downgrade(connection):
    connection.execute(text("""
        ALTER TABLE tasks
        DROP COLUMN media_file_id;
    """)) 