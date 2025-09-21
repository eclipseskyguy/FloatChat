import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

# Get the database URL from the environment
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ Error: DATABASE_URL not found. Make sure you have a .env file with the correct variable.")
else:
    try:
        # Create a connection engine
        engine = create_engine(db_url)

        # Try to connect
        with engine.connect() as connection:
            print("✅ Connection to the database was successful!")
            print("PostgreSQL Version:", connection.execute(text("SELECT version()")).scalar())

    except Exception as e:
        print(f"❌ Failed to connect to the database. Error: {e}")