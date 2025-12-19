print("Starting reset_db.py...")
import sys
import os

# Add current directory to path just in case
sys.path.append(os.getcwd())

print("Importing database...")
try:
    from app.db.database import engine, Base
    print("Imported database.")
except Exception as e:
    print(f"Failed to import database: {e}")
    sys.exit(1)

print("Importing models...")
try:
    from app.db.models import User, TrainingJob
    print("Imported models.")
except Exception as e:
    print(f"Failed to import models: {e}")
    sys.exit(1)

print("Resetting database tables (Drop All)...")
try:
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables.")
except Exception as e:
    print(f"Error dropping tables: {e}")
    sys.exit(1)

print("Creating all tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("Created all tables.")
    print("Database reset successfully!")
except Exception as e:
    print(f"Error creating tables: {e}")
    sys.exit(1)
