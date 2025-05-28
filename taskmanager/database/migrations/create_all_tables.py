"""Create all tables for the task manager bot."""

from sqlalchemy import text

def upgrade(connection):
    connection.execute(text('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            first_name VARCHAR,
            last_name VARCHAR,
            username VARCHAR UNIQUE,
            role VARCHAR,
            language_code VARCHAR DEFAULT 'en'
        );
    '''))
    connection.execute(text('''
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    '''))
    connection.execute(text('''
        CREATE TABLE team_members (
            id INTEGER PRIMARY KEY,
            team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR NOT NULL,
            CONSTRAINT uix_team_user UNIQUE (team_id, user_id)
        );
    '''))
    connection.execute(text('''
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            team_id INTEGER REFERENCES teams(id),
            creator_id INTEGER REFERENCES users(id),
            assignee_id INTEGER REFERENCES users(id),
            description VARCHAR,
            due_date DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR DEFAULT 'pending',
            media_file_id VARCHAR
        );
    '''))

def downgrade(connection):
    connection.execute(text('DROP TABLE IF EXISTS tasks;'))
    connection.execute(text('DROP TABLE IF EXISTS team_members;'))
    connection.execute(text('DROP TABLE IF EXISTS teams;'))
    connection.execute(text('DROP TABLE IF EXISTS users;')) 