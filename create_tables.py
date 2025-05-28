from taskmanager.database.models import Base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///taskmanager.db')

def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("All tables created.")

if __name__ == '__main__':
    main() 