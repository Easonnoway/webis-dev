"""
Database connection manager.
"""

import os
from typing import Generator

from sqlmodel import create_engine, Session, SQLModel

# Default to local SQLite for development
DATABASE_URL = os.environ.get("WEBIS_DB_URL", "sqlite:///webis.db")

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Initialize the database tables."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    with Session(engine) as session:
        yield session
