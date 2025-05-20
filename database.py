from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends
from sqlalchemy.orm import Session

# 🔧 Replace these with your actual PostgreSQL credentials
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "123#"
POSTGRES_DB = "postgres"
POSTGRES_HOST = "localhost"  # or your remote host
POSTGRES_PORT = "5433"

# PostgreSQL connection string
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

#  SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#  Base class for all models
Base = declarative_base()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
