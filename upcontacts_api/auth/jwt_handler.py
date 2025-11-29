"""JWT токены: создание и проверка."""

import os
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()  # загружаем переменные окружения из .env

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Создает JWT access токен.
    
    Args:
        data (dict): Данные для кодирования (обычно {"sub": email})
        expires_delta (timedelta, optional): Время жизни токена
        
    Returns:
        str: Закодированный JWT токен
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """
    Создает JWT refresh токен.
    
    Args:
        data (dict): Данные для кодирования
        expires_delta (timedelta, optional): Время жизни токена
        
    Returns:
        str: Закодированный JWT токен
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    """
    Декодирует JWT токен.
    
    Args:
        token (str): JWT токен
        
    Returns:
        dict | None: Payload токена или None если невалиден
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logging.error(f"JWT decode error: {e}")
        return None
