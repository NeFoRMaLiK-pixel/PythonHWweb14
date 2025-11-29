"""
Модели базы данных для приложения Contact Book.
Этот модуль содержит SQLAlchemy модели для пользователей и контактов.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """
    Модель пользователя системы.
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Email адрес пользователя (уникальный)
        hashed_password (str): Хэшированный пароль
        is_verified (bool): Флаг верификации email
        verification_token (str): Токен для верификации email
        reset_token (str): Токен для сброса пароля
        reset_token_expires (datetime): Время истечения токена сброса
        avatar_url (str): URL аватара из Cloudinary
        created_at (datetime): Дата создания аккаунта
        contacts (list[Contacts]): Список контактов пользователя
    """
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
    """
    Модель контакта в адресной книге.
    
    Attributes:
        id (int): Уникальный идентификатор контакта
        name (str): Имя контакта
        surname (str): Фамилия контакта
        email (str): Email контакта
        phone (str): Номер телефона
        birthday (date): Дата рождения
        extra (str): Дополнительная информация
        user_id (int): ID владельца контакта
        created_at (datetime): Дата создания контакта
        owner (User): Владелец контакта
    """
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