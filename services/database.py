from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from utils.config import DB_URL

Base = declarative_base()

_normalized_url = (
    DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    if DB_URL.startswith("postgresql://")
    else DB_URL
)

engine = create_engine(_normalized_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_connection():
    return SessionLocal()