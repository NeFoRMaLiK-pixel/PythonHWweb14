# Модели базы данных для Contact Book.

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contacts = relationship("Contacts", back_populates="owner", cascade="all, delete-orphan")


class Contacts(Base):

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=False, index=True, nullable=False)
    phone = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    extra = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="contacts")