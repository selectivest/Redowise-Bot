from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///taskmanager.db')
print('Using database file:', os.path.abspath('taskmanager.db'))

def main():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print('--- All team_members ---')
        result = conn.execute(text("SELECT id, user_id, team_id, role FROM team_members;"))
        for row in result.fetchall():
            print(dict(row))

        print('\n--- All team_members with role Owner ---')
        result = conn.execute(text("SELECT id, user_id, team_id, role FROM team_members WHERE role = 'Owner' OR role = 'OWNER';"))
        for row in result.fetchall():
            print(dict(row))

        print('\n--- All teams (query used for task creation) ---')
        result = conn.execute(text("SELECT * FROM teams;"))
        for row in result.fetchall():
            print(dict(row))

if __name__ == '__main__':
    main() 