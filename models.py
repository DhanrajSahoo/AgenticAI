from sqlalchemy import Column, String, Text
from database import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, index=True)
    entity_type = Column(String, index=True)
    data = Column(Text)  # Stores JSON as a string
