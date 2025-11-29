from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.jwt_handler import decode_token
from redis_client import get_cached_user, cache_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Получает текущего пользователя с кэшированием в Redis"""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Проверяем кэш Redis
    cached_user = get_cached_user(email)
    if cached_user:
        # Возвращаем объект User из кэша
        user = User(
            id=cached_user["id"],
            email=cached_user["email"],
            hashed_password="",  # не храним пароль в кэше
            is_verified=cached_user.get("is_verified", False),
            avatar_url=cached_user.get("avatar_url")
        )
        return user

    # Если не в кэше, получаем из БД
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    # Проверяем верификацию email
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден. Проверьте почту."
        )
    
    # Кэшируем пользователя
    cache_user(email, {
        "id": user.id,
        "email": user.email,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url
    })
    
    return user