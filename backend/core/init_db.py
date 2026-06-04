# app/core/init_db.py

from sqlalchemy import text
from backend.core.database import engine

SCHEMAS = [
    "public",
    "crm",
    "finance",
    "hrm",
    "projects",
    "analytics",
    "ai",
    "auth",
    "audit",
    "notifications",
    "automation",
]

def create_schemas():
    with engine.connect() as connection:
        for schema in SCHEMAS:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        connection.commit()

    print("Schemas created successfully.")

if __name__ == "__main__":
    create_schemas()
