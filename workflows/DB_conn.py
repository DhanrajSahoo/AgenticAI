from sqlalchemy import create_engine, Column, String, Text, JSON, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID


# 🔧 Replace these with your actual PostgreSQL credentials
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "12345"
POSTGRES_DB = "postgres"
POSTGRES_HOST = "localhost"  # or your remote host
POSTGRES_PORT = "5432"

# PostgreSQL connection string
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Workflow(Base):
    __tablename__ = "Workflow"
    workflows_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)  # Corrected import: Text instead of TEXT
    definition = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

class Tool(Base):
    __tablename__ = "Tools"
    tool_id = Column(Text, primary_key=True)
    tool_name = Column(Text, nullable=False)
    tool_description = Column(Text)
    parameters = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
        print("Connection established with the db", db)
    finally:
        db.close()