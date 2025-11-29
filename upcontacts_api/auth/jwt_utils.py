from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User

# Настройка для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет совпадение пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_email(db: Session, email: str):
    """Находит пользователя по email"""
    return db.query(User).filter(User.email == email).first()
