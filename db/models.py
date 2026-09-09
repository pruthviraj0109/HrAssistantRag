from sqlalchemy import Column, INTEGER, String, DateTime
from sqlalchemy.sql import func
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(INTEGER, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
