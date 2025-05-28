from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///taskmanager.db')

def main():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print('--- All team_members with role Owner ---')
        result = conn.execute(text("SELECT id, user_id, team_id, role FROM team_members WHERE role = 'Owner' OR role = 'OWNER';"))
        owners = result.fetchall()
        for row in owners:
            print(f"ID: {row[0]}, User ID: {row[1]}, Team ID: {row[2]}, Role: {row[3]}")
        if not owners:
            print('No owners found in team_members table.')

        print('\n--- All teams ---')
        result = conn.execute(text("SELECT * FROM teams;"))
        for row in result.fetchall():
            print(f"ID: {row[0]}, Name: {row[1]}, Created at: {row[2]}")

        print('\n--- All users ---')
        result = conn.execute(text("SELECT * FROM users;"))
        for row in result.fetchall():
            print(f"ID: {row[0]}, Telegram ID: {row[1]}, Username: {row[3]}, Role: {row[5]}")

if __name__ == '__main__':
    main() 